# [v8.1] Phase 2.5 — Formal Claim Audit (wrong-but-present errors)

**Type**: design / new pipeline phase
**Priority**: high (gates remaining gap closure to coarse)
**Origin**: 2026-05-02 codex 5.5 critical review (sess 30 turn 6) of post-v8.0 gap analysis

## Problem

v8.0 (issues #15 + #16-stripped + #17) handles **absences** of required objects: paper claims X but object Y is missing. That closes ~50% of the v7-vs-coarse coverage gap on the bench.

It does not handle **wrong-but-present** errors: paper provides Y, but Y is wrong under the paper's own definitions. v8.0 obligation extraction sees `satisfied: yes` and moves on. Examples coarse caught and v7 (and v8.0) miss:

- **Stephens #8** — the non-varying-sites paragraph conditions on too much. Paper *does* condition; it conditions on the *wrong* thing.
- **Stephens #10** — the tree count mixes topology with merger order. The count *is* present; it aggregates two different things.
- **Stephens #11** — the likelihood vs log-likelihood argument needs tightening. The argument *is* there; it's imprecise about which scale.
- **Stephens #12** — formula (8) recasts the problem rather than replacing the model-specific work. The formula *is* correct as restated; the novelty claim is wrong.
- **Forney Class V/VI** — the path enumeration / minimum distance arguments *are* presented; the arguments are flawed.

Strengthening v7's `broad_critic` prompts already failed empirically (drop-mini didn't catch these). The cheap path is closed. Need a separate mechanism.

## Proposal

A new **Phase 2.5 — Formal Claim Audit**, between discovery (Phase 2) and merge (Phase 3). Per-family pass with a separate calibration rubric distinct from both quote-supported (v7 `calibrate.md`) and gap-claim (v8.0 `gap_claim_calibration.md`).

The audit asks one question that obligation extraction does not:

> *Given the paper's stated definitions, does the present object actually support the claimed property?*

Sources of audit candidates:
- Holistic load-bearing claims (Phase 1)
- Satisfied obligations from the v8.0 obligation ledger (clusters with `integrated_status: unanimous_satisfied`)
- Discovery findings tagged `category: proof | empirics | identification`
- Key equations / definitions / propositions / results

For each candidate, produce a structured record:

```json
{
  "id": "FCA_001",
  "claim": "1-sentence statement of the asserted property",
  "present_object": "the paper's actual object that's supposed to support the claim (definition / formula / argument / equation)",
  "where_present": "section / equation anchor",
  "asserted_property": "what the paper says the present object establishes",
  "required_inference": "the logical step from object to claim",
  "paper_definitions_used": ["the definitions / lemmas / axioms the audit relies on, all from the paper itself"],
  "validity_status": "valid | partial | invalid | unclear",
  "failure_mode": "wrong_conditioning | aggregation_error | topology_order_confound | likelihood_loglikelihood_mismatch | equivalence_only_restates | hidden_quantifier_shift | novelty_exceeds_formal | scope_creep | other",
  "minimal_witness": "the smallest concrete construction showing the failure (counterexample, redefinition, computation that contradicts the claim)",
  "consequence_if_wrong": "what downstream claim/method/result fails or weakens",
  "confidence": "high | medium | low"
}
```

## Calibration rubric (`templates/claim_validity_calibration.md`)

A wrong-present claim is reportable only if **all six** hold:

1. The object and claimed property are both located in the paper.
2. The critique uses the paper's own definitions, not external machinery.
3. The mismatch is local and explainable in 1–2 sentences.
4. There is a minimal witness — concrete construction, not abstract objection.
5. The finding is scoped to what the error invalidates (not blanket "the proof is wrong").
6. Plausible benign interpretations were considered and rejected (the audit explicitly explains why a charitable reading does not save the claim).

Failure modes for the calibrator: hallucinated witnesses, importing external definitions, confusing imprecise prose with formal error, blanket-condemning a proof when only one step is wrong.

## Phase placement

```
Phase 0   — Orientation
Phase 1   — Holistic
Phase 1.5 — Obligation extraction + integration (v8.0)
Phase 2   — Discovery (9 tickets)
Phase 2.5 — Formal Claim Audit (v8.1, this issue)
Phase 3   — Merge + rank
Phase 3g  — Gap-claim calibration (v8.0)
Phase 3v  — Claim-validity calibration (v8.1, this issue)
Phase 5a  — Calibration pass 1 (existing)
Phase 4   — Escalation gate
Phase 5b  — Final calibration
Phase 6   — Panel + render
```

Both v8.0 (gap) and v8.1 (claim-validity) emit `claim_type`-tagged panel rows that merge with method-based rows before Phase 5a.

## Why this is a separate ticket from v8.0

Codex's verdict (sess 30 turn 6): "Do **not** fold this into obligation extraction. That will blur existence and correctness, and the model will start overclaiming gaps. Do **not** rely on broad_critic prompt strengthening either. That is the cheap path that already failed."

Cramming wrong-present detection into v8.0 turns a coherent release into a mixed architecture. Ship v8.0 first; let bench data tell us how much of the gap remains; design v8.1 against that residual.

## Bench gating

v8.1 should be benchmarked against the v8.0 baseline using the same harness (`docs/benchmark/v8_0_validation/PLAN.md`). Specifically the manual-audit checklist should add a category for "wrong-but-present error correctly identified" — at least 2 such recoveries on Stephens (where the failure mode is dense) for v8.1 to ship.

## Open questions

- **Self-judging risk on `paper_definitions_used`**: the audit imports definitions from the paper to evaluate the paper. Risk that the audit silently mis-imports a definition. Mitigation: require explicit quote/anchor for every cited definition, validated by calibrator.
- **Cost**: 8–15 candidates per paper × 3 families × ~1500 token output = ~20–35k output tokens per paper at the audit phase. Wall clock ~30 min.
- **Interaction with v8.0**: a `unanimous_satisfied` obligation that the audit then flags as `validity_status: invalid` is an evidence chain — paper has X, X is wrong. Worth surfacing both halves in the panel row, not silencing the obligation ledger entry.

## Related

- v8.0 issues #15 (obligation extraction), #16 (integration), #17 (gap calibration)
- v8.2 (next) — scope/framing overclaim audit for the third failure mode codex identified

## Source critique

> "Wrong-but-present asks: 'given the object exists, does it actually do the work the paper claims?' Do not fold this into obligation extraction. That will blur existence and correctness, and the model will start overclaiming gaps. Do not rely on broad_critic prompt strengthening either. That is the cheap path that already failed. The right mechanism is a separate **claim-validity audit**, probably v8.1." — codex/gpt-5.5, sess 30 turn 6
