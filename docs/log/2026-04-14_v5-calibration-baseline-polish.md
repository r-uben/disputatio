# 2026-04-14 — v5 redesign: calibration + baseline + polish + merge atomicity + M5 tighten

## Why

The 2026-04-14 v4 run showed the brutal-dialectic redesign worked structurally (real verdict mix: 5 defense_wins, 3 split, 1 prosecution_wins, 0 converged, vs v3's 8/8 converged) but produced a **worse calibrated report**:

- v4 overclaim rate on the 16 report-entering findings: **56.2%** (v3 full-pool: 18%, v3 debated top-8: 37.5%)
- v4 partial-quote rate: **18.8%** (v3: ~5%)
- The ONE material concern (merged_027 OA3.3 "general cost") was annotator-flagged overclaimed because the prose truncated the paper's own "as long as the budget is small" qualifier.
- 8 of 13 settled findings were flagged overclaimed — they shipped raw from merge_rank with no polish pass.
- Separately, v4 missed a textbook M5 finding (Section 5 "incomplete information" title vs footnote 23 "complete information" admission) that coarse.ink's single-shot opus caught. Post-hoc: discovery *did* surface it (claude_m2) but merge over-clustered it into `merged_012` (Prop 3 LQG-relabelling) and the Section-5 framing finding died when `merged_012` got `defense_wins`.

Diagnosis: the brutal redesign correctly routed strong-consensus issues away from debate's closure ritual, but that ritual had been doing unacknowledged polish work — softening overclaimed raw language into narrower `refined_claim` text. Removing it removed the softener. Plus merge_rank was over-clustering across discovery families, losing atomic findings.

## Goal

Beat coarse.ink on the same paper — measurably, with the provenance + verification that coarse can't offer. Coarse advantages we need to neutralise: tighter prose, end-to-end opus writing, simpler output. Disputatio advantages to preserve: verification, cross-architecture corroboration, auditability, dropped-claim transparency.

## What changed (v5, this branch)

### 1. merge_and_rank.md — atomicity hardened + baseline-diff step

**Step 2b (atomicity) now has enforced rules, not aspirational ones.** Verbatim-quote rule: every merged issue's `quote` must be an exact substring of `_paper/paper.md` (post whitespace normalisation). Orchestrator runs a mechanical validator after merge_rank and rejects any issue whose quote does not substring-match. One-cluster-one-concern rule: "touches the same section" is not a valid clustering criterion. Split triggers are explicit: non-overlapping quotes, different proposed fixes, claims connected by "and" that span two propositions.

**Step 2c (new) — baseline-diff coverage check.** After merge but before ranking, diff the baseline_review.json against the merged set. Baseline-unique findings get appended as new debate-status merged issues at rank 8. Catches anything merge lost to over-aggregation.

### 2. calibrate.md (new) — Phase 4 pre-publication calibration

Replaces post-hoc evaluation as the primary calibration loop. Every candidate report-entering finding runs through a blinded per-finding annotator (codex/gpt-5.4-mini default; sonnet fallback) with the same two-axis rubric as `templates/evaluate.md` (`quote_verified` × `calibration`). Disposition rules are demote-on-doubt:

- `quote_verified: no` OR `calibration: unsupported` → drop.
- `quote_verified: partial` OR `calibration: overclaimed` → one rewrite attempt via gemini-3.1-pro-preview polish, re-annotated; if still fails → drop or demote one tier.
- `supported` + `yes` → pass through.

Calibration writes `_calibration/final_findings.json` which becomes the only input to the final-report ticket (replaces `ranked_issues_verified.json` in that role). Expected overclaim rate in the final report: **<15%** (vs v4's 56%).

### 3. baseline.md (new) — coarse-style single-shot safety net

One extra ticket in Wave 2, runs alongside discovery: a single-shot opus referee review of the paper text alone. Prompt deliberately mimics the coarse.ink generic "write me a referee report" shape. At merge time, the orchestrator diffs baseline themes/comments against the merged set using three matching rules (same quote, same location + semantic match, opus yes-match). Baseline-unique findings are force-injected as debate-status merged issues. Cost: ~$2-3 per run. Protects against both discovery misses and merge over-aggregation.

### 4. polish.md (new) — Phase 5.5 editorial gemini writer

One gemini-3.1-pro-preview call per surviving report entry. Rewrites `surviving_text` (or raw merge claim for settled issues) into one paragraph of referee-letter prose. Preserves every fact, quote, and location; changes only sentence structure, word choice, and transitions. Output: `4_report/polished/<true_id>.md`. Render step assembles these into `referee_report.md` by tier. Closes the prose-quality gap vs coarse (coarse's advantage was end-to-end opus writing; we now give gemini the same end-to-end writing role, constrained to not change facts).

### 5. methods/m5_immanent.md — scope-mismatch checklist

Added Step 2b with an explicit checklist the discovery agent walks for every paper: section title vs body, abstract promise vs theorem conditions, footnote vs body, intro narrative vs formal statement, generality promise vs extension scope, caption vs figure content, "generic / technical" labels vs actual effect. The Section-5 framing finding v4 missed is exactly the "section title vs body" checklist item.

### 6. SKILL.md — phase renumbering, decision table updated, model routing updated

Phases are now:
- 0 Orientation
- 1 Discovery (+ parallel baseline ticket)
- 2 Merge/rank/verify (with atomicity validator + baseline-diff step)
- 3 Debate
- **4 Calibration (NEW)**
- **5 Final report (+ 5.5 gemini editorial polish)**
- 6 Post-hoc A/B evaluation (only on user request)

Model routing updated: Phase 4 calibrate annotator = codex/gpt-5.4-mini default; Phase 5.5 editorial polish = gemini-3.1-pro-preview.

### 7. emit_tickets.md — wave numbering

- Wave 2: 18 discovery + 1 baseline_review.
- Wave 6.5 (NEW): calibration sub-DAG.
- Final wave: final_report ticket consumes `_calibration/final_findings.json`, followed by parallel polish tickets.
- Wave 7: renamed to A/B evaluation, made optional (only on user request).

## Files touched

- `templates/merge_and_rank.md` (~80 lines added: atomicity enforcement, Step 2c baseline-diff)
- `templates/methods/m5_immanent.md` (~20 lines added: Step 2b scope-mismatch checklist)
- `templates/calibrate.md` **new**
- `templates/baseline.md` **new**
- `templates/polish.md` **new**
- `SKILL.md` (phase descriptions, decision table, mkdir, model routing, workspace diagram)
- `templates/emit_tickets.md` (Wave 2 baseline ticket, Wave 6.5 calibration, polish tickets)

## What did NOT change

- Orientation prompts (unchanged).
- Discovery prompts (except M5 — scope-mismatch checklist added).
- Debate prompts — the v4 brutal-dialectic prosecute/defend/synthesize templates stand. The debate stage is correctly routing via status; the fix is downstream of debate, not in debate itself.
- Ranking formula (`rank_score = centrality + 2×cross_agent_support + evidence_specificity + severity`) and status assignment (settled/debate).

## Expected v5 outcomes on Galeotti-Golub-Goyal 2020

Predictions (run v5 on the archived v4 workspace to test):

- **Overclaim rate in final report: <15%**, probably 10-12%. Down from v4's 56%. Driver: Phase 4 calibration demotes the 8 overclaimed settleds to appendix or drops them; polish rewrites the 1 overclaimed material concern to remove the truncated qualifier.
- **Partial-quote rate: <5%.** Driver: merge atomicity validator rejects partial-quote clusters at write-time.
- **Section 5 framing finding: surfaced.** Either M5 scope-mismatch checklist catches it directly, or claude_m2 still catches it and merge now splits the cluster rather than burying it, or the baseline_review catches it and Step 2c forces it into debate.
- **Non-symmetric SVD diagonalization gap (coarse-unique in v4): surfaced.** baseline_review catches it independently if M4/M5 don't.
- **Prose quality: parity with or above coarse.** Gemini 3.1-pro polish rewrites each entry into editor-grade paragraphs; coarse's advantage was end-to-end model writing, which we now match.

Cost delta per run vs v4: ~+$5 (baseline ~$3, polish ~$1-2, calibration ~$0.5-1). Time delta: +~10-15 minutes (baseline and polish run in parallel, calibration is a sub-DAG of 16 small calls at concurrent=4).

## Next test

Run v5 on `/tmp/galeotti-golub-goyal-2020.pdf` (reusing the archived mistral OCR and orient_claude.json). Measure:
- Phase 4 overclaim rate pre-demote vs post-demote.
- Baseline coverage rate (% of baseline items that matched a merged issue).
- Post-polish post-hoc overclaim rate (should be very low).
- Report prose quality side-by-side vs coarse's claude entry (`/tmp/coarse-reviews/claude.md`).

If v5 meets the predictions above, the redesign is done and we can pin a release tag. If any prediction misses by >5 points, diagnose and iterate before pinning.
