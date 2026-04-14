---
name: disputatio
description: Cross-architecture paper review panel for pre-submission authors and first-round referees
---

# Disputatio (v6)

**This file is the authoritative v6 orchestration spec.** When any other file in this repo disagrees with SKILL.md, SKILL.md wins — patch the other file toward SKILL.md. The templates under `templates/` are the authoritative prompts and sub-protocols for each phase; they MUST be consistent with the phase descriptions below. The repo also ships a number of documents (dev logs, architecture notes, roadmap, evaluation methodology) that are descriptive or historical and do NOT define orchestration behaviour.

A cross-architecture review panel designed for the two moments that matter before publication: before an author submits, and before a referee writes the report. The primary deliverable is a **finding panel** — each concern carries an exact quote, cross-architecture support, a contested-point debate trail (only when triggered), a calibration verdict, and a mode-specific priority label. The secondary deliverable is a single-writer prose memo summarizing the panel for the chosen reader (author or referee). Claims that do not survive verification are preserved in the audit trail with drop reasons — the system demonstrates restraint instead of hiding what got killed.

The pipeline is resumable, auditable, and replayable because every agent call is a ticket in a DAG on disk.

## What this is not

- **Not a polished referee letter as primary output.** The panel is primary; the memo is a secondary rendering.
- **Not a majority-vote truth engine.** Cross-family agreement is one signal on a finding, not a verdict. The evidence-backed finding after calibration is the decisive object.
- **Not a benchmark score generator.** Internal calibration is a quality gate, not a leaderboard.

## Usage

```
/disputatio <path-to-paper> [--mode author|referee] [--max-debate-rounds 2] [--skip-web]
```

Options:
- `--mode author` (default) — renders priority labels as `fix_before_submit | watch_in_review | can_ignore` and an optional revision plan.
- `--mode referee` — renders priority labels as `endorse | verify_before_endorsing | skip` and an optional referee-letter draft.
- `--max-debate-rounds R` — maximum rounds per escalated finding (default 2). Debate is escalation-only; most findings never trigger it.
- `--skip-web` — disable web verification (default: enabled).

Same engine, same panel, only the rendering differs between modes.

## Three discovery tracks (v6)

v6 cuts the v4/v5 method-heavy shape (18 tickets) to **nine tickets** organised as three tracks, one family per track, per spec in `docs/v6-upstream-plan.md`. A track is chosen for the candidate signal it produces, not for philosophical lineage.

| Track | What it does | Templates used |
|---|---|---|
| **Holistic** (3 tickets, one per family) | Produces a paper spine, main claims, attack surfaces, and likely referee questions. This is where conceptual-scope concerns surface — the kind of concern a single-shot model catches by reading the paper as one object. | `templates/holistic.md` |
| **Broad critic** (3 tickets, one per family) | Scans for contradictions, scope mismatches, commitment violations, and framing overclaims. This is the workhorse candidate generator. | `templates/methods/m2_contradiction.md`, `m5_immanent.md` |
| **Narrow evidence-judgment** (3 tickets, one per family) | Runs counterexample construction and transformation-based stress tests against specific propositions in the paper spine. Produces deep, evidence-heavy findings on a small number of targets. | `templates/methods/m3_transformation.md`, `m4_counterexample.md`, `m6_disentangling.md` |

Method 0 (mechanical proofreading / close reading), previously a standalone sweep, is now absorbed into the broad critic track. Method 1 (structured disputation) is reserved for escalated debate rounds. Method 7 (iterative refinement) is the synthesis step within debate.

Every candidate concern from any track is forced through a **targeted evidence compiler** that pins the exact quote, location, and whether support is direct or inferred. No finding progresses without verbatim quote support or an explicit `derived_inference` tag.

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

The review proceeds in seven phases (v6 adds a holistic pass up front and re-scopes debate to escalation-only). Each phase corresponds to one or more waves of tickets; see `templates/emit_tickets.md` for the ticket definitions.

### Phase 0 — Orientation (parallel, all agents)

Each of the three agents reads the paper once and produces a neutral **paper map**: claims, equations, propositions, assumptions, parameters, datasets, citations, section anchors, and OCR-corrupted regions. No judgments yet.

Raw outputs land in `_artifacts/json/orient_<agent>.json`; Claude then renders them as markdown into `0_orientation/<agent>.md`. The three maps are not merged — each agent uses its own map as its cache for the subsequent discovery passes. This preserves **model independence**: agents should not be anchored to each other's reading of the paper.

Run all three agents in parallel. Estimated time: ~15-20 minutes wall clock (Codex with `--full-auto` does deep web cross-referencing).

### Phase 1 — Holistic pass (v6, new)

Each of the three agents runs a **holistic conceptual pass** on the paper using its own paper map as the cache. Output per agent:

- **Paper spine** — the argumentative load path from setup to main claim
- **Main claims** — explicit list of what the paper asserts
- **Attack surfaces** — where a serious referee would push back (theory / empirics / identification / framing / robustness / exposition)
- **Likely referee questions** — specific questions a first-round referee would raise
- **Evidence-heavy scrutiny zones** — which sections need close engagement versus which can be scanned

This phase exists because single-shot reviewers have a structural advantage on conceptual-scope concerns when reading the paper as one object. The method-based discovery tracks in Phase 2 under-detect these; the holistic pass closes the gap. The three agents' holistic passes are NOT merged into a single paper map — each agent's pass becomes part of its own reading cache. The orchestrator does build a **canonical attack-surface index** (union across agents, dedup on surface description) that Phase 2 discovery tickets receive as context.

Raw outputs in `_artifacts/json/holistic_<agent>.json`; rendered into `0_holistic/<agent>.md`. Run in parallel. ~10-15 minutes wall clock.

Full spec in `templates/holistic.md`.

### Phase 2 — Discovery (v6: 9 tickets across 3 tracks)

Three tracks per family (holistic / broad critic / narrow evidence-judgment) produce candidate findings. Every candidate is typed by category at write time: `claim_scope_mismatch`, `proof_derivation_flaw`, `identification_empirical_design`, `robustness_missing_check`, `framing_literature_overreach`, or `notation_presentation_local`.

| Track | Tickets | Input | Purpose |
|---|---|---|---|
| Holistic candidate generation | 3 (one per family) | paper map + own holistic pass + canonical attack-surface index | surface conceptual-scope concerns the method tracks under-detect |
| Broad critic | 3 (one per family) | paper map + attack-surface index | scan for contradictions, scope mismatches, commitment violations, framing overclaims; absorbs former M0 close-reading |
| Narrow evidence-judgment | 3 (one per family) | paper map + attack-surface index + priority attack surfaces | counterexample construction, transformation stress tests, causal disentangling — deep, evidence-heavy findings on a small set of targets |

Raw outputs in `_artifacts/json/discover_<agent>_<track>.json`. Rendered into `1_discovery/<track>/<agent>.md`. All nine tickets run in parallel.

**Evidence compiler** (inline, per candidate). Every candidate finding is passed through a compiler that retrieves the verbatim quote, pins the location, records whether support is `direct_quote` or `derived_inference`, and rejects the finding outright if neither is achievable. No concern reaches merge without an evidence object.

**OCR-aware**: discovery prompts warn agents about OCR artifacts and instruct them not to flag corrupted passages as paper errors.

**Web search**: not triggered in this phase. Closed-book discovery.

### Phase 3 — Merge, rank, and verify

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

### Phase 4 — Dialectic debate (v6: escalation-only)

Debate is NOT the default path in v6. Most findings ship directly to calibration (Phase 5) and then into the panel without ever triggering a prosecution round. Debate fires only when **contested-finding escalation** is warranted.

A finding escalates to debate iff ALL of the following hold:

1. **Cross-family disagreement is real** — at least one family flagged the concern with high confidence and at least one family was silent or flagged low-confidence variants that conflict with the main claim.
2. **Evidence exists on both sides** — the evidence compiler found both supporting quotes and countervailing passages; the verdict is not obvious from the evidence object alone.
3. **Severity would change on verdict** — the outcome determines whether the finding is `material`, `local`, or dropped. A finding whose severity is already `nit` does not escalate regardless of disagreement.
4. **The finding would otherwise be user-visible** — no point debating concerns that are already below a priority threshold.

All four conditions. If any is absent, the finding skips debate and proceeds to calibration with its evidence object intact. The v5 status-routing rule (`settled` vs `debate`) is subsumed by this four-way gate in v6.

**Structure when debate does fire.** Prosecute → defend → synthesize, per `templates/prosecute.md` / `defend.md` / `synthesize.md`. Role rotation across rounds:

| Round | Prosecutor | Defender | Synthesizer |
|-------|-----------|----------|-------------|
| 1 | Claude | Codex | Gemini |
| 2 | Codex | Gemini | Claude |

Two rounds maximum by default (`--max-debate-rounds 2`); round 2 fires only if round-1 synthesis verdict is `split` or `escalate` AND the synthesizer explicitly states it cannot resolve without more input. `prosecution_wins` and `defense_wins` verdicts are terminal.

**Verdict vocabulary** (unchanged from v5): `prosecution_wins`, `defense_wins`, `split`, `escalate`. No `converged` option.

**Parallelism**: escalated issues debate in parallel, but within a single issue the path is strictly sequential. Cap concurrent issues at 2–3 to avoid rate-limiting the weakest transport (typically Gemini).

**Expected runtime**: on a typical economics or theory paper, 0–5 findings escalate. Most runs skip debate entirely. That is by design.

### Phase 5 — Pre-publication calibration (v5, carried into v6 with panel-row output)

Before the final report is compiled, every candidate finding that would enter it runs through a **blinded per-finding calibration pass**. This replaces the previous pipeline's post-hoc evaluation as the primary quality loop — post-hoc evaluation survives only as an A/B comparison tool (see Phase 6).

Why this phase exists: the 2026-04-14 v4 run shipped a 56.2% overclaim rate on report-entering findings because strong-consensus "settled" findings skipped the debate stage — which had been doing an unacknowledged polish pass by softening overclaimed raw language into narrower synthesizer `refined_claim` text. Phase 4 restores that polish as a cheap single-model pass, without the theatre cost of full dialectic.

**Inputs.** All panel-row candidates from merge (Step 6 of `templates/merge_and_rank.md`), plus any updates to debated rows from Phase 4 (verdict, `surviving_text`). Findings killed by defense during Phase 4 do not enter calibration — they are written directly to `dropped_findings[]` with the defender's counter-evidence as the drop reason.

**Blinding.** Same blinding protocol as the post-hoc evaluation (randomised `BF###` IDs in a shuffled pool, manifest_blind.json private, no metadata leak in the prompt).

**Rubric.** Same two axes (`quote_verified`, `calibration`) as `templates/evaluate.md`.

**Demote-on-doubt disposition.** Overclaimed and partial-quote findings get one rewrite attempt (polish pass via gemini-3.1-pro-preview against the real passage). If re-annotation still fails the rubric: demote one tier (material → local, local → appendix, appendix → drop) or drop outright if unsupported. The bias is toward a tighter report; edge-case hedging in the annotator's notes counts as a demote trigger.

**Outputs.** `_calibration/final_findings.json` — the calibrated set that feeds the final report (not `ranked_issues_verified.json`). Plus `_calibration/00_calibration.md` scorecard with pre/post overclaim rates.

Default annotator: **codex with `gpt-5.4-mini`**. Fallback: claude-sonnet-4.6 when codex is rate-limited and the paper exceeds haiku's context window. Full spec in `templates/calibrate.md`.

### Phase 6 — Panel + renderers (v6 replaces v5's "Final report")

The v6 primary deliverable is a **finding panel**. Prose memos are secondary renderings driven entirely off the panel rows — no prose stage can introduce new content, only summarize what survived calibration.

1. **`_artifacts/json/panel.json`** — the canonical output. Consumes `_calibration/final_findings.json`. Top-level shape:
   - `paper` — metadata
   - `engine` — version, mode (`author` | `referee`), families list
   - `holistic_pass` — paper spine + main claims + canonical attack-surface index (union of per-family holistic passes)
   - `findings[]` — one row per surviving finding with `concern`, `category`, `severity`, `confidence.band`, mode-specific `priority`, `evidence[]` (each entry: quote, location, why, `support_type`), per-family `architecture_support`, `debate` (triggered, reason, verdict, what_survived, history), `calibration` (verdict, quote_verified, annotator_notes, narrowing_notes, drop_reason), `suggested_action.author.fix` and `suggested_action.referee.how_to_use`, full `audit` trail
   - `dropped_findings[]` — findings killed by defender in debate or by calibration, with reason surfaced (not hidden)
   - `summary.counts`, `summary.top_priorities`, `summary.author_memo`, `summary.referee_memo`

2. **`4_panel/panel.md`** — panel rendered as a table, one row per finding, columns = concern / severity / confidence / priority (mode-specific) / evidence snippet / verdict history (compressed). The primary UI that a reader opens first.

3. **`4_panel/author_memo.md` OR `4_panel/referee_memo.md`** (depending on `--mode`) — a **single-writer prose memo** produced by a long-context model reading the entire `panel.json` in one pass. The writer can summarise rows but cannot invent findings or change a row's `calibration.verdict`. For `--mode author`, the memo prioritises fixes before submission; for `--mode referee`, it scaffolds a first-draft referee letter the human referee will edit.

4. **`4_panel/revision_plan.md`** (optional, `--mode author`) or **`4_panel/referee_letter_draft.md`** (optional, `--mode referee`) — auxiliary renderings generated from the same panel. These are secondary; the panel is primary.

Claude also updates `review.md` at the top of the paper folder to set `phase: complete`, `mode`, and populate the summary section.

Writer model: **gemini-3.1-pro-preview** for prose (strong at long-form), or **claude-opus** when the panel has >30 findings and Gemini's context is a concern. Full spec in `templates/render_panel.md`.

### Phase 7 — Post-hoc evaluation (A/B only)

Still available, but no longer the pipeline's calibration loop. Use this when you want to compare disputatio v5 against another review (disputatio v3, coarse.ink, Stanford Agentic Reviewer) on the same paper. Same blinded rubric, same `BF###` manifest shape, but now the pool can contain findings from multiple review versions simultaneously.

Typical use: cross-version comparison. Expected result when running post-hoc eval on a v5 report: very low overclaim rate, because Phase 4 already dropped/demoted what post-hoc would have flagged. A large gap between Phase 4 and Phase 6 overclaim rates is a bug in one of them.

See `templates/evaluation.md` for the post-hoc protocol and `templates/evaluate.md` for the per-finding prompt body (shared with Phase 4 calibration).

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
│   ├── issue_register.md                 # human-readable merge + panel-row candidates
│   ├── panel_rows_candidates.json        # canonical handoff to verify → debate → calibrate
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
│   └── referee_report.md                 # the deliverable (gemini-polished v5)
│
├── _calibration/                         # Phase 4 pre-publication calibration (v5)
│   ├── 00_calibration.md                 # scorecard: pre/post overclaim rate, kept/demoted/dropped
│   ├── final_findings.json               # calibrated set — the ONLY input to the final report
│   ├── dropped.json                      # findings killed by calibration (with reasons)
│   ├── demoted.json                      # findings demoted (old_tier → new_tier)
│   ├── manifest_blind.json               # blind_id → true_id (private to the orchestrator)
│   ├── tickets.json                      # calibration sub-DAG
│   ├── prompts/<blind_id>.md             # self-contained prompt per finding
│   ├── annotations/<blind_id>.json       # first-pass annotator output
│   ├── rewrites/<blind_id>.json          # polish-pass output (if the first annotation failed)
│   └── sessions/<blind_id>.log           # raw session capture
│
├── _evaluation/                          # Phase 6 A/B post-hoc evaluation (optional)
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
│ no debate tickets exist             │ Apply four-way escalation gate (Phase 4) to each    │
│                                     │ panel-row candidate. For each finding that clears   │
│                                     │ ALL four conditions, emit round 1 prosecute/defend/  │
│                                     │ synthesize triple. If zero findings clear the gate,  │
│                                     │ skip the debate phase. Write prompts.                │
├─────────────────────────────────────┼──────────────────────────────────────────────────────┤
│ debate tickets pending/running      │ For Claude-typed debate tickets: execute inline.      │
│                                     │ For external: $A run-dag --concurrent 2              │
│                                     │ After each synthesis: read output, check status.     │
│                                     │ If continue + budget remains → emit next round.      │
│                                     │ If converged/none → mark issue terminal.             │
│                                     │ Render debate markdown in 3_debates/.               │
├─────────────────────────────────────┼──────────────────────────────────────────────────────┤
│ all debate tickets terminal,        │ PHASE 4 CALIBRATION (v5): collect every candidate    │
│ no _calibration/tickets.json        │ report-entering finding (all settled + debate        │
│                                     │ survivors with prosecution_wins/split/escalate).     │
│                                     │ Shuffle, assign BF### IDs, write manifest_blind.json.│
│                                     │ Build one self-contained prompt per finding at       │
│                                     │ _calibration/prompts/<blind_id>.md. Emit calibrate   │
│                                     │ tickets to codex/gpt-5.4-mini (fallback: sonnet).    │
├─────────────────────────────────────┼──────────────────────────────────────────────────────┤
│ _calibration/tickets.json exists,   │ $A run-dag _calibration/tickets.json --concurrent 4. │
│ calibrate tickets pending/running   │ Validate each annotation has two-axis verdict.       │
├─────────────────────────────────────┼──────────────────────────────────────────────────────┤
│ all calibrate tickets done,         │ Apply demote-on-doubt disposition rules inline. For  │
│ no _calibration/final_findings.json │ partial or overclaimed findings, emit one polish     │
│                                     │ ticket to gemini-3.1-pro-preview, re-annotate. If    │
│                                     │ still fails: drop or demote one tier. Write          │
│                                     │ _calibration/final_findings.json, dropped.json,      │
│                                     │ demoted.json, 00_calibration.md scorecard.           │
├─────────────────────────────────────┼──────────────────────────────────────────────────────┤
│ _calibration/final_findings.json    │ Execute final_report inline CONSUMING                │
│ exists, no final_report ticket      │ _calibration/final_findings.json (not                │
│                                     │ ranked_issues_verified.json). Write final.json +     │
│                                     │ referee_report.md. Phase 5.5: for each report entry, │
│                                     │ call gemini-3.1-pro-preview to rewrite                │
│                                     │ surviving_text into referee-letter prose. Update     │
│                                     │ review.md to phase: complete.                         │
├─────────────────────────────────────┼──────────────────────────────────────────────────────┤
│ final_report = done,                │ PHASE 6 A/B (optional): collect findings from this   │
│ A/B comparison requested            │ run plus other review versions (v3/coarse/etc),      │
│ (no _evaluation/tickets.json)       │ shuffle into one pool, same blinding rubric, emit    │
│                                     │ evaluate tickets. Not auto-run — only when the user  │
│                                     │ requests cross-version comparison.                   │
├─────────────────────────────────────┼──────────────────────────────────────────────────────┤
│ _evaluation/tickets.json exists,    │ $A run-dag _evaluation/tickets.json --concurrent 4.  │
│ eval tickets pending/running        │ Wait for completion. Aggregate → results.json +      │
│                                     │ 00_evaluation.md (same rubric as Phase 4 calibrate).  │
├─────────────────────────────────────┼──────────────────────────────────────────────────────┤
│ _calibration/final_findings exists  │ EXIT. Review complete and calibrated.                │
│ AND report written (or _evaluation  │                                                      │
│ /results.json if A/B ran)           │                                                      │
└─────────────────────────────────────┴──────────────────────────────────────────────────────┘
```

### INIT procedure

When no `tickets.json` exists, the orchestrator runs **preflight first**, then workspace creation, then ticket emission. Failing fast at preflight time avoids burning 60–90 minutes on avoidable setup failures (expired OAuth, missing CLI, broken template) discovered only at phase N.

#### Step 0 — Preflight (fail-fast checks before any work)

Before creating the workspace or calling any agent, verify the environment is ready. Run every check; if any fails, **abort with a clear message stating what failed and how to fix it**. Do NOT create the paper folder until preflight passes — a failed preflight should leave zero new artifacts on disk.

Checks, in order:

1. **Agent authentication.** For every transport that will be used in Wave 1 (by default: `codex`, `gemini`; `claude` is inline and needs no check), launch a minimal ping session through `agent-ctl`:

   ```
   agent-ctl start codex  "Reply with the single word: pong" --timeout 60
   agent-ctl start gemini "Reply with the single word: pong" --timeout 60
   agent-ctl wait <codex-sid> <gemini-sid>
   agent-ctl result <codex-sid>  # must contain 'pong'
   agent-ctl result <gemini-sid> # must contain 'pong'
   ```

   Any non-zero exit, timeout, or missing `pong` → auth is broken. Typical fixes: `codex logout && codex login` for Codex; re-run `gemini` interactively once for Gemini OAuth. After the user re-authenticates, re-invoke `/disputatio` from scratch.

   If the planned team includes non-default transports (opencode, ollama), add their ping to this list. Ollama: use one of the pulled models from `ollama list` and a short prompt.

2. **Template placeholder sanity.** Every template that will be substituted at emit time must have all its `{{placeholder}}` tokens enumerated in the "Prompt generation" section below. Quick scan:

   ```
   grep -l '{{' templates/*.md templates/methods/*.md templates/agents/*.md templates/conventions/*.md
   ```

   For each file that contains `{{...}}` tokens, confirm every token appears in the "Prompt generation" substitution table. An unknown token means the template was edited without updating the generator — abort with the file path and the offending token.

3. **Vault write probe.** Before creating `$PAPER/`, verify the Obsidian vault root is writable:

   ```
   touch ~/Library/Mobile\ Documents/iCloud~md~obsidian/Documents/notes/work/referee-reports/.disputatio-preflight && rm ~/Library/Mobile\ Documents/iCloud~md~obsidian/Documents/notes/work/referee-reports/.disputatio-preflight
   ```

   A permission error or a stale iCloud lock surfaces here instead of at ticket-launch time. If it fails, tell the user to open Obsidian once (to sync) or check iCloud Drive status.

4. **OCR backend probe** (only when input is `.pdf`). Verify `socr` is available:

   ```
   which socr && socr --version
   ```

   If missing, tell the user to install smart-ocr before restarting. Skipping the OCR check for `.md` inputs is fine — the copy is straightforward.

5. **Agent-ctl state-file lock probe.** The launcher's state file (`~/.claude/agent-sessions.json`) uses `fcntl` locking; a stale lock from a crashed prior invocation can block launches. The ping checks above implicitly exercise this, so no extra step is needed — but if every ping times out at exactly 60 s, suspect a stale lock and suggest `agent-ctl cleanup`.

Preflight typically takes 30–60 seconds wall-clock (dominated by the two ping calls). If all checks pass, proceed to Step 1.

#### Step 1..8 — Workspace creation and wave-1 emission

1. Determine `<paper-slug>` from the input filename (lowercase, hyphens, no extension)
2. Set `$PAPER = ~/Library/Mobile Documents/iCloud~md~obsidian/Documents/notes/work/referee-reports/<paper-slug>/`
3. Create directory structure: `mkdir -p $PAPER/{_paper,0_orientation,1_discovery/{m0_close_reading,m2_contradictions,m3_transformations,m4_counterexample,m5_immanent,m6_disentangling},2_ranking,3_debates,4_report,_artifacts/{prompts,json,sessions},_calibration/{prompts,annotations,rewrites,sessions},_evaluation/{prompts,annotations,sessions}}`
4. If input is `.pdf`: run `socr <input> --save-figures` → copy result to `$PAPER/_paper/paper.md` and the figures tree to `$PAPER/_paper/figures/`. **Do NOT substitute `pdftotext` or any other extractor, ever, even if the PDF looks typeset.** If input is `.md`: copy directly.
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

**Budget tiering — removed in v2.** Pre-tiered round allocation by rank position was found (in the 2026-04-13 v3 run) to spend rounds on issues already destined to converge, while denying rounds to issues that genuinely needed them. Replaced with verdict-driven escalation: every issue gets round 1; rounds 2-3 are funded only when the synthesizer's verdict is `split` or `escalate`. The `--max-rounds` flag remains as a hard cap.

**Timeout guidance**: Codex with `--full-auto` can perform web searches mid-session. When it does, it often cross-references the published version of the paper to verify OCR content. This is valuable but takes time. A 10-minute budget is too tight; 20 minutes is the minimum for orientation. Short timeouts kill the agent mid-file-write, losing all work.

### Model routing

Not every task needs the strongest model. Use cheaper/faster models for mechanical work, reserve expensive models for judgment calls. When emitting tickets, set the `model` field per this table:

| Task | Claude | Codex | Gemini |
|------|--------|-------|--------|
| Orientation | sonnet | gpt-5.4-mini | gemini-3-flash-preview |
| Discovery (M0-M6) | sonnet | gpt-5.4-mini | gemini-3-flash-preview |
| Rendering (JSON→md) | haiku | — | — |
| Merge & Rank | **opus** | — | — |
| Coarse-style baseline (Tier 2) | **opus** | — | — |
| Prosecution (top third) | **opus** | — | — |
| Prosecution (rest) | sonnet | — | — |
| Defense | — | gpt-5.4 | gemini-3.1-pro-preview |
| Synthesis | **opus** | — | — |
| Verification (web) | — | — | gemini-3.1-pro-preview |
| **Phase 4 calibration annotator** | sonnet (fallback only) | **gpt-5.4-mini** | gemini-3-flash-preview (fallback) |
| **Phase 5.5 editorial polish** | — | — | **gemini-3.1-pro-preview** |
| Final report compilation | **opus** | — | — |

This cuts Opus usage to ~30% of the pipeline (merge, baseline, top prosecutions, synthesis, final-report compilation). The remaining 70% runs on Sonnet/Haiku/mini models at a fraction of the cost. Gemini owns both the verification web-search role and the editorial polish role (single long-context, fluid-prose model handling all human-facing writing). The Phase 4 calibration annotator defaults to codex/gpt-5.4-mini to match the 2026-04-12 manual baseline; sonnet takes over when codex is rate-limited on long-context papers (haiku cannot — it lacks the long-context beta for >50K token prompts).

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

## Explicit rules (v6)

Three orchestration decisions were previously left to orchestrator improvisation. They are now specified here to eliminate runtime ambiguity.

### Four-way escalation gate (Phase 4 entry)

A finding enters debate iff ALL four conditions hold, evaluated at the start of Phase 4 over every candidate panel row from merge:

1. **Cross-family disagreement is real.** Operationally: at least one family's discovery ticket flagged the concern with `confidence: high`, AND at least one other family either (a) did not surface the concern at all, or (b) surfaced a variant with `confidence: medium` or `low` whose claim conflicts with the high-confidence version. Encoded in `merge.debate_hint.cross_family_disagreement`: `strong` (condition met), `moderate` (one family flagged high, others silent without conflicting variant — does NOT satisfy the condition by itself), `none` (all families agree or all ignore).
2. **Evidence exists on both sides.** Operationally: the paper's text supports BOTH the finding's claim AND a plausible counter-claim. Encoded in `merge.debate_hint.evidence_conflict_in_paper`: `yes` if the paper contains passages that could be cited by either side; `no` if the paper's text uniformly supports one side. The evidence compiler's `support_type` tags inform this.
3. **Severity would change on verdict.** Operationally: if the finding's severity is `nit`, the condition is FALSE regardless. If severity is `local` or `material`, ask whether a `defense_wins` verdict would drop the finding entirely vs narrow it. Drops qualify; narrowings do not (since calibration can narrow without debate). Encoded in `merge.debate_hint.severity_sensitive`.
4. **Finding would otherwise be user-visible.** Operationally: after calibration, would this finding appear in the panel's `material`, `local`, or `settled` section? If calibration will drop it as `unsupported` anyway, debate is wasted compute. This condition is evaluated AFTER calibration runs on the candidate — which means in practice Phase 4 fires AFTER Phase 5's first pass, not before. See flow below.

**Revised v6 flow**: merge (Phase 3) → calibration first pass on all candidates (Phase 5a) → four-way gate applied to calibration survivors (Phase 4 trigger evaluation) → debate fires on gate-clearers (Phase 4) → calibration second pass on debate survivors to capture `surviving_text` (Phase 5b) → panel render (Phase 6). Templates keep their current names; the phases are conceptually interleaved.

If zero findings clear the gate, debate is skipped. That is the correct outcome on consensus-heavy papers.

### Category fallback

The v6 category vocabulary is fixed:
`proof | empirics | identification | framing | robustness | interpretation | notation | other`.

Discovery agents assign a category at write time. The evidence compiler rejects candidates with categories outside this set. If an agent cannot place a finding in one of the first seven categories with a concrete justification, it uses `other` and explains in `evidence.why`. Orchestrator behaviour:

- If `other` rate > 10% of a single discovery ticket's output, log a warning in the session log; the category schema may need revision. The run continues with `other`-tagged findings carried through to calibration.
- Panel-row transformation (merge Step 6) preserves the agent-assigned category unchanged. No post-hoc re-categorisation.
- Downstream category-level analytics (release-gate metrics, coverage-by-category in evaluation) treat `other` as a separate bucket — never collapsed into one of the first seven.

### Mode propagation

The `--mode` flag (`author` or `referee`) is set at `/disputatio` invocation and flows through the pipeline as a single field in the engine metadata:

- Written to `_artifacts/tickets.json` root: `"engine": {"version": "v6", "mode": "author" | "referee"}`.
- Passed to every render ticket via prompt substitution `{{mode}}`.
- Determines priority label vocabulary on every panel row:
  - `mode: author` → `priority.author` populated with `fix_before_submit | watch_in_review | can_ignore`; `priority.referee` null.
  - `mode: referee` → `priority.referee` populated with `endorse | verify_before_endorsing | skip`; `priority.author` null.
- Determines memo file name in Phase 6: `4_panel/author_memo.md` OR `4_panel/referee_memo.md` (mutually exclusive — one run produces one mode's memo).
- Determines optional auxiliary rendering: `revision_plan.md` (author) OR `referee_letter_draft.md` (referee).

Same engine, same 9 discovery tickets, same calibration. The mode affects only rendering. Switching modes on a finished run is cheap: re-run Phase 6 with the other mode flag; calibration does not need to re-run.

Dual-mode output (both memos from one run) is supported by a `--mode both` flag that fires two Phase 6 render tickets sequentially against the same `panel.json`. Use sparingly; the writer call is cheap but the memos are quite different in voice.
