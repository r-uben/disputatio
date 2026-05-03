# Claim validity integration prompt (v8.1, Phase 2.5c — new)

Merge per-family claim-validity audits (`_artifacts/json/claim_validity_<family>.json`, three files) into a single global audit ledger. Cluster equivalent **formal objects** (not equivalent issue wordings), preserve cross-family disagreement, and emit a sharp calibration queue downstream `templates/claim_validity_calibration.md` acts on.

This phase mirrors v8.0's obligation integrator (`templates/obligation_integrate.md`) but for claim-validity records. Same architecture, distinct purpose: v8.0 integrator merges obligations (about object existence); v8.1 integrator merges audits (about object correctness). They run in parallel; their outputs merge only at panel-row level.

## Inputs

- Three per-family audit files: `{{anthropic_audits_path}}`, `{{openai_audits_path}}`, `{{google_audits_path}}`
- Paper text: `{{paper_path}}`

If a family is unavailable (content filter, capacity, OAuth expiry), the integrator runs on the remaining families and records the partial-family note in engine metadata. Same graceful-degradation contract as v8.0.

## Task

Produce two output files.

### 1. Full audit ledger

Path: `{{ledger_output_path}}`

Every clustered audit including unanimous-`valid` ones. Audit trail; never enters calibration directly.

```json
{
  "paper_slug": "...",
  "families_present": ["anthropic", "openai", "google"],
  "ledger": [
    {
      "cluster_id": "CV_GLOBAL_001",
      "canonical_object": "the formal object the cluster centers on — functionally named, not lexically (e.g., 'minimum-distance bound for Lemma 4', not 'd_min^2 expression')",
      "object_kind": "theorem | proposition | lemma | algorithm | definition | derivation | equation_block | computation | benchmark_calibration",
      "shared_claim": "the asserted property the families audited — paraphrased and unified across families",
      "claim_locations": ["§II-G Lemma 4", "Section IV.B"],
      "object_locations": ["where the present formal object lives — possibly multiple"],
      "family_records": [
        {
          "family": "anthropic",
          "audit_id": "CV_001",
          "validity_status": "valid | partial | invalid | unclear",
          "failure_mode": "wrong_conditioning | aggregation_error | ... | other",
          "minimal_witness": "...",
          "consequence_if_wrong": "...",
          "benign_interpretation_considered": "...",
          "paper_definitions_used": [{"name": "...", "location": "...", "quote_or_paraphrase": "..."}],
          "confidence": "high | medium | low"
        }
      ],
      "integrated_status": "unanimous_valid | unanimous_partial | unanimous_invalid | split_valid_majority | split_invalid_majority | split_3way | same_object_different_defects | indeterminate",
      "consensus_failure_mode": "if all non-valid families agree on failure_mode: that mode; else 'multiple' or null",
      "merged_paper_definitions": ["union of cited paper definitions across families, deduplicated by name+location"],
      "consequence_if_wrong": "best-of-three description of what breaks downstream"
    }
  ]
}
```

### 2. Calibration queue

Path: `{{queue_output_path}}`

Only audits with reportable risk. Three forwarded states (mirrors v8.0 obligation queue):

- `invalid` — every available family said `invalid`. Calibrator validates the witness and ships if the rubric clears.
- `partial` — at least one family said `partial`; no family said `valid` more strongly. Calibrator assesses whether the narrower claim is what the paper actually needs.
- `disputed` — families disagree (one says `valid`, another says `invalid` or `partial`). Calibrator's job is to **resolve**, not to vote.

`unanimous_valid` rows do **not** enter the queue. They live in the ledger only.

`same_object_different_defects` is a special integrated_status: families agree the object has a problem but disagree on which failure_mode applies. Forward to calibration as `disputed` with both failure modes recorded for the calibrator to adjudicate.

```json
{
  "paper_slug": "...",
  "queue": [
    {
      "cluster_id": "CV_GLOBAL_NNN",
      "canonical_object": "...",
      "queue_state": "invalid | partial | disputed",
      "shared_claim": "...",
      "claim_locations": ["..."],
      "family_records": [/* same as ledger */],
      "candidate_failure_modes": ["aggregated list of failure_modes the families surfaced"],
      "calibration_priority": "high | medium | low",
      "calibration_priority_reason": "1-2 sentences on why this audit matters for the paper's main result"
    }
  ]
}
```

## How to work

### A. Object normalization (LLM clustering, not string similarity)

Read every audit record across the available families. Cluster records that audit the **same formal object attached to the same claim**. Merge rule is functional, not lexical:

- Three families auditing Lemma 4's minimum-distance formula → same cluster, even if claude calls it "d_min^2 bound," codex calls it "minimum-distance expression," and gemini calls it "Lemma 4 distance equation."
- claude auditing "Theorem 1's existence claim" and codex auditing "Theorem 1's uniqueness step" → **different clusters** even though they both touch Theorem 1. Same object, different defects, different audits.
- claude auditing OA3.1 row-sum invariance and codex auditing OA3.1 normalization → may or may not be same cluster depending on whether the audited *claim* is the same. If both ask "does OA3.1 generalize Property A?" → same cluster. If one asks generalization and the other asks well-definedness → different.

The canonical name is **functional**: `"minimum-distance bound for Lemma 4 in the decomposable mod-2 case"`, not whichever family phrased it best.

Distinguish three patterns explicitly:

1. **Same defect**: families agree on `failure_mode` and the minimal witness's character. Strongest signal.
2. **Same object, different defects**: families agree there's a problem but disagree on which failure_mode. Worth calibrating both.
3. **Family-only weak concern**: only one family flagged the cluster, no other family even audited it. Mark `integrated_status: indeterminate` unless triage on the silent families would have surfaced it (i.e., it was on their candidate list but they marked `valid`).

### B. Disagreement preservation

When families disagree on `validity_status`, record every family's verdict in `family_records[]` verbatim. Do not collapse. Do not vote.

`integrated_status` encodes the shape of disagreement, used only for routing and audit:

- `unanimous_valid` — every available family said `valid`.
- `unanimous_partial` — every available family said `partial` (no `valid` or `invalid`).
- `unanimous_invalid` — every available family said `invalid`.
- `split_valid_majority` — majority `valid`, minority `partial`/`invalid`/`unclear`.
- `split_invalid_majority` — majority `invalid`, minority `valid`/`partial`.
- `split_3way` — three families, three different verdicts.
- `same_object_different_defects` — non-`valid` families agree the object is wrong but disagree on `failure_mode`.
- `indeterminate` — partial-family run with insufficient signal, or only one family audited at all.

`integrated_status` is a **routing label**, not a truth claim. The downstream calibrator (`templates/claim_validity_calibration.md`) decides whether the audit clears the six-condition rubric and ships as a panel row.

### C. Cluster validation

For each cluster, validate before emission:

- **Object coherence**: all `family_records[]` audit the same formal object attached to the same claim. If not, split.
- **Definition merge**: `merged_paper_definitions` union must be internally consistent — if claude cites Definition 2 at §3.1 and codex cites Definition 2 at §3.2, one is wrong; the integrator should note the discrepancy in the cluster.
- **Witness check**: for `invalid`/`partial` clusters, at least one family must have a concrete `minimal_witness`. Vague witnesses across all families → cluster cannot be calibrated; mark `indeterminate`.
- **Anti-hallucination**: spot-check `paper_definitions_used` quotes against the paper text. If any cited definition is not at its claimed location, flag the cluster `indeterminate` and surface the hallucination in the audit log.

### D. Partial-family runs

Same contract as v8.0 obligation integrator. If anthropic is blocked (content filter on verbatim quoting), runs proceed with codex + gemini. Engine metadata records `families_present`, `families_blocked`, `block_reasons`. The `disputed` state is meaningful with 2 families.

### E. What this phase does not do

- It does not run claim-validity calibration. That is `templates/claim_validity_calibration.md`.
- It does not invent new audits. The integrator only operates on what the family audits produced.
- It does not interact with v8.0 obligation ledger. v8.1 integrator and v8.0 integrator are parallel; their outputs merge only at panel-row level (Phase 5a or earlier in the panel-row candidate stage).

### Length budget

For a typical paper with 3 families:

- Input: ~24–36 family records (8–12 per family from triage-then-audit).
- Ledger: 12–25 clusters (substantial cross-family overlap expected on triaged candidate set).
- Calibration queue: 4–10 clusters (only `invalid | partial | disputed`; valid clusters don't queue).

If your queue exceeds 12, you're under-clustering — re-run cluster validation with stricter merge rules. If your queue is below 3, either the paper is unusually well-specified or the audits over-credited `valid` — spot-check the ledger.
