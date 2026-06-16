# vendor/

Runtime helpers disputatio uses. **As of the symlink refactor, the skills and
the orchestrator are no longer committed here** — they are symlinks to their
canonical homes on the maintainer's machine and are git-ignored, so a clone of
this repo does **not** ship them:

| Path | What it is | Tracked? | Canonical home |
|------|-----------|----------|----------------|
| `skills/codex`  | second-opinion skill (OpenAI / Codex CLI) | no (symlink, ignored) | `~/.config/ai-skills/codex` |
| `skills/gemini` | second-opinion skill (Google / Antigravity CLI) | no (symlink, ignored) | `~/.config/ai-skills/gemini` |
| `agent_ctl.py`  | multi-agent orchestrator + ticket-DAG runner | no (symlink, ignored) | `~/.claude/skills/agent_ctl.py` |
| `agy-set-model` | pty wrapper around agy's interactive `/model` picker | **yes** | this repo (no home elsewhere) |
| `README.md`     | this file | **yes** | this repo |

Rationale: the skills and orchestrator are general-purpose helpers, not
disputatio's intellectual core. Keeping a single source of truth (and not a
drifting committed copy) matters more than bundling them. The symlinks point at
maintainer-local absolute paths, so they would dangle for anyone else — hence
they are git-ignored and never pushed.

## Installing (you are not the maintainer)

A fresh clone gives you `agy-set-model` and this README, but **not** `codex`,
`gemini`, or `agent_ctl.py`. To run disputatio:

1. Provide your own `codex` and `gemini` skills and `agent_ctl.py` in
   `~/.claude/skills/` (or wherever Claude Code discovers skills). Disputatio
   resolves them at runtime via normal skill discovery.
2. Run `./install.sh` from the repo root — it links the **disputatio** skill
   into `~/.claude/skills/` and nothing else.

disputatio needs `agent_ctl.py` at a path Claude Code can run (it shells out to
`agent_ctl.py run-dag`). Make sure your copy is on that path.

## `agent_ctl.py`

Subprocess manager for Codex and Antigravity (agy) CLI sessions. disputatio
needs it at runtime to launch external agents and execute the ticket DAG.
`run-dag` is what disputatio uses 99% of the time; the lower-level commands
(`start`, `wait`, `result`) exist for ad-hoc agent calls.

```bash
python3 ~/.claude/skills/agent_ctl.py <subcommand> --help
```

The maintainer edits the canonical file directly at
`~/.claude/skills/agent_ctl.py`; the old `scripts/sync-agent-ctl.sh`
copy-into-vendor step is retired now that `vendor/agent_ctl.py` is a symlink.
