# Merge and rank prompt (v6)

After Phase 2 completes, you have up to nine discovery JSON files — three tracks (`holistic_candidates`, `broad_critic`, `narrow_evidence`) × three families (anthropic, openai, google). This prompt describes how to merge them into atomic panel-row candidates.

## Inputs

Nine discovery JSON files, each containing `{"track": "...", "agent": "<family>", "issues": [...]}`:

```
_artifacts/json/discover_claude_holistic_candidates.json
_artifacts/json/discover_claude_broad_critic.json
_artifacts/json/discover_claude_narrow_evidence.json
_artifacts/json/discover_codex_holistic_candidates.json
_artifacts/json/discover_codex_broad_critic.json
_artifacts/json/discover_codex_narrow_evidence.json
_artifacts/json/discover_gemini_holistic_candidates.json
_artifacts/json/discover_gemini_broad_critic.json
_artifacts/json/discover_gemini_narrow_evidence.json
```

Plus one optional file from Wave 2.5:

```
_artifacts/json/baseline_review.json   # coarse-style single-shot coverage sentinel (per templates/baseline.md)
```

Every discovery candidate has already passed the evidence compiler (`templates/evidence_compile.md`) at write time — its `quote` is guaranteed to substring-match `_paper/paper.md`, its `category` is guaranteed to be in the canonical vocabulary, and its evidence array is guaranteed non-empty.

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
        merged_so_far.append(baseline_to_merged_issue(b, source="baseline"))
```

Matching uses the rules in `templates/baseline.md`. Baseline items covered by the merged set are *discarded* (we already have the concern). Baseline items *not* covered are appended to the merged set as new issues with `source: baseline` and a conservative default rank_score of 8; Phase 4's four-way escalation gate then decides independently whether any of them enters debate. In v6 the baseline is a **coverage sentinel, not a router** — if the baseline catches something the holistic pass should have caught, that is a signal to strengthen the holistic pass, not an automatic debate admission.

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

### Step 3b: Debate-eligibility flag (v6 — replaces v5 status routing)

In v5 every surviving merged issue got a `status ∈ {settled, debate}` that determined whether it entered Phase 4. v6 **removes that status field** and replaces it with the four-way escalation gate in `SKILL.md` Phase 4, which is computed separately over the full panel-row set (including baseline-unique findings from Step 2c).

Merge output therefore does NOT assign settled/debate. Instead it produces a `debate_hint` field on each merged issue summarising whether it is an escalation *candidate* by the three gate conditions merge can evaluate at this stage:

```json
"debate_hint": {
  "cross_family_disagreement": "strong | moderate | none",  // Derived from sources: conflicting/missing flags
  "evidence_conflict_in_paper": "yes | no | unknown",        // Does the paper's own text cut both ways?
  "severity_sensitive": true | false                          // Would severity change if the claim survives scrutiny?
}
```

The fourth gate condition (finding would otherwise be user-visible) is evaluated in Phase 4 after calibration and so is not in merge's purview.

Phase 4 reads `debate_hint` plus fresh calibration verdicts and decides which findings escalate. Debate selection is **not** merge's decision; merge only surfaces the evidence for the decision.

**Why this changed.** v5's two-tier routing (settled → report unchallenged, debate → dialectic) was semantically clean but created exactly the schema-split problem v6 is trying to eliminate. Two routing theories (status-based vs four-way-gate) in adjacent files produced silent wrong execution risks. v6 makes the four-way gate the single authority for debate routing and treats merge's output as neutral.

If the paper produces zero findings that trigger the four-way gate in Phase 4, debate is skipped entirely. That is the correct outcome on consensus-heavy papers.

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
      "debate_hint": {
        "cross_family_disagreement": "strong | moderate | none",
        "evidence_conflict_in_paper": "yes | no | unknown",
        "severity_sensitive": true
      },
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

### Step 5: Debate selection (v6 — delegated to Phase 4's four-way gate)

Merge does NOT pre-select the debate cohort. The full merged set flows into Phase 4, which applies the four-way escalation gate (cross-family disagreement real, evidence on both sides, severity would change on verdict, finding would be user-visible) to each finding independently.

`rank_score` remains the canonical importance ordering for the final panel table, but it does not gate debate eligibility in v6. An issue can have a very high rank_score and still skip debate if the four-way gate is not satisfied (e.g. all three families agreed, evidence is one-sided, and the panel would show the same result either way).

In practice: most findings ship through calibration straight to the panel. The 0–5 findings that clear the four-way gate get the adversarial round. This is a deliberate compute reallocation away from v5's "debate the top-N by rank" and toward "debate only what is actually contested and stakes-worthy."

### Step 6: Emit v6 panel rows

After ranking, status assignment, and baseline-diff augmentation, transform each surviving merged issue into a **v6 panel row** and write to `_artifacts/json/panel_rows_candidates.json`. This is the canonical structured output going into verify → debate → calibrate → render in v6. The legacy `ranked_issues.json` is preserved as the audit-trail artifact.

For each merged issue that survived triage and the atomicity validator, emit a panel row matching the v6 schema. **Single source of truth for the row shape: `templates/schemas/panel_row.md`** — if this file and the schema disagree on a field name or type, the schema wins. Field mapping:

```
merged issue                                    →  panel row
-------------------------------------------------------------
id (merged_NNN)                                 →  finding_id (F001, F002, ...) — zero-padded, re-indexed
claim                                           →  concern (verbatim)
category (already set by evidence compiler at   →  category (preserved unchanged — NO post-hoc
 write time from canonical vocabulary)             re-categorisation; "other" rate > 10% logs warning
                                                    per SKILL.md Explicit rules)
scores.severity → 'material'|'local'|'nit'      →  severity (map: 3→material, 2→material, 1→local, 0→nit)
(see note below)                                →  confidence.band: "not_calibrated"  (v6 placeholder)
(populated downstream)                          →  priority.author / priority.referee
quote + quote_location + evidence[]             →  evidence[] (preserve every entry with its
                                                    support_type; evidence compiler has already
                                                    validated every quote)
sources + family list per ticket                →  architecture_support.<family>.{supports, methods, notes}
debate_hint (Step 3b output)                    →  debate_hint (preserved unchanged; Phase 4 gate reads it)
(populated by Phase 4 debate, else not_run)     →  debate.{triggered, reason, verdict, what_survived, history}
(populated by Phase 5 calibration pass 1 and 2) →  calibration_pass1 / calibration_pass2
(populated by Phase 6 renderer)                 →  suggested_action.author.fix / referee.how_to_use
(compute from source ticket IDs + prompts)      →  audit.source_candidate_ids, prompt_trace_ids,
                                                    status: "survived" (panel rows from here) /
                                                    "dropped" (added to dropped_findings[] instead)
```

**Confidence band policy (v6).** The panel row's `confidence.band` is initialised to the string `"not_calibrated"` at merge time. This is deliberate: `rank_score` is a relative ordering within one run, not an epistemic confidence measure, so labelling it `high | medium | low` at this stage would mislead the reader. A future release that ships observed calibration data on a benchmark corpus can replace `"not_calibrated"` with a real `band`; until then, the placeholder is more honest than fake precision. The render step in `templates/render_panel.md` displays `"not_calibrated"` verbatim in the panel table.

The transform is a mechanical map — Claude (opus) executes it inline, no additional model call needed. The output `panel_rows_candidates.json` contains two top-level arrays:

```json
{
  "survived": [ /* panel row per issue that survived triage + atomicity validator + baseline-diff injection */ ],
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
