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
  "id": "discover_codex_narrow_evidence",
  "type": "discover",
  "agent": "codex",
  "family": "openai",
  "model": "gpt-5.4",
  "prompt_path": "_artifacts/prompts/discover_codex_narrow_evidence.md",
  "inputs": [
    "_paper/paper.md",
    "_artifacts/json/orient_codex.json",
    "_artifacts/json/holistic_codex.json",
    "_artifacts/json/attack_surface_index.json"
  ],
  "outputs": ["_artifacts/json/discover_codex_narrow_evidence.json"],
  "depends_on": ["holistic_codex"],
  "status": "pending",
  "attempt": 0,
  "max_attempts": 2,
  "timeout_s": 1800
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
2. Validates the wave's outputs (verbatim quote substring-match, JSON parse, schema check, etc.).
3. Renders curated markdown into the numbered folders.
4. Emits the next wave by writing new tickets and prompts.
5. Calls `run-dag` again.

This loop continues until the `panel_render` ticket is `done`.

---

## Wave protocol

Eight phases, mapping to the structure in `SKILL.md`. Within a wave the listed tickets run in parallel (bounded by the `--concurrent` cap); across waves the order is strict because each wave depends on the previous one's outputs.

| Wave | Phase | Tickets | Concurrency |
|---|---|---|---|
| 1 | **Phase 0 — Orientation** | 3 (one per family) → independent paper maps | 3 in parallel |
| 1.5 | **Phase 1 — Holistic pass** | 3 (one per family) → attack-surface lists, unioned into canonical index | 3 in parallel |
| 1.75 | **Phase 1.75 — Lit engagement** | 3 internal passes (A1 archetype questions → A2 codex ref-finder → A3 Claude+/chrome Scholar) | sequential |
| 2 | **Phase 2 — Discovery** | 9 = 3 families × 3 tracks (`holistic_candidates`, `broad_critic`, `narrow_evidence`) | 3 in parallel |
| 2.5 | **Phase 2.5 — Baseline sentinel** | 1 (single-shot opus, coverage check, runs in parallel with Wave 2) | n/a |
| 3 | **Phase 3 — Merge + rank** | 1 (Claude inline) → atomic clustering, quote validation, panel-row emission | n/a |
| 4 | **Phase 5a — Calibration pass 1** | 1 blinded ticket per candidate row, plus polish-rewrite + re-annotation on any flagged row | 4 in parallel |
| 4.5 | **Phase 4 — Two-route gate + debate** | 0 to ~10 debated rows; Route A = 3 tickets (prosecute → defend → synthesize); Route B = 2 tickets (defend → synthesize, no prosecutor) | 2–3 issues in parallel |
| 5 | **Phase 5b — Calibration pass 2** | 1 ticket per debate survivor, polish/re-annotate if flagged | 4 in parallel |
| 6 | **Phase 6 — Panel compile + render** | inline panel.json compile + 1 long-context render ticket per mode (referee, author, or both) | n/a |

Within an issue's debate, tickets are strictly sequential (Route A: defense depends on prosecution; synthesis depends on defense. Route B: synthesis depends on defense). Across issues, debates run in parallel bounded by the concurrency cap (typically 2–3, kept low to avoid rate-limiting Gemini).

Phase 4 fires only on rows that clear the two-route escalation gate: **Route A** triggers on cross-family disagreement with evidence on both sides plus severity sensitivity; **Route B** triggers when all three families flagged a material concern, in which case the defender runs as a red-team challenger against the consensus rather than as the paper's advocate. Most papers see 0–5 debates; many see none.

---

## Model routing

Not every task needs the strongest model. From `SKILL.md`:

| Task | Claude | Codex | Gemini |
|---|---|---|---|
| Orientation | Sonnet | gpt-5.4-mini | gemini-3-flash-preview |
| Holistic pass | **Opus** | gpt-5.4 (high effort) | gemini-3.1-pro-preview |
| Lit engagement A1 (archetype generator) | — | — | gemini-3.1-pro-preview |
| Lit engagement A2 (ref finder) | — | gpt-5.4 (medium effort) | — |
| Lit engagement A3 (Scholar fill-in) | **Opus** (with `/chrome` MCP) | — | — |
| Discovery — `holistic_candidates` | Sonnet | gpt-5.4-mini | gemini-3-flash-preview |
| Discovery — `broad_critic` | Sonnet | gpt-5.4 (medium effort) | gemini-3.1-pro-preview |
| Discovery — `narrow_evidence` | Sonnet | gpt-5.4 (medium effort) | gemini-3.1-pro-preview |
| Baseline sentinel | **Opus** | — | — |
| Merge & rank | **Opus** | — | — |
| Calibration pass 1 (annotator) | — | gpt-5.4-mini | — |
| Calibration polish-rewrite | — | — | gemini-3.1-pro-preview |
| Calibration re-annotation (upgraded) | — | gpt-5.4 (medium effort) | — |
| Defense (Route A or Route B red-team) | — | gpt-5.4 | gemini-3.1-pro-preview (rotating) |
| Synthesis | — | — | gemini-3.1-pro-preview |
| Verification (web) | — | — | gemini-3.1-pro-preview |
| Panel render | **Opus** | — | gemini-3.1-pro-preview (fallback) |

Heavy reasoning is concentrated on merge, synthesis, render, and baseline. Discovery splits effort by track: the conceptual `holistic_candidates` track uses cheaper models since the holistic pass already did the heavy framing work; the evidence-heavy tracks use full Codex / Gemini Pro.

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
│   ├── 00_orientation.md           # cross-family overview + per-family count table
│   ├── claude.md                   # Claude's paper map (rendered from JSON)
│   ├── codex.md
│   └── gemini.md
├── 0_holistic/
│   ├── 00_holistic.md
│   ├── claude.md                   # Claude's holistic pass (paper spine, attack surfaces, referee questions)
│   ├── codex.md
│   ├── gemini.md
│   └── attack_surface_index.md     # canonical union across families
├── 1_discovery/
│   ├── 00_discovery.md
│   ├── holistic_candidates/{claude,codex,gemini}.md
│   ├── broad_critic/{claude,codex,gemini}.md
│   └── narrow_evidence/{claude,codex,gemini}.md
├── 2_ranking/
│   ├── 00_ranking.md
│   ├── issue_register.md           # canonical panel-row register (atomic, ranked)
│   ├── triage.md                   # findings dropped at merge + reasons
│   ├── verification.md             # web-fact-check results (or no-op note)
│   └── baseline_diff.md            # coverage diff vs the Wave 2.5 sentinel
├── 3_debates/
│   ├── 00_debates.md
│   ├── <finding_id>/               # one folder per escalated row
│   │   ├── 00_issue.md             # the claim_under_challenge or prosecution target
│   │   ├── r1_defend.md            # defender's output (Route A or Route B red-team)
│   │   ├── r1_synthesize.md        # synthesizer's verdict
│   │   └── 99_summary.md           # disposition (shipped to panel / dropped)
│   └── ...                         # (r1_prosecute.md additionally for Route A rows)
├── 4_panel/
│   ├── panel_referee.md            # panel table view (referee priority labels)
│   ├── panel_author.md             # panel table view (author priority labels)
│   ├── referee_memo.md             # prose memo, referee voice
│   ├── author_memo.md              # prose memo, author voice
│   ├── referee_letter_draft.md     # first-draft referee letter (referee mode aux)
│   └── revision_plan.md            # sentence-level edit table (author mode aux)
├── _calibration/
│   ├── 00_calibration.md           # scorecard
│   ├── manifest_blind.json         # blind_id ↔ true_id map (PRIVATE)
│   ├── prompts/<BF_id>.md          # one prompt per calibrated row
│   ├── annotations/<BF_id>.json    # annotator outputs (pass 1, pass 2, reann)
│   ├── rewrites/<BF_id>.json       # polish-rewrite outputs
│   ├── final_findings.json         # calibrated set fed to panel compile
│   └── dropped_pass1.json          # findings killed at calibration with reasons
└── _artifacts/
    ├── tickets.json                # the DAG — source of truth
    ├── engine.json                 # run-level metadata (mode, families, opsec policy)
    ├── prompts/<ticket_id>.md      # one prompt per ticket
    ├── json/<ticket_id>.json       # one structured output per ticket (incl. panel.json)
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
- Holistic outputs exist → skip Phase 1.
- Discovery outputs exist for some family/track combinations → only re-run the missing ones.

You can interrupt and resume at any phase boundary with no loss of work.

---

## Cross-agent independence

A core design principle: **the three families must not see each other's reasoning during orientation, holistic, and discovery.**

- Each family gets only the paper text plus its own paper map (`orient_<family>.json`) and its own holistic pass (`holistic_<family>.json`) as inputs. Never another family's outputs.
- The canonical attack-surface index is a structural union of the three families' holistic outputs (built by the orchestrator inline). Discovery tickets see this union as shared context, but the union is a deduplication of independently-produced lists — it does not introduce cross-family contamination of the per-family reasoning artifacts.
- Cross-family agreement on a finding during merge gets weighted ×2 in ranking — agreement across architectures is more meaningful than three tracks on one family converging (which is correlated by construction).
- Three families × three tracks = 9 nominally-independent discovery passes. Some correlation remains (all three are LLMs trained on overlapping corpora), but the design intent is to maximise variance.

Role rotation during Route A debate (Claude prosecutes round 1, Codex defends, Gemini synthesises; rotates each round) preserves the same property: every model plays every role across rounds, so no single model gets the last word. Route B is one-shot by construction: Codex defends as red-team challenger, Gemini synthesises — no rotation, no round 2.

---

## Decision loop

When `/disputatio <path>` is invoked, Claude Code runs a state machine:

```
READ tickets.json
MATCH state → action

no tickets.json                              → INIT (create folders, OCR, emit Wave 1)
orient_* pending                             → Claude executes its own ticket inline as
                                                a subagent; run-dag launches codex/gemini
all orient done, no holistic tickets         → render 0_orientation, emit Wave 1.5
holistic_* pending                           → dispatch as Wave 1
all holistic done                            → render 0_holistic, union into the canonical
                                                attack_surface_index, emit Wave 1.75
literature_engagement_* pending              → run A1 (gemini) → A2 (codex) → A3 (Claude
                                                + /chrome MCP); orchestrator synthesises
literature_engagement complete                → emit Wave 2 (9 discovery + 1 baseline)
discover_* / baseline_review pending         → Claude tickets inline; run-dag for the rest
all discovery done, no merge_rank            → render 1_discovery, execute merge_rank inline
merge_rank done                              → render 2_ranking; emit calibration Pass 1
calibration Pass 1 done                      → apply two-route gate; emit debate tickets
                                                for gate-clearers (0 to ~10); rest go direct
                                                to panel
debate tickets pending                       → run-dag (defend → synthesize per row);
                                                Route B is one-shot, Route A may iterate to
                                                round 2 if synthesis returns "split"/"escalate"
all debate terminal                          → render 3_debates, emit calibration Pass 2
                                                on debate survivors
calibration Pass 2 done                      → compile panel.json inline, emit panel_render
panel_render done                            → 4_panel/ written, review marked complete
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
