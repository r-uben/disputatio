# OpenCode transport

OpenCode (`opencode` CLI) is a **gateway** that routes to many model providers through one argv surface. It is the preferred way to add Kimi, Ollama-served local models, OpenRouter-routed models, or anything else that does not ship a first-party CLI — one transport integration gives disputatio access to the full OpenCode catalogue.

## Invocation

Non-interactive mode (what disputatio uses):

```
opencode run -m <provider>/<model> [--agent <name>] [other flags] "<prompt>"
```

- The prompt is a **positional** argument (variadic in the upstream CLI), passed last. Earlier drafts of this doc used `--prompt`, which is wrong for `opencode run` (that flag belongs to the default tui subcommand). For prompts larger than ~10 KB, `agent_ctl.py` writes the prompt to a temp file, drops the trailing positional from the argv, and pipes the file on stdin — `opencode run` reads stdin when no message positional is present.
- `-m <provider>/<model>` is REQUIRED in disputatio. Never rely on the default; always pass it explicitly from the ticket. This also forces the orchestrator to make the family assignment consciously.
- Authentication is managed by OpenCode itself (`opencode providers` / `opencode auth`). `agent_ctl.py` does not unset provider-specific env vars for this transport — if a user has `OPENAI_API_KEY` set and picks `openai/gpt-4o`, OpenCode uses that key. This is intentional: OpenCode is the source of truth for provider credentials.

## Model string conventions

Every `-m` value is `<routing_provider>/<model_id>`. The routing provider is whoever is answering the HTTP request; the model_id identifies the actual model. Examples:

| Invocation | Routing provider | Actual model | Ticket `family` |
|---|---|---|---|
| `-m anthropic/claude-sonnet-4-6` | anthropic | Claude Sonnet 4.6 | `anthropic` |
| `-m openai/gpt-4o` | openai | GPT-4o | `openai` |
| `-m moonshot/k2.5` | moonshot | Kimi K2.5 | `moonshot` |
| `-m groq/llama-3.3-70b-versatile` | groq | Meta Llama 3.3 70B | `meta` |
| `-m openrouter/anthropic/claude-sonnet-4-6` | openrouter | Anthropic Claude Sonnet 4.6 | `anthropic` |
| `-m together/qwen2.5-72b-instruct` | together | Alibaba Qwen 2.5 | `alibaba` |
| `-m ollama/qwen2.5:32b` | ollama (local) | Alibaba Qwen 2.5 | `alibaba` |

Rule: **family follows the model, not the routing provider.** See `templates/agents/families.md` for the resolution procedure.

## Ticket shape

A discovery ticket for OpenCode looks like this:

```json
{
  "id": "discover_opencode_kimi_m5",
  "type": "discover",
  "agent": "opencode",
  "model": "moonshot/k2.5",
  "family": "moonshot",
  "flags": {},
  "prompt_path": "_artifacts/prompts/discover_opencode_kimi_m5.md",
  "inputs": [
    "_paper/paper.md",
    "_artifacts/json/orient_opencode_kimi.json"
  ],
  "outputs": ["_artifacts/json/discover_opencode_kimi_m5.json"],
  "depends_on": ["orient_opencode_kimi"],
  "status": "pending",
  "timeout_s": 900
}
```

Notes:

- `agent` is always `opencode`. The specific model lives in `model`.
- `family` is REQUIRED. The launcher rejects OpenCode tickets without it.
- Ticket IDs should include the short-name of the model for human-readable logs, e.g. `discover_opencode_kimi_m5` rather than `discover_opencode_m5`. When three OpenCode models run discovery in parallel, the ticket IDs disambiguate them.
- `orient_opencode_<short>` tickets come in matching pairs — each OpenCode-routed model gets its own paper map (model independence applies across model architectures, not across `-m` strings for the same underlying model).

## Flags the builder translates

`build_opencode_cmd` reads `ticket["flags"]` (a free-form dict) and translates known keys onto the OpenCode argv. Current translations:

| `flags` key | OpenCode argument | Notes |
|---|---|---|
| `agent` | `--agent <name>` | OpenCode's built-in agent personas; rarely used in disputatio |
| `log_level` | `--log-level <DEBUG\|INFO\|WARN\|ERROR>` | Useful when triaging a failing transport |
| `pure` | `--pure` | Run without external plugins; use when plugin behaviour is suspected of polluting outputs |
| `variant` | `--variant <high\|max\|minimal>` | Provider-specific reasoning effort (the OpenCode equivalent of codex's `model_reasoning_effort`) |
| `thinking` | `--thinking` | Show thinking blocks in the output |
| (other keys) | ignored with stderr warning | Fail visibly rather than silently pretend to apply |

Unknown flags do not block launch; they print a single-line warning to the session log. If a flag matters for correctness, promote it to an explicit field here and add the translation in `build_opencode_cmd`.

## Running multiple models in one review

Disputatio's cross-model design expects 3 agents of distinct families. A typical 3-agent OpenCode-only configuration:

- `opencode` + `anthropic/claude-sonnet-4-6` (family: `anthropic`)
- `opencode` + `openai/gpt-4o` (family: `openai`)
- `opencode` + `moonshot/k2.5` (family: `moonshot`)

Each gets its own orient ticket (`orient_opencode_claude`, `orient_opencode_gpt4o`, `orient_opencode_kimi`) and its own discovery sweeps. The short-name in the ticket ID is orchestrator-chosen and only needs to be unique within the review. In the merge step, cross-family count is 3 because there are three distinct `family` values across the discovery JSONs.

## Known caveats

- **OpenCode may inject its own system prompt.** The first opencode-backed discovery run on a paper should be smoke-tested against a native CLI for the same family (e.g. compare `opencode run -m anthropic/claude-sonnet-4-6` outputs to direct `claude` outputs on one discovery pass). If OpenCode is reshaping prompts in ways that degrade finding quality, prefer the native CLI.
- **Rate limits are the underlying provider's.** Anthropic 529s, OpenAI 429s, etc. still happen through OpenCode. `agent_ctl.py`'s fallback-on-429 logic needs a per-ticket `fallback_model` if this becomes common — not wired in yet; out of scope for the first opencode landing.
- **Local models via OpenCode (`ollama/...`) go through OpenCode AND Ollama.** That is two layers of indirection vs calling `ollama` directly. If there is no reason to stay in the OpenCode flow, prefer the `ollama` transport for local models.
