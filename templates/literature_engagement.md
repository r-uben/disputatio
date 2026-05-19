# Literature engagement track (v6.x — new)

Surface specialized older or adjacent works the paper does not cite but probably should engage with. Closes disputatio's "librarian gap" — the failure mode where a closed-book auditor produces correct atomic findings but misses the citation-positioning comments a domain expert referee writes naturally.

This track is **upstream** of Phase 2 discovery, not downstream. The output feeds discovery context so that subsequent narrow_evidence / broad_critic findings can engage the comparator literature when judging novelty, scope, and quantitative-anchoring expectations.

## When it fires

One ticket per paper. Emitted in **Wave 1.75**, between Wave 1.5 (holistic) and Wave 2 (discovery). Single agent — `gemini` with search grounding — chosen over per-family fan-out because the failure mode is **retrieval**, not cross-family reasoning. Three LLMs from memory will overproduce canonical references and underproduce long-tail specialized adjacency; one grounded search-capable model with structured query design does the job.

Optional `/chrome` follow-up for Google Scholar verification + lateral "Cited by N" / "Related articles" traversal on any unverifiable candidate.

## Inputs

- Paper spine, main_claims, attack_surface_index (from Wave 1.5)
- `citations_load_bearing[]` from any orientation map (any family's is fine — these are objective bibliography extracts)
- `entities.cited_papers[]` from orientation (full bibliography slugs)
- `_paper/paper.md` for the passage-anchor step
- **NOT** the full paper text in the search queries — see Confidentiality below

## Confidentiality discipline (hard)

This is the only disputatio phase that deliberately sends content to external services. Two rules:

1. **Search queries may use:** paper title, abstract themes (paraphrased), publicly named methods (e.g., "CARA-quadratic-Gaussian"), the headline mechanism in generic terms, names of *already-published* citations the paper engages with.
2. **Search queries may NOT use:** verbatim sentences from unpublished sections, unpublished equations, the author's specific framing of their novel contribution.

The prompt enforces this by instructing the agent to extract a "search vocabulary" first from the spine + key terms, and to use *only* that vocabulary in queries. Verbatim passage quoting from the paper is reserved for the final output rows (which document *which passage* would owe engagement), not for the search step.

A `--lit-engagement [strict|relaxed]` flag exposes the choice:
- `strict` (default): themes + keywords + already-cited works only.
- `relaxed`: short paraphrased sentences from the paper allowed, for harder retrieval cases.

## Procedure

### Step 1 — Build the search vocabulary

From the inputs:
- 4–6 method nouns (e.g., "CARA utility", "Gaussian Q-measure", "variance swap pricing")
- 4–6 mechanism nouns (e.g., "hedging pressure equilibrium", "spot market basis risk", "price-contingent risk sharing")
- The set of load-bearing already-cited works, by author-year

Write to `search_vocabulary[]` in the output JSON. The annotator can audit this against the confidentiality rule.

### Step 2 — Pass A: Model-memory recall (no search)

Prompt the gemini worker with the vocabulary and ask:
> "Drawing only on your training-corpus memory (no web search yet), name 8–12 specialized older or adjacent works on these topics that a domain expert would consider when refereeing a paper in this lineage. Include author + year + venue + one-sentence relevance for each. Prefer older or specialized works over recent canonical ones — the heuristic is 'long-tail adjacency the author may not have considered.'"

Capture the raw candidate list as `memory_recall_candidates[]`.

### Step 3 — Pass B: Search-grounded recall

Same vocabulary, but enable Gemini's search grounding:
> "Given this search vocabulary, search the web (Google Scholar, NBER, SSRN) for older or specialized adjacent works in the same lineage. Report 8–12 candidates with author + year + venue + DOI or URL and a one-sentence reason this paper should engage. Prefer specialised / older / less-canonical works."

Capture as `search_grounded_candidates[]`.

### Step 4 — Verification

For every candidate from Pass A or Pass B that lacks a verifiable URL/DOI:
- Send to `/chrome` to navigate Google Scholar, search the candidate's title + first author + year, and capture the first matching result's metadata
- If no match: drop the candidate, log as `unverifiable` in the output

For candidates that exist: record canonical citation form, DOI or stable URL, and the Scholar "Cited by N" count.

### Step 5 — Bibliography dedup

Mechanical regex / fuzzy match against:
- `entities.cited_papers[]` from orientation
- `citations_load_bearing[]` 
- The paper's bibliography section (parsed from `_paper/paper.md`)

Anything already cited drops with `status: already_cited`. Anything left is a v6 candidate.

### Step 6 — Passage-anchor selection

For each surviving candidate, identify the specific paper passage that would owe engagement with this reference. Allowed anchors:
- A literature-review paragraph that lists nearby strands
- A claim of novelty that overlaps with the candidate's contribution
- A method choice the candidate is known for
- An empirical setting the candidate addressed differently

Output: verbatim quote from `paper.md` + location anchor + one-sentence "why this candidate matters here."

If no passage anchor can be identified, the candidate drops with `status: no_passage_anchor` — the rule is "we surface the reference *because* a specific passage in the paper would owe engagement," not "we surface the reference because it exists."

### Step 7 — Ranking

Each surviving candidate scored on three dimensions, 0–3 each:

- **Author miss-likelihood** — would a careful author already know this paper? (0 = canonical, must know; 3 = specialised, plausibly missed)
- **Engagement obligation** — how strongly does the cited passage owe engagement? (0 = optional related work; 3 = direct competitor mechanism)
- **Specificity of the connection** — how concrete is the link between the candidate and the passage? (0 = vague topic match; 3 = same construction, different framing)

`engagement_score = miss_likelihood + 2 × engagement_obligation + specificity` (max 12). The weighting mirrors merge_and_rank.md's cross_agent_support weighting — the strongest signal (obligation) is weighted double.

## Output

Write a single JSON file to `_artifacts/json/literature_engagement.json`:

```json
{
  "search_vocabulary": ["..."],
  "memory_recall_candidates": [
    {
      "citation": "Breon-Drish (2015), 'On Existence and Uniqueness of Equilibrium in a Class of Noisy Rational Expectations Models,' Review of Economic Studies 82(3): 868-921",
      "doi_or_url": "...",
      "relevance_one_sentence": "...",
      "source_pass": "memory"
    }
  ],
  "search_grounded_candidates": [...],
  "verified_candidates": [...],
  "unverifiable_candidates": [...],
  "already_cited_drops": [...],
  "no_passage_anchor_drops": [...],
  "findings": [
    {
      "id": "le_001",
      "candidate": {
        "citation": "...",
        "doi_or_url": "...",
        "scholar_cited_by": 1234
      },
      "passage_anchor": {
        "quote": "verbatim from paper.md",
        "location": "section / page",
        "anchor_type": "lit_review | novelty_claim | method_choice | empirical_setting"
      },
      "engagement_rationale": "one-paragraph: what the candidate did, where it overlaps with the paper, why the author should engage.",
      "scores": {
        "miss_likelihood": 0,
        "engagement_obligation": 0,
        "specificity": 0
      },
      "engagement_score": 0
    }
  ]
}
```

## Downstream propagation

After this ticket completes, the orchestrator:

1. Writes `literature_engagement.json` to `_artifacts/json/`.
2. Adds the file to the input list of every Phase 2 discovery ticket prompt (so discovery agents can see the comparator literature when reasoning about novelty / scope / quantitative anchoring).
3. After Phase 3 merge, the `findings[]` from this template emit as **panel rows** into a new top-level array `literature_engagement_findings[]` in `panel.json` — separate from `findings[]` (which are auditor-style negative claims) and from `dropped_findings[]`.
4. The renderer (Phase 6) gets a new section in `panel.md`, `referee_memo.md`, and `referee_letter_draft.md` titled "Suggested literature engagement" — bullet list of candidate references with the passage anchor and one-sentence rationale per row.

This is the "different reviewer role" codex flagged. Auditor findings live in `findings[]`; librarian findings live in `literature_engagement_findings[]`. They render in separate sections of the panel.

## Calibration

This track has a **different evidentiary contract** from the main pipeline — the same pattern as `scope_framing_calibration.md` (v8.2). It does NOT enter `_calibration/post_pass1_panel_rows.json`. Instead, a lightweight inline check applies:

- The candidate must be verifiable (Step 4 must have produced a DOI or stable URL).
- The candidate must not be in the paper's bibliography (Step 5 dedup).
- The passage anchor must substring-match `paper.md` (verbatim-quote rule, same as the main pipeline).
- The engagement_obligation score must be ≥ 2 (if every candidate is "0 = optional related work" or "1 = mention-worthy," the track is producing noise and should drop the row).

Rows that fail any check drop to `_calibration/dropped_literature_engagement.json` with the failure reason.

## Quality bar

- 5–10 surviving candidates is normal on a paper that engages a deep literature. Fewer means the search vocabulary was too narrow; more means the dedup against bibliography was incomplete.
- Prefer specificity over coverage. A single sharply-positioned candidate ("this paper's mechanism is structurally identical to Gârleanu-Pedersen-Poteshman 2009's dealer model") beats 5 vaguely-related references.
- **No "you should also cite the textbook" comments.** If the engagement obligation is "this is in the standard syllabus," drop the candidate — Anthony's "no BS pointless extensions" rule applies here too.

## Failure modes

- **Gemini search hits captcha or 429** — retry once after 60 sec; fallback to /chrome scholar UI for the verification step.
- **Verification step finds the candidate doesn't exist** — drop, log as `hallucinated_citation`. This is the equivalent of the verbatim-quote validator failing in the main pipeline.
- **All candidates are already cited** — the paper is well-positioned; output an empty `findings[]` with a note. This is a clean outcome, not a failure.
- **No passage anchor can be identified for any candidate** — the search vocabulary was too generic. Re-run Step 1 with more specific method/mechanism nouns.

## Cost

Typical run: 2 gemini calls (Pass A + Pass B) ~ $0.10, plus 3–10 /chrome lookups for verification (~ 2–5 minutes wall clock). Total: ~5–10 minutes added to a 2-hour pipeline. Negligible.
