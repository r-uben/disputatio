# 2026-05-19 — Literature engagement v2 (graph-traversal via citation APIs)

## Why v2 — v1 failed under blind conditions

The v1 design (PR #36, `feat/33-literature-engagement-track` @ `6ad492b`) used `gemini-3-flash-preview` Pass A memory recall + `/chrome` Scholar verification. A blind empirical test on Zhang's "Markets for Price Risk" vs the actual AER Ref #2's 8 named specialised references scored **1/8 direct + 3/8 same-family-adjacent**. An earlier "8/8" test was contaminated — queries were constructed by lifting Ref #2's specific titles verbatim.

Panel review (codex gpt-5.4 high-effort + gemini-3.1-pro-preview) converged on the diagnosis:

- Parametric memory naturally favors most-frequent-token canonical papers (Kyle 1985, Ross 1976) — exactly the references a top-tier author already knows. Anthony's stated value was "helpful old references I'd never heard of," which canonical-bias precisely fails to deliver.
- The paper-text-grounded query target is under-specified — the paper engages variance-swap-pricing and asymmetric-info-derivatives traditions but doesn't name them, so Pass A can't reach what the paper doesn't name.
- Multi-family fan-out doesn't help — errors in canonical-bias are correlated across families (all LLMs push toward most-cited).
- This is a graph-traversal problem, not a semantic-search problem.

## v2 architecture (G+E hybrid per panel verdict)

- **Pass A (LLM)** — identify 3–5 load-bearing structural ancestors in the bibliography. Selection, not generation.
- **Pass B (citation API)** — traverse the citation graph of the ancestors. Two-anchor AND-intersection when ancestors share a sub-literature; single-anchor citation-fetch + LLM rerank otherwise.
- **Pass C (LLM)** — rerank by mechanism-overlap with the target paper. Drop topically-adjacent-but-mechanism-distinct.

The LLM's job shifts from generating citations to anchoring graph queries and evaluating retrieved candidates.

## Critical empirical finding (2026-05-19 smoke test)

Initial design used OpenAlex's `cites:W_A,cites:W_B` native AND-filter. Empirical testing of the helper revealed:

1. **OpenAlex citation coverage is sparse on pre-2010 econ papers.** Hirshleifer 1990 has **41 forward citations on OpenAlex vs 181 on Semantic Scholar** — 4.4× denser on SS. Most older Eca/JPE/QJE econ papers are similar.

2. **Two-anchor AND-intersection returns 0 candidates when ancestors cross sub-literatures**, even with dense Semantic Scholar coverage. Test: Hirshleifer 1990 (commodity-futures hedging-pressure, 181 cites) × Geanakoplos-Polemarchakis 1986 (incomplete-markets GEI, 200 cites) → intersection = 0. The two papers' citation sets simply don't overlap because they're from different sub-literatures.

3. **Within-sub-literature intersections work but are thin.** Hirshleifer × Breeden 1984 (both commodity-futures) → 1 result. Real signal when the ancestors match, but data is structurally sparse on this domain.

**Architectural lesson:** AND-intersection is precision-narrow but cross-literature-empty. The robust default is single-anchor citation-fetch (Semantic Scholar, 181+ candidates per ancestor) + LLM rerank.

## What this commit ships

- `templates/literature_engagement.md` — v2 protocol; supersedes v1's gemini-flash + /chrome design. Three-pass G+E hybrid. Pass B procedure prioritises single-anchor citation-fetch with two-anchor AND-intersection as the within-sub-literature precision query (when applicable).
- `scripts/openalex_query.py` — Python helper exposing both engines:
  - OpenAlex: `resolve`, `intersect`, `single` (anchor + concept filter), `abstract` (inverted-index reconstruction), `concept-search`.
  - Semantic Scholar: `ss-resolve` (DOI or free-text), `ss-intersect` (client-side AND-intersection of dense citation sets).
  - No API key required for either; both APIs free.
- `SKILL.md` — Phase 1.75 entry rewritten for v2; includes empirical finding and architectural lesson.
- `templates/emit_tickets.md` — Wave 1.75 entry rewritten; removes /chrome MCP hard prerequisite; documents v1→v2 supersession.

## What this commit does NOT ship

- **Smoke test against Ref #2 with full v2 implementation.** The helper script is tested and works; running the full three-pass pipeline against Zhang and scoring against Ref #2 is the next step.
- **OpenAlex / Semantic Scholar coverage benchmarking on 2–3 more papers.** n=1 on Zhang shows the sparse-on-econ pattern; multiple-paper validation would establish the pattern firmly.
- **Recommendation: prefer Semantic Scholar `/recommendations/v1/papers/forpaper/{id}` for fuzzy expansion** when intersection returns < 3 hits. Helper has the endpoint plumbed but not exposed as a subcommand yet.
- **PR #36 deprecation.** PR #36's v1 templates remain; v2 supersedes the architecture, but PR #36's commits are preserved as historical reference per #42 issue's recommendation.

## Test plan (next step, not in this commit)

Run the full three-pass pipeline against Zhang's workspace. Specifically:

1. Pass A — gemini-flash identifies 3–5 load-bearing ancestors. Confirm they're not foundational (Hirshleifer/Borch/Kyle generic) but specific mechanism-cousins.
2. Pass B — `scripts/openalex_query.py ss-intersect` on within-sub-literature pairs; `ss-resolve` + manual `ss-citations` traversal on cross-literature single anchors. Capture 30–50 candidates total.
3. Pass C — Claude reranks abstracts. Survivors: 4–8.
4. Score vs Ref #2's 8 named references.
5. Canonical-suppression check: ≤ 30% of survivors are pre-2010 with > 1000 cites.

Target: ≥ 4/8 direct hits on Ref #2 (v1 blind: 1/8); canonical-suppression ≤ 30%.

If the target isn't hit, the next iteration is to add `forpaper` recommendations + manual concept-tag enrichment. If it still isn't hit, the architectural conclusion is that **no automated system can reliably reach a specific human referee's specific picks**, and v2 ships as the best-effort librarian-candidate-generator rather than a referee-replicator.

## Files

- `templates/literature_engagement.md` — v2 protocol (full rewrite from v1's #36 version)
- `scripts/openalex_query.py` — dual-engine helper
- `SKILL.md` — Phase 1.75 entry
- `templates/emit_tickets.md` — Wave 1.75 entry
- `docs/log/2026-05-19_lit-engagement-v2-openalex.md` — this dev log

## Refs

- #33 (v1 lit-engagement, supersedes)
- #36 (v1 PR; recommend not merge — superseded)
- #42 (v2 design issue, this commit implements)
- Panel review 2026-05-19 (codex gpt-5.4 + gemini-3.1-pro-preview)
