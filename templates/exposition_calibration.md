# Exposition calibration prompt (Phase 3e — new)

Process the exposition queue (`_artifacts/json/exposition_queue.json` from Phase 2.7c) into exposition-class panel rows. Distinct from Phase 3g (gap-cal), Phase 3v (claim-validity), Phase 3s (scope/framing), and Phase 5a (quote-supported): this is the **fifth evidentiary contract**, scoped to v1's six structural exposition patterns.

This contract differs from the others in one key way: an exposition finding is a *constructive editorial suggestion*, not a defect claim. The calibrator therefore does not check "does evidence establish a claim of error" — it checks "does the proposed editorial fix close a real reader-friction gap without crossing into taste-level restructuring." The anti-pedantry guard is the load-bearing component.

## Inputs

- `_artifacts/json/exposition_queue.json` — clusters with `integrated_status` ∈ {`unanimous_reportable`, `majority_reportable`, `split_reportable_majority`, `disputed`, `indeterminate_with_majority_signal`} from Phase 2.7c.
- `_paper/paper.md` — for anchor verification and scope-of-fix sanity check.
- Optionally, the obligation / claim-validity / scope-framing ledgers — only consulted when the calibrator is unsure whether a fix crosses into substantive-claim territory (rare).

## Output

For each cluster that survives, emit a panel row with `claim_type: exposition`. Write to `_artifacts/json/exposition_calibrated_rows.json`:

```json
{
  "schema_version": "exposition_calibration_v1",
  "rows": [
    {
      "finding_id": "E001",
      "claim_type": "exposition",
      "pattern_kind": "notation_collision | duplicated_derivation | missing_symbol_table | section_order_dependency | label_mismatch | absent_running_example",
      "concern": "1-2 sentences naming the editorial gap and the fix in the same breath",
      "severity": "material | local | nit",
      "evidence": [
        {
          "quote": "verbatim from paper.md",
          "location": "section / page / equation anchor",
          "why": "1 sentence — what this quote anchors about the pattern"
        }
      ],
      "proposed_change": "the constructive editorial fix (carried from integration's merged_scope_correction)",
      "minimal_text_change": "the smallest textual change implementing the fix",
      "architecture_support": {
        "anthropic": {"supports": true | false, "audit_id": "...", "verdict_called": "..."},
        "openai": {"supports": true | false, "audit_id": "...", "verdict_called": "..."},
        "google": {"supports": true | false, "audit_id": "...", "verdict_called": "..."}
      },
      "calibration": {
        "verdict": "supported_editorial | demoted_partial | dropped",
        "anti_pedantry_pass": "yes | demoted_on_doubt | failed",
        "reader_friction_witness_strength": "strong | adequate | weak",
        "pattern_or_instance": "pattern | borderline_pattern",
        "fix_scope": "concrete_local | concrete_section | borderline_restructure | taste_level",
        "notes": "1 paragraph — load-bearing for the anti-pedantry guard. Specifically address: would a competent referee writing a busy report include this comment, and why."
      },
      "audit": {
        "source_audit_ids": ["EXP_AUDIT_001_a", "EXP_AUDIT_001_b"],
        "integrated_status": "unanimous_reportable | majority_reportable | ..."
      }
    }
  ],
  "drops": [
    {
      "cluster_id": "EXP_C0xx",
      "drop_source": "calibration_anti_pedantry | calibration_taste_level | calibration_resolved_at_anchor | calibration_witness_too_weak | calibration_single_instance",
      "drop_reason": "1-2 sentences"
    }
  ]
}
```

## Rubric — six components

All six must pass for `verdict: supported_editorial`. Components 2 and 3 (anti-pedantry + reader-friction witness) are the load-bearing guards.

### Component 1 — Pattern is real and anchored

Verify each `evidence[].quote` substring-matches `paper.md`. Verify the anchors collectively establish the `pattern_kind` (e.g. for `notation_collision`, at least two anchors showing the symbol used in distinct senses; for `duplicated_derivation`, both derivations anchored).

- **Pass**: anchors present, pattern observable from the quotes.
- **Fail**: anchors don't show what the pattern claims. Drop.

### Component 2 — Reader-friction witness is concrete (load-bearing)

The audit's `reader_friction_witness.concrete_friction` must name a specific cognitive cost the pattern imposes. Generic "this could be clearer" fails. Specific "a reader of Section 6.2 must hold three meanings of Δ in working memory while parsing equation (60)" passes.

- **Strong** — specific equation/sentence + named cognitive cost.
- **Adequate** — specific section + named cognitive cost.
- **Weak** — vague or generic friction claim. Triggers demotion or drop.

### Component 3 — Anti-pedantry guard (load-bearing)

Would a competent referee writing a busy report include this comment? Pose the question concretely:

- Does the pattern occur in a load-bearing part of the paper (setup, main theorem, central proof)?
- Does the cognitive cost to the reader scale with the pattern (more sections = more cost)?
- Is the proposed fix small enough that a copy editor or the author can implement it in a single revision pass?

If all three lean yes: **pass**.
If two of three lean yes and the third is borderline: **demote_on_doubt** — keep the row but demote severity one tier (material → local; local → nit) and tag `anti_pedantry_pass: "demoted_on_doubt"`.
If two or more lean no: **fail**. Drop with `drop_source: calibration_anti_pedantry`.

### Component 4 — Fix is concrete, not taste-level

The `proposed_change` must be implementable. Specifically:

- **`concrete_local`** — change is a few sentences or a notation table; no restructuring. Pass.
- **`concrete_section`** — change is a section-level edit (e.g. add a 2-paragraph summary, move a paragraph, rename a labeled item). Pass.
- **`borderline_restructure`** — change crosses into section-reorder territory but the audit has spelled out the exact reorder with anchors. Pass with `demoted_on_doubt`.
- **`taste_level`** — change requires rewriting from scratch with different structure. Fail. Drop with `drop_source: calibration_taste_level`. V1 of this track explicitly excludes taste-level work.

### Component 5 — Pattern, not instance

For each `pattern_kind`:

- `notation_collision`: at least 2 distinct meanings, each anchored. ≥ 2 = pattern.
- `duplicated_derivation`: at least 2 parallel derivations. = 2 = borderline pattern; ≥ 3 = pattern.
- `missing_symbol_table`: at least 20 symbols across body+appendix, and reader-friction witness names a specific re-lookup. Otherwise fail.
- `section_order_dependency`: a specific traceable dependency, not vague reorder preference. Pass if the dependency is named.
- `label_mismatch`: at least 3 subsequent references to the mis-labeled item. < 3 = single_instance.
- `absent_running_example`: at least 3 appearances of the example. < 3 = single_instance.

A `single_instance` finding drops with `drop_source: calibration_single_instance` and is rerouted to the M0 close-reading track if the orchestrator confirms the single instance is itself a typo or notation slip.

### Component 6 — Paper does not self-handle

If the audit's `paper_self_handling.does_paper_acknowledge == "yes"` AND `is_acknowledgement_adequate == "yes"`, the finding drops with `drop_source: calibration_resolved_at_anchor`. The paper already addresses the friction.

If `partial`: surface with severity demoted one tier; the panel reader can decide whether the partial acknowledgement is enough.

If `no`: pass through.

## Severity assignment

Editorial findings calibrate severity differently from defect findings:

- **`material`** (rare): the pattern blocks a competent reader from following a load-bearing argument. Example: `section_order_dependency` where Section N invokes an undefined object that is the central technical device, and no forward pointer exists. Or `label_mismatch` where the mis-labeled item is the most-cited result in the paper.
- **`local`**: the pattern adds cognitive cost in a specific section but the section is recoverable. Most patterns land here.
- **`nit`**: the pattern is cosmetic — the fix improves polish but a careful reader incurs minimal cost. `missing_symbol_table` on a short paper, `absent_running_example` where the example is introduced in Section 4 (one section late), etc.

Default severity is **`local`**. Promote to `material` only when a careful reader would be substantively blocked. Demote to `nit` when the cost is small.

## Disputed-cluster adjudication

For `integrated_status: disputed` clusters (families disagreed on `pattern_kind`):

- Do NOT majority-vote.
- Adjudicate by anchor strength: which family's `pattern_kind` has the more concrete anchor coverage?
- Adjudicate by witness specificity: which family's `reader_friction_witness` names a more concrete cognitive cost?
- Record the chosen `pattern_kind` and the runner-up in `audit.alternatives_considered`.

If both family interpretations are equally strong and the fixes are different in kind (e.g., one says "add a notation table," the other says "rename the symbol"), pick the less invasive fix. Note the alternative.

## Anti-pedantry — examples of patterns to FAIL

These are common drift patterns the calibrator should reject as `taste_level` or `anti_pedantry_fail`:

- "The paper is long; trim." — without a specific duplication target → `taste_level`.
- "I would have used different notation conventions." — author preference → `anti_pedantry_fail`.
- "Section X could be merged with Section Y to improve flow." — taste-level restructuring without a concrete dependency → `taste_level`.
- "More figures would help." — without a specific equation that would benefit → `anti_pedantry_fail`.
- "A summary table would be nice." — without naming what would go in the table → `anti_pedantry_fail`.

These are real referee comments that don't pass the load-bearing test. The track must reject them.

## Output validation (orchestrator runs)

Before merging the calibrated rows into the panel:

1. Every `evidence[].quote` substring-matches `paper.md`.
2. No row carries severity `material` unless the `calibration.notes` explicitly justifies the promotion against a load-bearing part of the paper.
3. No row has `fix_scope: taste_level` (those should have dropped at Component 4).
4. Drop counts in `drops[]` are surfaced in the panel summary so the system's restraint is visible.

## Where these rows ship

Calibrated exposition rows merge into `panel_rows_candidates.json` alongside main, gap (3g), validity (3v), and scope-framing (3s) rows. The `claim_type: exposition` tag routes them at render time to the panel's exposition section.

The renderer (Phase 6) surfaces exposition findings in a dedicated subsection of the panel and memo titled "Editorial / expositional suggestions" — distinct from the auditor `findings[]` (correctness defects) and from `literature_engagement_findings[]` (citation suggestions).
