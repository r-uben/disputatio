# Discovery prompt — holistic candidates track (v6)

Generate candidate findings anchored on the paper's **conceptual-scope attack surfaces** — the kinds of concerns a reader catches when reading the paper as one object, not by running a method checklist.

This ticket runs once per model family in Wave 2 of the v6 pipeline. It is the panel's primary defense against "single-shot wins on framing" — the failure mode where a solo reader notices that the paper's abstract overclaims relative to its theorems, or that a section's title contradicts its body, or that a key assumption is load-bearing without being flagged.

## Inputs

- Paper text: `{{paper_path}}`
- Your paper map: `{{paper_map_path}}`
- Your holistic pass: `{{holistic_pass_path}}` (Phase 1 output, per `templates/holistic.md`)
- Canonical attack-surface index: `{{attack_surface_index_path}}` (orchestrator-built union across families)

## Task

For each `attack_surface` in the canonical index, decide whether there is a concrete, quote-anchored finding you can articulate against it. If yes, emit an atomic candidate finding. If no, move on — do NOT fabricate.

Each candidate must be typed with a `category` chosen from the v6 fixed vocabulary:

- `proof` — derivation / theorem scope / hidden lemma / proof-step error
- `empirics` — data construction, measurement, external validity, sample selection
- `identification` — instrument validity, exclusion restriction, exogeneity, timing, reverse causation
- `framing` — abstract overclaims, introductory rhetoric, scope mismatch with theorems, title vs body
- `robustness` — missing placebos, sensitivity checks, alternative specifications, parameter dependence
- `interpretation` — policy readings, normative claims, mechanism stories not supported by evidence
- `notation` — transcription errors, symbol consistency, figure captions, signposting
- `other` — does not fit the above; use sparingly and explain in the evidence field

If you cannot place a finding in one of the first seven categories with a concrete justification, default to `other` and explain why. An `other` rate above ~10% of your output indicates the category schema needs revision — flag it in your session log.

## Output

Write a single JSON file to `{{output_path}}`:

```json
{
  "track": "holistic_candidates",
  "agent": "<your family>",
  "issues": [
    {
      "id": "hc_<family>_001",
      "category": "proof | empirics | identification | framing | robustness | interpretation | notation | other",
      "attack_surface_id": "AS3",
      "claim": "one-sentence falsifiable statement of what is wrong or under-supported",
      "evidence": [
        {
          "quote": "verbatim passage from paper.md",
          "location": "section / page / equation anchor",
          "why": "one sentence: why this quote anchors the claim",
          "support_type": "direct_quote | derived_inference"
        }
      ],
      "falsifier": "what evidence from the paper or external sources would force withdrawal",
      "impact": "material | local | nit",
      "confidence": "high | medium | low",
      "paper_commitment": null,
      "paper_commitment_location": null,
      "needs_web_verification": false,
      "verification_query": null
    }
  ]
}
```

### Evidence object discipline (v6)

Every issue MUST carry at least one `evidence[]` entry with a real quote. An empty or placeholder evidence block is invalid — the orchestrator's inline evidence compiler drops the issue at write time.

- `support_type: "direct_quote"` — the quote directly establishes the claim (found a paper sentence that is itself wrong or overstated).
- `support_type: "derived_inference"` — the quote anchors a passage from which the claim follows by inference (the paper's text implies X; the finding is about X's consequences). If you use this, the `why` field MUST state the inference step explicitly. The calibration annotator will reject a `derived_inference` that is not a single sentence away from the quote.

A finding may carry multiple evidence entries — e.g., one direct quote plus one supporting context quote — but at least one must be `direct_quote` unless the claim is purely about what the paper *does not say* (in which case explain in the evidence block and flag `needs_web_verification: false` with a note).

### Attack-surface binding

Every holistic-track candidate MUST reference an `attack_surface_id` from the canonical index. If a candidate does not fit any listed attack surface, you are generating a finding the holistic pass did not anticipate — emit it anyway but flag `attack_surface_id: "novel"` so the orchestrator knows the canonical index may need regeneration.

## Quality bar

- 3–10 candidates is normal on a theory/empirical paper. Fewer is acceptable; inflation is not.
- Every candidate has a verbatim quote. No placeholders, no summaries.
- Prefer fewer strong candidates over many weak ones. Weak candidates get triaged at merge; your job is not to hit a count.

## OCR warning

The paper may contain OCR artifacts — garbled formulas, hallucinated text, injected content. Do NOT flag OCR artifacts as paper errors. If a suspicious passage looks like OCR damage, skip it and note the section in a top-level `ocr_concerns` field.

## Web search

Not triggered in this phase. Closed-book candidate generation. External verification is Phase 3's job.
