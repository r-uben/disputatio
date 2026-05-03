# Scope/framing calibration prompt (v8.2, Phase 3s — new)

Validate **scope/framing audits** — findings that the paper's narrative claim overreaches what the formal evidence inside the paper actually establishes. This calibrator runs as a sub-DAG fed by the v8.2 integrator's queue. Distinct from v7 `calibrate.md`, v8.0 `gap_claim_calibration.md`, and v8.1 `claim_validity_calibration.md` — fourth evidentiary contract.

This phase exists because narrative-vs-formal mismatches have a different evidentiary contract from quote-supported errors, gap claims, or wrong-but-present errors:

- v7 `calibrate.md` — "does the cited quote say what the finding claims?"
- v8.0 `gap_claim_calibration.md` — "is the required object actually missing?"
- v8.1 `claim_validity_calibration.md` — "does the present formal object support the asserted property?"
- v8.2 `scope_framing_calibration.md` — "does the prose claim's scope/strength match what the formal apparatus actually delivers, accounting for self-caveats elsewhere?"

Single-stage rubric pass with a **pragmatic caveat-handling rule** built into one of the conditions.

## Inputs

- Single calibration queue entry: `{{queue_entry_path}}`
- Paper text: `{{paper_path}}`

## Task

Produce a single JSON file at `{{output_path}}`:

```json
{
  "queue_entry_id": "SF_GLOBAL_NNN",
  "blind_id": "BS_NNN",
  "rubric": {
    "narrative_claim_located": {
      "passes": "yes | partial | no",
      "prose_anchor": "exact location in abstract / intro / conclusion / section opening",
      "verbatim_or_paraphrase_check": "the prose text at that location, verified to match what the audit claimed it said",
      "notes": "1-2 sentences"
    },
    "formal_evidence_identified": {
      "passes": "yes | partial | no",
      "evidence_anchor": "exact theorem / proposition / experiment that bears on the claim",
      "anchor_source": "obligation_ledger | claim_validity_ledger | direct_search",
      "scope_conditions": ["explicit conditions on the formal evidence"],
      "notes": "1-2 sentences on whether the formal anchor actually addresses the prose claim"
    },
    "concrete_mismatch": {
      "passes": "yes | partial | no",
      "mismatch_kind": "comparator_unfairness | novelty_inflation | empirics_below_conclusion | general_method_from_narrow | formal_to_practical_leap | folk_theorem_framing | unconditional_claim_from_conditional_result | other",
      "specific_scope_or_strength_gap": "1-2 sentences naming the precise scope/strength gap — not 'the framing is too strong'",
      "witness_concrete": "yes | no",
      "notes": "if witness is vague: rubric fails here"
    },
    "scope_correction_offered": {
      "passes": "yes | no",
      "proposed_correction": "how the narrative claim could be re-stated to match the formal evidence",
      "constructive_not_gotcha": "yes | no",
      "notes": "audit must offer a re-statement; pure complaint without correction fails"
    },
    "caveat_handling": {
      "passes": "yes | partial | no",
      "claim_prose_surface": "abstract_topline | intro_topline | section_opening | conclusion_topline | discussion | other",
      "caveat_locations": ["where in the paper the prose claim is qualified"],
      "caveat_strength": "strong | weak | absent",
      "caveat_at_same_surface": "yes | no",
      "caveat_rule_applied": "abstract_topline_strict | intro_topline_strict | section_local_pragmatic | conclusion_pragmatic",
      "rule_decision": "caveat_does_not_save_claim | caveat_saves_claim | caveat_reduces_severity | caveat_reduces_confidence",
      "notes": "1-3 sentences explaining the caveat-rule application"
    },
    "audience_inference_genuinely_misled": {
      "passes": "yes | partial | no",
      "casual_reader_takeaway": "what an expert reader skimming abstract+intro+conclusion would actually take away",
      "would_be_misled": "yes | partial | no",
      "notes": "this is the anti-pedantry guardrail — flag only if a casual expert reader is genuinely misled, not if the claim is technically imprecise but contextually clear"
    }
  },
  "verdict": "reportable_framing_finding | resolved_normal_compression | caveat_saves_claim | inadequate_witness | no_audience_misdirection | indeterminate",
  "verdict_notes": "1-3 sentences on the disposition rationale",
  "panel_row_payload": {
    "concern": "1-sentence statement of the framing overclaim, used as panel-row concern",
    "category": "framing | empirics | interpretation | other",
    "claim_type": "framing",
    "severity": "material | local | nit",
    "mismatch_kind": "consensus or selected mismatch_kind",
    "evidence": [
      {
        "quote_or_paraphrase": "the prose claim as the paper makes it",
        "location": "prose_anchor",
        "support_type": "direct_quote | paraphrase | derived_inference",
        "role": "narrative_claim"
      },
      {
        "quote_or_paraphrase": "what the formal evidence actually delivers",
        "location": "evidence_anchor",
        "support_type": "direct_quote | paraphrase | derived_inference",
        "role": "formal_evidence"
      },
      {
        "quote_or_paraphrase": "the specific scope/strength gap",
        "location": "where the gap is most evident",
        "support_type": "derived_inference",
        "role": "minimal_witness"
      }
    ],
    "suggested_action": {
      "author": {"fix": "the proposed scope correction — re-stating the prose claim to match the formal evidence"},
      "referee": {"how_to_use": "how a referee would phrase this concern in a letter — what re-framing to ask for"}
    }
  }
}
```

`panel_row_payload` is populated only when `verdict == reportable_framing_finding`. Otherwise it is `null`.

## How to work

### Single-stage rubric

Six rubric components, evaluated in order. Five must pass for `verdict: reportable_framing_finding`. The caveat-handling component is special: its outcome can shift severity or confidence rather than block reporting outright.

#### 1. Narrative claim located

The prose claim must be locatable verbatim (or close paraphrase) at the anchor the audit specified. Verify the prose text actually matches the audit's `narrative_claim` field. If not, the audit is hallucinating prose. Fail.

#### 2. Formal evidence identified

The formal apparatus that bears on the claim must be locatable. If the audit cites Theorem 3 as the relevant evidence but Theorem 3 doesn't address the claim's domain, the audit is mis-anchored. Fail. Acceptable anchor sources: v8.0 obligation ledger (preferred), v8.1 claim-validity ledger (preferred), direct paper search (fallback).

If the audit's `expected_formal_anchor` was `none_clear` and the calibrator's own search confirms no formal apparatus addresses the claim at all, that itself is the framing failure — proceed to component 3.

#### 3. Concrete mismatch

The mismatch must be concrete: a specific scope condition the prose omits, a specific competitor and its tuning regime, a specific dataset scope vs. extrapolation phrase. Vague mismatches ("the framing is generally too strong") fail.

`mismatch_kind` must be one of the eight enumerated patterns (or `other` with description). The witness must use only the paper's own setup.

#### 4. Scope correction offered

The audit must propose a constructive re-statement — how the prose could be re-phrased to match the formal evidence. Pure complaint without correction is unconstructive and fails the rubric. The corrected version need not be perfect prose; it must be specific enough that a reader sees what the honest framing would be.

#### 5. Caveat handling (pragmatic)

This component implements the pragmatic caveat rule. Severity and confidence may shift based on outcome.

**Rule by prose surface**:

- **`abstract_topline_strict`** — abstract topline claims set the paper's contract. Caveats elsewhere (§6 conclusion, discussion) do **not** save the framing for an abstract reader. Severity stays at the audit's level. `rule_decision: caveat_does_not_save_claim` if caveat is only in distant sections; `caveat_reduces_severity` if abstract itself contains a weak qualifier; `caveat_saves_claim` only if abstract has a strong same-surface qualifier.

- **`intro_topline_strict`** — same as abstract. Intro topline claims are read with the paper's contract; caveats deep in conclusion do not retroactively scope intro.

- **`section_local_pragmatic`** — section-opening claims are usually defeated by nearby caveats (within the same section, often within the same paragraph). `rule_decision: caveat_saves_claim` if a strong same-section caveat exists; `caveat_does_not_save_claim` only if the caveat is genuinely buried, weak, or inconsistent with the section header.

- **`conclusion_pragmatic`** — conclusion topline claims are usually defeated by caveats in the same conclusion section (most papers caveat their own conclusions). High bar to flag. Reportable only if the conclusion makes a top-line claim AND fails to walk back AND the formal evidence is materially narrower.

The audit's `caveat_at_same_surface: yes/no` informs this. Calibrator independently verifies by checking the caveat locations.

#### 6. Audience inference genuinely misled (anti-pedantry guardrail)

The strictest filter. Even if components 1–5 pass, this asks: would an expert reader skimming abstract + intro + conclusion actually be misled?

- A claim that "characterizes" a phenomenon is normal academic shorthand for "characterizes typical regimes" — flag only if the omitted regime is a load-bearing case (e.g., the paper's own examples violate it).
- A claim of "outperforms" against a competitor is meaningful overclaim only if the competitor's underperformance is plausibly attributable to tuning the audit identifies.
- A claim of "general method" is overclaim only if the formal scope is genuinely narrow (PIM-only when method is sold as broadly applicable).

If a casual expert reader would not be misled, fail this component → `verdict: no_audience_misdirection`. Drop.

### Verdicts

Six possible outcomes:

- **`reportable_framing_finding`** — components 1–4 and 6 pass; component 5 either passes (caveat does not save) or returns `caveat_reduces_severity` / `caveat_reduces_confidence`. Populate `panel_row_payload`. Severity:
  - **`material`** if abstract_topline overreach with no same-surface caveat AND formal evidence is materially narrower.
  - **`local`** if intro_topline or section overreach with weak/absent caveats, OR abstract overreach with strong distant caveats.
  - **`nit`** if conclusion-only overclaim that even casual readers would treat with skepticism, OR section-opening overclaim with imminent same-section caveat.

- **`resolved_normal_compression`** — component 6 fails because the framing is normal academic shorthand; the casual expert reader is not misled. Drop.

- **`caveat_saves_claim`** — component 5's pragmatic rule returned `caveat_saves_claim`. Drop.

- **`inadequate_witness`** — component 3 fails. Drop.

- **`no_audience_misdirection`** — component 6 fails. Drop.

- **`indeterminate`** — component 1 or 2 fails in ways that prevent decision (prose is OCR-corrupted, anchor is ambiguous). Drop.

### Severity calibration for reportable framing findings

Three tiers, with caveat handling reducing severity rather than blocking:

- **`material`** — abstract topline overreach with no same-surface caveat AND formal evidence is materially narrower. Reader's takeaway is wrong without the audit.
- **`local`** — intro topline or section overreach with weak caveats; OR abstract overreach with strong distant caveats (caveat reduces severity from material to local). Misleading but partially mitigated.
- **`nit`** — conclusion-only overclaim; section-opening overclaim with imminent same-section caveat; cosmetic framing imprecision.

### Disputed entries

If the queue entry is `queue_state: disputed`, the calibrator does **not** majority-vote. Adjudicates by:

- Inspecting each family's `mismatch_assessment` and `minimal_witness`.
- Verifying the prose claim and formal evidence at the cited anchors.
- If one family's witness is concrete and the others' are vague, resolve toward the strong witness.
- If families disagree on `mismatch_kind` (`same_claim_different_mismatch_kinds` from integrator), adjudicate which kind actually applies and ship with the resolved kind.

### Same-claim-different-mismatch-kinds

Special case: integrator marked the cluster `same_claim_different_mismatch_kinds`. Calibrator:

- Decide which mismatch_kind actually holds for this prose surface and formal anchor.
- Ship the panel row with the consensus or stronger-witness `mismatch_kind`.
- Record alternatives as considered-and-rejected in `verdict_notes`.

## What this template does not do

- It does not run on quote-supported, gap, or wrong-but-present findings. Those go through their respective calibrators.
- It does not generate audits. Inputs come from the v8.2 integrator queue.
- It does not interact with attack-surface index, debate gates, or method-based discovery directly. Framing-class panel rows merge with method-based, gap-class, and validity-class rows in Phase 6 panel compilation.

## Volume budget

Per paper:
- Calibration queue input: 3–8 audits (per integrator's spec).
- Reportable framing findings shipped: 1–3 expected on most papers, more on papers with systematic framing issues.
- High `resolved_normal_compression` rate (>40%) suggests audit prompt is too aggressive — revise.
- High `no_audience_misdirection` rate (>30%) similar — audit needs better filter on what's audience-relevant.
- High `caveat_saves_claim` rate (>50%) suggests audit is missing the self-caveat check at audit time — that should catch most of these.

If every queued audit becomes a reportable framing finding, you're flagging normal academic compression as overclaim. If zero queued audits ship on a paper with abstract toplines that genuinely overreach, the rubric is too lenient — likely component 5 is over-rewarding distant caveats.
