# Exposition integration prompt (Phase 2.7c — new)

Cluster per-family exposition audits into a single ledger. Preserve cross-family disagreement verbatim. Forward only the rows that warrant calibration. Same orchestration pattern as `templates/scope_framing_integrate.md` (v8.2) and `templates/claim_validity_integrate.md` (v8.1).

This phase exists because each family runs its own triage + audit independently. Without integration, the panel would either (a) ship three near-duplicate findings per pattern, or (b) silently drop a finding because two of three families agreed and the third disagreement was lost. The integrator clusters by *same pattern attached to same paper artifact* (functional, not lexical), records every family's record, and emits a calibration queue.

## Inputs

Per-family audit outputs from Phase 2.7b:
- `{{exposition_anthropic_path}}` — Claude family audits
- `{{exposition_openai_path}}` — Codex family audits
- `{{exposition_google_path}}` — Gemini family audits

Engine metadata from `_artifacts/tickets.json` (for degraded-mode awareness when a family is blocked).

## Task

Produce two JSON files:

1. **Full ledger** at `_artifacts/json/exposition_ledger.json`. Every cluster including unanimous `resolved_in_paper`, `no_audience_misdirection`, `taste_level_restructuring`, `single_instance_not_pattern`, `indeterminate`. This is the audit trail — never enters discovery or calibration directly.

2. **Calibration queue** at `_artifacts/json/exposition_queue.json`. Only clusters whose `integrated_status` is `unanimous_reportable | majority_reportable | split_reportable_majority | disputed | indeterminate_with_majority_signal`. The downstream Phase 3e calibrator (`templates/exposition_calibration.md`) is responsible for the final ship/drop decision.

Output JSON shape for both files:

```json
{
  "schema_version": "exposition_integrate_v1",
  "engine": {
    "families_present": ["anthropic", "openai", "google"],
    "families_blocked": [],
    "degraded_mode": false
  },
  "clusters": [
    {
      "cluster_id": "EXP_C001",
      "pattern_kind": "notation_collision | duplicated_derivation | missing_symbol_table | section_order_dependency | label_mismatch | absent_running_example",
      "canonical_present_object": {
        "description": "best 1–2 sentence description of the artifact (drawn from the family with the strongest anchor coverage)",
        "anchors": [
          {
            "quote": "verbatim quote from paper.md",
            "location": "section / page / equation anchor"
          }
        ]
      },
      "family_records": [
        {
          "family": "anthropic",
          "audit_id": "EXP_AUDIT_xxx",
          "pattern_kind_as_called_by_family": "notation_collision",
          "verdict_as_called_by_family": "reportable_exposition_finding",
          "scope_correction": "the family's proposed_change verbatim",
          "minimal_text_change": "the family's minimal_text_change verbatim",
          "reader_friction_witness": "the family's reader_friction_witness.concrete_friction verbatim",
          "anti_pedantry_notes": "the family's anti_pedantry_check.notes verbatim",
          "paper_self_handling": "yes | no | partial"
        }
      ],
      "integrated_status": "unanimous_reportable | majority_reportable | split_reportable_majority | unanimous_resolved | unanimous_no_audience_misdirection | unanimous_taste_level | unanimous_single_instance | disputed | indeterminate_with_majority_signal | indeterminate",
      "integrated_status_reason": "1–2 sentences naming why the cluster lands at this status, including which family records weighed how",
      "merged_scope_correction": "the strongest scope_correction surviving integration (drawn from the family record(s) with `reportable_exposition_finding`; if multiple, the most concrete one)",
      "merged_minimal_text_change": "the strongest minimal_text_change surviving integration",
      "alternative_corrections_considered": [
        "scope_correction A (family X) — recorded but not chosen because Y",
        "scope_correction B (family Z) — recorded but not chosen because W"
      ]
    }
  ],
  "drops": [
    {
      "cluster_id": "EXP_C0xx",
      "pattern_kind": "...",
      "drop_reason": "unanimous_resolved | unanimous_no_audience_misdirection | unanimous_taste_level | unanimous_single_instance | unanimous_indeterminate",
      "family_records_dropped": ["audit_id_a", "audit_id_b", "audit_id_c"]
    }
  ]
}
```

The full ledger contains every cluster; the calibration queue contains only the clusters whose `integrated_status` starts with `unanimous_reportable | majority_reportable | split_reportable_majority | disputed | indeterminate_with_majority_signal`.

## How to work

### Step 1 — Pair audits across families

For each per-family audit record, find peer records in the other families that target the **same paper artifact** with the **same pattern_kind**. Match by:

1. **Anchor overlap** — at least one verbatim quote in `present_object.anchors` overlaps (substring match in either direction) with a peer's anchors.
2. **Pattern kind agreement** — both records call it the same `pattern_kind`.
3. **Functional equivalence** — the proposed fix would resolve both records' concerns. If family A proposes "add a notation table" and family B proposes "rename one of the uses," and both target the same colliding symbol, they are the same cluster.

When anchor overlap is absent but pattern_kind matches AND the `present_object.description`s clearly target the same artifact (e.g., both name "the symbol Δ" and the paper has only one major Δ collision), cluster them and note the partial overlap in `integrated_status_reason`.

### Step 2 — Build the canonical present_object

For each cluster, choose the canonical `present_object` from the family record that has the most anchor quotes. If two records tie, prefer the record whose anchors span more sections of the paper.

### Step 3 — Assign `integrated_status`

Apply these rules in order:

1. **`unanimous_reportable`** — all three families called it `reportable_exposition_finding`. The strongest signal.
2. **`majority_reportable`** — two of three families called it `reportable_exposition_finding`, the third gave a drop verdict (e.g. one family said `no_audience_misdirection`). Surface to calibration; the calibrator adjudicates whether the dissent indicates a real over-pedantry risk.
3. **`split_reportable_majority`** — two of three said `reportable_exposition_finding` but the third's verdict is itself uncertain (e.g. `indeterminate`). Surface to calibration with the dissent recorded.
4. **`disputed`** — families disagree on `pattern_kind` (one called it `notation_collision`, another called it `missing_symbol_table` against the same anchor). Or one family said reportable while another said `taste_level_restructuring`. Surface; calibration adjudicates by anchor strength and witness specificity, NOT by majority vote.
5. **`indeterminate_with_majority_signal`** — majority of family verdicts are `indeterminate`, but at least one family gave a reportable verdict with a concrete witness. Surface conservatively.
6. **`unanimous_resolved`** / **`unanimous_no_audience_misdirection`** / **`unanimous_taste_level`** / **`unanimous_single_instance`** / **`unanimous_indeterminate`** — all three families gave the same drop verdict. Drop. Record in `drops[]`.
7. **`indeterminate`** — none of the above patterns match. Conservative drop.

### Step 4 — Choose the merged scope_correction

For clusters that survive to the calibration queue:

- If unanimous reportable: pick the most concrete `scope_correction` across family records; if multiple are equally concrete, pick the one that proposes the least invasive change (the alternative_change field, if any family proposed one).
- If majority reportable: same rule, but only among the family records with `reportable_exposition_finding` verdict.
- If disputed (families disagreed on pattern_kind): record both alternatives in `alternative_corrections_considered`; the calibrator picks the one with the stronger witness.

The merged scope_correction is *not* a new fix invented at integration time — it is always one of the family records' proposals.

### Step 5 — Preserve disagreement

Every family's audit_id, verdict, scope_correction, and anti_pedantry_notes goes into `family_records[]` verbatim — even for drops. The full ledger is the audit trail; nothing is lost.

For `alternative_corrections_considered`, name which family proposed each alternative and the one-sentence reason the integration chose a different one.

## Degraded mode (per v8.0 engine contract)

If a family is blocked (content filter, capacity exhaustion, OAuth expiry), it is missing from `families_present` in `engine`. Adjust the status rules:

- "Unanimous" becomes "all available families agreed."
- "Majority" with only 2 families present = both. If only 1 family is present, treat any single reportable verdict as `indeterminate_with_majority_signal` and surface to calibration with explicit single-family caveat. Single-family findings get extra calibration scrutiny.
- Record degraded-mode awareness in `engine.degraded_mode: true` and surface in the panel-render summary.

## OCR warning

OCR-flagged candidates from any family are dropped at integration time without entering the ledger or queue. Record the drop in `drops[]` with reason `ocr_artifact_dropped_at_integration`.
