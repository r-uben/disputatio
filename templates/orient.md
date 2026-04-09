# Orientation prompt

Before running any discovery methods, you must produce a neutral map of the paper. Do not form judgments yet — just extract structure.

## Paper

{{paper_text}}

## Your task

Read the paper end to end and produce a **paper map** — a structured JSON object that will be used as the cache for all subsequent discovery methods. Do not evaluate the paper. Do not flag issues. Just extract.

## Output

Write a single file to: `{{output_path}}/paper_map.json`

```json
{
  "title": "...",
  "authors": ["..."],
  "venue": "...",
  "abstract": "full abstract text",
  "main_claims": [
    {
      "id": "C1",
      "claim": "one-sentence statement of a core claim",
      "location": "section/paragraph reference",
      "type": "theoretical | empirical | interpretive"
    }
  ],
  "equations": [
    {
      "id": "eq_1",
      "equation": "LaTeX or plain form",
      "label": "the paper's numbering, e.g. (1)",
      "definition": "what it defines or states"
    }
  ],
  "propositions": [
    {
      "id": "prop_1",
      "label": "Proposition 1",
      "statement": "one-sentence statement",
      "conditions": ["list of assumed conditions"]
    }
  ],
  "assumptions": [
    {
      "id": "A1",
      "assumption": "explicit assumption stated in the setup",
      "location": "where it is stated"
    }
  ],
  "parameters": [
    {
      "symbol": "θ",
      "description": "Poisson hazard rate for stockholder adjustment",
      "value": "0.5",
      "source": "Chodorow-Reich, Nenov, and Simsek (2021)"
    }
  ],
  "datasets": [
    {
      "name": "TIPS forward rates",
      "source": "Federal Reserve (Gürkaynak et al. 2007)",
      "period": "2019-2023",
      "used_for": "measuring p^MB(t)"
    }
  ],
  "citations_load_bearing": [
    {
      "cite": "Chodorow-Reich, Nenov, Simsek (2021)",
      "used_for": "MPC calibration",
      "claim_attributed": "MPC out of stock wealth equal to 3 cents"
    }
  ],
  "appendix_references": [
    {
      "ref": "Internet Appendix Proposition IA.1",
      "used_for": "fixed-point characterization",
      "location_in_main_text": "Section I.C.2"
    }
  ],
  "section_anchors": {
    "intro": "paragraph range",
    "model": "paragraph range",
    "main_result": "paragraph range",
    "empirics": "paragraph range",
    "conclusion": "paragraph range"
  },
  "section_summaries": {
    "intro": "one sentence",
    "model": "one sentence",
    "main_result": "one sentence",
    "empirics": "one sentence",
    "conclusion": "one sentence"
  }
}
```

## OCR warning

If the paper was OCR'd, you may see garbled formulas, hallucinated text blocks injected from unrelated documents, or broken LaTeX. **Do not include these artifacts in the paper map.** Only extract content that is clearly part of the actual paper. If a section appears to be corrupted, note it in a top-level "ocr_corrupted_sections" field but do not treat corrupted content as the paper's own.

```json
{
  ...
  "ocr_corrupted_sections": [
    {"location": "page N", "description": "what the corrupted content looked like"}
  ]
}
```
