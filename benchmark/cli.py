"""
disputatio-bench — one CLI for the whole head-to-head benchmark (issue #53).

    disputatio-bench match <paper.md> --outdir RUN     baseline + generate + score
    disputatio-bench baseline <paper.md> --outdir RUN  single-shot referee (refine's verbatim prompt)
    disputatio-bench generate <paper.md> --outdir RUN  disputatio contestant side
    disputatio-bench score --outdir RUN [--paper P]    ruler (auto-finds sides in RUN)
    disputatio-bench rescore --outdir RUN              verify + harmonize + re-judge
    disputatio-bench report --outdir RUN               result summary
    disputatio-bench cost --outdir RUN                 cost ledger for the run
    disputatio-bench selftest                          deterministic-core tests

Ruler and contestant stay separate modules (mirroring refine's design); this is just
the front door. Every subcommand is resume-safe where the underlying stage is.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from run import (REPO, agent_call, log_usage, run_pipeline, rescore,  # noqa: E402
                 selftest as run_selftest)

APPENDIX = Path(__file__).parent / "refine_appendix.md"


def referee_prompt():
    """Extract refine's verbatim single-shot referee prompt from the captured appendix."""
    t = APPENDIX.read_text()
    block = t[t.index("## Single-shot referee prompt"):]
    a = block.index("```") + 3
    b = block.index("```", a)
    return block[a:b].strip()


def cmd_baseline(paper, outdir, model="gpt-5.5"):
    """Generate the single-shot baseline review (previously a manual step)."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    out_md = outdir / "baseline_review.md"
    if out_md.exists() and out_md.stat().st_size > 2000:
        print(f"baseline: reusing existing {out_md}")
        return out_md
    paper = Path(paper).resolve()
    prompt = f"""{referee_prompt()}

The manuscript is the file at: {paper}
Read it in full, then produce the referee report per the structure above."""
    print(f"baseline: generating single-shot review ({model})")
    res = agent_call(prompt, "baseline_generate", outdir, model=model, write=False, timeout=900)
    if len(res) < 2000 or "Recommendation" not in res:
        raise SystemExit(f"baseline review looks broken ({len(res)} chars) — not saving")
    out_md.write_text(res)
    print(f"baseline: {out_md} ({len(res)} chars)")
    return out_md


def cmd_score(outdir, paper=None):
    outdir = Path(outdir)
    paper = Path(paper) if paper else outdir / "paper.md"
    x = outdir / "disputatio_concerns.json"
    y = outdir / "baseline_review.md"
    for f, hint in ((paper, "--paper"), (x, "run `generate` first"), (y, "run `baseline` first")):
        if not Path(f).exists():
            raise SystemExit(f"missing {f} ({hint})")
    return run_pipeline(str(paper), str(x), str(y), str(outdir))


def cmd_report(outdir):
    r = json.load(open(Path(outdir) / "result.json"))
    print(f"winner: {r['winner']}   panel score (P(X wins)): {r['panel_score_X']}")
    for side in ("disputatio", "baseline"):
        s = r[side]
        print(f"  {side:11}: {s['n_concerns']} concerns, {s['n_residual']} residual, "
              f"tiers {s['residual_tiers']}")
    print(f"  shared: {r['n_shared']}")
    for v in r.get("verdicts", []):
        print(f"  {v['judge']:5} {v['order']}: {v['winner']:4} — {v['reason'][:90]}")


def cmd_cost(outdir):
    from cost_ledger import load_prices, report
    usage = Path(outdir) / "usage.jsonl"
    if not usage.exists():
        raise SystemExit(f"no usage log at {usage}")
    rows = [json.loads(ln) for ln in open(usage) if ln.strip()]
    prices = load_prices(Path(__file__).parent / "model_prices.json")
    text, _ = report(rows, prices, 0.92)
    print(text)


def main():
    ap = argparse.ArgumentParser(prog="disputatio-bench", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    for name, needs_paper in (("match", True), ("baseline", True), ("generate", True),
                              ("score", False), ("rescore", False),
                              ("report", False), ("cost", False)):
        p = sub.add_parser(name)
        if needs_paper:
            p.add_argument("paper", help="path to the paper markdown (socr OCR output)")
        if name == "score":
            p.add_argument("--paper", help="paper path (defaults to RUN/paper.md)")
        if name == "baseline":
            p.add_argument("--model", default="gpt-5.5")
        p.add_argument("--outdir", required=True, help="run directory")
    sub.add_parser("selftest")

    args = ap.parse_args()
    if args.cmd == "selftest":
        run_selftest()
    elif args.cmd == "baseline":
        cmd_baseline(args.paper, args.outdir, model=args.model)
    elif args.cmd == "generate":
        from generate_disputatio import generate
        generate(args.paper, args.outdir)
    elif args.cmd == "score":
        cmd_score(args.outdir, paper=args.paper)
    elif args.cmd == "rescore":
        rescore(args.outdir)
    elif args.cmd == "report":
        cmd_report(args.outdir)
    elif args.cmd == "cost":
        cmd_cost(args.outdir)
    elif args.cmd == "match":
        outdir = Path(args.outdir)
        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / "paper.md").exists() or (outdir / "paper.md").write_text(
            Path(args.paper).read_text())
        cmd_baseline(args.paper, args.outdir)
        from generate_disputatio import generate
        generate(args.paper, args.outdir)
        cmd_score(args.outdir, paper=args.paper)
        cmd_report(args.outdir)


def cmd_review(paper, outdir):
    """EXPERIMENTAL standalone review — the discovery slice only (orient -> holistic ->
    index -> 3 tracks x 3 families -> merge), rendered to markdown. The full pipeline
    (calibration, escalation gate, debate, panel render) still runs via the /disputatio
    skill in Claude Code; porting it to code IS the v9 milestone."""
    from generate_disputatio import generate
    outdir = Path(outdir)
    merged = generate(paper, outdir)
    lines = [f"# Review concerns — {Path(paper).stem}", "",
             "> EXPERIMENTAL thin-slice output (discovery + merge only; not calibrated, "
             "not debated, not a full disputatio panel — see /disputatio for the full pipeline).", ""]
    for c in merged["concerns"]:
        fams = ",".join(c.get("architecture_support", []))
        anchor = c.get("anchor")
        loc = f" — *{anchor['kind']}: {anchor['ref'][:100]}*" if anchor else ""
        lines += [f"## {c['id']} · {c['title']}", f"({fams}){loc}", "", c["body"], ""]
    out_md = outdir / "review_concerns.md"
    out_md.write_text("\n".join(lines))
    print(f"review: {len(merged['concerns'])} concerns -> {out_md}")


def main_product():
    """`disputatio` — the product front door (like gws/obsidian: installed, on PATH).

        disputatio review <paper.md> --outdir RUN   experimental thin-slice review
        disputatio bench <subcommand> ...           the full benchmark CLI (see `disputatio bench --help`)
    """
    argv = sys.argv[1:]
    if argv and argv[0] == "bench":
        sys.argv = [sys.argv[0] + " bench"] + argv[1:]
        return main()
    ap = argparse.ArgumentParser(prog="disputatio", description=main_product.__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    rv = sub.add_parser("review", help="experimental thin-slice review (discovery+merge)")
    rv.add_argument("paper")
    rv.add_argument("--outdir", required=True)
    sub.add_parser("bench", help="benchmark subcommands (match/baseline/generate/score/...)")
    args = ap.parse_args(argv)
    if args.cmd == "review":
        cmd_review(args.paper, args.outdir)


if __name__ == "__main__":
    main()
