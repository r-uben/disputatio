# Worked example — entities → wikilinks

This file is a synthetic test of the `entities` schema introduced in `templates/orient.md` and the entity-wrap pass added to `templates/obsidian_render.md`. It shows one fabricated paper map, the body text the renderer would emit before wrapping, and the wrapped output. Anyone changing the canonicalisation rules in `templates/conventions/wikilinks.md` should make sure this example still round-trips.

## Input — fabricated paper map (excerpt)

```json
{
  "title": "Targeting interventions in networks",
  "authors": ["Andrea Galeotti", "Benjamin Golub", "Sanjeev Goyal"],
  "venue": "Econometrica",
  "main_claims": [
    {
      "id": "C1",
      "claim": "Optimal targeting of a planner intervening in a quadratic-utility network game depends on the Bonacich centrality of the principal eigenvector.",
      "location": "Section 3, Theorem 1",
      "type": "theoretical"
    }
  ],
  "citations_load_bearing": [
    {
      "cite": "Ballester, Calvo-Armengol & Zenou (2006)",
      "used_for": "Establishes Bonacich centrality as the equilibrium effort vector",
      "claim_attributed": "Equilibrium effort is proportional to weighted Bonacich centrality"
    }
  ],
  "datasets": [
    {"name": "Indian Microfinance",
     "source": "Banerjee, Chandrasekhar, Duflo & Jackson (2013)",
     "period": "2007-2011",
     "used_for": "Network structure for the empirical calibration"}
  ],
  "entities": {
    "people":       ["Andrea Galeotti", "Benjamin Golub", "Sanjeev Goyal",
                     "Coralio Ballester", "Antoni Calvo-Armengol", "Yves Zenou",
                     "Abhijit Banerjee", "Esther Duflo", "Matthew Jackson"],
    "cited_papers": ["2006__ballester__whos-who-key-player",
                     "2013__banerjee__diffusion-microfinance"],
    "concepts":     ["bonacich-centrality", "principal-eigenvector",
                     "quadratic-utility", "network-game"],
    "datasets":     ["Indian Microfinance"],
    "institutions": ["Bocconi", "Stanford", "NBER"],
    "venues":       ["Econometrica"],
    "topics":       ["network-economics", "information-design"],
    "software":     []
  }
}
```

## Pre-wrap render (what `obsidian_render.md` produces from the JSON before the entity pass)

```markdown
# Galeotti, Golub & Goyal — Paper map

## Paper metadata
- **Title**: Targeting interventions in networks
- **Authors**: Andrea Galeotti, Benjamin Golub, Sanjeev Goyal
- **Venue**: Econometrica

## Main claims
- **C1** (Section 3, Theorem 1, theoretical): Optimal targeting of a
  planner intervening in a quadratic-utility network game depends on
  the Bonacich centrality of the principal eigenvector.

## Load-bearing citations
- Ballester, Calvo-Armengol & Zenou (2006) — Establishes Bonacich
  centrality as the equilibrium effort vector. Attributed claim:
  Equilibrium effort is proportional to weighted Bonacich centrality.

## Datasets
- **Indian Microfinance** (Banerjee, Chandrasekhar, Duflo & Jackson
  (2013), 2007-2011) — Network structure for the empirical calibration.
```

## Post-wrap render (what should ship to `0_orientation/<agent>.md`)

```markdown
# [[Andrea Galeotti|Galeotti]], [[Benjamin Golub|Golub]] & [[Sanjeev Goyal|Goyal]] — Paper map

## Paper metadata
- **Title**: Targeting interventions in networks
- **Authors**: [[Andrea Galeotti]], [[Benjamin Golub]], [[Sanjeev Goyal]]
- **Venue**: [[Econometrica]]

## Main claims
- **C1** (Section 3, Theorem 1, theoretical): Optimal targeting of a
  planner intervening in a [[quadratic-utility]] [[network-game]] depends on
  the [[bonacich-centrality|Bonacich centrality]] of the [[principal-eigenvector]].

## Load-bearing citations
- [[2006__ballester__whos-who-key-player|Ballester, Calvo-Armengol & Zenou (2006)]]
  — Establishes [[bonacich-centrality|Bonacich centrality]] as the
  equilibrium effort vector. Attributed claim: Equilibrium effort is
  proportional to weighted [[bonacich-centrality|Bonacich centrality]].

## Datasets
- **[[Indian Microfinance]]** ([[2013__banerjee__diffusion-microfinance|Banerjee, Chandrasekhar, Duflo & Jackson (2013)]], 2007-2011) —
  Network structure for the empirical calibration.
```

## What this checks

- **People in the byline get the alias-pipe form** (`[[Andrea Galeotti|Galeotti]]`) so the heading reads naturally while the graph edge points at the canonical note.
- **Authors in the metadata block use the bare canonical form** because the metadata field is read as a list, not prose.
- **Concepts canonicalise to lowercase-hyphenated-singular** with the alias-pipe form for capitalised mentions in prose: `[[bonacich-centrality|Bonacich centrality]]` not `[[Bonacich centrality]]` and not `[[Bonacich Centrality]]`. Three reviews citing this paper produce one shared note.
- **Cited papers use the library-naming form** (`YEAR__lastname__short-title`) with the alias-pipe form supplying the academic citation style for prose.
- **Venues stay capitalised** (`[[Econometrica]]`) because that is the canonical brand form.
- **Datasets preserve casing** (`[[Indian Microfinance]]`) for the same reason.
- **Institutions in the entities list but absent from the rendered body do NOT appear in the output**. The wrap pass only acts on text that exists; it does not inject mentions. `[[Bocconi]]`, `[[Stanford]]`, `[[NBER]]` from the entities list never appear because the rendered body does not name them — that is correct behaviour.
- **Authors are not self-linked when only mentioned in their own paper's byline**. Per the convention in `templates/conventions/wikilinks.md`, the header line uses aliases pointing at the canonical notes, but the prose claim ("a planner intervening in a quadratic-utility network game") does NOT name them and so does not link them. If a later finding said "Galeotti et al. argue that...", THAT mention would be wrapped.

## What this does NOT check

This is a paper-map-level smoke. Three things it intentionally skips:

1. **Three-agent reconciliation.** The convention says when claude / codex / gemini disagree on canonical form, the orchestrator picks the longer one and logs the reconciliation. That requires three separate orient JSONs and a real reconciler — out of scope for a single-fixture sanity check.
2. **Wrap behaviour inside discovery / debate / report markdown.** Same conventions apply, but each of those render targets has its own template; verifying the rule across all of them needs either real outputs or a much larger fixture set. Single-paper-map check is enough to validate the convention; the per-template integration falls out of the next real review.
3. **Orphan-link visibility in the actual Obsidian graph view.** `[[2006__ballester__whos-who-key-player]]` will show up as an "unresolved" node until a corresponding note exists in the vault. That is correct behaviour but only confirmable in Obsidian itself, not in markdown.

The next real disputatio review will exercise (1)–(3); this file ensures the schema and the canonical forms are internally consistent before that run.
