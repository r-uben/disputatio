---
name: disputatio
description: High-precision academic paper review via seven-method dialectic debate
---

# Disputatio

Review an academic paper as a top-journal referee would, using seven methods of critical dialectic executed by three independent AI agents. The goal is not to be polite — the goal is to subject the paper to the kind of scrutiny that makes it publishable.

Orchestration is durable: every agent call is a **ticket** in a DAG on disk. The pipeline is resumable, auditable, and replayable by construction.

## Usage

```
/disputatio <path-to-paper> [--top-n 8] [--max-rounds 3] [--skip-web]
```

Options:
- `--top-n N` — debate the top N merged issues (default 8)
- `--max-rounds R` — maximum debate rounds per issue (default 3)
- `--skip-web` — disable web verification (default: enabled)

## The seven methods

Each method is described in detail under `templates/methods/`. They are not labels — they are operational procedures.

| # | Method | File | Role |
|---|--------|------|------|
| 1 | Structured disputation | `m1_disputation.md` | Gives every debate round its formal structure (quaestio → objections → sed contra → respondeo → replies) |
| 2 | Interrogation by contradiction | `m2_contradiction.md` | Finds pairs of claims that cannot both be true |
| 3 | Systematic transformation | `m3_transformation.md` | Runs each claim through eight mechanical transformations (negate, strengthen, weaken, substitute, reverse, consequence, boundary, analogy) |
| 4 | Counterexample construction | `m4_counterexample.md` | Tries to construct a case satisfying the assumptions but violating the conclusion; exposes hidden lemmas |
| 5 | Self-measured critique | `m5_immanent.md` | Finds the paper's own commitments and hunts for passages where the paper violates them. Strongest form of criticism |
| 6 | Causal disentangling | `m6_disentangling.md` | For each causal claim, enumerates co-factors and co-effects the paper has not ruled out |
| 7 | Iterative refinement | `m7_refinement.md` | Operates in synthesis: produces the refined claim after each round |

Methods 2-6 are **generative** (they find issues). Method 1 is **structural** (it shapes each round). Method 7 is **iterative** (it refines claims across rounds).

## Ticket DAG orchestration

Every agent call is a ticket on disk. Tickets live in `<paper-folder>/_artifacts/tickets.json` inside the Obsidian vault. The ticket schema, the wave protocol (how tickets are emitted), and the ID naming conventions are defined in `templates/emit_tickets.md`. Read that file before implementing any step of the protocol.

**Execution model**:
- Claude generates tickets in **waves**. Each wave depends on the outputs of the previous wave.
- `agent-ctl run-dag <paper-folder>/_artifacts/tickets.json --concurrent 3` executes all ready tickets in parallel up to the concurrency cap, then exits when no more ready tickets remain.
- Claude-typed tickets (`orient_claude`, `merge_rank`, `final_report`, wave-emission logic) are executed by Claude directly, not by agent-ctl.
- After `run-dag` exits, Claude inspects the outputs, renders them as curated markdown into the numbered folders, generates the next wave of tickets, and calls `run-dag` again.

**Automatic session archiving**: `agent-ctl run-dag` copies the session log (raw agent reasoning trace) into `<tickets_parent>/sessions/<ticket_id>.log` when a ticket finishes — both on success and on failure. The archive location is derived from the tickets.json parent directory, so for disputatio it lands in `<paper-folder>/_artifacts/sessions/`. Nothing is deleted; every reasoning trace is preserved forever.

**Key benefit — full provenance**: every agent call is replayable. The ticket stores the prompt path, inputs, outputs, timing, attempt count, and session ID. Combined with the stored prompt files, output files, and archived session logs, the entire review is replayable and auditable.

**Monitoring**: `agent-ctl dag-status <paper-folder>/_artifacts/tickets.json` prints a summary of ticket states at any time.

**Resumability**: the ticket DAG is the source of truth. Closing Claude Code, restarting later, and re-running the skill picks up from where it left off — ready tickets resume, already-done tickets are skipped.

## Protocol

The review proceeds in six phases. Each phase corresponds to one or more waves of tickets (see `templates/emit_tickets.md` for the exact ticket definitions).

### Phase 0 — Orientation (parallel, all agents)

Each of the three agents reads the paper once and produces a neutral **paper map**: claims, equations, propositions, assumptions, parameters, datasets, citations, section anchors, and OCR-corrupted regions. No judgments yet.

Raw outputs land in `_artifacts/json/orient_<agent>.json`; Claude then renders them as markdown into `0_orientation/<agent>.md`. The three maps are not merged — each agent uses its own map as its cache for the subsequent discovery passes. This preserves **model independence**: agents should not be anchored to each other's reading of the paper.

Run all three agents in parallel. Estimated time: ~15-20 minutes wall clock (Codex with `--full-auto` does deep web cross-referencing).

### Phase 1 — Discovery (fan-out-fan-out parallel)

Each agent runs **all five generative methods** (M2-M6) on the paper, using its own paper map as the cache. Each method produces one JSON output file containing all issues it found. Total: 3 agents × 5 methods = **15 discovery sweeps**, producing 15 JSON files.

Raw outputs land in `_artifacts/json/discover_<agent>_m<N>.json`. Claude then renders them as markdown, organized by method, into `1_discovery/m<N>/<agent>.md`.

**Parallelism**: the 3 agents run in parallel. Within each agent, the 5 methods should also run in parallel where the CLI supports it (if not, sequential within the agent). Target wall clock: 10-15 minutes.

**OCR-aware**: discovery prompts warn agents about OCR artifacts and instruct them not to flag corrupted passages as paper errors.

**Web search**: not triggered in this phase. Closed-book discovery.

### Phase 2 — Merge, rank, and verify

After discovery, Claude executes the merge and rank procedure described in `templates/merge_and_rank.md`:

1. **Triage** obvious non-issues (OCR artifacts, presentation-only complaints, low-confidence singletons)
2. **Deduplicate** — cluster candidate issues that point to the same underlying concern
3. **Rank** using the scoring function:
   - **Centrality** (0-3): how close to the paper's main contribution
   - **Cross-agent support** (0-3, weighted ×2): how many different agents found it
   - **Evidence specificity** (0-3): quote + falsifier + reproduction steps
   - **Severity** (0-3): what happens if the finding is correct
   - **Score = centrality + 2·cross_agent_support + evidence_specificity + severity** (max 15)
4. **Web verification**: Gemini fetches external evidence for issues marked `needs_web_verification: true`. Confirmed issues get +2 score; refuted issues get -3 and may be filtered out. See `templates/verify.md`.
5. **Budget cut**: only the top N issues (default 8) enter the debate phase. Below-cutoff issues are preserved in the final report as "appendix concerns."

**Ranking priority**: cross-agent support is weighted double because it is the strongest signal. Five methods on one model are correlated; agreement across different architectures is much more meaningful.

### Phase 3 — Dialectic debate (parallel across issues)

Each top-ranked issue enters a dialectic debate. The debate follows the structured disputation format (Method 1): quaestio → objections → sed contra → respondeo → replies → synthesis.

**Role rotation** across rounds:

| Round | Prosecutor | Defender | Synthesizer |
|-------|-----------|----------|-------------|
| 1 | Claude | Codex | Gemini |
| 2 | Codex | Gemini | Claude |
| 3 | Gemini | Claude | Codex |

The prosecutor picks **2-3 methods** from M2-M6 (see `templates/prosecute.md` for the selection heuristic) and applies them to the issue. The defender uses Method 1 to reply to each objection individually. The synthesizer applies Method 7 to produce the refined claim.

**Parallelism**: issues are debated in parallel, but within an issue the path is strictly sequential (prosecute → defend → synthesize). Cap concurrent issues at 2-3 to avoid rate-limiting the weaker model (typically Gemini).

**Short-circuit rules** (aggressive):
- **Pre-debate triage**: if an issue scored below the cutoff, skip it
- **Round 1 early-kill**: if the round 1 synthesis produces `impact: none`, stop — the issue dies
- **Stalled debate**: if round N synthesis is materially identical to round N-1 synthesis, mark `converged` and stop
- **Low priority cap**: budget tiering applies (see Configuration) — bottom third of top-N get 1 round, middle third get `max-rounds - 1`, top third get the full budget

### Phase 4 — Final report

Claude executes the `final_report` ticket inline and writes two outputs:

1. **`_artifacts/json/final.json`** — structured final report:
   - Surviving material issues with full debate history
   - Surviving local issues with brief summary
   - Dropped issues with the reason
   - Appendix concerns (below-cutoff issues)
   - Web-verified external evidence
   - Overall assessment

2. **`4_report/referee_report.md`** — the human-facing deliverable, rendered from the JSON using `templates/obsidian_render.md`.

Claude also updates `review.md` at the top of the paper folder to set `phase: complete` and populate the summary section. The paper folder itself — with all its numbered subfolders and the top-level index — IS the final live report.

### Phase 5 — Per-finding self-evaluation

After the report is written, the orchestrator runs a quality pass on the review itself as a **self-contained sub-DAG under `_evaluation/`** — its own `tickets.json`, `prompts/`, `annotations/`, and results, cleanly separated from the main pipeline's `_artifacts/`.

Findings are blinded with randomised `BF###` IDs (not `merged_NNN`). The orchestrator shuffles every finding being evaluated into one pool, assigns `BF###` in shuffled order, and writes `_evaluation/manifest_blind.json` with the `blind_id → (true_version, true_id)` map. The manifest is the only place this mapping exists; the annotator never sees it. For cross-review evaluation, V2 / V3 / coarse / reference findings all share the same shuffled pool — the annotator cannot tell which review produced which finding, either by ID, by position, or by metadata (stripped from the payload at emit time).

Each `evaluate` ticket points at a self-contained prompt at `_evaluation/prompts/<blind_id>.md` that inlines the rubric, the finding JSON, and the full paper text. The ticket's `inputs` list contains only the prompt file — everything the annotator needs is inside it. Default annotator: **codex with `gpt-5.4-mini`** (matches the 2026-04-12 manual baseline).

Each annotator returns a two-axis judgement written to `_evaluation/annotations/<blind_id>.json`: `quote_verified ∈ {yes, partial, no}` and `calibration ∈ {supported, overclaimed, unsupported}`, plus optional notes. The aggregator (Claude inline, no ticket) reads every annotation, joins with the blind manifest, writes `_evaluation/results.json` (flat `rows` + per-version `summary`), and renders `_evaluation/00_evaluation.md` (scorecard markdown) and `_evaluation/annotations_unblinded.csv` (human-readable join).

The evaluation **does not feed back into the review** — it is a separate quality assessment recorded alongside. The `overclaim_rate` is the metric that earns its keep: it discriminates a debate-hardened review (which walks back overconfident claims) from an aggressive single-pass one (which keeps them).

See `templates/evaluation.md` for the protocol and `templates/evaluate.md` for the per-finding prompt body.

## Workspace structure

**The Obsidian folder IS the workspace.** There is no separate scratch area. Every review is a self-contained folder inside the Obsidian vault. Curated markdown (the human-facing review) lives in numbered top-level folders; raw machine artifacts (tickets, JSON outputs, prompts, session logs) live inside `_artifacts/`.

```
~/.../notes/work/referee-reports/<paper-slug>/
│
├── review.md                          # top-level index: metadata, status, TOC
│
├── _paper/
│   └── paper.md                          # source paper
│
├── 0_orientation/                       # 3 paper maps as markdown
│   ├── 00_orientation.md
│   ├── claude.md
│   ├── codex.md
│   └── gemini.md
│
├── 1_discovery/                         # organized BY METHOD
│   ├── 00_discovery.md
│   ├── m2_contradictions/
│   │   ├── 00_m2.md
│   │   ├── claude.md
│   │   ├── codex.md
│   │   └── gemini.md
│   └── m3_transformations/ ... m6_disentangling/
│
├── 2_ranking/
│   ├── 00_ranking.md
│   ├── issue_register.md                 # canonical source of truth for all issues
│   ├── triage.md
│   └── verification.md
│
├── 3_debates/                           # one folder per debated issue
│   ├── 00_debates.md
│   ├── 01_<slug>/
│   │   ├── 00_issue.md
│   │   ├── r1_prosecute.md               # prompt + output + metadata + link to session
│   │   ├── r1_defend.md
│   │   ├── r1_synthesize.md
│   │   └── 99_summary.md
│   └── ...
│
├── 4_report/
│   └── referee_report.md                 # the deliverable
│
├── _evaluation/                          # per-finding self-evaluation (sub-DAG)
│   ├── 00_evaluation.md                  # aggregate scorecard (markdown)
│   ├── annotations_unblinded.csv         # human-readable join of rows + manifest
│   ├── manifest_blind.json               # blind_id → (true_version, true_id)
│   ├── tickets.json                      # eval sub-DAG
│   ├── results.json                      # machine truth: flat rows + per-version summary
│   ├── prompts/<blind_id>.md             # self-contained prompt per finding
│   ├── annotations/<blind_id>.json       # per-finding two-axis output
│   ├── sessions/<blind_id>.log           # raw annotator session capture
│   └── disagreements.md                  # only when ≥2 annotators ran (deferred)
│
└── _artifacts/                           # main-pipeline machine artifacts
    ├── manifest.md                       # human-readable index
    ├── tickets.json                      # the main DAG
    ├── prompts/                          # one .md per main-pipeline ticket
    ├── sessions/                         # raw agent reasoning traces (.log, never wiped)
    └── json/                             # raw structured outputs (.json)
```

See `templates/obsidian_structure.md` for the complete specification.

See `templates/obsidian_render.md` for how Claude transforms each JSON artifact into curated markdown.

## Agent routing

| Agent | CLI | Model | Special role |
|-------|-----|-------|--------------|
| Claude | Claude Code (you) | opus/sonnet | Orchestrator + runs discovery + role-rotates in debate |
| Codex | `/codex` via agent-ctl | GPT-5.4 | Independent reader + runs discovery + role-rotates in debate |
| Gemini | `/gemini` via agent-ctl | Gemini 3.1 Pro Preview | Independent reader + runs discovery + **external-evidence specialist (web search)** + role-rotates in debate |

Gemini's unique web search capability means it owns the verification step in Phase 2 — even for findings originally produced by other agents. This concentrates web search usage into a single agent that is specialized for it, rather than spreading it thin.

## Agent communication

Use `agent-ctl` to manage sessions. The DAG runner is the primary interface:

```bash
A="python3 ~/.claude/skills/agent_ctl.py"

# Run the DAG — executes all ready tickets, blocks until none remain
$A run-dag <paper-folder>/_artifacts/tickets.json --cwd <paper-folder> --concurrent 3

# Check progress without blocking
$A dag-status <paper-folder>/_artifacts/tickets.json
```

The lower-level commands are still available for ad-hoc agent calls (deprecated for the disputatio pipeline — use tickets instead):

```bash
$A start codex "$(cat /tmp/prompt.md)" --cwd <workspace> --timeout 900
$A wait 01 02 03
$A result 01
```

**Prompt files**: for long prompts (with paper map content, prior round history, etc.), write the prompt to a temp file and pass `$(cat /tmp/prompt-file.md)` to agent-ctl. Inline prompts larger than a few KB will break shell escaping.

**Context injection**: always paste paper excerpts, issue state, and prior round content **inline** in the prompt. Do not rely on agents being able to read workspace files — some CLIs (Gemini) cannot write files even when given paths, and some cannot reliably read gitignored directories.

**Output verification**: after each agent call, verify the output file exists before proceeding. If missing, parse the agent's stdout via `$A result <id>` and write the file manually. Both Codex and Gemini sometimes hallucinate file writes.

**Retry logic**: if an agent fails (timeout, rate limit, hallucinated success), retry once with a simplified prompt. If it fails again, default to KEEP (preserve the issue as-is, note the failure in the checkpoint, continue).

## Execution

When `/disputatio <path>` is invoked, Claude runs a decision loop. Each iteration: read state from disk, match the current phase, do ONE thing, write results to disk. No multi-step sequential protocol — just a lookup table.

**State**: `$PAPER/_artifacts/tickets.json` (the DAG) + `$PAPER/review.md` frontmatter (human-readable phase).

**Loop**: repeat until `final_report` ticket status is `done`:

```
READ tickets.json
MATCH current state → action:

┌─────────────────────────────────────┬──────────────────────────────────────────────────────┐
│ State                               │ Action                                               │
├─────────────────────────────────────┼──────────────────────────────────────────────────────┤
│ no tickets.json exists              │ INIT: create workspace, copy paper, emit wave 1,     │
│                                     │ write tickets.json                                   │
├─────────────────────────────────────┼──────────────────────────────────────────────────────┤
│ orient_claude = pending             │ Execute orient_claude inline: read paper, produce     │
│                                     │ paper map JSON, mark done                            │
├─────────────────────────────────────┼──────────────────────────────────────────────────────┤
│ orient_codex or orient_gemini       │ Run: $A run-dag tickets.json --concurrent 3          │
│ = pending                           │ Wait for completion. Validate outputs.               │
├─────────────────────────────────────┼──────────────────────────────────────────────────────┤
│ all orient = done,                  │ RENDER orientation (JSON → markdown in 20_orient/).  │
│ no discover tickets exist           │ Emit wave 2 (18 discovery tickets). Write prompts.   │
├─────────────────────────────────────┼──────────────────────────────────────────────────────┤
│ discover_claude_* = pending         │ Execute Claude discovery tickets inline (6 methods).  │
│                                     │ Write JSON outputs. Mark each done.                  │
├─────────────────────────────────────┼──────────────────────────────────────────────────────┤
│ discover_codex_* or                 │ Run: $A run-dag tickets.json --concurrent 3          │
│ discover_gemini_* = pending         │ Wait for completion. Validate outputs.               │
├─────────────────────────────────────┼──────────────────────────────────────────────────────┤
│ all discover = done,                │ RENDER discovery (JSON → markdown in 1_discovery/). │
│ no merge_rank ticket exists         │ Execute merge_rank inline: read 18 JSONs, triage,    │
│                                     │ dedupe, rank, write ranked_issues.json + triage.json.│
│                                     │ Render 2_ranking/ markdown. Emit verify ticket.     │
├─────────────────────────────────────┼──────────────────────────────────────────────────────┤
│ verify = pending                    │ Run: $A run-dag tickets.json --concurrent 1          │
│                                     │ (Gemini web verification). Validate output.          │
│                                     │ Render 2_ranking/verification.md.                   │
├─────────────────────────────────────┼──────────────────────────────────────────────────────┤
│ verify = done,                      │ Emit debate round 1 tickets for top N issues.        │
│ no debate tickets exist             │ Apply budget tiering. Write prompts.                 │
├─────────────────────────────────────┼──────────────────────────────────────────────────────┤
│ debate tickets pending/running      │ For Claude-typed debate tickets: execute inline.      │
│                                     │ For external: $A run-dag --concurrent 2              │
│                                     │ After each synthesis: read output, check status.     │
│                                     │ If continue + budget remains → emit next round.      │
│                                     │ If converged/none → mark issue terminal.             │
│                                     │ Render debate markdown in 3_debates/.               │
├─────────────────────────────────────┼──────────────────────────────────────────────────────┤
│ all debate tickets terminal,        │ Execute final_report inline: read all syntheses +     │
│ no final_report ticket              │ ranked issues. Write final.json + referee_report.md.  │
│                                     │ Update review.md to phase: complete.              │
├─────────────────────────────────────┼──────────────────────────────────────────────────────┤
│ final_report = done,                │ Collect findings (single or cross-review). Shuffle.  │
│ no _evaluation/tickets.json exists  │ Assign BF### IDs. Write _evaluation/manifest_blind.  │
│                                     │ json. Build one self-contained prompt per finding    │
│                                     │ at _evaluation/prompts/<blind_id>.md (rubric + JSON  │
│                                     │ + paper inlined). Emit one evaluate ticket per BF### │
│                                     │ into _evaluation/tickets.json, routed to             │
│                                     │ codex/gpt-5.4-mini.                                   │
├─────────────────────────────────────┼──────────────────────────────────────────────────────┤
│ _evaluation/tickets.json exists,    │ $A run-dag _evaluation/tickets.json --concurrent 4.  │
│ eval tickets pending/running        │ Wait for completion. Validate each annotation JSON   │
│                                     │ has blind_id + two-axis fields.                       │
├─────────────────────────────────────┼──────────────────────────────────────────────────────┤
│ all evaluate tickets done,          │ Execute aggregator inline: read every                │
│ no _evaluation/results.json         │ _evaluation/annotations/*.json, join with            │
│                                     │ manifest_blind.json, write _evaluation/results.json  │
│                                     │ (flat rows + per-version summary). Render            │
│                                     │ _evaluation/00_evaluation.md + annotations_unblinded.│
│                                     │ csv from results.json.                                │
├─────────────────────────────────────┼──────────────────────────────────────────────────────┤
│ _evaluation/results.json exists     │ EXIT. Review complete and self-evaluated.            │
└─────────────────────────────────────┴──────────────────────────────────────────────────────┘
```

### INIT procedure

When no `tickets.json` exists:

1. Determine `<paper-slug>` from the input filename (lowercase, hyphens, no extension)
2. Set `$PAPER = ~/Library/Mobile Documents/iCloud~md~obsidian/Documents/notes/work/referee-reports/<paper-slug>/`
3. Create directory structure: `mkdir -p $PAPER/{_paper,0_orientation,1_discovery/{m0_close_reading,m2_contradictions,m3_transformations,m4_counterexample,m5_immanent,m6_disentangling},2_ranking,3_debates,4_report,_artifacts/{prompts,json,sessions},_evaluation}`
4. If input is `.pdf`: run `socr <input>` → copy result to `$PAPER/_paper/paper.md`. If input is `.md`: copy directly.
5. Copy the PDF (if available) to `$PAPER/_paper/paper.pdf`
6. Write `$PAPER/review.md` with frontmatter: `phase: orientation`
7. Generate 3 orientation prompts (see "Prompt generation" below)
8. Write `$PAPER/_artifacts/tickets.json` with 3 orient tickets

### Prompt generation

To generate a prompt for a ticket:

1. Read the relevant template from `templates/` (e.g., `orient.md`, `discover.md`)
2. For discovery: also read the method template from `templates/methods/<method>.md`
3. Substitute placeholders:
   - `{{paper_text}}` → contents of `_paper/paper.md` (used in orient prompts only)
   - `{{paper_path}}` → `_paper/paper.md` (relative path for agents to read)
   - `{{paper_map_path}}` → `_artifacts/json/orient_<agent>.json`
   - `{{output_path}}` → `_artifacts/json/<ticket_id>.json`
   - `{{method_content}}` → full text of the method template
   - `{{issue_state}}`, `{{prosecution}}`, `{{defense}}`, `{{history}}` → debate context
   - `{{config.*}}` → configuration values
4. Write the result to `$PAPER/_artifacts/prompts/<ticket_id>.md`

### Inline execution (Claude-typed tickets)

When Claude executes a ticket inline:

1. Read the prompt at `_artifacts/prompts/<ticket_id>.md`
2. Read all input files listed in the ticket
3. Follow the prompt instructions (produce paper map / run method / merge issues / write report)
4. Write the JSON output to `_artifacts/json/<ticket_id>.json`
5. Write a reasoning summary to `_artifacts/sessions/<ticket_id>.log` (what was done, key decisions, issues found)
6. Apply the rendering spec from `templates/obsidian_render.md` to write curated markdown
7. Update `tickets.json`: set status to `done`, set `finished_at`

### Rendering

After each wave, render JSON outputs to Obsidian markdown per `templates/obsidian_render.md`. The JSON is the source of truth; the markdown is a human-readable projection. Both are preserved.

### Output validation (verification gates)

Before proceeding to the next phase, validate outputs:

- **Orientation**: each JSON must have `main_claims` with >=5 entries. If fewer, retry once.
- **Discovery**: each JSON must have `issues` array with >=1 entry. Empty outputs get one retry.
- **Merge_rank**: `ranked_issues.json` must have >=3 merged issues. Fewer triggers a warning (not a retry — paper may genuinely have few issues).
- **Debate synthesis**: JSON must have `refined_claim`, `impact`, and `status` fields. Malformed → retry.

### Logging contract

Every action writes to disk. Nothing lives only in Claude's context.

| What | Where | When |
|------|-------|------|
| Prompts sent to agents | `_artifacts/prompts/<ticket_id>.md` | Before launching ticket |
| Raw JSON output | `_artifacts/json/<ticket_id>.json` | After ticket completes |
| Agent session logs | `_artifacts/sessions/<ticket_id>.log` | Auto-archived by agent-ctl; written by Claude for inline tickets |
| Curated markdown | Numbered folders (0_orientation/, etc.) | After each wave |
| DAG state | `_artifacts/tickets.json` | After every action |
| Phase status | `review.md` frontmatter | At each major transition |

### Resumability

On re-invocation with an existing paper folder:

1. Read `$PAPER/_artifacts/tickets.json`
2. Skip all `done` tickets
3. Match current state in the decision table above
4. Resume from the first non-terminal state

This works because every action writes to disk before proceeding. If Claude crashes mid-wave, the completed tickets are marked `done` and the uncompleted ones are still `pending`.

## Configuration

All tunables are CLI parameters with sensible defaults. Templates reference these via `{{config.*}}` placeholders — no thresholds are hardcoded in prompts.

| Parameter | CLI flag | Default | Notes |
|-----------|----------|---------|-------|
| Top-N for debate | `--top-n` | 8 | Issues above this enter debate; rest go to appendix |
| Max rounds per issue | `--max-rounds` | 3 | Short-circuit rules can end earlier |
| Verification score delta (confirmed) | `--verify-boost` | +2 | Added to rank score when web evidence confirms |
| Verification score delta (refuted) | `--verify-penalty` | -3 | Subtracted from rank score when web evidence refutes |
| Web search budget | `--web-budget` | 5 | Max searches per issue during verification |
| Orientation timeout | `--orient-timeout` | 1200s | Per agent — must accommodate web cross-referencing |
| Discovery timeout | `--discover-timeout` | 1200s | Per agent, per method |
| Debate round timeout | `--debate-timeout` | 900s | Per agent, per role |

**Budget tiering** is derived from `--top-n` and `--max-rounds`, not hardcoded. The top third of debated issues get the full round budget, the middle third get `max-rounds - 1`, the bottom third get 1 round. This scales automatically with different top-n values.

**Timeout guidance**: Codex with `--full-auto` can perform web searches mid-session. When it does, it often cross-references the published version of the paper to verify OCR content. This is valuable but takes time. A 10-minute budget is too tight; 20 minutes is the minimum for orientation. Short timeouts kill the agent mid-file-write, losing all work.

### Model routing

Not every task needs the strongest model. Use cheaper/faster models for mechanical work, reserve expensive models for judgment calls. When emitting tickets, set the `model` field per this table:

| Task | Claude | Codex | Gemini |
|------|--------|-------|--------|
| Orientation | sonnet | gpt-5.4-mini | gemini-3-flash-preview |
| Discovery (M0-M6) | sonnet | gpt-5.4-mini | gemini-3-flash-preview |
| Rendering (JSON→md) | haiku | — | — |
| Merge & Rank | **opus** | — | — |
| Prosecution (top third) | **opus** | — | — |
| Prosecution (rest) | sonnet | — | — |
| Defense | — | gpt-5.4 | gemini-3.1-pro-preview |
| Synthesis | **opus** | — | — |
| Verification (web) | — | — | gemini-3.1-pro-preview |
| Final report | **opus** | — | — |

This cuts Opus usage to ~30% of the pipeline (merge, top prosecutions, synthesis, final report). The remaining 70% runs on Sonnet/Haiku/mini models at a fraction of the cost.

For Claude subagents, pass the `model` parameter: `Agent(model="sonnet")` or `Agent(model="haiku")`. For external agents, set the `model` field in the ticket and agent-ctl passes it via `-m`.

## Review criteria

The methods determine what counts as an issue. No external criteria file is needed — each method's template defines what it flags.

## Obsidian is the workspace

Every review lives inside a single folder in the Obsidian vault. Curated markdown (what you'd read as a human) lives in numbered folders at the top level; raw machine artifacts (tickets, prompts, JSON outputs, session logs) live inside `_artifacts/`. Nothing is ever deleted — session logs are automatically archived by `agent-ctl run-dag` so that every reasoning trace is preserved forever.

**Templates**:
- `templates/obsidian_structure.md` — the complete folder spec and design principles
- `templates/obsidian_render.md` — how Claude transforms each JSON artifact into curated markdown

**Key principle**: the JSON in `_artifacts/json/` is the machine format; the markdown in the numbered folders is the human format. Both are preserved. If the two disagree, the JSON wins. The markdown is a projection, not the source of truth.

**Why everything in Obsidian**: a review should be self-contained. Open one folder, see everything. The raw logs are there too (as `.log` attachments that don't pollute Obsidian's search index) so auditability and replay work without chasing files across disks.
