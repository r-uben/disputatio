# 2026-04-11: E2E test + Gemini fix + model routing

## What was done

Two end-to-end tests of the full disputatio pipeline:

1. **Population genetics** (Stephens & Donnelly 2000, 51pp) — first-ever cold-start test
2. **Coset codes** (Forney 1988, 29pp) — retest after Gemini fixes

## Gemini root cause analysis

Gemini was producing thin output (22 issues vs Claude's 60) and couldn't write files. Three bugs found:

1. **Missing `--yolo` flag** — Gemini CLI blocks on tool approval in headless mode without it. This was the critical fix: Gemini has `write_file` but never got to use it.
2. **Stdin quoting bug** — For large prompts (>10KB), the `-p` flag was being dropped. `gemini '' -m ...` instead of `gemini -p '' -m ...`. The prompt went to a positional arg instead of the `-p` flag value.
3. **JSON encoding** — Gemini embeds raw LaTeX in JSON strings, creating invalid `\escapes` and control characters. Added `_clean_json_text` to auto-repair.

Also added: retry backoff (30s * attempt), auto-fallback from `gemini-3.1-pro-preview` to `gemini-3-flash-preview` on 429 capacity exhaustion.

## Impact

| Metric | Before (run 1) | After (run 2) |
|--------|:---:|:---:|
| Gemini issues | 22 | **67** |
| Files salvaged | 6 | **0** |
| Gemini file writes | stdout only | **direct** |
| 429 errors | every session | **0** |
| Orientation time | 574s | **77s** |

## Quality comparison

Both runs produced full referee reports. Key finding: disputatio catches strategic issues that single-pass reviews miss (the trellis-vs-lattice conclusion, the IS-vs-MCMC causal identification), but produces fewer equation-level close-reading catches than the reference reviews.

## Model routing (designed, not yet tested)

Mapped each ticket type to cheapest viable model. Opus only for merge+rank, top prosecutions, synthesis, final report (~30% of pipeline). Sonnet for orientation + discovery (~50%). Haiku for rendering (~20%). Expected to cut Opus usage by ~70%.

## Decisions

- **Kept `gemini-3.1-pro-preview` as default** despite 429s. User pointed out it works fine interactively — capacity issues are transient. `gemini-3-flash-preview` is auto-fallback.
- **socr 2.0.0** with gemini engine for OCR. Clean LaTeX output, quality audit. pdftotext is fallback for digital PDFs when speed matters.
- **Skipped multi-round debate** in both tests (1 round only). Role rotation untested.
- **Debate ran as Claude subagents** not cross-model. Loses independence but saves time and complexity.

## Files changed

- `~/.claude/skills/agent_ctl.py` — 5 fixes (--yolo, quoting, JSON cleaning, salvage regex, fallback)
- `SKILL.md` — model routing table, Gemini model update
- `CLAUDE.md` — updated lessons from testing
- `compare/demo_data.json` — structured comparison data for website
