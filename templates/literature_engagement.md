# Literature engagement track (v6.x — new)

Surface specialized older or adjacent works the paper does not cite but probably should engage with. Closes disputatio's "librarian gap" — the failure mode where a closed-book auditor produces correct atomic findings but misses the citation-positioning comments a domain expert referee writes naturally.

This track is **upstream** of Phase 2 discovery, not downstream. The output feeds discovery context so that subsequent narrow_evidence / broad_critic findings can engage the comparator literature when judging novelty, scope, and quantitative-anchoring expectations.

## When it fires

One ticket per paper. Emitted in **Wave 1.75**, between Wave 1.5 (holistic) and Wave 2 (discovery).

**Executor: Claude-typed ticket** — the orchestrator runs the ticket inline in a Claude session with the `/chrome` MCP server connected. Claude is the executor because:

- The retrieval step requires `/chrome` MCP tools (Google Scholar navigation, lateral "Cited by N" / "Related articles" traversal). MCP tools are only available in Claude sessions, not in subagents or external CLIs.
- Verification cannot rely on training knowledge — the whole point is to fetch ground-truth metadata (DOI, venue, year) from Scholar.
- Memory-recall candidates from `gemini-3-flash-preview` are treated as one input source among several, not as the retrieval primitive.

**Hard prerequisite:** the Claude session must have the Chrome extension connected (via https://claude.ai/chrome) before the ticket runs. If `mcp__claude-in-chrome__tabs_context_mcp` returns "Browser extension is not connected," the ticket fails fast with a clear error — it does NOT fall back to training knowledge.

`gemini-3-flash-preview` is used inline by Claude (via `agent-ctl`) for the Pass A memory-recall step only. The pro-preview variant is forbidden — it capacity-exhausts on search-grounded prompts; flash is stable. Test result on the Han-Hu-Zhang paper (2026-05-19): pro-preview failed both Pass B attempts with capacity errors; flash returned in 64s with author+year+title accuracy for 6 of 8 Ref #2-named references (venues hallucinated but corrected at verification).

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

### Step 1 — Build the search vocabulary (Claude inline, derived from the paper)

The executor (Claude) reads the paper spine + main_claims + attack_surface_index + load-bearing citations and derives the search vocabulary. There is no hardcoded niche list in this template — the niches a paper engages with are paper-specific and must be derived from its content. The procedure is:

1. **Identify 3–6 sub-literatures the paper engages with.** Look at: the paper's lit-review section, the works it explicitly cites as nearest neighbors, the attack-surface index's `framing` and `theory` entries, the holistic pass's `main_claims`. A sub-literature is a named tradition with recurring authors and a recognizable problem (examples of the *shape*: "existence of equilibrium in noisy rational expectations", "endogenous market completeness via continuous-time diffusion", "variance risk premium asset-pricing tradition", "asymmetric-information welfare for derivatives" — but the actual sub-literatures depend on the paper).
2. **Extract 4–6 method nouns** (specific techniques the paper uses, named precisely).
3. **Extract 4–6 mechanism nouns** (the economic / structural mechanism the paper claims, in generic terms).
4. **Enumerate the load-bearing already-cited works** by author-year, from `citations_load_bearing` in the orientation map.

Write to `search_vocabulary` in the output JSON with sub-objects `sub_literatures[]`, `method_nouns[]`, `mechanism_nouns[]`, `already_cited[]`. The vocabulary is the audit handle for the confidentiality rule — if a sub-literature description quotes verbatim paper text, the rule was violated and the vocabulary must be rewritten before any retrieval call fires.

### Step 2 — Pass A: Model-memory recall (gemini-flash, no search)

Claude dispatches one `gemini-3-flash-preview` call via `agent-ctl` with the search vocabulary inlined. The prompt asks gemini to enumerate 10–15 specialized older or adjacent works for each sub-literature in the vocabulary, drawing from training-corpus memory only — explicitly *not* searching. Format constraint: strict JSON to stdout.

The gemini-flash output is captured as `memory_recall_candidates[]`. Treat these as **leads**, not verified citations — gemini-flash is paper-accurate but venue-noisy (correct paper, wrong volume / issue / year is a common failure mode). Verification (Step 4) is responsible for correcting metadata.

`gemini-3.1-pro-preview` is explicitly forbidden in this step — empirically capacity-exhausts on this prompt class.

### Step 3 — Pass B: Browser-driven retrieval (Claude + /chrome)

Claude drives Google Scholar through the `/chrome` MCP server. For each sub-literature in the vocabulary, Claude executes:

1. **Direct search.** Navigate to `scholar.google.com/scholar?q=<sub_literature_keywords>`, read the first 1–2 result pages, capture the first 8–10 results that match the sub-literature's theme.
2. **Lateral traversal.** For each load-bearing already-cited work that anchors a relevant sub-literature, click "Cited by N" and filter the resulting list for papers that match the paper's themes — these are forward citations of the literature the paper engages, and a frequent source of specialized adjacencies the author missed.
3. **Backward traversal (when valuable).** For top-ranked candidates from Step 1, click the candidate's "Cited by" page and look for older works the candidate cites that the paper does not — backward citation walks find the long-tail predecessors.

For every candidate produced by any traversal: capture `{title, authors, year, venue, volume, issue, pages, doi, scholar_url, cited_by_count}`. No metadata is fabricated; if Scholar doesn't display a venue, the field is null and the candidate is flagged for follow-up rather than completed from memory.

**Hard rule:** Pass B does NOT use training knowledge for any metadata field. Every value must trace to a Scholar result page or to the candidate paper's landing page. Training-knowledge fallbacks are an audit failure and the candidate drops as `unverifiable`.

The Pass B output is captured as `search_grounded_candidates[]`.

### Step 4 — Verification + dedup of Pass A leads

For every entry in `memory_recall_candidates[]` that is not already a duplicate of a `search_grounded_candidates[]` entry:

1. Search Scholar via `/chrome` for the candidate's title + first author + year as gemini reported them.
2. If a single confident match exists: pull canonical metadata (overwrite the gemini-reported fields) and add to `verified_candidates[]`.
3. If no match exists in the first 3 results: drop the candidate, log as `hallucinated_citation` in `unverifiable_candidates[]`.
4. If multiple candidates match (e.g., same authors with two papers near that year — Elul 1995 vs Elul 1999 is a real example), treat each as a separate verified candidate; downstream ranking decides which belongs in the panel.

This step is what catches gemini-flash's venue-hallucination failure mode — paper exists, metadata is wrong, Scholar fixes it.

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

- **`/chrome` MCP not connected** — ticket fails fast at start. No fallback to training knowledge. The user must connect the Chrome extension (https://claude.ai/chrome) and re-run. This is by design — silently degrading to training-knowledge retrieval would produce hallucinated citations the rest of the pipeline trusts as ground truth.
- **`gemini-3-flash-preview` capacity-exhausts on Pass A** — retry once after 60 sec; if still failing, skip Pass A entirely and run Pass B alone (browser-driven retrieval is sufficient on its own; gemini Pass A is an accelerator, not a critical path).
- **Scholar captcha / rate limit** — pause /chrome for 5 min, then continue. If captcha persists, the user must solve it manually in the Chrome window before the ticket can proceed.
- **Verification step finds the candidate doesn't exist** — drop, log as `hallucinated_citation`. gemini-flash's recall is paper-accurate but venue-noisy, so verification will frequently *correct* metadata rather than drop the candidate; an actual drop (paper doesn't exist) is rare.
- **All candidates are already cited** — the paper is well-positioned; output an empty `findings[]` with a note. This is a clean outcome, not a failure.
- **No passage anchor can be identified for any candidate** — the search vocabulary was too generic. Re-run Step 1 with more specific sub-literature descriptions and re-derive vocabulary from the holistic pass's `framing` and `theory` attack surfaces.

## Cost

Typical run: 1 `gemini-3-flash-preview` call for Pass A (~ $0.02, ~ 60 sec wall clock) + 20–40 `/chrome` navigations for Pass B + Step 4 verification (~ 15–25 min wall clock dominated by Scholar page-load latency, no per-call $ cost since /chrome is the user's browser session). Total: ~ 20–30 min added to a 2-hour pipeline.

The wall-clock cost is dominated by Scholar latency, not by inference. Scholar rate-limits aggressive automation; at single-paper volume this is not an issue, but a deployment fanning out across many papers concurrently would need either /chrome session pooling or a graduation to an OpenAlex/Semantic-Scholar API backend (deliberately out of scope for v1 — see issue #33).
