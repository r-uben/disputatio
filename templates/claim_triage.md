# Claim triage prompt (v8.1, Phase 2.5a — new)

Select **audit-worthy formal claims** for downstream claim-validity audit. This is a triage step, not the audit itself. Cast over holistic claims + satisfied obligations + discovery proof/empirics/identification findings + load-bearing theorems/propositions/equations. Output a capped list of candidates with the exact present formal object, the claimed property, the location, and a short justification of why auditing it could falsify something material.

This phase exists because v8.1's claim-validity audit is expensive and brittle on a bloated candidate set. Without triage, the audit prompt would drown in narrative scaffolding, motivating examples, and routine restatements that have no real audit value. Triage is intentionally lossy — it preserves a `dropped_because` list for accountability and prefers claims whose invalidity would change a theorem, proposition, empirical conclusion, or headline interpretation.

## Inputs

- Paper text: `{{paper_path}}`
- Paper map (your own): `{{paper_map_path}}`
- Holistic pass (your own): `{{holistic_pass_path}}`
- Obligation ledger (cross-family from v8.0): `{{obligation_ledger_path}}`
- Discovery findings (your own, all 3 tracks): `{{discover_holistic_path}}`, `{{discover_broad_path}}`, `{{discover_narrow_path}}`

## Task

Produce a single JSON file at `{{output_path}}`:

```json
{
  "family": "anthropic | openai | google",
  "candidates": [
    {
      "id": "CV_TRIAGE_001",
      "claim": "1-sentence statement of the asserted property the paper claims",
      "claim_location": "section / theorem / equation anchor",
      "present_object": "the paper's actual formal object that's supposed to support the claim — definition, formula, argument, equation, derivation",
      "object_location": "where the formal object lives, often different from the claim location",
      "object_kind": "theorem | proposition | lemma | algorithm | definition | derivation | equation_block | computation | benchmark_calibration",
      "audit_priority": "high | medium | low",
      "audit_priority_reason": "1-2 sentences on why auditing this could falsify something material — what theorem/proposition/empirical conclusion/headline interpretation breaks if the present object does not support the claim under the paper's own definitions",
      "source": "holistic | obligation_ledger | discovery_holistic | discovery_broad | discovery_narrow | manual_paper_scan",
      "source_id": "MC1 | OBL_GLOBAL_NNN | hc_claude_NNN | etc — the input record this candidate originated from"
    }
  ],
  "dropped_because": [
    {
      "candidate_description": "1-line description of what was considered",
      "source": "where it came from",
      "drop_reason": "narrative_scaffolding | restated_in_passing | not_load_bearing | motivating_example_only | future_work_gesture | already_caveated_in_paper | redundant_with_kept_candidate"
    }
  ]
}
```

## How to work

### Volume cap

Aim for **8–12 audit candidates per family per paper**. Hard cap at 18 — beyond that, triage is failing its purpose. Below 5 means you're being too aggressive about dropping; reconsider what counts as load-bearing.

The `dropped_because` list should typically have 10–25 entries. A near-empty `dropped_because` means triage isn't actually filtering — every candidate the holistic/discovery/obligation pipeline surfaced went through. That defeats the purpose.

### What counts as audit-worthy

A candidate is audit-worthy iff **all three** hold:

1. The paper presents a formal object (definition / formula / derivation / algorithm / theorem proof) — not just a narrative claim.
2. The paper attaches a property to that object — what the object is supposed to establish or compute.
3. The property's invalidity, under the paper's own definitions, would change a theorem statement, a proposition's scope, an empirical conclusion's strength, or a headline-claim interpretation.

If condition 3 fails — the paper would be unaffected by the audit — drop it. Cosmetic clarity issues, motivating examples, related-work claims, and future-work gestures all fail condition 3.

### What to drop

Common drop reasons (use these exact strings in `drop_reason`):

- **`narrative_scaffolding`**: connecting prose between sections, intuition pumps, summary statements that recap a formal object without adding a checkable property.
- **`restated_in_passing`**: same claim made multiple times; keep one canonical instance, drop reformulations.
- **`not_load_bearing`**: the paper's main contribution survives if this claim is wrong.
- **`motivating_example_only`**: example exists to illustrate, not to be analytically used downstream.
- **`future_work_gesture`**: paper itself flags as not-yet-done or extension territory.
- **`already_caveated_in_paper`**: paper itself disclaims the claim's strength elsewhere — reader is not misled.
- **`redundant_with_kept_candidate`**: a stronger version of this audit is already in the kept set.

### Lossy and accountable

Triage drops claims that don't survive the three-condition test. The `dropped_because` list is the audit trail — the integrator and downstream calibrator can spot-check whether triage was reasonable. If the calibrator finds ship-worthy gaps in the `dropped_because` list, triage prompt needs revision.

### Source diversity

Don't pull every candidate from one source. A paper's audit-worthy claims live across:

- Holistic main_claims (5–10 per family) — frame-level claims
- Obligation ledger satisfied entries — places where v8.0 said "the object is there" and v8.1 asks "but is it doing the right work?"
- Discovery proof/empirics/identification findings — places where method-based discovery flagged something but didn't fully audit

A balanced candidate set draws from all three. If 90% comes from one source, triage is biased — re-cast.

### Per-family

Triage is a per-family pass. Run once per family (anthropic / openai / google). The cross-family integrator (`templates/claim_validity_integrate.md`) merges audits, not triage outputs — triage outputs feed into the per-family audit (`templates/claim_validity.md`).

### What this phase does not do

- It does not audit anything. Triage decides what's worth auditing; the audit is `templates/claim_validity.md`.
- It does not assign verdicts (`valid | partial | invalid | unclear`). Those come at audit + calibration time.
- It does not interact with v8.0 Phase 1.5b's integrator output beyond reading the ledger as a candidate source. Obligation calibration runs in parallel with claim-validity calibration; they merge at panel-row level only.

## Output validation

- Every candidate must have a citable `claim_location` anchor and a citable `object_location` anchor.
- Every candidate's `audit_priority_reason` must name a specific downstream consequence (theorem name, conclusion phrase, headline claim) — not "the proof would be weaker."
- `dropped_because` is mandatory. An empty `dropped_because` list is a triage failure — reject and re-run.
