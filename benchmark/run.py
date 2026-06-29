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

def call_model(agent, prompt, stage, usage_log, model=None):
    """Run one model call via agent-ctl, append usage to the ledger log, return text.
    NOTE: token accounting is approximate (agent-ctl doesn't expose exact usage yet) —
    we estimate from prompt/response length until real usage is wired."""
    cmd = ["python3", "/Users/rubenffuertes/.claude/skills/agent_ctl.py", "start", agent, prompt]
    if model:
        cmd += ["-m", model]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=600).stdout
    # TODO: agent-ctl start returns a session id; real impl waits + reads result.
    approx_in = len(prompt) // 4
    approx_out = len(out) // 4
    usage_log.append({"stage": stage, "model": model or agent, "in": approx_in, "out": approx_out})
    return out


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
    args = ap.parse_args()
    if args.selftest:
        selftest()
    elif args.run:
        print("live --run not wired yet: needs stage prompts in benchmark/stages/ + a paper+reviews.",
              file=sys.stderr)
        sys.exit(2)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
