# [v8] Section-extract → global-integrate

**Type**: design / new pipeline phase
**Priority**: high
**Origin**: 2026-04-25 head-to-head; codex 5.5 critique

## Problem

v7 reads the paper as a single object across orient + holistic, then narrows attention via the canonical attack-surface index. Coarse fans out one agent per major section, achieving granular engagement with each section's local technical content. Coarse caught 8 spec gaps on Stephens that v7 missed; the per-section drill-down is plausibly a major reason.

But naive per-section drill-down has a hidden trap: **a methods gap may span intro claim + algorithm + appendix + proof**. Section-local agents would each see only their slice and miss that an obligation stated in §1 is satisfied (or not satisfied) in Appendix A. Local blindness.

## Proposal

Two-stage:

### Stage 1 — Section-local extraction (parallel, per-family-per-section)

Each major section (≈8–12 per typical paper) gets its own ticket per family. The agent reads ONLY that section + the holistic spine + the obligation index. Output:

- `local_obligations[]` — obligations stated in this section
- `local_evidence[]` — definitions, properties, algorithms, proofs that satisfy obligations from anywhere in the paper
- `local_findings[]` — concerns specific to this section

### Stage 2 — Global integration (one ticket, claude/opus inline)

A single integrator reads:

- All section-local outputs across families
- The full paper text
- The obligation index (issue #01)

It checks each obligation against the union of all local evidence. **Unsatisfied obligations** are emitted as gap-finding candidates with structured records (issue #03 schema).

## Why this is sharper than my original "per-section drill-down"

My naive version had agents merge by union with no integrator → high recall, exploded noise, no global reconciliation. Codex's correction: section agents do **extraction** (cheap and bounded), the global integrator does **satisfaction-checking** (expensive and definitive).

## Open questions

- **How is "major section" defined?** Should follow the paper's structure (its own §1, §2…), not a fixed N. The orient ticket already extracts section anchors — reuse those.
- **What if sections are imbalanced (one tiny intro, one giant theory)?** Cap at K=12 sections per family; merge tiny sections, split monster ones via subsection anchors.
- **Cost**: ~10 sections × 3 families = 30 extraction tickets + 1 integrator. Parallel; subscription ~free; wall ~15 min added.
- **What model for the integrator?** Opus for sure — this is a long-context reconciliation task with high quality bar.

## Concrete schema for section-local output

```json
{
  "section_id": "Section 3.2",
  "family": "anthropic",
  "local_obligations": [
    {"obligation_id": "OBL_LOCAL_001", "claim_quote": "...", "required_object": "...", "why_required": "..."}
  ],
  "local_evidence": [
    {"evidence_id": "EV_001", "object": "...", "definition_quote": "...", "satisfies_obligation_candidates": ["OBL_001", "OBL_LOCAL_007"]}
  ],
  "local_findings": [
    {... standard finding shape ...}
  ]
}
```

## Related

- Issue #01: Obligation extraction
- Issue #03: Gap-claim calibration rubric
- Issue #05: Bench against multiple papers before committing

## Source critique

> "Per-section is not obviously right. It helps with attention, but creates local blindness. A methods gap may require intro claim + algorithm + appendix + proof. Better: section agents extract obligations and local evidence; a separate integrator checks whether obligations are satisfied anywhere in the paper." — codex/gpt-5.5, 2026-04-25
