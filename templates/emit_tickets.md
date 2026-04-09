# Ticket emission protocol

Disputatio uses a ticket DAG for durable, resumable, auditable orchestration. Claude (you) generates tickets in **waves**. `agent-ctl run-dag` executes each wave; between waves, Claude inspects the outputs of completed tickets and emits the next wave.

The ticket file lives at `workspace/<paper-slug>/tickets.json`. It is a dict keyed by ticket ID.

## Ticket schema

Every ticket has the same shape. Fields marked `(required)` must be present; others are optional.

```json
{
  "id": "orient_claude",                     // unique, stable (required)
  "type": "orient",                          // disputatio ticket type (required)
  "agent": "claude",                         // claude | codex | gemini (required)
  "prompt_path": "workspace/<slug>/prompts/orient_claude.md",
                                             // relative to cwd (required for non-claude tickets)
  "inputs": [                                // files this ticket consumes (informational)
    "workspace/<slug>/paper.md"
  ],
  "outputs": [                               // files this ticket must produce (required)
    "workspace/<slug>/orientation/claude/paper_map.json"
  ],
  "depends_on": ["previous_ticket_id"],      // list of ticket IDs (required, may be empty)
  "status": "pending",                       // pending | running | done | failed (default: pending)
  "attempt": 0,                              // retry counter (default: 0)
  "max_attempts": 2,                         // default 2
  "timeout_s": 1200,                         // per-attempt timeout in seconds
                                             // recommended: 1200 (20 min) for orient/discover
                                             // — agents with web search access (codex, gemini)
                                             // can take longer than the default 300s when they
                                             // cross-reference external sources. Short timeouts
                                             // cause the agent to be killed mid-file-write
  "output_format": "json_stdout",            // optional. Set to "json_stdout" for agents that
                                             // cannot write files directly (Gemini CLI).
                                             // run-dag will salvage the JSON block from stdout
                                             // and write it to the first output path
                                             // automatically on successful completion.
  "model": "gpt-5.4",                        // optional model override
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

| Type | Produces | Consumes | Agent |
|------|----------|----------|-------|
| `orient` | `orientation/<agent>/paper_map.json` | `paper.md` | any |
| `discover` | `discovery/<agent>/m<N>/issue_*.json` | `paper.md`, `orientation/<agent>/paper_map.json` | any |
| `merge_rank` | `ranked_issues.json`, `triage.json` | all `discovery/**/issue_*.json` | claude |
| `verify` | `ranked_issues.json` (updated) | `ranked_issues.json` | gemini |
| `prosecute` | `rounds/<issue>/round_<N>_prosecute.json` | `ranked_issues.json` or prior synthesis | rotating |
| `defend` | `rounds/<issue>/round_<N>_defend.json` | prosecute output, `paper.md` | rotating |
| `synthesize` | `rounds/<issue>/round_<N>_synthesize.json` | prosecute + defend outputs | rotating |
| `final_report` | `final.json`, Obsidian note | all `rounds/**/synthesize.json` | claude |

## Wave protocol

Claude generates tickets in waves. After each `agent-ctl run-dag` completes, Claude inspects the outputs of the last wave and emits the next wave.

### Wave 1 — Orientation (emitted by Claude at `/disputatio` invocation)

```json
{
  "orient_claude": {
    "id": "orient_claude", "type": "orient", "agent": "claude",
    "prompt_path": "workspace/<slug>/prompts/orient_claude.md",
    "inputs": ["workspace/<slug>/paper.md"],
    "outputs": ["workspace/<slug>/orientation/claude/paper_map.json"],
    "depends_on": [], "status": "pending", "timeout_s": 1200
  },
  "orient_codex": { "...same shape, timeout_s 1200..." },
  "orient_gemini": { "...same shape, timeout_s 1200, output_format: json_stdout..." }
}
```

Claude-typed tickets are a special case: Claude executes them directly, without going through agent-ctl. When Claude sees a `claude`-typed ticket is ready, it runs the work itself and writes the output file. Claude-typed tickets must still be marked `done` in tickets.json after execution.

All three prompt files are written to `workspace/<slug>/prompts/` by substituting `{{paper_path}}` into `templates/orient.md`.

### Wave 2 — Discovery (emitted after orientation)

For each of the three agents, emit five discovery tickets (M2-M6):

```json
{
  "discover_claude_m2": {
    "id": "discover_claude_m2", "type": "discover", "agent": "claude",
    "prompt_path": "workspace/<slug>/prompts/discover_claude_m2.md",
    "inputs": [
      "workspace/<slug>/paper.md",
      "workspace/<slug>/orientation/claude/paper_map.json"
    ],
    "outputs": ["workspace/<slug>/discovery/claude/m2/"],
    "depends_on": ["orient_claude"],
    "status": "pending", "timeout_s": 900
  },
  "discover_claude_m3": { "...", "depends_on": ["orient_claude"] },
  "discover_claude_m4": { "...", "depends_on": ["orient_claude"] },
  "discover_claude_m5": { "...", "depends_on": ["orient_claude"] },
  "discover_claude_m6": { "...", "depends_on": ["orient_claude"] },
  "discover_codex_m2":  { "...", "depends_on": ["orient_codex"] },
  // ... etc, 15 total discovery tickets
}
```

Discovery tickets for one agent depend only on that agent's orientation. This preserves independence and maximizes parallelism.

Prompt files for each discovery ticket are generated by reading `templates/discover.md` and the specific method file `templates/methods/m<N>_*.md`, and substituting:
- `{{paper_path}}`: path to paper.md
- `{{paper_map_path}}`: path to that agent's paper map
- `{{output_dir}}`: the `discovery/<agent>/m<N>/` directory
- `{{method_content}}`: the full text of the method template

The prompt tells the agent to run **only that one method** on the paper, using its paper map as the cache.

### Wave 3 — Merge and rank (emitted after all discovery tickets complete)

One ticket:

```json
{
  "merge_rank": {
    "id": "merge_rank", "type": "merge_rank", "agent": "claude",
    "prompt_path": "workspace/<slug>/prompts/merge_rank.md",
    "inputs": [
      "workspace/<slug>/discovery/claude/",
      "workspace/<slug>/discovery/codex/",
      "workspace/<slug>/discovery/gemini/"
    ],
    "outputs": [
      "workspace/<slug>/ranked_issues.json",
      "workspace/<slug>/triage.json"
    ],
    "depends_on": [
      "discover_claude_m2", "discover_claude_m3", "discover_claude_m4",
      "discover_claude_m5", "discover_claude_m6",
      "discover_codex_m2", "discover_codex_m3", "discover_codex_m4",
      "discover_codex_m5", "discover_codex_m6",
      "discover_gemini_m2", "discover_gemini_m3", "discover_gemini_m4",
      "discover_gemini_m5", "discover_gemini_m6"
    ],
    "status": "pending", "timeout_s": 1200
  }
}
```

### Wave 4 — Verification (emitted after merge_rank)

One ticket, Gemini only (because it owns web search):

```json
{
  "verify": {
    "id": "verify", "type": "verify", "agent": "gemini",
    "prompt_path": "workspace/<slug>/prompts/verify.md",
    "inputs": ["workspace/<slug>/ranked_issues.json"],
    "outputs": ["workspace/<slug>/ranked_issues.json"],
    "depends_on": ["merge_rank"],
    "status": "pending", "timeout_s": 1800
  }
}
```

Note: this ticket reads and overwrites `ranked_issues.json`. The `agent-ctl run-dag` output check will verify the file exists and is non-empty; it cannot check that the content was updated. That is acceptable for this use case.

### Wave 5 — Debate round 1 (emitted after verify)

For each of the top N (default 8) issues in `ranked_issues.json`, emit three tickets:

```json
{
  "debate_merged_001_r1_prosecute": {
    "id": "debate_merged_001_r1_prosecute", "type": "prosecute",
    "agent": "claude",
    "prompt_path": "workspace/<slug>/prompts/debate_merged_001_r1_prosecute.md",
    "inputs": [
      "workspace/<slug>/paper.md",
      "workspace/<slug>/orientation/claude/paper_map.json",
      "workspace/<slug>/ranked_issues.json"
    ],
    "outputs": ["workspace/<slug>/rounds/merged_001/round_1_prosecute.json"],
    "depends_on": ["verify"],
    "status": "pending", "timeout_s": 900
  },
  "debate_merged_001_r1_defend": {
    "id": "debate_merged_001_r1_defend", "type": "defend",
    "agent": "codex",
    "prompt_path": "...",
    "inputs": ["...", "workspace/<slug>/rounds/merged_001/round_1_prosecute.json"],
    "outputs": ["workspace/<slug>/rounds/merged_001/round_1_defend.json"],
    "depends_on": ["debate_merged_001_r1_prosecute"],
    "status": "pending", "timeout_s": 900
  },
  "debate_merged_001_r1_synthesize": {
    "id": "debate_merged_001_r1_synthesize", "type": "synthesize",
    "agent": "gemini",
    "prompt_path": "...",
    "inputs": ["...", "workspace/<slug>/rounds/merged_001/round_1_defend.json"],
    "outputs": ["workspace/<slug>/rounds/merged_001/round_1_synthesize.json"],
    "depends_on": ["debate_merged_001_r1_defend"],
    "status": "pending", "timeout_s": 900
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

After a `debate_<issue>_r<N>_synthesize` ticket completes, Claude reads the synthesis output. If `status: "continue"` and `N < max_rounds`, emit round N+1 tickets for that issue. If `status` is `converged`, `split`, or `escalate`, do not emit more tickets for that issue.

**Special case — split**: if the synthesis produces `split`, the child issues are appended to `ranked_issues.json` and wave-5-style round-1 tickets are emitted for each child.

**Budget tiering**: when emitting round 2+ tickets, check the issue's rank score. If the issue is in the bottom half of the top-N (low priority), do not emit further rounds even if synthesis says `continue`. This enforces the budget cap described in SKILL.md.

### Final wave — Final report (emitted after all debate tickets are terminal)

One ticket:

```json
{
  "final_report": {
    "id": "final_report", "type": "final_report", "agent": "claude",
    "prompt_path": "workspace/<slug>/prompts/final_report.md",
    "inputs": [
      "workspace/<slug>/ranked_issues.json",
      "workspace/<slug>/rounds/"
    ],
    "outputs": [
      "workspace/<slug>/final.json",
      "$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/notes/work/referee-reports/<slug>.md"
    ],
    "depends_on": [ "list of all terminal debate tickets" ],
    "status": "pending", "timeout_s": 600
  }
}
```

## Run sequence

From Claude's perspective, the end-to-end flow is:

1. `/disputatio paper.pdf` → Claude creates the workspace, copies the paper, generates wave 1 tickets, writes the wave 1 prompts, writes tickets.json
2. Claude executes the `orient_claude` ticket itself (reads paper, writes paper_map.json) and marks it done in tickets.json
3. Claude runs `agent-ctl run-dag workspace/<slug>/tickets.json --concurrent 3` — executes orient_codex and orient_gemini in parallel, blocks until complete
4. Claude reads the completed orientations, generates wave 2 tickets and prompts, appends to tickets.json
5. Claude executes wave-2 claude-typed discovery tickets itself (or run-dag handles them if Claude is fine with it blocking), and runs `agent-ctl run-dag` for codex/gemini tickets
6. Claude reads discovery outputs, generates wave 3 (`merge_rank`) ticket — which is a claude-typed ticket, so Claude executes it directly (inline), writes `ranked_issues.json`, marks the ticket done
7. Claude emits wave 4 (`verify`) ticket, runs `agent-ctl run-dag`, Gemini does web verification
8. Claude reads `ranked_issues.json`, emits wave 5 (debate round 1 tickets for top N issues), runs `agent-ctl run-dag`
9. For each completed synthesis, Claude reads it and decides whether to emit round N+1
10. When all debate tickets are terminal, Claude emits the `final_report` ticket and executes it (writes final.json and Obsidian note)

## Resumability

Because every ticket is a file on disk, the entire pipeline can be resumed at any point. To resume a review:

1. Navigate to the workspace
2. Run `agent-ctl dag-status tickets.json` to see what's done
3. Run `agent-ctl run-dag tickets.json` to execute any remaining ready tickets
4. If Claude-typed tickets are pending (merge_rank, final_report, or round-emission logic), Claude resumes those inline

The skill is fully resumable: closing Claude Code, restarting later, and re-running the skill on the same workspace picks up where it left off.

## Live Obsidian note

The Obsidian note at `notes/work/referee-reports/<slug>.md` is updated after each wave completes. Claude writes the note. Updates include:

- After wave 1: paper metadata, "orientation complete" status
- After wave 2: discovery summary per agent per method
- After wave 3: ranked issue list with scores
- After wave 4: web verification results
- After each debate round: prosecution/defense/synthesis summary
- After final_report: the complete review

The Obsidian note is NOT a ticket output — it is a side effect of Claude's wave-transition work. This is deliberate: the note is for human consumption, the tickets are for machine durability.
