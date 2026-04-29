# 2026-04-28 — PR #20 spec reconciliation (post-codex review)

Codex (gpt-5.5) reviewed PR #20 and surfaced five spec-consistency blockers I missed:
phase-ordering contradictions in SKILL.md, missing prompt-substitution placeholders,
stale calibrate.md references to the old "four-way gate" naming, Route B not fully
integrated into Pass 2's trigger set, and M8 mandatory-on-theory/proof being
unauditable from output alone. Codex also reframed the hardcoded `5 surfaces` /
`6 findings` floor in `discover_narrow.md` from "merge blocker" to "wrong shape" —
the floor isn't a floor (second underproduction ships anyway), and the count
violates the global rule against hardcoded thresholds in templates.

Surgical fixes applied to SKILL.md, calibrate.md, emit_tickets.md,
discover_narrow.md, synthesize.md:

- **SKILL.md Phase 3 step 5** — removed v5 "top N (default 8) enter the debate
  phase" budget cut. Replaced with: merge produces panel-row candidates;
  routing is decided downstream by calibration Pass 1 + the two-route gate, not
  by a budget cut.
- **SKILL.md prompt-substitution example** — extended with `{{route}}`,
  `{{claim_under_challenge}}`, `{{three_family_signals}}`,
  `{{holistic_pass_path}}`. Added an explicit preflight rule: unsubstituted
  `{{...}}` aborts; templates omit irrelevant placeholder lines rather than
  leaving the token.
- **SKILL.md historical narrative** — `refined_claim` → `surviving_text` (the
  current synthesizer field name).
- **calibrate.md** — replaced four "four-way gate" strings with "two-route
  gate" / Route A vs Route B framing. Extended Pass 2 trigger set from
  `{prosecution_wins, split, escalate}` to also include Route B
  `consensus_held`. Added explicit "what does NOT enter calibration" entry for
  Route B `consensus_broken` rows.
- **emit_tickets.md track table + retry paragraph** — replaced "minimum 6
  findings per ticket" framing with structural-engagement audit:
  `surface_attempts[]` is checked for (1) high-priority surface coverage,
  (2) M8 outcome on every theory/proof surface, (3) at least one method per
  surface. Failures trigger a single retry; second failure logs and the
  failure surfaces in the panel-render summary so a human reviewer sees the
  gap.
- **emit_tickets.md debate-ticket example** — split into two examples (Route A
  three tickets / Route B two tickets). Updated input path from v5
  `ranked_issues_verified.json` to v6 `_calibration/post_pass1_panel_rows.json`.
  Added `route` field on every ticket so downstream prompt-rendering can
  branch.
- **discover_narrow.md** — removed "exactly 5 priority attack surfaces" and
  "Mandatory minimum: 6 findings" hardcoded thresholds. Replaced with: take
  every `priority: high` AND `requires_deep_engagement: true` surface, extend
  to `priority: medium` if the agent judges the set too thin; engage every
  selected surface until method application is exhausted; do not pad.
  Added `surface_attempts[]` to output schema with `m8_required` /
  `m8_outcome` so a clean M8 trace and a skipped M8 are distinguishable
  downstream. Updated Quality bar to drop the count framing.
- **synthesize.md Route B verdict criteria** — strengthened
  `consensus_broken` requirement from "at least one mode landed
  holds_against" to a three-part conjunction: mode landed AND counter-evidence
  directly falsifies `claim_under_challenge.claim` AND no target drift. A
  fired mode that *weakens* the pinned claim without falsifying it now stays
  on `consensus_held` (calibration Pass 2 narrows it). Cited the 2026-04-17
  F003 over-pruning incident as the documented failure mode.

## Not addressed in this pass

- PR body still says "Modified tracked files (README/SKILL/templates) — not in
  this PR" — needs a separate edit before merge. Documentation hygiene only.
- Bench n=4 / mixed-judge framing in
  `docs/log/2026-04-27_coarse-bench-and-drop-mini.md` — already caveated as
  directional.
- Schema additivity (old `_v7` panels lack new fields) — renderer compatibility
  not verified. Follow-up: spot-test render against an old `_v7` panel.json or
  add a migration helper.
- Codex weekly-cap fragility — known issue per CLAUDE.md; the upgraded
  re-annotator only fires on ~8 polished rows, so cost delta is real but small.
  Real fix is cap-aware graceful degradation, tracked separately.

## Round-2 fixes (post-codex session 150)

Codex re-reviewed the round-1 fixes and flagged additional gaps. Round-2 patches:

- **emit_tickets.md Wave 3** — rewrote with the nine v6 inputs
  (`discover_<family>_<track>.json` × 3 × 3 + `baseline_review.json`); output now
  includes `panel_rows_candidates.json` as canonical alongside the legacy
  `ranked_issues.json` audit artifact.
- **emit_tickets.md Wave 4 verify** — input now `panel_rows_candidates.json`,
  output `panel_rows_candidates_verified.json` (was the v5
  `ranked_issues_verified.json`).
- **templates/verify.md** — rewrote inputs/outputs/budget logic to match v6.
  Removed the v5 budget cut entirely (verify is no longer a router; it's
  evidence for calibration). Refuted rows are NOT auto-dropped at verify time
  — calibration Pass 1 reads `web_verification` and decides.
- **emit_tickets.md / calibrate.md Wave 5a input** — calibration Pass 1 now
  reads `panel_rows_candidates_verified.json` (or
  `panel_rows_candidates.json` if `--skip-web`).
- **emit_tickets.md table at lines 109–113** — input/output paths corrected
  for merge_rank, verify, prosecute, defend, synthesize. Route A vs Route B
  inputs split per row.
- **schemas/panel_row.md** — `dropped_by_red_team` added to `status` enum and
  to the `final_findings.json` shape statement; "four-way gate" → "two-route
  gate" in two cross-references.
- **discover_narrow.md** — closed the contradiction (high-priority surfaces
  may NOT be skipped even if holistic addressed them); added
  `engagement_outcome` field (`finding_emitted | engaged_no_finding`) so
  honest non-theory zero-finding runs are not falsely rejected.
- **emit_tickets.md engagement audit** — tightened so
  `engagement_outcome: finding_emitted` requires `len(issues_emitted) > 0`
  AND every id in `issues_emitted` resolves to a row in `issues[]`.
- **emit_tickets.md row-disposition** — added explicit `not_run` disposition:
  synthesizer route-mismatch failures fall back to `calibration_pass1`
  verdict and ship to the panel (NOT a drop — Pass 1 already vouched for the
  row); failures logged at `_artifacts/sessions/synth_route_mismatch.log`.
- **SKILL.md placeholder list** — extended to closed-set form covering all
  live placeholders across the template tree, with three groupings (general /
  discovery-only / debate-only) and a "reserved" section for `{{mode}}` (not
  yet substituted by any template — render reads engine.mode from
  panel.json).
- **SKILL.md validation rules** — added a Synthesis entry requiring `route` +
  route-correct `verdict` vocabulary + non-empty `surviving_text` on non-drop
  verdicts; mismatched-route verdicts trigger the `not_run` disposition path.
- **merge_and_rank.md / attack_surface_index.md / prosecute.md /
  baseline.md** — bulk replaced "four-way gate" → "two-route gate". The only
  remaining `four-way` string in the tree is the historical reference at
  emit_tickets.md:555 documenting that the duplicate helper was removed.

## Source

`/codex` (gpt-5.5) sessions 148, 150, 152 + Claude review of PR #20.
