# 2026-04-13 — ollama transport validation (coset-codes)

Third post of the day, after the branch-cleanup log and the `feat/opencode-backend` design note. This one is narrower: does the ollama transport added in PR #4 actually work end-to-end, not just on a `pong` smoke?

Answer: it works, but three real bugs had to be fixed along the way. None of them would have surfaced without a real paper-sized prompt.

## What we ran

One M0 (close-reading) discovery ticket against `qwen3:32b`, with the paper excerpted to the first 60 KB (~45 KB of the 184 KB OCR'd Forney 1988 coset-codes paper — intro through the main Section IV results). The ticket file lived under `_artifacts/validation/coset-codes-ollama/` (gitignored), outside the Obsidian vault, because this was a transport sanity check, not a real review.

Model: `qwen3:32b` (Q4_K_M quantisation, 20 GB), 40K native context — the largest model available locally that fits the excerpt.

## Three bugs surfaced and fixed

### 1. `--options key=value` does not exist

`build_ollama_cmd` was emitting `--options temperature=0.0 --options num_ctx=40960` etc. `ollama run` refuses these with "Error: unknown flag: --options" and exits in milliseconds. My first-pass fiction was that ollama accepted per-call sampling options on the CLI. It does not. The CLI exposes only argv-level flags (`--format`, `--hidethinking`, `--think`, `--keepalive`, `--nowordwrap`, `--verbose`); per-call sampling options live on Modelfiles or the REST `/api/generate` endpoint.

Fix: rewrite the flag translator around the actual CLI surface. Sampling-like keys (`temperature`, `num_ctx`, `num_predict`, `top_p`, `top_k`, `seed`, `repeat_penalty`) now produce a clear stderr warning pointing at the Modelfile workaround or REST path instead of silently no-op'ing. `templates/agents/ollama.md` updated to match.

### 2. `--think false` breaks the CLI parser; `--think=false` works

With bare-space form, ollama reads `--think` and then tries to use `false` as the model name, producing `Error: pull model manifest: file does not exist`. With the equals form, it works. The `--think` help output says `string[="true"]`, suggesting equals is the intended form.

Fix: `build_ollama_cmd` now emits `--think=<value>` with an explicit comment explaining why the space form is wrong. Verified with direct CLI probing.

### 3. `_clean_json_text` did not strip ANSI escape sequences

ollama emits cursor-hide (`\x1b[?25l`), cursor-show (`\x1b[?25h`), and bracketed-paste markers continuously during output, even in non-TTY mode. `script -q` in `_launch_background` captures them verbatim, so the session log ends up with JSON tokens like `{"[?25l[?25hissues[?25l[?25h": []}`.

The existing cleaner stripped single-byte control chars (including ESC `\x1b`), but the following CSI sequence bytes — `[`, `?`, `2`, `5`, `l` — are printable ASCII and survived. `json.loads` then saw `{"[?25l[?25hissues"` and choked.

Fix: strip full ANSI sequences BEFORE the single-byte control-char pass. Three regex passes cover the common cases:

- `\x1b\[[\x30-\x3f]*[\x20-\x2f]*[\x40-\x7e]` — CSI sequences (most cursor/colour codes)
- `\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)` — OSC sequences (title-setting, bracketed-paste)
- `\x1b[@-_]` — two-byte ESC commands

Verified by replaying the existing session log through `_salvage_stdout_json` after the fix: `{"issues": []}` extracts cleanly. Before the fix, the same log produced no output file and the ticket went to `failed`.

## What the validation did prove

- `agent-ctl run-dag` correctly dispatches ollama-typed tickets through `build_ollama_cmd`.
- Prompts of ~60 KB pipe cleanly via stdin under `_ollama_stdin_rewrite` (which drops the trailing positional, leaving `ollama run <flags> <model>` to read the piped prompt).
- Response capture survives ollama's TTY-assumption ANSI spew after the `_clean_json_text` fix.
- `_salvage_stdout_json` writes the recovered JSON to the ticket's declared output path.
- `_validate_ticket_family` accepts `family: alibaba` for an ollama ticket without complaint.
- The DAG state machine transitions through `pending → running → done` correctly, with session-id and timestamps written in place.

End-to-end wall-clock after the fixes: ~10 s for the first-pass run where the model decided it had nothing to flag, ~3 min for the run where it genuinely thought.

## What the validation did NOT prove

`qwen3:32b` on this paper produced `{"issues": []}` — zero findings — under both `--think=false` and `--think=high`. Two plausible explanations, and we did not discriminate:

1. **Genuine emptiness**: Forney 1988 is a well-edited classic; it is not implausible that a competent M0 reader finds no typos or notation slips in the first 60 KB. A real test would compare against a paper with known errors.
2. **Format-JSON-suppresses-reasoning**: `--format json` seems to short-circuit the thinking block — the session log had no `<think>` content under `--think=high`, which contradicts the flag's documented behaviour. May be an ollama-side interaction: JSON mode keeps the output to the declared schema and prevents reasoning traces from being emitted. A test with `--format` unset plus a JSON-schema instruction in the prompt would separate the two causes.

Either way, this is a **quality-of-findings** question, not a transport question. The transport works. Whether `qwen3:32b` is a useful disputatio agent is a separate investigation, worth doing before recommending ollama for real reviews but not required for landing this branch.

## Recommended follow-ups (not blocking)

- **Separate transport validation from model validation.** A canned test with a paper that has known M0 issues (e.g. one of the prior V2 runs where M0 caught real typos) would let us check whether a given ollama model is finding the known-good set. Not a project goal today but worth writing down.
- **Re-run with `--format` unset and explicit JSON instruction in the prompt.** If that produces findings, then `--format json` is the culprit and should only be used for the final emit, not during the reasoning trace.
- **Try `qwen3.5:35b`** instead of `qwen3:32b` — newer architecture, same user environment, may have stronger M0 reasoning. The transport is model-agnostic so this is a zero-code experiment.
- **Document which ollama models are suitable for which methods.** Discovery M0 (surface proofreading) may need a different model than M5 (self-measured critique). `templates/agents/ollama.md` could grow a "recommended models per method" table once we have data.

## Artefacts (gitignored)

All under `_artifacts/validation/coset-codes-ollama/`:

- `_paper/paper.md` — full 184 KB OCR
- `_paper/paper_excerpt.md` — first 60 KB
- `_artifacts/prompts/discover_ollama_qwen3-32b_m0.md` — the assembled discovery prompt (62 KB)
- `_artifacts/tickets.json` — single-ticket DAG, final status `done`
- `_artifacts/json/discover_ollama_qwen3-32b_m0.json` — `{"issues": []}`
- `_artifacts/sessions/discover_ollama_qwen3-32b_m0.log` — raw ANSI-polluted session capture

Not committed because `_artifacts/` is gitignored project-wide. Kept locally in case someone wants to replay the same smoke test.
