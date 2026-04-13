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

### Step 2b: Atomicity check (one issue, one location)

Each merged issue must be **atomic**: one claim, one primary quote, one primary location. This is required for the per-finding evaluation protocol (`templates/evaluation.md`) — findings that bundle N sub-issues under "various locations" cannot be annotated triple-by-triple and must be rejected here.

Rules:
- **One `quote`, one `quote_location`.** The `quote` field must be a verbatim passage from the paper. "Multiple locations" or "Various" is not allowed.
- **If a cluster contains N related-but-distinct errors** (e.g. "15 notation typos across the appendix"), split it into N separate merged issues, each with its own triple. Ranking can then correctly assign low centrality/severity to each one; they won't dominate the top-N cutoff.
- **Exception — true aggregate findings**: if the *aggregate pattern itself* is the finding (e.g. "the appendix lacks proofreading rigor" as an editorial judgment), produce one merged issue with:
  - `aggregated: true`
  - `sub_findings: [{quote, quote_location, evidence}, ...]` — one entry per sub-item
  - The top-level `quote` is the most representative sub-item, not a placeholder
- **Never** emit a merged issue whose `quote` is a summary ("Multiple locations in Appendix A and Online Appendix") or whose `quote_location` says "Various".

This atomicity rule keeps evaluation tractable and prevents a single bundled finding from evading per-triple scrutiny.

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

The full list is preserved in `ranked_issues.json`, but only the **top N** issues enter the debate phase, where N is set by the skill configuration (default: top 8). Issues below the cutoff are recorded as "appendix concerns" in the final report but not debated.
