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

Gateway specs pass a resolver function. **Important correction (caught by a Codex review of the first draft): for gateway transports, the string before the slash is a *routing provider*, not always a model family.** `anthropic/claude-sonnet-4-6` does collapse provider and family, but `groq/llama-3.3-70b` is Meta's Llama served via Groq's inference layer — the family is `meta`, not `groq`. Same for OpenRouter (`openrouter/*`), Together, Fireworks, and any other reseller/inference-layer prefix. Under-counting this as `family="groq"` would silently inflate cross-family agreement when two "groq" models are actually the same underlying Llama.

So OpenCode resolution is two-step: split on `/` to get `(provider, model_id)`, then route through a provider-specific resolver. Most providers (Anthropic, OpenAI, Google, Moonshot) are direct — provider equals family. Resellers need a model-name lookup.

```python
# Direct providers: provider string IS the family.
_OPENCODE_DIRECT_PROVIDERS = {
    "anthropic": "anthropic",
    "openai": "openai",
    "google": "google",
    "moonshot": "moonshot",
    "deepseek": "deepseek",
    "mistral": "mistral",
}

# Resellers / inference layers: look up the model-name prefix to find
# the true family of the underlying model.
_OPENCODE_RESELLER_PROVIDERS = {"groq", "openrouter", "together", "fireworks"}

def _family_from_model_prefix(model_id: str) -> str | None:
    """Match the leading token of a bare model name (no provider/) to a
    known family. Returns None if nothing matches."""
    base = model_id.split(":", 1)[0].lower()
    for prefix, fam in {
        "llama":    "meta",
        "qwen":     "alibaba",
        "deepseek": "deepseek",
        "mistral":  "mistral",
        "mixtral":  "mistral",
        "gemma":    "google",
        "phi":      "microsoft",
        "command":  "cohere",
    }.items():
        if base.startswith(prefix):
            return fam
    return None

def _opencode_family(model: str) -> str:
    if "/" not in model:
        raise ValueError(
            f"OpenCode model must be in 'provider/model' form, got: {model!r}"
        )
    provider, model_id = model.split("/", 1)
    if provider in _OPENCODE_DIRECT_PROVIDERS:
        return _OPENCODE_DIRECT_PROVIDERS[provider]
    if provider in _OPENCODE_RESELLER_PROVIDERS:
        fam = _family_from_model_prefix(model_id)
        if fam is None:
            raise ValueError(
                f"Cannot infer family for reseller model {model!r}. "
                "Add the underlying architecture prefix to the family table."
            )
        return fam
    raise ValueError(
        f"Unknown OpenCode provider {provider!r}. "
        f"Direct: {sorted(_OPENCODE_DIRECT_PROVIDERS)}; "
        f"resellers: {sorted(_OPENCODE_RESELLER_PROVIDERS)}."
    )

AgentSpec(
    name="opencode",
    family=_opencode_family,
    default_model="anthropic/claude-sonnet-4-6",
    build_cmd=build_opencode_cmd,
    ...
)
```

For Ollama, **query the daemon before heuristics**. Ollama's `/api/show` endpoint (or `ollama show <model> --modelfile`) returns the base model and architecture. Prefix matching on the display name is a fallback for when the API is unreachable, not the primary source — otherwise custom fine-tunes (`my-qwen-finetune:latest`), HF-imported models (`hf.co/user/model:Q4_K_M`), and user-renamed aliases silently fail even when the underlying architecture is obvious:

```python
def _ollama_family(model: str) -> str:
    # Primary: ask the daemon what the base model is.
    try:
        info = subprocess.run(
            ["ollama", "show", model, "--modelfile"],
            capture_output=True, text=True, timeout=10, check=True,
        ).stdout
        # Modelfile has a `FROM <base>` line when the model was derived
        # from another; or `architecture: llama` metadata in the show
        # output. Parse the base-model reference first.
        m = re.search(r"^FROM\s+(\S+)", info, re.MULTILINE)
        if m:
            base = m.group(1)
            fam = _family_from_model_prefix(base)
            if fam:
                return fam
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        pass  # fall through to prefix heuristic

    # Fallback: prefix-match on the display name for stock model names.
    fam = _family_from_model_prefix(model)
    if fam is None:
        raise ValueError(
            f"Cannot determine Ollama model family for {model!r}. "
            "Ollama daemon did not expose a recognisable FROM line, "
            "and the display name does not match any known prefix."
        )
    return fam
```

`_family_from_model_prefix` is shared between OpenCode (reseller path) and Ollama — it's the architecture-to-family table, so having one source of truth keeps `groq/llama-3.3-70b` and `ollama run llama3.3:70b` resolving to the same family `meta`.

## The OpenCode-vs-native-CLI decision

A user who wants to add Kimi has two choices:

1. **Via OpenCode**: one transport already in the registry; Kimi appears automatically once its provider prefix is added to `_OPENCODE_PROVIDER_TO_FAMILY`.
2. **Via native Moonshot CLI** (if one ships): new `build_kimi_cmd` + new `AgentSpec(name="kimi", family="moonshot", ...)`.

OpenCode is cheaper to add (no new build function, no new env-var plumbing) but may reshape prompts or inject its own system prompt, degrading output quality. The rule we'll apply during onboarding: **prefer OpenCode by default, fall back to a native CLI only if a discovery-pass smoke test shows materially worse findings** (fewer issues, generic rather than paper-specific claims, loss of quotes).

## Per-call settings go on a separate object, not on AgentSpec

Codex's third pushback on the first draft: **`AgentSpec` is static transport metadata; per-call settings aren't.** Things like `reasoning_effort` (Codex-specific), `temperature`, tool-use toggles, context-window hints, image attachments — these vary per invocation, not per spec. If we keep piling them onto `AgentSpec` and growing the `build_cmd` signature, we'll refactor again in two branches.

The right shape is a separate `CallOptions` dataclass threaded through `build_cmd`:

```python
@dataclass(frozen=True)
class CallOptions:
    """Per-invocation knobs. Any subset may be populated; build_cmd
    functions pick out what they know how to map onto their CLI and
    silently ignore options their transport does not support."""
    reasoning_effort: str | None = None    # codex: low/medium/high/xhigh
    temperature: float | None = None       # opencode, ollama
    max_tokens: int | None = None          # most transports
    tool_use: bool | None = None           # codex: --full-auto vs -s read-only
    images: tuple[str, ...] = ()           # codex: -i <path>
    extra_flags: tuple[str, ...] = ()      # escape hatch

def build_codex_cmd(prompt: str, model: str, *, options: CallOptions,
                    result_file: Path, cwd: str, **_unused) -> list[str]:
    cmd = ["codex", "exec", ...]
    if options.reasoning_effort:
        cmd.extend(["--reasoning-effort", options.reasoning_effort])
    if options.images:
        for img in options.images:
            cmd.extend(["-i", img])
    ...
```

Each transport also declares which options it *understands* via a capability set on the spec, so we can warn (or error) when a ticket asks for `reasoning_effort=xhigh` on a transport that has no concept of it:

```python
@dataclass(frozen=True)
class AgentSpec:
    name: str
    family: str | Callable[[str], str]
    default_model: str
    supported_options: frozenset[str] = frozenset()
    ...
```

A ticket that wants Codex with high reasoning becomes:

```json
{
  "agent": "codex",
  "model": "gpt-5.4",
  "options": {"reasoning_effort": "high", "tool_use": true}
}
```

`_launch_ticket` reads `ticket.get("options", {})`, constructs a `CallOptions`, validates it against `spec.supported_options`, and passes it into `spec.build_cmd`. Specs that don't care stay trivial.

## Forward compatibility

Keeping `family` as `str | Callable` and putting per-call knobs on `CallOptions` means the AgentSpec shape stays stable. New transports add an entry. New per-call features add a `CallOptions` field plus the transports that know how to map it. Neither requires touching dispatch logic.

If a future transport's family resolver needs more than the model string (say, a runtime feature flag), the resolver signature can widen to `Callable[[str, CallOptions], str]` — specs that don't care ignore the second argument.

## What the PR that lands this will contain

- `AgentSpec.family` widened to `str | Callable[[str], str]`, plus a `resolve_family(model)` helper method.
- `AgentSpec.supported_options: frozenset[str]` for capability declaration.
- New `CallOptions` dataclass threaded through `build_cmd`; `_launch_ticket` and `cmd_start` read it from tickets / CLI flags.
- `_family_from_model_prefix` shared helper (single architecture→family table).
- `_opencode_family` with direct-provider vs reseller-provider routing (Groq / OpenRouter / Together go through the model-name table).
- `_ollama_family` that queries `ollama show` first, falls back to the prefix heuristic.
- Two new AgentSpec entries: `opencode` and `ollama`, both with callable `family` and `supported_options` populated.
- One `build_opencode_cmd` and one `build_ollama_cmd` accepting the new `CallOptions` kwarg.
- Existing `build_codex_cmd` / `build_gemini_cmd` updated to accept `options: CallOptions = CallOptions()` (default keeps current behaviour byte-identical).
- Smoke tests mirroring `feat/agent-spec-refactor`: registry shape, argv construction, family resolution for `anthropic/claude-sonnet-4-6`, `groq/llama-3.3-70b` (must resolve to `meta`, not `groq`), `ollama qwen2.5:32b`, plus a live `agent-ctl start opencode -m anthropic/claude-sonnet-4-6 "ping"` against a real OpenCode install.
- No changes to ranking math yet. The `f + 0.5·w` formula from `adding-agents.md` Q3 consumes `resolve_family(model)` but lives in the merge-and-rank template, not in agent-ctl.
