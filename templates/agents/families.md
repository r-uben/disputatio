# Canonical model families

This file is the single source of truth for the `family` field on discovery/debate tickets. `vendor/agent_ctl.py` reads the alphabetical list below at launch time; a ticket whose `family` is not in the list is refused by the launcher. Keep the list in lockstep with the resolution rules further down.

The orchestrator (Claude Code) reads this file when emitting tickets for gateway transports (`opencode`, `ollama`) and picks the right value for each model. Single-family transports (`codex` → `openai`, `gemini` → `google`, `claude` → `anthropic`) get their family copied from the AgentSpec automatically; the orchestrator still fills in the field so every ticket has the same shape.

## The list

One family per line, alphabetical, lowercase. Nothing else. **Adding or renaming entries is a schema change that must propagate to old discovery JSONs before re-ranking.**

```
alibaba
anthropic
cohere
deepseek
google
meta
microsoft
mistral
moonshot
openai
xai
```

Aliases that MUST map onto the canonical name above:
- `llama` → `meta`
- `qwen` → `alibaba`
- `gemma` → `google`
- `phi` → `microsoft`
- `command` / `command-r` → `cohere`
- `kimi` → `moonshot`
- `mixtral` → `mistral`
- `grok` → `xai`

If a new model architecture lands that is not on the list, add a row here first and document its aliases before emitting any ticket that uses it.

## Resolution rules (for the orchestrator)

When Claude writes a ticket for a gateway transport, it picks the family by applying these rules in order:

1. **Look at the model architecture, not the routing provider.** For OpenCode `-m provider/model_id`, the family is determined by what `model_id` actually is, not what `provider` routes through. `groq/llama-3.3-70b` → `meta` (Groq is reselling Llama). `openrouter/anthropic/claude-sonnet-4-6` → `anthropic` (OpenRouter is reselling Claude). `together/qwen2.5-72b-instruct` → `alibaba`.
2. **Direct providers collapse provider and family for their own models only.** `anthropic/claude-sonnet-4-6` → `anthropic`. `openai/gpt-4o` → `openai`. `google/gemini-2.5-pro` → `google`. But if any of these providers start hosting foreign models (e.g. Google Vertex serving Llama as `google/llama-3.3`), still apply rule 1: the family is `meta`, not `google`.
3. **Fine-tunes inherit their base model's family.** `my-qwen-finetune:latest` → `alibaba`. `mylab/deepseek-r1-distilled` → `deepseek`. If the base is unclear from the name, consult `ollama show --modelfile` (or the equivalent registry metadata) and use the `FROM` line.
4. **When in doubt, add the transport name to the ticket's `flags` and raise the ambiguity with the user.** Do not guess. A silent misclassification costs more than a paused pipeline.

## Why this is a separate file

The launcher validates against this list. The orchestrator reads this list when picking a family. The merge-and-rank template reads the `family` field off discovery JSONs and counts distinct values. All three consumers share the same vocabulary, so the vocabulary lives once, in markdown, and every consumer re-reads it at the moment they need it. Keeping it out of code means a stale entry shows up the next time someone reads the file, not silently six months later in a skewed ranking.
