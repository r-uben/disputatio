# Benchmark harness (#53) — the dual ruler

A faithful reimplementation of the [refine.ink](https://www.refine.ink/blog/refine-ai-reviewer-benchmark) 8-stage head-to-head, plus a from-scratch cost ledger. It measures both axes that decide #53: **quality** (verified residual-concern yield) and **cost** (€/paper). "Their rules, so beating them on it is unimpeachable." Design rationale: `docs/log/2026-06-17_refine-benchmark.md`; placement in the rebuild: `docs/log/2026-06-18_v9-architecture.md`.

## The two rulers

**Quality — 8-stage head-to-head** (compares two reviews of the same paper):

| Stage | Job | Model tier |
|---|---|---|
| 1 extract | free-text review → atomic concerns (disputatio panels skip this) | small |
| 2 classify | 4 axes: scope / significance / actionability / external_factual | small |
| 3 anchor-check | does the concern name a real paper feature? | small |
| 4 align | match shared concerns between the two reviews | small→mid |
| 5 rank | order residual (unique) concerns by significance bucket | small |
| 6 judge | flip-averaged panel + model-family self-bias filter → winner | **frontier** |

Metrics: head-to-head win rate; unique verified residual concerns per significance tier (target: beat refine's 28.1 overall / 1.76 load-bearing).

**Cost — the ledger** (`cost_ledger.py`): every model call logs `{stage, model, in, out}` to `usage.jsonl`; the ledger totals token volume + API-equivalent USD (subscription marginal cost is ~$0, so the API-equivalent number is the comparator vs Refine's €50/paper).

Data contracts: `schemas.md`.

## Status

- [x] Cost ledger (`cost_ledger.py`) + price config (`model_prices.json`, prices to verify)
- [x] Data-contract schemas (`schemas.md`)
- [x] Verbatim refine.ink appendix captured (`refine_appendix.md`) — faithful-reimplementation reference
- [x] Deterministic core: bucketing, residual diff, flip-averaged judge, self-bias filter, aggregation (`run.py`, `--selftest` green)
- [x] Stage prompts, verbatim from the appendix (`stages/1_extract.md` … `stages/6_judge.md`)
- [x] Judge routing decided: disputatio is cross-architecture (anthropic+openai+google), so GPT/Gemini judges are ALWAYS self-bias-disqualified on a disputatio match. Primary panel = **Grok + Kimi** (neutral), flip-averaged. GPT-5.5+Gemini run only as a caveated secondary panel. See `stages/6_judge.md` header note.
- [ ] Wire live `--run` (real agent-ctl calls + XML/JSON parsing — `call_model` is currently a stub)
- [ ] First run on an arXiv econ-preprint pair (disputatio panel vs single-shot baseline)

## Run the cost ledger

```bash
uv run benchmark/cost_ledger.py --selftest                       # synthetic demo
uv run benchmark/cost_ledger.py <run>/usage.jsonl --report c.json # a real run
```
