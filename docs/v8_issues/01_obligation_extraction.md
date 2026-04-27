# [v8] Obligation-extraction layer

**Type**: design / new pipeline phase
**Priority**: high
**Origin**: 2026-04-25 head-to-head against coarse.ink on Stephens & Donnelly (2000); codex 5.5 critical review of v8 plan

## Problem

v7 misses **formal-specification gaps** that adversarial single-model reviewers (coarse) catch routinely. On Stephens & Donnelly, coarse flagged 8 such gaps (kernel definitions incomplete, MH algorithm missing complete-data density, ascertainment too weak, tree-count topology mixing, etc.); v7 caught 0 of them.

Diagnosis: v7's discovery tracks (`holistic_candidates`, `broad_critic`, `narrow_evidence`) bias toward *concept and contradiction*. None of them ask "for this claimed method/result, what objects MUST exist for it to be executable/provable?" Even stronger models charitably interpolate the missing pieces when they read incomplete specs.

The root cause is **not** model size and **not** missing prompt cleverness. It is the absence of an explicit **obligation model**.

## Proposal

Add a new pipeline layer between Phase 1 (holistic) and Phase 2 (discovery): **obligation extraction**.

For every method, theorem, proposition, algorithm, or worked claim in the paper, produce a structured record:

```json
{
  "obligation_id": "OBL_001",
  "claim_id": "Theorem 1 / Algorithm 1 / Proposition 2",
  "claim_quote": "verbatim",
  "claim_location": "section / equation / page",
  "required_objects": [
    {
      "object": "complete-data density f(A, theta)",
      "why_required": "MH algorithm at line 4 needs proposal density to compute acceptance ratio",
      "type": "definition | property | bound | algorithm | proof_step | dataset"
    }
  ],
  "satisfied_at": [
    {"object": "complete-data density", "found_at": "Section 3.2 eq (8)", "confidence": "high|partial|none"}
  ]
}
```

The output of this phase is a **per-family obligation index** (sibling to the canonical attack-surface index from v6). Discovery and the new gap-finding sub-method (issue #03) consume it.

## Why this is the right primitive

- It's prescriptive, not exploratory. Fixed schema → calibrator can audit the search.
- It separates "what the paper claims" from "what those claims oblige" — distinct from holistic main_claims, which is descriptive.
- It feeds both gap-finding (issue #03) and section integration (issue #02) cleanly.

## Open questions

- **Which agent runs obligation extraction?** Probably all three families in parallel (model-independence preserved). Then the global integrator (issue #02) reconciles.
- **Does it run once or per-section?** Both — obligation extraction is global-claim-anchored; section integration cross-references local evidence.
- **Cost**: 3 tickets, full-paper context calls. Subscription cost ~free; wall ~10 min.

## Related

- Issue #02: Section-extract → global-integrate
- Issue #03: Gap-claim calibration rubric
- Issue #04: Stronger discovery models (least structural fix)
- Issue #05: Adversarial benchmark before redesign

## Source critique

> "The actual root cause is probably not model size. It is that disputatio lacks an explicit specification-obligation model: 'given this claimed method/result, what objects must exist for it to be executable/provable?' Without that, stronger models may still charitably interpolate." — codex/gpt-5.5, 2026-04-25
