## Disputatio

High-precision academic paper review via multi-agent adversarial debate. This is a Claude Code skill, not a Python package — Claude Code is the runtime.

### How it works

`/disputatio paper.pdf` triggers a three-phase pipeline:

1. **Discovery** — Claude Code reads the paper passage by passage, finds candidate issues
2. **Debate** — each comment is challenged by `/codex` (GPT), then judged by `/gemini` (Google). Independent model families prevent correlated errors
3. **Merge** — deduplicate survivors, write final output

### Structure

```
disputatio/
├── SKILL.md                  # skill definition — the full protocol
├── CLAUDE.md                 # this file
├── templates/
│   ├── challenge.md          # prompt for /codex (challenger)
│   └── verdict.md            # prompt for /gemini (judge)
├── references/
│   └── criteria.md           # what counts as a valid issue
└── .gitignore
```

Runtime workspace (created per review):
```
workspace/<paper-slug>/
├── paper.md                  # parsed paper
├── checkpoint.json           # resumable state
├── comments/comment_NNN.json # discovery output
├── challenges/comment_NNN.json # codex challenges
├── verdicts/comment_NNN.json   # gemini verdicts
└── final.json                # surviving comments
```

### Key decisions

- **No Python** — Claude Code orchestrates everything. Agents communicate via files
- **File-based coordination** — reliable, checkpointable, debuggable
- **Model independence** — challenger (GPT) and judge (Gemini) are different from discoverer (Claude). This is the whole point
- **Fail-safe** — if an agent dies, default to KEEP. Don't lose findings to infrastructure issues
- **Checkpointing** — every debate round is saved. Resume from where you left off

### Prerequisites

- `codex` CLI installed and authenticated (ChatGPT Pro)
- `gemini` CLI installed and authenticated (Google OAuth)
- `agent-ctl` (`~/.claude/skills/agent_ctl.py`)
