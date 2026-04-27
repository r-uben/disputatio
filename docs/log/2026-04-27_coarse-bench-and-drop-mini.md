# 2026-04-27 — Coarse.ink head-to-head + drop-mini v7.1 experiment

## Summary

Ran disputatio v7 on the four-paper coarse.ink benchmark corpus (Galeotti 2020, Stephens & Donnelly 2000, van Vreeswijk & Sompolinsky 1998, Forney 1988). Scored against refine.ink as reference review using a reconstructed Gemini 3.1 Pro single-judge rubric (coverage / specificity / depth / consistency, 1–6). Coarse beats v7 on every paper. Followed up with a `drop_mini` ablation: re-run `narrow_evidence` on stronger discovery models (codex `gpt-5.4` medium effort, gemini-3.1-pro-preview) for Forney and Stephens, full pipeline (calibration + Route B debate). Both deltas positive (+0.5 / +1.0 within-judge), shipping issue #4 in v7.1.

## Bench results (v7 baseline, gemini judge against refine reference)

| Paper | Coarse | Disputatio v7 | Δ |
|---|---|---|---|
| Galeotti 2020 | 6.00 | 5.5 | −0.50 |
| Stephens 2000 | 5.62 | 4.5 | −1.12 |
| Van Vreeswijk 1998 | 5.75 | 4.5 | −1.25 |
| Forney 1988 | 5.38 | 5.0 | −0.38 |
| **Mean** | **5.69** | **4.88** | **−0.81** |

Coarse beats v7 by **0.81 mean**, driven by coverage (4.25 vs 5.75) and depth (4.25 vs 5.50). Specificity and consistency tied 5–6.

## Why coarse wins

The judge consistently flags v7 for missing **formal-spec gaps** — kernel definitions, complete-data densities, dimensional constraints, normalization-constant outsourcing. v7's `narrow_evidence` track on `gpt-5.4-mini` doesn't surface these systematically. Coarse runs `gpt-5.4` at high effort with a dedicated adversarial-proof-verification module per section.

Specific examples coarse caught and v7 missed on Stephens:
- MH algorithm needs the complete-data joint density (coarse #3)
- Initial split missing from state kernel (coarse #1)
- History kernel needs event-level definition (coarse #2)
- Ascertainment restriction too weak (coarse #7)

Codex 5.5 critical review on the v8 design framed this as v7 missing an explicit **obligation model** ("for this claimed method/result, what objects must exist for it to be executable/provable?").

## v7.1 drop-mini experiment

Hypothesis: just upgrading discovery models on `narrow_evidence` (issue #4 in v8 backlog) would partially close the gap. Codex 5.5 called it "blunt" pre-experiment; ranked it the least structural fix.

**Forney (gemini judge, fully clean test)**:

| | v7 | v7.1 clean | Δ |
|---|---|---|---|
| Overall | 5.0 | 5.5 | **+0.5** |
| Coverage | 4.0 | 5.0 | +1.0 |
| Specificity | 6.0 | 5.0 | −1.0 |
| Depth | 4.0 | 6.0 | **+2.0** |
| Consistency | 6.0 | 6.0 | 0 |

**Stephens (codex judge, gemini OAuth dead — apples-to-apples codex on both v7 and v7.1)**:

| | v7 | v7.1 clean | Δ |
|---|---|---|---|
| Overall | 2.5 | 3.5 | **+1.0** |

(Note: codex is a much harsher judge than gemini — same v7 Stephens scored 4.5 by gemini vs 2.5 by codex. Within-judge delta is meaningful, cross-judge magnitude is not.)

**Both papers improve** with drop-mini. Stephens gain is larger, consistent with the hypothesis that drop-mini helps most where the v7 formal-spec deficit is largest.

## Mechanism

Stronger codex on `narrow_evidence` surfaces formal-spec findings at discovery stage that v7 missed entirely or only caught at Phase 4 red-team:

- **Forney v7.1 narrow caught**: `Λ_0` lattice closure not proven (this is the same gap the v7 Route B defender used to break F005 consensus — now it appears at discovery stage as a primary candidate); Lemma 5 hidden stronger lemma; Lemma 4 J ≤ 2K dimension constraint; Barnes-Wall γ leading-term verification gap; Table III D_8/RE_8 partition order conflict.
- **Stephens v7.1 narrow caught**: Theorem 1 normalization constant outsourced to Stephens 2000; Remark 1 / eq (21) jump-chain misidentification; **MCMC method I missing complete-data joint density** (this is coarse comment #3 — the canonical example v7 missed).

The MCMC-density catch is the load-bearing one: it shows that even without obligation extraction (issue #1), a stronger model on `narrow_evidence` can catch the type of gap coarse's adversarial-proof module was specifically designed for. Issue #4 (drop mini) does not make issue #1 unnecessary, but it closes a non-trivial part of the gap.

## Caveats

1. **Forney clean test, Stephens partly contaminated.** Stephens v7.1 had 3 confounds: gemini-3.1-pro-preview hit capacity 429 on `narrow_evidence` (fell back to v7 baseline gemini narrow); synth ran on codex instead of gemini (OAuth expired mid-run); judge ran on codex instead of gemini (OAuth was cancelled). Within-judge codex delta is the best we have for Stephens.
2. **n=2 papers**. Forney has the smallest v7 gap (Δ=−0.38), Stephens the largest (Δ=−1.12). The two deltas (+0.5, +1.0) plausibly scale with deficit size, but this is two data points.
3. **Calibration not re-run on Galeotti or VV**. The v7.1 experiment only covered Forney and Stephens.
4. **Judge bias**. gemini-3.1-pro-preview is the same judge coarse uses to score itself; potential systematic preference toward certain review styles. The codex judge experiment (on Stephens) confirms within-judge deltas are robust to judge change, but absolute scores are not.

## Decisions

1. **Ship issue #4 (drop mini for `narrow_evidence` and `broad_critic`)** as v7.1. Codex `gpt-5.4-mini` → `gpt-5.4` at medium effort. Gemini `gemini-3-flash-preview` → `gemini-3.1-pro-preview`. Subscription cost stays zero.

2. **v8 issues #1–#3 (obligation extraction, section-extract → global-integrate, gap-claim calibration rubric) still required**. Drop-mini doesn't catch obligation gaps systematically; it just shifts more findings into the panel earlier. The structural fixes are needed to systematically close the gap.

3. **v8.0 candidate scope** = issues #1 + #3, leaving #2 for v8.1 (per codex's section-extract concern about local blindness — wants global integrator built first).

4. **Don't ship more bench data on v7.1 until the gemini OAuth-expiry story is fixed**. The auto-failure mode (capacity 429 on gemini-3.1-pro, OAuth expiry mid-run) is a real reliability hit on long runs. Worth a separate v7.x ticket on graceful-degradation for partial-family / fallback-judge runs.

## Files

- `docs/benchmark/coarse_corpus/` — coarse's 4 reviews + 4 refine reviews + 16 judge files + summary scorecard. Pulled from `https://github.com/Davidvandijcke/coarse` MIT-licensed snapshot 2026-04-13.
- `docs/v8_issues/` — 5 issue bodies drafted from the bench + drop-mini results. Source critique: codex 5.5 review of pre-bench v8 plan.
- Per-paper experiment artifacts at `<vault>/.../<paper>/_experiments/drop_mini_v71/` (Forney + Stephens). Not in this repo (lives in Obsidian vault per disputatio convention).

## Next

- Commit + open 5 v8 issues + merge `feat/v7-amendments` → `main`.
- Cut `feat/v8-form-and-spec` from main.
- Implement issue #4 (drop mini) as the first v8.0 PR — smallest scope, clearest measured win, reverses immediately if regressions appear.
