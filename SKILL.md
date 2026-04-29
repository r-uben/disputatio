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

v6 cuts the v4/v5 method-heavy shape (18 tickets) to **nine tickets** organised as three tracks, one family per track, per spec in `docs/log/2026-04-14_upstream-pivot-plan.md`. A track is chosen for the candidate signal it produces, not for philosophical lineage.

| Track | What it does | Templates used |
|---|---|---|
| **Conceptual candidates** (3 tickets, one per family) — on-disk track key `holistic_candidates` | Generates candidate findings *from* each family's holistic pass (Phase 1). Surfaces conceptual-scope concerns — the kind of concern a single-shot model catches by reading the paper as one object. Note: this is the discovery *track*, not the Phase 1 holistic *pass*; the pass produces the paper spine, the track produces candidate findings against it. | `templates/discover_holistic.md` |
| **Broad critic** (3 tickets, one per family) | Scans for contradictions, scope mismatches, commitment violations, and framing overclaims. This is the workhorse candidate generator. | `templates/methods/m2_contradiction.md`, `m5_immanent.md` |
| **Narrow evidence-judgment** (3 tickets, one per family) | Runs counterexample construction, transformation-based stress tests, and step-by-step algebraic derivation traces against specific propositions in the paper spine. Produces deep, evidence-heavy findings on a small number of targets. M8 (derivation trace) is mandatory on every selected theory/proof surface — it closes the algebra-checking gap surfaced in the 2026-04-15 A/B vs coarse.ink. | `templates/methods/m3_transformation.md`, `m4_counterexample.md`, `m6_disentangling.md`, `m8_derivation.md` |

Method 0 (mechanical proofreading / close reading), previously a standalone sweep, is now absorbed into the broad critic track. Method 1 (structured disputation) is reserved for escalated debate rounds. Method 7 (iterative refinement) is the synthesis step within debate.

Every candidate concern from any track is forced through a **targeted evidence compiler** that pins the exact quote, location, and whether support is direct or inferred. No finding progresses without verbatim quote support or an explicit `derived_inference` tag.

## Ticket DAG orchestration

Every agent call is a ticket on disk. Tickets live in `<paper-folder>/_artifacts/tickets.json` inside the Obsidian vault. The ticket schema, the wave protocol (how tickets are emitted), and the ID naming conventions are defined in `templates/emit_tickets.md`. Read that file before implementing any step of the protocol.

**Execution model**:
- Claude generates tickets in **waves**. Each wave depends on the outputs of the previous wave.
- `agent-ctl run-dag <paper-folder>/_artifacts/tickets.json --concurrent 3` executes all ready tickets in parallel up to the concurrency cap, then exits when no more ready tickets remain.
- Claude-typed tickets (`orient_claude`, `holistic_claude`, `discover_claude_*`, `baseline_review`, `merge_rank`, and wave-emission logic) are executed by Claude directly, not by agent-ctl.
- After `run-dag` exits, Claude inspects the outputs, renders them as curated markdown into the numbered folders, generates the next wave of tickets, and calls `run-dag` again.

**Automatic session archiving**: `agent-ctl run-dag` copies the session log (raw agent reasoning trace) into `<tickets_parent>/sessions/<ticket_id>.log` when a ticket finishes — both on success and on failure. The archive location is derived from the tickets.json parent directory, so for disputatio it lands in `<paper-folder>/_artifacts/sessions/`. Nothing is deleted; every reasoning trace is preserved forever.

**Key benefit — full provenance**: every agent call is replayable. The ticket stores the prompt path, inputs, outputs, timing, attempt count, and session ID. Combined with the stored prompt files, output files, and archived session logs, the entire review is replayable and auditable.

**Monitoring**: `agent-ctl dag-status <paper-folder>/_artifacts/tickets.json` prints a summary of ticket states at any time.

**Resumability**: the ticket DAG is the source of truth. Closing Claude Code, restarting later, and re-running the skill picks up from where it left off — ready tickets resume, already-done tickets are skipped.

## Protocol

The review proceeds in **eight phases (Phase 0 through Phase 7)**. Phase 7 is optional (post-hoc A/B evaluation); the default run executes Phases 0–6. v6 adds a holistic pass up front (Phase 1) and re-scopes debate (Phase 4) to escalation-only. Each phase corresponds to one or more waves of tickets; see `templates/emit_tickets.md` for the ticket definitions.

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

Three tracks per family (holistic / broad critic / narrow evidence-judgment) produce candidate findings. Every candidate is typed by category at write time. **Canonical category vocabulary** (single source of truth, used by discovery, merge, calibration, and the panel schema):

`proof | empirics | identification | framing | robustness | interpretation | notation | other`

See **Category fallback** below for the `other` rule. Earlier draft labels (`claim_scope_mismatch`, `proof_derivation_flaw`, etc.) are deprecated — discovery agents must emit one of the eight canonical labels.

| Track | Tickets | Input | Purpose |
|---|---|---|---|
| Conceptual candidates (track key `holistic_candidates`) | 3 (one per family) | paper map + own holistic pass + canonical attack-surface index | surface conceptual-scope concerns the method tracks under-detect |
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
4. **Panel-row emission**: every surviving merged issue becomes a panel-row candidate written to `panel_rows_candidates.json`. There is no top-N cut at merge — the rank score is metadata used by calibration ordering and (for `cross_agent_support`) by the consensus-route gate. Whether a finding ships, drops, or escalates to debate is decided downstream by calibration Pass 1 and the two-route gate, not by a budget cut here.
5. **Web verification (Wave 4)**: Gemini fetches external evidence for rows whose row-level `needs_web_verification: true`. Verify writes `web_verification = {status: confirmed | refuted | inconclusive, impact_on_row: strengthen | weaken | unchanged, ...}` onto the row and emits `panel_rows_candidates_verified.json`. Verify does NOT alter `rank_score` and does NOT drop rows in v6 — it produces evidence that calibration Pass 1 reads (a `refuted` row biases the annotator toward `unsupported`, but the verdict is the annotator's). The v5 +2/−3 score-modification + budget-cut logic has been removed. See `templates/verify.md`.

**Ranking priority**: cross-agent support is weighted double because it is the strongest signal. Five methods on one model are correlated; agreement across different architectures is much more meaningful.

### Phase 4 — Dialectic debate (v6: escalation-only)

Debate is NOT the default path in v6. Most findings ship directly to calibration (Phase 5) and then into the panel without ever triggering a prosecution round. Debate fires only when **contested-finding escalation** is warranted.

A finding escalates to debate via one of two routes.

**Route A — Disagreement.** Escalate iff ALL four conditions hold:

1. **Cross-family disagreement is real** — at least one family flagged the concern with high confidence and at least one family was silent or flagged low-confidence variants that conflict with the main claim.
2. **Evidence exists on both sides** — the evidence compiler found both supporting quotes and countervailing passages; the verdict is not obvious from the evidence object alone.
3. **Severity would change on verdict** — the outcome determines whether the finding is `material`, `local`, or dropped. A finding whose severity is already `nit` does not escalate regardless of disagreement.
4. **The finding would otherwise be user-visible** — derived rule, not a stored field: `calibration_pass1.verdict in {supported, calibrated_narrowed}` AND `severity in {material, local}`.

Route A fires the standard prosecute → defend → synthesize debate structure.

**Route B — Consensus override (added 2026-04-16).** Escalate iff `debate_hint.high_severity_consensus == true` AND Condition 4 above holds. Trigger: `severity == "material"` AND all three families (anthropic, openai, google) independently flagged the concern. This route catches the failure mode where three independent LLMs share the same misreading of a paper and the resulting agreement is mistaken for ground truth. Route B runs a **red-team challenge**, not a full debate:

- **Skipped**: prosecute step. The merged finding with its three-family `evidence[]` IS the prosecution; a separate prosecutor ticket would just paraphrase it.
- **Fired**: defend (consensus red-team mode) + synthesize (consensus mode).
- **Defender's target**: the `claim_under_challenge` block emitted by merge (`{claim, cited_evidence, failure_condition}`) pins the exact claim; the defender attacks that claim, not a paraphrase.
- **Synthesizer's verdicts**: explicit Route B labels `consensus_held` / `consensus_broken`, NOT the Route A labels `prosecution_wins` / `defense_wins`. Polarity is different on Route B and reusing Route A labels regresses on every synthesizer call.

A finding that matches both routes (rare — disagreement typically implies not-consensus) takes Route A.

Whichever route fires, if zero rows clear either, debate is skipped entirely. That is the correct outcome on consensus-heavy papers *without* any three-family material concerns.

**Canonical row shape**: `templates/schemas/panel_row.md` is the single source of truth for every field referenced above (`debate_hint`, `claim_under_challenge`, `calibration_pass1`, `severity`, `gate_decision`, `debate.verdict`, etc.).

**Structure when Route A debate fires.** Prosecute → defend → synthesize, per `templates/prosecute.md` / `defend.md` / `synthesize.md`. Role rotation across rounds:

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

Why this phase exists: the 2026-04-14 v4 run shipped a 56.2% overclaim rate on report-entering findings because strong-consensus "settled" findings skipped the debate stage — which had been doing an unacknowledged polish pass by softening overclaimed raw language into narrower synthesizer `surviving_text`. Phase 5 restores that polish as a cheap single-model pass, without the theatre cost of full dialectic.

**Inputs.** All panel-row candidates from merge (Step 6 of `templates/merge_and_rank.md`), plus any updates to debated rows from Phase 4 (verdict, `surviving_text`). Findings killed by defense during Phase 4 do not enter calibration — they are written directly to `dropped_findings[]` with the defender's counter-evidence as the drop reason.

**Blinding.** Same blinding protocol as the post-hoc evaluation (randomised `BF###` IDs in a shuffled pool, manifest_blind.json private, no metadata leak in the prompt).

**Rubric.** Same two axes (`quote_verified`, `calibration`) as `templates/evaluate.md`.

**Demote-on-uncertainty disposition.** Overclaimed and partial-quote findings get one rewrite attempt (polish pass via gemini-3.1-pro-preview against the real passage). The re-annotation uses an **upgraded annotator** (codex `gpt-5.4` full, not mini) to break correlated-error blind spots between two mini reads on the same rubric — the 2026-04-15 A/B found 7 of 28 shipped findings still read as overclaimed to a fresh judge, all from polished rows where mini-then-mini said supported. Three-way disposition:
- **Clean pass** (unqualified `supported` + `quote: yes`, no uncertainty triggers) → `calibrated_narrowed`, keep severity.
- **Uncertain pass** (any of four triggers fire: qualified verdict, hedging language like `ambiguous`/`partially`/`inferential`/`not explicit`, indirect support, internal rubric disagreement) → `calibrated_narrowed` AND demote severity one tier (material → local, local → nit).
- **Still failing** (verdict `overclaimed` / `partial` / `unsupported`, or `quote: no`) → drop. No further rewrites, no second demotion.

**Outputs.** `_calibration/final_findings.json` — the calibrated set that feeds the final report (not `ranked_issues_verified.json`). Plus `_calibration/00_calibration.md` scorecard with pre/post overclaim rates.

Default first-pass annotator: **codex with `gpt-5.4-mini`** (volume model, ~38 rows/run, rubric-bounded). Re-annotator after polish: **codex with `gpt-5.4`** full (fires on ~8 rows/run, ~$1-2 cost delta). Fallback: claude-sonnet-4.6 when codex is rate-limited and the paper exceeds haiku's context window. Full spec in `templates/calibrate.md`.

### Phase 6 — Panel + renderers (v6 replaces v5's "Final report")

The v6 primary deliverable is a **finding panel**. Prose memos are secondary renderings driven entirely off the panel rows — no prose stage can introduce new content, only summarize what survived calibration.

1. **`_artifacts/json/panel.json`** — the canonical output. Compiled inline by the orchestrator (Wave 7a, no ticket) by wrapping `_calibration/final_findings.json` with paper/engine/holistic_pass/summary metadata. Rows follow `templates/schemas/panel_row.md` — the row shape is never redefined here. Top-level shape:
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

**The Obsidian folder IS the workspace.** There is no separate scratch area. Every review is a self-contained folder inside the Obsidian vault. Curated markdown lives in top-level numbered folders; raw machine artifacts live in `_artifacts/`, `_calibration/`, and `_evaluation/`.

```
~/.../notes/work/referee-reports/<paper-slug>/
│
├── review.md                          # top-level index: metadata, status, TOC
├── _paper/
│   ├── paper.md                       # source paper
│   └── paper.pdf                      # optional original PDF
├── 0_orientation/                     # independent paper maps
│   ├── 00_orientation.md
│   ├── claude.md
│   ├── codex.md
│   └── gemini.md
├── 0_holistic/                        # per-family holistic passes + attack-surface index
│   ├── 00_holistic.md
│   ├── claude.md
│   ├── codex.md
│   ├── gemini.md
│   └── attack_surface_index.md
├── 1_discovery/
│   ├── 00_discovery.md
│   ├── holistic_candidates/{claude,codex,gemini}.md
│   ├── broad_critic/{claude,codex,gemini}.md
│   └── narrow_evidence/{claude,codex,gemini}.md
├── 2_ranking/
│   ├── 00_ranking.md
│   ├── issue_register.md
│   ├── triage.md
│   └── verification.md
├── 3_debates/
│   ├── 00_debates.md
│   ├── 01_<slug>/
│   │   ├── 00_issue.md
│   │   ├── r1_prosecute.md
│   │   ├── r1_defend.md
│   │   ├── r1_synthesize.md
│   │   └── 99_summary.md
│   └── ...
├── 4_panel/
│   ├── panel.md
│   ├── author_memo.md OR referee_memo.md
│   └── revision_plan.md OR referee_letter_draft.md
├── _calibration/
│   ├── 00_calibration.md
│   ├── final_findings.json
│   ├── dropped.json
│   ├── demoted.json
│   ├── manifest_blind.json
│   ├── tickets.json
│   ├── prompts/<blind_id>.md
│   ├── annotations/<blind_id>.json
│   ├── rewrites/<blind_id>.json
│   └── sessions/<blind_id>.log
├── _evaluation/
│   ├── 00_evaluation.md
│   ├── annotations_unblinded.csv
│   ├── manifest_blind.json
│   ├── tickets.json
│   ├── results.json
│   ├── prompts/<blind_id>.md
│   ├── annotations/<blind_id>.json
│   └── sessions/<blind_id>.log
└── _artifacts/
    ├── tickets.json
    ├── prompts/
    ├── sessions/
    └── json/
```

See `templates/obsidian_structure.md` for the complete specification and `templates/obsidian_render.md` for the markdown projection rules.

## Agent routing

| Agent | Executor | Default role |
|-------|----------|--------------|
| Claude | Claude Code (inline) | Orchestrator, Claude-owned discovery/merge tickets, rotated debate role |
| Codex | `agent-ctl` | Independent reader, calibration annotator, rotated debate role |
| Gemini | `agent-ctl` | Independent reader, web verification, panel writer, rotated debate role |

Gemini owns the verification step because web search is concentrated there by design. Claude owns orchestration and inline tickets. Codex is the default calibrator because the calibration loop is rubric-bounded and benefits from a different architecture than Claude.

## Agent communication

Use `agent-ctl run-dag` as the primary interface:

```bash
agent-ctl run-dag <paper-folder>/_artifacts/tickets.json --cwd <paper-folder> --concurrent 3
agent-ctl dag-status <paper-folder>/_artifacts/tickets.json
```

Claude-owned tickets do **not** go through `agent-ctl`. Claude executes them inline, writes the declared outputs, and marks them `done` in `tickets.json`.

Long prompts live on disk under `_artifacts/prompts/`. Tickets point at prompt files; do not rely on shell-inline mega-prompts.

## Execution

When `/disputatio <path>` is invoked, Claude runs a state-driven loop. Read disk, do one thing, write disk, repeat.

**State sources**:
- `$PAPER/_artifacts/tickets.json` — machine source of truth
- `$PAPER/review.md` frontmatter — human-readable phase summary

**Current flow**:

1. **Init + preflight** — create the paper folder only after auth, vault-write, and template sanity checks pass.
2. **Wave 1: orientation** — 3 independent paper maps.
3. **Wave 1.5: holistic** — 3 holistic passes plus inline `attack_surface_index.json`.
4. **Wave 2: discovery** — 9 tickets (3 tracks × 3 families) plus optional baseline sentinel.
5. **Phase 3: merge + verify** — merge atomic findings, produce panel-row candidates, optionally run web verification.
6. **Phase 5a: calibration pass 1** — blind-annotate all candidate panel rows before any debate decision.
7. **Phase 4: escalation gate** — apply Route A / Route B to calibration survivors only; emit debate tickets only for gate-clearers.
8. **Phase 5b: finalize calibrated set** — polish/re-annotate where required, then write `_calibration/final_findings.json`.
9. **Phase 6: panel compile + render** — compile `_artifacts/json/panel.json`, then run one render ticket producing `4_panel/panel.md` plus the mode-specific memo and optional auxiliary file.
10. **Phase 7: optional A/B evaluation** — only on request, under `_evaluation/`.

The run is complete when `panel.json` exists, the Phase 6 render outputs exist, and `review.md` is marked `phase: complete`.

### Init procedure

When no `tickets.json` exists:

1. Run preflight:
   - agent auth pings for the transports you will actually use
   - vault write probe
   - template placeholder sanity
   - OCR backend probe when the input is a PDF
2. Determine `<paper-slug>` from the input filename.
3. Create the current directory layout:
   `mkdir -p $PAPER/{_paper,0_orientation,0_holistic/{},1_discovery/{holistic_candidates,broad_critic,narrow_evidence},2_ranking,3_debates,4_panel,_artifacts/{prompts,json,sessions},_calibration/{prompts,annotations,rewrites,sessions},_evaluation/{prompts,annotations,sessions}}`
4. Copy or OCR the paper into `_paper/paper.md`; copy the PDF to `_paper/paper.pdf` when available.
5. Write `review.md`.
6. Emit Wave 1 tickets into `_artifacts/tickets.json`.

### Prompt generation

To generate a prompt for a ticket:

1. Read the relevant template from `templates/`.
2. Inline or reference only the inputs the phase actually needs.
3. Substitute placeholders. The full set in current use across the template tree:

   General (most prompts):
   - `{{paper_path}}`, `{{paper_text}}` — path or inlined text of the source paper
   - `{{output_path}}` — where to write the JSON output
   - `{{paper_map_path}}` — agent's own orientation JSON
   - `{{holistic_pass_path}}` — agent's own holistic-pass JSON
   - `{{attack_surface_index_path}}` — canonical attack-surface index
   - `{{config.*}}` — configuration values

   Reserved (declared in this contract but not yet substituted by any current template — the renderer reads `engine.mode` from `panel.json` directly):
   - `{{mode}}` — `author` | `referee`. If a future render template starts substituting this token, it does not need to be re-added here.

   Discovery-only:
   - `{{method_content}}` — full text of the method template inlined into the discovery prompt

   Debate-only (Route A and Route B):
   - `{{prosecution}}` — Route A defend/synthesize input; Route B does not use this
   - `{{defense}}` — defend output, used by synthesize on both routes
   - `{{history}}` — prior-round synthesis output for rounds 2+
   - `{{issue_state}}` — the panel-row payload for the issue under debate
   - `{{route}}` — `disagreement` | `consensus`, mandatory on every Phase 4 debate ticket
   - `{{claim_under_challenge}}` — Route B defend/synthesize only (the merge-emitted block pinning the consensus target)
   - `{{three_family_signals}}` — Route B defend/synthesize only (per-family confidence + candidate IDs)

   Preflight aborts on any unsubstituted `{{...}}` token in a written prompt. When a placeholder is not relevant to a given template, the orchestrator must omit the line entirely rather than leave the token in place. The list above is the closed set; adding a new placeholder requires updating this list and the preflight checker simultaneously.
4. Write the result to `_artifacts/prompts/<ticket_id>.md` (or the matching `_calibration/` / `_evaluation/` prompt folder for those sub-DAGs).

### Inline execution

When Claude executes a ticket inline:

1. Read the prompt and declared input files.
2. Produce the declared output files.
3. Render curated markdown where the phase requires it.
4. Mark the ticket `done` in `tickets.json`.

### Validation rules

Before moving forward:

- **Orientation**: every `orient_*.json` must parse and contain a usable paper map.
- **Holistic**: every `holistic_*.json` must parse and expose attack surfaces plus main claims.
- **Discovery**: every discovery output must parse; `narrow_evidence` is subject to the engagement audit on `surface_attempts[]` (see `templates/emit_tickets.md` → "Narrow-evidence engagement audit") and gets one retry on a structural failure.
- **Merge**: `panel_rows_candidates.json` must exist and parse.
- **Calibration**: every annotation must return both rubric axes (`quote_verified`, `calibration`).
- **Synthesis**: every `debate_*_synthesize.json` must include a `route` field matching the debate ticket's route, a `verdict` from the route-correct vocabulary (Route A: `prosecution_wins | defense_wins | split | escalate`; Route B: `consensus_held | consensus_broken`), and a non-empty `surviving_text` whenever the verdict is not a drop. Mismatched-route verdicts (e.g. `prosecution_wins` on a Route B ticket) are rejected and the row's debate field is set to `not_run`.
- **Render**: `panel.md` plus the mode-specific memo must exist; dropped findings must be visible (including `dropped_by_red_team` on Route B).

### Logging contract

Every action writes to disk. Nothing lives only in Claude context.

| What | Where | When |
|------|-------|------|
| Prompts sent to agents | `_artifacts/prompts/<ticket_id>.md` | Before launching ticket |
| Raw JSON outputs | `_artifacts/json/<ticket_id>.json` | After ticket completes |
| Agent session logs | `_artifacts/sessions/<ticket_id>.log` | Auto-archived by `agent-ctl`; written inline by Claude for Claude-owned tickets |
| Curated markdown | numbered folders | After each completed phase |
| Calibration artifacts | `_calibration/` | During Phase 5 |
| Evaluation artifacts | `_evaluation/` | During optional Phase 7 |
| DAG state | `_artifacts/tickets.json` | After every state transition |

### Resumability

Re-invoking `/disputatio` on an existing paper folder resumes from disk:

1. Read `_artifacts/tickets.json`.
2. Skip all `done` tickets.
3. Run any ready non-Claude tickets via `agent-ctl run-dag`.
4. Resume Claude-owned inline work from the first ready Claude ticket or inline orchestration step.

## Configuration

User-facing knobs:

| Parameter | CLI flag | Default | Notes |
|-----------|----------|---------|-------|
| Render mode | `--mode` | `author` | `author` or `referee` |
| Debate cap | `--max-debate-rounds` | `2` | Hard cap per escalated finding |
| Web verification | `--skip-web` | off | Skip only when the user explicitly disables it |

Runtime defaults:

| Setting | Default |
|---------|---------|
| Main DAG concurrency | `3` |
| Calibration concurrency | `4` |
| Evaluation concurrency | `4` |

### Runtime envelope (typical economics paper, ~30–60 pages)

Reference figures from the Galeotti, Golub & Goyal 2020 benchmark and steady-state runs on similar-shape papers. Treat as order-of-magnitude, not contractual.

| Quantity | Typical value |
|---|---|
| Wall clock end-to-end | **~2 hours** (parallelism-limited by the slowest family per wave) |
| Total agent calls per run | **~80–130** (3 orient + 3 holistic + 9 discovery + ~5–10 merge/verify + ~30–50 calibration + 0–15 debate + 1–2 render) |
| Calibration row count | ~30–50 candidate rows annotated; ~5–10 trigger polish + re-annotate |
| Debate triggers | **0–5 findings** escalate; typical paper sees 1–3 Route-A or Route-B fires |
| Findings shipped to panel | ~20–30 after merge → calibration → debate (110 raw → 27 shipped on Galeotti) |
| Marginal cost per run | **$0** on default routing — Claude Pro / ChatGPT Pro / Gemini OAuth subscriptions cover all calls. The only real cost is wall clock + per-subscription rate caps (Codex OAuth has a weekly cap that ~1 full run can hit on heavy use; see Known limitations in README). |
| API-equivalent cost (reference only) | ~$5–$15 if the same calls were billed at provider list prices. Not what you pay; included so the compute envelope is comparable to API-only systems. |

Length scales the envelope roughly linearly above 60 pages — orientation, holistic, and discovery are all full-paper context calls. A 100-page paper is ~1.6×; a 200-page handbook chapter is closer to 3×. The wall-clock and rate-cap costs scale with it; the dollar marginal cost stays at zero.

### Model routing

When emitting tickets, route models per the current pipeline:

| Task | Claude | Codex | Gemini |
|------|--------|-------|--------|
| Orientation | sonnet | gpt-5.4-mini | gemini-3-flash-preview |
| Holistic pass | opus/sonnet | gpt-5.4 | gemini-3.1-pro-preview |
| Discovery | sonnet | gpt-5.4-mini | gemini-3-flash-preview |
| Merge & rank | **opus** | — | — |
| Baseline sentinel | **opus** | — | — |
| Defense | — | gpt-5.4 | gemini-3.1-pro-preview |
| Synthesis | **opus** | — | — |
| Verification (web) | — | — | gemini-3.1-pro-preview |
| Calibration pass 1 | sonnet (fallback) | **gpt-5.4-mini** | gemini-3-flash-preview (fallback) |
| Calibration re-annotator | sonnet (fallback) | **gpt-5.4** | — |
| Panel render | claude-opus (fallback) | — | **gemini-3.1-pro-preview** |

## Review criteria

The methods and the panel-row schema determine what counts as a valid finding. No separate criteria file overrides them.

## Obsidian is the workspace

Every review lives inside one folder in the Obsidian vault. Curated markdown is the human projection. JSON is the machine source of truth. Session logs are preserved so the run remains auditable and replayable.

## Explicit rules (v6)

Three orchestration decisions were previously left to orchestrator improvisation. They are now specified here to eliminate runtime ambiguity.

### Two-route escalation gate (Phase 4 entry)

A finding enters debate via one of two routes. Both evaluate at the start of Phase 4 over every candidate panel row from merge.

#### Route A — Disagreement

Escalate iff ALL four conditions hold:

1. **Cross-family disagreement is real.** Operationally: at least one family's discovery ticket flagged the concern with `confidence: high`, AND at least one other family either (a) did not surface the concern at all, or (b) surfaced a variant with `confidence: medium` or `low` whose claim conflicts with the high-confidence version. Encoded in `merge.debate_hint.cross_family_disagreement`: `strong` (condition met), `moderate` (one family flagged high, others silent without conflicting variant — does NOT satisfy the condition by itself), `none` (all families agree or all ignore).
2. **Evidence exists on both sides.** Operationally: the paper's text supports BOTH the finding's claim AND a plausible counter-claim. Encoded in `merge.debate_hint.evidence_conflict_in_paper`: `yes` if the paper contains passages that could be cited by either side; `no` if the paper's text uniformly supports one side. The evidence compiler's `support_type` tags inform this.
3. **Severity would change on verdict.** Operationally: if the finding's severity is `nit`, the condition is FALSE regardless. If severity is `local` or `material`, ask whether a `defense_wins` verdict would drop the finding entirely vs narrow it. Drops qualify; narrowings do not (since calibration can narrow without debate). Encoded in `merge.debate_hint.severity_sensitive`.
4. **Finding would otherwise be user-visible.** Derived rule, not a stored field: `calibration_pass1.verdict in {supported, calibrated_narrowed}` AND `severity in {material, local}`. If calibration Pass 1 dropped the finding as `unsupported` or demoted it to `nit`, debate is wasted compute. Evaluated on the Pass 1 verdict (not on the post-debate `calibration` verdict, which Pass 2 may overwrite) — Phase 4 therefore fires AFTER Phase 5 Pass 1, not before. See flow below.

Route A structure: **prosecute → defend → synthesize**. Verdicts: `prosecution_wins | defense_wins | split | escalate`. Polarity: `prosecution_wins` ships the concern to the panel; `defense_wins` drops the concern.

#### Route B — Consensus override

Escalate iff BOTH hold:

- **`debate_hint.high_severity_consensus == true`** — set by merge when `severity == "material"` AND the distinct-families set across `sources[]` equals `{"anthropic", "openai", "google"}` (explicit family-set check; NOT a threshold on the `cross_agent_support` rank-score field, which can saturate spuriously).
- **Condition 4 above holds** (calibration Pass 1 verdict user-visible AND severity material/local).

Route B exists because three independent LLMs agreeing on a material concern produces `cross_family_disagreement == "none"` and closes Route A — but that agreement is also exactly the regime where a shared hallucination can ship as ground truth.

Route B structure: **defend + synthesize only**. No prosecute. The three-family `evidence[]` plus the `claim_under_challenge` block emitted by merge is the prosecution; a separate prosecutor call would just paraphrase it.

- **Defender reads `claim_under_challenge`**, not a prosecutor output. The block pins the exact claim, the three cited evidence passages, and the failure condition. Defender plays red-team: prove the three families share a misreading.
- **Synthesizer verdicts on Route B**: `consensus_held` (defender failed to break the consensus — ship the finding with a "consensus survived red-team" badge) or `consensus_broken` (defender proved shared misreading — drop the finding with the defender's counter-evidence as drop reason). Route A labels are NOT valid on Route B. Reusing `prosecution_wins` / `defense_wins` on Route B regresses the synthesizer because training priors treat `defense_wins` as "paper wins, ship concern" — the opposite of Route B's polarity.

A finding matching both routes takes Route A. If it matches neither, it does not escalate.

**Revised v6 flow**: merge (Phase 3) → calibration first pass on all candidates (Phase 5a) → two-route gate applied to calibration survivors (Phase 4 trigger evaluation) → debate fires on gate-clearers (Phase 4, Route A or Route B structure) → calibration second pass on debate survivors to capture `surviving_text` (Phase 5b) → panel render (Phase 6). Templates keep their current names; the phases are conceptually interleaved.

If zero findings clear either route, debate is skipped. That is the correct outcome on consensus-heavy papers *without* three-family material concerns — the mere absence of disagreement no longer closes debate if Route B conditions hold.

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
