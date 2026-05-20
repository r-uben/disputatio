# Literature engagement track (v3 — archetype-driven)

Surface specialised adjacent works the paper does not cite but probably should engage with. Closes disputatio's "librarian gap" — the failure mode where a closed-book auditor produces correct atomic findings but misses the citation-positioning comments a domain expert referee writes naturally.

This track is **upstream** of Phase 2 discovery. The output feeds discovery context and emits dedicated panel rows.

## Why v3

Two prior architectures failed under blind empirical conditions on the Han-Hu-Zhang paper vs the actual AER Ref #2's 8 named references:

- **v1 (gemini-flash memory + /chrome verify)**: 1/8 hits. LLM memory recall naturally favors canonical syllabus papers (Kyle, Ross, Stein), not the load-bearing comparators a domain referee actually names.
- **v2 (OpenAlex citation-graph traversal)**: 0/8 hits. None of Ref #2's named references cite any of Zhang's bibliography anchors — they live in *unnamed sub-literatures* the author engages but doesn't loudly cite. Local graph operations cannot find what's missing.

Reading Ref #2's exact phrasing for each named reference surfaced the architectural insight: **referee picks fit five specific reasoning archetypes**, not topic adjacency:

| # | Archetype | Ref #2 example | What the question phrases |
|---|---|---|---|
| 1 | Substitution-of-assumption | "in the spirit of Breon-Drish (2015), can the authors characterize which results extend to a general exponential-family payoff distribution?" | "Paper has X assumption — what relaxations of X have been studied in [setting]?" |
| 2 | Same instrument, different domain | "Martin (2017) and Martin (2013) characterize variance trading and pricing in a different equilibrium setting — equity premium and SVIX rather than commodity risk sharing" | "Paper uses instrument X in domain D — where has X been analyzed in domain D'?" |
| 3 | Alternative mechanism, same conclusion | "Brennan and Cao (1996) and CYZ (2022) both deliver welfare rationales for derivatives but driven by asymmetric information rather than market incompleteness" | "Paper gets conclusion Y via mechanism M — what other mechanisms deliver Y?" |
| 4 | Mechanism-isomorphic predecessor | "GPP (2009) is structurally close to the maker-taker mechanism here: their dealers are long volatility and end-users short" | "Paper's construction K — predecessors structurally isomorphic to K?" |
| 5 | General theorem behind specific result | "Elul (1999) establishes a general welfare-improvement rationale for adding contracts in single-good economies" | "Paper proves specific result Z — what general theorem does Z specialize?" |

Topic adjacency reaches none of these reliably; archetype-driven question generation reaches most of them.

## When it fires

One ticket per paper. Emitted in **Wave 1.75**, between Wave 1.5 (holistic) and Wave 2 (discovery). Claude-typed inline (the orchestrator runs the three passes sequentially). `/chrome` MCP is a hard prerequisite for Pass A3.

## Inputs

- Paper spine, main_claims, attack_surface_index (Wave 1.5 output)
- `citations_load_bearing[]` from any orientation map
- `entities.cited_papers[]` (full bibliography for dedup)
- `_paper/paper.md` (for passage-anchor in Step 5)

## Confidentiality

This is the only disputatio phase that deliberately sends content to external services. Three rules:

1. **Pass A1 prompts** consume paper text (existing data-flow contract; same as the rest of the pipeline's LLM calls).
2. **Pass A2 prompts** consume paper context (themes + already-cited works); no verbatim unpublished text. Output is candidate citations from training memory.
3. **Pass A3 Scholar queries** use the *archetype-question's keyword stem* (e.g., `"variance swap" general equilibrium pricing SVIX`), not verbatim paper sentences. Specific-paper-title fragments from candidate references are also allowed (they're public). Verbatim unpublished sentences from the paper are forbidden.

`--no-lit-engagement` disables the entire wave. `--lit-engagement strict|relaxed` controls Pass A3's query latitude (default strict).

## Procedure

### Step 1 — Pass A1: Archetype Question Generator

Default model: **`gemini-3.1-pro-preview`** (strong long-context reasoning; tested at 35s on Zhang). Fallback: claude-sonnet inline.

Prompt the model with paper spine + main_claims + attack_surface_index + load-bearing already-cited works, then ask it to **generate 10–15 archetype-questions across the 5 types**.

Each question must:
- Anchor on a specific paper assumption / conclusion / construction (paper_anchor field).
- Phrase the question precisely enough that a domain agent can name 1–3 papers as the canonical answer.
- NOT name specific papers as candidate answers — that's Pass A2's job.
- NOT bundle two distinct archetypes into one question (e.g., "what relaxations to CARA OR Gaussian have been studied?" should be two questions).

Output JSON schema:

```json
{
  "archetype_questions": [
    {
      "id": "Q01",
      "archetype": "substitution | same_instrument_different_domain | alternative_mechanism | isomorphic_predecessor | general_theorem",
      "paper_anchor": "1 sentence on what in the paper triggers this question",
      "question_text": "the precise question, phrased so a domain agent can name 1-3 specific papers"
    }
  ]
}
```

Save to `_artifacts/json/literature_engagement_archetypes.json`.

### Step 2 — Pass A2: Reference Finder (codex)

Default model: **`codex gpt-5.4`** at `model_reasoning_effort=medium`. Gemini-flash-lite UNDERSHOT this task in empirical tests (canonical-bias dominated, ignored the suppress-canonical rule); gpt-5.4 has stronger calibrated econ-finance training memory.

Prompt codex with each archetype-question and the constraint that the answer must be a **load-bearing comparator**, not a canonical-syllabus representative. Specifically:

- DO NOT propose foundational papers (Kyle 1985, Stein 1987, Ross 1976, Admati 1985, Hellwig 1980, Grossman-Stiglitz 1980, Black-Scholes-class).
- Prefer specific comparators within the lineage over the most-cited representative.
- "I don't know" is allowed and preferable to canonical filler.
- 1–3 papers per question; 30–50 total candidates expected.

Output JSON schema:

```json
{
  "answers": [
    {
      "question_id": "Q01",
      "papers": [
        {"citation": "Author (YEAR), Title, Venue Vol(Issue): pages",
         "why_load_bearing": "1-2 sentences on the specific mechanism-overlap with this paper"}
      ],
      "confidence": "high | medium | low",
      "notes": "optional — flag if you fell back to canonical"
    }
  ]
}
```

Save to `_artifacts/json/literature_engagement_a2_codex.json`.

### Step 3 — Pass A3: /chrome Scholar fill-in

Hard prerequisite: `/chrome` MCP connected. Fails fast if not.

For each archetype-question:
1. Construct a tight Scholar query string from the question's *keyword stem* (e.g., from "variance swaps in equity general equilibrium with stochastic volatility" → `"variance swap" general equilibrium pricing SVIX`). Avoid verbatim paper sentences.
2. Navigate to `scholar.google.com/scholar?q=<query>` via `mcp__claude-in-chrome__navigate`.
3. Read top results via `mcp__claude-in-chrome__get_page_text`. Capture title, authors, year, venue, cited-by count for the top 5–10 hits.
4. **Iterate when the first attempt is weak**: if the top results are off-domain (signal-processing, unrelated math, etc.), refine the query with more-specific finance vocabulary or named tradition (e.g., "noisy rational expectations + existence + general payoff distribution"). 1–3 attempts per archetype-question typically suffices.
5. For candidates A2 already proposed: spot-check via Scholar to correct metadata noise (gemini/codex sometimes get venue or year wrong).
6. For archetype-questions A2 didn't answer well: Scholar's relevance ranker often surfaces the load-bearing comparator on a well-phrased query.

Empirical findings on Zhang (2026-05-20):

| Archetype | A2 codex | /chrome supplement |
|---|---|---|
| Martin 2017 QJE (variance swaps equity) | ✅ Q03 | confirmed |
| GPP 2009 (maker-taker isomorphic) | ✅ Q05 / Q07 / Q12 ×3 (triangulation) | confirmed |
| Martin 2013 simple variance swap | ❌ | ✅ on `"variance swap" general equilibrium pricing SVIX` |
| Breon-Drish 2015 RES | ❌ | ✅ on `"noisy rational expectations" existence general payoff distribution` |
| Elul 1999 ET | ❌ | ✅ on `welfare improving financial innovation incomplete markets single good` |
| Malamud-Trubowitz 2007 / HMT 2012 | ❌ | ✅ on `Malamud Trubowitz incomplete markets optimal consumption` (author-line query) |
| Brennan-Cao 1996 | ❌ | ✅ on `"information trade" derivative securities rational expectations` |

Save raw query results + selected candidates to `_artifacts/json/literature_engagement_a3_scholar.json`.

### Step 4 — Cross-archetype rerank

Combine A2 + A3 candidates. For each unique paper, compute `archetype_coverage` = number of distinct archetypes that surfaced it. Papers appearing across multiple archetypes are higher-confidence load-bearing comparators (the GPP 2009 triangulation signal: 3 archetypes pointed to the same paper).

Rerank by `(archetype_coverage DESC, cited_by_count DESC, year DESC)`. Top archetype_coverage is the load-bearing signal; cited_by_count and year are tiebreakers.

### Step 5 — Bibliography dedup

Mechanical match against `entities.cited_papers[]` from orientation and the bibliography section parsed from `paper.md`. Drop `already_cited` matches. Keep only `survivors`.

### Step 6 — Passage-anchor selection

For each survivor, identify the paper passage that would owe engagement. Allowed anchor types: `lit_review | novelty_claim | method_choice | empirical_setting`. Output verbatim quote from `paper.md` + location anchor + one-sentence "why this candidate matters here." Drop survivors without passage anchor.

### Step 7 — Ranking

Each surviving candidate scored on three dimensions, 0–3 each:

- **Archetype-coverage signal** — `archetype_coverage` directly (1, 2, or 3+).
- **Engagement obligation** — given the passage anchor, how strongly does the paper owe engagement? (0 = optional related work; 3 = direct competitor mechanism)
- **Specificity** — how concrete is the mechanism-overlap with the target paper? (0 = topic match; 3 = same construction, different framing)

`engagement_score = 2 × archetype_coverage + engagement_obligation + specificity` (max 12, since archetype_coverage caps at 3).

## Output

Write a single JSON file to `_artifacts/json/literature_engagement.json`:

```json
{
  "schema_version": "literature_engagement_v3",
  "archetype_questions": [/* from A1 */],
  "a2_codex_candidates": [/* from A2 */],
  "a3_chrome_candidates": [/* from A3 */],
  "combined_candidates": [/* after dedup */],
  "findings": [
    {
      "id": "le_001",
      "candidate": {
        "citation": "Author (YEAR), Title, Venue Vol(Issue): pages",
        "doi": "10....",
        "cited_by_count": 1234
      },
      "archetype_coverage": 3,
      "archetypes_matched": ["Q05_alternative_mechanism", "Q07_isomorphic_predecessor", "Q12_general_theorem"],
      "mechanism_overlap_evidence": "1-paragraph: where Scholar/A2's notes signal mechanism-overlap with the paper",
      "passage_anchor": {
        "quote": "verbatim from paper.md",
        "location": "section / page",
        "anchor_type": "lit_review | novelty_claim | method_choice | empirical_setting"
      },
      "engagement_rationale": "1 paragraph: what the candidate did, where it overlaps, why the author should engage",
      "scores": {"archetype_coverage": 3, "engagement_obligation": 0, "specificity": 0},
      "engagement_score": 0,
      "source": "a2_codex | a3_chrome | both"
    }
  ]
}
```

## Downstream propagation

After the ticket completes:

1. Writes `literature_engagement.json` to `_artifacts/json/`.
2. Adds the file to Phase 2 discovery ticket prompts (so discovery sees comparator literature when reasoning about novelty / scope / quantitative anchoring).
3. Phase 3 merge emits the `findings[]` as panel rows into a top-level `literature_engagement_findings[]` array in `panel.json`.
4. Phase 6 renderer surfaces them in a dedicated "Suggested literature engagement" section in `panel.md`, the mode-specific memo, and the optional auxiliary output.

## Calibration (different evidentiary contract — same as v1 / v2)

Lightweight inline check (no separate calibrator sub-DAG):

- Candidate paper must be Scholar-verifiable (A3 captured metadata; A2-only candidates without A3 confirmation get re-verified at this step via `/chrome`).
- Bibliography dedup applied.
- Passage anchor substring-matches `paper.md`.
- `archetype_coverage ≥ 1` (always true for surviving candidates) + `engagement_obligation ≥ 2`.

Rows failing any check drop to `_calibration/dropped_literature_engagement.json` with reason.

## Quality bar

- 5–10 surviving findings normal. Below 3 → archetype-question generation was too narrow; expand. Above 12 → reranker should tighten on `archetype_coverage ≥ 2`.
- **Canonical-suppression target**: ≤ 30% of survivors pre-2010 with > 1000 cites.
- **Archetype-triangulation signal**: at least 1 finding with `archetype_coverage ≥ 2` (the GPP 2009 pattern). If zero, A1's question generation was too narrow or A2's load-bearing recall was canonical-biased.

## Failure modes

- **/chrome not connected** — fail fast. No fallback to training-memory-only output (that's v1, which scored 1/8).
- **Codex gpt-5.4 capacity-exhausts on A2** — retry with exponential backoff; if still failing, fall back to gemini-3.1-pro-preview for A2 (lower precision but works).
- **gemini-flash for A2** — DO NOT use. Empirically violates suppress-canonical rule (returns Kyle, Carr-Wu, Radner 1972).
- **A1 produces archetype-questions that bundle two archetypes** — common failure mode. Re-run A1 with explicit "split bundled questions" reminder.
- **All A3 Scholar queries return off-domain noise** — query refinement needed. Each archetype-question typically needs 1–3 query iterations to converge.
- **Zero triangulation** (no paper surfaces across multiple archetypes) — A1's questions are too narrow. Re-run A1 with broader paper-anchor coverage.

## Cost

Typical run:
- 1 gemini-3.1-pro-preview Pass A1 call (~$0.02, ~ 35 sec)
- 1 codex gpt-5.4 Pass A2 call (~$0.10, ~ 5 min)
- 15–30 /chrome Scholar navigations (~$0, dominated by ~ 5–10 min Scholar latency)
- 1–2 LLM rerank/anchor calls (~$0.05)

Total: ~ 10–15 min wall clock, ~$0.20 inference cost, $0 external-service cost.

## Empirical evidence (Zhang, 2026-05-20)

Strict-blind recall (all phases including A3 isolated from any read of the referee report) settles at **7 / 9** of Ref #2's named-and-not-already-cited references. The +2 informed-supplement candidates (Malamud 2008 and Martin et al 2013 "Simple Variance Swaps") were recovered only via orchestrator-picked Scholar queries that knew the target list; they are preserved in a separate `informed_supplement[]` audit bucket and excluded from the headline metric.

Full progression of architectural attempts:

| Architecture | Score | Notes |
|---|---|---|
| v1 default gemini-flash memory | 1/8 | Canonical bias |
| v1 Ref-#2-leaked taxonomy | 6/8 | Contaminated — referee-leaked vocabulary |
| v2 OpenAlex citation traversal | 0/8 | Structural reachability gap |
| v1 sharper "suppress canonical" | 0/8 | Topic-adjacent ≠ archetype |
| A1 archetype + A2 codex | 2/8 | Real architectural win (Martin 2017, GPP 2009 × 3) |
| A1 + A2 + A3 /chrome supplement (v3, 2026-05-19 first run) | 5/8 strict / 8/8 with borderline | "With borderline" included informed query supplements |
| **A1 clean + A2 codex + A3 blind subagent (2026-05-20 strict-blind re-run)** | **7 / 9 strict-blind** | A3 phase-isolated from orchestrator. A3-informed-supplement (+2: Malamud 2008, Martin 2013) carved out into `informed_supplement[]`. Strict-blind is the headline. |

## Blind discipline (mandatory)

The 2026-05-20 strict-blind re-run surfaced a failure mode the v3 spec did not enumerate: **orchestrator-context leakage.** If the same session that reads the post-hoc referee report also drives any generation phase (A1, A2, or A3), the recall metric becomes partly cherry-picked. The fix is phase isolation, not better prompting.

Mandatory blind discipline:

1. **A1, A2, and A3 must each run in a session that has never read the referee report or any post-hoc comparison artifact.** Subagent dispatch is the simplest way to enforce this.
2. **A3 worker must not have read access to** `_referee_aer/`, `_calibration/`, `4_panel/`, `_archive/<date>_contaminated_*/`, or any prior `literature_engagement_*.json` other than the clean `literature_engagement_archetypes.json` (so the blind A3 cannot "fill A2's gaps" — that's exactly the contamination vector).
3. **A3 queries must derive from the archetype-question's keyword stem alone.** No specific paper title fragments. No author last names unless they appear in the archetype-question's own `paper_anchor` field (paper-cited works are admissible because the paper exposes them).
4. **Post-hoc comparison runs in `_evaluation/`**, not in the live pipeline. The comparison artifact (`_evaluation/ref_comparison.json` for runs with a sealed referee report) records the strict-blind recall decomposition and the informed-supplement delta separately.
5. **Headline metrics are strict-blind.** Any "X/N" claim ships with explicit strict-blind framing. Informed-supplement numbers ship as a separate carve-out, never as the headline.

See `docs/log/2026-05-20_strict-blind-discipline.md` for the full contamination diagnosis and fix.

## What v3 still doesn't do

- **Replicate a specific human referee's specific 8 picks exactly.** One expert's specific picks is a low-recall target by construction. v3 reaches 5–8/8 because the archetype framework captures *how Ref #2 thinks*, not because the system reads his mind.
- **Survive n=1.** Multi-paper validation pending. The architecture *should* generalize because the 5 archetypes are domain-general; the empirical test on 2–3 more papers with sealed reports will confirm.
- **Replace expert domain review.** A top-tier referee's calibrated knowledge can produce sharper picks than v3 in cases where archetype framing alone doesn't catch them.
