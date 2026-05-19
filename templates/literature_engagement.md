# Literature engagement track (v2 — graph-traversal via OpenAlex)

Surface specialised older or adjacent works the paper does not cite but probably should engage with. Closes disputatio's "librarian gap" — the failure mode where a closed-book auditor produces correct atomic findings but misses the citation-positioning comments a domain expert referee writes naturally.

This track is **upstream** of Phase 2 discovery, not downstream. The output feeds discovery context so that subsequent narrow_evidence / broad_critic findings can engage the comparator literature when judging novelty, scope, and quantitative-anchoring expectations.

## Why v2 (and not v1)

The v1 design (gemini-flash memory recall → /chrome Scholar verification) was tested blind on the Han-Hu-Zhang paper vs the actual AER Ref #2 report (2026-05-19). Result: **1 / 8 direct hit + 3 / 8 same-family-adjacent**, with most surviving candidates being canonical syllabus papers (Kyle 1985, Ross 1976, Stein 1987 — papers a top-tier author already knows).

Panel review (codex gpt-5.4 + gemini-3.1-pro-preview) converged on the diagnosis:

- **Parametric memory naturally favors most-frequent tokens.** LLM recall from training corpus produces the canonical representative for each adjacency, not the load-bearing comparator the paper actually engages.
- **The paper-text-grounded query target is under-specified.** The paper engages variance-swap-pricing and asymmetric-information-derivatives traditions but doesn't loudly *name* them; Pass A can't reach what the paper doesn't name.
- **Multi-family fan-out doesn't help.** Errors in canonical-bias are correlated across families (all three LLMs push toward the same most-cited papers). Union = noise, intersection = deletes the rare specialist hits.
- **This is a graph-traversal problem, not a semantic-search problem.** To reach a load-bearing comparator like Martin 2017 QJE you ask: *which papers cite [load-bearing ancestor A] AND [load-bearing ancestor B] but are NOT in the current bibliography?* Scholar can't do that AND-filter cleanly; OpenAlex can.

v2 replaces v1's Pass A "propose candidates from memory" + Pass B "/chrome Scholar verification" with a three-pass G+E hybrid:

- **Pass A (LLM)**: identify 3–5 load-bearing structural ancestors in the bibliography.
- **Pass B (OpenAlex)**: graph-traversal — citation-intersection of those ancestors.
- **Pass C (LLM)**: rerank retrieved abstracts by mechanism-overlap with the target paper.

The LLM's job shifts from *generating* citations to *anchoring* the graph query and *evaluating* its results.

## When it fires

One ticket per paper. Emitted in **Wave 1.75**, between Wave 1.5 (holistic) and Wave 2 (discovery). Claude-typed inline (the orchestrator runs the three passes sequentially). Optionally dispatchable as an external `agent-ctl start claude` subprocess when #34 ClaudeSpec lands — agent/type fields are forward-compatible.

`/chrome` MCP is no longer a hard prerequisite. v2 retrieval uses the OpenAlex HTTPS API, not browser automation. `/chrome` remains optional for final candidate spot-checks (e.g., reading a paper's PDF when the OpenAlex abstract is thin), but the pipeline doesn't depend on it.

## Inputs

- Paper spine, main_claims, attack_surface_index (from Wave 1.5)
- `citations_load_bearing[]` from any orientation map (any family's is fine — these are objective bibliography extracts)
- `entities.cited_papers[]` from orientation (full bibliography slugs)
- `_paper/paper.md` for the passage-anchor step (Step 6)

## Confidentiality discipline (hard)

This is the only disputatio phase that deliberately sends content to external services. v2's discipline is structurally tighter than v1's because the OpenAlex query format is `cites:W[ancestor_id]` — IDs of already-published works the paper cites, not text from the paper itself.

Three rules:

1. **OpenAlex queries may use:** Work IDs of already-cited references; the paper's title (publicly known); generic concept tags (e.g., `concept:variance_swap`).
2. **OpenAlex queries may NOT use:** verbatim sentences from unpublished sections, unpublished equations, the author's specific framing of their novel contribution.
3. **LLM evaluator prompts (Pass A and Pass C) may use:** the paper's full text — these calls go to your own gemini/claude subscriptions which are part of the existing pipeline's authorized data flow, not to external scholarly databases.

Rule (1) is naturally enforced by the query syntax — `cites:W123` is a Work ID, not paper text. Rule (3) means Pass A and Pass C use the same data-flow contract as the rest of the disputatio pipeline; no new confidentiality surface.

A `--no-lit-engagement` flag skips this wave entirely if the paper is confidential beyond the strict-mode threshold (rare; the OpenAlex query is paper-bibliography-derived, not paper-content-derived, so strict-mode is the default safe state).

## Procedure

### Step 1 — Pass A: Load-bearing ancestor identification (LLM, paper-content-grounded)

Claude dispatches one `gemini-3-flash-preview` call via `agent-ctl` (or runs inline) with paper spine + bibliography. The prompt asks the LLM to **select ancestors, not generate candidates**:

> "Identify the 3–5 most **load-bearing structural ancestors** in this paper's bibliography. These are NOT foundational citations everyone cites (Arrow, Kyle 1985 generic asymmetric-info, Borch, etc.). They are the direct mechanism-cousins — papers whose specific construction or mechanism this paper extends, refutes, or runs parallel to. For each, name: (a) the cited author/year, (b) what mechanism this paper inherits or extends from them, (c) what the OpenAlex Work ID is or how to look it up."

Output: small structured list of ancestors with mechanism-overlap rationale.

`gemini-3-flash-preview` is the default — stable, fast, good at the selection task. Avoid `gemini-3.1-pro-preview` per the v1 finding (capacity-exhausts on this prompt class).

### Step 2 — OpenAlex Work ID resolution

For each ancestor identified in Step 1 that lacks a known Work ID, resolve via the OpenAlex search endpoint:

```
GET https://api.openalex.org/works?search=<author>+<title-fragment>&per-page=3&mailto=<email>
```

Take the top result as the canonical Work ID. If no confident match (top result has < 50 citations or title diverges), drop the ancestor and document in `unresolvable_ancestors[]`.

### Step 3 — Pass B: Citation traversal (Semantic Scholar primary, OpenAlex fallback)

**Critical empirical finding (smoke test 2026-05-19 on Zhang's bibliography):**

OpenAlex's citation graph is **sparse on pre-2010 econ papers**. Hirshleifer 1990 has 41 forward citations on OpenAlex vs **181 on Semantic Scholar** (4.4× denser). Two-anchor AND-intersection on OpenAlex returns 0–1 results on most ancestor pairs from Zhang's bibliography; same on Semantic Scholar when ancestors cross sub-literatures (Hirshleifer hedging-pressure × Geanakoplos-Polemarchakis incomplete-markets = 0 intersection even with 181 × 200 dense citation sets).

The architectural lesson: **two-anchor AND-intersection only works when both ancestors are in the SAME sub-literature.** Cross-sub-literature pairs produce empty intersections regardless of citation-graph density.

**Revised Pass B procedure:**

1. **Primary: single-anchor citation-fetch + client-side rerank** via Semantic Scholar `/graph/v1/paper/{paperId}/citations` (denser than OpenAlex). For each ancestor `paperId`, fetch up to 200 citing papers (paginated), sorted by `citationCount` desc. Repeat across all 3–5 ancestors. Output: per-ancestor candidate sets.

2. **Secondary (when applicable): within-sub-literature two-anchor intersection.** If two ancestors share a sub-literature (e.g., Hirshleifer 1990 + Breeden 1984, both commodity-futures hedging-pressure), apply the AND-intersection. This is the precision-narrow query the v2 design originally proposed; useful when it works, returns nothing when ancestors are cross-literature.

3. **Tertiary fallback: concept-filter on single anchor.** When the per-ancestor citation-fetch returns too many candidates (>100), narrow by concept filter:

   ```
   GET https://api.openalex.org/works?filter=cites:W_A,concepts.id:<concept_id>&per-page=50
   ```

   Concept IDs come from OpenAlex's concept taxonomy; look up via `scripts/openalex_query.py concept-search <term>`.

The orchestrator combines all returned works into `graph_traversal_candidates[]`. Each entry carries: title, authors, year, venue, cited_by_count, paper_id (SS) or openalex_id, doi.

Mechanical de-dup against the paper's bibliography (`entities.cited_papers[]` + bibliography section parsed from `paper.md`). Drop `already_cited` matches.

**Helper script:** `scripts/openalex_query.py` ships both engines (`openalex resolve/intersect/single/abstract/concept-search` and `ss-resolve/ss-intersect`). Use SS for the primary citation-fetch on econ papers; OpenAlex for concept-filter narrowing and abstract-reconstruction.

### Step 4 — Pass C: LLM evaluation of retrieved abstracts

For the top 20–30 surviving candidates from Step 3 (sorted by cited_by_count desc), fetch abstracts (OpenAlex returns `abstract_inverted_index`; reconstruct to plain text). Feed to Claude or Gemini:

> "Target paper's mechanism: [paragraph from holistic main_claims]. Below are N candidate papers retrieved by citation-intersection traversal of the target's load-bearing ancestors. Which ones **directly threaten, extend, or run parallel to** the target's mechanism? For each: cite the abstract sentence that signals the mechanism-overlap. Drop candidates that are merely topically adjacent without mechanism-overlap."

Output: surviving 4–8 candidates with abstract-anchor on each.

### Step 5 — Passage-anchor selection (Step 6 of v1, retained)

For each Pass C survivor, identify the specific paper passage that would owe engagement with this reference. Allowed anchors:

- A literature-review paragraph that lists nearby strands
- A claim of novelty that overlaps with the candidate's contribution
- A method choice the candidate is known for
- An empirical setting the candidate addressed differently

Output: verbatim quote from `paper.md` + location anchor + one-sentence "why this candidate matters here."

If no passage anchor can be identified, the candidate drops with `status: no_passage_anchor`.

### Step 6 — Ranking (Step 7 of v1, simplified)

Each surviving candidate scored on three dimensions, 0–3 each:

- **Author miss-likelihood** — would a careful author already know this paper? (0 = canonical, must know; 3 = specialised, plausibly missed) — heuristic: papers cited > 500 times AND published before 2000 default to 0 unless evidence otherwise.
- **Mechanism overlap specificity** — how concrete is the mechanism-overlap with the target paper? (0 = topical only; 3 = same construction, different framing) — read from Pass C's abstract-anchor.
- **Engagement obligation** — given the passage anchor, how strongly does the paper owe engagement? (0 = optional related work; 3 = direct competitor mechanism)

`engagement_score = miss_likelihood + 2 × mechanism_overlap_specificity + engagement_obligation` (max 12). Weighting reflects that mechanism-overlap-specificity is the load-bearing signal in v2 (where v1 weighted engagement_obligation).

## Output

Write a single JSON file to `_artifacts/json/literature_engagement.json`:

```json
{
  "schema_version": "literature_engagement_v2",
  "load_bearing_ancestors": [
    {
      "citation": "Hirshleifer (1990), 'Hedging Pressure and Futures Price Movements in a General Equilibrium Model', Econometrica 58(2): 411-428",
      "openalex_id": "W2167298011",
      "mechanism_overlap": "the paper's Section 6.1 explicitly generalises Hirshleifer's GE hedging-pressure result",
      "source": "pass_a_llm_identification"
    }
  ],
  "unresolvable_ancestors": [],
  "graph_traversal_candidates": [],
  "already_cited_drops": [],
  "no_passage_anchor_drops": [],
  "findings": [
    {
      "id": "le_001",
      "candidate": {
        "openalex_id": "W...",
        "citation": "Author (YEAR), Title, Venue Vol(Issue): pages",
        "doi": "10....",
        "cited_by_count": 1234
      },
      "ancestor_pair": ["W_A", "W_B"],
      "mechanism_overlap_evidence": {
        "abstract_sentence": "verbatim sentence from candidate's OpenAlex abstract",
        "why": "1 sentence on how this signals the mechanism-overlap"
      },
      "passage_anchor": {
        "quote": "verbatim from paper.md",
        "location": "section / page",
        "anchor_type": "lit_review | novelty_claim | method_choice | empirical_setting"
      },
      "engagement_rationale": "1 paragraph: what the candidate did, where it overlaps with the paper, why the author should engage.",
      "scores": {
        "miss_likelihood": 0,
        "mechanism_overlap_specificity": 0,
        "engagement_obligation": 0
      },
      "engagement_score": 0
    }
  ]
}
```

## Downstream propagation

After this ticket completes, the orchestrator:

1. Writes `literature_engagement.json` to `_artifacts/json/`.
2. Adds the file to the input list of every Phase 2 discovery ticket prompt (so discovery agents see comparator literature when reasoning about novelty / scope / quantitative anchoring).
3. After Phase 3 merge, the `findings[]` from this template emit as **panel rows** into a top-level array `literature_engagement_findings[]` in `panel.json` — separate from `findings[]` and `dropped_findings[]`.
4. The renderer (Phase 6) gets a dedicated "Suggested literature engagement" section in `panel.md`, the mode-specific memo, and the optional auxiliary output.

## Calibration (different evidentiary contract — same as v1)

Lightweight inline check applied at write time (no separate calibrator sub-DAG):

- **Existence**: Pass B retrieved real OpenAlex records (every Work ID resolves to a real OpenAlex `works/W...` document).
- **Bibliography dedup**: Step 3 mechanical de-dup passed.
- **Mechanism-overlap evidence**: Pass C produced a concrete `abstract_sentence` for each survivor.
- **Passage anchor**: substring-matches `paper.md` (verbatim-quote rule).
- **Engagement obligation ≥ 2**: produced by Step 6.

Rows that fail any check drop to `_calibration/dropped_literature_engagement.json` with the failure reason.

## API specifics

### OpenAlex (concept-filter, abstract reconstruction)

- No API key required. Free, unauthenticated.
- Polite pool: send `mailto=<email>` query parameter. Higher rate-limit priority.
- Rate limit: 100K req/day, 10 req/sec.
- Native AND-filter on `cites:W_A,cites:W_B` and `concepts.id:C_id`.
- Abstract format: `abstract_inverted_index` field — positional index map; reconstruct to plain text via helper.
- **Coverage caveat**: citation graph is sparse on pre-2010 economics papers (Hirshleifer 1990: 41 cites vs 181 on Semantic Scholar). For econ workflows, OpenAlex is best used for concept-filter narrowing and metadata canonicalisation, not as the primary citation-fetch engine.

### Semantic Scholar (primary citation-fetch on econ)

- No API key required for basic use; key available free for higher rate limits.
- Rate limit (unauthenticated): 100 req / 5 min. Aggressive; pace calls.
- Citation-fetch: `/graph/v1/paper/{paperId}/citations?fields=...&limit=100&offset=N` paginated.
- **No native AND-filter** on citation sets — client-side intersection required (helper does this).
- DOI resolution: `/graph/v1/paper/DOI:10.xxx` returns a paper record.
- Free-text search: `/graph/v1/paper/search?query=...`.
- **Recommendations**: `/recommendations/v1/papers/forpaper/{paperId}?limit=15` returns ML-recommended papers. Empirically biased toward fresh/uncited recent papers — useful as *complementary* signal, not as primary candidate source.

Helper: `scripts/openalex_query.py` exposes both engines via subcommands (`resolve`, `intersect`, `single`, `abstract`, `concept-search` for OpenAlex; `ss-resolve`, `ss-intersect` for Semantic Scholar).

### Smoke-test findings (2026-05-19 on Zhang's bibliography)

| Query | Result | Diagnostic |
|---|---|---|
| `openalex resolve "Hirshleifer" "Hedging Pressure Futures Price Movements General Equilibrium"` | W1968347163, Eca 1990 (41 cites) | OpenAlex `search` ranks by relevance; works if title is exact-ish. Use `raw_author_name.search` filter to disambiguate when author surname is common. |
| `openalex intersect W1968347163 W3139998473` (Hirshleifer × Geanakoplos-Polemarchakis) | 0 results | Cross-sub-literature AND-intersection on OpenAlex; sparse. |
| `openalex intersect W1968347163 W2038010306` (Hirshleifer × Breeden, both commodity-futures) | 1 result | Same-sub-literature intersection works but data is thin. |
| `ss-resolve "DOI:10.2307/2938209"` (Hirshleifer 1990) | 181 cites on Semantic Scholar | 4.4× denser than OpenAlex. |
| `ss-intersect Hirshleifer-1990 GP-1986` (cross-literature, dense) | cites_A=181, cites_B=200, **intersection=0** | Cross-sub-literature returns empty even with dense data. **Architectural lesson: two-anchor intersection only works within a sub-literature.** |

## Quality bar

- **5–10 surviving findings is normal.** Below 3 → ancestor identification is too narrow; expand to single-anchor + concept filter. Above 12 → mechanism-overlap-specificity threshold should rise.
- **Canonical-suppression target**: ≤ 30% of surviving candidates should be pre-2010 with > 1000 citations. If higher, Pass A's ancestor selection is leaning canonical (the failure v2 was designed to fix).
- **Novelty check** (post-hoc): a fresh blind Claude pass on the candidate list — "would a top-tier author plausibly say 'I'd never heard of this'?" — target ≥ 50% plausibly-novel-to-a-domain-expert.

## Failure modes

- **OpenAlex API 429** — retry with exponential backoff (60s, 2min, 5min). If still failing, document in `lit_engagement_partial: true` and proceed with what's been retrieved.
- **Ancestor unresolvable** — Pass A names a paper that OpenAlex doesn't index or returns ambiguously. Drop, log, proceed with the remaining ancestors.
- **Pass A selects foundational papers as ancestors** — these are bad anchors (intersection returns the canonical mass). Flag and re-run Pass A with explicit "exclude foundational citations" reminder. Hard rule: every Pass A output must include a `why_load_bearing` field explaining what specific mechanism this paper inherits from the ancestor; "foundational" is not a valid reason.
- **Zero intersection hits** — the ancestor pair is too narrow or one ancestor is itself rare. Fall back to single-anchor + concept filter, document the fallback in the audit trail.
- **All candidates already cited** — the paper is well-positioned. Output empty `findings[]` with a note. Clean outcome.

## Cost

Typical run: 1 Pass A LLM call + 3–8 OpenAlex requests + 1 Pass C LLM call. Wall clock: ~2–5 min. Inference cost: ~$0.05. OpenAlex cost: $0.

Substantially cheaper than v1's 20–30 /chrome navigations.

## Comparison with v1 — what changed

| Aspect | v1 | v2 |
|---|---|---|
| Pass A role | Propose 12–18 candidate citations from memory | Identify 3–5 load-bearing ancestors in bibliography |
| Pass B engine | /chrome Scholar verification + lateral traversal | OpenAlex `cites:W_A,cites:W_B` graph-intersection HTTP query |
| Pass C role | (none — verification was the last step) | LLM reranks Pass B's abstracts by mechanism-overlap |
| /chrome MCP | Hard prerequisite | Optional (for spot-checks only) |
| Confidentiality | Strict-mode rule on query strings | Naturally enforced by query syntax (Work IDs, not text) |
| Wall-clock cost | 20–30 min | 2–5 min |
| Inference cost | ~$0.02 | ~$0.05 |
| External-service cost | $0 (browser) | $0 (free API) |
| Architectural insight | Verify LLM memory | Use LLM to anchor graph queries, then evaluate retrieved nodes |

## What v2 still doesn't do

- **It is not a precision-1.0 specific-must-cite generator.** A specific human referee's specific 8 picks are one defensible candidate set among many; v2 produces a different defensible set with structurally better characteristics (graph-grounded, canonical-suppressed) but not 1:1 alignment to any single referee.
- **It does not catch sub-literatures the paper engages without citing.** If the paper engages variance-swap-pricing without citing Carr-Wu / Martin / Demeterfi-Derman, there's no ancestor in the bibliography to anchor a `cites:W_A` query. Pass A may flag this as a coverage gap; the orchestrator can fall back to concept-filter-only queries, but recall on these sub-literatures remains structurally hard.
- **It does not replace expert domain review.** A top-tier referee's specific picks reflect calibrated knowledge that no LLM has. v2's goal is to surface a useful candidate set, not to replicate a referee.
