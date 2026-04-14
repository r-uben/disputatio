# Panel renderer prompt (v6, Phase 6)

A single long-context model reads `_calibration/final_findings.json` and the full `panel.json` and produces three outputs: the panel rendered as markdown, a mode-specific prose memo, and an optional auxiliary rendering (revision plan for author mode, or referee-letter draft for referee mode). The writer can summarise rows that survived calibration; **it cannot invent findings, change a `calibration.verdict`, or restore a dropped row.**

This is the step that closes the prose-uniformity gap. Fragment assembly (what v5 did) produces stitched-together paragraphs with mixed voices. A single writer reading the entire panel produces consistent tone across all findings.

## Inputs

- Panel JSON: `_calibration/final_findings.json` (or the v6 `panel.json` build at the same path if the renderer runs after panel compilation)
- Paper text: `_paper/paper.md` — for context and for verification that quotes resolve where the panel says they do
- Mode: `author` or `referee` (from the engine section of the panel)

## Outputs

Three files. All under `4_panel/`.

### 1. `4_panel/panel.md` — panel as a table

One-line-per-finding markdown table. Primary UI. Columns:

| Severity | Confidence | Priority (mode-specific) | Category | Concern | Evidence | Verdict history | Suggested action |

Render `priority` using the mode-specific vocabulary (`fix_before_submit | watch_in_review | can_ignore` for author, `endorse | verify_before_endorsing | skip` for referee). Render `confidence.band` as `high | medium | low`. Render the quote in the `Evidence` column truncated to ~140 characters with a wikilink to the full finding page.

Sort: by priority (highest first), then severity (`material` → `local` → `nit`), then confidence (high → low).

Follow the table with a **Dropped findings** section that lists every `dropped_findings[]` entry with its drop reason. This is mandatory — the whole point of calibration is that the system shows what it dropped and why, instead of hiding it.

### 2. `4_panel/author_memo.md` OR `4_panel/referee_memo.md`

One prose memo, 800–1500 words, written by the renderer model end-to-end in a consistent voice. Structure:

```
---
tags: [disputatio, panel, <paper-slug>, <mode>]
mode: author | referee
date: YYYY-MM-DD
---

# Author memo OR Referee memo — <paper title>

## Headline

One paragraph, 3-5 sentences. What the panel concluded overall.
Author mode: "the panel surfaced N concerns that warrant attention before submission; K of them are high-priority fixes and should be addressed before the paper goes out."
Referee mode: "the panel compiled N findings for your consideration; K are high-priority concerns the report should endorse and N-K are candidates worth verifying before endorsing."

## High-priority findings (fix_before_submit / endorse)

One paragraph per finding in this bucket, ordered by severity then confidence. Each paragraph:
- States the concern in one sentence using the paper's own terminology.
- Quotes the paper verbatim where relevant (bounded quote).
- Explains what is at stake (why the panel rates it high priority).
- Names the suggested action.

Keep each paragraph self-contained. A reader skimming only this section should see the top concerns with no ambiguity.

## Medium-priority findings (watch_in_review / verify_before_endorsing)

Shorter paragraphs, 2-4 sentences each. Same structure as above but more compressed.

## Low-priority findings (can_ignore / skip)

A single list with one line per finding. No prose paragraphs — just name + location + one-sentence explanation.

## Dropped findings (calibration-transparent)

A single paragraph acknowledging the count of findings dropped by defense during debate and by calibration. Name the single most consequential drop (by rank, not by severity) and its reason, so the reader understands the system's restraint. Then a one-line table listing each drop with its reason.

## Method notes

Two sentences on the pipeline version, modes available, and where to find the canonical panel JSON.
```

### 3. `4_panel/revision_plan.md` (author mode) OR `4_panel/referee_letter_draft.md` (referee mode)

Optional; produced when `--auxiliary-render` is on (default).

**Revision plan** (author mode) — section-by-section table mapping each high-and-medium priority finding to a concrete sentence-level edit:

| Finding | Paper location | Current wording (verbatim) | Proposed revision | Action type |

Action type is one of: `sentence_rewrite`, `paragraph_restructure`, `add_citation`, `add_robustness_check`, `reframe_scope`, `add_caveat`, `correct_typo`.

**Referee letter draft** (referee mode) — a first-draft referee letter the human referee will edit into their own voice. Structure:

```
Editor:

Summary of contribution: [one paragraph from the panel's holistic_pass.paper_spine]

Main concerns:
1. [one paragraph per high-priority finding, written as a referee comment — not as a finding row]
2. ...

Additional comments:
- [bullet per medium-priority finding]
- ...

Minor issues:
- [one-line per low-priority finding]

Recommendation: [omitted — the renderer does not recommend accept/revise/reject; the human referee makes that call]
```

The draft must NOT recommend acceptance or rejection. The renderer does not have the context to make that call; only the human referee does.

## Writing rules

- **Preserve verbatim quotes exactly.** A quote from the panel that reads `"Property A ... facilitates analysis, it is not essential."` must render with the same punctuation and ellipsis in every output.
- **Preserve the paper's own qualifiers.** If a quote contains "as long as the budget is small", do not strip the qualifier when summarising.
- **Use the paper's terminology.** Don't introduce synonyms ("principal component" → "eigenvector") unless the panel finding explicitly makes that substitution part of its claim.
- **No new concerns.** Every sentence in every output must trace to a panel row. The renderer does not have discovery authority.
- **No severity inflation.** If the panel says `local`, the memo says local. Do not promote to material for rhetorical effect.
- **Calibration-transparent.** Dropped findings always appear in the panel table and in the memo's dedicated section. The system shows its work.
- **Mode-appropriate voice.** Author memo addresses the author directly ("your paper's framing..."). Referee memo addresses the editor or the referee's own notes ("the paper's framing claims..."), in the referee's voice.

## Writer model

Default: **gemini-3.1-pro-preview** — strong at long-form prose, handles the full panel context comfortably.

Fallback: **claude-opus** when the panel has >30 findings (context pressure) or when gemini is rate-limited.

One call. No fragment stitching. This is a deliberate architectural choice — the writer reads the whole panel as one object so the voice is uniform across all renderings.

## Cost

Typical run: ~15-25K token prompt (panel + paper context + rubric), ~3-6K token output per file, 3 files. One model call renders all three files in one pass when feasible; otherwise a separate call per file keeping context cached. Budget: ~$0.50–$1.50 per run.

## Failure modes

- **Quote drift in output**: if the writer paraphrases a quote, the orchestrator re-verifies post-render that every `>` block in memo/letter output substring-matches the paper. Any mismatch triggers one regeneration attempt with an explicit "do not paraphrase quotes" correction. Second failure → ship with a warning in the `method notes` section.
- **Dropped findings hidden**: if the renderer omits the Dropped findings section, reject and regenerate with the explicit instruction.
- **Severity inflation**: if the memo promotes a `local` finding to material rhetoric, reject and regenerate.

All three failures are mechanically detectable and the orchestrator enforces them before the panel is marked complete.
