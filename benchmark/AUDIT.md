# End-to-end harness audit — 2026-07-08

Joint audit: Claude (systematic pass, verified against the ricco2026 artifacts) + Codex
gpt-5.5 (independent, session 22). Every finding below was confirmed in code or run
artifacts, not speculated. **Until the HIGH items are fixed and re-run, the ricco2026
panel score of 1.0 is PROVISIONAL** — two findings (blinding leak, post-hoc protocol
change) directly taint it.

## The two verdict-tainting findings

**T1 — Blinding leak through data (not prompt).** `residuals.json` — the file judges
read — carried `architecture_support: ["claude",...]` and `source_ids: ["bc_claude_008"]`
on X concerns (naming model families) while Y had anonymous `source_id: C1`. The
blinding assert only checked prompt text. Judges could infer X = multi-model system.
Fix: sanitize both sides to an identical judge-facing field set.

**T2 — Protocol changed after seeing the result.** The match-verification stage was
added AFTER observing the 0.50 tie, and flipped it to 1.00. The stage is defensible
(refine's own "no topical adjacency" rule, symmetric by construction) — but adding it
post-hoc is classic garden-of-forking-paths. Fix: freeze the scoring protocol now;
treat ricco2026 as a DEV paper; headline numbers only from papers scored under the
frozen protocol.

## A. Fidelity bugs (vs benchmark/refine_appendix.md)

| # | Finding | Sev | Fix |
|---|---|---|---|
| A1 | Anchor-check computed but never filters (unanchored Y15 reached judges); refine: "filters ... out of the scoring path" | high | drop unanchored before align/diff; matches touching them revert partners to residual |
| A2 | scope=external_or_positioning/generic concerns reach the judge — whose verbatim prompt asserts they were "already filtered out upstream" (X7 was even pivotal in result.json) | high | filter to internal before judging |
| A3 | Cosmetic concerns passed to judge in-file with only a prompt instruction to ignore | high | physically remove from judge inputs + headline tiers |
| A4 | Stage 5 (rank within buckets) never wired — prompt file exists, no stage_rank | high | wire it between diff and judge |
| A5 | Panel-level tie-break missing (refine: "harness breaks a panel-level tie by counting concerns") | high | count filtered substantive residuals on tie |
| A6 | Self-bias filter true only by construction; not enforced in stage_judge | high | judge registry + fail-closed family check |
| A7 | = T2 (match verification is a scoring-rule change) | high | freeze protocol; disclose as our documented addition |
| A8 | X skips stage-1 extraction (submits pre-atomized concerns + own metadata) while Y gets extracted — asymmetric atomization control | med | contestant submits a rendered REPORT; ruler extracts both sides identically |
| A9 | Judge receives file paths to raw JSON, not fenced ranked `<x_concerns>`/`<y_concerns>` blocks | med | build sanitized fenced blocks inline |

## B. Correctness / robustness

| # | Finding | Sev |
|---|---|---|
| B1 | Stale-artifact reuse can cross-contaminate papers (baseline reused by size; paper.md kept if exists; driver reuses any parseable JSON) — needs run manifests w/ hashes | high |
| B2 | Subprocess return codes ignored; stages don't delete stale outputs before calls → silent stale-parse | high |
| B3 | = T1 blinding data leak | high |
| B4 | Validation too weak (only significance enum checked; duplicate ids, invented pivotal ids accepted) | high |
| B5 | Judge routing: any judge != "kimi" silently becomes grok-build but is labeled as requested | med |
| B6 | flip_average accepts incomplete panels (missing orders) | med |
| B7 | aggregate() recomputes unfiltered residuals instead of consuming the canonical filtered artifact | med |
| B8 | Contestant merge unvalidated (9 files present? source-id coverage? quote substring check?) | med |
| B9 | Cost logging is chars//4 of prompt/result only — files agents read/write uncounted | med |

## C. Process gaps (what a credible benchmark still needs)

1. **n=1 is not a benchmark** — pre-specify a multi-paper sample; report win rate + Wilson CI (as refine does).
2. **Judge variance unmeasured** — repeat judge runs; agreement stats; sensitivity panel (GPT+Gemini, caveated).
3. **No recall/reference metric** — judged preference ≠ recall; build a reference concern set on ≥1 paper.
4. **Protocol freeze + held-out papers** (= T2 discipline).
5. **external_factual labeled but never routed** — exclude from internal scoring or verify via web track.
6. **Cost headline not citable** — null prices for most models; token counts estimated.
7. **Contestant is the thin slice** — full disputatio (calibration/debate/render) benchmarked separately once ported (v9).
8. **No human spot-check protocol** — sample stage artifacts per paper for blinded human audit.
9. **Baseline suite incomplete** — single-shot suite across families; report vs strongest baseline.

## Disposition

Mechanical HIGH fixes (A1-A6, B2-B7 partial, T1) → implemented in run.py now, then
re-judge ricco2026 under the corrected ruler; result stays labeled DEV/provisional per
T2. A8, B1, B8, B9 and all of C → tracked as the next milestones on #53.
