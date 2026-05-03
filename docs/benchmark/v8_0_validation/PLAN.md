# v8.0 validation bench plan

**Pre-registered before any v8.0 runs.** Documents the harness, success criterion, and manual-audit checklist so the experiment can't be moved after the fact.

## Goal

Answer two questions:

1. **Does v8.0 beat v7.1 on the 4-paper bench corpus**, judged on the same rubric coarse uses (gemini-3.1-pro single judge against refine.ink reference, 4 axes)?
2. **Does the gain come from coverage/depth/formal-spec recovery**, not from specificity polish or rubric noise?

The release gate is "v8.0 beats v7.1." The aspirational target is "v8.0 matches or beats coarse" — but that target is **not** the gate. With n=4, flaky judge availability, and mixed-model substitution risks, requiring "beats coarse" is too brittle and would either suppress real wins or force scoreboard chasing.

## Method

Hybrid harness per codex sess 30 turn 5:

### Pure-addition test (J) — all 4 papers

For each paper, take the existing v7.1 panel artifacts and run **only** the new v8.0 phases on top:

1. Phase 1.5a — per-family obligation extraction (`templates/obligations.md`)
2. Phase 1.5b — obligation integration (`templates/obligation_integrate.md`)
3. Phase 3g — gap-claim calibration (`templates/gap_claim_calibration.md`)
4. Append calibrated `claim_type: gap` rows to the existing v7.1 panel
5. Re-render referee_memo via gemini-3.1-pro
6. Re-judge against refine.ink with the same prompt used in the v7.1 bench

Cost per paper: ~30–45 min. Tests the marginal contribution of the obligation pass.

### Full v8.0 run (K) — Stephens only

Run the entire pipeline end-to-end on Stephens at v8.0. Stephens is the right clean datapoint because it is failure-rich, formal-spec-heavy, and already showed v7.1 improvement without closing the gap to coarse. **Do not run K on Forney** — Forney is too easy and near ceiling; a full run there mostly tests plumbing.

Cost: ~3 hours.

### Sanity check

Compare Stephens pure-addition (J) vs Stephens full (K) results. If they materially diverge — different finding sets, different judge scores, different severity distribution — the other three J results are reported as "marginal obligation-pass evidence" not "full v8.0 evidence." If they converge, J on all 4 stands as the v8.0 measurement.

## Papers in scope

| Paper | v7 baseline (gemini judge vs refine) | v7.1 (measured) | v8.0 method |
|---|---|---|---|
| Galeotti, Golub & Goyal 2020 | 5.5 | not measured | J |
| Stephens & Donnelly 2000 | 4.5 | 3.5 (codex judge) | J + K |
| Van Vreeswijk & Sompolinsky 1998 | 4.5 | not measured | J (anthropic blocked → 2-fam at obligation phase) |
| Forney 1988 | 5.0 | 5.5 | J |

## Judge protocol

Same as v7.1 bench:

- Judge: gemini-3.1-pro-preview, single mode
- Reference (Review A): refine.ink published review per paper
- Subject (Review B): disputatio v8.0 referee_memo
- Rubric: coverage / specificity / depth / consistency, 1–6 each
- Output: JSON with overall_score (mean of 4), per-dim score + reasoning, strengths, weaknesses

If gemini OAuth expires mid-run, fall back to codex/gpt-5.4 judge **on both v7.1 and v8.0 of the same paper** to keep within-judge comparison clean. Cross-judge comparisons are not reported.

## Success criterion (release gate)

All four conditions must hold for v8.0 to ship:

1. **v8.0 mean ≥ v7.1 mean** on the 4-paper corpus (same judge protocol per paper).
2. **Gain concentrated in coverage and depth**, not specificity or consistency. Specifically: coverage and depth dimensions improve on at least 3 of 4 papers; specificity and consistency neutral or improving.
3. **Recovery on coarse-only misses**: manual audit of calibrated gap claims must show v8.0 recovers a meaningful subset of issues coarse caught and v7 missed (kernel definitions, MH/complete-data densities, ascertainment-style obligations). At least 3 such recoveries across the 4 papers.
4. **Stephens K does not underperform Stephens J** by more than 0.3 on overall_score (sanity check that wiring matches addition).

If any of (1)–(4) fails, v8.0 does **not** ship as-is. Findings get logged, design gets revised, retry.

## Manual-audit checklist

For each calibrated gap claim that ships in a v8.0 panel:

- [ ] Burden evidence is genuine — paper actually claims/uses the object
- [ ] Required object (Y) is correctly identified — would a competent reader actually need Y?
- [ ] Search trail covers the obligation's natural homes for this paper
- [ ] No "unsupported absence" claims — every reportable_gap has a concrete defect_if_any
- [ ] Severity is calibrated — material only if a load-bearing claim breaks
- [ ] Paraphrased evidence (degraded mode) is honest — no hallucinated content

If audit finds >20% of shipped gap claims have a defect from the above checklist, v8.0 fails the audit gate even if it passed the score gate. Quality of restraint is part of v8.0's value proposition; sloppy gap claims would undercut it.

## Caveats (pre-acknowledged)

1. **n=4** papers. Insufficient for a strong statistical claim. v8.0 evidence is directional.
2. **Same-judge constraint** depends on gemini-3.1-pro-preview availability. OAuth expiry / capacity 429 may force codex fallback on a subset of papers.
3. **Two paper-level confounds carry over from v7.1 bench**: Galeotti was originally run in `--mode author` not `--mode referee`; van Vreeswijk had Anthropic content-filter blocking and ran 2-family. v8.0 does not change these.
4. **Coarse comparison** uses coarse's published gpt-5.4-high run (single variant) against the same refine reference. Coarse has 4 model variants; we are not testing against all.
5. **Self-judging risk**: gemini-3.1-pro-preview is the judge AND a v8.0 family at obligation extraction. The judge sees the family it scored. Cross-system evaluation has this issue too — coarse uses the same judge for itself — so the comparison stays apples-to-apples.

## Reporting template

A docs/log dev entry on completion:

- Per-paper score table: v7 / v7.1 / v8.0 (J or J+K) / coarse, per-dim breakdown
- Stephens J vs K convergence
- Calibrated gap claims that recovered coarse-only misses (with paper IDs)
- Manual-audit findings
- Pass/fail per release-gate condition (1)–(4)
- Decision: ship v8.0 / revise / abandon

## What this plan does NOT validate

- The full adversarial benchmark expansion (#19) — that's v8.1 work, not v8.0 release gate.
- v8.0 performance on papers outside the bench corpus — first production run after merge will be the real-world test.
- Long-run reliability under OAuth/capacity churn — v7.1 bench already exposed this; v8.0 inherits the same operational fragility.

## Concrete next actions

1. Run J on Galeotti — start with the easiest path (paper exists, v7 panel exists, no anthropic blocking).
2. Run J on Forney — second-easiest, results expected near ceiling.
3. Run J on Stephens — formal-spec-heavy, expected biggest gain.
4. Run J on van Vreeswijk — 2-family obligation phase due to anthropic content filter; tests graceful-degradation contract end-to-end.
5. Run K on Stephens — full v8.0 run for sanity check.
6. Score all 5 results with gemini-3.1-pro-preview judge.
7. Manual-audit each shipped gap claim.
8. Write up findings against this plan's release-gate conditions.
9. If pass: open v8.0 PR closing #15, #16 (stripped), #17. If fail: revise design.

Total budget: ~6 hours wall clock + ~1 hour audit + 30 min write-up. Doable in one session if everything goes smoothly; more realistically split across two sessions to absorb gemini auth churn.

## Bench order across v8.x layers (per codex turn 9 revision)

**Strictly sequential for the first slice; parallel after the first integration is verified.**

1. **Run v8.0 in full** per the steps above. Decide ship/revise per the release gate.
2. **Run a small v8.1 bench on the v8.0 ledger** (one paper, e.g., Stephens) and inspect whether the validity ledger shape is stable — does the integrator emit the expected cross-phase IDs, do the calibrator's verdicts cluster sensibly, does the shape match what v8.2 will need to consume?
3. **If v8.1 ledger shape is stable**, v8.2 can run in parallel with broader v8.1 bench. v8.2 mainly needs v8.0 anchors and can optionally consume v8.1 outcomes.
4. **If v8.1 ledger shape needs revision**, hold v8.2 bench until v8.1 is stable. Otherwise v8.2 may bake in incompatible ledger references.

The risk this orders against: if v8.1 reveals integration changes that v8.2 should reuse (e.g., a new anchor format, a different cluster_id scheme, a missed field), running v8.2 in parallel with v8.1's first integration would force later schema migration. One-shot serialization avoids that.
