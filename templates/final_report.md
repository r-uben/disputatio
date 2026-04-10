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

For each issue that entered debate, read its final synthesis and classify it:

- **Material** — the refined claim affects the paper's central results or main interpretation. `impact: material` in the last synthesis AND the debate did not reduce it to `none`.
- **Local** — the refined claim affects a specific passage, calibration, or robustness check but not the core contribution. `impact: local` in the last synthesis.
- **Dropped** — the debate resolved the issue. `impact: none` in the last synthesis, or the issue was killed by early-kill / stalled-debate rules.

For issues that were below the budget cut (never debated), classify them as **Appendix** — preserved for completeness but not examined.

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
      "claim": "the refined claim after debate",
      "original_claim": "the claim before debate",
      "rank_score": 13,
      "rounds": 2,
      "final_status": "converged | escalate",
      "accepted_facts": ["..."],
      "refuted_components": ["..."],
      "open_disputes": ["..."],
      "constructive_suggestion": "...",
      "web_verified": true,
      "web_summary": "one-line summary of external evidence"
    }
  ],
  "local_issues": [
    {
      "id": "merged_005",
      "claim": "the refined claim after debate",
      "rank_score": 9,
      "rounds": 1,
      "constructive_suggestion": "..."
    }
  ],
  "dropped_issues": [
    {
      "id": "merged_008",
      "claim": "original claim",
      "reason": "why it was dropped (e.g., 'resolved in round 1 defense')"
    }
  ],
  "appendix_issues": [
    {
      "id": "merged_012",
      "claim": "original claim",
      "rank_score": 6,
      "reason": "below budget cut"
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

Write `60_final_report/referee_report.md` using the rendering spec from `templates/obsidian_render.md` (Type: Final report). The markdown is a projection of `final.json` — if the two disagree, the JSON wins.

### Step 4: Update the top-level index

Update `00_review.md`:
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
2. `60_final_report/referee_report.md`

Plus an update to `00_review.md`.
