# 2026-05-19 — Expositional craft track (closes #39)

## Why

Third of three gaps surfaced by the Han-Hu-Zhang vs AER Ref #2 comparison (#33). Ref #2 had 8 "Other comments" about paper craft — section ordering, Claim→Lemma renaming, inequality unification, symbol-table-for-overloaded-delta, length trim, running-example placement. Anthony's public evaluation (2026-05-19 tweet) singled out "great expositional comments" as the property of Ref #2 that made the report valuable.

Disputatio's pre-#39 taxonomy had no slot for "the paper would read better if X." The evidence compiler requires a verbatim quote *of something wrong*; craft suggestions are "current state is fine but Y would be better" — wrong shape for the rubric.

## Codex review framing (pre-#39, high effort)

> "The hard part is real: the current system is built around falsifiable defect claims with quote-backed support. [...] But you do NOT need to treat that as unprecedented architectural surgery. The repo already accepts multiple evidentiary contracts for different failure modes, e.g. scope/framing gets its own calibrator precisely because quote-verification alone is the wrong rubric (`scope_framing_calibration.md`). So the right conclusion is not 'impossible under disputatio,' it is 'fifth contract, if justified.'"

And on scope:

> "'Exposition' is too broad. Split it. Easy-ish subset: notation collisions, duplicated derivations, missing symbol tables, section-order dependency mismatches, label mismatch (Claim that functions as a lemma), absent running example despite repeated abstract references. Hard subset: taste-level restructuring advice. Ship only the first subset if you do this. Otherwise you will build a pedantry generator."

## What this commit ships

Four templates following the v8.2 `scope_framing` pattern:

- **`templates/exposition_triage.md`** (Phase 2.7a) — per-family selection of 4–8 audit candidates from the 6 patterns; mandatory `dropped_because[]` listing the explicit "anti-pedantry catalog" of common temptations the track refuses to surface (taste-level restructuring, minor typos handled by M0, single instances, already-handled-in-paper, length/style complaints, author preference disagreement).

- **`templates/exposition.md`** (Phase 2.7b) — per-family audit producing `scope_correction` (concrete fix + minimal text change + alternative), `reader_friction_witness` (named cognitive cost, not "could be clearer"), `paper_self_handling`, and the load-bearing `anti_pedantry_check`. Per-pattern audit-note guidance is spelled out for each of the six pattern kinds.

- **`templates/exposition_integrate.md`** (Phase 2.7c) — cluster audits across families by *same paper artifact + same pattern_kind* (functional, not lexical). Preserves cross-family disagreement verbatim. Two outputs: full ledger + calibration queue. Same `engine.degraded_mode` handling as v8.0/8.1/8.2.

- **`templates/exposition_calibration.md`** (Phase 3e) — six-component rubric, all must pass for `verdict: supported_editorial`. Components 2 (reader-friction witness specificity) and 3 (anti-pedantry guard) are load-bearing. Demote-on-doubt fallback for borderline anti-pedantry. The track explicitly classifies the proposed fix on a four-tier scale (concrete_local / concrete_section / borderline_restructure / taste_level); taste-level fails outright.

Integration:

- **`SKILL.md`** — new Phase 2.7 (three sub-waves) + Phase 3e entries between scope-framing (2.6/3s) and Phase 4 debate. Documents the contract difference: exposition is a constructive editorial suggestion, not a defect claim; the calibrator checks "does the fix close a real reader-friction gap without crossing into taste-level restructuring" rather than "does evidence establish a claim of error."

- **`templates/emit_tickets.md`** — Wave 2.7 sub-DAG (3 triage tickets parallel → 3 audit tickets parallel → 1 integration ticket) + Phase 3e calibration sub-DAG. Uses codex/`gpt-5.4` (full, not mini) for calibration per the same rationale as the post-polish upgraded re-annotator in `templates/calibrate.md` — anti-pedantry adjudication requires more than rubric-bounded mini reads.

## V1 scope — the six patterns (hard line)

1. `notation_collision` — same symbol, ≥ 2 distinct meanings, no notation table or local redefinition.
2. `duplicated_derivation` — ≥ 2 parallel proofs with identical structural steps.
3. `missing_symbol_table` — ≥ 20 distinct symbols, no notation section, documented reader-friction.
4. `section_order_dependency` — specific traceable forward-reference (not vague reorder preference).
5. `label_mismatch` — "Claim" used ≥ 3 times as load-bearing lemma.
6. `absent_running_example` — example appears ≥ 3 times across the paper, introduced late.

## V1 deliberately out of scope (anti-pedantry firewall)

- Taste-level restructuring ("Section X should be rewritten")
- Single instances of a pattern (= 1 occurrence; rerouted to M0 close-reading)
- Length critique without a specific duplication target
- Author-preference disagreements about conventions
- Writing-quality complaints unrelated to mathematical exposition
- "More figures would help" / "A summary table would be nice" without specific anchors

The triage template's `dropped_because.drop_reason` enumeration carries this list as a hard schema constraint. The audit template's `anti_pedantry_check` field, plus the calibrator's Component 3, enforce it at audit + ship time.

## What this commit does NOT ship

Deliberately out of scope; tracked for separate work:

- **Render integration.** `templates/render_panel.md` needs a section titled "Editorial / expositional suggestions" surfacing `exposition_calibrated_rows.json` separately from the main `findings[]` table. Tracked as a render follow-up.
- **Panel-row schema update.** `templates/schemas/panel_row.md` may need a `pattern_kind` field on rows with `claim_type: exposition` — TBD whether the existing schema already handles this via the `category: other` slot. Smoke test on Zhang will clarify.
- **Inline calibration smoke test on Zhang.** This commit defines the protocol; running it against Zhang's existing workspace is a separate measurement step.

## Test plan

- [ ] Run Phase 2.7 + Phase 3e on the Zhang workspace once the orchestrator wires the new templates.
- [ ] Measure how many of Ref #2's 8 "Other comments" the track surfaces. Target: ≥ 3 of the structural ones (the "delta" symbol overload, the Claim→Lemma rename, the inequality unification — though the last is closer to a unification suggestion than a v1 pattern; may fail the witness-specificity test).
- [ ] Run on a paper with no obvious expositional issues (a well-written control). Target: ≤ 1 finding (zero is the clean outcome; one is acceptable false-positive rate).
- [ ] Manually inspect the calibration drops to verify the anti-pedantry firewall is rejecting taste-level suggestions and single-instance noise.

## Files

- `templates/exposition_triage.md` (new)
- `templates/exposition.md` (new)
- `templates/exposition_integrate.md` (new)
- `templates/exposition_calibration.md` (new)
- `SKILL.md` — Phase 2.7 + Phase 3e entries
- `templates/emit_tickets.md` — Wave 2.7 + Phase 3e wave definitions

## Sequencing

Independent of #33 (literature engagement), #34 (ClaudeSpec), #38 (quant-anchoring). Can merge in parallel.

Critical path per codex's 2026-05-19 follow-up review: this track is the **next feature** (after validating #33 on Zhang) on the path to Anthony-quality review. #34 ClaudeSpec is infrastructure; #38 quant-anchoring is lower-density and risks the "BS extensions" failure mode Anthony explicitly disliked.
