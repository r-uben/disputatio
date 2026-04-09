# Obsidian report template

Claude updates a live Obsidian note at every phase transition. The note is **human-facing** — it is not a machine artifact. Its job is to let you read the review as it unfolds, and to serve as the final deliverable (a proper referee report you could send to an author or save for your records).

The note lives at:

```
~/Library/Mobile Documents/iCloud~md~obsidian/Documents/notes/work/referee-reports/<paper-slug>.md
```

## Initial structure (written at `/disputatio` invocation)

```markdown
---
tags: [referee-report, disputatio]
paper: "<full paper title>"
authors: "<authors>"
venue: "<journal>"
status: orientation
date: <YYYY-MM-DD>
top_n: 8
max_rounds: 3
---

# Referee Report: <short title>

> **Status**: Orientation in progress. All three agents reading the paper in parallel.

## Summary
*Pending — will be written after the full review completes.*

## Orientation
*Pending.*

## Discovery
*Pending.*

## Ranking
*Pending.*

## Web Verification
*Pending.*

## Debate
*Pending.*

## Final Assessment
*Pending.*

## Method Notes
- Orchestration: ticket DAG, %N% tickets total
- Runtime: TBD
- Agents: Claude (<model>), Codex (<model>), Gemini (<model>)
```

The `status` field in the frontmatter takes values: `orientation | discovery | merge | verify | debate | complete`.

## Update rules

Claude updates the note at each phase transition. **Always update the frontmatter `status` field** to reflect the current phase, and **replace** the relevant section (do not append stale content).

### After orientation (Phase 0 complete)

Replace the `## Orientation` section with:

```markdown
## Orientation

Three agents produced independent paper maps (used as caches for discovery).

| Agent | Claims | Equations | Propositions | Assumptions | Parameters | OCR Corrupted Sections |
|-------|--------|-----------|--------------|-------------|------------|------------------------|
| Claude | N | N | N | N | N | N |
| Codex | N | N | N | N | N | N |
| Gemini | N | N | N | N | N | N |

**Shared understanding**: <one sentence about what the three maps agree on>

**Divergences**: <one sentence about where they differ, if anywhere>
```

Update status frontmatter to `discovery`.

### After discovery (Phase 1 complete)

Replace the `## Discovery` section with:

```markdown
## Discovery

Each agent ran all five generative methods against its own paper map. Total discovery sweeps: 15 (3 agents × 5 methods).

### Claude — N raw issues
- **M2 (contradictions)**: n issues
- **M3 (transformations)**: n issues
- **M4 (counterexamples)**: n issues
- **M5 (self-measured)**: n issues
- **M6 (causal disentangling)**: n issues

### Codex — N raw issues
(same structure)

### Gemini — N raw issues
(same structure)

**Total raw issues**: N (pre-triage)
```

Update status frontmatter to `merge`.

### After merge + rank (Phase 2 partial)

Replace the `## Ranking` section with a table of all ranked issues, with the top N highlighted:

```markdown
## Ranking

After triage, deduplication, and scoring. Scoring: `centrality + 2×cross_agent_support + evidence_specificity + severity` (max 15).

### Top N (will be debated)

| # | Issue | Score | Agents | Methods |
|---|-------|-------|--------|---------|
| 1 | <one-line claim> | 13 | claude+codex | M5, M3 |
| 2 | ... | ... | ... | ... |

### Appendix concerns (below cutoff, not debated)

| Issue | Score | Reason |
|-------|-------|--------|
| <one-line claim> | 7 | below top-N cutoff |
```

Update status frontmatter to `verify`.

### After web verification (Phase 2 complete)

Replace the `## Web Verification` section:

```markdown
## Web Verification

Gemini verified N issues that flagged `needs_web_verification`. Results:

| Issue | Status | Evidence | Δ Score |
|-------|--------|----------|---------|
| issue_003 | confirmed | Chodorow-Reich (2021) confirms 3-cent stock MPC | +2 |
| issue_005 | refuted | Internet Appendix resolves the contradiction | -3 → dropped |
| issue_007 | inconclusive | no authoritative source found | 0 |
```

Update status frontmatter to `debate`.

### After each debate round

**Append** to the `## Debate` section (one new sub-section per round per issue). For the first round of an issue, start with the header:

```markdown
### Issue N: <short title>

**Original claim**: <the merged claim from discovery>
**Rank score**: 13 (centrality 3, cross-agent 2, specificity 3, severity 2)

#### Round 1 — Claude prosecutes | Codex defends | Gemini synthesizes

- **Prosecution** (methods: M5, M3)
    - Objection 1: <one sentence>
    - Objection 2: <one sentence>
    - Objection 3: <one sentence>
- **Defense**
    - Sed contra: <one sentence>
    - Reply to obj 1: <concede | answer — one sentence>
    - Reply to obj 2: <...>
    - Reply to obj 3: <...>
- **Synthesis**
    - Accepted facts: <bullet list>
    - Refuted components: <bullet list>
    - Open disputes: <bullet list>
    - **Refined claim**: <the new claim>
    - **Impact**: material | local | none
    - **Status**: continue | converged | split | escalate
```

For subsequent rounds, add a `#### Round 2 — ...` subsection with rotated roles.

### After final report (Phase 4 complete)

Replace the `## Summary` and `## Final Assessment` sections with the actual content:

```markdown
## Summary

A plain-prose paragraph summarizing the review's main conclusions. This is what a human reader will see first. It should be precise and honest — not politer than the debate actually was.

## Final Assessment

### Surviving material issues (N)
1. **<title>** — <refined claim>
   - Constructive fix: <suggestion>
2. ...

### Surviving local issues (N)
1. **<title>** — <one-line summary>
2. ...

### Dropped issues (N)
- **<title>** — Reason: <why dropped>

### Overall verdict

A one-paragraph evaluation the reviewer would write at the bottom of a referee report. Something of the form: "The paper's qualitative contributions are sound, but Section III overclaims on housing and requires tightening around forward guidance. With the revisions suggested above, the paper would be publishable at <venue>."
```

Update status frontmatter to `complete`.

## Method Notes section (always at the bottom)

This section is rewritten at the end with the actual runtime stats:

```markdown
## Method Notes

- Tickets total: <N> (of which <X> Claude-typed, <Y> Codex-typed, <Z> Gemini-typed)
- Wall clock: <time>
- Discovery sweeps: 15 (3 agents × 5 methods)
- Issues found (raw): <N>
- Issues after triage + merge: <N>
- Issues debated: <N>
- Total debate rounds: <N>
- Web verifications: <N>
- Failures/retries: <N>
```

## Principles

- **The note is human-facing.** Use prose where prose works, tables where tables work. Do not dump raw JSON into the note.
- **Replace, do not append** — except for the `## Debate` section, which grows as rounds complete.
- **Update the status frontmatter every time you touch the note.** This is what makes the note reflect "where we are" at any moment.
- **The note is NOT the source of truth.** The ticket DAG and the JSON outputs in the workspace are. The note is a human-readable projection.
- **If a phase produces a finding that is surprising or would not be obvious from the JSON files, mention it briefly in the relevant section.** The note is where unusual observations can live.
