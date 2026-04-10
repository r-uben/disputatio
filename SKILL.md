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

The review proceeds in five phases. Each phase corresponds to one or more waves of tickets (see `templates/emit_tickets.md` for the exact ticket definitions).

### Phase 0 — Orientation (parallel, all agents)

Each of the three agents reads the paper once and produces a neutral **paper map**: claims, equations, propositions, assumptions, parameters, datasets, citations, section anchors, and OCR-corrupted regions. No judgments yet.

Raw outputs land in `_artifacts/json/orient_<agent>.json`; Claude then renders them as markdown into `20_orientation/<agent>.md`. The three maps are not merged — each agent uses its own map as its cache for the subsequent discovery passes. This preserves **model independence**: agents should not be anchored to each other's reading of the paper.

Run all three agents in parallel. Estimated time: ~15-20 minutes wall clock (Codex with `--full-auto` does deep web cross-referencing).

### Phase 1 — Discovery (fan-out-fan-out parallel)

Each agent runs **all five generative methods** (M2-M6) on the paper, using its own paper map as the cache. Each method produces one JSON output file containing all issues it found. Total: 3 agents × 5 methods = **15 discovery sweeps**, producing 15 JSON files.

Raw outputs land in `_artifacts/json/discover_<agent>_m<N>.json`. Claude then renders them as markdown, organized by method, into `30_discovery/m<N>/<agent>.md`.

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

2. **`60_final_report/referee_report.md`** — the human-facing deliverable, rendered from the JSON using `templates/obsidian_render.md`.

Claude also updates `00_review.md` at the top of the paper folder to set `phase: complete` and populate the summary section. The paper folder itself — with all its numbered subfolders and the top-level index — IS the final live report.
   - Final assessment at the bottom

## Workspace structure

**The Obsidian folder IS the workspace.** There is no separate scratch area. Every review is a self-contained folder inside the Obsidian vault. Curated markdown (the human-facing review) lives in numbered top-level folders; raw machine artifacts (tickets, JSON outputs, prompts, session logs) live inside `_artifacts/`.

```
~/.../notes/work/referee-reports/tests/<paper-slug>/
│
├── 00_review.md                          # top-level index: metadata, status, TOC
│
├── 10_paper/
│   └── paper.md                          # source paper
│
├── 20_orientation/                       # 3 paper maps as markdown
│   ├── 00_orientation.md
│   ├── claude.md
│   ├── codex.md
│   └── gemini.md
│
├── 30_discovery/                         # organized BY METHOD
│   ├── 00_discovery.md
│   ├── m2_contradictions/
│   │   ├── 00_m2.md
│   │   ├── claude.md
│   │   ├── codex.md
│   │   └── gemini.md
│   └── m3_transformations/ ... m6_disentangling/
│
├── 40_ranking/
│   ├── 00_ranking.md
│   ├── issue_register.md                 # canonical source of truth for all issues
│   ├── triage.md
│   └── verification.md
│
├── 50_debates/                           # one folder per debated issue
│   ├── 00_debates.md
│   ├── 01_<slug>/
│   │   ├── 00_issue.md
│   │   ├── r1_prosecute.md               # prompt + output + metadata + link to session
│   │   ├── r1_defend.md
│   │   ├── r1_synthesize.md
│   │   └── 99_summary.md
│   └── ...
│
├── 60_final_report/
│   └── referee_report.md                 # the deliverable
│
└── _artifacts/                           # machine artifacts, non-markdown
    ├── manifest.md                       # human-readable index
    ├── tickets.json                      # the DAG — source of truth for orchestration
    ├── prompts/                          # one .md per ticket
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
| Gemini | `/gemini` via agent-ctl | Gemini 2.5 Pro | Independent reader + runs discovery + **external-evidence specialist (web search)** + role-rotates in debate |

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

## Checkpointing

**Tickets are the checkpoint.** `_artifacts/tickets.json` records the status of every unit of work. There is no separate checkpoint file.

To resume a review:
1. Open the paper folder in Obsidian (or navigate to it in the filesystem)
2. `agent-ctl dag-status <paper-folder>/_artifacts/tickets.json` — inspect what is done
3. `agent-ctl run-dag <paper-folder>/_artifacts/tickets.json` — execute any remaining ready tickets
4. Re-invoke `/disputatio` on the same paper folder — Claude picks up the wave-transition work from where it left off (if any Claude-typed tickets are pending, they execute next)

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

## Review criteria

The methods determine what counts as an issue. No external criteria file is needed — each method's template defines what it flags.

## Obsidian is the workspace

Every review lives inside a single folder in the Obsidian vault. Curated markdown (what you'd read as a human) lives in numbered folders at the top level; raw machine artifacts (tickets, prompts, JSON outputs, session logs) live inside `_artifacts/`. Nothing is ever deleted — session logs are automatically archived by `agent-ctl run-dag` so that every reasoning trace is preserved forever.

**Templates**:
- `templates/obsidian_structure.md` — the complete folder spec and design principles
- `templates/obsidian_render.md` — how Claude transforms each JSON artifact into curated markdown

**Key principle**: the JSON in `_artifacts/json/` is the machine format; the markdown in the numbered folders is the human format. Both are preserved. If the two disagree, the JSON wins. The markdown is a projection, not the source of truth.

**Why everything in Obsidian**: a review should be self-contained. Open one folder, see everything. The raw logs are there too (as `.log` attachments that don't pollute Obsidian's search index) so auditability and replay work without chasing files across disks.
