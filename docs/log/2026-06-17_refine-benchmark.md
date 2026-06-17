# Refine.ink benchmark — break their numbers, open, at a fraction of the cost

**Issue:** #53 · **Branch:** `feat/53-refine-benchmark` · **Started:** 2026-06-17

## Mission

An open, auditable paper reviewer that **beats Refine's published benchmark numbers** *and* runs at **a fraction of their €50/paper**, by engineering a **big+small model orchestration** rather than brute-forcing frontier models behind a closed product. The benchmark is both the goal (break the numbers) and the ruler (prove it). Openness is the third axis Refine concedes: they disclose methodology but ship no code, data, or leaderboard, and charge €50/paper.

Source: <https://www.refine.ink/blog/refine-ai-reviewer-benchmark> + appendix.

## Objective — two hard axes, both measured

**Quality (break the numbers).** On a faithful reimplementation of Refine's 8-stage flip-averaged head-to-head harness, disputatio must:
- exceed **28.1** unique verified residual concerns/paper (their reported average; competitors ≈ 14.5),
- exceed **1.76** load-bearing (central-result tier) residual concerns/paper (competitors ≈ 1.03),
- out-margin Refine against the *same* field: single-shot GPT-5.5 / Gemini 3.1 Pro / Opus / Fable, and GPT-5.5+Coarse.

**Cost (fraction of €50).** Tracked per run as Σ(tokens × model price). Goal: an order of magnitude below Refine on the cost-quality frontier.

Proof artifact: a cost-quality frontier plot (disputatio vs Refine vs single-shot vs Coarse) + fully open methodology.

## Key insight — the benchmark closes disputatio's own acknowledged gap

`templates/evaluation.md` (current Phase 7) judges **each finding against the paper** and explicitly refuses recall and head-to-head ("you cannot measure recall without a gold register … deferred until a reference pool of real issues exists"). Refine's head-to-head **residual-concern** comparison sidesteps the gold-key problem a different way: align the two systems' shared concerns, diff to each side's *unique* concerns, and have a judge panel decide which residual list better serves the author. That is a *relative* quality measure with **no answer key** — exactly the recall-adjacent signal disputatio said it lacked. So this is additive, not a replacement.

## What disputatio already has (reuse, don't rebuild)

- **`templates/schemas/panel_row.md`** — the atomic concern unit, already ~80% of Refine's `<concern>`:
  | Refine atomic concern | disputatio panel_row |
  |---|---|
  | `title` / `body` | `concern` (one-sentence falsifiable claim) |
  | `anchor kind=...` + verbatim ref | `evidence[].quote` + `evidence[].location` |
  | `specificity` specific/general | (derive from `support_type` direct_quote/derived_inference) |
  | `significance` load_bearing/substantive_local/cosmetic | `severity` material/local/nit — near 1:1 |
  | scope internal/external/generic | `category` + `needs_web_verification` |
  | actionability | `suggested_action` |
  | external_factual | `needs_web_verification` |
- **`_evaluation/` sub-DAG + blinding** (`manifest_blind.json`, randomised `BF###`, metadata-strip) — reuse wholesale for the judge stage's anti-bias discipline.
- **`agent-ctl` per-phase model routing + Ollama/family-aware transports** — the plumbing for big+small routing already exists.

## What must be built (Phase A — the dual ruler)

A new head-to-head sub-DAG, sibling to the existing per-finding eval, under `_benchmark/` in the paper folder. Eight stages, each a ticket; small models do the mechanical ones.

| # | Stage | Input | Output | Default model (cost tier) |
|---|---|---|---|---|
| 1 | **Extract** | free-text review (baselines only; disputatio panels skip this) | atomic concerns (panel_row-compatible) | small (Haiku / Flash / Qwen) |
| 2 | **Classify** | paper_md + concern | 4 axes (scope, significance, actionability, external_factual) + reasoning | small |
| 3 | **Anchor-check** | paper_md + concerns | `anchored: true/false` per concern (names a real feature, not "is it correct") | small |
| 4 | **Align** | concerns X, concerns Y | `{matches, x_unmatched, y_unmatched}` w/ confidence | small→mid |
| 5 | **Rank** | residual concerns bucketed | ordered residual lists per bucket | small |
| 6 | **Judge** | paper_md + residual X + residual Y | `{winner, reason, pivotal_concerns}`, flip-averaged, self-bias filter | **frontier** (GPT-5.5 + Gemini Pro) |
| — | **Cost ledger** | every ticket's token usage | per-run Σ(tokens × price), €/paper | (instrumentation, build from scratch) |
| — | **Aggregate** | all judge verdicts | win-rate, residual yield by tier, €/paper | inline (no ticket) |

Self-bias filter (mandatory): drop any judge whose model family matches a contestant — else the disputatio-internal Claude/GPT/Gemini contaminate the judging.

**Cost ledger is build-from-scratch:** `agent_ctl.py` does not track usage (its token refs only *strip* CLI noise). Phase A instruments per-ticket token capture → price table → `_benchmark/cost.json`.

## Model-routing thesis (the actual product, Phase C)

Stages 1–5 are structured, well-specified tasks → small/local models do them ~free. Frontier models earn cost only on: subtle load-bearing **discovery** (main pipeline), the **M8 derivation** check, and the **judge**. Constraint already on record: Haiku can't take 140KB-paper prompts → small-model stages that need the whole paper require chunking or short-context sub-tasks (anchor-check, classify are per-concern → naturally short-context).

## Risks (honest)

1. **Disputatio may currently cost MORE than Refine** — cross-arch multi-agent DAG. The cost win is engineered + measured, not assumed. Hence cost ledger from run one.
2. **Calibration trades count for precision** — demote-on-doubt may drop concerns the judge would credit. Phase C needs a benchmark-aware calibration mode that holds precision without over-pruning.
3. **Judge contamination** — enforce the self-bias filter rigorously.
4. **Small-model quality floor** — validate small models don't degrade extraction/anchor/classify before trusting them; a bad classifier poisons the whole comparison.

## Phases

- **A — Dual ruler** (this log's build): 8-stage head-to-head harness + cost ledger under `_benchmark/`.
- **B — Honest baseline**: 5–10 econ preprints (NBER + arXiv mix); single-shot baselines w/ Refine's exact referee prompt; run disputatio as-is; score quality + €/paper. No flattering.
- **C — Cost-down + quality-up**: tier the pipeline onto small/local models; benchmark-aware calibration; harder M8/narrow_evidence on load-bearing econ errors; push past 28.1 / 1.76 while cutting €/paper.
- **D — Publish**: 150-paper-shape run; frontier plot + open methodology as the empirical spine of `docs/research-notes/methodology-note/`.

## Open question (non-blocking)

Direct disputatio-vs-Refine match needs Refine's actual outputs (not released). Obtain (free tier / blog worked example) or settle for "beats the same field by a bigger margin." Doesn't block A/B.

## Decisions log

- 2026-06-17 — Reimplement Refine's harness faithfully (their stages, their judge protocol) rather than invent our own metric, so "we beat them" is on their rules. Build it as a `_benchmark/` sub-DAG sibling to `_evaluation/`, reusing the blinding infra. Cost ledger is a first-class Phase A deliverable, not an afterthought.
