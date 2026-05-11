# vendor/

Pinned snapshots of dependencies disputatio uses at runtime. The upstream versions live in the maintainer's `~/.claude/skills/` and may evolve faster than the disputatio release cadence; the copies here are what shipped with the current disputatio commit.

## Drift policy

These files are **not** disputatio's intellectual core — they are general-purpose helpers (a multi-agent orchestrator and two second-opinion skills) that happen to be useful here. By bundling them, disputatio buys easier installation at the cost of letting the snapshots drift behind their upstream versions.

When you are someone other than the maintainer, you have two choices:

1. **Use the bundled versions** (default). Run `./install.sh` from the repo root. Vendored copies symlink into `~/.claude/skills/` and you get a self-contained working setup. You will not see upstream improvements until the next disputatio release pulls them in.
2. **Use your own versions**. Run `./install.sh install --minimal`, which links only the disputatio skill itself. Manage `codex`, `gemini`, and `agent_ctl.py` independently in `~/.claude/skills/`. Disputatio will resolve them at runtime via Claude Code's normal skill discovery.

## Layout

```
vendor/
├── agent_ctl.py        # multi-agent orchestrator (1310 lines)
├── skills/
│   ├── codex/SKILL.md  # second-opinion skill (OpenAI / Codex CLI)
│   └── gemini/SKILL.md # second-opinion skill (Google / Gemini CLI)
└── README.md           # this file
```

## `agent_ctl.py`

Subprocess manager for Codex and Gemini CLI sessions. The disputatio skill needs this at runtime to launch external agents and execute the ticket DAG.

### Source of truth

`~/.claude/skills/agent_ctl.py` (the maintainer's local Claude Code skills directory).

This `vendor/` copy is a **synced snapshot** committed for two reasons:

1. **Public users** can read the dependency without having access to the maintainer's machine.
2. **Reproducibility** — the version of `agent_ctl.py` that ships with a given disputatio commit is pinned alongside it.

### Installation (public users)

To use disputatio you need this script at `~/.claude/skills/agent_ctl.py`. From a fresh checkout:

```bash
mkdir -p ~/.claude/skills
cp vendor/agent_ctl.py ~/.claude/skills/agent_ctl.py
chmod +x ~/.claude/skills/agent_ctl.py
```

Verify by running:

```bash
python3 ~/.claude/skills/agent_ctl.py --help
```

You should see the `start / send / check / result / kill / status / wait / run-dag / dag-status / cleanup` subcommand list.

### Updating (maintainer)

When you edit `~/.claude/skills/agent_ctl.py`, refresh the vendored copy:

```bash
./scripts/sync-agent-ctl.sh
```

This is a one-liner that copies the source into `vendor/agent_ctl.py`. Commit the diff so the public copy stays current.

### Subcommands

`run-dag` is what disputatio uses 99% of the time. The lower-level commands (`start`, `wait`, `result`) exist for ad-hoc agent calls. Full reference:

```bash
python3 vendor/agent_ctl.py <subcommand> --help
```
