# Transport, model, family — and why Python stays out of it

This note was revised twice (Codex, then Gemini, then a sharper Codex xhigh pass) and each round pushed the same direction: **the orchestrator knows what the launcher never will, so the launcher should stop pretending**. Below is the final design.

## The three concepts

| Concept | Question it answers | Who owns it |
|---|---|---|
| **Transport** | How does Claude invoke this agent? argv, env, stdin shape. | `AgentSpec` in `vendor/agent_ctl.py` |
| **Model** | Which specific model runs inside the transport? | The orchestrator (Claude) sets it per ticket |
| **Family** | Which org/architecture built that model? Drives cross-agent ranking weights. | The orchestrator writes it into each ticket at emit time |

For single-family transports (`codex` → always `openai`, `gemini` → always `google`, `claude` → always `anthropic`) the family is implicit in the transport and `agent_ctl.py` can fill it in. For gateway transports (`opencode`, `ollama`) the same CLI routes to many families depending on the chosen model, so the orchestrator annotates each ticket.

## Why not a Python family resolver

The first draft of this note proposed `AgentSpec.family: str | Callable[[str], str]`, `_opencode_family()` that parsed `provider/model` strings, an `_ollama_family()` that subprocess-probed `ollama show --modelfile`, and a `CallOptions` dataclass with `supported_options` validation. Every round of review surfaced fragilities:

- **Provider ≠ family for resellers.** Groq, OpenRouter, Together, Fireworks host other companies' models. `groq/llama-3.3-70b` is Meta's Llama, not "family=groq".
- **Direct providers become resellers.** Google Vertex already hosts Llama; Anthropic could tomorrow. Any static `provider → family` table silently misclassifies as soon as the model catalogue shifts.
- **Ollama display names lie.** Custom fine-tunes, HF-imported models (`hf.co/...`), and user-renamed aliases defeat prefix matching. Subprocess probes are slow (10s × N tickets) and fragile when the daemon is off.
- **`extra_flags` defeats `supported_options`.** An escape hatch that lets callers bypass validation is not validation.
- **`CallOptions` forces a second refactor.** Per-call knobs (`reasoning_effort`, `temperature`, `tool_use`, `images`) balloon the type surface with no clear upper bound.

All of these failure modes share a root cause: **the Python launcher is trying to rediscover facts the orchestrator already knows**. When Claude emits a ticket for `opencode` with `model=moonshot/k2.5`, Claude already chose that combination deliberately; having Python parse the string a second time to recover "moonshot" is redundant at best and wrong at worst.

## The actual design

### `agent_ctl.py` — transport only

`AgentSpec` holds *only* what the subprocess launcher needs to know:

```python
@dataclass(frozen=True)
class AgentSpec:
    name: str                                    # CLI dispatch key
    default_model: str                           # when ticket/CLI does not override
    fallback_model: str | None = None            # on 429-style capacity errors
    unset_env_keys: tuple[str, ...] = ()         # OAuth-conflict env vars
    inline_only: bool = False                    # orchestrator executes, not launcher
    supports_multi_turn: bool = False            # cmd_send refuses False transports
    build_cmd: Callable[..., list[str]] | None = None
    stdin_rewrite: Callable[[list[str]], list[str]] | None = None
    implicit_family: str | None = None           # single-family transports only
```

- No `family` resolver. No `CallOptions`. No `supported_options`. No `extra_flags` on the spec.
- `implicit_family` is set for single-family transports (`"openai"` for codex, `"google"` for gemini, `"anthropic"` for claude). `None` for gateway transports — the ticket must supply `family`.
- `supports_multi_turn` replaces the hardcoded codex/gemini branches in `cmd_send`; unknown transports get rejected explicitly instead of silently falling through.

### Tickets carry `family`

Every discovery/debate ticket written by Claude carries a `family` field. For single-family transports, the orchestrator copies `spec.implicit_family` into the ticket for schema uniformity. For gateway transports, the orchestrator picks a family from the canonical vocabulary (`templates/agents/families.md`) based on which model it is invoking.

Example ticket:

```json
{
  "id": "discover_opencode_kimi_m2",
  "type": "discover",
  "agent": "opencode",
  "model": "moonshot/k2.5",
  "family": "moonshot",
  "flags": {"reasoning_effort": "high"},
  "prompt_path": "_artifacts/prompts/...",
  "outputs": ["_artifacts/json/..."],
  "depends_on": [],
  "status": "pending",
  "timeout_s": 600
}
```

`flags` is free-form JSON. `build_opencode_cmd` picks keys it knows how to translate (`reasoning_effort` → `--reasoning-effort`); unknown keys are ignored with a one-line warning to stderr. If opencode rejects a flag, the subprocess fails loudly and the ticket retries or fails. No validation layer required.

### Launch-time family validation

`agent_ctl.py` imports the canonical family vocabulary once at module load and refuses to launch gateway-transport tickets whose `family` is missing or outside the set:

```python
_CANONICAL_FAMILIES = frozenset(_read_family_vocabulary())

def _validate_ticket_family(ticket: dict, spec: AgentSpec) -> None:
    fam = ticket.get("family")
    if spec.implicit_family is not None:
        if fam and fam != spec.implicit_family:
            sys.exit(
                f"ticket {ticket['id']}: family={fam!r} conflicts with "
                f"transport {spec.name!r} (implicit family: {spec.implicit_family!r})"
            )
        return
    if not fam:
        sys.exit(
            f"ticket {ticket['id']}: gateway transport {spec.name!r} requires "
            "an explicit 'family' field"
        )
    if fam not in _CANONICAL_FAMILIES:
        sys.exit(
            f"ticket {ticket['id']}: unknown family {fam!r}. "
            f"See templates/agents/families.md for the canonical set."
        )
```

Python stays dumb but not blind. Orchestrator typos (`"moonshott"`) die at launch, not silently corrupt the ranking.

### Markdown describes each CLI

Per-transport behaviour lives in `templates/agents/<transport>.md`:

- `templates/agents/families.md` — canonical family vocabulary. Alphabetical list plus rules for picking the right one (resellers → underlying model's family; fine-tunes → base model's family).
- `templates/agents/opencode.md` — how to invoke, model-string conventions, flag translation, which families it can produce.
- `templates/agents/ollama.md` — same, for local models.

Claude reads these when emitting tickets for the corresponding transport. Adding a new transport is **one AgentSpec entry + one markdown doc + one `build_<name>_cmd` function**. No resolver, no lookup table, no subprocess probe.

## Why markdown beats Python for this

Codex (xhigh) put it most sharply: *"code tables rot worse than markdown because they fail silently and look authoritative."* A Python lookup that silently misclassifies a model produces the wrong cross-family count with zero warning. A stale markdown doc produces a visible drift the next time Claude reads it, and re-reading is cheap because the orchestrator already reads markdown at every phase transition.

The project's existing shape is already markdown-driven: seven methods, three phases, two debate roles — all expressed as operational procedures Claude executes. Family assignment belongs in the same layer.

## What still goes in code

Two bugs are independent of this design and need fixing regardless:

1. **State-file locking.** `load_state` / `next_id` / `save_state` in `vendor/agent_ctl.py` have no `fcntl.flock` and no atomic write. Two concurrent `agent-ctl start` invocations can produce duplicate session IDs or overwrite each other's state. Fix with a `FileLock` context manager + rename-on-write.
2. **`cmd_send` hardcoded branches.** Currently matches on the literal strings `"codex"` and `"gemini"`. New transports that land before this is fixed silently fall through. `supports_multi_turn` on the spec turns this into an explicit per-transport decision.

Both ship in a separate commit on this branch.

## What does NOT go in this branch

- Ranking math changes (`f + 0.5·w` formula). That belongs in `templates/merge_and_rank.md`; Claude reads the `family` field off each discovery JSON and computes the weighted cross-agent count. Separate concern from transport plumbing.
- Role rotation for N>3 agents. Also a template concern, also deferred until someone actually runs a 4+ agent team.
- Per-call `reasoning_effort` / `temperature` / tool-use toggles as typed fields. Free-form `ticket["flags"]` covers this; promoting any individual flag to a typed field earns its keep the first time we need to document it across multiple transports.
