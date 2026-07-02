# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Contestant driver — produce disputatio's side of a benchmark head-to-head (issue #53).

Runs the discovery-relevant slice of the real pipeline, scripted end to end:
  orient (3 families, parallel)
  -> holistic (3 families, parallel)
  -> attack-surface index (union, 1 call)
  -> discovery: holistic_candidates + broad_critic + narrow_evidence x 3 families (parallel)
  -> merge/dedup -> concerns_X.json (atomic-concern schema the ruler consumes)

Deliberately scripted as a SEPARATE driver from run.py (the ruler): the benchmark
stays neutral — contestants produce reviews however they like; the ruler only scores.
Calibration/debate/render are still skipped (thin slice); that is a known, flagged
difference from full disputatio, not hidden.

Transports: codex + gemini via agent-ctl (they WRITE output files; workspace-write),
claude family via headless `claude -p` printing JSON to stdout (driver saves it).
All prompts are short disk-reference prompts (see run.py lessons). Usage logged.

  uv run benchmark/generate_disputatio.py --paper benchmark/data/ricco2026/paper.md \
      --outdir benchmark/data/ricco2026/full_run
"""
import argparse
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from run import REPO, agent_call, log_usage, HarnessError, _with_retry  # noqa: E402

TEMPLATES = REPO / "templates"
FAMILIES = ("claude", "codex", "gemini")
CODEX_MODELS = {"orient": "gpt-5.4-mini", "holistic": "gpt-5.4",
                "holistic_candidates": "gpt-5.4-mini", "broad_critic": "gpt-5.4",
                "narrow_evidence": "gpt-5.4"}
CLAUDE_MODELS = {"orient": "sonnet", "holistic": "sonnet", "holistic_candidates": "sonnet",
                 "broad_critic": "sonnet", "narrow_evidence": "sonnet",
                 "index": "opus", "merge": "opus"}


def json_repair(text):
    """Parse JSON out of agent output: strip fences, extract the outermost {...} if
    there is surrounding prose, and repair gemini's raw-LaTeX-backslash failure mode."""
    text = re.sub(r"^```json\s*|\s*```\s*$", "", text.strip())
    candidates = [text]
    if "{" in text and "}" in text:
        candidates.append(text[text.find("{"):text.rfind("}") + 1])
    for cand in candidates:
        for attempt in (cand, re.sub(r'\\(?!["\\/bfnrtu])', r"\\\\", cand)):
            try:
                return json.loads(attempt)
            except json.JSONDecodeError:
                continue
    raise ValueError(f"unparseable JSON (first 120 chars: {text[:120]!r})")


def claude_call(prompt, stage, outdir, model="sonnet", timeout=900):
    """Headless claude CLI; prints JSON to stdout, driver saves. Read-only tools."""
    r = subprocess.run(["claude", "-p", prompt, "--model", model],
                       capture_output=True, text=True, timeout=timeout)
    log_usage(outdir, stage, f"claude-{model}", len(prompt) // 4, len(r.stdout) // 4)
    return r.stdout


def family_task(family, phase, prompt, out_path, outdir, timeout=900):
    """Run one (family, phase) call. codex writes out_path itself (with a chat-salvage
    fallback — mini models sometimes print instead of writing); gemini and claude
    PRINT JSON which we save (Antigravity can't write files headlessly without -y).
    Resume-safe: an existing, parseable out_path is reused without a new call."""
    out_path = Path(out_path)
    if out_path.exists():
        try:
            d = json.load(open(out_path))
            print(f"  {phase}.{family}: reusing existing output")
            return d
        except Exception:
            out_path.unlink()  # corrupt leftover — regenerate
    def go():
        if family == "claude":
            raw = claude_call(prompt, f"{phase}.claude", outdir,
                              model=CLAUDE_MODELS[phase], timeout=timeout)
            out_path.write_text(json.dumps(json_repair(raw), indent=2))
        elif family == "codex":
            res = agent_call(prompt, f"{phase}.codex", outdir, agent="codex",
                             model=CODEX_MODELS[phase], write=True, timeout=timeout)
            if out_path.exists():
                out_path.write_text(json.dumps(json_repair(out_path.read_text()), indent=2))
            else:  # salvage: model printed the JSON in chat instead of writing the file
                out_path.write_text(json.dumps(json_repair(res), indent=2))
        else:  # gemini prints; we save
            res = agent_call(prompt, f"{phase}.gemini", outdir, agent="gemini",
                             write=False, timeout=timeout)
            out_path.write_text(json.dumps(json_repair(res), indent=2))
        return json.load(open(out_path))
    return _with_retry(f"{phase}.{family}", go)


def phase_prompt(template, paper, extra_inputs, out_path, family):
    """Short disk-reference prompt: agent reads the real template + inputs itself."""
    inputs = "\n".join(f"- {k}: {v}" for k, v in extra_inputs.items())
    write_clause = (
        f"WRITE your output JSON directly to the file: {out_path}\n"
        "Do NOT print the JSON in chat; reply with a one-line summary."
        if family == "codex" else
        "PRINT the output JSON — the complete JSON object and nothing else: no prose, no markdown fence."
    )
    return f"""You are one family worker in disputatio's benchmark thin-slice run (issue #53).

Read the task template at: {template}
Follow its Task and Output schema EXACTLY, with these deviations only:
- Inputs are these files (ignore the template's {{{{...}}}} placeholders):
- paper: {paper}
{inputs}
- If the template mentions an attack_surface_index and none is listed above, use "novel" for attack_surface_id fields.
- Every quote MUST be a verbatim substring of the paper file (whitespace-normalized).
- Set "agent" to "{family}".

{write_clause}"""


def run_wave(phase, paper, outdir, extra_inputs_fn, template, timeout=900):
    outdir = Path(outdir)
    results = {}
    with ThreadPoolExecutor(3) as ex:
        futs = {}
        for fam in FAMILIES:
            out_path = outdir / f"{phase}_{fam}.json"
            prompt = phase_prompt(template, paper, extra_inputs_fn(fam), out_path, fam)
            futs[fam] = ex.submit(family_task, fam, phase, prompt, out_path, outdir, timeout)
        for fam, fut in futs.items():
            results[fam] = fut.result()  # raises HarnessError on double failure
            print(f"  {phase}.{fam}: ok")
    return results


def build_index(paper, outdir):
    """Union the 3 holistic passes into one attack-surface index (orchestrator step)."""
    out_path = Path(outdir) / "attack_surface_index.json"
    prompt = f"""Build disputatio's canonical attack-surface index (union step after the holistic wave).

Read the three holistic passes: {outdir}/holistic_claude.json, {outdir}/holistic_codex.json, {outdir}/holistic_gemini.json
Union their attack surfaces, dedup on surface description (same paper feature + same worry = one entry, keep the sharpest phrasing), and emit JSON:
{{"attack_surfaces": [{{"id": "AS1", "type": "theory|proof|empirics|identification|framing|robustness|exposition", "description": "...", "paper_location": "...", "priority": "high|medium|low", "requires_deep_engagement": true|false, "families": ["claude","codex","gemini"]}}]}}
Priority: high = load-bearing for the paper's main claims AND flagged by 2+ families or clearly central.

PRINT the JSON to stdout — nothing else."""
    def go():
        raw = claude_call(prompt, "index.claude", outdir, model=CLAUDE_MODELS["index"])
        d = json_repair(raw)
        if not d.get("attack_surfaces"):
            raise ValueError("empty attack-surface index")
        Path(out_path).write_text(json.dumps(d, indent=2))
        return d
    return _with_retry("index", go)


def merge_concerns(outdir):
    """Merge 9 discovery outputs into the atomic-concern set the ruler consumes."""
    outdir = Path(outdir)
    files = sorted(str(p) for p in outdir.glob("discover_*.json"))
    out_path = outdir / "disputatio_concerns.json"
    prompt = f"""Merge disputatio's discovery outputs into one deduplicated atomic-concern set (orchestrator merge step).

Read ALL of these discovery files (fields: issues[] with id/claim/evidence/impact/...):
{chr(10).join('- ' + f for f in files)}

Rules:
- One concern = one issue. Cluster findings from different families/tracks that raise the SAME flaw about the SAME paper feature into ONE concern; record all source ids and the set of families in "architecture_support".
- Do NOT drop any distinct finding. Do NOT invent findings.
- Keep the sharpest phrasing; prefer entries with verbatim quotes.
- Output ids X1..Xn.

Emit JSON:
{{"side": "disputatio", "n_raw": <total input issues>, "concerns": [{{"id": "X1", "title": "<=100 chars", "specificity": "specific|general", "anchor": {{"kind": "quote|section|equation|table|figure", "ref": "<=180 chars"}} | null, "body": "full claim", "architecture_support": ["claude",...], "source_ids": ["bc_claude_001",...]}}]}}

PRINT the JSON to stdout — nothing else."""
    def go():
        raw = claude_call(prompt, "merge.claude", outdir, model=CLAUDE_MODELS["merge"], timeout=1200)
        d = json_repair(raw)
        n = len(d.get("concerns", []))
        if n < 10:
            raise ValueError(f"merge produced only {n} concerns — implausible")
        ids = [c["id"] for c in d["concerns"]]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate concern ids")
        Path(out_path).write_text(json.dumps(d, indent=2))
        return d
    return _with_retry("merge", go)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper", required=True)
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    paper = str(Path(args.paper).resolve())

    print("[wave 1/5] orient (3 families)")
    run_wave("orient", paper, outdir, lambda f: {}, TEMPLATES / "orient.md", timeout=600)

    print("[wave 2/5] holistic (3 families)")
    run_wave("holistic", paper, outdir,
             lambda f: {"your own paper map": outdir / f"orient_{f}.json"},
             TEMPLATES / "holistic.md", timeout=600)

    print("[wave 3/5] attack-surface index (union)")
    idx = build_index(paper, outdir)
    print(f"  index: {len(idx['attack_surfaces'])} surfaces")

    print("[wave 4/5] discovery (3 tracks x 3 families)")
    for track, tmpl in (("holistic_candidates", "discover_holistic.md"),
                        ("broad_critic", "discover_broad.md"),
                        ("narrow_evidence", "discover_narrow.md")):
        # phase key for model routing; output name discover_<track>_<family>.json
        def inputs(f, track=track):
            return {"your own paper map": outdir / f"orient_{f}.json",
                    "your own holistic pass": outdir / f"holistic_{f}.json",
                    "canonical attack-surface index": outdir / "attack_surface_index.json"}
        outnames = {fam: outdir / f"discover_{track}_{fam}.json" for fam in FAMILIES}
        with ThreadPoolExecutor(3) as ex:
            futs = {fam: ex.submit(
                family_task, fam, track,
                phase_prompt(TEMPLATES / tmpl, paper, inputs(fam), outnames[fam], fam),
                outnames[fam], outdir, 1200) for fam in FAMILIES}
            for fam, fut in futs.items():
                fut.result()
                print(f"  {track}.{fam}: ok")

    print("[wave 5/5] merge -> disputatio_concerns.json")
    merged = merge_concerns(outdir)
    print(f"  merged: {merged['n_raw']} raw -> {len(merged['concerns'])} concerns")
    print("DONE:", outdir / "disputatio_concerns.json")


if __name__ == "__main__":
    main()
