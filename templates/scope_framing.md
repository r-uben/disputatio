# Scope/framing audit prompt (v8.2, Phase 2.6b — new)

For each triaged candidate, audit whether the paper's narrative claim matches what the formal evidence actually establishes. The third failure mode after absences (v8.0) and wrong-but-present (v8.1): the formal object exists, the formal object is correct, but the narrative framing around it overreaches.

This template runs once per family on candidates that survived triage (`templates/scope_framing_triage.md`). The output is structured per-claim audit records that feed the integrator (`templates/scope_framing_integrate.md`) and calibrator (`templates/scope_framing_calibration.md`).

## Inputs

- Paper text: `{{paper_path}}`
- Triage output (your own): `{{triage_path}}`
- Obligation ledger (cross-family from v8.0, optional): `{{obligation_ledger_path}}`
- Claim-validity ledger (cross-family from v8.1, optional): `{{claim_validity_ledger_path}}`

## Task

Produce a single JSON file at `{{output_path}}`:

```json
{
  "family": "anthropic | openai | google",
  "audits": [
    {
      "id": "SF_001",
      "candidate_id": "SF_TRIAGE_NNN",
      "narrative_claim": "the paper's prose claim, paraphrased",
      "prose_location": "abstract | intro §1.2 | conclusion §6 | section opening §3 | other",
      "prose_surface": "abstract_topline | intro_topline | section_opening | conclusion_topline | discussion | other",
      "narrative_scope": {
        "domain": "what the prose claim asserts the result applies to",
        "strength": "how strong the prose phrases the claim",
        "audience_inference": "what a reader is licensed to infer from the prose alone"
      },
      "formal_evidence": {
        "what_paper_proves": "the actual formal result(s) the paper establishes that bears on this claim",
        "where": "theorem/proposition/section anchor",
        "anchor_source": "obligation_ledger | claim_validity_ledger | direct_search",
        "scope_conditions": ["explicit conditions on the formal result — assumptions, restrictions, regimes"],
        "empirical_support": "what experiments/datasets actually back the claim, and their scope (or null if claim is theoretical)"
      },
      "mismatch_assessment": {
        "exists": "yes | no | unclear",
        "kind": "comparator_unfairness | novelty_inflation | empirics_below_conclusion | general_method_from_narrow | formal_to_practical_leap | folk_theorem_framing | unconditional_claim_from_conditional_result | none | other",
        "kind_other_description": "if kind == other: name the pattern in 1 sentence"
      },
      "minimal_witness": "the smallest concrete demonstration of the mismatch — e.g., 'Theorem 1 requires condition X; abstract claim does not state X', 'comparator MCMC was run at default settings, paper itself notes tuning could improve', 'empirical bench has 5-loci datasets; abstract extrapolates to genome-scale'",
      "scope_correction": "how the narrative claim could be re-stated to match the formal evidence — constructive, not gotcha",
      "consequence_if_unaddressed": "1-2 sentences on what the reader is misled into believing",
      "self_caveat_check": {
        "claim_caveated_elsewhere": "yes | partial | no",
        "caveat_locations": ["where in the paper, if anywhere, the prose claim is qualified or scoped"],
        "caveat_strength": "strong | weak | absent",
        "caveat_at_same_surface": "yes | no — is the caveat at the same prose surface as the claim (e.g., abstract claim caveated in abstract), or in a different surface (abstract claim caveated only in §6 conclusion)?",
        "caveat_prominence": "same_sentence | same_paragraph | same_surface | later_prominent | buried | none"
      },
      "obligation_id": "v8.0 obligation cluster ID this claim's formal apparatus anchors to, if any (cross-phase ID for stable merging) — null if direct_search anchor",
      "claim_validity_id": "v8.1 claim-validity cluster ID for the underlying formal object, if any — null if no v8.1 audit on this object",
      "formal_object_id": "stable identifier for the formal apparatus the prose claim references (e.g. 'theorem_1', 'algorithm_3.2', 'experiment_5.4') — used for cross-phase deduplication",
      "missing_formal_anchor": "yes | no — set to yes only when no theorem/proposition/experiment in the paper bears on the prose claim at all (overclaim from no formal support); requires direct paper search to confirm",
      "source_phase": "v8.2",
      "confidence": "high | medium | low"
    }
  ]
}
```

## How to work

### Primary instruction

For each triaged candidate, ask:

> **Does the paper's narrative claim (abstract / introduction / conclusion / framing prose) match what the formal evidence inside the paper actually establishes?**

Use the v8.0 obligation ledger and v8.1 claim-validity ledger as authoritative anchor maps for "what formal apparatus exists." If a claim's expected anchor is in the obligation ledger as `unanimous_satisfied`, the apparatus exists. If in the v8.1 ledger as `unanimous_valid`, the apparatus is correct. The audit then asks whether the prose's scope/strength matches what that apparatus actually delivers.

If no ledger anchor exists, fall back to direct paper search and mark `anchor_source: direct_search` with quotes from the searched location.

### Mismatch kinds (probe list, not exhaustive)

These eight patterns are common, not exhaustive. If you detect a different pattern, set `mismatch_assessment.kind: other` and name it.

- **`comparator_unfairness`** — paper compares against a competitor at default/untuned settings; abstract makes broader "outperforms" claim. Stephens example: MCMC compared at default settings.
- **`novelty_inflation`** — paper introduces "new classes" that body acknowledges are re-labelings of existing work. Forney example: Section VI's "eight new classes" are re-labelings of Wei/Calderbank-Sloane.
- **`empirics_below_conclusion`** — bench has narrow scope; abstract extrapolates broadly. Stephens example: 5-loci datasets → "modern population genetics data."
- **`general_method_from_narrow`** — proof valid only under specific conditions; framing implies generality. Stephens example: PIM-only result framed as broadly applicable.
- **`formal_to_practical_leap`** — Theorem 1 establishes existence; abstract says "method efficiently solves...". Conflates formal result with practical performance.
- **`folk_theorem_framing`** — qualitative gain progression presented as theorem-like without conditions or proof. Forney example: 1.5/3/4.5/5.25/6 dB folk theorem.
- **`unconditional_claim_from_conditional_result`** — formal result holds under conditions; abstract states it unconditionally.
- **`none`** — narrative claim and formal evidence match. Audit found no overreach.

### Self-caveat check is mandatory

Every audit must include the `self_caveat_check`:

- Search the paper for places where the prose claim is qualified (search §6 conclusion, discussion sections, paragraph after the claim).
- Record `caveat_locations` (multiple if applicable) and `caveat_strength` (`strong | weak | absent`).
- Critical: tag `caveat_at_same_surface`. An abstract claim caveated in §6 is **not** caveated at the same surface — abstract readers don't necessarily reach §6.

The calibrator uses this to apply pragmatic caveat handling: caveats at the same surface usually save the framing; caveats only in distant sections usually do not save abstract/intro topline claims.

### Minimal witness

For mismatches, the witness is the smallest concrete demonstration:

- The exact prose claim (paraphrased) and the exact formal scope condition that the prose omits.
- A specific competitor the prose claims to outperform with the specific tuning regime mismatch.
- The exact dataset scope vs. the exact extrapolation phrase.

Vague witnesses ("the framing is too strong somewhere") fail calibration.

### Scope correction is mandatory

For mismatches, propose a constructive scope correction — how the narrative claim could be re-stated to match the formal evidence. The audit's value to the author/referee is the corrected framing, not the gotcha.

### Anti-pedantry guardrail

Three filters at the audit level (calibrator applies more):

1. **Normal compression**: every paper compresses. "We propose a new method" need not specify "new under our specific definitions." If the prose's compression is normal academic shorthand, mark `mismatch_assessment.exists: no`.
2. **Audience expectation**: papers are written for an expert audience. A claim that "characterizes" a phenomenon need not formally enumerate every case if the expert audience would read it as "characterizes typical regimes." Don't flag unless the audience expectation is clearly violated.
3. **Self-correction**: if the paper itself caveats the claim within the same prose surface, the framing is honest framing-economy. Don't flag.

The audit's job is to find genuine misleading framing — not to enforce maximally pedantic precision.

### Per-family

Audit is a per-family pass. The integrator (`templates/scope_framing_integrate.md`) handles cross-family merge.

### Length budget

Triage caps candidates at 6–10 per family. Audit produces one record per candidate, so output is 6–10 audit records per family. Each record's prose fields are tight — 1–2 sentences per field.

## What this template does not do

- It does not run on free-form discovery. Inputs come from triage.
- It does not adjudicate between families. The integrator does.
- It does not assign panel-row severity. The calibrator does.
- It does not interact with v8.0 obligation extraction or v8.1 claim-validity audit beyond reading the ledgers as anchor map. Scope/framing is the third independent audit; outputs merge at panel-row stage only.
