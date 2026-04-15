# Holistic pass prompt (v6, new)

Read the paper as one object and produce a structured map of what the paper claims and where a serious referee would push back. This is **not** a discovery step — it does not produce findings. It produces the attack-surface index that Phase 2 discovery uses as context and that the panel renderer surfaces up-front.

This phase exists because method-based discovery tracks under-detect conceptual-scope concerns — the kind of concern a reader catches by reading the paper holistically, not by running a checklist. The holistic pass is the step where that framing-level analysis happens; Phase 2 discovery still runs, but against a richer shared context.

## Inputs

- Paper text: `{{paper_path}}`
- Paper map (your own): `{{paper_map_path}}`

## Task

Produce a single JSON file at `{{output_path}}` with the following structure:

```json
{
  "paper_spine": "2-4 sentences naming the argumentative load path: what the paper sets up, what it claims, what it proves, what it applies. The spine is the shortest faithful description of the paper as an argumentative object, not a summary of its contents.",
  "main_claims": [
    {
      "id": "MC1",
      "claim": "one-sentence falsifiable statement of a central assertion the paper makes",
      "type": "theoretical | empirical | methodological | interpretive",
      "location": "section / page / equation where it is stated most clearly"
    }
  ],
  "attack_surfaces": [
    {
      "id": "AS1",
      "type": "theory | empirics | identification | framing | robustness | exposition",
      "description": "one-paragraph description of a specific angle where a serious referee would push back",
      "representative_question": "the concrete question a referee would ask",
      "priority": "high | medium | low",
      "paper_location": "section / page where the concern lives (may be multiple)",
      "requires_deep_engagement": true
    }
  ],
  "likely_referee_questions": [
    "at least 6 concrete questions a first-round referee at a top journal would raise"
  ],
  "evidence_heavy_zones": [
    {
      "section": "section name / anchor",
      "why": "why this section needs close engagement rather than a scan"
    }
  ]
}
```

## How to work

### Paper spine

The paper spine is the shortest faithful description of the paper *as an argument*. Not a summary of content — a compression of the load-bearing structure. Example for an econometrics paper: "Uses panel variation in X to identify effect Y, interpreted through model M; applies to policy P; claims novelty on the identification side (Z instrument) and on interpretation (mechanism W)."

### Attack surfaces

An attack surface is a specific angle of criticism, not a finding. "The paper's Property A is load-bearing" is NOT an attack surface — that is a finding. An attack surface is the general category: `theory` attack surface around "scope conditions of Theorem 1 are stronger than the introduction's framing suggests" — this is where findings will be looked for.

Attack surfaces are typed by the kind of scrutiny they warrant:

- **theory** — theorem scope, hidden assumptions, definitional drift, proof dependencies
- **empirics** — data construction, measurement, external validity, sample selection
- **identification** — instrument validity, exclusion restriction, exogeneity, timing, reverse causation
- **framing** — abstract overclaims, introductory rhetoric, scope mismatch with theorems, title vs body
- **robustness** — missing placebos, sensitivity checks, alternative specifications, parameter dependence
- **exposition** — transcription errors, notation consistency, figure captions, signposting, claim/quote mismatches

Every attack surface needs a **representative_question** — the single concrete referee question that captures the category. This question anchors downstream discovery.

`priority`:
- `high` — the paper's central contribution stands or falls on this surface
- `medium` — the concern would affect a section, calibration, or robustness
- `low` — local, mostly presentational

`requires_deep_engagement`: true if Phase 2 narrow evidence-judgment track should target this surface; false if the broad critic track is sufficient.

### Likely referee questions

At least 6. These should be questions a serious first-round referee at a top journal would actually write in their report. Not general prompts; specific questions grounded in the paper's text. Example: "Why does the large-C limit in Proposition 1 require strategic complements to land on the first principal component rather than any other?" — not "why this network?"

### Evidence-heavy zones

Sections where the referee must engage closely with specific equations, derivations, or identifying restrictions. Used to focus the narrow evidence-judgment track in Phase 2. Examples: "Section 4.2 proof of Proposition 2 — the threshold bound scales with ‖b̂‖² which materially affects the headline claim"; "Table 3 — the balance check cuts an important subsample."

## Output discipline

- Every entry references the paper by section/page/equation anchor.
- Main claims carry a type; attack surfaces carry a priority and a representative question.
- Do NOT produce findings here. If you spot a specific concern, record it as an attack surface with a representative question; the candidate finding will be generated in Phase 2 against that surface.
- If the paper is well-written and you genuinely cannot surface 6 referee questions, produce fewer — do not fabricate. The downstream discovery tracks will still run.

## Writing style

Neutral, structured, not adversarial. This is an index the other agents will consume, not a review. Prose should be readable by a non-orchestrator reader who wants to understand the paper in 60 seconds plus the attack-surface landscape in another 60 seconds.

## OCR warning

If the paper is OCR'd and contains garbled LaTeX or hallucinated text blocks injected from unrelated documents, flag those explicitly in a top-level `ocr_corrupted_sections` field (same shape as in `templates/orient.md`) and do not treat corrupted content as paper content.
