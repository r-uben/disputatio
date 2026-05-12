# `.claude/agents/` — disputatio subagent definitions

Claude Code subagents (the `Agent` tool) that the disputatio orchestrator can dispatch for specific phases of the pipeline.

## Status

**Wiring in progress.** The orchestrator originally dispatched Claude-side phases inline (Claude reads `SKILL.md` and executes directly). Wiring those phases through these subagent definitions is incremental:

| Phase / role | Subagent | Wired in SKILL.md? |
|---|---|---|
| Phase 0 — orientation (Claude family) | [`orient-reader`](orient-reader.md) | **Yes** |
| Phase 1 — holistic pass (Claude family) | [`holistic-reader`](holistic-reader.md) | **Yes** |
| Phase 2 — discovery (any track, any family) | [`discovery-worker`](discovery-worker.md) | Defined, pending smoke test |
| Wave 2.5 — baseline coverage sentinel | (pending — `baseline-reviewer`) | Not yet defined |
| Phase 3 — atomic merge + ranking | (pending — `merge-ranker`) | Not yet defined |
| Phase 4 — debate (escalation only) | [`debate-prosecutor`](debate-prosecutor.md), [`debate-synthesizer`](debate-synthesizer.md) | Defined, pending smoke test |
| Phase 5 — blinded calibration | [`calibration-judge`](calibration-judge.md) | Defined, pending smoke test |
| Phase 6 — single-writer render | [`panel-renderer`](panel-renderer.md) | Defined, pending smoke test |

The wiring sequence (per codex 5.5 review):
1. Wire orient + holistic first (this round). Run a smoke test on a real paper through Phase 1.
2. After smoke test passes, define and wire `baseline-reviewer` and `merge-ranker`.
3. After Phase 3 lands, wire the rest in order: calibration, debate, render.

When you want to invoke one directly from an interactive Claude Code session for testing:
```
> Use the orient-reader subagent to produce the Claude orientation map for the current paper.
```

## What's NOT here

- **No codex / gemini subagents.** Those families are still invoked via `agent_ctl.py` shell-out to the external CLIs. Claude Code subagents are Claude-side only; they cannot replace cross-architecture dispatch.
- **No orchestrator subagent.** The top-level disputatio runner is the default Claude Code session, not a subagent — it has to read `SKILL.md`, emit ticket waves, inspect landed artifacts, decide the next wave. Dispatching that role would lose the stateful control loop.
- **No wave-emission subagent.** Wave-emission shapes the next wave based on what just landed; it is orchestration logic, not worker labor.
- **No polish-rewriter.** Polish-rewrite is a sub-step of calibration with the same role as the judge — handled inside `calibration-judge`, not a separate subagent.
- **No discovery-broad / discovery-narrow / discovery-holistic split.** Track is a parameter to the generic `discovery-worker`, not a separate role.

## How these relate to AGENTS.md / GEMINI.md

`AGENTS.md` and `GEMINI.md` at the repo root are operating manuals for the **external CLIs** (codex, gemini) — they are loaded by those CLIs when invoked in a paper workspace. The subagent files here are **internal to Claude Code** — they shape Claude's behavior when it dispatches a phase to itself as a subagent.

The two layers do not overlap. A discovery ticket dispatched to codex picks up `AGENTS.md`; the same ticket dispatched to Claude via the `discovery-worker` subagent picks up `discovery-worker.md`. Same task, two different operating manuals depending on which family runs it.

## Design rationale

See `docs/design-notes/` for the broader architectural reasoning. The short version: Claude Code's native subagent system gives role/context isolation for Claude-side phases. It does not replace `agent_ctl.py`, which still handles the hard parts of cross-CLI orchestration (timeouts, weekly caps, OAuth expiry, retries).
