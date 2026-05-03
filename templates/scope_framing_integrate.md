# Scope/framing integration prompt (v8.2, Phase 2.6c — new)

Merge per-family scope/framing audits into a single global ledger and calibration queue. Cluster equivalent **narrative claims** (not equivalent issue wordings), preserve cross-family disagreement, and emit a sharp queue downstream `templates/scope_framing_calibration.md` acts on.

Same architectural pattern as v8.0 obligation integrator and v8.1 claim-validity integrator. Different inputs (narrative claims + formal-evidence anchors), different forwarded states (`overreaches | partial | disputed`), but the disagreement-preservation discipline is identical.

## Inputs

- Three per-family audit files: `{{anthropic_audits_path}}`, `{{openai_audits_path}}`, `{{google_audits_path}}`
- Paper text: `{{paper_path}}`

Partial-family runs supported: same graceful-degradation contract as v8.0/v8.1.

## Task

Produce two output files.

### 1. Full ledger

Path: `{{ledger_output_path}}`

Every clustered audit including unanimous-`mismatch_assessment.exists: no` clusters. Audit trail; never enters calibration directly.

```json
{
  "paper_slug": "...",
  "families_present": ["anthropic", "openai", "google"],
  "ledger": [
    {
      "cluster_id": "SF_GLOBAL_001",
      "canonical_narrative_claim": "the prose claim the cluster centers on — paraphrased and unified across families",
      "claim_prose_locations": ["abstract", "§1.1", "§6 conclusion topline"],
      "claim_prose_surfaces": ["abstract_topline", "intro_topline", "conclusion_topline"],
      "shared_reader_inference": "what readers are licensed to infer — best-of-three framing across families",
      "expected_formal_anchor": {"should_back": "...", "anchor_kind": "..."},
      "merged_formal_evidence": {
        "what_paper_proves": "best-of-three description of the formal apparatus the paper actually delivers",
        "where": ["all anchor locations across families"],
        "scope_conditions": ["union of scope conditions identified"],
        "anchor_sources": ["obligation_ledger | claim_validity_ledger | direct_search"]
      },
      "family_records": [
        {
          "family": "anthropic",
          "audit_id": "SF_001",
          "mismatch_exists": "yes | no | unclear",
          "mismatch_kind": "comparator_unfairness | ... | none | other",
          "minimal_witness": "...",
          "scope_correction": "...",
          "self_caveat_check": {
            "claim_caveated_elsewhere": "yes | partial | no",
            "caveat_strength": "strong | weak | absent",
            "caveat_at_same_surface": "yes | no",
            "caveat_prominence": "same_sentence | same_paragraph | same_surface | later_prominent | buried | none"
          },
          "obligation_id": "v8.0 cluster ID if anchor came from obligation ledger, null otherwise",
          "claim_validity_id": "v8.1 cluster ID if anchor came from claim-validity ledger, null otherwise",
          "formal_object_id": "stable cross-phase ID for the formal apparatus",
          "missing_formal_anchor": "yes | no",
          "confidence": "high | medium | low"
        }
      ],
      "integrated_status": "unanimous_overreach | unanimous_partial | unanimous_no_mismatch | split_overreach_majority | split_no_mismatch_majority | split_3way | same_claim_different_mismatch_kinds | indeterminate",
      "consensus_mismatch_kind": "if all overreach families agree on kind: that kind; else 'multiple' or null",
      "consensus_caveat_assessment": "best-of-three on whether self-caveat saves the claim, accounting for prose_surface differential",
      "consensus_caveat_prominence": "best-of-three on caveat_prominence enum; if families disagree on prominence, calibrator independently re-judges",
      "consensus_missing_formal_anchor": "true if all overreach families agree no formal anchor exists; false otherwise",
      "obligation_id": "v8.0 cluster ID if all family records anchor to the same one; null otherwise",
      "claim_validity_id": "v8.1 cluster ID if all family records anchor to the same one; null otherwise",
      "formal_object_id": "consensus stable identifier across families",
      "consequence_if_unaddressed": "best-of-three description of reader misdirection"
    }
  ]
}
```

### 2. Calibration queue

Path: `{{queue_output_path}}`

Only audits with reportable risk. Three forwarded states:

- `overreaches` — every available family said `mismatch_exists: yes` with consistent kinds. Calibrator applies the caveat-handling rule and ships if rubric clears.
- `partial` — at least one family said `partial`; no family said `no` strongly. Calibrator assesses the strength of the partial mismatch.
- `disputed` — families disagree (one says `yes`, another says `no` or `unclear`). Calibrator's job is to **resolve**, not to vote.

`unanimous_no_mismatch` clusters do **not** enter the queue. They live in the ledger only.

`same_claim_different_mismatch_kinds` is special: families agree the prose overreaches but disagree on which mismatch_kind. Forward to calibration as `disputed` with both kinds recorded for adjudication.

```json
{
  "paper_slug": "...",
  "queue": [
    {
      "cluster_id": "SF_GLOBAL_NNN",
      "canonical_narrative_claim": "...",
      "queue_state": "overreaches | partial | disputed",
      "claim_prose_locations": ["..."],
      "claim_prose_surfaces": ["..."],
      "candidate_mismatch_kinds": ["aggregated kinds the families surfaced"],
      "consensus_caveat_assessment": "...",
      "family_records": [/* same as ledger */],
      "calibration_priority": "high | medium | low",
      "calibration_priority_reason": "1-2 sentences"
    }
  ]
}
```

## How to work

### A. Claim normalization (LLM clustering, not string similarity)

Read every audit record across the available families. Cluster records that audit the **same narrative claim**. Merge rule is functional — same prose claim, same expected formal anchor, same kind of reader inference.

- Three families auditing the abstract's "outperforms MCMC" claim → same cluster, even with different paraphrasings.
- claude auditing "outperforms MCMC at default settings" and codex auditing "outperforms MCMC under tuning equivalence" → split: same prose claim, different audit angle. Either same cluster with `same_claim_different_mismatch_kinds`, or two clusters depending on whether the audited reader_inference is the same.
- claude auditing abstract's "modern population genetics data" claim and codex auditing intro's "modern data" claim → likely same cluster (same prose claim spread across surfaces); preserve all `claim_prose_locations`.

The canonical name should preserve the prose's actual phrasing as much as possible since that's what the calibrator and reader will see — but normalize across family paraphrasings.

### B. Disagreement preservation

When families disagree on `mismatch_exists`, record every family's verdict in `family_records[]`. Do not collapse. Do not vote.

`integrated_status`:

- `unanimous_overreach` — every available family said `mismatch_exists: yes`.
- `unanimous_partial` — every available family said `partial`.
- `unanimous_no_mismatch` — every available family said `no`.
- `split_overreach_majority` — majority `yes`, minority `partial`/`no`/`unclear`.
- `split_no_mismatch_majority` — majority `no`, minority `yes`/`partial`.
- `split_3way` — three families, three different verdicts.
- `same_claim_different_mismatch_kinds` — overreach families agree on existence but disagree on kind.
- `indeterminate` — partial-family run with insufficient signal, or only one family audited.

`consensus_caveat_assessment` matters for downstream. Even when families agree mismatch exists, they may disagree on whether self-caveat in §6 saves an abstract claim. The integrator records the consensus best-of-three reading; the calibrator applies the pragmatic caveat-handling rule.

### C. Cluster validation

For each cluster, validate before emission:

- **Claim coherence**: all `family_records[]` audit the same prose claim. If two families clearly addressed different prose passages, split.
- **Surface tagging**: `claim_prose_surfaces` union must be coherent. An abstract-topline claim that one family tagged as `discussion` is a tagging error to flag.
- **Anchor consistency**: `merged_formal_evidence.where` should align across families. If anchors point to fundamentally different parts of the paper, the families are auditing different claims — split.
- **Witness check**: for `overreaches` clusters, at least one family must have a concrete `minimal_witness`. Vague witnesses across all families → mark `indeterminate`.

### D. Caveat handling at integration time

The integrator **does not** decide whether self-caveats save the claim — that's the calibrator's job. But the integrator does normalize the caveat data:

- `consensus_caveat_assessment` records the cross-family consensus on `caveat_at_same_surface` and `caveat_strength`.
- This normalization helps the calibrator apply the pragmatic rule consistently across families.

### E. Partial-family runs

Same contract as v8.0/v8.1 integrators. Engine metadata records `families_present`, `families_blocked`, `block_reasons`. The `disputed` state is meaningful with 2 families.

### F. What this phase does not do

- It does not run scope/framing calibration. That is `templates/scope_framing_calibration.md`.
- It does not invent new audits. Operates only on what families audited.
- It does not interact with v8.0 or v8.1 ledgers beyond reading them as anchor maps (which the audits already used). Outputs merge at panel-row stage.

### Length budget

For a typical paper with 3 families:

- Input: ~18–30 family records (6–10 per family from triage-then-audit).
- Ledger: 8–18 clusters (substantial cross-family overlap on prose claims).
- Calibration queue: 3–8 clusters (only `overreaches | partial | disputed`).

If queue exceeds 10, you're under-clustering. If queue is below 2, either the paper is unusually framing-honest (rare) or audits over-credited `no_mismatch` (more likely; spot-check ledger).
