# Wikilink conventions

Disputatio reviews live in an Obsidian vault that already holds notes on people, papers, concepts, datasets, and institutions. When a review mentions any of those entities, the mention should be a wikilink (`[[Canonical Name]]`) so Obsidian's backlink engine adds an edge to the knowledge graph. Three reviews citing the same author become connected only if all three spell the author the same way.

This file is the single source of truth for canonical entity names. The orient phase extracts entities into the paper map's `entities` block; render templates read that block and wrap mentions wherever they appear in curated markdown. **Agents do not invent wikilink names** — they pick a canonical form per the rules below; render code substitutes mechanically.

## Canonical forms

| Entity type | Canonical form | Examples |
|---|---|---|
| **Person** | `[[FirstName LastName]]` — full given and family names, no titles, no commas, no initials when the full first name is known. | `[[Daron Acemoglu]]`, `[[Esther Duflo]]`, `[[Ben Golub]]` |
| **Person (initials only)** | `[[F. LastName]]` only when the full first name is genuinely unknown from the paper or the metadata. | `[[A. Galeotti]]` is wrong if the paper signs Andrea Galeotti — use `[[Andrea Galeotti]]` |
| **Cited paper** | `[[YEAR__lastname__short-title]]` — matches the local papers-library naming under `~/.../Library/Papers/papers/`. Use the FIRST author's last name, lowercase, ASCII; short title is 3–5 words, lowercased and hyphenated. | `[[2021__chodorow-reich__mpc-cumulative-stimulus]]`, `[[2020__galeotti__targeting-interventions-networks]]` |
| **Concept / method** | lowercase, hyphenated, singular. | `[[bonacich-centrality]]`, `[[difference-in-differences]]`, `[[immanent-critique]]`, `[[network-economics]]` |
| **Dataset** | brand name as registered, preserve case. | `[[FactSet]]`, `[[Compustat]]`, `[[CRSP]]`, `[[Trucost]]` |
| **Institution** | short canonical, no "University of" prefix unless ambiguous. | `[[Stanford]]`, `[[Bocconi]]`, `[[NBER]]`, `[[CEPR]]` |
| **Venue / journal** | short canonical, prefer the journal's standard abbreviation. | `[[Econometrica]]`, `[[QJE]]`, `[[AER]]`, `[[REStud]]` |
| **Topic / field** | lowercase, hyphenated. Same shape as concepts; the distinction is granularity (a topic is a research area, a concept is a specific tool or definition). | `[[monetary-policy]]`, `[[network-economics]]`, `[[information-design]]` |
| **Software / tool** | brand name as registered. | `[[Python]]`, `[[R]]`, `[[Stata]]`, `[[Julia]]`, `[[PyTorch]]` |

## Rules of thumb

**Don't wikilink common words.** "Welfare" appearing in prose is not `[[welfare]]`. The rule: if you wouldn't create a standalone Obsidian note about it, don't link it. Concepts that are actually load-bearing in the paper (the paper's central object of study) are linkable; throwaway adjectives and conjunctions are not.

**Don't link the paper's own authors inside its own review.** The review note already names them in frontmatter; linking them inside the body inflates self-references and adds no graph value. Do link them when discussing prior work by the same authors ("As [[Daron Acemoglu]] showed in [[2002__acemoglu__directed-technical-change]]...").

**Pluralize via aliases, not separate notes.** `[[bonacich-centrality|Bonacich centralities]]` displays "Bonacich centralities" but links to the singular note. Avoid creating both `[[bonacich-centrality]]` and `[[bonacich-centralities]]` — they would be orphan siblings in the graph.

**Use the alias pipe for natural prose.** `[[difference-in-differences|DiD]]` reads naturally inline and still connects the graph to the canonical note. Same for `[[2020__galeotti__targeting-interventions-networks|Galeotti, Golub & Goyal (2020)]]` when the citation needs to read like a normal academic reference.

**Disambiguate institutions when needed.** `[[Stanford]]` is fine for the university; `[[Stanford GSB]]` or `[[Stanford Economics]]` only when the paper specifically references the school. Don't proliferate sub-entities unless the graph needs them.

**Cited papers without local notes are still linked.** Even if the paper has not been read or OCR'd locally, the wikilink creates a placeholder. When the paper later joins the library, the placeholder resolves automatically.

**Lowercase, hyphenated, singular for concepts** is a strict rule because the graph depends on it. `[[Bonacich Centrality]]` and `[[bonacich-centrality]]` and `[[bonacich centrality]]` would be three separate notes. The orchestrator must canonicalize before emitting.

## Provenance: where the entity list comes from

Entities are extracted during the **orient** phase by each reading agent and stored in the paper map JSON under `entities`:

```json
"entities": {
  "people":       ["Daron Acemoglu", "Esther Duflo"],
  "cited_papers": ["2021__chodorow-reich__mpc-cumulative-stimulus", ...],
  "concepts":     ["bonacich-centrality", "difference-in-differences"],
  "datasets":     ["FactSet", "Compustat"],
  "institutions": ["NBER", "Stanford"],
  "venues":       ["Econometrica"],
  "topics":       ["network-economics", "monetary-policy"],
  "software":     ["Stata"]
}
```

Names in this list are already in canonical form (the agent applies the table above). Render templates then wrap any occurrence of a canonical name (or a documented alias) in `[[...]]` when emitting curated markdown for `0_orientation/`, `1_discovery/`, `2_ranking/`, `3_debates/`, `4_report/`, and `_evaluation/`.

## Three-agent reconciliation

Orientation runs three independent readers; each produces its own entities list. The lists are NOT merged automatically — model independence applies here too. But before render, the orchestrator unions the three lists and drops duplicates (case-insensitive comparison on the canonical form). If the three readers disagree on canonicalization (`Daron Acemoglu` vs `D. Acemoglu`), the orchestrator picks the longer/more-complete form and logs the reconciliation in `_artifacts/sessions/orient_reconcile.log`.

Disagreements about whether something IS an entity (one reader includes `[[network-economics]]` as a topic, another doesn't) are resolved by inclusion: if any reader flagged it, it goes in the union. The cost of an extra wikilink is a marginal graph edge; the cost of missing one is a disconnected node forever.

## What this file is NOT

- It is not a vocabulary of allowed entities. New people, papers, and concepts get canonical names invented by the orient agent following the rules above; the agent does not need pre-approval to mention `[[Some New Author]]`.
- It is not a list of existing notes in the vault. Wikilinks to non-existent notes are valid Obsidian behaviour — they show up as "unresolved" placeholders and resolve when a note with that name is created later.
- It is not a style guide for prose. It only governs the `[[...]]` wrapper. Whether a sentence reads well with seven wikilinks vs one is the writer's call (but per the "common words" rule above, fewer is usually better).
