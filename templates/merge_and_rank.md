# Merge and rank prompt

After 3 agents have each run 5 discovery methods, you have up to 15 sets of candidate issues. This prompt describes how to merge them into a single ranked list.

## Inputs

All 15 discovery JSON files (3 agents × 5 methods), each containing `{"issues": [...]}`:

```
_artifacts/json/discover_claude_m2.json
_artifacts/json/discover_claude_m3.json
...
_artifacts/json/discover_gemini_m6.json
```

## Procedure

### Step 1: Triage

Discard candidate issues that are:
- **OCR artifacts**: the "error" is in a passage that is clearly corrupted (injected text from unrelated documents, broken LaTeX, hallucinated content)
- **Presentation-only complaints**: the paper "should explain X better" with no concrete error
- **Singleton findings with low confidence**: found by only one agent, only one method, with `confidence: low` and `impact: local` or `unclear`
- **Style/grammar complaints**: the paper's writing could be clearer but nothing is wrong

Record what was triaged and why in `_artifacts/json/triage.json`.

### Step 2: Deduplication

Cluster remaining issues by whether they point to the same underlying concern. Two issues are the same if they:
- Cite the same passage or equation
- Make claims that imply each other
- Would be resolved by the same fix

For each cluster, produce a single merged issue that takes the strongest version of the claim and aggregates the evidence from all members.

### Step 2b: Atomicity check (one issue, one location) — v5 hardened

Each merged issue must be **atomic**: one claim, one primary quote, one primary location. This is required for the per-finding evaluation protocol (`templates/evaluation.md`) — findings that bundle N sub-issues under "various locations" cannot be annotated triple-by-triple and must be rejected here.

Atomicity is a hard gate. The 2026-04-13 v3 run and the 2026-04-14 v4 run both saw merge_rank over-cluster: distinct concerns landed in the same `merged_NNN` cluster because they touched the same section, then rode each other into the report. v4 example: claude_m2 independently flagged both "Prop 3's certainty-equivalence is LQG relabelled" AND "Section 5 title 'incomplete information' contradicts footnote 23's 'complete information' admission." Merge bundled them into one `merged_012` because both cited Section 5; the Section-5 framing finding then disappeared when `merged_012` got `defense_wins` on the LQG-relabelling half. That is a **routing failure, not a discovery failure** — discovery had both findings, merge lost one.

### Rules (enforced, not aspirational)

**Verbatim quote rule.** Every merged issue's `quote` field MUST appear as an exact substring of `_paper/paper.md`. No paraphrasing, no one-word edits, no truncation that changes meaning, no appending "…" for omitted middle text. Substrings spanning line breaks are fine if the paper's source wraps the same way. *If no agent surfaced a verbatim quote, the finding is rejected — there is nothing to annotate.*

The orchestrator MUST run a post-merge validator (trivial: `quote in open("_paper/paper.md").read()` after whitespace normalisation) and fail the merge ticket back to the agent for any merged issue whose quote does not substring-match. An "OCR cleanup" exception is allowed only for character-level differences (ligatures, em-dashes, superscript vs LaTeX form); any difference that drops or adds a word is a rewrite and must be caught.

**One-cluster-one-concern rule.** Two source findings belong in the same cluster only if:
- They cite the same passage **and** make implications that force the same fix, or
- They are the same claim restated (one paraphrases the other).

Two findings that cite different sentences or propositions, or that would be fixed by different paper edits, go to different clusters. *"Touches the same section"* or *"both are about Section 5"* is NOT a valid clustering criterion. A cluster that contains N distinct fixes is N clusters.

Concrete split triggers during merging — if ANY of these holds, the cluster MUST be split:
1. Two candidate issues cite non-overlapping quotes.
2. Two candidate issues propose different minimal edits to the paper.
3. Two candidate issues could be `defense_wins` and `prosecution_wins` *independently* in debate (i.e. their truth values are independent).
4. The proposed merged `claim` uses the word "and" to connect two propositions that do not imply each other (e.g. "X contradicts Y **and** also the paper overstates Z" — these are two claims).

**True-aggregate exception.** If the *aggregate pattern itself* is the finding (e.g. "the appendix lacks proofreading rigor — here are 5 representative typos"), produce one merged issue with:
  - `aggregated: true`
  - `sub_findings: [{quote, quote_location, evidence}, ...]` — **one entry per sub-item, each with its own verbatim quote**
  - The top-level `quote` is the most representative sub-item, not a placeholder
  - **Every sub-finding's quote must pass the verbatim validator too** — no bundling unverifiable sub-claims inside an aggregate wrapper (the v4 `merged_019` pattern: one real typo plus seven unsubstantiated ones under one cluster). The validator rejects the aggregate if any `sub_findings[i].quote` does not substring-match the paper.

**Summary quotes are banned.** A merged issue whose `quote` is `"Multiple locations…"`, `"Various appendix passages…"`, `"See Appendix A and OA3.1…"`, or any other meta-description is rejected. If the finding really is about a pattern, use the `aggregated: true` structure above and cite sub-findings individually.

### Post-merge validator (orchestrator runs this)

After the merge ticket writes `ranked_issues.json`, the orchestrator runs a mechanical check BEFORE emitting Wave 3 (verify) tickets:

```python
paper = open("_paper/paper.md").read()
def norm(s): return " ".join(s.split())          # collapse whitespace
issues = json.load(open("_artifacts/json/ranked_issues.json"))["ranked_issues"]
for it in issues:
    if norm(it["quote"]) not in norm(paper):
        reject(it["id"], "quote not substring of paper.md")
    if it.get("aggregated"):
        for sf in it.get("sub_findings", []):
            if norm(sf["quote"]) not in norm(paper):
                reject(it["id"], f"sub_finding quote not substring")
    claim_words = it["claim"].lower()
    if " and " in claim_words and any(sep in claim_words for sep in [
        "contradicts", "overstates", "as well as", "plus", "additionally"
    ]):
        flag(it["id"], "claim may bundle two independent propositions — check Rule 4")
```

Rejections force the merge ticket back to `pending` with a failure_reason listing which issues to fix. The merge agent re-runs with the list and either splits the cluster, finds a real verbatim quote, or drops the finding.

This is a hard gate. In v5 no merged issue enters verify, debate, or report without passing the validator. The atomicity discipline is what prevents distinct concerns from being lost inside over-clustered merged IDs — as happened to the Section-5 framing finding in v4.

### Step 2c: Baseline-diff coverage check (v5)

Alongside discovery (Wave 2), the pipeline runs a coarse-style single-shot opus review (`baseline_review` ticket per `templates/baseline.md`) on the paper text alone. After merging is complete but BEFORE ranking and status assignment, diff the baseline's findings against the merged set:

```python
baseline = json.load(open("_artifacts/json/baseline_review.json"))
baseline_items = baseline["themes"] + baseline["detailed_comments"]

for b in baseline_items:
    match = find_matching_merged_issue(b, merged_so_far)
    # match rules: same quote OR same location anchor + semantic match OR opus yes-match
    if not match:
        # The baseline caught something disputatio missed.
        # Force it in as a debate-status merged issue at moderate rank.
        merged_so_far.append(baseline_to_merged_issue(b, source="baseline", status="debate"))
```

Matching uses the rules in `templates/baseline.md`. Baseline items covered by the merged set are *discarded* (we already have the concern). Baseline items *not* covered are appended to the merged set as new issues with `status: debate` (forced adjudication, since cross-agent support is 0) and a conservative default rank_score of 8. This protects against merge-over-aggregation: even if disputatio's discovery surfaced the concern but merge lost it, the baseline recovers it.

Write `_artifacts/json/baseline_diff.json` recording which baseline items matched which merged issues and which went to forced debate. Include a `coverage_rate` = matched / total_baseline_items. A coverage rate below ~70% means discovery or merge is missing too much and the run should be flagged for investigation.

After this step, proceed to Step 3 (ranking) with the possibly-augmented merged set.

### Step 3: Ranking

Score each merged issue on four dimensions. Each dimension is scored 0-3.

**Centrality** (how close to the paper's main contribution):
- 0 = footnote or robustness check
- 1 = supporting argument
- 2 = main empirical or theoretical result
- 3 = the paper's central claim

**Cross-agent support** — based on model **family**, not transport.

What counts as "an agent" for this score is the *family* field on each ticket that produced a contributing discovery JSON. Open `_artifacts/tickets.json` alongside the discovery outputs: each `discover_*` ticket carries `"family"` (written by the orchestrator at emit time per `templates/agents/families.md`). Group findings by the family of the ticket that produced them.

Counting rules:
- `f` = number of distinct families that flagged the issue.
- `w` = number of within-family repeats (e.g. two opencode sessions against the same Meta Llama count as one family with one repeat).
- Add a `+1` method bonus if at least two different M-numbers (M2..M6) surfaced it across any agents.

**Cross-agent support = min(3, f + 0.5·w + method_bonus)**

For the common 3-agent case (codex → `openai`, gemini → `google`, claude → `anthropic`), `w = 0` always and the score reduces to: 0 = one family, 1 = two, 2 = three, 3 = three plus cross-method. Same shape as the pre-family design.

For larger or mixed configurations (e.g. codex + gemini + opencode/moonshot + opencode/meta), each distinct family increments `f`; two opencode sessions against Llama models from different routing providers still count as one family (`meta`) with a within-family repeat.

Rationale: **cross-architecture agreement is the strongest independence signal.** Two models from the same family trained on overlapping data will repeat each other's errors; two models from different families independently arriving at the same conclusion is evidence the finding is real. Transport choice (which CLI launched the model) does not affect the correlation — only the architecture does.

**Evidence specificity** (how concrete is the finding):
- 0 = general concern with no specific quote
- 1 = quote provided but no derivation
- 2 = specific quote and falsifier
- 3 = specific quote, falsifier, and direct reproduction steps (the finding can be verified independently)

**Severity** (what happens if the finding is correct):
- 0 = cosmetic
- 1 = local correction needed
- 2 = a section must be revised
- 3 = the main result is affected

**Rank score = centrality + 2×cross-agent support + evidence specificity + severity**

Cross-agent support is weighted double because it is the strongest signal of a real issue.

Maximum score: 3 + 6 + 3 + 3 = 15.

`rank_score` is the **single canonical importance score**. It drives the ordering of the final report. It does NOT directly select the debate cohort — see Step 3b for the routing rule.

### Step 3b: Assign status (drop / settled / debate)

After scoring, every surviving merged issue gets a `status` that determines whether it enters debate. **There is no second score.** Status is a pure filter on top of `rank_score`.

```
drop    = removed in Step 1 (triage). Already gone — never reaches the report.
settled = strong corroboration AND strong evidence AND web-verification not inconclusive.
          Specifically: cross_agent_support ≥ 2 (two or more model families flagged it)
                    AND evidence_specificity ≥ 2 (specific quote + falsifier)
                    AND (no web check requested OR web_verification.status ∈ {confirmed, refuted, unchecked}).
debate  = everything else. Either contested across families, weak evidence, or web-verification
          left it inconclusive — i.e. the issue is important enough to keep but not
          settled enough to ship unchallenged.
```

Rationale: dialectic is for **unresolved but important** questions, not for high-disagreement-in-the-abstract and not for anything-that-ranks-high. Three families converging on a well-evidenced issue is exactly what should ship to the report unchallenged. Singletons that survive triage, partial-support findings, and web-inconclusive issues are exactly what needs adversarial pressure.

If a paper produces zero `debate`-status issues, the debate phase is **skipped entirely**. That is the correct outcome — it means findings are either solid or noise, not contested. Forcing debate when nothing is live produces theater (round-1 convergence on every issue, defenders conceding pre-settled points), which the 2026-04-13 v3 run on Galeotti-Golub-Goyal exemplified.

### Step 4: Produce the ranked list

Output a single file `_artifacts/json/ranked_issues.json` containing all merged issues sorted by rank score descending. Format:

```json
{
  "ranked_issues": [
    {
      "id": "merged_001",
      "claim": "...",
      "quote": "...",
      "quote_location": "...",
      "evidence": "...",
      "falsifier": "...",
      "rank_score": 13,
      "scores": {
        "centrality": 3,
        "cross_agent_support": 2,
        "evidence_specificity": 3,
        "severity": 3
      },
      "status": "settled | debate",
      "status_reason": "one-sentence justification for the status assignment",
      "sources": [
        {"agent": "claude", "method": "m5", "issue_id": "m5_issue_002"},
        {"agent": "codex", "method": "m3", "issue_id": "m3_issue_001"}
      ],
      "needs_web_verification": true,
      "verification_query": "Does the paper's citation of Chodorow-Reich (2021) support the claimed MPC of 0.03?",
      "aggregated": false
    }
  ]
}
```

For aggregated findings (rare — only when the *pattern* is itself the finding):

```json
{
  "id": "merged_099",
  "claim": "The appendix shows insufficient proofreading, with 15 distinct notation/transcription errors across OA1–OA3.",
  "quote": "u_i^1(G) = sqrt(n)",
  "quote_location": "Online Appendix, Lemma OA1",
  "evidence": "Representative example; see sub_findings for the full list.",
  "aggregated": true,
  "sub_findings": [
    {"quote": "u_i^1(G) = sqrt(n)", "quote_location": "Lemma OA1", "evidence": "Should be 1/sqrt(n) by the Perron-Frobenius normalization convention."},
    {"quote": "...", "quote_location": "...", "evidence": "..."}
  ]
}
```

### Step 5: Budget cut

The full list is preserved in `ranked_issues.json`. Selection for the debate phase is **status-driven, then rank-ordered**:

1. Filter to `status == "debate"` issues only.
2. Sort by `rank_score` descending.
3. Take the top `--top-n` (default 8) of the filtered list.

If fewer than `--top-n` issues have `status == "debate"`, debate the smaller cohort (or zero, in which case the debate phase is skipped). Do not pad the cohort with `settled` issues to hit the cap.

All `status != "drop"` issues — settled and debated alike — appear in the final report, ordered by `rank_score`. The report distinguishes:
- **Settled** issues: shipped as referee comments without dialectic. Strong cross-architecture corroboration is itself the warrant.
- **Debated** issues: shipped with their debate trace. The verdict (prosecution_wins / defense_wins / split) determines whether they appear as material concerns, surviving local concerns, or are dropped post-debate.
- **Appendix concerns**: low-rank `settled` items the report deprioritises.

### Step 6: Emit v6 panel rows

After ranking, status assignment, and baseline-diff augmentation, transform each surviving merged issue into a **v6 panel row** and write to `_artifacts/json/panel_rows_candidates.json`. This is the canonical structured output going into verify → debate → calibrate → render in v6. The legacy `ranked_issues.json` is preserved as the audit-trail artifact.

For each merged issue with `status != "drop"`, emit a panel row matching the v6 schema (see `docs/v6-upstream-plan.md` and `templates/render_panel.md` for the full spec). Field mapping:

```
merged issue                                    →  panel row
-------------------------------------------------------------
id (merged_NNN)                                 →  finding_id (F001, F002, ...) — zero-padded, re-indexed
claim                                           →  concern (verbatim)
(new)                                           →  category (inferred from method + quote context; one of:
                                                    proof | empirics | identification | framing |
                                                    robustness | interpretation | notation | other)
scores.severity → 'material'|'local'|'nit'      →  severity (map: 3→material, 2→material, 1→local, 0→nit)
scores.cross_agent_support / rank_score context →  confidence.band (high/medium/low derived from
                                                    rank_score tertile within surviving set)
(populated downstream)                          →  priority.author / priority.referee
quote + quote_location + evidence               →  evidence[] (array of one entry with support_type:
                                                    "direct_quote", plus any additional quotes the
                                                    evidence compiler captured)
sources + family list per ticket                →  architecture_support.<family>.{supports, methods, notes}
(populated by Phase 4 debate, else not_run)     →  debate.{triggered, reason, verdict, what_survived, history}
(populated by Phase 5 calibration)              →  calibration.{verdict, quote_verified, annotator_notes,
                                                    narrowing_notes, drop_reason}
(populated by Phase 6 renderer)                 →  suggested_action.author.fix / referee.how_to_use
(compute from source ticket IDs + prompts)      →  audit.source_candidate_ids, prompt_trace_ids,
                                                    status: "survived" (panel rows from here) /
                                                    "dropped" (added to dropped_findings[] instead)
```

The transform is a mechanical map — Claude (opus) executes it inline, no additional model call needed. The output `panel_rows_candidates.json` contains two top-level arrays:

```json
{
  "survived": [ /* panel row per status != "drop" issue */ ],
  "dropped_at_merge": [
    {
      "finding_id": "F_drop_001",
      "true_id": "merged_XXX",
      "drop_source": "triage | atomicity_validator | baseline_diff_no_match",
      "drop_reason": "one-sentence explanation",
      "original_claim": "..."
    }
  ]
}
```

Downstream phases (verify, debate, calibrate, render) operate on the `survived` array. Items in `dropped_at_merge` are preserved in the panel's `dropped_findings[]` at render time so the final output shows restraint transparently.

**Legacy path**: Runs resuming from pre-v6 workspaces may still use `ranked_issues.json` as the primary handoff to verify / debate. The v6 renderer will accept either input and normalise to panel rows at render time; Step 6 just moves the transform earlier so downstream phases can operate on the canonical shape.
