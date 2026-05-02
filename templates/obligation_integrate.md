# Obligation integration prompt (v8.0, new)

Merge per-family obligation records (`_artifacts/json/obligations_<family>.json`, three files) into a single global ledger. Cluster equivalent required objects, preserve cross-family disagreement, and emit a sharp calibration queue downstream gap-claim calibration acts on.

This phase exists because per-family obligation extraction (`templates/obligations.md`) operates locally to each family. Without a global integrator, "Λ_0 closure under addition is unproven" might appear in the codex output but not in the anthropic output, and v8 would never notice. The integrator owns the cross-family search-and-merge step.

Per-section drill-down is **out of scope** for v8.0. The integrator works at the obligation level: each cluster is a single mathematical/statistical object that the paper's claim/method requires. Local section blindness is acceptable here because a missing object that one family searched in §3.2 and another searched in Appendix A is still the same missing object — disagreement on `searched_locations` is *evidence*, not noise.

## Inputs

- Three per-family obligation files: `{{anthropic_obligations_path}}`, `{{openai_obligations_path}}`, `{{google_obligations_path}}`
- Paper text: `{{paper_path}}`

If a family is unavailable (content filter, capacity, OAuth expiry), the integrator runs on the remaining families and records the partial-family note in engine metadata.

## Task

Produce two output files.

### 1. Full obligation ledger

Path: `{{ledger_output_path}}`

Every normalized obligation cluster, including unanimous-satisfied ones. Audit trail and replay surface — never enters discovery or calibration.

```json
{
  "paper_slug": "...",
  "families_present": ["anthropic", "openai", "google"],
  "ledger": [
    {
      "cluster_id": "OBL_GLOBAL_001",
      "canonical_name": "complete-data joint density for the MH augmentation",
      "kind": "definition | property | bound | algorithm | proof_step | dataset | parameter_value | reference_calibration",
      "claim_or_method": "shared description of what the paper claims/method this object enables — paraphrased and unified across families",
      "claim_locations": ["§3.2 algorithm 1", "eq (7)", "Section 3.2.1"],
      "family_records": [
        {
          "family": "anthropic",
          "obligation_id": "OBL_001",
          "satisfied": "yes | partial | no | unclear",
          "found_at": "Section 3.2 eq (8)",
          "searched_locations": ["§3.2", "Appendix A.1", "Definition 2"],
          "support_type": "direct_quote | paraphrase | derived_inference",
          "missing_piece": "...",
          "consequence_if_missing": "..."
        }
      ],
      "integrated_status": "unanimous_satisfied | unanimous_partial | unanimous_unsatisfied | split_satisfied_majority | split_unsatisfied_majority | split_3way | indeterminate",
      "merged_searched_locations": ["union of all family searched_locations, deduplicated"],
      "consequence_if_missing": "best-of-three description of what breaks downstream"
    }
  ]
}
```

### 2. Calibration queue

Path: `{{queue_output_path}}`

Only obligations with unresolved risk. Three forwarded states:

- `unsatisfied` — every available family said `no`. Calibration validates absence rigorously.
- `partial` — at least one family said `partial`; no family said `no` more strongly. Calibration checks whether the partial substitute is enough for the claim.
- `disputed` — families disagree (one says `yes`, another says `no` or `partial`). Calibration's job is to **resolve the conflict**, not to vote.

`unanimous_satisfied` rows do **not** enter the queue. They live in the ledger only.

```json
{
  "paper_slug": "...",
  "queue": [
    {
      "cluster_id": "OBL_GLOBAL_NNN",
      "canonical_name": "...",
      "queue_state": "unsatisfied | partial | disputed",
      "claim_or_method": "...",
      "claim_locations": ["..."],
      "merged_searched_locations": ["..."],
      "family_records": [/* same as ledger */],
      "calibration_priority": "high | medium | low",
      "calibration_priority_reason": "1-2 sentences on why this obligation matters for the paper's main result"
    }
  ]
}
```

## How to work

### A. Object normalization (LLM clustering, not string similarity)

Read every obligation record across the available families. Cluster records that require the **same mathematical/statistical object to make the same method/result executable or provable**. The merge rule is functional, not lexical:

- "complete-data joint density," "augmenting density," and "joint law of latent variables" → same cluster if they all attach to the same MH algorithm in §3.2.
- "Λ₀ closure under addition" and "time-zero lattice is a lattice" → same cluster.
- "transition matrix domain" and "kernel acts on conditional A_n" → same cluster if both attach to Definition 1.

Distinct objects:

- "complete-data joint density" attached to MH method I (§3.2) ≠ "complete-data joint density" attached to MH method II (§3.3) — different methods, different obligations, different clusters even if the object name is identical.
- "non-negative weights" in IS proposal vs "non-negative weights" in MCMC importance reweighting — different methods → different clusters.

The canonical name should be **functional**, not lexical. Pick "complete-data joint density for the MH augmentation," not whichever family phrased it best.

Record volume is small enough (roughly 24–45 records when three families are present) that direct LLM clustering works. Do not add Jaccard heuristics or token-overlap thresholds — they create brittle alias failures exactly where this matters.

### B. Disagreement preservation

When families disagree on `satisfied`, record every family's verdict in `family_records[]` verbatim. Do not collapse. Do not vote.

`integrated_status` encodes the shape of disagreement, used only for routing and audit:

- `unanimous_satisfied` — every available family said `yes`.
- `unanimous_partial` — every available family said `partial` or `unclear` (no one said `yes` or `no`).
- `unanimous_unsatisfied` — every available family said `no`.
- `split_satisfied_majority` — majority `yes`, minority `partial`/`no`/`unclear`.
- `split_unsatisfied_majority` — majority `no`/`partial`, minority `yes`/`unclear`.
- `split_3way` — three families, three different verdicts.
- `indeterminate` — partial-family run with insufficient signal (e.g., 1-of-2 says `unclear`, the other says `partial`).

`integrated_status` is a **routing label**, not a truth claim. The downstream calibrator (`templates/gap_claim_calibration.md`) is responsible for deciding whether the obligation is genuinely unsatisfied. Specifically:

- If any family says `satisfied=yes`, calibration must inspect that cited location first. A split becomes a reportable gap only when calibration explains why the positive citation does **not** satisfy the obligation (wrong object, incomplete definition, only informal prose, missing conditioning variables, not usable for the claimed result).
- Majority vote is not enough. One correct satisfied citation defeats the gap.
- Conversely, one `satisfied` verdict with a bad citation should not suppress the gap.
- If calibration cannot resolve the conflict, the obligation is dropped as `indeterminate` and never becomes a finding.

### C. Cluster validation

For each cluster, validate before emission:

- **Functional coherence**: all `family_records[]` describe the same object attached to the same method/claim. If not, split.
- **Searched-location merge**: the union of `searched_locations` across families is the authoritative search trail. The downstream calibrator uses this to assess whether absence is genuinely scoped or whether more search is needed.
- **Claim-location anchoring**: every cluster must have at least one citable claim location. Without an anchor, the obligation cannot be calibrated and is dropped.

### D. Partial-family runs

If only 2 families are available (anthropic blocked, codex weekly cap, gemini OAuth dead), proceed with whichever 2 are present. Add `families_present` to the ledger metadata. The queue's `disputed` state is meaningful with 2 families (one yes / one no), and `unanimous` requires only the available set to agree.

### E. What this phase does not do

- It does not run gap-claim calibration. That is `templates/gap_claim_calibration.md`.
- It does not invent new obligations. The integrator only operates on what the family extractors produced.
- It does not interact with attack-surface index, holistic_pass, or discovery tracks. Obligation flow is parallel to method-based discovery; downstream merge in Phase 3 is where they meet.

### Length budget

For a typical paper with 3 families:

- Input: ~24–45 family records (8–15 per family).
- Ledger: 12–25 clusters (substantial cross-family overlap is expected).
- Calibration queue: 5–12 clusters (only `unsatisfied | partial | disputed`).

If your queue exceeds 15 clusters, you are likely over-fragmenting — re-run cluster validation with stricter merge rules. If your queue is below 3, you are likely under-clustering or the paper has unusually clean specification (rare; double-check before forwarding).
