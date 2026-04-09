---
name: disputatio
description: High-precision academic paper review via seven-method dialectic debate
---

# Disputatio

Review an academic paper as a top-journal referee would, using seven methods of critical dialectic executed by three independent AI agents. The goal is not to be polite — the goal is to subject the paper to the kind of scrutiny that makes it publishable.

Orchestration is durable: every agent call is a **ticket** in a DAG on disk. The pipeline is resumable, auditable, and reproducible by construction.

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

Every agent call is a ticket on disk. Tickets live in `workspace/<slug>/tickets.json`. The ticket schema, the wave protocol (how tickets are emitted), and the ID naming conventions are defined in `templates/emit_tickets.md`. Read that file before implementing any step of the protocol.

**Execution model**:
- Claude generates tickets in **waves**. Each wave depends on the outputs of the previous wave.
- `agent-ctl run-dag workspace/<slug>/tickets.json --concurrent 3` executes all ready tickets in parallel up to the concurrency cap, then exits when no more ready tickets remain.
- Claude-typed tickets (`orient_claude`, `merge_rank`, `final_report`, wave-emission logic) are executed by Claude directly, not by agent-ctl.
- After `run-dag` exits, Claude inspects the outputs, generates the next wave of tickets, and calls `run-dag` again.

**Key benefit — full provenance**: every agent call is reproducible. The ticket stores the prompt path, inputs, outputs, timing, attempt count, and session ID. Combined with the stored prompt files and output files, the entire review is replayable and auditable.

**Monitoring**: `agent-ctl dag-status workspace/<slug>/tickets.json` prints a summary of ticket states at any time.

**Resumability**: the ticket DAG is the source of truth. Closing Claude Code, restarting later, and re-running the skill picks up from where it left off — ready tickets resume, already-done tickets are skipped.

## Protocol

The review proceeds in five phases. Each phase corresponds to one or more waves of tickets (see `templates/emit_tickets.md` for the exact ticket definitions).

### Phase 0 — Orientation (parallel, all agents)

Each of the three agents reads the paper once and produces a neutral **paper map**: claims, equations, propositions, assumptions, parameters, datasets, citations, section anchors, and OCR-corrupted regions. No judgments yet.

```
workspace/<paper-slug>/orientation/
├── claude/paper_map.json
├── codex/paper_map.json
└── gemini/paper_map.json
```

The three maps are not merged — each agent uses its own map as its cache for the subsequent discovery passes. This preserves **model independence**: agents should not be anchored to each other's reading of the paper.

Run all three agents in parallel. Estimated time: ~5 minutes each, so 5 minutes wall clock.

### Phase 1 — Discovery (fan-out-fan-out parallel)

Each agent runs **all five generative methods** (M2-M6) on the paper, using its own paper map as the cache. Each method produces its own set of candidate issues. Total: 3 agents × 5 methods = **15 discovery sweeps**.

```
workspace/<paper-slug>/discovery/
├── claude/
│   ├── m2/issue_*.json
│   ├── m3/issue_*.json
│   ├── m4/issue_*.json
│   ├── m5/issue_*.json
│   └── m6/issue_*.json
├── codex/
│   └── ... (same structure)
└── gemini/
    └── ... (same structure)
```

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
- **Low priority cap**: issues in the bottom half of the top-N get at most 1 round; middle get 2; top 2-3 get the full 3 rounds

### Phase 4 — Final report

Claude writes two outputs:

1. **`workspace/<paper-slug>/final.json`** — structured final report:
   - Surviving material issues with full debate history
   - Surviving local issues with brief summary
   - Dropped issues with the reason
   - Appendix concerns (below-cutoff issues)
   - Web-verified external evidence
   - Overall assessment

2. **Live Obsidian note** — `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/notes/work/referee-reports/<paper-slug>.md`:
   - Updated after each phase (orientation → discovery → merge → debate → final)
   - Frontmatter includes status, date, paper metadata
   - Debate section shows each round's prosecution, defense, and synthesis
   - Final assessment at the bottom

## Workspace structure

```
workspace/<paper-slug>/
├── paper.md                             # parsed paper
├── tickets.json                         # the DAG — source of truth for orchestration
├── prompts/                             # one file per ticket, stored for audit
│   ├── orient_claude.md
│   ├── discover_codex_m4.md
│   ├── debate_merged_001_r1_prosecute.md
│   └── ...
├── orientation/
│   ├── claude/paper_map.json
│   ├── codex/paper_map.json
│   └── gemini/paper_map.json
├── discovery/
│   ├── claude/{m2,m3,m4,m5,m6}/issue_*.json
│   ├── codex/{m2,m3,m4,m5,m6}/issue_*.json
│   └── gemini/{m2,m3,m4,m5,m6}/issue_*.json
├── triage.json                          # issues filtered out before ranking
├── ranked_issues.json                   # merged + ranked list with web verification
├── rounds/
│   └── <issue_id>/
│       ├── round_1_prosecute.json
│       ├── round_1_defend.json
│       ├── round_1_synthesize.json
│       └── ...
└── final.json
```

`tickets.json` + `prompts/` + the output files constitute a complete, replayable record of the review.

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
$A run-dag workspace/<slug>/tickets.json --concurrent 3

# Check progress without blocking
$A dag-status workspace/<slug>/tickets.json
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

**Tickets are the checkpoint.** `tickets.json` records the status of every unit of work. There is no separate checkpoint file.

To resume a review:
1. Navigate to the workspace
2. `agent-ctl dag-status tickets.json` — inspect what is done
3. `agent-ctl run-dag tickets.json` — execute any remaining ready tickets
4. Re-invoke `/disputatio` on the same workspace — Claude picks up the wave-transition work from where it left off (if any Claude-typed tickets are pending, they execute next)

## Budget defaults

| Parameter | Default | Notes |
|-----------|---------|-------|
| Top-N for debate | 8 | Top 3 get full 3 rounds, middle 3 get 2 rounds, bottom 2 get 1 round |
| Max rounds per issue | 3 | Short-circuit rules can end earlier |
| Orientation timeout | 20 min | per agent — must accommodate web cross-referencing |
| Discovery timeout | 20 min | per agent, per method |
| Debate round timeout | 15 min | per agent, per role |
| Web search budget | 5 queries | per issue |
| Total runtime | ~2-3 hours | wall clock, parallelized |

**Timeout guidance**: Codex with `--full-auto` can perform web searches mid-session. When it does, it often cross-references the published version of the paper to verify OCR content. This is valuable but takes time. A 10-minute budget is too tight; 20 minutes is the minimum for orientation. Short timeouts kill the agent mid-file-write, losing all work.

## Review criteria

The methods determine what counts as an issue. No external criteria file is needed — each method's template defines what it flags.

## Live report (Obsidian)

Maintain a live Obsidian note at `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/notes/work/referee-reports/<paper-slug>.md`. Claude writes and updates this note at every phase transition.

**Template**: `templates/obsidian_report.md` — defines the full structure, frontmatter, per-phase update rules, and the principle that the note is human-facing (not machine-readable). The note is a projection of the workspace, not a source of truth.

The note is the human-readable face of the review: a proper referee report that evolves as the debate unfolds. By the end, it should read as something you could send to the author of the paper or save for your records.
