# Web verification prompt (Gemini-specific)

Gemini is the designated external-evidence specialist because its CLI has web search. This prompt runs as Wave 4 in v6 — after merge-and-rank, before calibration Pass 1 — and verifies the panel-row candidates that flagged `needs_web_verification: true` at discovery time.

## Inputs

- Panel-row candidates: `_artifacts/json/panel_rows_candidates.json`
- Paper maps: `_artifacts/json/orient_<agent>.json`

## Your task

For each row in `panel_rows_candidates.json[survived]` whose row-level `needs_web_verification == true`, use web search to answer the row's `verification_query`. Your goal is either to **confirm** the row (the external evidence supports the finding) or to **resolve** it (the external evidence refutes the finding).

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

Write the full panel-row set with verification results to a **new file** `_artifacts/json/panel_rows_candidates_verified.json` (preserving the same `{survived: [...], dropped_at_merge: [...]}` shape as the input). Do not overwrite `panel_rows_candidates.json`. Each verified row gets a `web_verification` field:

```json
{
  ...existing row fields...,
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
    "impact_on_row": "does this strengthen, weaken, or leave unchanged the original finding?"
  }
}
```

All three outcomes write to the row's `web_verification` block (row-level field, distinct from the row's top-level `status` enum). Do not write a bare `status` key at row level.

If verification **refutes** the row, set `web_verification.status: "refuted"` and `web_verification.impact_on_row: "weaken"`. The row is NOT auto-dropped at this stage — calibration Pass 1 reads `web_verification` and treats `refuted` as evidence toward `unsupported`. There is no debate budget cut at verify time in v6 (the v5 budget-cut logic has been removed); whether a refuted row reaches the panel is decided downstream by calibration Pass 1 + the two-route gate, exactly like every other row.

If verification **confirms** the row, set `web_verification.status: "confirmed"` and `web_verification.impact_on_row: "strengthen"`. Calibration Pass 1 will treat this as supporting evidence on the row's `evidence[]` array.

If **inconclusive**, set `web_verification.status: "inconclusive"`, `web_verification.impact_on_row: "unchanged"`, and let calibration handle it on the original evidence.

## Types of verification by method

Different discovery methods produce different kinds of verification needs:

- **M2 (contradictions)**: rarely needs web verification — contradictions are internal
- **M3 (transformations)**: the analogy test (T8) and consequence test (T6) may need literature search
- **M4 (counterexamples)**: high verification need — counterexamples often depend on known results in the literature; citations must be checked
- **M5 (self-measured critique)**: verification is needed when the paper's commitment comes from an external source (cited work); the cited work must be fetched to check whether the paper correctly represents its own commitment
- **M6 (causal disentangling)**: highest verification need — confounders, alternative explanations, and external validity all require external data and related literature

## Budget

Web verification is rate-limited. Budget: up to `{{config.web_budget}}` searches per row. Stop early if the answer is clear. If a row requires more searches than the budget allows, set `web_verification.status: "inconclusive"` and `impact_on_row: "unchanged"`; calibration Pass 1 will then judge the row on its in-paper evidence (and, if the gate fires later, debate may pick it up). Verify does NOT escalate inconclusive rows directly — the v6 path is always verify → calibration Pass 1 → two-route gate.
