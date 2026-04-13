# Architecture

How disputatio orchestrates multi-agent paper criticism.

## Two-layer design

**Layer 1: the protocol.** Defined in `SKILL.md` and the `templates/` folder. Pure markdown. Describes ticket types, the wave protocol, the decision loop, and method procedures. Has no executable code of its own.

**Layer 2: the runtime.** Claude Code reads the protocol and executes it. The only auxiliary executable is `agent-ctl` (a Python script under `~/.claude/skills/`), which handles ticket DAG execution, session management for external agents, output validation, and retry logic.

This separation is deliberate: the protocol is portable (any Claude-Code-class orchestrator could run it given the templates), and the runtime is replaceable (`agent-ctl` is one specific implementation; another could be substituted as long as it honors the same ticket schema and CLI contract).

---

## The ticket DAG

Every agent call is a **ticket** — a JSON object recording its type, agent, prompt path, inputs, outputs, dependencies, status, attempt count, timeout, and (after execution) session id, timing, and failure reason. All tickets for a paper live in `<paper-folder>/_artifacts/tickets.json`.

Schema (full version in `templates/emit_tickets.md`):

```json
{
  "id": "discover_codex_m4",
  "type": "discover",
  "agent": "codex",
  "prompt_path": "_artifacts/prompts/discover_codex_m4.md",
  "inputs": ["_paper/paper.md", "_artifacts/json/orient_codex.json"],
  "outputs": ["_artifacts/json/discover_codex_m4.json"],
  "depends_on": ["orient_codex"],
  "status": "pending",
  "attempt": 0,
  "max_attempts": 2,
  "timeout_s": 1200,
  "model": "gpt-5.4-mini"
}
```

Three types of tickets coexist in the same DAG:

| Agent | Executor | When |
|---|---|---|
| `claude` | The orchestrator (Claude Code) executes inline | Orientation by Claude, merge-and-rank, top-third prosecution, synthesis (top-third), final report |
| `codex` | `agent-ctl` launches a `codex exec` subprocess | Discovery (Codex), defense, synthesis (when role-rotated to Codex) |
| `gemini` | `agent-ctl` launches a `gemini` subprocess | Discovery (Gemini), web verification, synthesis, defense (when role-rotated) |

`agent-ctl run-dag` walks the DAG, launches every ticket whose dependencies are met (up to a concurrency cap), waits for any to complete, validates outputs (`outputs[0]` must exist and be non-empty), retries failures up to `max_attempts`, and writes session logs to `_artifacts/sessions/`. It exits when no more ready non-Claude tickets remain.

When `run-dag` exits, Claude Code:
1. Reads the updated `tickets.json`.
2. Validates the wave's outputs (issue counts ≥ thresholds, JSON parse, etc.).
3. Renders curated markdown into the numbered folders.
4. Emits the next wave by writing new tickets and prompts.
5. Calls `run-dag` again.

This loop continues until the `final_report` ticket is `done`.

---

## Wave protocol

Five waves, mapping to the five phases in `SKILL.md`:

| Wave | Phase | Tickets | Concurrency |
|---|---|---|---|
| 1 | Orientation | 3 (one per agent) | 3 in parallel |
| 2 | Discovery | 18 (3 agents × 6 methods, M0 + M2–M6) | 3–6 in parallel |
| 3 | Merge & rank | 1 (Claude inline) | n/a |
| 4 | Verification | 1 (Gemini web search, only if any issue flagged) | 1 |
| 5+ | Debate | 3 per debated issue per round (prosecute → defend → synthesise) | 2–3 issues in parallel |
| Final | Report | 1 (Claude inline) | n/a |

Within an issue's debate, tickets are strictly sequential (defense depends on prosecution, synthesis depends on defense). Across issues, debates run in parallel bounded by the concurrency cap (kept low to avoid rate-limiting the weaker model — typically Gemini).

---

## Model routing

Not every task needs the strongest model. From `SKILL.md`:

| Task | Claude | Codex | Gemini |
|---|---|---|---|
| Orientation | Sonnet | gpt-5.4-mini | gemini-3-flash-preview |
| Discovery (M0–M6) | Sonnet | gpt-5.4-mini | gemini-3-flash-preview |
| Rendering (JSON → markdown) | Haiku | — | — |
| Merge & rank | **Opus** | — | — |
| Prosecution (top third) | **Opus** | — | — |
| Prosecution (rest) | Sonnet | — | — |
| Defense | — | gpt-5.4 | gemini-3.1-pro-preview |
| Synthesis | **Opus** | — | — |
| Verification (web) | — | — | gemini-3.1-pro-preview |
| Final report | **Opus** | — | — |

This concentrates Opus usage on judgment-heavy tickets (merge, top prosecutions, synthesis, final). Roughly 70% of pipeline tokens flow through cheaper Sonnet / Haiku / mini / flash models.

---

## File layout

Every review is a self-contained Obsidian folder. Curated markdown lives at the top level; raw machine artifacts live inside `_artifacts/`.

```
notes/work/referee-reports/<paper-slug>/
├── review.md                       # top-level index, frontmatter phase, status
├── _paper/
│   ├── paper.md                    # OCR'd source
│   └── paper.pdf                   # original
├── 0_orientation/
│   ├── 00_orientation.md           # cross-agent overview
│   ├── claude.md                   # Claude's paper map (rendered from JSON)
│   ├── codex.md
│   └── gemini.md
├── 1_discovery/
│   ├── 00_discovery.md
│   ├── m0_close_reading/{claude,codex,gemini}.md
│   ├── m2_contradictions/...
│   └── m3..m6 likewise
├── 2_ranking/
│   ├── 00_ranking.md
│   ├── issue_register.md           # canonical merged issue list
│   ├── triage.md                   # rejected findings + reasons
│   └── verification.md             # web-fact-check results
├── 3_debates/
│   ├── 00_debates.md
│   ├── 01_<slug>/
│   │   ├── 00_issue.md
│   │   ├── r1_prosecute.md
│   │   ├── r1_defend.md
│   │   ├── r1_synthesize.md
│   │   ├── ... (more rounds if needed)
│   │   └── 99_summary.md
│   └── ...
├── 4_report/
│   └── referee_report.md           # the deliverable
└── _artifacts/
    ├── tickets.json                # the DAG — source of truth
    ├── prompts/<ticket_id>.md      # one prompt per ticket
    ├── json/<ticket_id>.json       # one structured output per ticket
    └── sessions/<ticket_id>.log    # auto-archived agent reasoning trace
```

Two principles:

1. **JSON is the machine format; markdown is the human format.** The JSON in `_artifacts/json/` is the source of truth. Markdown in numbered folders is a projection. If they disagree, JSON wins.
2. **Nothing is ever deleted.** Session logs are auto-archived by `agent-ctl run-dag`. Re-runs append, never overwrite.

---

## Resumability

Because every action writes to disk before the next one starts, a crashed or killed run is always recoverable. To resume:

```
/disputatio /path/to/paper.pdf
```

The skill reads `_artifacts/tickets.json`, sees what's `done`, and picks up at the first non-terminal state. In-flight tickets that died mid-execution (e.g. laptop closed, OAuth expired) get retried up to `max_attempts`.

The skill works idempotently on:
- Paper folder already exists → reuse it.
- `_paper/paper.md` already exists → skip OCR.
- Orientation outputs exist → skip Phase 0.
- Discovery outputs exist for some agents/methods → only re-run the missing ones.

You can interrupt and resume at any phase boundary with no loss of work.

---

## Cross-agent independence

A core design principle: **the three agents must not see each other's reasoning during discovery.**

- Each agent gets only the paper text plus its own paper map (orient_<agent>.json) as inputs. Never another agent's map.
- Claude Code (the orchestrator) does see everything, but its role during discovery is to dispatch tickets, not to share content between agents.
- Cross-agent agreement on an issue during merge gets weighted ×2 in ranking — agreement across architectures is more meaningful than five methods on one model converging (which is correlated by construction).
- Three agents × six methods = 18 nominally-independent passes. In practice some correlation remains (all three are language models trained on similar corpora), but the design intent is to maximise variance.

Role rotation during debate (Claude prosecutes round 1, Codex defends, Gemini synthesises; rotates each round) preserves the same property: every model plays every role across rounds, so no single model gets the last word.

---

## Decision loop

When `/disputatio <path>` is invoked, Claude Code runs a state machine:

```
READ tickets.json
MATCH state → action

no tickets.json                              → INIT (create folders, OCR, emit wave 1)
orient_claude pending                        → execute Claude's orientation inline
orient_codex or orient_gemini pending        → run-dag to launch external orientations
all orient done, no discover tickets         → render orientation, emit wave 2
discover_claude_* pending                    → run Claude discovery inline (or via subagents)
discover_codex_* or discover_gemini_*        → run-dag for external discoveries
all discover done, no merge_rank             → render discovery, execute merge_rank inline
merge_rank done, no verify                   → emit verify ticket (or skip if no flags)
verify done, no debate tickets               → emit wave 5 (round-1 debate tickets)
debate tickets pending                       → execute Claude tickets inline; run-dag for others
                                                after each synthesis: emit next round if "continue"
all debate terminal, no final_report         → execute final_report inline
final_report done                            → EXIT, review complete
```

The loop is purely state-driven: read disk, match state, do one thing, write to disk. No multi-step sequential protocol. This makes resumption trivial — re-invoke and the same state produces the same next action.

---

## What `agent-ctl` is responsible for

- Spawning external CLI subprocesses (`codex exec`, `gemini`).
- Capturing stdout to a session log file.
- Detecting completion (process exit + outputs file present and non-empty).
- Salvaging JSON from stdout when an agent failed to write the declared output file (Gemini specifically — cleaner falls back to extracting the largest fenced ` ```json ... ``` ` block from stdout).
- Cleaning the salvaged JSON (control chars, trailing commas, runaway LaTeX backslashes — see `_clean_json_text`).
- Retrying with backoff on failure.
- Falling back to a more available Gemini model when 429s pile up.

What it is **not** responsible for:

- Deciding what tickets to emit. That's the orchestrator's job.
- Validating semantic content of outputs. Only structural validation (file exists, is non-empty, parses as JSON if expected).
- Rendering markdown. The orchestrator does that between waves.
