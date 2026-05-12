# `.claude/agents/` — disputatio subagent definitions

Claude Code subagents (the `Agent` tool) that the disputatio orchestrator can dispatch for specific phases of the pipeline.

## Status

**Defined, not yet wired in.** The orchestrator currently dispatches inline (Claude reads `SKILL.md` and executes phases directly). These subagent definitions exist so that Phase B of the orchestration evolution — moving Claude-side phase dispatch into the native subagent system — can be done incrementally without touching `agent_ctl.py` (which still handles the codex/gemini CLI shell-outs).

When you want to invoke one of these directly from an interactive Claude Code session for testing:
```
> Use the discovery-worker subagent to run track T2 on the current paper.
```

## What's here

| File | Role | When dispatched |
|---|---|---|
| [`discovery-worker.md`](discovery-worker.md) | Generic discovery role — finds candidate concerns on a single track for a single family | Phase 2 (Discovery) — 9 tickets total when fully wired |
| [`calibration-judge.md`](calibration-judge.md) | Blinded per-finding annotator with demote-or-drop discipline | Phase 5 (Calibration) — once per candidate row |
| [`debate-prosecutor.md`](debate-prosecutor.md) | Adversarial prosecution role in escalation debate rounds | Phase 4 (Disputatio) — only on escalated findings |
| [`debate-synthesizer.md`](debate-synthesizer.md) | Synthesizer role producing the refined claim after prosecution + defense | Phase 4 — once per debated finding |
| [`panel-renderer.md`](panel-renderer.md) | Single long-context writer for the final panel + memo + optional aux | Phase 6 (Determinatio) — once per run |

## What's NOT here

- **No codex / gemini subagents.** Those families are still invoked via `agent_ctl.py` shell-out to the external CLIs. Claude Code subagents are Claude-side only; they cannot replace cross-architecture dispatch.
- **No orchestrator subagent.** The top-level disputatio runner is the default Claude Code session, not a subagent — it has to read SKILL.md and emit tickets, which is the orchestrator role itself.
- **No discovery-broad / discovery-narrow / discovery-holistic separate files.** Track is a parameter to the generic `discovery-worker`, not a separate role.

## How these relate to AGENTS.md / GEMINI.md

`AGENTS.md` and `GEMINI.md` at the repo root are operating manuals for the **external CLIs** (codex, gemini) — they are loaded by those CLIs when invoked in a paper workspace. The subagent files here are **internal to Claude Code** — they shape Claude's behavior when it dispatches a phase to itself as a subagent.

The two layers do not overlap. A discovery ticket dispatched to codex picks up `AGENTS.md`; the same ticket dispatched to Claude via the `discovery-worker` subagent picks up `discovery-worker.md`. Same task, two different operating manuals depending on which family runs it.

## Design rationale

See `docs/design-notes/` for the broader architectural reasoning. The short version: Claude Code's native subagent system gives role/context isolation for Claude-side phases. It does not replace `agent_ctl.py`, which still handles the hard parts of cross-CLI orchestration (timeouts, weekly caps, OAuth expiry, retries).
