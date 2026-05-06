---
name: codex
description: Query OpenAI GPT via Codex CLI for second opinions, code review, or analysis
---

# Codex

Query OpenAI GPT via Codex CLI for second opinions, code review, or analysis. Codex CLI is a full coding agent (like Claude Code) — not just a chat API.

Sessions are **stateful**: agent-ctl persists them in `~/.claude/agent-sessions.json` and Codex resumes natively (`codex exec resume --last`). Default to fresh sessions, but resume on follow-ups (see "Continuing a session" below).

## Hard rules (read these first)

**Showing results to the user.** Print exactly `agent_ctl.py result <id>`. Do **not** pipe through `grep`, `tail`, `head`, `sed`, or `awk`. The file is already cleaned via `--output-last-message` — any filter you add strips real content and is what makes the visible output look like garbage. If `result` returns "(still running — no result yet)", wait; do not fall back to scraping the raw stdout log.

**Polling.** Never run visible `for i in $(seq …); do sleep 60; …; done` loops — they spam status lines into the transcript. Use `agent_ctl.py wait <id>` (blocks until done) or `run_in_background` a single poll. The user should see the result, not the wait.

**Resume by default.** Whenever a recent codex session (≤ 2 hours, same `cwd`) exists, use `send-or-start`, not `start` — even for bare prompts like "does codex agree?", "ask again", "follow up". Only use `start` when (a) no recent session exists, (b) the topic clearly changed, or (c) `send-or-start` reports ambiguity (then surface the candidates and ask).

## Multi-account routing (vox)

If `$CLAUDE_CONFIG_DIR` is set to a non-default path matching `~/.claude-<suffix>` (e.g. `~/.claude-vox`), prefix every direct `codex` invocation with `CODEX_HOME="$HOME/.codex-<suffix>"` so the secondary Codex account is used. `agent-ctl` does this automatically; the raw `codex exec` fallbacks below do NOT — add the env var manually when running under a non-default config dir.

## agent-ctl (preferred)

Use `agent-ctl` for all Codex interactions. It runs Codex in the background so you stay in control — no blocking, progress checking, cancellation.

```bash
A="python3 ~/.claude/skills/agent_ctl.py"

# Start a session (returns immediately)
$A start codex "Your prompt here"                                    # default: gpt-5.4, 300s timeout
$A start codex "Frontier reasoning" -m gpt-5.5                      # frontier model
$A start codex "Quick question" -m gpt-5.1-codex-mini               # fast model
$A start codex "Analyze code" --cwd /path/to/repo                   # set working dir
$A start codex "Fix tests" --timeout 600 --flags --full-auto        # agentic mode

# Monitor
$A status                   # list all sessions (codex + gemini)
$A status --json            # machine-readable for routing decisions
$A check 01                 # tail output of session 01
$A check 01 --tail 100      # more lines

# Get results
$A result 01                # clean final response (via --output-last-message)

# Control
$A kill 01                  # kill a hung session
$A cleanup --agent codex    # kill all codex sessions
$A cleanup                  # kill ALL sessions (both agents)
```

## Continuing a session (follow-ups)

Default to **fresh sessions** for new topics. **Resume** when the user signals continuation — "follow up", "ask codex again", "continue", "revise that", "what did it find?" — and there is a unique recent codex session in the same `cwd`.

The safe primitive is `send-or-start`: it resumes a unique match, starts a new session if none exists, and **fails on ambiguity** rather than silently picking the wrong session.

```bash
$A send-or-start codex "Follow-up question building on prior context" --cwd /path/to/repo
# 0 matches  → starts new session
# 1 match    → sends as turn N+1 (preserves full context)
# >1 matches → exits non-zero with candidate list; ASK the user which to resume
```

If `send-or-start` reports ambiguity, surface the candidate list to the user and let them pick — never auto-resolve. To bypass that and grab the most recent match anyway: `--latest`.

Heuristic for resume vs start fresh:
- **Resume** (call `send-or-start`) whenever a codex session in the same `cwd` finished within the last ~2 hours — this is the default for any short follow-up prompt.
- **Start fresh** when the topic clearly changed, the user is in a different repo, or the last session is stale (default cutoff: 7 days; tune via `--max-age-hours`).
- **Ask** when ambiguous — multiple plausible matches, or unclear whether the user is following up or starting over.

Direct send (when you already know the session id, e.g. just got it from `start` or `status`):

```bash
$A send 01 "Follow-up that builds on the earlier turn"
```

### Extra flags via `--flags`

Pass any `codex exec` flags after `--flags`:

```bash
$A start codex "task" --flags --full-auto              # auto-approve + sandbox
$A start codex "task" --flags -s read-only             # read-only sandbox
$A start codex "task" --flags -i screenshot.png        # attach image
$A start codex "task" --flags -c model_reasoning_effort=high   # raise reasoning effort
```

## Auth

Codex uses **ChatGPT OAuth** (Pro subscription). No API keys. Auth is stored in `~/.codex/auth.json`. agent-ctl automatically unsets conflicting env vars.

If auth breaks: `codex logout && codex login` (browser OAuth, NOT `--device-auth`).

## Direct commands (fallback only)

If agent-ctl doesn't work for some reason:

```bash
(unset OPENAI_API_KEY OPENAI_BASE_URL CODEX_API_KEY; codex exec --skip-git-repo-check "YOUR QUESTION")
```

## Code Review (direct only — not via agent-ctl)

```bash
(unset OPENAI_API_KEY OPENAI_BASE_URL CODEX_API_KEY; codex review)
(unset OPENAI_API_KEY OPENAI_BASE_URL CODEX_API_KEY; codex review --diff-target main)
```

## Model Selection

| Model | Best For |
|-------|----------|
| `gpt-5.5` | Frontier model — complex coding, research, hardest reasoning |
| `gpt-5.4` | Strong everyday coding, second opinions — **default** |
| `gpt-5.4-mini` | Small, fast, cost-efficient for simpler tasks |
| `gpt-5.3-codex` | Coding-optimized (agentic file edits, exploration) |
| `gpt-5.3-codex-spark` | Ultra-fast coding |
| `gpt-5.2` | Professional work and long-running agents |
| `gpt-5.1-codex-mini` | Budget/trivial (note: doesn't support `xhigh` reasoning effort) |

Default stays `gpt-5.4`. Reach for `gpt-5.5` when the task genuinely needs frontier reasoning — it's slower and more expensive.

## Reasoning Effort

There is no dedicated CLI flag — pass it as a config override via `-c`:

```bash
$A start codex "task" --flags -c model_reasoning_effort=high
$A start codex "task" --flags -c model_reasoning_effort=xhigh
```

Valid values: `low`, `medium`, `high`, `xhigh`. Default is the model's built-in default (typically `medium`).

`xhigh` is supported by: `gpt-5.5`, `gpt-5.4`, `gpt-5.4-mini`, `gpt-5.3-codex`, `gpt-5.3-codex-spark`, `gpt-5.2`. Not supported by `gpt-5.1-codex-mini`.

Persistent default: set `model_reasoning_effort = "high"` in `~/.codex/config.toml`.

## Response Handling

1. **Synthesize** — summarize key insights, don't paste raw output
2. **Compare** — contrast with your own analysis, note agreements/disagreements
3. **Evaluate** — Codex can be wrong; apply critical judgment
4. **Cite** — say "Codex suggests..." when reporting its views
