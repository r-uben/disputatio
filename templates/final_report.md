# Final report prompt

You are writing the final referee report. All debates are complete. Your job is to read every synthesis output, classify the surviving issues, and produce two files: a structured JSON and a human-facing markdown report.

## Inputs

- Ranked issues (post-verification): `_artifacts/json/ranked_issues_verified.json`
- All terminal synthesis outputs (injected inline below)
- Paper text: `{{paper_path}}`

## Terminal syntheses

{{syntheses}}

## Your task

### Step 1: Classify every issue

For each issue that entered debate, read its final synthesis `verdict` and classify it:

- **Material** — `verdict: "prosecution_wins"`. The synthesizer ruled the prosecution's case survived. The issue's `surviving_text` is the material concern statement.
- **Local** — `verdict: "split"`. A narrower (surviving) claim survives in the synthesizer's `surviving_text`. Local concern.
- **Dropped** — `verdict: "defense_wins"`. The defense defeated every objection. Issue is recorded but does not appear in the referee letter as a concern.
- **Escalated** — `verdict: "escalate"` after the round budget exhausted. Flagged for human review; appears in the report as an open question.

For issues that had `status: "settled"` at merge time (never debated), classify them as **Settled** — they ship as referee comments without dialectic, ordered by `rank_score`. Not "appendix"; settled issues are first-class content. Use **Appendix** only for low-rank settled items the report deprioritises.

### Step 2: Write the structured output

Write `_artifacts/json/final.json`:

```json
{
  "paper": {
    "title": "...",
    "authors": ["..."],
    "venue": "..."
  },
  "material_issues": [
    {
      "id": "merged_001",
      "surviving_text": "the synthesizer's report-grade paragraph for prosecution_wins",
      "original_claim": "the claim before debate",
      "rank_score": 13,
      "rounds": 2,
      "verdict": "prosecution_wins",
      "attack_outcomes": ["..."],
      "defense_outcomes": ["..."],
      "constructive_suggestion": "the concrete sentence-level fix",
      "web_verified": true,
      "web_summary": "one-line summary of external evidence"
    }
  ],
  "local_issues": [
    {
      "id": "merged_005",
      "surviving_text": "the surviving (narrower) claim from a split verdict",
      "rank_score": 9,
      "rounds": 1,
      "verdict": "split",
      "constructive_suggestion": "..."
    }
  ],
  "dropped_issues": [
    {
      "id": "merged_008",
      "claim": "original claim",
      "verdict": "defense_wins",
      "reason": "what the defender established that defeated the objection"
    }
  ],
  "escalated_issues": [
    {
      "id": "merged_011",
      "claim": "original claim",
      "verdict": "escalate",
      "open_question": "what human review must resolve"
    }
  ],
  "settled_issues": [
    {
      "id": "merged_002",
      "claim": "claim that shipped without debate due to status: settled",
      "rank_score": 11,
      "status_reason": "two families flagged it with verbatim quotes; no inconclusive verification"
    }
  ],
  "appendix_issues": [
    {
      "id": "merged_012",
      "claim": "original claim",
      "rank_score": 4,
      "reason": "low-rank settled item, deprioritised in the report"
    }
  ],
  "overall_assessment": "one paragraph — honest, not polite",
  "methodology_summary": {
    "total_tickets": 0,
    "discovery_sweeps": 15,
    "raw_issues": 0,
    "after_triage": 0,
    "debated": 0,
    "total_debate_rounds": 0,
    "web_verifications": 0,
    "wall_clock_minutes": 0
  }
}
```

### Step 3: Write the human-facing report

Write `4_report/referee_report.md` using the rendering spec from `templates/obsidian_render.md` (Type: Final report). The markdown is a projection of `final.json` — if the two disagree, the JSON wins.

### Step 4: Update the top-level index

Update `review.md`:
- Set frontmatter `phase: complete`
- Update the Status line
- Fill in the "Headline findings" section with the material issues

## Rules

- **Do not invent issues.** Every issue in the report must trace back to a debate synthesis or the ranked issues list. No new findings at this stage.
- **Do not soften findings.** If the debate concluded that an issue is material, report it as material. The report is not a diplomatic exercise.
- **Do not omit dropped issues.** The reader should see what was examined and dismissed, not just what survived.
- **Preserve provenance.** Every issue in the markdown report must link back to its debate folder and its entry in the issue register.

## Output

Two files:
1. `_artifacts/json/final.json`
2. `4_report/referee_report.md`

Plus an update to `review.md`.
