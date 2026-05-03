# [v8.2] Scope/framing overclaim audit (narrative-vs-formal mismatch)

**Type**: design / new pipeline phase
**Priority**: medium (third failure mode after absences and wrong-present)
**Origin**: 2026-05-02 codex 5.5 critical review (sess 30 turn 6)

## Problem

After v8.0 (absences) and v8.1 (wrong-but-present), a third failure mode remains: **scope and framing overclaim**. The formal object exists *and* is correct under the paper's own definitions; the narrative claim around it overreaches what the formal evidence supports.

Distinct from v8.1 because:
- v8.1 asks: "does the formal object support the asserted property under paper's own definitions?"
- v8.2 asks: "does the asserted property in the formal sense match what the paper's prose / abstract / introduction claims?"

Examples of the failure mode:

- **Comparator unfairness** — Section 5 compares against MCMC at default settings; abstract claims "outperforms MCMC."
- **Novelty inflation** — Section 6 introduces "eight new classes"; text concedes most are re-labelings of existing Wei / Calderbank-Sloane codes.
- **Empirical evidence weaker than conclusion** — bench has 5-loci datasets; abstract extrapolates to "modern population genetics data."
- **General method from narrow case** — proof valid only for parent-independent mutation; framing implies generality.
- **Formal result sold as practical performance** — Theorem 1 establishes existence; abstract says "method efficiently solves..."
- **Folk-theorem framing** — qualitative gain progression presented as theorem-like without conditions.

These are real findings (several appeared in v7 panels under `category: framing`) but disputatio currently catches them inconsistently. Cross-architecture happens to flag some; many slip through.

## Proposal

A new **Phase 2.6 — Scope/Framing Audit**, after v8.1's claim-validity audit. Per-family pass with calibration rubric distinct from gap and claim-validity.

The audit asks one question:

> *Does the paper's narrative claim (abstract / introduction / conclusion) match what the formal evidence inside the paper actually establishes?*

Sources of audit candidates:
- Holistic main_claims (Phase 1) — list every load-bearing narrative claim.
- For each, locate the formal evidence the paper points to (or implies).
- Compare narrative scope to formal scope.

Structured record:

```json
{
  "id": "SFA_001",
  "narrative_claim": "verbatim or paraphrased statement from abstract/intro/conclusion",
  "narrative_location": "abstract / §1.1 / §6 conclusion",
  "narrative_scope": {
    "domain": "what the prose claim asserts the result applies to",
    "strength": "how strong the prose phrases the claim",
    "audience_inference": "what a reader is licensed to infer from the prose alone"
  },
  "formal_evidence": {
    "what_paper_proves": "the actual formal result(s) the paper establishes",
    "where": "theorem/proposition/section anchor",
    "scope_conditions": ["explicit conditions on the formal result — assumptions, restrictions, regimes"],
    "empirical_support": "what experiments/datasets actually back the claim, and their scope"
  },
  "mismatch_kind": "comparator_unfairness | novelty_inflation | empirics_below_conclusion | general_method_from_narrow | formal_to_practical_leap | folk_theorem_framing | unconditional_claim_from_conditional_result | other",
  "minimal_witness": "the smallest concrete demonstration of the mismatch (e.g., 'Theorem 1 requires condition X; abstract claim does not state X')",
  "scope_correction": "how the narrative claim could be re-stated to match the formal evidence",
  "consequence_if_unaddressed": "what a reader is misled into believing",
  "confidence": "high | medium | low"
}
```

## Calibration rubric (`templates/scope_framing_calibration.md`)

A scope/framing claim is reportable only if **all five** hold:

1. The narrative claim is verbatim located in abstract / introduction / conclusion / other prose surface.
2. The formal evidence is explicitly identified (theorem / proposition / experiment) — not inferred.
3. The mismatch is concrete: a specific scope condition / comparator detail / regime that the prose obscures.
4. A scope correction is offered — the finding is constructive, not gotcha.
5. The mismatch is not already disclosed elsewhere in the paper. (If the paper itself caveats the framing in §6, the prose claim is acceptable framing-economy, not overclaim.)

The fifth condition matters: in v7 we had findings that "overclaim" framings the paper *itself* admits in a later paragraph. Those should drop at calibration. The reader has the paper; if the caveat is in the paper, the framing isn't overclaim.

## Phase placement

```
... (v8.0 + v8.1 phases) ...
Phase 2.6 — Scope/Framing Audit (v8.2, this issue)
Phase 3   — Merge + rank (existing)
Phase 3g  — Gap-claim calibration (v8.0)
Phase 3v  — Claim-validity calibration (v8.1)
Phase 3s  — Scope/framing calibration (v8.2, this issue)
... (existing flow) ...
```

## Why v8.2 not v8.0 or v8.1

Codex's verdict: "ship v8.0 as-is. Add v8.1 ticket: formal claim-validity audit. Do not cram. ... Third failure mode: scope/framing overclaim. ... That needs an overclaim/comparator audit later." Each layer is coherent on its own. Bundling explodes the design surface area; bench evidence on each layer can guide whether the next is needed.

## Open questions

- **Severity calibration**: novelty inflation and comparator unfairness are typically `local` not `material` — the formal evidence stands, the framing is misleading. But if the framing drives the *only* claim a reader takes away (abstract overclaim with no caveats anywhere), it can be `material`.
- **Interaction with v8.0/v8.1**: a finding can be all three — required object missing AND wrong-where-present AND overclaimed in the abstract. Need a merge rule that ships them as related panel rows, not three duplicates.
- **Risk of pedantry**: every paper makes some narrative compression. The "scope correction is constructive" condition is meant to filter, but bench audit needed to confirm.

## Bench gating

v8.2 follows the same harness pattern as v8.0/v8.1. Add to manual-audit checklist: "scope/framing overclaim correctly identified, with constructive correction." Threshold for ship: at least 2 such recoveries on the bench corpus, with no obviously pedantic complaints.

## Related

- v8.0 (issues #15, #16-stripped, #17): existence
- v8.1 (issue #06): correctness of present formal object
- v8.2 (this issue): correctness of narrative framing around the formal object

Together they form a three-layer architecture: existence → correctness → framing. Each addresses a distinct failure mode that v7 missed.

## Source critique

> "Third failure mode: scope/framing overclaim. This is neither absence nor wrong-present. The formal object may exist and be correct, but the paper's narrative claim overreaches: unfair comparator, novelty inflation, empirical evidence weaker than conclusion, 'general method' from narrow cases, or formal result sold as practical performance. That needs an overclaim/comparator audit later." — codex/gpt-5.5, sess 30 turn 6
