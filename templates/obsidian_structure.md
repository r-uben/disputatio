# Obsidian folder structure

The Obsidian folder **is the workspace**. There is no separate scratch area. Every artifact from a review — tickets, prompts, raw JSON, session logs, and curated markdown — lives inside a single paper folder under the Obsidian vault.

## Location

```
~/Library/Mobile Documents/iCloud~md~obsidian/Documents/notes/work/referee-reports/<paper-slug>/
```

Peer to live reviews:

- `_archive/` — frozen pre-v1 test runs (old 20–60 numbering). Left in place for history; no code should read from it.

## Folder tree

```
<paper-slug>/
├── review.md                             # entry point: metadata, status, TOC, summary
│
├── _paper/                                # source paper (input, not a phase)
│   ├── paper.md
│   ├── paper.pdf                          # optional
│   └── metadata.md                        # title, authors, venue, date, model versions, run id
│
├── 0_orientation/                         # phase 00 — lectio (the reading)
│   ├── 00_orientation.md                  # overview + cross-agent comparison
│   ├── claude.md
│   ├── codex.md
│   └── gemini.md
│
├── 1_discovery/                           # phase 01 — quaestio (the inquiry)
│   ├── 00_discovery.md                    # summary across methods and agents
│   ├── m2_contradictions/
│   │   ├── 00_m2.md
│   │   ├── claude.md
│   │   ├── codex.md
│   │   └── gemini.md
│   ├── m3_transformations/
│   ├── m4_counterexamples/
│   ├── m5_immanent/
│   └── m6_disentangling/
│
├── 2_ranking/                             # phase 02 — ordinatio (the ordering)
│   ├── 00_ranking.md
│   ├── issue_register.md                  # canonical list of merged issues, stable IDs
│   ├── triage.md                          # filtered-out candidates + reasons
│   └── web_verification.md                # Gemini web-verification results (external evidence only)
│
├── 3_debates/                             # phase 03 — disputatio (the debate)
│   ├── 00_debates.md                      # map of debated issues with status
│   ├── 01_<issue_slug>/
│   │   ├── 00_issue.md
│   │   ├── r1_prosecute.md
│   │   ├── r1_defend.md
│   │   ├── r1_synthesize.md
│   │   ├── r2_prosecute.md
│   │   ├── r2_defend.md
│   │   ├── r2_synthesize.md
│   │   └── 99_summary.md
│   └── ...
│
├── 4_report/                              # phase 04 — the deliverable
│   └── referee_report.md
│
├── _artifacts/                            # machine outputs (non-markdown where possible)
│   ├── manifest.md                        # human-readable index of everything in _artifacts
│   ├── tickets.json                       # DAG state (source of truth for orchestration)
│   ├── prompts/                           # exact prompts sent to agents (.md)
│   ├── sessions/                          # raw agent reasoning traces (.log, never wiped)
│   └── json/                              # raw structured outputs (.json)
│
└── _evaluation/                           # meta: quality assessment of the review itself
    ├── 00_evaluation.md                   # scorecard + aggregate metrics
    ├── annotations.md                     # per-finding annotation worksheet (keyed by finding_id)
    └── comparison.md                      # optional: side-by-side vs coarse / reference / prior version
```

## Principles

### Five phases, zero-indexed (0–4)

Phase numbering matches the public description:

| Folder | Phase | Latin | Role |
|---|---|---|---|
| `0_orientation/` | 00 | lectio | the reading |
| `1_discovery/` | 01 | quaestio | the inquiry |
| `2_ranking/` | 02 | ordinatio | the ordering |
| `3_debates/` | 03 | disputatio | the debate |
| `4_report/` | 04 | — | the deliverable |

Numbers are tight (no gaps of 10). If a phase is ever inserted, the folders are renamed. That cost is negligible compared to the readability win.

### Underscore-prefixed folders are not pipeline phases

- `_paper/` — input to the pipeline
- `_artifacts/` — machine state (tickets, prompts, JSON, session logs)
- `_evaluation/` — meta assessment of the output

These sort after the numbered phases and are visually marked as "not part of the generative flow."

### `review.md` is the entry point

A single flat filename at the root. No ASCII-sort tricks, no folder-note plugin dependency. Every reference in templates and code uses this exact filename.

### Within each folder, `00_<name>.md` sorts first

The folder's index uses `00_<name>.md`. Debate rounds use `r1_`, `r2_`, `r3_` prefixes; the final per-issue summary uses `99_summary.md` so it sorts last.

### Discovery is organized by method, not by agent

"What contradictions were found?" is the useful question at ranking time, not "what did Codex find across all methods?" Methods are the first-level split; agents are subfiles within each method.

### Canonical issue register with stable IDs

`2_ranking/issue_register.md` is the single source of truth for all merged issues. Every reference from debates, the final report, web verification, and `_evaluation/` links back to the issue's stable `finding_id` (e.g. `merged_001`). Once assigned, IDs never change.

### `_artifacts/` stays non-markdown for raw data

Session logs are `.log`, raw structured outputs are `.json`. This keeps them preserved but keeps them out of Obsidian's search index, backlink graph, and graph view. The only `.md` files in `_artifacts/` are `manifest.md` and `prompts/*.md`.

### Three independent paper maps, never merged

Each agent produces an independent paper map. The three maps are NOT merged. Independence is what makes cross-agent support a strong ranking signal.

### `_evaluation/` is human judgment, distinct from web verification

`2_ranking/web_verification.md` holds Gemini's fact-checking of claims against external sources. `_evaluation/` holds human (or blind-LLM) per-finding annotation of the review itself: quote verification and calibration. The two must never be conflated.

Each annotation in `_evaluation/annotations.md` is keyed by `finding_id` (never by text). Schema per row:

```yaml
finding_id: merged_001
quote_verified: yes | partial | no           # does the quote appear at the cited location
calibration:    supported | overclaimed | unsupported
annotator:      <name>
annotated_at:   YYYY-MM-DD
notes:          <free text>
```

See `templates/evaluation.md` for the operational procedure.

### Frontmatter minimal and flat

Every `.md` file navigated as a Dataview target (review root, debates, final report, evaluation) has frontmatter like:

```yaml
---
tags: [disputatio, referee-report, <paper-slug>]
paper: "<paper title>"
venue: "<journal>"
phase: lectio | quaestio | ordinatio | disputatio | report | complete | evaluation
date: YYYY-MM-DD
---
```

Nothing nested, nothing dynamic.

### Stable slugs

The paper slug (folder name) is chosen at start and never changes. Debate issue slugs are chosen at merge time and never change. Renames break links and tooling.

## Agent-ctl and Obsidian

`agent-ctl run-dag` automatically preserves session logs into `_artifacts/sessions/<ticket_id>.log` when a ticket completes. The destination is derived from the `tickets.json` parent directory.

`agent-ctl cleanup` only wipes volatile scratch in `/tmp/agent-ctl/`. Nothing important lives there by the time cleanup runs.

## Life cycle

1. **Init**: Claude creates the paper folder, writes `review.md` (phase: lectio), `_paper/paper.md`, `_artifacts/tickets.json` with wave 1 tickets, and `_artifacts/prompts/*.md`.
2. **Wave 1 runs**: `agent-ctl run-dag` executes orientation tickets. JSON lands in `_artifacts/json/`. Session logs archived.
3. **Render**: Claude reads the JSON and writes curated markdown to `0_orientation/{claude,codex,gemini}.md`. `00_orientation.md` summary is written. `review.md` advances to phase: quaestio.
4. **Wave 2**: Claude emits discovery tickets, `run-dag` executes, Claude renders to `1_discovery/m<N>/{claude,codex,gemini}.md`.
5. Continue through `2_ranking/`, `3_debates/`, `4_report/`.
6. **Evaluation (optional, post-hoc)**: annotator fills in `_evaluation/annotations.md` against the frozen `issue_register.md`. Aggregates computed in `00_evaluation.md`.

At any point, open `review.md` to see the current phase.
