# Section brief — §5: archetype-driven literature engagement

**Section title (working):** Pattern 4: Archetype-driven literature engagement

**Word target:** 800-1200 words

**Output path:** `docs/research-notes/methodology-note/sections/05_lit_engagement.md`

## What the section must do

Establish the fourth architectural pattern: instead of generating literature comparators via topic-adjacency search or citation-graph traversal, generate them by reasoning archetypes — five distinct shapes of how a senior referee picks load-bearing comparators. Make the pattern transferable to other fields.

## Key claims the section must support

1. **The two failed predecessors.** Two architectures we tried before this one each scored 0-1/8 on the Han-Hu-Zhang sealed Ref #2 benchmark. Naming them concretely:
   - LLM training-memory recall by topic (gemini-flash memory pass): 1/8 — canonical-syllabus bias dominates; the model returns Kyle 1985, Ross 1976, Stein 1987 when asked for "papers on derivative welfare," missing the load-bearing specific comparators the referee actually named.
   - OpenAlex citation-graph traversal (cites-of-cited-by from the paper's existing bibliography): 0/8 — structural reachability gap; Ref #2's named references do NOT cite any of Zhang's bibliography anchors, so local-graph operations cannot reach them.
2. **The architectural insight.** Reading Ref #2's exact phrasing surfaced five distinct reasoning archetypes that the human referee was using to pick comparators:
   - Substitution-of-assumption
   - Same instrument, different domain
   - Alternative mechanism, same conclusion
   - Mechanism-isomorphic predecessor
   - General theorem behind specific result
   These are field-agnostic; they describe *how* a referee picks comparators, not *what* the comparators are about.
3. **The three-pass procedure.** A1 generates archetype-questions FROM the paper (10-15 questions, archetype-typed, paper-anchored to a specific assumption/proposition/equation). A2 names candidate comparators per question from training memory (codex gpt-5.4 medium-effort, with explicit suppress-canonical rule). A3 confirms via Scholar / Semantic Scholar.
4. **The empirical result on Zhang** (strict-blind, post-contamination-fix): 7/9 of Ref #2's named-and-not-already-cited references surfaced. 6 of those 7 came from A2's training memory alone; the 7th (Martin 2017) also from A2. The 2 misses (Malamud 2008 long-run forward rates; Martin et al 2013 Simple Variance Swaps) are paper-specificity gaps in A2's training distribution, not archetype-question shape gaps. A3 blind subagent added 0 additional Ref #2 refs.
5. **Triangulation as a confidence signal.** GPP 2009 was surfaced by 3 distinct archetype-questions (alternative mechanism, isomorphic predecessor — two slots). That triangulation is a stronger confidence signal than any single-archetype hit. Hirshleifer 1989 EJ was the second triangulation winner (storage substitution + producer hedging predecessor).
6. **The design-overfit caveat is non-negotiable in this section.** The 5 archetype taxonomy was derived (by the prior development team) from reading the AER Ref #2's exact phrasing patterns for each named reference. Zhang is therefore partly a design case for this taxonomy, not a fully held-out test. Today's strict-blind discipline keeps the *execution* clean; it does not retroactively make the protocol design Ref-#2-naive. The 7/9 number should not be read as a *prospective* recall claim. State this explicitly in the section, ideally before the empirical result.

## Source material

Required reading:

- `templates/literature_engagement.md` — full template, especially the "Empirical evidence" section and the new "Blind discipline" section
- `docs/log/2026-05-20_lit-engagement-v3-archetype.md` — the prior team's dev log explaining the v3 architecture and the five-archetype derivation
- `docs/log/2026-05-20_strict-blind-discipline.md` — today's strict-blind re-run with corrected 7/9 result
- `draft.md` §§1-4 for tone match

Optional / lift-from where useful:

- `SKILL.md` Phase 1.75 section
- `templates/emit_tickets.md` Wave 1.75 entry

## Domain-portability discussion (end of section)

The five archetypes are field-agnostic by construction — they describe a referee's question shape, not topic content. Notes a forker needs:

- A field-specific Scholar / database backend (PubMed for biotech, SSRN for econ/finance, arXiv for ML/physics, Westlaw for legal). The Semantic Scholar API works for most of these via their unified graph.
- A field-specific suppress-canonical list. In economics: Kyle 1985, Stein 1987, Ross 1976, Admati 1985, Hellwig 1980, Grossman-Stiglitz 1980, Black-Scholes. In other fields the canonical-syllabus papers will be different but the dynamic is identical — A2 needs to be steered off them or it returns the foundational reps not the load-bearing comparators.
- A field-specific question-shape calibration. The five archetypes generalize, but specific archetype weights may differ. Legal review may lean heavily on "same-instrument-different-domain" (precedent in different jurisdictions). Biotech may lean on "mechanism-isomorphic predecessor" (similar mechanism in adjacent organism).

## Tone-match anchors from §§1-4

- The "we want to be careful here" cadence from §3 when discussing Route B's interpretation
- The willingness to disclose competing interpretations (over-pruning vs accuracy gain)
- The single-paragraph "the pattern transfers because..." closer used in §§2-3

## Anti-patterns to avoid

- Marketing the archetype framework as a discovered universal. It is a useful heuristic backed by one case study; treat it that way.
- Burying the design-overfit caveat in a footnote. It belongs in the section's argument, ideally before the empirical result lands.
- Listing all 13 archetype-questions from the Zhang run. The reader needs the *shape* of the taxonomy, not the specific 13 instances. Use 2-3 illustrative examples max.
- Comparing to other lit-engagement tools by name. Stay descriptive about what topic-adjacency search and citation-graph traversal do; do not punch at specific products.

## Open questions to flag in your output (if relevant)

- Whether the 5-archetype taxonomy is sufficient or whether additional archetypes (e.g., "negative result in adjacent literature," "competing empirical claim") would extend recall. The current taxonomy was derived from one referee's report.
- Whether the suppress-canonical list belongs in the template or should be paper-specific. Today it is hard-coded in the prompt; a fork would need to re-tune per field.
- Whether triangulation (archetype_coverage ≥ 2) is the right confidence signal or whether semantic similarity across archetype-question phrasings would do better. We have not measured this.
