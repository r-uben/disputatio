---
name: gemini
description: Query Gemini (via Antigravity CLI) for second opinions, web research, analysis, or debate
---

# Ask Gemini (Antigravity CLI)

Query Google's **Antigravity CLI** (`agy`, v1.0+) for second opinions, analysis, or debate. Antigravity is a full coding agent — the successor to Gemini CLI — sharing the same harness as the Antigravity 2.0 desktop app and the same conversation store under `~/.gemini/config/projects/`.

Conversations are **stateful**: every prompt creates a conversation in the Antigravity store and can be resumed natively with `agy -c` (most recent) or `agy --conversation <ID>` (specific).

## Hard rules (read these first)

**Non-interactive only.** Always invoke `agy -p "<prompt>"` (print mode) from the skill — never `-i`/`--prompt-interactive`, never bare `agy` (which would open a TUI). `-p` runs the prompt headless and prints the final response to stdout — nothing else.

**Timeout.** `agy -p` defaults to a 5-minute internal timeout (`--print-timeout 5m0s`). Bash's default timeout is 120s, so a non-trivial query (web research, code review, deep reasoning) WILL exceed it. Two safe patterns:

- **Short prompts (< ~90s expected)**: call `agy -p "..."` inline via Bash with `timeout: 120000` (Bash default). Fine for quick fact checks.
- **Anything else**: call with `run_in_background: true` on the Bash tool, then wait for the harness notification. Also bump `--print-timeout` if you expect more than 5 min: `agy -p "..." --print-timeout 15m`.

Never poll with visible `for/sleep` loops — they spam the transcript.

**Resume on follow-ups.** Whenever the user signals continuation ("ask again", "follow up", "what did it find?", "revise that") and a recent conversation exists, resume with `agy -c -p "<follow-up>"` instead of starting fresh. Note the **`-c -p` combination is required** — `agy -c` alone (no `-p`) opens an interactive TUI and fails non-interactively with a TTY error. `-c` continues the most recent conversation; `-p` keeps it headless.

**Resumed output includes the full history.** `agy -c -p "..."` prints every prior assistant turn (one per line) followed by the new response. To extract just the latest reply, pipe through `tail -1`. Fresh `agy -p "..."` only prints the single response and needs no filter.

## Quick reference

```bash
# Fresh single-shot query (default: Gemini 3.5 Flash (High), 5 min timeout)
agy -p "Your prompt here"

# Long-running query — bump the print timeout
agy -p "Deep research task" --print-timeout 20m

# Continue the most recent conversation (headless — note the -p)
agy -c -p "Follow-up that builds on the prior turn" | tail -1

# Continue a specific conversation by ID
agy --conversation 1381f7e3-4b78-4547-b28b-ba5f7b8bd222 -p "Follow-up" | tail -1

# Give agy access to extra directories (workspace context)
agy -p "Review @./src/main.py" --add-dir /path/to/repo

# Auto-approve all tool calls (use with care — agy can run shell commands)
agy -p "Analyze repo and write a report" --dangerously-skip-permissions

# Sandboxed run (restrict terminal access during the session)
agy -p "Untrusted exploration task" --sandbox
```

## Full flag list

```
--add-dir                       Add a directory to the workspace (repeatable)
-c, --continue                  Continue the most recent conversation
--conversation <ID>             Resume a specific conversation by ID
--dangerously-skip-permissions  Auto-approve all tool permission requests
-i, --prompt-interactive        Run an initial prompt then continue interactively (DON'T USE from this skill)
--log-file <PATH>               Override CLI log file path
-p, --print, --prompt           Run a single prompt non-interactively and print the response
--print-timeout <DUR>           Timeout for print mode wait (default 5m0s)
--sandbox                       Run in a sandbox with terminal restrictions enabled
```

Subcommands: `changelog`, `install`, `plugin` (alias `plugins`), `update`. Rarely needed from the skill.

## Continuing a session (follow-ups)

Default to **fresh sessions** for new topics. **Resume** when the user signals continuation and the previous Antigravity conversation is recent (within the working session).

```bash
# Most-recent continue — the common case (tail -1 strips the prior-turn echo)
agy -c -p "Follow-up question building on prior context" | tail -1

# Specific conversation
agy --conversation <UUID> -p "Follow-up" | tail -1
```

Conversation IDs live in `~/.gemini/config/projects/<UUID>.json`. If you need to recover one, list the most recently modified file there. The two products (Antigravity CLI and Antigravity 2.0) share this store — conversations started in the CLI are also visible inside the desktop app via the `@conversation` dropdown (and vice versa, but only on explicit import).

Heuristic for resume vs start fresh:

- **Resume** (`agy -c -p "..." | tail -1`) on any short follow-up where the topic is clearly the same.
- **Start fresh** (`agy -p "..."`) when the topic changed, or the prior session is from a different conversation context.
- **Ask** when ambiguous — never silently resume an unrelated conversation.

## Models

Antigravity does **not** expose a `-m`/`--model` flag at the CLI. The reasoning model is selected via the in-app `/model` picker (interactively) **or** via the `agy-set-model` pty wrapper (programmatically). It is **sticky in encrypted global state** — once switched, the selection persists across all future `agy` calls until changed again.

```bash
agy-set-model --list                      # show known model names
agy-set-model "Gemini 3.1 Pro (High)"     # switch (idempotent — no-op if already on target)
agy-set-model "Gemini 3.5 Flash (High)"   # switch back
```

`agy-set-model` is a TUI driver — it spawns `agy`, navigates the `/model` picker, commits, and verifies. Takes ~6–10s. Fails loud if the picker doesn't render. Required by `agent_ctl` for per-phase model routing (e.g. disputatio); also useful for ad-hoc switches before invoking this skill.

Currently available reasoning models (live selector):

| Model | Use For |
|-------|---------|
| **Gemini 3.5 Flash (High)** | Default — strong reasoning at Flash speed/cost |
| Gemini 3.5 Flash (Medium) | Same model, lower thinking budget — faster, cheaper |
| Gemini 3.1 Pro (High) | Deep research, complex reasoning, code review, debate |
| Gemini 3.1 Pro (Low) | Pro reasoning at reduced thinking budget |
| Claude Sonnet 4.6 (Thinking) | Cross-vendor second opinion (Anthropic) |
| Claude Opus 4.6 (Thinking) | Cross-vendor deep-reasoning second opinion (Anthropic) |
| GPT-OSS 120B (Medium) | Open-weights frontier model for breadth/diversity |

**Practical implication for this skill**: programmatic switching IS possible via `agy-set-model` (above). If a task needs Pro-grade reasoning, either (a) call `agy-set-model "Gemini 3.1 Pro (High)"` before running the query, or (b) tell the user to switch manually via the app's `/model`. Either way, the selection is sticky for all subsequent calls until changed again. There is still no `-m` flag at the CLI level — don't fabricate one.

Other (non-customizable) models in the stack: **Nano Banana 2** is used internally for generative image tasks (UI mockups, diagrams).

## Auth

Antigravity authenticates via **Google AI Pro OAuth**, handled by the Antigravity desktop app on first launch. The CLI inherits the same credentials — no API keys, no env vars. If the CLI ever prompts for re-auth, open the Antigravity desktop app once and re-sign-in there.

## File & multimodal context

Two ways to give `agy` files:

1. **`@` references inside the prompt** — works for files inside the current `cwd` or any `--add-dir` workspace:
   ```bash
   agy -p "Review @./src/main.py for bugs" --add-dir /path/to/repo
   agy -p "Summarize @./src/ architecture" --add-dir /path/to/repo
   agy -p "Describe @screenshot.png"
   ```

2. **`--add-dir`** to expand the workspace beyond `cwd` (repeatable):
   ```bash
   agy -p "Compare these two repos" --add-dir /path/repo-a --add-dir /path/repo-b
   ```

Antigravity is multimodal — `@image.png`, `@doc.pdf`, and screenshots all work as references.

## Web search & research

Antigravity inherits Google Search grounding from the underlying Gemini models — this auto-triggers when the model decides current information is needed. No flag is required. This is the primary reason to prefer `agy` over local-only reasoning agents.

```bash
# Auto-grounded current-events query
agy -p "What are the latest changes to Basel IV implementation timelines?"

# Deep research with auto-approve (agent will browse, search, synthesize)
agy -p "Research semiconductor supply chain trends, gather multiple sources" \
    --dangerously-skip-permissions --print-timeout 20m
```

For research that requires the agent to drive a browser, use `/browser` inside an interactive session — not available from `-p` print mode.

## When to use Gemini (Antigravity)

- **Web research** (primary advantage): live Google Search grounding
- **Deep research reports**: long-horizon agent tasks with `--print-timeout 20m` and `--dangerously-skip-permissions`
- **Second opinion**: cross-check analysis (especially via Claude Sonnet/Opus models inside Antigravity for a real cross-vendor read)
- **Multimodal**: screenshots, PDFs, images via `@`
- **Debate**: present two sides, ask Antigravity to argue one

## Response handling

Fresh `agy -p "..."` prints **only the model's final response** to stdout — no banner, no progress, no JSON wrapper. Pipe-safe. Do not filter.

Resumed `agy -c -p "..."` (and `--conversation <ID> -p`) prints every prior assistant turn one per line, with the new response last. Pipe through `tail -1` to extract just the latest reply. There is no JSON or banner noise — only assistant text — so `tail -1` is safe.

1. **Synthesize** — summarize key insights, don't paste raw output back to the user verbatim
2. **Compare** — contrast with your own analysis, note agreements/disagreements
3. **Evaluate** — Antigravity can be wrong; apply critical judgment
4. **Cite** — say "Antigravity (Gemini 3.5 Flash) suggests..." when reporting its views, since the actual model depends on the user's `/model` setting

## Migration from the old Gemini CLI skill

For users coming from the old `gemini -p` / `agent-ctl` workflow:

| Old (gemini CLI + agent-ctl) | New (agy) |
|---|---|
| `agent_ctl.py start gemini "..."` | `agy -p "..."` (with `run_in_background: true` for long queries) |
| `agent_ctl.py send-or-start gemini "..."` | `agy -c -p "..." \| tail -1` (most recent — `-c -p` required for headless) |
| `agent_ctl.py result <id>` | (not needed — `agy -p` prints directly) |
| `agent_ctl.py kill <id>` | `pkill -f "agy -p"` (rare; agy exits cleanly on `--print-timeout`) |
| `-m gemini-3.1-pro-preview` | `agy-set-model "Gemini 3.1 Pro (High)"` before invoking |
| `--flags -y` | `--dangerously-skip-permissions` |
| `--flags -s` | `--sandbox` |
| `gemini --resume <UUID>` | `agy --conversation <UUID> -p "..."` |
| `gemini --list-sessions` | Read `~/.gemini/config/projects/` (mtime-sorted) |

The old Gemini CLI (`gemini`) is still installed at `/opt/homebrew/lib/node_modules/@google/gemini-cli/` and remains usable as a fallback for any agent_ctl-based workflows still tied to it (e.g. `disputatio`). But for `/gemini` invocations, prefer `agy`.
