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
- [x] Live `--run` wired end-to-end (`run.py`): extract → classify → anchor → align → residuals → flip-averaged neutral judge panel, with per-stage validation gates, retry-once-then-halt, blinding asserts, and cost logging (failures included)
- [x] Contestant driver (`generate_disputatio.py`): orient → holistic → attack-surface index → 3 discovery tracks × 3 families → merge, fully scripted (ruler and contestant kept separate, mirroring refine's design)
- [x] First manual thin-slice run (ricco2026, broad_critic-only): panel score 0.25 → baseline won; flagged as non-informative for the core thesis (wrong track for an identification paper) — see session log
- [x] Full-discovery re-run on ricco2026 through the unified harness: **panel score 0.50 — tie** (up from 0.25). Judges split cleanly and order-stably (Grok→baseline on its 5 unique load-bearing identification critiques; Kimi→disputatio on specificity/anchoring density). 27 shared concerns ate most of disputatio's credit; its unique set kept only 1 load-bearing.
- [x] Match verification + harmonize added to the ruler (`--rescore`): enforcing refine's own "same flaw, same feature — not topical adjacency" rule dropped 11/27 matches (symmetric: baseline's unique load-bearing actually GREW 5→7). Result: **panel score 1.0 — unanimous disputatio win, both judges, both orders** (Grok flipped). Mechanism: over-matching had been hiding baseline's generic filler inside "shared"; once visible in its residual, judges penalized it per refine's own vagueness criterion. Trajectory on ricco2026: 0.25 → 0.50 → 1.00.
- Caveats (always disclose): n=1 paper, single judge sample (no error bars); the verification stage is our documented, symmetric addition — refine's own diff internals are unpublished.
- [ ] Next: run more papers (the harness is two commands per paper) for a real sample; optional: calibration pass in the contestant driver

## Run it — the CLI

```bash
uv run disputatio-bench match <paper.md> --outdir <rundir>   # everything: baseline + generate + score + report
```

Or stage by stage (each resume-safe):

```bash
uv run disputatio-bench baseline <paper.md> --outdir <rundir>   # single-shot referee (refine's verbatim prompt)
uv run disputatio-bench generate <paper.md> --outdir <rundir>   # disputatio contestant side
uv run disputatio-bench score    --outdir <rundir>              # ruler: classify -> anchor -> align -> verify -> judge
uv run disputatio-bench rescore  --outdir <rundir>              # re-run verify+harmonize+judges only
uv run disputatio-bench report   --outdir <rundir>              # verdict summary
uv run disputatio-bench cost     --outdir <rundir>              # per-run cost ledger
```

Entry point defined in the root `pyproject.toml` (`benchmark.cli:main`).

## Run the cost ledger

```bash
uv run benchmark/cost_ledger.py --selftest                       # synthetic demo
uv run benchmark/cost_ledger.py <run>/usage.jsonl --report c.json # a real run
```
