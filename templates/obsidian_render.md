# Obsidian rendering template

Between waves, Claude reads the raw JSON outputs in `_artifacts/json/` and writes human-readable markdown into the curated folders (`20_orientation/`, `30_discovery/`, etc.). This template specifies how to transform each artifact type.

The principle: **the JSON is the machine format, the markdown is the human format**. Both are preserved. The markdown is never the source of truth — if the two disagree, the JSON wins.

## Common frontmatter

Every rendered markdown file gets a minimal frontmatter block:

```yaml
---
tags: [disputatio, <phase>, <paper-slug>]
paper: "<paper title>"
agent: claude | codex | gemini
ticket: <ticket_id>
phase: orientation | discovery | ranking | debate
date: <YYYY-MM-DD>
---
```

The `ticket` field is a link back to the originating ticket in `_artifacts/tickets.json` so provenance is always recoverable.

## Type: Paper map (orientation)

**Source**: `_artifacts/json/orient_<agent>.json`  
**Destination**: `20_orientation/<agent>.md`

```markdown
---
tags: [disputatio, orientation, <paper-slug>]
paper: "<paper title>"
agent: <agent>
ticket: orient_<agent>
phase: orientation
date: <YYYY-MM-DD>
---

# <Agent>'s Paper Map

> Reasoning trace: [[_artifacts/sessions/orient_<agent>.log]]  
> Raw output: [[_artifacts/json/orient_<agent>.json]]

## Paper metadata

- **Title**: <title>
- **Authors**: <authors>
- **Venue**: <venue>

## Abstract

<full abstract text>

## Main claims

1. **C1**: <claim> — *<type>* (<location>)
2. **C2**: ...
...

## Equations

| ID | Label | Definition | LaTeX |
|----|-------|------------|-------|
| eq_1 | (1) | <definition> | `<latex>` |
...

## Propositions

### Proposition 1: <label>

**Statement**: <one-sentence statement>

**Conditions**:
- <condition 1>
- <condition 2>

## Assumptions

| ID | Assumption | Location |
|----|------------|----------|
| A1 | <assumption> | <location> |
...

## Parameters

| Symbol | Description | Value | Source |
|--------|-------------|-------|--------|
| θ | Poisson hazard rate | 0.5 | Chodorow-Reich et al. (2021) |
...

## Datasets

| Name | Source | Period | Used for |
|------|--------|--------|----------|
| TIPS forwards | Federal Reserve | 2019-2023 | Measuring p^MB(t) |
...

## Load-bearing citations

| Citation | Used for | Claim attributed |
|----------|----------|------------------|
| Chodorow-Reich, Nenov, Simsek (2021) | MPC calibration | 3-cent stock MPC |
...

## Appendix references

| Reference | Used for | Main-text location |
|-----------|----------|--------------------|
| IA Proposition IA.1 | Fixed-point characterization | Section I.C.2 |
...

## Section anchors

- **Intro**: <paragraph range + one-sentence summary>
- **Model**: ...
- **Main result**: ...
- **Empirics**: ...
- **Conclusion**: ...

## OCR-corrupted sections

| Location | Description |
|----------|-------------|
| Page 2 | Entire page replaced by unrelated ARDL/ECM discussion |
...
```

## Type: Orientation overview

**Source**: all three `_artifacts/json/orient_*.json`  
**Destination**: `20_orientation/00_orientation.md`

```markdown
---
tags: [disputatio, orientation, <paper-slug>]
paper: "<paper title>"
phase: orientation
date: <YYYY-MM-DD>
---

# Orientation Overview

> Three agents produced independent paper maps. No merging — each agent's reading is preserved as-is. This preserves the independence that makes cross-agent support a strong ranking signal in the discovery phase.

## Summary table

| Agent | Claims | Equations | Propositions | Assumptions | Parameters | OCR Sections Flagged |
|-------|--------|-----------|--------------|-------------|------------|----------------------|
| [[claude]] | N | N | N | N | N | N |
| [[codex]] | N | N | N | N | N | N |
| [[gemini]] | N | N | N | N | N | N |

## What all three agree on

<one paragraph listing the core claims, equations, and propositions that all three paper maps identified>

## Notable divergences

<one paragraph describing where the agents' readings differ, if anywhere. Example: "Codex identified 6 propositions vs. Claude's 4; Claude treated Lemma 2 and Corollary 1 as inline rather than numbered results">

## OCR corruption consensus

<one paragraph describing which sections all three agents agree are corrupted, and which only one agent flagged>
```

## Type: Discovery issue (one method, one agent)

**Source**: `_artifacts/json/discover_<agent>_<method>.json`  
**Destination**: `30_discovery/<method>/<agent>.md`

```markdown
---
tags: [disputatio, discovery, <method>, <paper-slug>]
paper: "<paper title>"
agent: <agent>
method: <method>
ticket: discover_<agent>_<method>
phase: discovery
date: <YYYY-MM-DD>
---

# <Agent> — <Method Name>

> Method: see [[templates/methods/<method>]]  
> Reasoning trace: [[_artifacts/sessions/discover_<agent>_<method>.log]]  
> Raw output: [[_artifacts/json/discover_<agent>_<method>.json]]

## Findings — N issues

### Issue 1: <one-line summary>

**Claim**: <the falsifiable claim>

**Quote** (from paper, <location>):
> <exact quote>

**Evidence**: <why the claim is correct>

**Falsifier**: <what would withdraw the claim>

**Impact**: material | local | unclear  
**Confidence**: high | medium | low  
**Needs web verification**: yes/no — <query if yes>

### Issue 2: <one-line summary>

...
```

## Type: Discovery method summary (across agents)

**Source**: all three `_artifacts/json/discover_*_<method>.json` for one method  
**Destination**: `30_discovery/<method>/00_<method>.md`

```markdown
---
tags: [disputatio, discovery, <method>, <paper-slug>]
paper: "<paper title>"
method: <method>
phase: discovery
date: <YYYY-MM-DD>
---

# <Method Name> — Cross-Agent Summary

> [[templates/methods/<method>|What is this method?]]

## Findings by agent

- [[claude]]: N issues
- [[codex]]: N issues
- [[gemini]]: N issues

**Total raw**: N issues  
**Unique concerns** (after rough dedup): M

## Shared findings

Issues that multiple agents independently identified via this method:

1. **<short title>** — claude, codex, gemini: same concern about <X>
2. **<short title>** — claude, codex: identified <Y>
...

## Agent-unique findings

Issues only one agent flagged:

- **Claude only**: <list>
- **Codex only**: <list>
- **Gemini only**: <list>
```

## Type: Issue register entry

**Source**: merged issues after `merge_and_rank`  
**Destination**: single entry inside `40_ranking/issue_register.md`

```markdown
### <issue_id>: <short title>

- **Rank score**: N/15 (centrality C, cross-agent A×2, specificity S, severity V)
- **Status**: pending | in debate | converged | dropped
- **Impact**: material | local | none
- **Sources**: [[30_discovery/m5_immanent/claude|claude-m5]], [[30_discovery/m3_transformations/codex|codex-m3]]
- **Needs web verification**: yes/no
- **Debate folder**: [[50_debates/01_<slug>/00_issue]]

**Claim**: <the merged claim>

**Quote** (<location>):
> <exact quote>

**Evidence**: <why the claim is correct>

**Falsifier**: <what would withdraw the claim>
```

## Type: Debate round (prosecute/defend/synthesize)

**Source**: `_artifacts/json/debate_<issue_id>_r<N>_<role>.json`  
**Destination**: `50_debates/<rank>_<slug>/r<N>_<role>.md`

```markdown
---
tags: [disputatio, debate, <paper-slug>]
paper: "<paper title>"
agent: <agent>
role: prosecute | defend | synthesize
issue: <issue_id>
round: N
ticket: debate_<issue_id>_r<N>_<role>
phase: debate
date: <YYYY-MM-DD>
---

# Round <N> — <Role> (<Agent>)

> [[../00_issue|← Back to issue]]  
> Prompt: [[_artifacts/prompts/debate_<issue_id>_r<N>_<role>]]  
> Reasoning trace: [[_artifacts/sessions/debate_<issue_id>_r<N>_<role>.log]]  
> Raw output: [[_artifacts/json/debate_<issue_id>_r<N>_<role>.json]]

## Prompt (summary)

<one-paragraph summary of what the agent was asked to do>

## Output

<the structured content: objections for prosecute, sed_contra + respondeo + replies for defend, refined claim + reasoning for synthesize — rendered as markdown>

## Metadata

- **Agent**: <agent>
- **Model**: <model>
- **Tokens used**: ~<N>
- **Wall clock**: <seconds>s
- **Ticket**: `<ticket_id>`
```

## Type: Debate summary

**Source**: last synthesis + the full round history  
**Destination**: `50_debates/<rank>_<slug>/99_summary.md`

```markdown
---
tags: [disputatio, debate, summary, <paper-slug>]
paper: "<paper title>"
issue: <issue_id>
phase: debate
date: <YYYY-MM-DD>
---

# <Issue Title> — Debate Summary

> [[00_issue|← Original issue]]  
> [[../../40_ranking/issue_register#<issue_id>|Register entry]]

## Status

**Final verdict**: material | local | none | split | escalate  
**Rounds run**: N  
**Converged at**: round N

## Refined claim

<the final refined version of the claim after all rounds>

## Rounds

### Round 1 — Claude prosecutes, Codex defends, Gemini synthesizes

- **Prosecution**: [[r1_prosecute]] — <1-sentence summary>
- **Defense**: [[r1_defend]] — <1-sentence summary>
- **Synthesis**: [[r1_synthesize]] — <1-sentence summary>

### Round 2 — ...

## Accepted facts

<bullet list of what both sides agreed on>

## Refuted components

<bullet list of what was disproved>

## Open disputes

<bullet list of what remained unresolved, if anything>

## Constructive suggestion

<how the author could fix this>
```

## Type: Final report

**Source**: all synthesis outputs + issue register  
**Destination**: `60_final_report/referee_report.md`

```markdown
---
tags: [disputatio, final-report, <paper-slug>]
paper: "<paper title>"
authors: "<authors>"
venue: "<journal>"
phase: complete
date: <YYYY-MM-DD>
---

# Referee Report: <short title>

## Summary

<one-paragraph plain-prose summary of the review's main conclusions. This is what a human reader sees first.>

## Material issues (N)

1. **<title>** — <one-sentence summary of refined claim>
   - Constructive fix: <suggestion>
   - Full debate: [[../50_debates/<slug>/99_summary|debate summary]]

2. ...

## Local issues (N)

1. **<title>** — <one-sentence summary>
2. ...

## Dropped issues (N)

- **<title>** — Reason: <why dropped>

## Overall verdict

<one-paragraph evaluation — the kind of thing a referee writes at the bottom of a real report. Honest, not politer than the debate actually was.>

## Methodology

- Orchestration: ticket DAG, <N> tickets total
- Discovery: 3 agents × 5 methods = 15 sweeps
- Issues: <raw> raw → <after triage> after triage → <debated> debated
- Debate rounds: <total>
- Web verifications: <N>
- Wall clock: <total time>
- Models: Claude <model>, Codex <model>, Gemini <model>
```

## Type: Top-level review index

**Destination**: `00_review.md` (top of paper folder)

```markdown
---
tags: [disputatio, review, <paper-slug>]
paper: "<paper title>"
authors: "<authors>"
venue: "<journal>"
phase: <current phase>
date: <YYYY-MM-DD>
---

# Review of: <short title>

**Status**: <current phase and what is happening>

## Quick links

- [[10_paper/paper|Source paper]]
- [[10_paper/metadata|Metadata]]
- [[20_orientation/00_orientation|Orientation]] — 3 paper maps
- [[30_discovery/00_discovery|Discovery]] — 15 method sweeps
- [[40_ranking/00_ranking|Ranking]] and [[40_ranking/issue_register|Issue register]]
- [[50_debates/00_debates|Debates]]
- [[60_final_report/referee_report|Final report]]
- [[_artifacts/manifest|Artifacts manifest]]

## Progress

| Phase | Status | Time |
|-------|--------|------|
| Orientation | done | 4 min |
| Discovery | running | — |
| Ranking | pending | — |
| Verification | pending | — |
| Debate | pending | — |
| Final report | pending | — |

## Headline findings (preview)

<one or two sentences about the most important findings so far, updated as phases complete>
```

## Rendering rules

1. **Never drop data.** Every field in the JSON must appear somewhere in the markdown. If the markdown abstracts a field (e.g., summarizes instead of listing), the raw field must still be accessible via the `[[_artifacts/json/...]]` link.

2. **Always include provenance links.** Every rendered file points back to: the originating ticket, the session log, and the raw JSON output. This makes replay and audit trivial.

3. **Use Obsidian wiki links** `[[...]]` not markdown links `[...](...)`. Obsidian's graph, backlinks, and unlinked mentions all work off wiki links.

4. **Keep frontmatter minimal and flat** — no nested objects, no long arrays, no dynamic values. Obsidian Dataview queries work best on flat frontmatter.

5. **Use tables where the JSON has a list of objects**, prose where the JSON has a single rich field.

6. **Links between debate rounds use relative paths**: `[[r1_prosecute]]` within the same issue folder, `[[../02_other_issue/00_issue]]` across issues, `[[../../40_ranking/issue_register]]` up and across.
