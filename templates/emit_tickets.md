# Ticket emission protocol

Disputatio uses a ticket DAG for durable, resumable, auditable orchestration. Claude (you) generates tickets in **waves**. `agent-ctl run-dag` executes each wave; between waves, Claude inspects the outputs of completed tickets, renders them as curated markdown in the numbered folders, and emits the next wave.

**The workspace is the Obsidian paper folder.** Every review lives inside a single folder:

```
~/Library/Mobile Documents/iCloud~md~obsidian/Documents/notes/work/referee-reports/<paper-slug>/
```


The ticket file lives at `<paper-folder>/_artifacts/tickets.json`. It is a dict keyed by ticket ID. All path references in tickets are **relative to the paper folder**, not to the repo or to the Obsidian vault root. Agent-ctl is invoked with `--cwd <paper-folder>` so every relative path resolves correctly.

## Ticket schema

Every ticket has the same shape. Fields marked `(required)` must be present; others are optional.

```json
{
  "id": "orient_claude",                     // unique, stable (required)
  "type": "orient",                          // disputatio ticket type (required)
  "agent": "claude",                         // transport name: any AgentSpec in
                                             // vendor/agent_ctl.py (required)
  "model": "opus-4.6",                       // model identifier for the transport
                                             // (required for gateway transports
                                             // like opencode/ollama; optional for
                                             // single-family transports, which
                                             // fall back to spec.default_model)
  "family": "anthropic",                     // model-architecture family from
                                             // templates/agents/families.md
                                             // (required; the launcher rejects
                                             // tickets whose family is missing
                                             // or outside the canonical set).
                                             // Single-family transports can set
                                             // it to the spec's implicit_family;
                                             // gateway transports must match
                                             // the chosen model per the rules
                                             // in templates/agents/families.md
  "flags": {},                               // free-form per-call knobs. build_cmd
                                             // picks what it knows how to translate
                                             // (e.g. reasoning_effort, temperature,
                                             // num_ctx). Unknown keys print a
                                             // warning and are ignored. Validation
                                             // is at the CLI, not in Python
  "prompt_path": "_artifacts/prompts/orient_claude.md",
                                             // relative to paper folder (required for non-claude tickets)
  "inputs": [                                // files this ticket consumes (informational)
    "_paper/paper.md"
  ],
  "outputs": [                               // files this ticket must produce (required)
    "_artifacts/json/orient_claude.json"
  ],
  "depends_on": ["previous_ticket_id"],      // list of ticket IDs (required, may be empty)
  "status": "pending",                       // pending | running | done | failed (default: pending)
  "attempt": 0,                              // retry counter (default: 0)
  "max_attempts": 2,                         // default 2
  "timeout_s": 1200,                         // per-attempt timeout in seconds
                                             // recommended: 1200 (20 min) for orient/discover on
                                             // cloud transports, 1800+ for local Ollama models
  "output_format": "json_stdout",            // optional. Set to "json_stdout" for agents that
                                             // cannot write files directly (Gemini CLI, Ollama).
                                             // run-dag salvages the JSON block from stdout
                                             // and writes it to the first output path
                                             // automatically on successful completion
  "cwd": "/absolute/path",                   // optional working directory override
  "session_id": null,                        // filled by agent-ctl when launched
  "started_at": null,                        // ISO timestamp, filled on launch
  "finished_at": null,                       // ISO timestamp, filled on completion
  "failure_reason": null                     // populated if status == failed
}
```

**Ticket ID naming convention** (stable across waves, critical for auditability):

```
<type>_<scope>[_<param>]

Examples:
orient_claude
orient_codex
orient_gemini
discover_claude_m2
discover_codex_m5
discover_gemini_m4
merge_rank
verify_<issue_id>
debate_<issue_id>_r1_prosecute
debate_<issue_id>_r1_defend
debate_<issue_id>_r1_synthesize
debate_<issue_id>_r2_prosecute
...
final_report
```

Issue IDs are assigned during merge (e.g., `merged_001`, `merged_002`).

## Ticket types (disputatio-specific)

All paths below are relative to the paper folder (`<paper-folder>` root). Raw JSON outputs land in `_artifacts/json/`; curated markdown is written into the numbered folders by Claude between waves (see `templates/obsidian_render.md`).

| Type | Raw output (JSON) | Consumes | Agent |
|------|-------------------|----------|-------|
| `orient` | `_artifacts/json/orient_<agent>.json` | `_paper/paper.md` | any |
| `discover` | `_artifacts/json/discover_<agent>_m<N>.json` | `_paper/paper.md`, `_artifacts/json/orient_<agent>.json` | any |
| `merge_rank` | `_artifacts/json/ranked_issues.json`, `_artifacts/json/triage.json` | all `_artifacts/json/discover_*.json` | claude |
| `verify` | `_artifacts/json/ranked_issues.json` (updated) | `_artifacts/json/ranked_issues.json` | gemini |
| `prosecute` | `_artifacts/json/debate_<issue>_r<N>_prosecute.json` | `_artifacts/json/ranked_issues.json` or prior synthesis | rotating |
| `defend` | `_artifacts/json/debate_<issue>_r<N>_defend.json` | prosecute output, `_paper/paper.md` | rotating |
| `synthesize` | `_artifacts/json/debate_<issue>_r<N>_synthesize.json` | prosecute + defend outputs | rotating |
| `final_report` | `_artifacts/json/final.json`, `4_report/referee_report.md` | all debate synthesis outputs | claude |
| `evaluate` | `_evaluation/annotations/<blind_id>.json` | `_evaluation/prompts/<blind_id>.md` (self-contained) | external (default codex/`gpt-5.4-mini`) |

## Wave protocol

Claude generates tickets in waves. After each `agent-ctl run-dag` completes, Claude inspects the outputs of the last wave and emits the next wave.

### Wave 1 — Orientation (emitted by Claude at `/disputatio` invocation)

```json
{
  "orient_claude": {
    "id": "orient_claude", "type": "orient", "agent": "claude",
    "prompt_path": "_artifacts/prompts/orient_claude.md",
    "inputs": ["_paper/paper.md"],
    "outputs": ["_artifacts/json/orient_claude.json"],
    "depends_on": [], "status": "pending", "timeout_s": 1200
  },
  "orient_codex": { "...same shape, timeout_s 1200..." },
  "orient_gemini": { "...same shape, timeout_s 1200, output_format: json_stdout..." }
}
```

Claude-typed tickets are a special case: Claude executes them directly, without going through agent-ctl. When Claude sees a `claude`-typed ticket is ready, it runs the work itself and writes the output file. Claude-typed tickets must still be marked `done` in tickets.json after execution.

All three prompt files are written to `prompts/` by substituting `{{paper_path}}` into `templates/orient.md`.

### Wave 2 — Discovery + single-shot baseline (emitted after orientation)

Wave 2 emits **two independent tracks** that run in parallel:

1. **18 discovery tickets** (3 agents × 6 methods) — the main structured-discovery channel.
2. **1 baseline_review ticket** — a single-shot opus referee review on the paper text alone, independent of orientation (no `depends_on`). Per `templates/baseline.md`. Runs concurrently with discovery, completes in ~5 minutes. Used at merge time to diff against the merged set and catch any finding the baseline surfaced that disputatio's discovery missed.

The baseline ticket is:

```json
{
  "baseline_review": {
    "id": "baseline_review", "type": "baseline",
    "agent": "claude", "model": "opus", "family": "anthropic", "flags": {},
    "prompt_path": "_artifacts/prompts/baseline_review.md",
    "inputs": ["_paper/paper.md"],
    "outputs": ["_artifacts/json/baseline_review.json"],
    "depends_on": [],
    "status": "pending", "timeout_s": 900
  }
}
```

For each of the three agents, emit six discovery tickets (M0, M2-M6):

```json
{
  "discover_claude_m0": {
    "id": "discover_claude_m0", "type": "discover", "agent": "claude",
    "prompt_path": "_artifacts/prompts/discover_claude_m0.md",
    "inputs": [
      "_paper/paper.md",
      "_artifacts/json/orient_claude.json"
    ],
    "outputs": ["_artifacts/json/discover_claude_m0.json"],
    "depends_on": ["orient_claude"],
    "status": "pending", "timeout_s": 1200
  },
  "discover_claude_m2": {
    "id": "discover_claude_m2", "type": "discover", "agent": "claude",
    "prompt_path": "_artifacts/prompts/discover_claude_m2.md",
    "inputs": [
      "_paper/paper.md",
      "_artifacts/json/orient_claude.json"
    ],
    "outputs": ["_artifacts/json/discover_claude_m2.json"],
    "depends_on": ["orient_claude"],
    "status": "pending", "timeout_s": 1200
  },
  "discover_claude_m3": { "...", "depends_on": ["orient_claude"] },
  "discover_claude_m4": { "...", "depends_on": ["orient_claude"] },
  "discover_claude_m5": { "...", "depends_on": ["orient_claude"] },
  "discover_claude_m6": { "...", "depends_on": ["orient_claude"] },
  "discover_codex_m0":  { "...", "depends_on": ["orient_codex"] },
  "discover_codex_m2":  { "...", "depends_on": ["orient_codex"] },
  // ... etc, 18 total discovery tickets (3 agents x 6 methods)
}
```

Discovery tickets for one agent depend only on that agent's orientation. This preserves independence and maximizes parallelism.

**M0 (close reading)** is a mechanical proofreading pass. It catches typos, notation errors, sign mistakes, and wording slips. See `templates/methods/m0_close_reading.md`.

Each discovery ticket produces a **single JSON file** containing all issues that agent found with that method. The JSON schema is `{"issues": [{"id": "...", "claim": "...", ...}, ...]}`. Outputting a single file per ticket simplifies validation: run-dag just checks the file exists and is non-empty.

Prompt files for each discovery ticket are generated by reading `templates/discover.md` and the specific method file `templates/methods/m<N>_*.md`, and substituting:
- `{{paper_path}}`: `_paper/paper.md`
- `{{paper_map_path}}`: `_artifacts/json/orient_<agent>.json`
- `{{output_path}}`: `_artifacts/json/discover_<agent>_m<N>.json`
- `{{method_content}}`: the full text of the method template

The prompt tells the agent to run **only that one method** on the paper, using its paper map as the cache.

### Wave 3 — Merge and rank (emitted after all discovery tickets complete)

One ticket:

```json
{
  "merge_rank": {
    "id": "merge_rank", "type": "merge_rank", "agent": "claude",
    "prompt_path": "_artifacts/prompts/merge_rank.md",
    "inputs": [
      "_artifacts/json/discover_claude_m0.json",
      "_artifacts/json/discover_claude_m2.json",
      "_artifacts/json/discover_claude_m3.json",
      "... and 15 more discovery JSON files (18 total) ..."
    ],
    "outputs": [
      "_artifacts/json/ranked_issues.json",
      "_artifacts/json/triage.json"
    ],
    "depends_on": [
      "discover_claude_m0", "discover_claude_m2", "discover_claude_m3",
      "discover_claude_m4", "discover_claude_m5", "discover_claude_m6",
      "discover_codex_m0", "discover_codex_m2", "discover_codex_m3",
      "discover_codex_m4", "discover_codex_m5", "discover_codex_m6",
      "discover_gemini_m0", "discover_gemini_m2", "discover_gemini_m3",
      "discover_gemini_m5", "discover_gemini_m6"
    ],
    "status": "pending", "timeout_s": 1200
  }
}
```

Note: `merge_rank` is a claude-typed ticket, so Claude executes it inline (reading all 15 discover JSON files, merging them, scoring, and writing the two outputs). After writing the JSON outputs, Claude also writes the human-readable `2_ranking/00_ranking.md`, `2_ranking/issue_register.md`, and `2_ranking/triage.md` as curated markdown.

### Wave 4 — Verification (emitted after merge_rank)

One ticket, Gemini only (because it owns web search):

```json
{
  "verify": {
    "id": "verify", "type": "verify", "agent": "gemini",
    "prompt_path": "_artifacts/prompts/verify.md",
    "inputs": ["_artifacts/json/ranked_issues.json"],
    "outputs": ["_artifacts/json/ranked_issues_verified.json"],
    "depends_on": ["merge_rank"],
    "status": "pending", "timeout_s": 1800,
    "output_format": "json_stdout"
  }
}
```

Note: verify writes a new file `ranked_issues_verified.json` instead of overwriting `ranked_issues.json`. This makes the run-dag output check straightforward. After verification, Claude updates the human-readable `2_ranking/verification.md` from the new file.

### Wave 5 — Debate round 1 (emitted after verify)

**Cohort selection: status-driven, not score-driven.** Open `_artifacts/json/ranked_issues_verified.json`, filter to issues where `status == "debate"` (assigned by `merge_and_rank.md` Step 3b), sort by `rank_score` descending, take the top `--top-n` (default 8). If fewer than `--top-n` issues have `status == "debate"`, emit the smaller cohort. **If zero issues have `status == "debate"`, skip the debate phase entirely and proceed directly to the final report** — that is the correct outcome on consensus-heavy papers and saves substantial budget.

For each cohort issue, emit three tickets. Example for `issue_001`:

```json
{
  "debate_issue_001_r1_prosecute": {
    "id": "debate_issue_001_r1_prosecute", "type": "prosecute",
    "agent": "claude",
    "prompt_path": "_artifacts/prompts/debate_issue_001_r1_prosecute.md",
    "inputs": [
      "_paper/paper.md",
      "_artifacts/json/orient_claude.json",
      "_artifacts/json/ranked_issues_verified.json"
    ],
    "outputs": ["_artifacts/json/debate_issue_001_r1_prosecute.json"],
    "depends_on": ["verify"],
    "status": "pending", "timeout_s": 1200
  },
  "debate_issue_001_r1_defend": {
    "id": "debate_issue_001_r1_defend", "type": "defend",
    "agent": "codex",
    "prompt_path": "_artifacts/prompts/debate_issue_001_r1_defend.md",
    "inputs": [
      "_paper/paper.md",
      "_artifacts/json/orient_codex.json",
      "_artifacts/json/debate_issue_001_r1_prosecute.json"
    ],
    "outputs": ["_artifacts/json/debate_issue_001_r1_defend.json"],
    "depends_on": ["debate_issue_001_r1_prosecute"],
    "status": "pending", "timeout_s": 1200
  },
  "debate_issue_001_r1_synthesize": {
    "id": "debate_issue_001_r1_synthesize", "type": "synthesize",
    "agent": "gemini",
    "prompt_path": "_artifacts/prompts/debate_issue_001_r1_synthesize.md",
    "inputs": [
      "_paper/paper.md",
      "_artifacts/json/debate_issue_001_r1_prosecute.json",
      "_artifacts/json/debate_issue_001_r1_defend.json"
    ],
    "outputs": ["_artifacts/json/debate_issue_001_r1_synthesize.json"],
    "depends_on": ["debate_issue_001_r1_defend"],
    "status": "pending", "timeout_s": 1200,
    "output_format": "json_stdout"
  }
}
```

**Role rotation by round:**

| Round | Prosecutor | Defender | Synthesizer |
|-------|-----------|----------|-------------|
| 1 | claude | codex | gemini |
| 2 | codex | gemini | claude |
| 3 | gemini | claude | codex |

Within a single issue's debate, the tickets are strictly sequential. Across issues, they are parallel (bounded by agent-ctl's `--concurrent` cap).

### Wave 6+ — Subsequent rounds (emitted after each synthesize completes)

After a `debate_<issue>_r<N>_synthesize` ticket completes, Claude reads the synthesis output. The `verdict` field decides whether round N+1 is funded:

- `verdict: "prosecution_wins"` → **terminal**. No round N+1. Issue ships to the report as a material concern with the synthesizer's `surviving_text`.
- `verdict: "defense_wins"` → **terminal**. No round N+1. Issue is dropped from the report (recorded in the debate trace, not in the referee letter).
- `verdict: "split"` and `N < max_rounds` → emit round N+1 tickets for the issue, prosecuting the **surviving** (narrower) claim from `surviving_text`, not the original. Roles rotate per the table below.
- `verdict: "escalate"` and `N < max_rounds` → emit round N+1 tickets focused on the verifiable point named in `next_round_focus`. Roles rotate. Also flag for human review (record in `_artifacts/json/escalations.json`).

**There is no `converged` verdict.** It was removed in v2 — see `templates/synthesize.md` for rationale. Convergence-as-default produced 100% round-1 termination on the 2026-04-13 v3 run, draining all dialectic value.

**No tier-based pre-allocation of rounds.** Every issue starts with a budget of 1 round. Rounds 2 and 3 are funded **only when the synthesizer's verdict demands continuation** (`split` or `escalate`). Budget follows tension, not pre-assigned rank tier. Hard cap at `--max-rounds` (default 3).

**Role rotation across rounds** (unchanged):

| Round | Prosecutor | Defender | Synthesizer |
|-------|-----------|----------|-------------|
| 1 | claude | codex | gemini |
| 2 | codex | gemini | claude |
| 3 | gemini | claude | codex |

### Wave 6.5 — Calibration sub-DAG (v5, emitted after all debate tickets terminal)

Calibration is a self-contained sub-DAG under `<paper-folder>/_calibration/`, emitted BETWEEN the last debate synthesis and the final_report ticket. It is the v5 quality gate that replaces post-hoc evaluation as the primary calibration loop. See `templates/calibrate.md` for the full spec and disposition rules.

Emission procedure (orchestrator, inline):

1. Collect every finding that would enter the final report: all `status: settled` issues from `ranked_issues_verified.json` PLUS all debated issues with verdict `prosecution_wins`, `split`, or `escalate` (use their synthesizer `surviving_text` as the annotated claim). Exclude `defense_wins` and triaged.
2. Shuffle and assign randomised `BF###` IDs.
3. Write `_calibration/manifest_blind.json` with `[{blind_id, true_id, tier}, ...]`.
4. Build one self-contained prompt at `_calibration/prompts/<BF###>.md` per `templates/calibrate.md`: rubric + `{blind_id, claim, quote, quote_location, evidence}` (metadata stripped) + full paper text.
5. Emit calibration tickets:

```json
{
  "calibrate_BF001": {
    "id": "calibrate_BF001", "type": "calibrate",
    "agent": "codex", "model": "gpt-5.4-mini", "family": "openai", "flags": {},
    "prompt_path": "_calibration/prompts/BF001.md",
    "inputs": ["_calibration/prompts/BF001.md"],
    "outputs": ["_calibration/annotations/BF001.json"],
    "depends_on": [],
    "status": "pending", "timeout_s": 900, "max_attempts": 2
  }
}
```

6. Run: `agent-ctl run-dag <paper>/_calibration/tickets.json --cwd <paper> --concurrent 4`.

7. After all calibration annotations complete, the orchestrator applies disposition rules inline:
   - `quote_verified: no` OR `calibration: unsupported` → drop. Record in `_calibration/dropped.json`.
   - `quote_verified: partial` OR `calibration: overclaimed` → emit a polish ticket (gemini-3.1-pro-preview) that rewrites the claim using the annotator's notes. Re-annotate the rewrite (second calibration ticket, same BF ID with a `_v2` suffix). If still fails: drop or demote one tier.
   - `calibration: supported` + `quote_verified: yes` → kept as-is.

8. Write `_calibration/final_findings.json` — the calibrated set, keyed by tier (material / local / settled / appendix). This is the ONLY input to the final_report ticket; `ranked_issues_verified.json` is bypassed after calibration.

9. Write `_calibration/00_calibration.md` scorecard: pre/post overclaim rate, per-finding disposition table.

### Final wave — Final report (emitted after calibration final_findings.json exists)

One ticket:

```json
{
  "final_report": {
    "id": "final_report", "type": "final_report", "agent": "claude",
    "prompt_path": "_artifacts/prompts/final_report.md",
    "inputs": [
      "_calibration/final_findings.json",
      "_artifacts/json/ranked_issues_verified.json"
    ],
    "outputs": [
      "_artifacts/json/final.json",
      "4_report/referee_report.md"
    ],
    "depends_on": [ "calibration aggregator inline step" ],
    "status": "pending", "timeout_s": 1200
  }
}
```

v5 addition: after the opus-compiled `final.json` is written, Claude emits one `polish` ticket per report entry to gemini-3.1-pro-preview, rewriting each finding's `surviving_text` into referee-letter prose. Input: the calibrated finding + its paper-text context (± 20 lines). Output: a one-paragraph rewrite that goes into `4_report/referee_report.md`. Polish runs in parallel (concurrent=4), does NOT change any facts, and leaves `final.json` untouched.

Claude also updates `review.md` at the top of the paper folder to set `phase: complete` and populate the summary section.

### Wave 7 — A/B evaluation (optional, emitted after `final_report = done`, only on user request)

Evaluation is a **self-contained sub-DAG** under `<paper-folder>/_evaluation/`, with its own `tickets.json`, `prompts/`, `annotations/`, `sessions/`, and results. Findings are blinded with randomised `BF###` IDs (not `merged_NNN`); the `blind_id → true_version/true_id` map lives only in `_evaluation/manifest_blind.json` and is never shown to the annotator. Default annotator: **codex with `gpt-5.4-mini`** (matches the 2026-04-12 manual baseline). See `templates/evaluation.md` for protocol and `templates/evaluate.md` for the prompt body.

Emission procedure (orchestrator runs this inline before `run-dag`):

1. Collect findings from every review version being evaluated (single-review: just current `ranked_issues.json`; cross-review: gather from each version).
2. Shuffle all findings across all versions into one pool; assign sequential `BF###` IDs in shuffled order.
3. Write `_evaluation/manifest_blind.json` with the `[{blind_id, true_version, true_id}, ...]` list.
4. Build one self-contained prompt per finding at `_evaluation/prompts/<blind_id>.md` — rubric + finding JSON (with blind_id baked in, metadata stripped) + paper text inlined + `write_file` output instruction pointing at `_evaluation/annotations/<blind_id>.json`.
5. Write `_evaluation/tickets.json` with one ticket per finding:

```json
{
  "eval_BF001": {
    "id": "eval_BF001",
    "type": "evaluate",
    "agent": "codex",
    "model": "gpt-5.4-mini",
    "family": "openai",
    "flags": {},
    "prompt_path": "_evaluation/prompts/BF001.md",
    "inputs": [
      "_evaluation/prompts/BF001.md"
    ],
    "outputs": [
      "_evaluation/annotations/BF001.json"
    ],
    "depends_on": [],
    "status": "pending",
    "timeout_s": 900,
    "max_attempts": 2
  }
}
```

Note the inputs list is just the prompt — everything the annotator needs (paper text, rubric, finding) is inlined into the prompt body. This keeps the annotator's world closed: it cannot see other findings, other prompts, or `_artifacts/json/`.

Run the sub-DAG with `agent-ctl run-dag <paper>/_evaluation/tickets.json --cwd <paper> --concurrent 4`.

After all `evaluate` tickets are `done`, Claude **runs the aggregator inline** (no ticket): reads every `_evaluation/annotations/*.json`, joins with `_evaluation/manifest_blind.json`, writes `_evaluation/results.json` (machine truth: flat `rows` + per-version `summary`), then renders `_evaluation/00_evaluation.md` (scorecard) and `_evaluation/annotations_unblinded.csv` (human-readable join) from it.

For aggregated findings (`aggregated: true` with `sub_findings`), each sub-finding gets its own `BF###` in the shuffled pool; the manifest records the sub-finding id in `true_id` (e.g. `merged_099.a`). The aggregator surfaces per-sub scores in the scorecard alongside a sub-averaged summary.

## Run sequence

Let `$PAPER` = the absolute path of the paper folder inside the Obsidian vault, e.g. `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/notes/work/referee-reports/caballero-simsek-2024`.

From Claude's perspective, the end-to-end flow is:

1. `/disputatio <path-to-paper.md>` → Claude creates `$PAPER/` and all subfolders (`review.md`, `_paper/paper.md`, `0_orientation/`, ..., `_artifacts/{prompts,json,sessions}/`)
2. Claude generates wave 1 tickets, writes the orientation prompts into `_artifacts/prompts/`, writes `_artifacts/tickets.json`
3. Claude executes the `orient_claude` ticket inline (reads paper, writes `_artifacts/json/orient_claude.json`, marks the ticket done in tickets.json)
4. Claude runs `agent-ctl run-dag $PAPER/_artifacts/tickets.json --cwd $PAPER --concurrent 3` — executes orient_codex and orient_gemini in parallel, blocks until complete. Session logs are auto-archived to `_artifacts/sessions/`
5. Claude renders the three orientation JSON files into `0_orientation/{claude,codex,gemini}.md` and writes `0_orientation/00_orientation.md`
6. Claude emits wave 2 discovery tickets and their prompts, appends to tickets.json, runs `agent-ctl run-dag` again
7. Claude renders the 15 discovery JSON files into `1_discovery/m<N>/{claude,codex,gemini}.md` and writes the per-method summaries
8. Claude executes `merge_rank` inline (reads the 15 discovery files, merges, scores, writes `_artifacts/json/ranked_issues.json`, `_artifacts/json/triage.json`, and the markdown in `2_ranking/`)
9. Claude emits `verify` ticket, runs `agent-ctl run-dag`, Gemini does web verification
10. Claude renders `2_ranking/verification.md` from the verified JSON
11. Claude emits wave 5 (debate round 1 tickets for top N issues), runs `agent-ctl run-dag`
12. For each completed synthesis, Claude renders the round files into `3_debates/<rank>_<slug>/r1_*.md` and decides whether to emit round N+1 based on the synthesis status
13. When all debate tickets are terminal, Claude executes `final_report` inline (writes `_artifacts/json/final.json` and `4_report/referee_report.md`, updates `review.md` to `phase: complete`)

Between waves, Claude's job is two-fold: **render** the JSON outputs into curated markdown, and **emit** the next wave's tickets. Both happen before the next `run-dag` invocation. See `templates/obsidian_render.md` for the exact rendering templates.

## Resumability

Because every ticket is a file on disk inside the paper folder, the entire pipeline can be resumed at any point. To resume a review:

1. Open the paper folder in Obsidian (or cd to it in the filesystem)
2. `agent-ctl dag-status _artifacts/tickets.json` — inspect what is done
3. `agent-ctl run-dag _artifacts/tickets.json --cwd .` — execute any remaining ready tickets
4. If Claude-typed tickets are pending (orient_claude, merge_rank, final_report, or wave-emission logic), re-invoke `/disputatio` on the same paper folder and Claude resumes those inline

The skill is fully resumable: closing Claude Code, restarting later, and re-running the skill on the same paper folder picks up where it left off.

## The Obsidian folder structure IS the review

Unlike earlier designs, there is no separate Obsidian "live note" that tracks progress. The paper folder itself — with its numbered subfolders and the `review.md` at the top — IS the live report. It updates as Claude renders outputs into it. `review.md` tracks the current phase in its frontmatter and the top-of-file "Status" line.

See `templates/obsidian_structure.md` for the full folder spec and `templates/obsidian_render.md` for how each JSON artifact is rendered into markdown.
