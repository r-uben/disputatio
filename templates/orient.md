# Orientation prompt

Before running any discovery methods, you must produce a neutral map of the paper. Do not form judgments yet — just extract structure.

## Paper

{{paper_text}}

## Your task

Read the paper end to end and produce a **paper map** — a structured JSON object that will be used as the cache for all subsequent discovery methods. Do not evaluate the paper. Do not flag issues. Just extract.

## Output

Write a single JSON file to: `{{output_path}}`

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
      "symbol": "symbol used in the paper",
      "description": "what the parameter represents",
      "value": "calibrated or assumed value",
      "source": "where the value comes from"
    }
  ],
  "datasets": [
    {
      "name": "dataset name",
      "source": "provider and citation",
      "period": "time coverage",
      "used_for": "what the paper uses it for"
    }
  ],
  "citations_load_bearing": [
    {
      "cite": "author (year)",
      "used_for": "what role this citation plays",
      "claim_attributed": "what the paper says this source supports"
    }
  ],
  "appendix_references": [
    {
      "ref": "appendix item label",
      "used_for": "what it contributes",
      "location_in_main_text": "where the main text references it"
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
  },
  "entities": {
    "people":       ["Daron Acemoglu", "Esther Duflo"],
    "cited_papers": ["2021__chodorow-reich__mpc-cumulative-stimulus"],
    "concepts":     ["bonacich-centrality", "difference-in-differences"],
    "datasets":     ["FactSet", "Compustat"],
    "institutions": ["NBER", "Stanford"],
    "venues":       ["Econometrica"],
    "topics":       ["network-economics", "monetary-policy"],
    "software":     ["Stata"]
  }
}
```

### entities — wikilink targets for the Obsidian graph

Every name in `entities` MUST already be in **canonical form** per `templates/conventions/wikilinks.md`. The render step does not canonicalize; it only wraps occurrences in `[[...]]`. Misspellings or stylistic variants here become permanent disconnected nodes in the knowledge graph.

Quick reference (full rules in `templates/conventions/wikilinks.md`):
- `people` — `FirstName LastName`, no titles, no commas. Use the full first name when the paper or its metadata reveals it; fall back to `F. LastName` only when genuinely unknown.
- `cited_papers` — `YEAR__lastname__short-title` matching the local papers-library naming. First author's last name, ASCII lowercase; short title is 3–5 words lowercased and hyphenated.
- `concepts`, `topics` — lowercase, hyphenated, **singular**. `[[bonacich-centrality]]`, never `[[Bonacich Centrality]]` or `[[bonacich-centralities]]`.
- `datasets`, `institutions`, `venues`, `software` — preserve the registered casing (`FactSet`, `NBER`, `Econometrica`, `Stata`).

What goes in `entities`:
- **people**: paper authors, prior-work authors the paper credits, named scholars the paper engages with
- **cited_papers**: every load-bearing citation that the paper builds on or contests; not every paper in the bibliography
- **concepts**: tools, methods, theorems the paper uses or extends — only those genuinely load-bearing for the paper, not casual mentions
- **datasets**: any data source the paper uses, by brand name
- **institutions**: affiliations of the authors and any institutions the paper specifically references
- **venues**: the journal of publication (one entry); other venues only if the paper specifically cites them
- **topics**: research areas the paper sits in; one or two are usually enough — too many degrades the graph
- **software**: programming languages, statistical packages, simulation environments the paper uses

What does NOT go in `entities`:
- Generic terms (`welfare`, `equilibrium`, `model`) — the "would I create a standalone note about it?" test from the conventions file
- The paper's own authors when the only mention is in the bylines (frontmatter handles them)
- Common words that happen to be capitalized in the paper title

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
