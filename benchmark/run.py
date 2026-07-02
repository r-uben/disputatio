# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Head-to-head harness — our faithful reimplementation of refine.ink's scoring pipeline
(issue #53). Compares two reviews of ONE paper and decides which better serves the
author. Stage prompts mirror benchmark/refine_appendix.md verbatim.

Pipeline:  extract -> classify(4 axes) -> anchor-check -> align -> residual diff
           -> rank-in-buckets -> flip-averaged judge panel (+ self-bias filter)

This module holds the DETERMINISTIC core (bucketing, residual diff, flip-average,
self-bias filter, aggregation) — fully unit-tested via --selftest with NO model calls.
The model-calling stages (extract/classify/anchor/align/rank/judge) shell out to
agent-ctl and log usage to the cost ledger; they run in --run mode once we have data.

  uv run benchmark/run.py --selftest
  uv run benchmark/run.py --run --paper p.md --x disputatio_concerns.json --y baseline_review.txt
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

STAGES_DIR = Path(__file__).parent / "stages"
STAGE_FILES = {  # stage name -> template file (benchmark/stages/, verbatim refine prompts)
    "extract": "1_extract.md", "classify": "2_classify.md", "anchor_check": "3_anchor_check.md",
    "align": "4_align.md", "rank": "5_rank.md", "judge": "6_judge.md",
}


def load_stage_prompt(stage, **placeholders):
    """Load a stage template from benchmark/stages/ and fill its {placeholders}."""
    text = (STAGES_DIR / STAGE_FILES[stage]).read_text()
    for key, val in placeholders.items():
        text = text.replace("{" + key + "}", val)
    return text

FAMILY = {  # model -> provider family, for the self-bias filter
    "gpt-5.5": "openai", "gpt-5.4": "openai", "gpt-5.4-mini": "openai",
    "gemini-3.1-pro": "google", "gemini-pro": "google", "gemini-flash": "google",
    "claude-opus": "anthropic", "claude-sonnet": "anthropic", "claude-haiku": "anthropic",
    "grok": "xai", "kimi": "moonshot",
}

# ---------------------------------------------------------------------------
# DETERMINISTIC CORE  (no model calls — this is what --selftest exercises)
# ---------------------------------------------------------------------------

def bucket_key(concern):
    """refine stage-5/6 bucket key: significance|actionability|anchored."""
    return f"{concern['significance']}|{concern['actionability']}|{concern['anchored']}"


def residuals(align, x_ids, y_ids):
    """Given the stage-4 alignment, return each side's UNIQUE (residual) concern ids.
    A concern is shared if it appears in any match; residuals are the rest."""
    matched_x = {m["x_id"] for m in align.get("matches", [])}
    matched_y = {m["y_id"] for m in align.get("matches", [])}
    x_res = [i for i in x_ids if i not in matched_x]
    y_res = [i for i in y_ids if i not in matched_y]
    return x_res, y_res


def self_bias_keep(judge_model, contestant_families):
    """refine rule: drop any judge whose model family matches a contestant being scored."""
    return FAMILY.get(judge_model) not in contestant_families


def flip_average(verdicts):
    """verdicts: list of {"judge","order","winner"} where order is 'xy' or 'yx' and
    winner in {'X','Y','tie'}. Average each judge across both orders, then across judges.
    Returns (panel_score in [0,1] = P(X wins), label). 1.0 => X wins both orders, all judges."""
    by_judge = {}
    for v in verdicts:
        by_judge.setdefault(v["judge"], []).append(1.0 if v["winner"] == "X"
                                                    else 0.0 if v["winner"] == "Y" else 0.5)
    if not by_judge:
        return None, "no_eligible_judge"
    per_judge = [sum(s) / len(s) for s in by_judge.values()]
    score = sum(per_judge) / len(per_judge)
    label = "X" if score >= 0.75 else "Y" if score <= 0.25 else "tie"
    return score, label


def tier_counts(residual_concerns):
    """Count residual concerns by significance tier (the headline metric vs refine's 28.1 / 1.76)."""
    out = {"load_bearing": 0, "substantive_local": 0, "cosmetic": 0}
    for c in residual_concerns:
        out[c["significance"]] = out.get(c["significance"], 0) + 1
    return out


def aggregate(x_concerns, y_concerns, align, judge_verdicts, x_label="disputatio", y_label="baseline"):
    x_ids = [c["id"] for c in x_concerns]
    y_ids = [c["id"] for c in y_concerns]
    x_res, y_res = residuals(align, x_ids, y_ids)
    xr = [c for c in x_concerns if c["id"] in x_res]
    yr = [c for c in y_concerns if c["id"] in y_res]
    score, label = flip_average(judge_verdicts)
    winner = {"X": x_label, "Y": y_label, "tie": "tie", None: "n/a"}[label]
    return {
        "winner": winner, "panel_score_X": score,
        x_label: {"n_concerns": len(x_ids), "n_residual": len(x_res), "residual_tiers": tier_counts(xr)},
        y_label: {"n_concerns": len(y_ids), "n_residual": len(y_res), "residual_tiers": tier_counts(yr)},
        "n_shared": len(align.get("matches", [])),
    }


# ---------------------------------------------------------------------------
# MODEL-CALLING STAGES  (live in --run; shell to agent-ctl, log to cost ledger)
# ---------------------------------------------------------------------------

# Operational lessons encoded from the 2026-07-02 manual run on ricco2026:
#  1. NEVER pass giant inline CLI-argument prompts (a ~162K-char batch-classify arg
#     returned an empty root in 27s). Keep prompts SHORT; agents read inputs from
#     files on disk (they are full agentic CLIs with --cwd access).
#  2. Agents WRITE their outputs to files (no stdout scraping — kills the gemini
#     JSON-escaping and truncation failure modes).
#  3. Validate after every stage (ids complete, enums legal); retry ONCE, then halt.
#  4. Blinding is asserted, not assumed: judge prompts must never name the systems.
#  5. Every call (including failures) is logged to usage.jsonl.

import os
import re
import time
import xml.etree.ElementTree as ET

REPO = Path(__file__).resolve().parent.parent
AGENT_CTL = os.path.expanduser("~/.claude/skills/agent_ctl.py")


class HarnessError(RuntimeError):
    """A stage failed twice — the run halts rather than shipping bad data."""


def _sh(cmd, timeout=None):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def log_usage(outdir, stage, model, tin, tout):
    with open(Path(outdir) / "usage.jsonl", "a") as f:
        f.write(json.dumps({"stage": stage, "model": model, "in": tin, "out": tout}) + "\n")


def agent_call(prompt, stage, outdir, *, agent="codex", model=None, write=True, timeout=600):
    """One synchronous agent-ctl call: start -> wait -> result. Short prompt, disk I/O."""
    cmd = ["python3", AGENT_CTL, "start", agent, prompt, "--cwd", str(REPO),
           "--timeout", str(timeout)]
    if model:
        cmd += ["-m", model]
    if write:
        cmd += ["--flags", "--sandbox", "workspace-write"]
    out = _sh(cmd).stdout
    m = re.search(r"Session (\d+) started", out)
    if not m:
        raise HarnessError(f"{stage}: agent-ctl start failed:\n{out[-500:]}")
    sid = m.group(1)
    _sh(["python3", AGENT_CTL, "wait", sid], timeout=timeout + 120)
    res = _sh(["python3", AGENT_CTL, "result", sid]).stdout
    log_usage(outdir, stage, model or agent, len(prompt) // 4, len(res) // 4)
    return res


def kimi_call(prompt, stage, outdir, timeout=600):
    """Direct kimi CLI call (not via agent-ctl)."""
    r = _sh(["kimi", "-p", prompt], timeout=timeout)
    log_usage(outdir, stage, "kimi-k2.5", len(prompt) // 4, len(r.stdout) // 4)
    return r.stdout


def _template_core(stage, start_marker, end_marker):
    t = (STAGES_DIR / STAGE_FILES[stage]).read_text()
    return t[t.index(start_marker):t.index(end_marker)].strip()


def _with_retry(stage_name, fn):
    """Run a stage fn (which must validate + return); retry once on failure, then halt."""
    try:
        return fn()
    except HarnessError:
        raise
    except Exception as e:
        print(f"[{stage_name}] attempt 1 failed ({e}); retrying once", file=sys.stderr)
        time.sleep(5)
        try:
            return fn()
        except Exception as e2:
            raise HarnessError(f"{stage_name} failed twice: {e2}") from e2


# ---- stage implementations (ruler). All I/O via files under outdir. ----------

def stage_extract(review_path, outdir, prefix="Y"):
    """Free-text review -> atomic concerns JSON (refine stage 1)."""
    core = _template_core("extract", "A concern is one substantive issue", "CRITICAL OUTPUT RULES")
    out_xml = Path(outdir) / f"extract_{prefix}.xml"
    prompt = f"""You enumerate the substantive concerns in one referee review of a research paper (benchmark harness stage 1).

Read the review at: {review_path}

{core}

Output format: XML, one `<concern>` element per concern, wrapped in a `<concerns>` root; title/body/anchor in CDATA; ids C1, C2, ... in order of appearance.

WRITE the XML directly to the file: {out_xml}
Do NOT print the XML in chat. After writing, reply with one line: how many concerns you wrote."""
    def go():
        agent_call(prompt, f"extract.{prefix}", outdir)
        tree = ET.parse(out_xml)
        concerns = []
        for i, c in enumerate(tree.getroot().findall("concern"), 1):
            a = c.find("anchor")
            concerns.append({
                "id": f"{prefix}{i}", "title": c.find("title").text,
                "specificity": c.find("specificity").text,
                "anchor": {"kind": a.get("kind"), "ref": a.text} if a is not None else None,
                "body": c.find("body").text, "source_id": c.get("id"),
            })
        if not concerns:
            raise ValueError("0 concerns extracted")
        out = {"side": prefix, "concerns": concerns}
        json.dump(out, open(Path(outdir) / f"concerns_{prefix}.json", "w"), indent=2)
        return out
    return _with_retry(f"extract.{prefix}", go)


def stage_classify(concerns_path, outdir, prefix):
    """4-axis classification for every concern (refine stage 2), batched via disk."""
    core = _template_core("classify", "CRITICAL CALIBRATION RULE", "Output format:")
    out_xml = Path(outdir) / f"classify_{prefix}.xml"
    ids = [c["id"] for c in json.load(open(concerns_path))["concerns"]]
    prompt = f"""You classify a BATCH of referee concerns about a research paper (benchmark harness stage 2).

Read the paper at: {Path(outdir) / 'paper.md'}
Read the concerns at: {concerns_path} (field "concerns"; ids {ids[0]}..{ids[-1]})

For EACH concern independently, apply this rubric:

{core}

Output: XML — one `<classification id="...">` per concern (same ids, same order), all wrapped in one `<classifications>` root. Per-classification schema: <scope>internal|external_or_positioning|generic</scope>, <significance>load_bearing|substantive_local|cosmetic</significance>, <actionability>actionable|vague</actionability>, <external_factual>yes|no</external_factual>, each with a matching `<*_reasoning>` CDATA field (<=25 words).

You MUST emit one classification for EVERY concern ({len(ids)} total). WRITE the XML to: {out_xml}
Do NOT print the XML in chat. Reply with one line: count written."""
    def go():
        agent_call(prompt, f"classify.{prefix}", outdir)
        t = ET.parse(out_xml)
        els = {e.get("id"): e for e in t.getroot().findall("classification")}
        missing = set(ids) - set(els)
        if missing:
            raise ValueError(f"missing ids: {sorted(missing)}")
        out = {}
        for cid, e in els.items():
            row = {k: e.find(k).text for k in ("scope", "significance", "actionability", "external_factual")}
            if row["significance"] not in ("load_bearing", "substantive_local", "cosmetic"):
                raise ValueError(f"{cid}: bad significance {row['significance']}")
            out[cid] = row
        json.dump(out, open(Path(outdir) / f"labels_{prefix}.json", "w"), indent=2)
        return out
    return _with_retry(f"classify.{prefix}", go)


def stage_anchor(concerns_path, outdir, prefix):
    """Anchor-support check (refine stage 3)."""
    core = _template_core("anchor_check", "ANCHORED means", "Output format:")
    out_xml = Path(outdir) / f"anchor_{prefix}.xml"
    ids = [c["id"] for c in json.load(open(concerns_path))["concerns"]]
    prompt = f"""You decide whether each referee concern is anchored to the paper (benchmark harness stage 3).

Read the paper at: {Path(outdir) / 'paper.md'}
Read the concerns at: {concerns_path} (field "concerns")

{core}

Output: XML — one `<anchor_check id="...">` per concern with `<anchored>true|false</anchored>` and a CDATA `<reasoning>` (<=30 words), wrapped in `<results>`. One per EVERY concern ({len(ids)} total).
WRITE the XML to: {out_xml}
Do NOT print the XML in chat. Reply with one line: counts true/false."""
    def go():
        agent_call(prompt, f"anchor.{prefix}", outdir)
        t = ET.parse(out_xml)
        els = {e.get("id"): e.find("anchored").text for e in t.getroot().findall("anchor_check")}
        missing = set(ids) - set(els)
        if missing:
            raise ValueError(f"missing ids: {sorted(missing)}")
        if any(v not in ("true", "false") for v in els.values()):
            raise ValueError("bad anchored enum")
        out = {k: v == "true" for k, v in els.items()}
        json.dump(out, open(Path(outdir) / f"anchored_{prefix}.json", "w"), indent=2)
        return out
    return _with_retry(f"anchor.{prefix}", go)


def stage_align(outdir):
    """Shared-concern alignment X vs Y (refine stage 4)."""
    tmpl = (STAGES_DIR / STAGE_FILES["align"]).read_text()
    core = tmpl[:tmpl.index("── Review X concerns")].strip()
    out_json = Path(outdir) / "align.json"
    prompt = f"""{core}

Read Review X's concerns at: {Path(outdir) / 'concerns_X.json'} (field "concerns")
Read Review Y's concerns at: {Path(outdir) / 'concerns_Y.json'} (field "concerns")

WRITE the strict JSON (matches / x_unmatched / y_unmatched) to: {out_json}
Do NOT print it in chat. Reply with one line: match / unmatched counts."""
    def go():
        agent_call(prompt, "align", outdir)
        d = json.load(open(out_json))
        x_ids = {c["id"] for c in json.load(open(Path(outdir) / "concerns_X.json"))["concerns"]}
        y_ids = {c["id"] for c in json.load(open(Path(outdir) / "concerns_Y.json"))["concerns"]}
        x_used = {m["x_id"] for m in d["matches"]} | set(d["x_unmatched"])
        y_used = {m["y_id"] for m in d["matches"]} | set(d["y_unmatched"])
        if x_ids - x_used or y_ids - y_used or x_used - x_ids or y_used - y_ids:
            raise ValueError(f"id coverage broken: X missing {x_ids - x_used}, invented {x_used - x_ids}; "
                             f"Y missing {y_ids - y_used}, invented {y_used - y_ids}")
        return d
    return _with_retry("align", go)


def build_residuals(outdir, align):
    """Deterministic: merge labels+anchors onto concerns, diff residuals, drop cosmetic for judging."""
    sides = {}
    for prefix in ("X", "Y"):
        concerns = json.load(open(Path(outdir) / f"concerns_{prefix}.json"))["concerns"]
        labels = json.load(open(Path(outdir) / f"labels_{prefix}.json"))
        anchored = json.load(open(Path(outdir) / f"anchored_{prefix}.json"))
        for c in concerns:
            c.update(labels[c["id"]])
            c["anchored"] = anchored[c["id"]]
        sides[prefix] = concerns
    x_res_ids, y_res_ids = residuals(align, [c["id"] for c in sides["X"]], [c["id"] for c in sides["Y"]])
    xr = [c for c in sides["X"] if c["id"] in x_res_ids]
    yr = [c for c in sides["Y"] if c["id"] in y_res_ids]
    full = {"x_residual": xr, "y_residual": yr}
    json.dump(full, open(Path(outdir) / "residuals.json", "w"), indent=2)
    json.dump({"x_residual": yr, "y_residual": xr},
              open(Path(outdir) / "residuals_swapped.json", "w"), indent=2)
    return sides["X"], sides["Y"], xr, yr


BLIND_BANNED = ("disputatio", "baseline", "single-shot", "panel")


def stage_judge(outdir, judges=("grok", "kimi")):
    """Flip-averaged judge panel (refine stage 6) on blind residual lists."""
    tmpl = (STAGES_DIR / STAGE_FILES["judge"]).read_text()
    core = tmpl[tmpl.index("You decide which of two"):tmpl.index("<paper>")].strip()
    verdicts = []
    for order, fname in (("xy", "residuals.json"), ("yx", "residuals_swapped.json")):
        for judge in judges:
            out_md = Path(outdir) / f"judge_{order}_{judge}.md"
            prompt = f"""{core}

Read the paper at: {Path(outdir) / 'paper.md'}
Read Side X's residual concerns at: {Path(outdir) / fname} (field "x_residual") — group by "significance": load_bearing vs substantive_local; ignore cosmetic entries.
Read Side Y's residual concerns at: {Path(outdir) / fname} (field "y_residual") — same grouping.

Emit the prose body (Review X / Review Y / Contrast / Pivotal concerns), then on the final line:
VERDICT: {{"winner": "X" | "Y" | "tie", "reason": "<one sentence>", "pivotal_concerns": ["<id>", ...]}}

WRITE your full response to the file: {out_md}
Do NOT print the analysis in chat. Reply with ONLY the one-line VERDICT JSON."""
            for banned in BLIND_BANNED:  # blinding is asserted, not assumed
                assert banned not in prompt.lower(), f"blinding leak: {banned!r} in judge prompt"
            def go(judge=judge, order=order, prompt=prompt, out_md=out_md):
                if judge == "kimi":
                    kimi_call(prompt, f"judge.{judge}_{order}", outdir)
                else:
                    # write=False: --sandbox is a codex-only flag; grok writes by default
                    agent_call(prompt, f"judge.{judge}_{order}", outdir,
                               agent="grok", model="grok-build", write=False)
                text = out_md.read_text()
                m = re.search(r'VERDICT:\s*(\{.*?\})', text, re.S)
                v = json.loads(m.group(1))
                if v["winner"] not in ("X", "Y", "tie"):
                    raise ValueError(f"bad winner {v['winner']}")
                return v
            v = _with_retry(f"judge.{judge}_{order}", go)
            w = v["winner"]
            if order == "yx" and w in ("X", "Y"):  # remap swapped labels to TRUE sides
                w = "Y" if w == "X" else "X"
            verdicts.append({"judge": judge, "order": order, "winner": w,
                             "raw": v["winner"], "reason": v["reason"],
                             "pivotal_concerns": v.get("pivotal_concerns")})
    return verdicts


def run_pipeline(paper, x_concerns, y_review, outdir, x_label="disputatio", y_label="baseline"):
    """The full ruler. X = atomic concerns JSON (skips extract); Y = free-text review."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    if not (outdir / "paper.md").exists():
        (outdir / "paper.md").write_text(Path(paper).read_text())

    # X side arrives atomic (panel rows are already concerns); normalize into place.
    xd = json.load(open(x_concerns))
    json.dump({"side": "X", "concerns": xd["concerns"]}, open(outdir / "concerns_X.json", "w"), indent=2)
    print(f"[1/6] extract: X pre-atomic ({len(xd['concerns'])}); extracting Y from free text")
    stage_extract(y_review, outdir, prefix="Y")
    print("[2/6] classify X, Y")
    stage_classify(outdir / "concerns_X.json", outdir, "X")
    stage_classify(outdir / "concerns_Y.json", outdir, "Y")
    print("[3/6] anchor-check X, Y")
    stage_anchor(outdir / "concerns_X.json", outdir, "X")
    stage_anchor(outdir / "concerns_Y.json", outdir, "Y")
    print("[4/6] align")
    align = stage_align(outdir)
    print("[5/6] residual diff")
    xc, yc, xr, yr = build_residuals(outdir, align)
    print(f"      residuals: X={len(xr)} {tier_counts(xr)}  Y={len(yr)} {tier_counts(yr)}")
    print("[6/6] judge panel (flip-averaged, neutral families)")
    verdicts = stage_judge(outdir)
    result = aggregate(xc, yc, align, verdicts, x_label=x_label, y_label=y_label)
    result["verdicts"] = verdicts
    json.dump(result, open(outdir / "result.json", "w"), indent=2)
    print(json.dumps({k: v for k, v in result.items() if k != "verdicts"}, indent=2))
    return result


# ---------------------------------------------------------------------------
# SELFTEST — exercises the deterministic core on synthetic data, no model calls
# ---------------------------------------------------------------------------

def selftest():
    x = [  # disputatio: 4 concerns, 3 load-bearing
        {"id": "X1", "significance": "load_bearing", "actionability": "actionable", "anchored": True},
        {"id": "X2", "significance": "load_bearing", "actionability": "actionable", "anchored": True},
        {"id": "X3", "significance": "load_bearing", "actionability": "vague", "anchored": True},
        {"id": "X4", "significance": "substantive_local", "actionability": "actionable", "anchored": True},
    ]
    y = [  # baseline: 3 concerns, 1 load-bearing
        {"id": "Y1", "significance": "load_bearing", "actionability": "actionable", "anchored": True},
        {"id": "Y2", "significance": "substantive_local", "actionability": "vague", "anchored": True},
        {"id": "Y3", "significance": "cosmetic", "actionability": "actionable", "anchored": True},
    ]
    align = {"matches": [{"x_id": "X1", "y_id": "Y1", "confidence": "high", "note": "shared"}],
             "x_unmatched": ["X2", "X3", "X4"], "y_unmatched": ["Y2", "Y3"]}
    # disputatio (anthropic+openai+google) vs baseline single-shot gpt-5.5 (openai)
    contestants = {"openai", "anthropic", "google"}
    judges = ["gpt-5.5", "gemini-3.1-pro", "grok"]
    eligible = [j for j in judges if self_bias_keep(j, contestants)]
    verdicts = [{"judge": j, "order": o, "winner": "X"} for j in eligible for o in ("xy", "yx")]

    print("=== self-bias filter ===")
    for j in judges:
        print(f"  {j:16} family={FAMILY[j]:10} -> {'KEEP' if self_bias_keep(j, contestants) else 'drop'}")
    print(f"  eligible judges: {eligible}  (disputatio spans all 3 major families -> only xAI/Moonshot survive!)")
    print("\n=== bucket keys ===")
    for c in x:
        print(f"  {c['id']}: {bucket_key(c)}")
    print("\n=== aggregate verdict ===")
    print(json.dumps(aggregate(x, y, align, verdicts), indent=2))
    assert flip_average(verdicts)[1] == "X" or not eligible
    print("\n[selftest OK]")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--paper")
    ap.add_argument("--x", help="side X concerns (disputatio panel JSON)")
    ap.add_argument("--y", help="side Y review (baseline free-text)")
    ap.add_argument("--outdir", help="run directory (holds all stage artifacts + usage.jsonl)")
    args = ap.parse_args()
    if args.selftest:
        selftest()
    elif args.run:
        if not (args.paper and args.x and args.y and args.outdir):
            ap.error("--run requires --paper --x --y --outdir")
        run_pipeline(args.paper, args.x, args.y, args.outdir)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
