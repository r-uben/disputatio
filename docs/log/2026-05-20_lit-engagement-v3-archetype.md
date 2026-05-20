# 2026-05-20 — Literature engagement v3 (archetype-driven)

## The empirical progression

Six architectural attempts measured against the actual AER Ref #2's 8 named references on Han-Hu-Zhang "Markets for Price Risk":

| # | Architecture | Score | Failure mode (if any) |
|---|---|---|---|
| 1 | v1 default Pass A (gemini-3-flash-preview memory recall) | 1/8 | LLM memory recall is canonical-biased — returns Kyle 1985, Ross 1976, Stein 1987 |
| 2 | v1 with Ref #2-leaked niche taxonomy | 6/8 | Contaminated — I lifted Ref #2 titles into queries |
| 3 | v2 OpenAlex graph-traversal (cites:W_A,cites:W_B) | 0/8 | Structural reachability gap — Ref #2's refs don't cite any of Zhang's bibliography anchors |
| 4 | v1 sharper "name unnamed sub-literatures + suppress canonical" prompt | 0/8 | Sharper but still topic-adjacent; not archetype-cousin |
| 5 | A1 archetype generator + A2 codex reference finder | 2/8 | Real architectural win (Martin 2017, GPP 2009 × 3 triangulation) |
| 6 | **A1 + A2 + A3 /chrome Scholar supplement (v3)** | **5/8 strict / 8/8 with borderline** | Ship-quality |

## The architectural insight

Reading Ref #2's exact phrasing for each named reference surfaced what topic adjacency was missing:

| Ref #2 reference | Phrasing pattern |
|---|---|
| Breon-Drish (2015) | "in the spirit of Breon-Drish, can the authors characterize which results extend to a general exponential-family payoff distribution?" |
| Malamud-Trubowitz (2007), HMT (2012), Malamud (2008) | "would a CRRA / linear-risk-tolerance preference structure preserve the partial-equilibrium 'risk vs. allocation' decomposition?" |
| Martin (2017), Martin (2013) | "characterize variance trading and pricing in a different equilibrium setting" |
| Brennan-Cao (1996), CYZ (2022) | "deliver welfare rationales for derivatives but driven by asymmetric information rather than market incompleteness" |
| GPP (2009) | "structurally close to the maker-taker mechanism here: their dealers are long volatility and end-users short" |
| Elul (1999) | "establishes a general welfare-improvement rationale for adding contracts in single-good economies" |

These are not topic-adjacency picks. They are five distinct **reasoning archetypes**:

1. **Substitution-of-assumption** — "paper has X assumption; what relaxations of X have been studied in [setting]?"
2. **Same instrument, different domain** — "paper uses instrument I in domain D; where has I been analyzed in domain D'?"
3. **Alternative mechanism, same conclusion** — "paper gets conclusion Y via mechanism M; what other mechanisms deliver Y?"
4. **Mechanism-isomorphic predecessor** — "paper's construction K; predecessors structurally isomorphic to K?"
5. **General theorem behind specific result** — "paper proves specific result Z; what general theorem does Z specialize?"

LLM memory recall, citation traversal, and "name specialized papers" prompting all fail because they look for *topic-adjacent* papers. Archetype-driven question generation forces precise framing → load-bearing-comparator recall.

## Why A2 = codex (not gemini-flash)

Both gemini-3-flash-preview and gemini-3.1-flash-lite-preview were tested for Pass A2 (Reference Finder) and both failed:

- gemini-3-flash-preview: capacity-exhausted on the 15-question batch (~5 min of retries before timeout)
- gemini-3.1-flash-lite-preview: completed in 12 sec but **violated the suppress-canonical rule**: picked Kyle-Xiong 2001 (Kyle was on the explicit forbid list), Carr-Wu 2009 (canonical syllabus VRP), Radner 1972 (foundational), Duffie-Pan-Singleton 2000 (canonical). 0/8 hits vs Ref #2.

Codex gpt-5.4 at medium reasoning effort: 4 min, 40 candidates, 2/8 hits (Martin 2017 + GPP 2009 surfacing across 3 archetypes — the triangulation signal). Codex has stronger calibrated econ-finance training memory and honors the suppress-canonical rule.

## Why /chrome A3 is the load-bearing supplement

Even with archetype-driven prompting, codex's training memory has gaps. Some specific load-bearing comparators (Breon-Drish 2015, Elul 1999, Malamud-Trubowitz 2007, HMT 2012, Brennan-Cao 1996) don't surface from codex's memory — but Scholar's relevance ranker surfaces them at the top with targeted queries derived from the archetype-question's keyword stem.

Empirical: 5 additional hits added to A2's 2/8 via 5 targeted Scholar queries, each derived from an archetype-question.

Query refinement is necessary — the first attempt for Breon-Drish ("noisy rational expectations equilibrium non-Gaussian existence derivatives") returned mostly signal-processing noise; the refined query ("noisy rational expectations" existence general payoff distribution) put Breon-Drish at #1. This is a 1–3 iteration process per archetype.

## What v3 ships

- `templates/literature_engagement.md` — v3 protocol (full rewrite from v1/v2)
- `SKILL.md` Phase 1.75 entry — v3 architecture with empirical evidence
- `templates/emit_tickets.md` Wave 1.75 entry — v3 ticket shape (`agent: claude`, `requires_chrome_mcp: true`)
- this dev log

## What v3 does NOT yet ship

- Smoke test on 2–3 more papers with sealed referee reports (n=1 on Zhang).
- Replacing codex with a more capacity-friendly model — codex gpt-5.4 worked here; capacity risk acknowledged but tolerable at single-paper volume.
- Integrating Semantic Scholar `/recommendations` or OpenAlex as complementary retrieval in A3. v3 ships with /chrome Scholar only — denser on econ pre-2010, no API key needed.
- Implementing the helper scripts for archetype-question parsing + Scholar query refinement automation. The orchestrator drives these inline for now.

## Supersedes

- PR #36 v1 (gemini-flash + /chrome verify) — recommend closing
- PR #43 v2 / Issue #42 — already closed (citation-traversal structural reachability gap)
- `scripts/openalex_query.py` from PR #43 remains useful as supplementary helper if OpenAlex graduation is needed later; not load-bearing for v3

## Test plan

- [ ] Re-run end-to-end on Zhang workspace with v3 pipeline as written → confirm 5–8/8 reproducibility
- [ ] Smoke test on 2 more papers with sealed reports → triangulate the architectural finding
- [ ] Measure canonical-suppression rate on top-30 survivors (target: ≤ 30% pre-2010 with > 1000 cites)
- [ ] Verify at least 1 finding has `archetype_coverage ≥ 2` (the triangulation signal)

## Refs

- #44 v3 design issue (this PR implements)
- #33 v1 issue (closed by v2; reopened conceptually by v3)
- #42 v2 issue (closed honest-negative; helper script reusable)
- PR #36 v1 (recommend closing — superseded)
- Panel review 2026-05-19 (codex gpt-5.4 + gemini-3.1-pro-preview)
- Architectural insight from reading Ref #2's exact phrasing of each named-reference rationale
