# Ticket emission protocol

Disputatio uses a ticket DAG for durable, resumable, auditable orchestration. Claude (you) generates tickets in **waves**. `agent-ctl run-dag` executes each wave; between waves, Claude inspects the outputs of completed tickets, renders them as curated markdown in the numbered folders, and emits the next wave.

**The workspace is the Obsidian paper folder.** Every review lives inside a single folder:

```
~/Library/Mobile Documents/iCloud~md~obsidian/Documents/notes/work/referee-reports/<paper-slug>/
```


The ticket file lives at `<paper-folder>/_artifacts/tickets.json`. It is a dict keyed by ticket ID. All path references in tickets are **relative to the paper folder**, not to the repo or to the Obsidian vault root. Agent-ctl is invoked with `--cwd <paper-folder>` so every relative path resolves correctly.

**Row shape authority**: every wave after Phase 3 operates on panel rows defined in `templates/schemas/panel_row.md`. Waves add fields to each row; they do not reshape the row.

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
holistic_claude
discover_claude_holistic_candidates
discover_codex_broad_critic
discover_gemini_narrow_evidence
merge_rank
verify_<issue_id>
debate_<issue_id>_r1_prosecute
debate_<issue_id>_r1_defend
debate_<issue_id>_r1_synthesize
debate_<issue_id>_r2_prosecute
...
panel_render
```

Issue IDs are assigned during merge (e.g., `merged_001`, `merged_002`).

## Ticket types (disputatio-specific)

All paths below are relative to the paper folder (`<paper-folder>` root). Raw JSON outputs land in `_artifacts/json/`; curated markdown is written into the numbered folders by Claude between waves (see `templates/obsidian_render.md`).

| Type | Raw output (JSON) | Consumes | Agent |
|------|-------------------|----------|-------|
| `orient` | `_artifacts/json/orient_<agent>.json` | `_paper/paper.md` | any |
| `holistic` | `_artifacts/json/holistic_<agent>.json` | `_paper/paper.md`, `_artifacts/json/orient_<agent>.json` | any |
| `discover` | `_artifacts/json/discover_<agent>_<track>.json` | paper map + holistic pass + attack-surface index | any |
| `merge_rank` | `_artifacts/json/panel_rows_candidates.json`, `_artifacts/json/ranked_issues.json` (audit), `_artifacts/json/triage.json` | all nine `_artifacts/json/discover_<agent>_<track>.json` files + `baseline_review.json` | claude |
| `verify` | `_artifacts/json/panel_rows_candidates_verified.json` | `_artifacts/json/panel_rows_candidates.json` | gemini |
| `prosecute` (Route A only) | `_artifacts/json/debate_<issue>_r<N>_prosecute.json` | `_calibration/post_pass1_panel_rows.json` (Round 1) or prior synthesis (Rounds 2+) | rotating |
| `defend` | `_artifacts/json/debate_<issue>_r<N>_defend.json` | Route A: prosecute output + `_paper/paper.md`. Route B: `_calibration/post_pass1_panel_rows.json` (`claim_under_challenge` block) + `_paper/paper.md` | rotating |
| `synthesize` | `_artifacts/json/debate_<issue>_r<N>_synthesize.json` | Route A: prosecute + defend outputs. Route B: defend output only | rotating |
| `render` | `4_panel/panel.md` + mode-specific memo | `_artifacts/json/panel.json`, `_paper/paper.md` | gemini |
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

### Wave 1.5 — Holistic pass (v6, emitted after orientation)

Each of the three agents runs one holistic conceptual pass on the paper using its own paper map. Per `templates/holistic.md`.

```json
{
  "holistic_claude": {
    "id": "holistic_claude", "type": "holistic", "agent": "claude",
    "model": "opus", "family": "anthropic", "flags": {},
    "prompt_path": "_artifacts/prompts/holistic_claude.md",
    "inputs": ["_paper/paper.md", "_artifacts/json/orient_claude.json"],
    "outputs": ["_artifacts/json/holistic_claude.json"],
    "depends_on": ["orient_claude"],
    "status": "pending", "timeout_s": 900
  },
  "holistic_codex": { "...same shape, agent: codex, model: gpt-5.4, family: openai, depends_on: [orient_codex]..." },
  "holistic_gemini": { "...same shape, agent: gemini, model: gemini-3.1-pro-preview, family: google, depends_on: [orient_gemini], output_format: json_stdout..." }
}
```

After all three holistic tickets complete, the orchestrator builds a **canonical attack-surface index** inline: union of `attack_surfaces[]` across the three agents, deduplicated by `description` semantic match, priorities aggregated. Written to `_artifacts/json/attack_surface_index.json`. Phase 2 discovery tickets receive this as additional input context.

### Wave 1.75 — Literature engagement (v2 — graph-traversal)

One ticket per paper, emitted between Wave 1.5 (holistic) and Wave 2 (discovery). **Claude-typed (executed inline by the orchestrator).** Three internal passes: LLM ancestor identification → citation-API graph traversal → LLM mechanism-overlap rerank. See `templates/literature_engagement.md` for the authoritative protocol; `scripts/openalex_query.py` for the API helper.

```json
{
  "literature_engagement": {
    "id": "literature_engagement", "type": "literature_engagement",
    "agent": "claude", "model": "sonnet", "family": "anthropic", "flags": {},
    "prompt_path": "_artifacts/prompts/literature_engagement.md",
    "inputs": [
      "_paper/paper.md",
      "_artifacts/json/orient_claude.json",
      "_artifacts/json/holistic_claude.json",
      "_artifacts/json/attack_surface_index.json"
    ],
    "outputs": ["_artifacts/json/literature_engagement.json"],
    "depends_on": ["holistic_claude", "holistic_codex", "holistic_gemini"],
    "status": "pending", "timeout_s": 1800
  }
}
```

After the ticket completes, the surviving candidates feed Phase 2 discovery as additional input context AND emit panel rows into a new top-level array `literature_engagement_findings[]` at Phase 6 compile time.

**Disable flag:** Run with `--no-lit-engagement` to skip this wave entirely. Independent of `--skip-web`.

**v2 supersedes the v1 design in `feat/33-literature-engagement-track` (PR #36).** The v1 templates remain in the historical record; v2 replaces the Pass A/B contract and removes the /chrome MCP hard prerequisite.

### Wave 2 — Discovery (v6: 9 tickets across 3 tracks)

Three tracks per family × 3 families = **9 discovery tickets**. Replaces the v5 18-ticket shape. Every ticket receives `_artifacts/json/attack_surface_index.json` as additional input context so the same index anchors all three tracks.

| Track | Template | Purpose |
|---|---|---|
| `holistic_candidates` | `templates/discover_holistic.md` (method-neutral; uses paper spine + attack surfaces + likely referee questions) | conceptual-scope concerns the method tracks under-detect |
| `broad_critic` | `templates/discover_broad.md` (fuses M0 close-reading + M2 contradictions + M5 self-measured) | scan for contradictions, scope mismatches, commitment violations, framing overclaims, transcription errors |
| `narrow_evidence` | `templates/discover_narrow.md` (fuses M3 transformations + M4 counterexamples + M6 causal disentangling + M8 algebraic derivation trace, targeted at priority attack surfaces) | deep evidence-heavy findings on the priority attack-surface set the agent selects; M8 mandatory on every theory/proof surface; orchestrator audits `surface_attempts[]` for coverage + M8 + engagement and rejects-and-retries once on a structural failure (see "Narrow-evidence yield retry") |

Sample ticket:

```json
{
  "discover_claude_holistic_candidates": {
    "id": "discover_claude_holistic_candidates", "type": "discover", "agent": "claude",
    "model": "sonnet", "family": "anthropic", "flags": {},
    "prompt_path": "_artifacts/prompts/discover_claude_holistic_candidates.md",
    "inputs": [
      "_paper/paper.md",
      "_artifacts/json/orient_claude.json",
      "_artifacts/json/holistic_claude.json",
      "_artifacts/json/attack_surface_index.json"
    ],
    "outputs": ["_artifacts/json/discover_claude_holistic_candidates.json"],
    "depends_on": ["holistic_claude"],
    "status": "pending", "timeout_s": 1200
  }
}
```

Nine tickets total:
- `discover_claude_{holistic_candidates, broad_critic, narrow_evidence}`
- `discover_codex_{holistic_candidates, broad_critic, narrow_evidence}`
- `discover_gemini_{holistic_candidates, broad_critic, narrow_evidence}`

All nine run in parallel (depends_on references the per-family holistic ticket, which finished in Wave 1.5).

**Evidence compiler inline.** Every candidate finding produced by any ticket passes through a compiler step BEFORE it is written to the discovery JSON. The compiler extracts the verbatim quote, pins the location, and decides whether support is `direct_quote` or `derived_inference`. Findings that cannot produce either are dropped at write time, not at merge time. This enforces the verbatim-quote discipline pre-emptively.

**Narrow-evidence engagement audit.** After each `discover_*_narrow_evidence` ticket completes, the orchestrator audits `surface_attempts[]` and `issues[]` against three structural checks (NOT against a hardcoded issue count — the agent picks the surface set, so a fixed count would either pad easy papers or reject hard ones):

1. **Surface coverage.** Every attack surface in the index marked `priority: high` AND `requires_deep_engagement: true` must appear in `surface_attempts[]`. Missing high-priority surfaces fail the check.
2. **M8 audit.** Every `surface_attempts[]` entry whose `type ∈ {theory, proof}` must have `m8_required: true` AND `m8_outcome ∈ {finding_emitted, clean_trace}`. `m8_outcome: "not_applicable"` on a theory/proof surface fails the check.
3. **Engagement.** Every entry must populate `methods_attempted[]` with at least one method AND `engagement_outcome ∈ {finding_emitted, engaged_no_finding}`. An honest run that engages every selected surface and finds nothing passes the audit (`engagement_outcome: engaged_no_finding` on every entry); the failure is "skipped surfaces", not "low yield". `engagement_outcome: "finding_emitted"` is verified mechanically: `len(issues_emitted) > 0` AND every id in `issues_emitted` resolves to an entry in `issues[]`. A row claiming `finding_emitted` with empty `issues_emitted`, or naming an issue id absent from `issues[]`, fails the check.

If any check fails, the ticket is **rejected and re-run once** with the same prompt and an inline reviewer note naming the specific failure (e.g. "M8 missing on AS3 (theory)"). Re-runs append `_retry1` to the session log archive name. A second failure is logged as a model failure in `_artifacts/sessions/narrow_evidence_underproduction.log` (one line per family with the failing check); the run continues with whatever the second attempt returned, but the failure surfaces in the panel-render summary so the human reviewer sees the gap rather than discovering it via missing findings.

This rule applies only to the `narrow_evidence` track; `broad_critic` and `holistic_candidates` have no engagement audit. Rationale: the 2026-04-15 A/B vs coarse.ink had narrow_evidence emit 4 findings per family under the prior "3–8" quality bar; two algebra findings coarse.ink caught lived in surfaces narrow_evidence selected but did not deeply engage. The earlier "minimum 6 issues" framing was a hardcoded threshold against the project rule and was not a real floor either (second-retry shipped whatever it got). Auditing engagement structurally is the actual fix.

Each ticket's JSON output is `{"issues": [...]}` where each issue carries `category`, `evidence[]` (each entry with `quote`, `location`, `why`, `support_type`), `falsifier`, and optional `paper_commitment` / `paper_commitment_location` for self-measured critiques.

**Web search**: not triggered. Closed-book discovery.

### Wave 2.5 — Coarse-style baseline (v5, retained as safety net)

The single-shot opus baseline from v5 is **kept** as a safety net for the first v6 releases. Once the holistic pass + 9-ticket discovery has been measured on 3+ papers and shown to match baseline coverage, this ticket can be retired.

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

Runs in parallel with discovery (no `depends_on`). Per `templates/baseline.md`. Used at merge time in Step 2c of `templates/merge_and_rank.md` to diff against the merged set and force baseline-unique findings into debate as coverage insurance.

### Legacy Wave 2 (v3/v4/v5, 18 tickets — RETIRED in v6)

The following is kept for reference and for runs that resume from pre-v6 workspaces. New runs should use the 9-ticket shape above.

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

One ticket. Inputs are the **nine v6 discovery files** (3 families × 3 tracks), not the retired 18-method shape. Output includes the canonical v6 panel-row candidates alongside the legacy ranked-issues audit artifact.

```json
{
  "merge_rank": {
    "id": "merge_rank", "type": "merge_rank", "agent": "claude",
    "prompt_path": "_artifacts/prompts/merge_rank.md",
    "inputs": [
      "_artifacts/json/discover_claude_holistic_candidates.json",
      "_artifacts/json/discover_claude_broad_critic.json",
      "_artifacts/json/discover_claude_narrow_evidence.json",
      "_artifacts/json/discover_codex_holistic_candidates.json",
      "_artifacts/json/discover_codex_broad_critic.json",
      "_artifacts/json/discover_codex_narrow_evidence.json",
      "_artifacts/json/discover_gemini_holistic_candidates.json",
      "_artifacts/json/discover_gemini_broad_critic.json",
      "_artifacts/json/discover_gemini_narrow_evidence.json",
      "_artifacts/json/baseline_review.json"
    ],
    "outputs": [
      "_artifacts/json/panel_rows_candidates.json",
      "_artifacts/json/ranked_issues.json",
      "_artifacts/json/triage.json"
    ],
    "depends_on": [
      "discover_claude_holistic_candidates", "discover_claude_broad_critic", "discover_claude_narrow_evidence",
      "discover_codex_holistic_candidates",  "discover_codex_broad_critic",  "discover_codex_narrow_evidence",
      "discover_gemini_holistic_candidates", "discover_gemini_broad_critic", "discover_gemini_narrow_evidence",
      "baseline_review"
    ],
    "status": "pending", "timeout_s": 1200
  }
}
```

`merge_rank` is a claude-typed ticket, so Claude executes it inline. After writing the JSON outputs, Claude also writes the human-readable `2_ranking/00_ranking.md`, `2_ranking/issue_register.md`, and `2_ranking/triage.md` as curated markdown. `panel_rows_candidates.json` is the canonical structured output that flows into Wave 5 (calibration Pass 1); `ranked_issues.json` is preserved purely as the audit-trail artifact for inspection.

### Wave 4 — Verification (emitted after merge_rank)

One ticket, Gemini only (because it owns web search). Verify reads the panel-row candidates and writes a verified copy used by Wave 5 calibration.

```json
{
  "verify": {
    "id": "verify", "type": "verify", "agent": "gemini",
    "prompt_path": "_artifacts/prompts/verify.md",
    "inputs": ["_artifacts/json/panel_rows_candidates.json"],
    "outputs": ["_artifacts/json/panel_rows_candidates_verified.json"],
    "depends_on": ["merge_rank"],
    "status": "pending", "timeout_s": 1800,
    "output_format": "json_stdout"
  }
}
```

Note: verify writes a new file `panel_rows_candidates_verified.json` instead of overwriting `panel_rows_candidates.json`. This makes the run-dag output check straightforward. After verification, Claude updates the human-readable `2_ranking/verification.md` from the new file.

### Wave 5 — Calibration-wraps-debate (v6)

v6 replaces v5's "debate-then-calibrate-top-N" with **calibration wrapping debate**: a first calibration pass runs on every panel-row candidate from merge, the two-route gate (Route A disagreement / Route B consensus override) is evaluated over calibrated survivors, debate fires only on gate-clearers, and a second calibration pass narrows debate `surviving_text` before it enters the panel.

Concretely Wave 5 decomposes into three sub-waves that the orchestrator emits in sequence:

#### Wave 5a — Calibration pass 1 (all candidates)

For every row in `_artifacts/json/panel_rows_candidates_verified.json[survived]` (produced by Wave 4 verify, or `panel_rows_candidates.json[survived]` if the run used `--skip-web`), emit one `calibrate` ticket per row. Default annotator: codex/gpt-5.4-mini; fallback: claude-sonnet-4.6. Ticket shape per `templates/calibrate.md`. Run with `agent-ctl run-dag _calibration/tickets.json --concurrent 4`.

Output: `_calibration/annotations/<BF_id>.json` per row. The aggregator (Claude inline) applies disposition rules:

- `quote_verified: no` OR `calibration: unsupported` → drop immediately; write to `_calibration/dropped_pass1.json` with reason; no debate, no further processing
- `quote_verified: partial` OR `calibration: overclaimed` → fire one polish-rewrite ticket (gemini-3.1-pro-preview, per `templates/polish.md`) to narrow the claim. Re-annotate with the **upgraded re-annotator** (codex `gpt-5.4` full, NOT gpt-5.4-mini — breaks correlated-error blind spots between the two mini reads; full rationale in `templates/calibrate.md` "Upgraded re-annotator"). Disposition:
  - **Clean pass** (unqualified `supported` + `quote: yes`, no uncertainty triggers) → `calibrated_narrowed`, keep severity, carry to gate
  - **Uncertain pass** (any of the 4 triggers in `templates/calibrate.md`: qualified verdict, hedging language, indirect support, internal rubric disagreement) → `calibrated_narrowed` AND demote severity one tier, carry to gate
  - **Still failing** (`overclaimed`, `partial`, `unsupported`, or `quote: no`) → drop, no further rewrites
- `calibration: supported` → carry to gate evaluation unchanged

Write `_calibration/post_pass1_panel_rows.json` with the surviving set + `calibration_pass1` field populated on each row.

#### Wave 5b — Two-route gate evaluation (inline, no tickets)

The orchestrator applies the two-route escalation gate (spec in `SKILL.md` → Explicit rules) to every row in `_calibration/post_pass1_panel_rows.json`. Pseudocode:

```python
REQUIRED_SEVERITIES = {"material", "local"}
REQUIRED_CAL_VERDICTS = {"supported", "calibrated_narrowed"}


def user_visible(row):
    cal1 = row.get("calibration_pass1", {})
    if cal1.get("verdict") not in REQUIRED_CAL_VERDICTS:
        return False, f"calibration_pass1_verdict_not_user_visible:{cal1.get('verdict')}"
    if row.get("severity") not in REQUIRED_SEVERITIES:
        return False, f"severity_not_user_visible:{row.get('severity')}"
    return True, None


def should_escalate(row):
    """Return (escalate, route, reason). Route A takes precedence if both match."""
    hint = row.get("debate_hint", {})

    # Route A — disagreement
    if hint.get("cross_family_disagreement") != "strong":
        route_a_failure = "cross_family_disagreement_not_strong"
    elif hint.get("evidence_conflict_in_paper") != "yes":
        route_a_failure = "no_evidence_conflict_in_paper"
    elif not hint.get("severity_sensitive"):
        route_a_failure = "severity_not_sensitive_to_verdict"
    else:
        ok4, why4 = user_visible(row)
        route_a_failure = None if ok4 else why4

    if route_a_failure is None:
        return True, "disagreement", "all_conditions_met"

    # Route B — consensus override
    if hint.get("high_severity_consensus") is True:
        ok4, why4 = user_visible(row)
        if ok4:
            return True, "consensus", "high_severity_consensus_override"
        return False, "none", why4

    return False, "none", route_a_failure


rows = json.load(open("_calibration/post_pass1_panel_rows.json"))
to_debate, to_panel = [], []
for r in rows:
    ok, route, reason = should_escalate(r)
    r["gate_decision"] = {"escalated": ok, "route": route, "reason": reason}
    (to_debate if ok else to_panel).append(r)

summary = {
    "n_in": len(rows),
    "n_debate": len(to_debate),
    "n_panel": len(to_panel),
    "by_route": {
        "disagreement": sum(1 for r in to_debate if r["gate_decision"]["route"] == "disagreement"),
        "consensus":    sum(1 for r in to_debate if r["gate_decision"]["route"] == "consensus"),
    },
}
json.dump({"debate": to_debate, "direct_to_panel": to_panel, "summary": summary},
          open("_artifacts/json/gate_decision.json", "w"))
```

If `len(to_debate) == 0`, Wave 5c is skipped entirely. Rows in `to_panel` proceed directly to Wave 6 (panel render).

#### Wave 5c — Debate round 1 on gate-clearers (only)

Ticket structure **differs by route**:

- **Route A (disagreement)** rows: emit the standard three-ticket triple `prosecute → defend → synthesize`. Role rotation for Round 1: claude prosecutes, codex defends, gemini synthesizes. Defender runs its normal "senior author" posture. Synthesizer uses Route A verdicts: `prosecution_wins | defense_wins | split | escalate`.

- **Route B (consensus)** rows: emit TWO tickets only — `defend → synthesize`. No prosecute. The finding's `claim_under_challenge` block (emitted by merge) is the pinned target the defender reads. Defender runs consensus red-team mode (see `templates/defend.md`). Synthesizer uses Route B verdicts: `consensus_held | consensus_broken`. Role assignment for Route B: codex defends (red-team), gemini synthesizes.

Rounds 2+ emitted post-synthesis if the Route A verdict is `split` or `escalate` AND `N < --max-debate-rounds`; default cap is 2 rounds. Route B has **no round 2** — the red-team challenge is terminal by construction. Either the consensus held or it broke; there is no partial state to iterate.

After every synthesis, the finding's row is updated with the `debate` field (triggered, route, reason, verdict, what_survived, history).

Row disposition by verdict:
- Route A `prosecution_wins`, `split`, `escalate` → flow into Wave 5d (Pass 2 on `surviving_text`)
- Route A `defense_wins` → appended to `_calibration/dropped_by_defense.json` with defender's counter-evidence as drop reason; does NOT re-enter calibration
- Route B `consensus_held` → flow into Wave 5d (the consensus held up under challenge; re-annotate its `surviving_text` if the synthesizer produced one, otherwise keep the original row)
- Route B `consensus_broken` → appended to `_calibration/dropped_by_red_team.json` with defender's shared-hallucination analysis as drop reason; does NOT re-enter calibration
- **`not_run`** → set by the synth-output validator (see `SKILL.md` → Validation rules → Synthesis) when a synthesizer returns a verdict from the wrong route's vocabulary, or omits `surviving_text` on a non-drop verdict, or omits `route`. The row falls back to its `calibration_pass1` verdict and ships to the panel as if it had skipped debate; the failure is logged at `_artifacts/sessions/synth_route_mismatch.log` (one line per offending ticket: row id, ticket route, synth-emitted verdict). NOT a drop — calibration Pass 1 already vouched for the row, so the conservative behaviour is "ship the pre-debate row" rather than "drop on synth failure". Surfaces in the panel-render summary as `n_synth_validator_rejections`.

#### Wave 5d — Calibration pass 2 (debate survivors)

For each debate survivor, emit a fresh `calibrate` ticket against the synthesizer's `surviving_text` (not the original claim). Same annotator, same rubric. Polish-rewrite fires the same way if needed. Output: `_calibration/post_pass2_panel_rows.json` with `calibration_pass2` field populated.

Merge into final set: rows that went direct from Wave 5a → to_panel keep `calibration_pass1` only; rows that went through debate carry both `calibration_pass1` AND `calibration_pass2`. Both survive into the panel. The renderer reads whichever calibration is most recent on each row.

Write `_calibration/final_findings.json` with the complete calibrated set, preserving both calibration passes per row, debate history per debated row, and dropped findings in separate arrays (`dropped_pass1`, `dropped_by_defense` (Route A defense_wins), `dropped_by_red_team` (Route B consensus_broken), `dropped_pass2`). Each Route B `consensus_broken` row records the synthesizer's `mode_fired` field as the drop reason.

**Route A (disagreement) — three tickets per issue.** Example for `issue_001` (Route A row pulled from `_calibration/post_pass1_panel_rows.json` via the `gate_decision.route == "disagreement"` filter):

```json
{
  "debate_issue_001_r1_prosecute": {
    "id": "debate_issue_001_r1_prosecute", "type": "prosecute",
    "agent": "claude",
    "prompt_path": "_artifacts/prompts/debate_issue_001_r1_prosecute.md",
    "inputs": [
      "_paper/paper.md",
      "_artifacts/json/orient_claude.json",
      "_calibration/post_pass1_panel_rows.json"
    ],
    "outputs": ["_artifacts/json/debate_issue_001_r1_prosecute.json"],
    "depends_on": ["calibrate_pass1"],
    "status": "pending", "timeout_s": 1200,
    "route": "disagreement"
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
    "status": "pending", "timeout_s": 1200,
    "route": "disagreement"
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
    "output_format": "json_stdout",
    "route": "disagreement"
  }
}
```

**Route B (consensus override) — two tickets per issue, no prosecute.** Example for `issue_007` (Route B row pulled by the `gate_decision.route == "consensus"` filter; prompts MUST inline the row's `claim_under_challenge` block via the `{{claim_under_challenge}}` placeholder):

```json
{
  "debate_issue_007_r1_defend": {
    "id": "debate_issue_007_r1_defend", "type": "defend",
    "agent": "codex",
    "prompt_path": "_artifacts/prompts/debate_issue_007_r1_defend.md",
    "inputs": [
      "_paper/paper.md",
      "_artifacts/json/orient_codex.json",
      "_calibration/post_pass1_panel_rows.json"
    ],
    "outputs": ["_artifacts/json/debate_issue_007_r1_defend.json"],
    "depends_on": ["calibrate_pass1"],
    "status": "pending", "timeout_s": 1200,
    "route": "consensus"
  },
  "debate_issue_007_r1_synthesize": {
    "id": "debate_issue_007_r1_synthesize", "type": "synthesize",
    "agent": "gemini",
    "prompt_path": "_artifacts/prompts/debate_issue_007_r1_synthesize.md",
    "inputs": [
      "_paper/paper.md",
      "_artifacts/json/debate_issue_007_r1_defend.json"
    ],
    "outputs": ["_artifacts/json/debate_issue_007_r1_synthesize.json"],
    "depends_on": ["debate_issue_007_r1_defend"],
    "status": "pending", "timeout_s": 1200,
    "output_format": "json_stdout",
    "route": "consensus"
  }
}
```

**Role rotation by round** (Route A only — Route B is one-shot, no rotation):

| Round | Prosecutor | Defender | Synthesizer |
|-------|-----------|----------|-------------|
| 1 | claude | codex | gemini |
| 2 | codex | gemini | claude |
| 3 | gemini | claude | codex |

Route B always assigns codex defender + gemini synthesizer (defender gets the stronger non-Claude code-reasoning model; synthesizer gets long-context arbiter). Within a single issue's debate, the tickets are strictly sequential. Across issues, they are parallel (bounded by agent-ctl's `--concurrent` cap).

### Gate helper canonical location

The single source of truth for the gate helper is the pseudocode in the **Wave 5b** section above (`should_escalate(row) -> (escalate, route, reason)` with Route A and Route B, and the `decide()` wrapper writing `gate_decision.json` with per-row `gate_decision` + a `by_route` summary). Previous editions of this file carried a duplicate four-way-only helper here; it has been removed to avoid schema split. If you need a standalone script, copy the Wave 5b snippet into a scratch file — do not maintain a second copy.

### Wave 6+ — Subsequent rounds (emitted after each synthesize completes)

After a `debate_<issue>_r<N>_synthesize` ticket completes, Claude reads the synthesis output. The `verdict` field decides whether round N+1 is funded:

**Route A verdicts:**

- `verdict: "prosecution_wins"` → **terminal**. No round N+1. Issue ships to the panel with the synthesizer's `surviving_text`.
- `verdict: "defense_wins"` → **terminal**. No round N+1. Issue dropped (recorded in debate trace + `dropped_by_defense.json`).
- `verdict: "split"` and `N < max_rounds` → emit round N+1 tickets, prosecuting the **surviving** (narrower) claim from `surviving_text`, not the original. Roles rotate.
- `verdict: "escalate"` and `N < max_rounds` → emit round N+1 tickets focused on the verifiable point named in `next_round_focus`. Roles rotate. Also flag for human review (record in `_artifacts/json/escalations.json`).

**Route B verdicts (terminal in one round by construction):**

- `verdict: "consensus_held"` → **terminal**. Issue ships to the panel with a "consensus survived red-team" badge. Synthesizer's `surviving_text`, if present, overrides the original claim text; otherwise keep the original `claim_under_challenge.claim`.
- `verdict: "consensus_broken"` → **terminal**. Issue dropped (recorded in debate trace + `dropped_by_red_team.json` with the defender's shared-hallucination analysis as drop reason).

Route B does not iterate. The red-team challenge is one-shot by design — the defender either finds evidence of shared misreading in round 1 or does not. A "split" outcome on Route B is not meaningful (who would split *against* three-family consensus plus evidence?). If the synthesizer cannot decide, it emits `consensus_held` conservatively — the onus is on the red-team to prove shared hallucination, not on the synthesizer to prove genuine flaw.

**There is no `converged` verdict.** It was removed in v2 — see `templates/synthesize.md` for rationale. Convergence-as-default produced 100% round-1 termination on the 2026-04-13 v3 run, draining all dialectic value.

**No tier-based pre-allocation of rounds.** Every issue starts with a budget of 1 round. Round 2 is funded **only when the synthesizer's verdict demands continuation** (`split` or `escalate`). Budget follows tension, not pre-assigned rank tier. Hard cap at `--max-debate-rounds` (default 2).

**Role rotation across rounds** (unchanged):

| Round | Prosecutor | Defender | Synthesizer |
|-------|-----------|----------|-------------|
| 1 | claude | codex | gemini |
| 2 | codex | gemini | claude |
| 3 | gemini | claude | codex |

### Wave 6.5 — DEPRECATED (v5-only)

Do not use the old post-debate calibration sub-DAG or the legacy report-centric handoff described in pre-v6 editions of this file. The authoritative v6 flow is Wave 5a → 5b → 5c → 5d above, then Wave 7 panel compilation/render below. `templates/calibrate.md` now describes the two-pass calibration flow that wraps debate; there is no longer a "calibration-after-debate-only" sub-DAG.

### Wave 7 — Panel compile + render (v6, emitted after calibration final_findings.json exists)

**Step 7a — Panel compile (inline orchestrator, no ticket).** Once `_calibration/final_findings.json` exists, Claude wraps it into `_artifacts/json/panel.json` by adding `paper`, `engine` (version + mode + families), `holistic_pass` (union attack-surface index from Phase 1), and `summary` metadata. The `findings[]` and `dropped_findings[]` arrays are copied through unchanged — panel rows follow `templates/schemas/panel_row.md` and are never reshaped at compile time. This is the ONLY step that writes `panel.json`; the renderer cannot produce it.

**Step 7b — Panel render ticket.** One ticket, per `templates/render_panel.md`. The panel renderer is a single long-context call that reads the compiled `panel.json` plus the paper and produces the markdown outputs in uniform voice.

```json
{
  "panel_render": {
    "id": "panel_render", "type": "render",
    "agent": "gemini", "model": "gemini-3.1-pro-preview", "family": "google", "flags": {},
    "prompt_path": "_artifacts/prompts/panel_render.md",
    "inputs": [
      "_artifacts/json/panel.json",
      "_paper/paper.md"
    ],
    "outputs": [
      "4_panel/panel.md",
      "4_panel/author_memo.md"
    ],
    "depends_on": [ "panel compile inline step (7a)" ],
    "status": "pending", "timeout_s": 1200,
    "output_format": "json_stdout"
  }
}
```

Outputs depend on `--mode`:
- `--mode author` → `4_panel/author_memo.md` + optional `4_panel/revision_plan.md`
- `--mode referee` → `4_panel/referee_memo.md` + optional `4_panel/referee_letter_draft.md`

Both modes always produce `4_panel/panel.md` (table view) from the already-compiled `_artifacts/json/panel.json`. The writer cannot invent findings, change `calibration.verdict`, or hide dropped rows — the orchestrator re-verifies these constraints post-render and regenerates once on any violation. Row shape authority: `templates/schemas/panel_row.md`.

Claude also updates `review.md` at the top of the paper folder to set `phase: complete` and populate the summary section.

Fallback model: `claude-opus` when the panel has >30 findings or gemini is rate-limited.

### Wave 7c — A/B evaluation (optional, emitted after panel render completes, only on user request)

Evaluation is a **self-contained sub-DAG** under `<paper-folder>/_evaluation/`, with its own `tickets.json`, `prompts/`, `annotations/`, `sessions/`, and results. Findings are blinded with randomised `BF###` IDs (not `merged_NNN`); the `blind_id → true_version/true_id` map lives only in `_evaluation/manifest_blind.json` and is never shown to the annotator. Default annotator: **codex with `gpt-5.4-mini`** (matches the 2026-04-12 manual baseline). See `templates/evaluation.md` for protocol and `templates/evaluate.md` for the prompt body.

Emission procedure (orchestrator runs this inline before `run-dag`):

1. Collect findings from every review version being evaluated (single-review: current `_calibration/final_findings.json`; cross-review: gather from each frozen version's calibrated set or equivalent).
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
3. Claude executes `orient_claude` inline; `agent-ctl run-dag` executes orient_codex and orient_gemini.
4. Claude renders `0_orientation/`.
5. Claude emits holistic tickets, builds `attack_surface_index.json`, then emits the 9 discovery tickets and the optional baseline sentinel.
6. Claude renders `0_holistic/` and `1_discovery/`.
7. Claude executes `merge_rank` inline, writing ranked artifacts plus `panel_rows_candidates.json`, then renders `2_ranking/`.
8. Claude emits verification work only when needed and renders `2_ranking/verification.md`.
9. Claude emits calibration pass-1 tickets, applies the Route A / Route B gate over survivors, and emits debate tickets only for gate-clearers.
10. For each completed synthesis, Claude renders `3_debates/<rank>_<slug>/...` and emits another round only when the synthesizer explicitly demands continuation and budget remains.
11. After calibration finalization, Claude compiles `_artifacts/json/panel.json`.
12. Claude emits one `panel_render` ticket; after it completes, `4_panel/` is rendered and `review.md` is marked `phase: complete`.

Between waves, Claude's job is two-fold: **render** the JSON outputs into curated markdown, and **emit** the next wave's tickets. Both happen before the next `run-dag` invocation. See `templates/obsidian_render.md` for the exact rendering templates.

## Resumability

Because every ticket is a file on disk inside the paper folder, the entire pipeline can be resumed at any point. To resume a review:

1. Open the paper folder in Obsidian (or cd to it in the filesystem)
2. `agent-ctl dag-status _artifacts/tickets.json` — inspect what is done
3. `agent-ctl run-dag _artifacts/tickets.json --cwd .` — execute any remaining ready tickets
4. If Claude-typed tickets are pending (orientation, holistic, discovery, merge, panel compile, or wave-emission logic), re-invoke `/disputatio` on the same paper folder and Claude resumes those inline

The skill is fully resumable: closing Claude Code, restarting later, and re-running the skill on the same paper folder picks up where it left off.

## The Obsidian folder structure IS the review

Unlike earlier designs, there is no separate Obsidian "live note" that tracks progress. The paper folder itself — with its numbered subfolders and the `review.md` at the top — IS the live report. It updates as Claude renders outputs into it. `review.md` tracks the current phase in its frontmatter and the top-of-file "Status" line.

See `templates/obsidian_structure.md` for the full folder spec and `templates/obsidian_render.md` for how each JSON artifact is rendered into markdown.
