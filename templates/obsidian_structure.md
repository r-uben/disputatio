# Obsidian folder structure

The Obsidian folder **is the workspace**. There is no separate scratch area. Every artifact from a review — tickets, prompts, raw JSON, session logs, and curated markdown — lives inside a single paper folder under your Obsidian vault.

## Location

```
~/Library/Mobile Documents/iCloud~md~obsidian/Documents/notes/work/referee-reports/tests/<paper-slug>/
```

(The `tests/` subfolder will be dropped once the skill is production-ready. See SKILL.md.)

## Folder tree

```
<paper-slug>/
├── 00_review.md                          # top-level index: metadata, status, TOC, current phase
│
├── 10_paper/
│   ├── paper.md                          # source paper (copied in at start)
│   └── metadata.md                       # title, authors, venue, date, model versions, run id
│
├── 20_orientation/
│   ├── 00_orientation.md                 # overview + cross-agent comparison
│   ├── claude.md                         # Claude's paper map as markdown
│   ├── codex.md                          # Codex's paper map
│   └── gemini.md                         # Gemini's paper map
│
├── 30_discovery/                         # organized BY METHOD, agents as subfiles
│   ├── 00_discovery.md                   # summary across methods and agents
│   ├── m2_contradictions/
│   │   ├── 00_m2.md                      # per-method summary, cross-agent
│   │   ├── claude.md                     # Claude's contradictions findings
│   │   ├── codex.md
│   │   └── gemini.md
│   ├── m3_transformations/
│   │   ├── 00_m3.md
│   │   ├── claude.md
│   │   ├── codex.md
│   │   └── gemini.md
│   ├── m4_counterexamples/
│   ├── m5_immanent/
│   └── m6_disentangling/
│
├── 40_ranking/
│   ├── 00_ranking.md                     # overview + scoring methodology
│   ├── issue_register.md                 # canonical list of all merged issues, stable IDs
│   ├── triage.md                         # filtered-out candidate issues + reasons
│   └── verification.md                   # Gemini web verification results
│
├── 50_debates/
│   ├── 00_debates.md                     # map of debated issues with status
│   ├── 01_<issue_slug>/                  # <rank>_<slug>, one folder per debated issue
│   │   ├── 00_issue.md                   # original claim + link back to register
│   │   ├── r1_prosecute.md               # prompt + structured output + session link + metadata
│   │   ├── r1_defend.md
│   │   ├── r1_synthesize.md
│   │   ├── r2_prosecute.md               # if debate continues
│   │   ├── r2_defend.md
│   │   ├── r2_synthesize.md
│   │   └── 99_summary.md                 # final state + constructive suggestion
│   ├── 02_<issue_slug>/
│   └── ...
│
├── 60_final_report/
│   └── referee_report.md                 # THE deliverable
│
└── _artifacts/                           # machine artifacts, non-markdown where possible
    ├── manifest.md                       # human-readable index of everything in _artifacts
    ├── tickets.json                      # DAG state (source of truth for orchestration)
    ├── prompts/
    │   ├── orient_claude.md              # exact prompt sent to claude for orientation
    │   ├── orient_codex.md
    │   ├── discover_claude_m2.md
    │   └── ...
    ├── sessions/                         # raw agent reasoning traces — NEVER wiped
    │   ├── orient_codex.log              # copied by agent-ctl on ticket completion
    │   ├── orient_gemini.log
    │   ├── discover_codex_m4.log
    │   └── ...
    └── json/                             # raw structured outputs
        ├── orient_claude.json
        ├── orient_codex.json
        ├── orient_gemini.json
        ├── discover_claude_m2.json
        └── ...
```

## Principles

### Numeric prefixes with gaps

Top-level folders use `00, 10, 20, 30, ...` not `00, 01, 02, ...`. This lets us insert new stages (for example a `25_clarification` phase if the skill grows) without renumbering everything.

Within each folder, files that serve as the folder's index use `00_<name>.md` so they sort first. Debate rounds use `r1_, r2_, r3_` prefixes; the final summary uses `99_summary.md` so it sorts last.

### `00_review.md` is the entry point

Obsidian does not treat `README.md` as a special folder index. So the entry point at every level is a numbered file that sorts first: `00_review.md` at the paper root, `00_orientation.md` inside orientation, `00_issue.md` inside a debate folder, etc.

### Discovery is organized by method

The mental model: "what contradictions were found?" is the useful question at ranking time, not "what did Codex find across all methods?" Methods are the first-level split; agents are subfiles within each method. The opposite choice (agent-first) would have been better for tracking provenance, but comparison matters more than provenance here.

### Canonical issue register

`40_ranking/issue_register.md` is the single source of truth for all merged issues. Every reference to an issue in the debates, final report, or verification links back to its entry in the register. Issue IDs are stable — once assigned, they do not change.

### `_artifacts/` uses non-markdown for raw data

Session logs are `.log`, not `.md`. Raw structured outputs are `.json`, not `.md`. This keeps them preserved but prevents Obsidian from polluting its search index, backlink graph, and graph view with thousands of lines of raw agent reasoning. Obsidian treats non-markdown files as attachments — accessible but not first-class content.

The only `.md` files in `_artifacts/` are:
- `manifest.md` — a human-readable index of everything in `_artifacts/`
- `prompts/*.md` — exact prompts sent to agents (rendered as markdown for readability but rarely navigated)

### Reasoning traces live in session logs, not debate files

Debate files (`r1_prosecute.md`, etc.) contain: the prompt, the structured output, the agent's metadata (model, timing, tokens), and a link to the full session log in `_artifacts/sessions/`. The full reasoning trace is preserved in the `.log` file. This keeps debate files readable and session logs complete.

### Three full paper maps, not shared + deltas

Each agent produces an independent paper map. The three maps are NOT merged. This preserves the independence that makes cross-agent support a strong ranking signal.

### Frontmatter minimal and flat

Every `.md` file that is navigated as a Dataview target (paper root, debates, final report) has frontmatter like:

```yaml
---
tags: [disputatio, referee-report, <paper-slug>]
paper: "<paper title>"
venue: "<journal>"
phase: orientation | discovery | ranking | debate | complete
date: 2026-04-09
---
```

Nothing nested, nothing dynamic. Obsidian Dataview can query across papers easily.

### Stable slugs

The paper slug (used in folder name) is chosen at start and never changes. Debate issue slugs are chosen at merge time and never change. Renames break links and external tooling — don't rename.

## Agent-ctl and Obsidian

`agent-ctl run-dag` automatically preserves session logs into `_artifacts/sessions/<ticket_id>.log` when a ticket completes successfully. The destination is derived from the `tickets.json` parent directory. No configuration needed.

`agent-ctl cleanup` only wipes the volatile scratch in `/tmp/agent-ctl/`. Since session logs are archived at ticket completion, nothing important lives in `/tmp/` by the time cleanup runs.

## Life cycle

A review follows this write pattern:

1. **Start**: Claude creates the paper folder, writes `00_review.md` (phase: orientation), `10_paper/paper.md`, `_artifacts/tickets.json` with wave 1 tickets, and `_artifacts/prompts/*.md` for wave 1.
2. **Wave 1 runs**: `agent-ctl run-dag` executes orientation tickets. JSON outputs land in `_artifacts/json/`. Session logs are archived to `_artifacts/sessions/` on completion.
3. **Claude renders**: between waves, Claude reads the JSON outputs and writes curated markdown to `20_orientation/{claude,codex,gemini}.md`. The `00_orientation.md` summary is written. `00_review.md` is updated to phase: discovery.
4. **Wave 2 emits**: Claude emits discovery tickets, writes their prompts to `_artifacts/prompts/`, updates `_artifacts/tickets.json`, runs `run-dag`.
5. **Wave 2 runs and renders**: same pattern. Discovery markdown goes to `30_discovery/m<N>/{claude,codex,gemini}.md`.
6. ... and so on through merge, verify, debate, final report.

At any point, the user can open the paper folder in Obsidian and see exactly where things stand. The `00_review.md` at the top always reflects the current phase.
