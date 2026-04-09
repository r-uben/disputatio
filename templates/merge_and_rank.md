# Merge and rank prompt

After 3 agents have each run 5 discovery methods, you have up to 15 sets of candidate issues. This prompt describes how to merge them into a single ranked list.

## Inputs

All issues from all agents and methods:

```
workspace/<paper-slug>/discovery/
├── claude/{m2,m3,m4,m5,m6}/issue_*.json
├── codex/{m2,m3,m4,m5,m6}/issue_*.json
└── gemini/{m2,m3,m4,m5,m6}/issue_*.json
```

## Procedure

### Step 1: Triage

Discard candidate issues that are:
- **OCR artifacts**: the "error" is in a passage that is clearly corrupted (injected text from unrelated documents, broken LaTeX, hallucinated content)
- **Presentation-only complaints**: the paper "should explain X better" with no concrete error
- **Singleton findings with low confidence**: found by only one agent, only one method, with `confidence: low` and `impact: local` or `unclear`
- **Style/grammar complaints**: the paper's writing could be clearer but nothing is wrong

Record what was triaged and why in `workspace/<paper-slug>/triage.json`.

### Step 2: Deduplication

Cluster remaining issues by whether they point to the same underlying concern. Two issues are the same if they:
- Cite the same passage or equation
- Make claims that imply each other
- Would be resolved by the same fix

For each cluster, produce a single merged issue that takes the strongest version of the claim and aggregates the evidence from all members.

### Step 3: Ranking

Score each merged issue on four dimensions. Each dimension is scored 0-3.

**Centrality** (how close to the paper's main contribution):
- 0 = footnote or robustness check
- 1 = supporting argument
- 2 = main empirical or theoretical result
- 3 = the paper's central claim

**Cross-agent support** (which agents found it):
- 0 = found by one agent only
- 1 = found by two agents
- 2 = found by all three agents
- 3 = found by all three agents via different methods

Note: **cross-agent support is more valuable than cross-method support within a single agent.** Five methods on one model are correlated; agreement across architectures is stronger evidence.

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

Output a single file `workspace/<paper-slug>/ranked_issues.json` containing all merged issues sorted by rank score descending. Format:

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
      "verification_query": "Does the paper's citation of Chodorow-Reich (2021) support the claimed MPC of 0.03?"
    }
  ]
}
```

### Step 5: Budget cut

The full list is preserved in `ranked_issues.json`, but only the **top N** issues enter the debate phase, where N is set by the skill configuration (default: top 8). Issues below the cutoff are recorded as "appendix concerns" in the final report but not debated.
