# Transport, model, family — three things we used to conflate

A design note written before the OpenCode / Ollama specs land. It refines one concept from `docs/adding-agents.md` that the first draft got half-right.

## The conflation

The original AgentSpec has a single `family` field. That works for the three agents we started with:

- `codex` CLI → always calls OpenAI's GPT family → `family = "openai"`.
- `gemini` CLI → always calls Google's Gemini family → `family = "google"`.
- `claude` (inline, via the orchestrator) → always Anthropic → `family = "anthropic"`.

For each of these, the **CLI you invoke** and the **model family you hit** are locked 1:1. You can pick `gpt-5.4` vs `gpt-5.4-mini` from the codex CLI, or `gemini-3.1-pro-preview` vs `gemini-3-flash-preview` from gemini, but you can't ask codex to call Gemini. One CLI, one family.

OpenCode and Ollama break that assumption.

## Three separable things

Going forward we distinguish:

| Concept | Question it answers | Examples |
|---|---|---|
| **Transport** | How does Claude invoke this agent? What does the argv look like? What env vars conflict? | `codex`, `gemini`, `claude` (inline), `opencode`, `ollama` |
| **Model** | Which specific model runs inside that transport? | `gpt-5.4`, `gemini-3.1-pro-preview`, `qwen2.5:32b`, `moonshot/k2.5`, `anthropic/claude-sonnet-4-6` |
| **Family** | Which org/architecture built that model? The thing that matters for cross-agent ranking weights. | `openai`, `google`, `anthropic`, `moonshot`, `meta` (Llama), `alibaba` (Qwen), `deepseek`, `mistral` |

For `codex` / `gemini` / `claude` the three collapse (transport determines family). For gateway CLIs they do not:

- `opencode run -m moonshot/k2.5 "..."` → transport: `opencode`, model: `moonshot/k2.5`, family: `moonshot`.
- `opencode run -m anthropic/claude-sonnet-4-6 "..."` → transport: `opencode`, model: `anthropic/claude-sonnet-4-6`, family: `anthropic`.
- `ollama run qwen2.5:32b "..."` → transport: `ollama`, model: `qwen2.5:32b`, family: `alibaba`.
- `ollama run llama3.3:70b "..."` → transport: `ollama`, model: `llama3.3:70b`, family: `meta`.

Same transport, different family per call. So `family` can't be a static attribute of the spec for gateway transports.

## Why this matters (beyond neatness)

The ranking step weights cross-agent support at ×2 because agreement across **model families** is a stronger independence signal than agreement across multiple methods inside a single family. If we treat "opencode" as one family, then running OpenCode→Kimi and OpenCode→Llama and OpenCode→Qwen on the same paper would look like one agent's opinion repeated three times. The ranking math would under-credit the genuine cross-architecture agreement.

The honest accounting: the thing we're counting for cross-agent support is distinct **families**, not distinct **transports**. A review with Codex (openai) + Gemini (google) + OpenCode→Kimi (moonshot) has three distinct families. A review with OpenCode→Kimi + OpenCode→Llama + OpenCode→Qwen also has three distinct families. Both should count as full cross-family agreement (`f = 3` in the formula from `adding-agents.md` Q3). A review with Codex (openai) + OpenCode→gpt-4 (openai) has `f = 1, w = 1` — same family from two transports, not independent evidence.

## What this means for AgentSpec

`family` goes from `str` to `str | Callable[[str], str]`:

```python
@dataclass(frozen=True)
class AgentSpec:
    name: str                                      # transport name
    family: str | Callable[[str], str]             # static, or model→family resolver
    default_model: str
    ...

    def resolve_family(self, model: str) -> str:
        if callable(self.family):
            return self.family(model)
        return self.family
```

Fixed-transport specs keep a plain string:

```python
AgentSpec(name="codex", family="openai", default_model="gpt-5.4", ...)
AgentSpec(name="gemini", family="google", default_model="gemini-3.1-pro-preview", ...)
AgentSpec(name="claude", family="anthropic", default_model="opus-4.6", inline_only=True)
```

Gateway specs pass a resolver function. OpenCode's `-m` argument is already in `provider/model` form, so resolution is a string split:

```python
_OPENCODE_PROVIDER_TO_FAMILY = {
    "anthropic": "anthropic",
    "openai": "openai",
    "google": "google",
    "moonshot": "moonshot",
    "ollama": "ollama",  # further resolved below if needed
    "deepseek": "deepseek",
    "mistral": "mistral",
    "groq": "groq",
    # ... extend as needed
}

def _opencode_family(model: str) -> str:
    """'moonshot/k2.5' -> 'moonshot'. Errors loudly on malformed input."""
    if "/" not in model:
        raise ValueError(
            f"OpenCode model must be in 'provider/model' form, got: {model!r}"
        )
    provider, _ = model.split("/", 1)
    fam = _OPENCODE_PROVIDER_TO_FAMILY.get(provider)
    if fam is None:
        raise ValueError(
            f"Unknown OpenCode provider prefix: {provider!r}. "
            f"Known: {sorted(_OPENCODE_PROVIDER_TO_FAMILY)}."
        )
    return fam

AgentSpec(
    name="opencode",
    family=_opencode_family,
    default_model="anthropic/claude-sonnet-4-6",
    build_cmd=build_opencode_cmd,
    ...
)
```

Ollama's `-m` argument is just `<model>:<tag>` with no provider prefix, so resolution needs an explicit map:

```python
_OLLAMA_MODEL_TO_FAMILY = {
    # Prefix-match: any model name starting with "qwen" is alibaba, etc.
    "qwen": "alibaba",
    "llama": "meta",
    "deepseek": "deepseek",
    "mistral": "mistral",
    "gemma": "google",
    "phi": "microsoft",
}

def _ollama_family(model: str) -> str:
    base = model.split(":", 1)[0].lower()
    for prefix, fam in _OLLAMA_MODEL_TO_FAMILY.items():
        if base.startswith(prefix):
            return fam
    raise ValueError(
        f"Unknown Ollama model family for {model!r}. "
        "Add an entry to _OLLAMA_MODEL_TO_FAMILY."
    )
```

## The OpenCode-vs-native-CLI decision

A user who wants to add Kimi has two choices:

1. **Via OpenCode**: one transport already in the registry; Kimi appears automatically once its provider prefix is added to `_OPENCODE_PROVIDER_TO_FAMILY`.
2. **Via native Moonshot CLI** (if one ships): new `build_kimi_cmd` + new `AgentSpec(name="kimi", family="moonshot", ...)`.

OpenCode is cheaper to add (no new build function, no new env-var plumbing) but may reshape prompts or inject its own system prompt, degrading output quality. The rule we'll apply during onboarding: **prefer OpenCode by default, fall back to a native CLI only if a discovery-pass smoke test shows materially worse findings** (fewer issues, generic rather than paper-specific claims, loss of quotes).

## Forward compatibility

Keeping `family` as `str | Callable` also means we can extend the resolver later without touching AgentSpec itself. If some future transport needs to *also* consider the prompt content or a runtime feature flag to decide family, the resolver signature can grow; specs that don't care ignore the new arguments.

## What the PR that lands this will contain

- `AgentSpec.family` widened to `str | Callable[[str], str]`, plus a `resolve_family(model)` helper method.
- `_OPENCODE_PROVIDER_TO_FAMILY` and `_ollama_family` helpers.
- Two new AgentSpec entries: `opencode` (gateway; family resolved from `provider/model`) and `ollama` (gateway; family resolved from model prefix).
- One `build_opencode_cmd` and one `build_ollama_cmd`.
- Smoke tests mirroring the `feat/agent-spec-refactor` PR: registry shape, argv construction, family resolution for a handful of provider/model pairs, and a live `agent-ctl start opencode -m anthropic/claude-sonnet-4-6 "ping"` against a real OpenCode install.
- No changes to ranking math yet. The `f + 0.5·w` formula from `adding-agents.md` Q3 is a separate concern and belongs in the merge-and-rank template, not in agent-ctl.
