# vendor/

Vendored third-party (or other-repo) dependencies that disputatio relies on.

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
