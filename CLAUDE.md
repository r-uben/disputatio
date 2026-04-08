## Disputatio

High-precision academic paper review via multi-agent dialectic debate. This is a Claude Code skill, not a Python package -- Claude Code is the runtime.

### How it works

`/disputatio paper.pdf` triggers a three-phase pipeline:

1. **Discovery** -- all three agents (Claude, Codex, Gemini) read the paper independently and find candidate issues. Results are merged and deduplicated
2. **Dialectic rounds** -- each issue enters a rotating debate: prosecutor, defender, synthesizer. Roles rotate across agents each round. The synthesis becomes the new input, not a verdict
3. **Final synthesis** -- surviving issues are rendered as structured reviewer comments with uncertainty preserved

### Structure

```
disputatio/
├── SKILL.md                  # skill definition -- the full protocol
├── CLAUDE.md                 # this file
├── templates/
│   ├── discover.md           # prompt for discovery phase (codex/gemini)
│   ├── prosecute.md          # prompt for prosecutor role
│   ├── defend.md             # prompt for defender role
│   └── synthesize.md         # prompt for synthesizer role
├── references/
│   └── criteria.md           # what counts as a valid issue
└── .gitignore
```

Runtime workspace (created per review):
```
workspace/<paper-slug>/
├── paper.md                          # parsed paper
├── checkpoint.json                   # resumable state
├── discovery/
│   ├── claude/issue_NNN.json         # claude's findings
│   ├── codex/issue_NNN.json          # codex's findings
│   └── gemini/issue_NNN.json         # gemini's findings
├── issues/issue_NNN.json             # merged issues
├── rounds/
│   └── issue_NNN/
│       ├── round_1_prosecute.json
│       ├── round_1_defend.json
│       ├── round_1_synthesize.json
│       └── ...
└── final.json                        # surviving issues
```

### Key decisions

- **No Python** -- Claude Code orchestrates everything. Agents communicate via files
- **Dialectic, not adjudication** -- synthesis produces refined understanding, not keep/drop verdicts
- **All models, all roles** -- every agent takes every role across rounds. No fixed assignments
- **Parallel discovery** -- all three models scan independently, preventing single-model blind spots
- **Convergence, not one-shot** -- issues are debated until the synthesis stabilizes or budget cap (3 rounds)
- **Fast path** -- unanimously weak issues die in round 1. Only contested issues get full rotation
- **Fail-safe** -- if an agent dies, default to KEEP. Don't lose findings to infrastructure issues
- **Checkpointing** -- every round is saved. Resume from where you left off

### Prerequisites

- `codex` CLI installed and authenticated (ChatGPT Pro)
- `gemini` CLI installed and authenticated (Google OAuth)
- `agent-ctl` (`~/.claude/skills/agent_ctl.py`)
