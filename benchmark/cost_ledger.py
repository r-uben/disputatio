# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Cost ledger — the cost axis of the disputatio benchmark dual ruler (issue #53).

`agent_ctl` does not track usage, so this is built from scratch. It records BOTH
numbers that matter:
  - token volume (always real, transport-independent)
  - API-equivalent USD (tokens x provider list price) — the comparable cost number,
    reported even though marginal cost on subscription routing (Claude Pro / ChatGPT
    Pro / Gemini OAuth) is ~$0. This is what places disputatio against Refine's
    EUR50/paper on a cost-quality frontier.

Input: a usage log, one JSON object per model call:
  {"stage": "discovery.narrow", "model": "gpt-5.4", "in": 12000, "out": 1500}

Usage:
  uv run benchmark/cost_ledger.py <usage.jsonl> [--prices benchmark/model_prices.json] [--fx 0.92]
  uv run benchmark/cost_ledger.py --selftest
"""
import argparse
import json
from collections import defaultdict


def load_prices(path):
    with open(path) as f:
        d = json.load(f)
    return d.get("prices", d)


def cost_usd(model, tin, tout, prices):
    p = prices.get(model)
    if not p:  # unknown / null-priced model -> flag, never silently zero
        return None
    return tin / 1e6 * p["in_per_mtok"] + tout / 1e6 * p["out_per_mtok"]


def tally(rows, prices):
    by_stage = defaultdict(lambda: {"in": 0, "out": 0, "usd": 0.0, "calls": 0})
    by_model = defaultdict(lambda: {"in": 0, "out": 0, "usd": 0.0, "calls": 0})
    unpriced = set()
    for r in rows:
        m, tin, tout = r["model"], int(r.get("in", 0)), int(r.get("out", 0))
        usd = cost_usd(m, tin, tout, prices)
        if usd is None:
            unpriced.add(m)
            usd = 0.0
        for key, agg in ((r.get("stage", "?"), by_stage), (m, by_model)):
            a = agg[key]
            a["in"] += tin
            a["out"] += tout
            a["usd"] += usd
            a["calls"] += 1
    return by_stage, by_model, unpriced


def report(rows, prices, fx):
    by_stage, by_model, unpriced = tally(rows, prices)
    tin = sum(int(r.get("in", 0)) for r in rows)
    tout = sum(int(r.get("out", 0)) for r in rows)
    usd = sum(m["usd"] for m in by_model.values())
    L = ["# Cost ledger", "",
         f"calls: {len(rows)}   tokens in: {tin:,}   out: {tout:,}   total: {tin + tout:,}",
         f"API-equivalent: ${usd:.2f}  (EUR {usd * fx:.2f} @ fx={fx})   "
         f"marginal on subscription routing: ~$0"]
    if unpriced:
        L.append(f"!! UNPRICED models (counted as $0): {sorted(unpriced)} — add to prices config")
    L.append("\n## by stage (USD desc)")
    for s, a in sorted(by_stage.items(), key=lambda kv: kv[1]["usd"], reverse=True):
        L.append(f"  ${a['usd']:7.2f}  {a['in'] + a['out']:>9,} tok  x{a['calls']:<3}  {s}")
    L.append("\n## by model (USD desc)")
    for m, a in sorted(by_model.items(), key=lambda kv: kv[1]["usd"], reverse=True):
        L.append(f"  ${a['usd']:7.2f}  {a['in'] + a['out']:>9,} tok  x{a['calls']:<3}  {m}")
    summary = {"calls": len(rows), "tok_in": tin, "tok_out": tout,
               "usd": round(usd, 2), "eur": round(usd * fx, 2), "unpriced": sorted(unpriced)}
    return "\n".join(L), summary


SELFTEST = [
    {"stage": "extract", "model": "claude-haiku", "in": 8000, "out": 1200},
    {"stage": "classify", "model": "claude-haiku", "in": 3000, "out": 400},
    {"stage": "discovery.narrow", "model": "claude-opus", "in": 40000, "out": 3000},
    {"stage": "merge", "model": "claude-sonnet", "in": 30000, "out": 2000},
    {"stage": "judge", "model": "gpt-5.5", "in": 20000, "out": 800},
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("usage", nargs="?")
    ap.add_argument("--prices", default="benchmark/model_prices.json")
    ap.add_argument("--fx", type=float, default=0.92, help="USD->EUR rate")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--report", help="write JSON summary here")
    args = ap.parse_args()
    prices = load_prices(args.prices)
    if args.selftest:
        rows = SELFTEST
    elif args.usage:
        with open(args.usage) as f:
            rows = [json.loads(ln) for ln in f if ln.strip()]
    else:
        ap.error("usage log required (or --selftest)")
    text, summary = report(rows, prices, args.fx)
    print(text)
    if args.report:
        with open(args.report, "w") as f:
            json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
