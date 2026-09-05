# CLAUDE.md

*This file is read by Claude Code when working inside this repo. It is contributor / agent guidance, not user documentation. If you are looking for what disputatio does or how to install it, see [README.md](README.md). If you are looking for the formal pipeline protocol, see [SKILL.md](SKILL.md).*

---

## Disputatio (v6)

A cross-architecture paper-review panel for pre-submission authors and first-round referees. Primary deliverable is a **finding panel** — each concern with exact quote, cross-family support, debate trail (only when triggered), calibration verdict, and a mode-specific priority label. Secondary deliverables (prose memo, optional revision plan or referee-letter draft) are rendered off the panel; the writer cannot invent findings. Claims that do not survive verification are preserved in the audit trail with drop reasons — the system demonstrates restraint instead of hiding what got killed.

This is a Claude Code skill, not a Python package — Claude Code is the runtime.

### Authoritative spec

**`SKILL.md` is the single source of truth for v6 orchestration.** When any other file in this repo disagrees with SKILL.md, SKILL.md wins. If you find a contradiction, patch the other file toward SKILL.md rather than the reverse.

The templates are the authoritative spec for their respective phases:

| Phase | Authoritative template |
|-------|------------------------|
| 0. Orient | `templates/orient.md` |
| 1. Holistic | `templates/holistic.md` |
| 2. Discovery (9 tickets across 3 tracks) | `templates/discover_holistic.md`, `templates/discover_broad.md`, `templates/discover_narrow.md` |
| 3. Merge + rank + verify | `templates/merge_and_rank.md`, `templates/verify.md` |
| 4. Debate (escalation-only) | `templates/prosecute.md`, `templates/defend.md`, `templates/synthesize.md` |
| 5. Calibration | `templates/calibrate.md` + `templates/polish.md` (rewrite sub-step) |
| 6. Panel + renderers | `templates/render_panel.md` |
| 7. A/B evaluation (optional) | `templates/evaluation.md` + `templates/evaluate.md` |
| Wave 1.5 aux | `templates/holistic.md` + inline attack-surface-index builder (see SKILL.md) |
| Wave 2.5 aux (coverage sentinel) | `templates/baseline.md` |
| Meta | `templates/emit_tickets.md` for the wave-level ticket schema |

### How it works

`/disputatio <paper> [--mode author|referee]` runs a seven-phase pipeline orchestrated as a ticket DAG. Claude generates tickets in waves; `agent-ctl run-dag` executes each wave; between waves Claude inspects outputs and emits the next wave.

0. **Orientation** — each of 3 agents reads the paper once and produces a neutral paper map. Maps are NOT merged; each agent uses its own as a cache.
1. **Holistic pass (v6, new)** — each agent produces a paper spine + main claims + attack surfaces + likely referee questions. The orchestrator unions these into a canonical attack-surface index that Phase 2 discovery uses as shared context.
2. **Discovery** — 9 tickets total (3 agents × 3 tracks: `holistic_candidates`, `broad_critic`, `narrow_evidence`). Each candidate passes through an inline evidence compiler that pins a verbatim quote + location + `direct_quote | derived_inference` tag before the candidate is written.
3. **Merge, rank, verify, emit panel rows** — atomic merge with programmatic verbatim-quote validator, rank scoring for importance ordering, Gemini web-verification on external-fact claims, baseline-diff coverage sentinel check, then emit `panel_rows_candidates.json`.
4. **Debate (escalation-only)** — fires only when all four gate conditions hold (cross-family disagreement real, evidence on both sides, severity would change on verdict, finding would be user-visible). Most findings skip debate entirely. 2 rounds maximum default.
5. **Calibration** — every candidate panel row runs through a blinded per-finding annotator. Overclaimed or partial-quote findings get one polish-rewrite attempt; unsupported ones drop. Result: calibrated panel rows.
6. **Panel + renderers** — single long-context writer reads the calibrated set and produces `panel.json` (canonical) + `panel.md` (table view) + mode-specific memo + optional auxiliary (revision plan or referee-letter draft). Writer cannot invent findings or change verdicts.
7. **A/B evaluation (optional)** — post-hoc blinded comparison vs prior versions or other systems. Not part of the default run.

### Three discovery tracks (v6, replacing v5's seven methods)

Methods still exist (M0 close reading, M2 contradictions, M3 transformations, M4 counterexamples, M5 self-measured critique, M6 causal disentangling, M8 algebraic derivation trace) but are **folded into three tracks** that each ticket runs:

| Track | Templates in scope | Purpose |
|---|---|---|
| `holistic_candidates` | `holistic.md` output + attack-surface index | Conceptual-scope concerns the method tracks under-detect |
| `broad_critic` | M0 + M2 + M5 fused | Contradictions, scope mismatches, commitment violations, transcription errors |
| `narrow_evidence` | M3 + M4 + M6 + M8 fused, targeted at priority attack surfaces | Deep evidence-heavy findings on a small set of targets; M8 mandatory on every theory/proof surface |

M1 (structured disputation) is reserved for Phase 4 debate rounds. M7 (iterative refinement) is the synthesis step within debate.

### Structure (v6 repo)

```
disputatio/
├── SKILL.md                         # authoritative v6 protocol
├── CLAUDE.md                        # this file — pointer to SKILL.md
├── docs/
│   ├── log/2026-04-14_upstream-pivot-plan.md  # product + architecture plan (historical)
│   ├── log/                         # dated dev log
│   └── ...
└── templates/
    ├── emit_tickets.md              # ticket schema + wave protocol
    ├── obsidian_structure.md        # per-paper Obsidian folder spec
    ├── obsidian_render.md           # rendering spec
    ├── orient.md                    # Phase 0
    ├── holistic.md                  # Phase 1 (v6)
    ├── discover_holistic.md         # Phase 2 track 1 (v6)
    ├── discover_broad.md            # Phase 2 track 2 (v6)
    ├── discover_narrow.md           # Phase 2 track 3 (v6)
    ├── merge_and_rank.md            # Phase 3
    ├── verify.md                    # Phase 3 web-verify
    ├── baseline.md                  # Wave 2.5 coverage sentinel
    ├── prosecute.md                 # Phase 4 escalated-only
    ├── defend.md                    # Phase 4
    ├── synthesize.md                # Phase 4
    ├── calibrate.md                 # Phase 5
    ├── polish.md                    # Phase 5 rewrite sub-step
    ├── render_panel.md              # Phase 6
    ├── evaluation.md                # Phase 7 A/B protocol
    ├── evaluate.md                  # Phase 7 per-finding prompt
    └── methods/
        ├── m1_disputation.md        # shapes debate rounds
        ├── m2_contradiction.md      # subsumed into broad_critic
        ├── m3_transformation.md     # subsumed into narrow_evidence
        ├── m4_counterexample.md     # subsumed into narrow_evidence
        ├── m5_immanent.md           # subsumed into broad_critic
        ├── m6_disentangling.md      # subsumed into narrow_evidence
        ├── m7_refinement.md         # used by synthesize.md
        ├── m8_derivation.md         # subsumed into narrow_evidence (mandatory on theory/proof surfaces)
        └── m0_close_reading.md      # subsumed into broad_critic
```

A review lives inside the Obsidian vault, not this repo:

```
notes/work/referee-reports/<paper-slug>/
├── review.md                     # top-level index, mode, phase status
├── _paper/paper.md               # socr-OCR'd source
├── 0_orientation/                # per-agent paper maps
├── 0_holistic/                   # per-agent holistic passes + attack-surface index
├── 1_discovery/                  # per-agent, per-track candidate findings
├── 2_ranking/                    # merged atomic findings + panel-row candidates
├── 3_debates/                    # only escalated findings
├── 4_panel/                      # panel.md table + panel.json + memo + optional aux
├── _calibration/                 # blinded per-finding annotations + rewrites
├── _evaluation/                  # optional A/B post-hoc comparison
└── _artifacts/                   # tickets.json, prompts/, json/, sessions/
```

### Key v6 design decisions

- **Finding panel is primary, prose memo is secondary.** The writer renders the panel into prose; it cannot invent findings, change verdicts, or hide drops.
- **Holistic pass closes the conceptual-scope gap** that method-based sweeps miss. 3 tickets, one per family.
- **9-ticket discovery** (3 tracks × 3 families), down from the v3–v5 shape of 18. Track names are stable output anchors (`holistic_candidates`, `broad_critic`, `narrow_evidence`).
- **Inline evidence compiler** enforces verbatim-quote discipline at write time, not merge time. Candidates without a quote object are dropped pre-write.
- **Atomic merge with programmatic validator** — every merged issue's `quote` must substring-match `_paper/paper.md`. Cluster-split rules enforced.
- **Baseline is a coverage sentinel, not a router.** Wave 2.5 single-shot opus runs in parallel with Phase 1+2; if it surfaces a conceptual-scope concern the holistic pass missed, that's a signal to strengthen the holistic pass, not a route into debate. (Active during the first v6 releases; retirement gated on 3+ papers of measurement.)
- **Debate is escalation-only.** Four-way gate: cross-family disagreement real + evidence on both sides + severity would change on verdict + finding would be user-visible. Most findings skip debate.
- **Calibration is the pre-publication quality gate.** Blinded per-finding annotator, demote-on-doubt, one polish rewrite per flagged finding, drop if still failing. Calibration writes onto panel rows.
- **Single-writer rendering.** One long-context call (Antigravity with Gemini 3.1 Pro (High) as the recommended reasoning model, opus fallback) reads the calibrated panel and produces panel.md + memo + optional aux in uniform voice.
- **Mode flag propagates to priority labels.** `--mode author` renders `fix_before_submit | watch_in_review | can_ignore`. `--mode referee` renders `endorse | verify_before_endorsing | skip`. Same engine, same panel, different label vocabulary.
- **Dropped findings surfaced, not hidden.** Panel output explicitly lists drops from debate defenders and calibration demote-to-drop, with reasons. System demonstrates restraint.
- **Ticket DAG orchestration** — every agent call is a ticket on disk. Claude plans, `agent-ctl run-dag` executes. Resumable, auditable, replayable.

### Lessons from testing (historical, kept for operational wisdom)

- **Codex needs `--full-auto`** (now default in agent-ctl) to write files
- **Antigravity (`agy`) replaces the legacy `gemini` CLI** as the backend for the `"gemini"` agent label in `agent-ctl`. Same agent_ctl API surface — `start gemini`, `send`, `result`, `send-or-start` — but the underlying binary is `agy`, the model store lives at `~/.gemini/antigravity-cli/conversations/`, and resume uses `--conversation <UUID>` instead of `--resume`.
- **Antigravity needs `--dangerously-skip-permissions`** to write files headlessly (equivalent to old `--yolo`). `agent-ctl` translates `-y` / `--yolo` automatically; tickets that already pass either flag keep working.
- **Antigravity has no `-m` / `--model` flag**, but `agent-ctl` ships an `agy-set-model` pty wrapper that drives the `/model` picker programmatically and is called under a flock before each gemini ticket. Per-phase model routing is therefore restored: ticket `model: "gemini-3.1-pro-preview"` actually switches Antigravity to `Gemini 3.1 Pro (High)` for that ticket, `gemini-3-flash-preview` switches to `Gemini 3.5 Flash (High)`, and so on. Concurrent gemini tickets serialize through the lock (~10s per switch). Unrecognized model strings or a missing `agy-set-model` binary fall back to whichever model is globally active.
- **Antigravity OAuth lives in the desktop app.** If a DAG ticket fails with auth errors (FatalCancellationError, "not authenticated"), open the Antigravity app and re-sign-in, OR run `agy -p 'ping'` once to refresh. `agent-ctl run-dag` halts the whole DAG with an actionable message on this path so the user can re-auth before resuming.
- **Server-side 429s are still capacity, not quota** — retrying with backoff usually resolves.
- **Antigravity writes malformed JSON** — embeds raw LaTeX with control characters and invalid escapes (inherits the issue from the underlying Gemini models). `agent-ctl run-dag` auto-cleans JSON files after write.
- **OCR'd papers need explicit warnings** — hallucinated text blocks from unrelated documents get flagged as "errors" otherwise.
- **YOU MUST use `socr` for every PDF input — no exceptions.** Not `pdftotext`, not `pdftohtml`. socr preserves equations, figure captions, and structural cues the review depends on.
- **Canonical socr invocation:** `socr process <pdf> --save-figures -o <out>`. Bare `process` is the agentic default; there is now only one pipeline (UnifiedPipeline) and `--unified` is an accepted no-op kept for compatibility. See `~/.claude/skills/ocr/SKILL.md` for the rationale.
- **If a specific page comes out wrong**, fix the classifier or escalation rule (socr side). Do not switch engines for the whole document. There is no consensus mode on `process`: `--multi-engine` was deleted in socr #298, and `--engines` exists only on `socr benchmark run`. There is no forced-engine flag either: the agentic ladder is built from `enabled_engines` (orchestrator PP-5) and `--primary` only sets the recorded primary engine. To pin an engine for one document, pass a config file with `enabled_engines: [<engine>]`.
- **Long prompts need temp files** — inline shell escaping breaks beyond a few KB.
- **`$A wait <ids>` eliminates polling loops** — use it.
- **Codex hits weekly cap every ~1 full run** on ChatGPT Pro. High-volume users need a direct API-key transport; `agent-ctl` currently supports only the OAuth path.
- **Haiku cannot handle 140KB-paper prompts** — long-context beta not enabled on subagent subscription. Use sonnet or opus for long-context annotation.

### Prerequisites

- `claude` CLI authenticated (Claude Pro / Claude Code)
- `codex` CLI authenticated (ChatGPT Pro). Default model `gpt-5.4`
- `agy` (Antigravity CLI) authenticated via the Antigravity desktop app (Google AI Pro OAuth). Per-phase model routing is handled automatically by `agent-ctl` via the `agy-set-model` wrapper — no manual `/model` step is required, but `agy-set-model` must be on PATH (default install: `~/.local/bin/agy-set-model`).
- `agent-ctl` at `~/.claude/skills/agent_ctl.py` with `wait`, `run-dag`, `dag-status`, `--full-auto` default for Codex. The `"gemini"` agent label now routes to `agy` under the hood.
- Obsidian vault at `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/notes/` with a `work/referee-reports/` subtree
