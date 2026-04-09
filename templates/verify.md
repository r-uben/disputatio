# Web verification prompt (Gemini-specific)

Gemini is the designated external-evidence specialist because its CLI has web search. This prompt is used after the merge-and-rank step, before the debate phase, to verify issues that flagged `needs_web_verification: true`.

## Inputs

- Ranked issues: `workspace/<paper-slug>/ranked_issues.json`
- Paper map: `workspace/<paper-slug>/paper_map.json`

## Your task

For each ranked issue where `needs_web_verification: true`, use web search to answer the `verification_query`. Your goal is either to **confirm** the issue (the external evidence supports the finding) or to **resolve** it (the external evidence refutes the finding).

## Procedure

For each issue to verify:

1. **Read the verification query.** What specifically needs to be checked?
2. **Formulate a precise search.** Don't do vague searches. Target:
   - Exact citations: "Chodorow-Reich Nenov Simsek 2021 stock wealth MPC"
   - Specific data series: "TIPS 30-year forward rate 2021"
   - Institutional facts: "Federal Reserve FG forward guidance COVID-19 timeline"
   - Appendix content: try to find the paper's Internet Appendix PDF directly
3. **Fetch the evidence.** Use web search to get the relevant pages.
4. **Verify.** Compare what the external source actually says with what the paper claims.
5. **Write the result.**

## Output

Append a `web_verification` field to each verified issue in `ranked_issues.json`:

```json
{
  ...existing issue fields...,
  "web_verification": {
    "status": "confirmed | refuted | inconclusive",
    "summary": "one-paragraph summary of what the external evidence shows",
    "sources": [
      {
        "url": "https://...",
        "title": "...",
        "relevant_excerpt": "..."
      }
    ],
    "impact_on_issue": "does this strengthen, weaken, or leave unchanged the original finding?"
  }
}
```

If verification **refutes** the issue, update the issue's `rank_score` by subtracting 3 — it should drop in the priority list. If the issue's new score is too low for the budget cut, remove it from the debate phase (record in `triage.json` as "resolved by verification").

If verification **confirms** the issue, update the issue's `rank_score` by adding 2 — it rises in priority.

If **inconclusive**, leave the score unchanged but flag it for a cautious prosecution in round 1.

## Types of verification by method

Different discovery methods produce different kinds of verification needs:

- **M2 (contradictions)**: rarely needs web verification — contradictions are internal
- **M3 (transformations)**: the analogy test (T8) and consequence test (T6) may need literature search
- **M4 (counterexamples)**: high verification need — counterexamples often depend on known results in the literature; citations must be checked
- **M5 (self-measured critique)**: verification is needed when the paper's commitment comes from an external source (cited work); the cited work must be fetched to check whether the paper correctly represents its own commitment
- **M6 (causal disentangling)**: highest verification need — confounders, alternative explanations, and external validity all require external data and related literature

## Budget

Web verification is rate-limited. Default budget: up to 5 searches per issue. Stop early if the answer is clear. If an issue requires more than 5 searches, mark it inconclusive and let the debate handle it.
