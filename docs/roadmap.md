# Roadmap & known issues

State of the world after the V3 run on targeting-interventions (2026-04-12).

---

## Validation backlog (highest-priority)

The disputatio thesis ("debate reduces overclaiming") has *n* = 1 evidence on theory papers. To make a defensible general claim:

1. **Re-run on population-genetics** with the current skill. The earlier comparison on this paper used a stale disputatio version; the public website page is currently marked "DRAFT — DO NOT CITE" pending a fresh run. ~2 h compute.
2. **Run two more papers** end-to-end (cortical-circuits, coset-codes both have reference + coarse baselines staged in `docs/archive/compare/`). Gives *n* = 4 for the holistic comparison. ~4 h additional compute.
3. **Cross-judge validation** on targeting-interventions. Re-run `judge.py` with Opus and GPT-4 as judges (~5 samples each) to confirm the win isn't a Gemini-family preference. ~30 min.
4. **Cross-annotator** for the per-finding evaluation. Re-annotate targeting-interventions findings with Gemini and Opus as annotators (currently only Codex). ~20 min per annotator.

After (1)–(2) the holistic claim becomes "disputatio beats coarse on N papers." After (3)–(4) it becomes "the win is robust across judges/annotators." Both together would be publication-grade.

---

## Known bugs (worked around in V3, fix in V4)

These all surfaced during the targeting-interventions run on 2026-04-12. None blocked completion (each had a workaround) but all should be fixed properly before the next run.

### 1. `agent-ctl` misroutes `claude`-typed tickets to the Gemini CLI

`cmd_start` has `if agent == "codex": ...` followed by an unconditional `else:` that builds a Gemini command. Any non-`codex` agent — including `claude` — gets sent to `gemini -p ... -m sonnet`, which 404s in ~15 seconds (no `sonnet` model on the Gemini API). `agent-ctl run-dag` then auto-retries to attempt 2 with the same misrouting.

**Workaround applied:** patched `_ticket_ready` in `~/.claude/skills/agent_ctl.py` to return `False` for any ticket with `agent == "claude"`, so `run-dag` never picks them up. The orchestrator (Claude Code) executes them inline. This is a one-line patch; not yet upstreamed.

**Proper fix:** `cmd_start` should explicitly raise on unknown agents instead of falling through to Gemini. `_ticket_ready` should keep its current behavior of skipping claude tickets (orchestrator's job).

### 2. Gemini OAuth silently expires mid-run

After ~24 h of inactivity, the Gemini CLI's OAuth token expires. The next call prints `Error authenticating: FatalCancellationError: Authentication cancelled by user` to stdout and exits 0. `agent-ctl` sees process exit + outputs missing → marks the ticket failed, retries, fails again, marks failed permanently. From the user's perspective, every Gemini-dependent ticket starts failing simultaneously with no obvious cause.

**Workaround applied:** noticed the `FatalCancellationError` in a session log when investigating a stuck wave; ran `gemini -p "ping"` from the user's terminal to trigger the OAuth flow; reset the failed tickets to `pending`; relaunched `run-dag`.

**Proper fix:** `agent-ctl run-dag`'s retry loop should sniff the session log for `FatalCancellationError` or `Opening authentication page` before retrying; on detection, halt the DAG with an actionable error message ("Gemini OAuth expired — run `gemini -p ping` to re-authenticate, then re-run the skill").

### 3. Gemini JSON output frequently has runaway LaTeX backslash escapes

When Gemini outputs JSON containing LaTeX, the existing `_clean_json_text` in `agent-ctl` produces sequences like `\\\\\\\\\\\\\\sum` (14 backslashes) that don't parse. The iterative regex matches single backslashes followed by invalid escape chars and doubles them, but doesn't account for backslashes already part of an escaped pair, so each pass adds more.

**Workaround applied:** wrote an inline two-pass cleaner — first collapse `\\{2,}` to `\\\\` (two backslashes, which is the JSON encoding of one literal backslash), then apply the invalid-escape regex with a negative lookbehind so already-escaped pairs are left alone.

**Proper fix:** replace `_clean_json_text` upstream with the two-pass approach. The replacement is straightforward and the existing test cases should continue to pass.

### 4. Synthesis prompts ship with `[[WILL BE INJECTED]]` placeholders

The synthesis prompt template uses `{{prosecution}}` and `{{defense}}` placeholders that should be filled with the upstream tickets' outputs *just before* the synthesis ticket runs. The current ticket emitter writes the prompts up front (before prosecutions/defenses have run) and leaves the placeholders as literal `[[WILL BE INJECTED AFTER ...]]` markers.

In V3, this happened to work because Gemini (running with `--yolo`) reads the missing dependency files directly via `read_file` tool calls. The synthesis output references specific objections and replies correctly. But this is fragile — it relies on Gemini's tool-use ability and on the file paths being correct in the prompt.

**Workaround applied:** none in V3 (Gemini's file reading saved us).

**Proper fix:** add a "prompt hook" stage to `agent-ctl` — before launching a ticket, run a JIT injection step that reads the dependency JSONs and substitutes them into the prompt. Or have the orchestrator regenerate the prompt right before stamping the ticket ready.

### 5. Between-phase rendering is skipped by default

`SKILL.md` describes a rendering step after each wave: read the JSON outputs and write curated markdown into `0_orientation/`, `1_discovery/`, `2_ranking/`, `3_debates/`. In practice this is treated as optional and was skipped throughout V3 — only `4_report/referee_report.md` and `_artifacts/json/` were populated.

Consequence: the final report contains wikilinks like `[[../3_debates/01_<slug>/99_summary]]` that don't resolve in Obsidian because the target files don't exist. The report still reads well, but the provenance trail from the report back to individual debate transcripts is broken.

**Workaround applied:** none — the final report references debate summaries that don't exist on disk.

**Proper fix:** make the rendering step mandatory. Per the model routing table, Haiku is the right model for it (mechanical projection JSON → markdown). The orchestrator should delegate to a Haiku subagent after each phase completes; total cost is small.

### 6. judge.py occasionally fails to parse Gemini 3.1 Pro outputs

When `--model gemini/gemini-3.1-pro-preview` is used, the judge sometimes returns malformed JSON (extra commentary outside the JSON block, or invalid escape sequences). `judge.py`'s `json.loads` then crashes the whole evaluation.

**Workaround applied:** fell back to `gemini/gemini-2.5-pro` for the multi-sample evaluation.

**Proper fix:** judge.py should catch `JSONDecodeError`, attempt a salvage (extract the largest fenced JSON block, apply the same two-pass cleaner from bug 3), and only fail the run if salvage also fails.

---

## Adapter limitations

The `docs/archive/compare/adapt.py` flattener was patched in commit `30f2032` to handle the current `templates/final_report.md` heading formats. It now extracts:

- Material issues (`### N. Title` format with `**Refined claim.**` / `**Constructive fix.**` bold sub-fields)
- Local issues (`N. **Title.**` numbered list format)
- Appendix concerns (bullet-list `- **merged_NNN** (name): ...` format OR numbered `### N. Title (rank X/15)` format)

What it does *not* yet handle:

- Sub-clauses within issues (e.g. nested bullet lists inside a Material issue body)
- Inline block quotes in the original prose — the flattened version paraphrases instead of using `>` blockquotes, which the judge sometimes notes as a weakness
- Multiple "Material issues" subsections (some templates have separate sections for material logical gaps vs material scope issues)

These would each move the auto-adapted score by ~0.1–0.2 points if fixed.

---

## Public claim hygiene

Currently the public website at `disputatio-ccc1a3e8/` contains:

| Page | Status |
|---|---|
| `index.html` | Updated 2026-04-13 — targeting score 6.00 (5-sample mean), pop-gen marked "score withdrawn" |
| `cases/targeting-interventions.html` | Updated 2026-04-13 — current numbers, current methodology disclosed |
| `cases/population-genetics.html` | Updated 2026-04-13 — DRAFT banner at top, score replaced with "pending re-run" panel; content preserved but flagged not-for-citation |

The principle: **never publish a number we wouldn't defend in detail.** When a comparison becomes unfair (e.g. through skill-version drift), withdraw the number rather than leaving it standing.

---

## V4 scope (suggested)

A V4 sprint focused on the bugs above would:

1. Patch the 5 `agent-ctl` / template / judge bugs upstream.
2. Add a multi-sample wrapper to `judge.py` (--samples N → mean ± stddev table).
3. Add a cross-judge wrapper to `judge.py` (--judges gemini-2.5-pro,opus,gpt-4 → side-by-side table).
4. Run the validation backlog (re-run pop-gen; run cortical-circuits + coset-codes; cross-judge validate).

Estimated effort: 4–6 h coding, 8–12 h compute (mostly waiting for paper runs to finish).

After V4, the public claim could be: "Disputatio outperforms single-pass Sonnet 4.6 reviews by ~0.5 points on the coarse.ink benchmark across N theory papers, robust across {Gemini, Opus, GPT-4} judges, with overclaim rate reduced from X to Y vs the prior single-model debate version."
