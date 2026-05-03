# Cross-system bench: disputatio vs coarse.ink

*Website post draft. Lives in `docs/outreach/` until ready to translate to the gh-pages site under `posts/2026-05-coarse-bench.md` (or equivalent).*

## TL;DR

- 4-paper head-to-head against [coarse.ink](https://coarse.ink), refine.ink as reference, gemini-3.1-pro single judge.
- Disputatio v7 lost on average by Δ = −0.81 (coverage and depth — coarse caught formal-spec gaps v7 missed systematically).
- v7.1 (drop discovery models from mini to gpt-5.4 / gemini-3.1-pro) closed +0.5 to +1.0 per paper, depending on case.
- v8.0 (new obligation-extraction layer) measured on Galeotti: **5.8 vs coarse 6.00** — closest tie disputatio has come.
- v8.1 (wrong-but-present audit) and v8.2 (framing audit) shipped as design; bench pending.

## What we measured

Coarse.ink publishes a 4-paper bench corpus: Galeotti / Stephens / Van Vreeswijk / Forney. They run their own pipeline on each, score with gemini-3.1-pro single judge against [refine.ink](https://refine.ink) reviews as reference. We replicated the same harness for disputatio, using the same judge prompt, same reference reviews, same scoring rubric (coverage / specificity / depth / consistency, 1–6).

The coarse-vs-refine baseline is published at coarse.ink/compare. The disputatio runs and scoring scripts live in `docs/benchmark/coarse_corpus/` and `docs/benchmark/v8_0_validation/`.

## v7 baseline — losing on coverage and depth

| Paper | coarse | disputatio v7 | Δ |
|---|---|---|---|
| Galeotti, Golub & Goyal 2020 | 6.00 | 5.5 | −0.50 |
| Stephens & Donnelly 2000 | 5.62 | 4.5 | −1.12 |
| Van Vreeswijk & Sompolinsky 1998 | 5.75 | 4.5 | −1.25 |
| Forney 1988 | 5.38 | 5.0 | −0.38 |
| **Mean** | **5.69** | **4.88** | **−0.81** |

Specificity and consistency tied at 5–6 across both systems. The loss was concentrated in coverage and depth — coarse caught **formal-specification gaps** (kernel definitions missing initial conditions, MH algorithms missing complete-data densities, ascertainment restrictions too weak) that v7's discovery tracks missed systematically.

## v7.1 — drop the mini

The v7 discovery loop ran codex `gpt-5.4-mini` and gemini-3-flash-preview. Hypothesis: just upgrading those to full models on the `narrow_evidence` and `broad_critic` tracks would surface formal-spec gaps at panel stage instead of missing them entirely.

Validated on two papers, full pipeline (calibration + Route-B debate):

| Paper | v7 | v7.1 | Δ | Judge |
|---|---|---|---|---|
| Forney 1988 | 5.0 | 5.5 | **+0.5** | gemini-3.1-pro |
| Stephens 2000 | 2.5 | 3.5 | **+1.0** | codex/gpt-5.4 (gemini OAuth dead mid-run) |

Stephens v7.1 specifically caught the **MCMC complete-data-density gap** — coarse comment #3 — that v7 missed entirely. Modest but real win.

## v8.0 — obligation extraction (the structural fix)

A 5.5 critical review by codex flagged the actual gap: v7 has no **obligation model**. For each method/result, what objects MUST exist for it to be executable or provable? Without that, even stronger discovery models charitably interpolate the missing pieces.

v8.0 adds three new pipeline phases between holistic and discovery:

- **Phase 1.5a** — per-family obligation extraction. For every load-bearing claim, list required objects (definitions, properties, conditions). Search the paper. Mark each `satisfied | partial | unsatisfied`.
- **Phase 1.5b** — global integrator. Cluster equivalent obligations across families using LLM clustering (not string similarity). Preserve cross-family disagreement verbatim — never collapse to a vote.
- **Phase 3g** — gap-claim calibration. Two-stage: satisfaction-check fires only on disputed/yes/partial obligations (one correct citation defeats the gap; one bad satisfied verdict does not suppress it). Then a five-component rubric (burden + obligation + scoped absence + substitute evaluation + consequence). All five must hold for `reportable_gap`.

Plus a graceful-degradation contract for partial-family runs (Anthropic content filter blocks van Vreeswijk; gemini OAuth expires mid-run; codex weekly cap) — engine metadata records `families_present`, `families_blocked`, `block_reasons`, `support_type`. Hard-fail is not the policy.

## v8.0 J on Galeotti — first measurement

Pure-addition test: take the existing v7.1 panel, add v8.0 gap-class rows on top, render, judge. Result:

| | Galeotti score | vs coarse 6.00 |
|---|---|---|
| disputatio v7 | 5.5 | −0.50 |
| disputatio v7.1 | 5.0 | −1.00 (mode mismatch with v7) |
| **disputatio v8.0 J** | **5.8** | **−0.20** |

**Closest disputatio has gotten to coarse on any paper.** +0.8 over the v7.1 baseline (referee-mode comparison) on one design change.

Per-dimension (judge, gemini-3.1-pro):

| Dim | v7.1 | v8.0 J |
|---|---|---|
| Coverage | 4 | 5 |
| Specificity | 5 | 6 |
| Depth | 6 | 6 |
| Consistency | 5 | 6 |

The judge specifically praises the new findings: J ≤ 2K dimension constraint (Lemma 4), `Λ₀` lattice closure, Barnes-Wall γ leading-term verification, dimensional inconsistency in trellis-gain expression. These are obligation-style gaps v7 missed.

The single shipped v8.0 gap row (OA3.1 corner regime sketched not closed, local severity) was the only one of 12 obligation-queue candidates that survived gap calibration. The other 11 were correctly killed as resolved-by-paper or not-real-gaps. The +0.8 gain came mostly from calibration discipline making the panel sharper, not from the single new row.

## v8.1 + v8.2 — what's left

v8.0 closes the **absence** failure mode. Two more failure modes coarse catches that v8.0 alone doesn't:

- **v8.1 wrong-but-present** — the formal object exists; the formal object is wrong under the paper's own definitions. Stephens #8 (non-varying-sites conditions on too much), #10 (tree count mixes topology with merger order), Forney Class V/VI flawed distance arguments.
- **v8.2 scope/framing overreach** — the formal object exists and is correct; the narrative claim around it overreaches. Comparator unfairness, novelty inflation, empirics-below-conclusion, formal-to-practical leap.

Both shipped as designs in PRs #25 and #26. Templates + integrators + calibration rubrics with cross-phase IDs, audit-time anti-pedantry guardrails, and a pragmatic caveat-handling rule that distinguishes abstract topline overreach (caveats elsewhere don't save) from section/conclusion overreach (same-section caveats usually do save).

Bench pending. Strictly sequential per the validation plan: v8.0 already validated on Galeotti → small v8.1 bench → v8.2 in parallel with broader v8.1 bench, only after the v8.1 ledger shape is stable.

## What this does not claim

- **n=4 papers**, one full-pipeline v8.0 measurement. Directional, not statistical.
- **Single judge**: gemini-3.1-pro. Cross-judge stress test pending.
- **Same-judge dependency**: gemini OAuth expires mid-run; capacity 429 hits unpredictably. v7.1 Stephens fell back to codex judge; cross-judge magnitude not comparable to gemini-judge magnitude.
- **No author/referee user study yet.** Coarse-comparison measures judge scores, not utility to a real author or referee.
- **Bench corpus is coarse-curated.** The papers we bench against are the ones coarse picked. Real-world papers are different.

The architecture covers the failure modes coarse demonstrably catches. The validation that disputatio actually catches them at scale is multi-week empirical work, not yet complete.

## What we'd like

If you read this far and have an econ-theory or applied econometrics paper near submission, we'd like to test on it. Email anchor / contact form: TBD.

If you've already looked at the [Galeotti demo panel](LINK) and have feedback: [feedback form](LINK).
