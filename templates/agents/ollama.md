# Ollama transport

Ollama (`ollama` CLI) runs local models on the user's machine. It is a gateway transport in the family sense — one CLI, many architectures — but unlike OpenCode every call stays on localhost. No provider credentials, no external rate limits, no network round-trip. Trade-off: the user must have `ollama serve` running and must have pulled the chosen model beforehand.

## Invocation

Non-interactive mode:

```
ollama run <model> "<prompt>"
```

- `<model>` is a single-string identifier like `qwen2.5:32b`, `llama3.3:70b`, `deepseek-r1:14b`, or a user-chosen local name like `my-custom-finetune:latest`.
- Large prompts: `agent_ctl.py` writes the prompt to a temp file and pipes it on stdin. The `stdin_rewrite` for this transport replaces the positional prompt argument with an empty string; Ollama treats stdin as the prompt when the argument is empty.
- Output is plain text on stdout. Ollama has no native JSON output mode; discovery prompts must therefore instruct the model to emit fenced `json` blocks, and `_salvage_stdout_json` in `agent_ctl.py` already handles that pattern.
- No `--yolo`-style flag needed. Ollama models cannot call tools by default; they are pure text-in text-out. For discovery and debate, that is exactly what we want.

## Model string conventions

`<model>[:<tag>]`. The tag is optional and defaults to `:latest`. Common conventions in the Ollama registry:

| Invocation | Architecture | Ticket `family` |
|---|---|---|
| `ollama run qwen2.5:32b` | Alibaba Qwen 2.5 | `alibaba` |
| `ollama run llama3.3:70b` | Meta Llama 3.3 | `meta` |
| `ollama run deepseek-r1:14b` | DeepSeek R1 (reasoning) | `deepseek` |
| `ollama run mistral-nemo:12b` | Mistral Nemo | `mistral` |
| `ollama run gemma2:27b` | Google Gemma 2 | `google` |
| `ollama run phi4:14b` | Microsoft Phi 4 | `microsoft` |

For custom or renamed models where the family is not obvious from the name, run:

```
ollama show <model> --modelfile
```

and read the `FROM` line. `FROM qwen2.5:32b` means the family is `alibaba` regardless of what the local alias is called. The orchestrator does this lookup when emitting the ticket; it does NOT go into `agent_ctl.py` as a runtime probe.

## Ticket shape

```json
{
  "id": "discover_ollama_qwen_m5",
  "type": "discover",
  "agent": "ollama",
  "model": "qwen2.5:32b",
  "family": "alibaba",
  "flags": {},
  "prompt_path": "_artifacts/prompts/discover_ollama_qwen_m5.md",
  "inputs": [
    "_paper/paper.md",
    "_artifacts/json/orient_ollama_qwen.json"
  ],
  "outputs": ["_artifacts/json/discover_ollama_qwen_m5.json"],
  "depends_on": ["orient_ollama_qwen"],
  "status": "pending",
  "timeout_s": 1800
}
```

Notes:

- `timeout_s` should be higher than for cloud transports. 14B-32B local models on a consumer GPU take several minutes for long prompts; 70B takes longer. Start with 1800 s and adjust per model.
- `family` is REQUIRED. The launcher rejects Ollama tickets without it. This is the check that prevents a typo (`"qwen-2.5"` instead of `"qwen2.5"`) from silently misclassifying the finding.
- Ollama tickets are best scheduled one at a time (`--concurrent 1`) unless the user has multiple GPUs. Running three 32B models concurrently on a single GPU pushes swap and destroys throughput.

## Flags the builder translates

`build_ollama_cmd` reads `ticket["flags"]` and translates known keys onto the actual `ollama run` argv. The CLI does not expose per-call sampling options (`temperature`, `num_ctx`, `num_predict`, etc.) — those are Modelfile parameters set at model-build time or via the REST `POST /api/generate` endpoint. Tickets that need them either pre-build a Modelfile variant of the model with the values baked in, or talk to the REST API directly (out of scope for `agent_ctl.py` today).

| `flags` key | Translation | Notes |
|---|---|---|
| `format` | `--format <string>` | Pass `"json"` to force the model into JSON output mode — useful for discovery tickets where `_salvage_stdout_json` parses the response |
| `hidethinking` | `--hidethinking` | Strip `<think>...</think>` blocks from the output. Use with reasoning models like `qwen3:*` and `deepseek-r1:*` where the thinking block bloats stdout and complicates JSON parsing |
| `think` | `--think <true\|false\|high\|medium\|low>` | Disable thinking entirely with `false` (faster + cleaner output) or set the effort level. `qwen3` family supports the verbal levels |
| `keepalive` | `--keepalive <duration>` | How long to keep the model resident in VRAM after the call. Default is 5m; set to `30m` if running multiple sequential tickets against the same model so the model does not reload between calls |
| `nowordwrap` | `--nowordwrap` | Do not soft-wrap output. Cleaner for downstream parsing |
| `verbose` | `--verbose` | Show timings; useful when debugging a slow model |
| `temperature`, `num_ctx`, `num_predict`, `top_p`, `top_k`, `seed`, `repeat_penalty` | warn and ignore | Listed only so callers get a clear stderr message pointing at the REST-API path or the Modelfile workaround. Setting them in `flags` does NOT take effect through `ollama run` |
| (other keys) | ignored with stderr warning | — |

### Pre-built Modelfile variants

If a paper consistently needs a custom temperature or context window across many tickets, build a named Modelfile variant once and reference it by name in tickets:

```
ollama create qwen3:32b-disputatio -f - <<EOF
FROM qwen3:32b
PARAMETER temperature 0.0
PARAMETER num_ctx 32768
PARAMETER num_predict 4096
EOF
```

Then ticket `model` becomes `qwen3:32b-disputatio` and the parameters are baked in. This is the recommended path for production runs; raw `qwen3:32b` is fine for sanity-check passes.

## Preflight the orchestrator should do

Before emitting the first Ollama ticket in a review:

1. Check `ollama list` to confirm the requested model is pulled. If missing, the user must `ollama pull <model>` first; fail the emit with a clear message rather than letting the ticket run and error out.
2. Check `ollama ps` to confirm the daemon is alive. If not, prompt the user to `ollama serve`.
3. Pick a sensible `num_predict` based on the prompt type. Orientation and M5 (immanent critique) need more output tokens than close-reading M0.

These checks live in the orchestrator at ticket-emit time, not inside `agent_ctl.py`. Failing-fast at emit time is cheaper than waiting for a 30-minute ticket to exhaust its timeout.

## Known caveats

- **Local models are genuinely weaker at long-context scientific papers.** A 32B Qwen is not a peer of Claude Opus or Gemini Pro on dense theory work. Use Ollama transports to *widen* the agent pool (more cross-family evidence, cheaply) rather than to *replace* cloud agents for the final debate.
- **Sampling is nondeterministic by default.** If reproducibility matters for a particular test run, pass `temperature: 0.0` in `flags`. Deterministic runs are important when comparing two skill versions on the same paper; non-deterministic runs are fine for accumulating cross-agent evidence.
- **Context windows vary wildly by model.** `qwen2.5:32b` ships with 32K by default; `llama3.3:70b` ships with 128K. A long paper (60+ pages after OCR) may exceed 32K even after orientation summarisation. If orientation on a particular Ollama model consistently truncates, pass `num_ctx` explicitly in `flags` and verify the machine has RAM to back it.
