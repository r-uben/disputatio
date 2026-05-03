# Claim-validity calibration prompt (v8.1, Phase 3v — new)

Validate **claim-validity audits** — findings that the paper's present formal object does not actually support its asserted property under the paper's own definitions. This calibrator runs as a sub-DAG fed by the v8.1 integrator's calibration queue. It is **distinct** from `templates/calibrate.md` (quote-supported error/overclaim findings) and from `templates/gap_claim_calibration.md` (gap claims about absences).

This phase exists because wrong-but-present claims have a different evidentiary contract from both quote-supported errors and gap claims:

- v7 `calibrate.md` asks: "does the cited quote say what the finding claims?"
- v8.0 `gap_claim_calibration.md` asks: "is the required object actually missing?"
- v8.1 `claim_validity_calibration.md` asks: "given the present object, does the audit's defect actually break the claim under the paper's own definitions?"

Single-stage rubric pass. No satisfaction-check sub-stage (unlike v8.0 gap-cal) because v8.1 candidates already start from present formal objects — there's no existence question to adjudicate before the rubric.

## Inputs

- Single calibration queue entry: `{{queue_entry_path}}`
- Paper text: `{{paper_path}}`

## Task

Produce a single JSON file at `{{output_path}}`:

```json
{
  "queue_entry_id": "CV_GLOBAL_NNN",
  "blind_id": "BV_NNN",
  "rubric": {
    "object_and_property_located": {
      "passes": "yes | partial | no",
      "object_anchor": "where the present formal object lives in the paper",
      "claim_anchor": "where the asserted property is stated",
      "notes": "1-2 sentences"
    },
    "uses_paper_definitions": {
      "passes": "yes | partial | no",
      "cited_definitions": [
        {"name": "...", "location": "...", "verified_at_location": "yes | no | not_checked", "load_bearing": "yes | no"}
      ],
      "verification_coverage": "all | spot_check_50 | spot_check_3 | none",
      "external_machinery_imported": "yes | no",
      "notes": "1-2 sentences. Verification coverage rule: ALL definitions must be verified for any audit headed for reportable_validity_finding. Non-reportable / indeterminate audits verify max(3, 50% of cited_definitions). If any definition tagged load_bearing: yes is unverified or not at claimed location, the audit cannot be reportable regardless of other rubric components passing."
    },
    "local_and_explainable": {
      "passes": "yes | partial | no",
      "scope_of_failure": "what the failure invalidates — narrow region of the paper, single proof step, single conclusion",
      "explainable_in_two_sentences": "yes | no",
      "notes": "if no: the audit is too sprawling to be a clean panel row"
    },
    "minimal_witness": {
      "passes": "yes | partial | no",
      "witness_kind": "counterexample | redefinition | computation | unanticipated_case | derivation_break",
      "witness_concrete": "yes | partial | no — is the witness a specific construction or a vague gap?",
      "witness_within_paper_setup": "yes | no — does the witness use only the paper's own setup?",
      "notes": "if witness is vague or relies on external setup: rubric fails here"
    },
    "scoped_to_invalidation": {
      "passes": "yes | partial | no",
      "scoped_consequence": "what the audit invalidates and what it does NOT invalidate",
      "audit_does_not_blanket_condemn": "yes | no",
      "notes": "audit must not say 'the proof is wrong' when only one step is wrong"
    },
    "benign_interpretation_rejected": {
      "passes": "yes | partial | no",
      "charitable_reading_considered": "1-2 sentences naming the most charitable reading",
      "why_charitable_reading_does_not_save": "1-2 sentences on why the charitable reading does not actually apply",
      "notes": "if charitable reading would save the claim and audit doesn't address why not, rubric fails"
    }
  },
  "verdict": "reportable_validity_finding | resolved_audit_overclaim | charitable_reading_holds | hallucinated_definitions | inadequate_witness | indeterminate",
  "verdict_notes": "1-3 sentences on the disposition rationale",
  "panel_row_payload": {
    "concern": "1-sentence statement of the wrong-but-present finding, used as panel-row concern",
    "category": "proof | empirics | identification | framing | robustness | interpretation | notation | other",
    "claim_type": "validity",
    "failure_class": "validity_failure | support_mismatch",
    "severity": "material | local | nit",
    "failure_mode": "the consensus or selected failure_mode from the audit",
    "minimal_formal_correction": "the smallest concrete edit to the paper that would resolve the failure (carried over from audit)",
    "obligation_id": "v8.0 cluster ID if anchored, null otherwise",
    "formal_object_id": "stable cross-phase identifier",
    "source_phase": "v8.1",
    "evidence": [
      {
        "quote_or_paraphrase": "the asserted property the paper makes",
        "location": "claim_anchor",
        "support_type": "direct_quote | paraphrase | derived_inference",
        "role": "asserted_property"
      },
      {
        "quote_or_paraphrase": "the present formal object",
        "location": "object_anchor",
        "support_type": "direct_quote | paraphrase | derived_inference",
        "role": "present_object"
      },
      {
        "quote_or_paraphrase": "the minimal witness — counterexample / redefinition / computation",
        "location": "where the witness is constructed",
        "support_type": "derived_inference",
        "role": "witness"
      }
    ],
    "suggested_action": {
      "author": {"fix": "the minimal_formal_correction — re-state the claim narrower, repair the proof step, add the missing condition, swap to a different formal object that actually supports the claim"},
      "referee": {"how_to_use": "how a referee would phrase this concern in a letter — what to ask the author"}
    }
  }
}
```

`panel_row_payload` is populated only when `verdict == reportable_validity_finding`. Otherwise it is `null`.

## How to work

### Single-stage rubric

The six rubric components evaluate in order. **All six must pass** (not partial, not no) for `verdict: reportable_validity_finding`. Any single failure shifts the verdict.

#### 1. Object and property located

Both the present formal object and the asserted property must be locatable in the paper at specific anchors. If the audit cites Theorem 1 but the paper has no Theorem 1, fail. If the audit names a property the paper does not actually claim, fail.

#### 2. Uses paper definitions (anti-hallucination)

The audit must cite paper-internal definitions only. Verification coverage depends on the audit's likely outcome:

- **For audits headed for `reportable_validity_finding`**: verify **all** entries in `cited_definitions[]`. Every load-bearing definition (those the audit's `required_inference` actually depends on) must be verified at its claimed location.
- **For non-reportable / indeterminate audits**: verify at least `max(3, 50% of cited_definitions)`. Spot-check covers the most-cited or most-load-bearing entries first.

For each cited definition, set `verified_at_location: yes | no | not_checked` and `load_bearing: yes | no`.

**Hard rule**: if any definition tagged `load_bearing: yes` is unverified (`verified_at_location: no` or `not_checked`), the audit **cannot** be reportable regardless of other rubric components passing. Verdict becomes `hallucinated_definitions` (if a load-bearing cite is `no`) or `indeterminate` (if a load-bearing cite is `not_checked` and verification was prevented by access/filter).

**External machinery flag**: if the audit's `required_inference` relies on machinery the paper doesn't define (e.g., a measure-theoretic concept the paper never uses), `external_machinery_imported: yes` and the rubric fails → verdict: `hallucinated_definitions`.

This rule prevents a finding from standing on invented local terminology. The cost (verifying all cited definitions for reportable audits) is bounded — a typical audit cites 2–5 definitions, and the verification quote-match against the paper is mechanical.

#### 3. Local and explainable

A reportable validity finding affects a bounded scope (one proof step, one corollary, one regime). If the audit's `consequence_if_wrong` blanket-condemns ("the entire proof is invalid"), fail. The audit must explain the failure in 1–2 sentences without resorting to a sprawl of qualifiers.

#### 4. Minimal witness

The witness must be:
- **Concrete**: a specific construction, computation, or counterexample — not "the proof has a gap somewhere."
- **Within the paper's own setup**: uses the paper's own variables, definitions, examples. External counterexamples (papers from other fields, hypothetical models the paper doesn't consider) don't count.
- **Categorized**: assign `witness_kind` (counterexample / redefinition / computation / unanticipated_case / derivation_break).

Fail → verdict: `inadequate_witness`.

#### 5. Scoped to invalidation

The audit must distinguish what it invalidates from what it does not. If audit says "Theorem 1 is wrong" when actually only the case w<0 fails, the audit must scope to "Theorem 1 fails for w<0; the w>0 case is unaffected."

This component prevents the gotcha pattern: blanket-condemning a proof when one step is wrong.

#### 6. Benign interpretation rejected

The most charitable reading of the paper that would save the claim must be considered explicitly. The audit must explain why that charitable reading does not apply. If the charitable reading would actually save the claim and the audit doesn't address it, fail → verdict: `charitable_reading_holds`.

This is the anti-pedantry guardrail — many papers compress notation or rely on conventions readers are expected to fill in.

### Verdicts

Six possible outcomes:

- **`reportable_validity_finding`** — all six rubric components pass. Populate `panel_row_payload`. Severity:
  - **`material`** if the failure invalidates a load-bearing claim (theorem, main proposition, headline empirical conclusion).
  - **`local`** if the failure narrows but does not break a result (e.g., theorem holds for w>0; w<0 case fails).
  - **`nit`** if the failure is cosmetic (notation collapse, dimensional inconsistency that's mechanically inferable).

- **`resolved_audit_overclaim`** — rubric components 1–5 pass; component 6 fails because the charitable reading saves the claim. The audit was over-aggressive. Drop.

- **`charitable_reading_holds`** — equivalent to above, used when the charitable reading is the dominant reason. Drop.

- **`hallucinated_definitions`** — component 2 fails. The audit cited a definition that is not at its claimed location, or imported external machinery. Drop with strong note in `verdict_notes` — repeated hallucinations across audits indicate the family's prompt needs revision.

- **`inadequate_witness`** — component 4 fails. The witness is vague, external, or non-concrete. Drop.

- **`indeterminate`** — components 1, 3, or 5 fail in ways that prevent decision (e.g., audit's `claim_anchor` is ambiguous; OCR garble at the object location; scope-of-failure is genuinely unclear from the paper). Drop.

### Severity calibration for reportable validity findings

Three tiers:

- **`material`** — the failure means a load-bearing claim from the abstract or intro does not hold under the paper's own definitions. The reader's takeaway is wrong without the audit.
- **`local`** — the failure narrows a result. The reader who relies on the broader claim is misled; the reader who relies on the narrower claim is fine.
- **`nit`** — cosmetic. Notation collapse, dimensional inconsistency, terminology slip that doesn't change the math.

### Disputed entries

If the queue entry has `queue_state: disputed` (families disagreed on `validity_status`), the calibrator does **not** majority-vote. Instead:

- Inspect each family's audit and witness.
- Decide which audit's reasoning holds under the paper's own definitions.
- If one family's witness is genuinely concrete and uses only paper machinery, and another family said `valid` but didn't engage with that witness, the disputed entry resolves toward the audit with the stronger witness.
- If both audits rely on different aspects of the same object and both have concrete witnesses, this is `same_object_different_defects` from the integrator — calibrate the audit with the stronger witness; drop the weaker as `inadequate_witness`.

### Same-object-different-defects

Special case: integrator marked the cluster `same_object_different_defects` (families agree there's a problem but disagree on `failure_mode`). Calibrator:

- Adjudicate which `failure_mode` actually holds under the paper's own definitions.
- Ship the panel row with the consensus or stronger-witness `failure_mode`.
- Record in `verdict_notes` that the alternative failure_mode was considered and rejected.

## What this template does not do

- It does not run on quote-supported findings. Those go through `templates/calibrate.md`.
- It does not run on gap claims. Those go through `templates/gap_claim_calibration.md`.
- It does not generate audits. Inputs come from the v8.1 integrator queue.
- It does not interact with the v7 attack-surface index, debate gates, or method-based discovery directly. Validity-class panel rows merge with method-based rows in Phase 6 panel compilation.

## Volume budget

Per paper:
- Calibration queue input: 4–10 audits (per integrator's spec).
- Reportable validity findings shipped: 1–4 expected on a careful paper, more on a paper with systematic correctness issues.
- High `hallucinated_definitions` rate (>10% of queue) suggests the audit prompt is too generative — revise.
- High `charitable_reading_holds` rate (>30%) suggests the audit prompt is too aggressive — revise.

If every queued audit becomes a reportable finding, you're rubber-stamping. If zero queued audits become reportable on a paper that has genuine correctness issues, the rubric is too strict.
