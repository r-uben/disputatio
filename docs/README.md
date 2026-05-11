# docs/

Documentation map. For installation and a quick description, start with the [top-level README](../README.md).

## What to read first

| If you want to… | Start here |
|---|---|
| Understand what disputatio does and why | [`pitch.md`](pitch.md) |
| Read the formal pipeline protocol Claude Code executes | [`../SKILL.md`](../SKILL.md) |
| See the ticket DAG, agent routing, and file layout | [`architecture.md`](architecture.md) |
| Read the nine discovery methods (M0–M8) | [`methods.md`](methods.md) |

## Design rationale

| File | What it covers |
|---|---|
| [`adding-agents.md`](adding-agents.md) | How to extend the three-family panel to additional architectures (Kimi, Ollama-served local models, OpenCode). Also covers reduced-mode runs (2-family + `solo-draft` 1-family). |
| [`transport-model-family.md`](transport-model-family.md) | Why the orchestrator owns model/family routing and the launcher does not. |
| [`design-notes/`](design-notes/) | Per-feature design briefs for the v8.x audit layers (obligation extraction, gap calibration, claim-validity audit, scope/framing audit). |

## Historical record

| Folder | What it is |
|---|---|
| [`log/`](log/) | Dated dev log entries — decisions, pivots, validation runs as they happened. Useful for understanding *why* something looks the way it does. |

The log is the time-stamped record. Earlier entries may make claims (bench scores, comparisons) that were subsequently reframed; the entries are kept as-written. For the current public framing of the project, see the [README](../README.md) and the [pitch](pitch.md).
