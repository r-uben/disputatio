---
name: gemini
description: Query Gemini for second opinions, web research, analysis, or debate
---

# Ask Gemini

Query Gemini CLI (v0.28+) for second opinions, analysis, or debate. Gemini CLI is a full coding agent (like Claude Code) — not just a chat API.

Sessions are **stateful**: agent-ctl persists them in `~/.claude/agent-sessions.json` and Gemini resumes natively (`gemini --resume <UUID>`). Default to fresh sessions, but resume on follow-ups (see "Continuing a session" below).

## Hard rules (read these first)

**Showing results to the user.** Print exactly `agent_ctl.py result <id>`. Do **not** pipe through `grep`, `tail`, `head`, `sed`, or `awk`. The output is already cleaned — any filter you add strips real content and is what makes the visible output look like garbage. If `result` returns "(still running — no result yet)", wait; do not fall back to scraping the raw stdout log.

**Polling.** Never run visible `for i in $(seq …); do sleep 60; …; done` loops — they spam status lines into the transcript. The Bash tool's default timeout is 120s and a typical Gemini query (web research, code review, debate) can easily exceed that, so a naked `wait` call will time out *before* gemini finishes and look like a hang. Two safe patterns:

- `agent_ctl.py wait <id> --max-wait 90` — bounded wait; exits 2 with "still running" before busting Bash's cap. Re-call until the session finishes.
- `run_in_background: true` on a plain `agent_ctl.py wait <id>` — the harness notifies you when it returns.

Use the second when you want to do other work while gemini runs. Use the first when you need to feed the result back into your next step.

**Resume by default.** Whenever a recent gemini session (≤ 2 hours, same `cwd`) exists, use `send-or-start`, not `start` — even for bare prompts like "does gemini agree?", "ask again", "follow up". Only use `start` when (a) no recent session exists, (b) the topic clearly changed, or (c) `send-or-start` reports ambiguity (then surface the candidates and ask).

## Multi-account routing (vox)

If `$CLAUDE_CONFIG_DIR` is set to a non-default path matching `~/.claude-<suffix>` (e.g. `~/.claude-vox`), prefix every direct `gemini` invocation with `GEMINI_CLI_HOME="$HOME/.gemini-<suffix>"` so the secondary Gemini account is used. `agent-ctl` does this automatically; the raw `gemini -p` fallbacks below do NOT — add the env var manually when running under a non-default config dir.

## agent-ctl (preferred)

Use `agent-ctl` for all Gemini interactions. It runs Gemini in the background so you stay in control — no blocking, progress checking, cancellation.

```bash
A="python3 ~/.claude/skills/agent_ctl.py"

# Start a session (returns immediately)
$A start gemini "Your prompt here"                                   # default: gemini-3.1-pro-preview, 300s timeout
$A start gemini "Quick question" -m gemini-3.1-flash-lite-preview    # fast model
$A start gemini "Analyze code" --cwd /path/to/repo                  # set working dir
$A start gemini "Explore project" --timeout 600 --flags -y          # agent mode (auto-approve)

# Monitor
$A status                   # list all sessions (codex + gemini)
$A status --json            # machine-readable for routing decisions
$A check 01                 # tail output of session 01 — see note on buffering below

# Get results
$A result 01                # get final response

# Control
$A kill 01                  # kill a hung session
$A cleanup --agent gemini   # kill all gemini sessions
$A cleanup                  # kill ALL sessions (both agents)
```

## Continuing a session (follow-ups)

Default to **fresh sessions** for new topics. **Resume** when the user signals continuation — "follow up", "ask gemini again", "continue", "revise that", "what did it find?" — and there is a unique recent gemini session in the same `cwd`.

The safe primitive is `send-or-start`: it resumes a unique match, starts a new session if none exists, and **fails on ambiguity** rather than silently picking the wrong session.

```bash
$A send-or-start gemini "Follow-up question building on prior context" --cwd /path/to/repo
# 0 matches  → starts new session
# 1 match    → sends as turn N+1 (preserves full context)
# >1 matches → exits non-zero with candidate list; ASK the user which to resume
```

If `send-or-start` reports ambiguity, surface the candidate list to the user and let them pick — never auto-resolve. To bypass that and grab the most recent match anyway: `--latest`.

Heuristic for resume vs start fresh:
- **Resume** (call `send-or-start`) whenever a gemini session in the same `cwd` finished within the last ~2 hours — this is the default for any short follow-up prompt.
- **Start fresh** when the topic clearly changed, the user is in a different repo, or the last session is stale (default cutoff: 7 days; tune via `--max-age-hours`).
- **Ask** when ambiguous — multiple plausible matches, or unclear whether the user is following up or starting over.

Direct send (when you already know the session id):

```bash
$A send 01 "Follow-up that builds on the earlier turn"
```

### Extra flags via `--flags`

Pass any `gemini` flags after `--flags`:

```bash
$A start gemini "task" --flags -y                          # agent mode (auto-approve)
$A start gemini "task" --flags -y -s                       # agent mode + sandbox
$A start gemini "task" --flags --approval-mode plan        # read-only exploration
$A start gemini "Review @./src/" --flags -y                # with file references
```

## Buffering: `check` is not a stream

Gemini's `-o text` mode block-buffers stdout when not writing to a TTY — empirically, the entire response lands in a single write at process exit, not line-by-line. So `agent_ctl.py check <id>` shows essentially nothing useful during execution (just the startup ripgrep warning) and the real answer appears at the moment the session goes from RUNNING to DONE. Don't try to use `check` for live progress. Wait for the session to finish, then call `result`.

(This is a deliberate trade-off: agent_ctl previously wrapped agents in `script -q /dev/null` to defeat buffering, but that created a fresh session for gemini's node worker which then escaped agent_ctl's process group and survived `kill` on timeout — leaking processes that held OAuth state and polluted `gemini --list-sessions`. Losing live streaming is the right price.)

## Auth

Gemini CLI uses **OAuth cached credentials** (not API keys). agent-ctl automatically unsets conflicting env vars (`GOOGLE_API_KEY`, `GEMINI_API_KEY`).

## Direct commands (fallback only)

If agent-ctl doesn't work for some reason:

```bash
env -u GOOGLE_API_KEY -u GEMINI_API_KEY gemini -p "YOUR QUESTION" -m gemini-3.1-pro-preview -o text --skip-trust 2>/dev/null
```

`--skip-trust` is required for any cwd that isn't under a folder listed in `~/.gemini/trustedFolders.json`. agent-ctl adds it conditionally for you (only when needed); the direct fallback above hard-codes it because there's no way to detect at the shell level.

## File & Multimodal Context

Gemini supports `@` references for files, images, PDFs, and directories:

```bash
$A start gemini "Review @./src/main.py for bugs" --cwd /path/to/repo
$A start gemini "Summarize @./src/ architecture" --cwd /path/to/repo --flags -y
$A start gemini "Describe @screenshot.png" --cwd /path/to/dir
```

## Web Search & Research

Gemini has built-in Google Search grounding — auto-triggers when queries need current information. This is Gemini's killer advantage.

```bash
# Auto-grounded web search
$A start gemini "What are the latest changes to Basel IV implementation timelines?"

# Deep research with agent mode
$A start gemini "Research semiconductor supply chain trends, search multiple sources" --flags -y --timeout 600
```

## Models

| Model | Use For |
|-------|---------|
| `gemini-3.1-pro-preview` | Complex reasoning, deep research, code review, debate — **default** |
| `gemini-3-flash-preview` | Mid-tier — Pro-level intelligence at Flash speed/cost |
| `gemini-3.1-flash-lite-preview` | Quick questions, fast web searches, simple lookups |
| `gemini-2.5-pro` | Stable fallback when preview is rate-limited |
| `gemini-2.5-flash` | Fast stable — best price-performance for high-volume tasks |

## When to Use Gemini

- **Web research** (primary advantage): live Google Search grounding
- **Deep research reports**: agent mode to search, synthesize, write
- **Second opinion**: cross-check analysis
- **Multimodal**: screenshots, PDFs, images via `@`
- **Debate**: present two sides, ask Gemini to argue one

## Response Handling

1. **Synthesize** — summarize key insights, don't paste raw output
2. **Compare** — contrast with your own analysis, note agreements/disagreements
3. **Evaluate** — Gemini can be wrong; apply critical judgment
4. **Cite** — say "Gemini suggests..." when reporting its views
