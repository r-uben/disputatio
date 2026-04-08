---
name: disputatio
description: High-precision academic paper review via multi-agent adversarial debate
---

# Disputatio

Review an academic paper using adversarial debate between independent AI agents.

## Usage

```
/disputatio <path-to-paper>
```

## Protocol

### Phase 1 — Discovery

Read the paper and find candidate issues passage by passage. For each passage:

1. Read the passage + surrounding context (±3 passages)
2. Maintain a running summary of definitions, notation, equations, and key claims
3. Find concrete, verifiable errors (wrong math, inconsistent notation, logical contradictions, parameter mismatches, unjustified claims)
4. Write each comment to `workspace/comments/comment_NNN.json`

Do NOT flag style, readability, or subjective issues. Only flag things that are concretely wrong or misleading.

### Phase 2 — Adversarial Debate

For each candidate comment, run a debate:

1. **Challenge** — send the comment + paper context to `/codex`. Codex tries to REFUTE the criticism: find resolving context, cite conventions, show it's a misreading. Codex writes its challenge to `workspace/challenges/comment_NNN.json`

2. **Verdict** — send the comment + challenge + paper context to `/gemini`. Gemini renders an impartial verdict: keep, drop, or rewrite. Gemini writes its verdict to `workspace/verdicts/comment_NNN.json`

3. **Record** — read both files, update `workspace/checkpoint.json`

If an agent fails or times out, retry once. If it fails again, default to KEEP (don't lose findings to infrastructure issues).

### Phase 3 — Merge

Deduplicate surviving comments. If two comments flag the same underlying error, merge them (keep the stronger explanation). Write final output to `workspace/final.json`.

## Workspace structure

```
workspace/<paper-slug>/
├── paper.md                  # parsed paper text
├── checkpoint.json           # resumable session state
├── comments/
│   ├── comment_001.json      # {"title", "quote", "explanation", "comment_type", "paragraph_index"}
│   └── ...
├── challenges/
│   ├── comment_001.json      # codex's counter-argument
│   └── ...
├── verdicts/
│   ├── comment_001.json      # {"decision": "keep|drop|rewrite", "reason": "..."}
│   └── ...
└── final.json                # merged surviving comments
```

## Agent routing

| Role | Agent | Why |
|------|-------|-----|
| Discoverer | Claude Code (you) | Direct paper access, progressive reading |
| Challenger | `/codex` (GPT-5.4) | Independent model family, strong at finding counter-evidence |
| Judge | `/gemini` (Gemini 2.5 Pro) | Independent model family, good at weighing arguments |

The key property is **model independence**: the challenger and judge are different architectures from the discoverer. This prevents correlated errors where the same model endorses its own mistakes.

## Agent communication

Use `agent-ctl` to manage sessions:

```bash
A="python3 ~/.claude/skills/agent_ctl.py"

# Start challenger
$A start codex "PROMPT" --cwd <workspace> --flags -s read-only --timeout 300

# Start judge
$A start gemini "PROMPT" --cwd <workspace> --timeout 300

# Check status
$A status

# Get result
$A result <session-id>
```

Each agent is instructed to write its output to a specific file in the workspace. Claude Code polls for the file to appear, then reads it.

## Checkpointing

After each debate round completes, update `checkpoint.json` with:
- Which comments have been challenged
- Which verdicts have been rendered
- Which comments survived

If the session is interrupted, read `checkpoint.json` and resume from the last completed debate.

## Prompt templates

Challenge and verdict prompt templates are in `templates/`.

## Review criteria

The criteria for what constitutes a valid issue are in `references/criteria.md`.
