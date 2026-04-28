# Calibration prompt (v6, two-pass wrapping debate)

Calibration is a **blinded per-finding quality gate** that wraps debate in v6: Pass 1 runs on every candidate panel row from merge, the two-route escalation gate (Route A disagreement / Route B consensus override) reads Pass 1 results to decide which findings enter debate, and Pass 2 runs on debate survivors to narrow their `surviving_text` before the panel is rendered. This is the primary quality mechanism in the pipeline. The post-hoc evaluation (`templates/evaluation.md`) is a separate A/B comparison tool, not the calibration loop.

**Row shape authority**: `templates/schemas/panel_row.md`. Calibration adds `calibration`, `calibration_pass1`, and (for debated rows) `calibration_pass2` fields to each row; it never reshapes the row.

## Why this flow exists

v5 ran calibration after debate on the top-N by rank_score, then shipped a referee letter. Result: 56.2% overclaim rate on report-entering findings in the 2026-04-14 v4 run, and debate budget wasted on claims that a cheap first-pass calibrator would have killed or narrowed immediately. v6 reverses the order: calibrate first (cheap, kills obvious overclaims), then fire the two-route gate, then debate only on gate-clearers, then calibrate again on debate survivors.

## What this does NOT do

- Does not rediscover issues — if discovery missed something, calibration will not invent it (the Phase 1 holistic pass and Wave 2.5 baseline are the coverage mechanisms).
- Does not re-rank — `rank_score` from merge is preserved for panel ordering.
- Does not override the two-route gate — Pass 1's verdict feeds the gate but does not itself decide escalation.

## Which findings enter calibration — v6 two-pass model

**Pass 1 (Wave 5a, before the gate)**: every row in `_artifacts/json/panel_rows_candidates_verified.json` (the Wave 4 verify output) — or in `panel_rows_candidates.json` directly if the run skipped web verification via `--skip-web`. No filter; the pass annotates every `survived` row with `quote_verified` × `calibration` verdicts. Rows whose `web_verification.status == "refuted"` should bias the annotator toward `calibration: unsupported`, but the verdict is the annotator's, not the verifier's.

Disposition after Pass 1:

- `quote_verified: no` OR `calibration: unsupported` → drop. Written to `_calibration/dropped_pass1.json` with reason. Does NOT enter the two-route gate or debate.
- `quote_verified: partial` OR `calibration: overclaimed` → fire one polish-rewrite via `templates/polish.md`; re-annotate once **with an upgraded annotator** (codex gpt-5.4 non-mini, fallback sonnet) — NOT the same gpt-5.4-mini that ran Pass 1, to break correlated-error blind spots between the two mini reads. Then:
  - **Clean pass** (upgraded re-annotator returns unqualified `supported` + `quote: yes`, no hedging triggers — see below) → mark `calibration_pass1.verdict: calibrated_narrowed`, keep severity.
  - **Uncertain pass** (any one of the four triggers below fires) → mark `calibrated_narrowed` AND demote severity one tier (material → local, local → nit). Demote is the conservative fallback when the stronger re-annotator can't cleanly vouch for the narrowed claim.
  - **Still failing** (verdict `overclaimed`, `partial`, or `unsupported`; or `quote: no`) → drop. No further rewrites.
  - **Uncertainty triggers** (any one → demote, don't keep): (i) re-annotator does NOT return unqualified `supported`; (ii) justification contains hedging language (`ambiguous`, `unclear`, `partially`, `depends`, `borderline`, `missing`, `inferential`, `not explicit`); (iii) cited support is indirect rather than sentence-level/text-grounded; (iv) structured rubric fields disagree internally (e.g., weak quote evidence but verdict `supported`).
- `calibration: supported` + `quote_verified: yes` → mark `calibration_pass1.verdict: supported`.

Pass 1 survivors (supported or calibrated_narrowed) flow into Wave 5b gate evaluation.

**Pass 2 (Wave 5d, after debate)**: every debate survivor — Route A verdicts in {`prosecution_wins`, `split`, `escalate`} OR Route B verdict `consensus_held` — re-annotated against the synthesizer's `surviving_text` (or, on Route B `consensus_held` rows where the synthesizer produced no `surviving_text`, against the original `claim_under_challenge.claim`). Same rubric, same disposition rules. Written to `calibration_pass2` field.

Pass 2 does NOT fire on findings that bypassed debate — their Pass 1 verdict is final and flows straight to the panel.

**What does NOT enter calibration at any point:**
- Triaged findings from merge Step 1 (already dropped pre-merge).
- Findings killed by defender in Route A debate (verdict: `defense_wins`) — written to `_calibration/dropped_by_defense.json`, do not get a Pass 2.
- Findings dropped by Route B red-team (verdict: `consensus_broken`) — written to `_calibration/dropped_by_red_team.json`, do not get a Pass 2.
- `dropped_at_merge` items from merge Step 6's atomicity/validator rejections.

## Blinding

Same rules as `templates/evaluation.md`:

- Randomised `BF###` IDs assigned to every finding entering calibration.
- Manifest `_calibration/manifest_blind.json` maps `blind_id → true_id`. Annotator never sees it.
- Payload inlined into each prompt: only `{blind_id, claim, quote, quote_location, evidence}`. Strip `status`, `rank_score`, `sources`, `verdict`, `surviving_text`, debate trace, annotator notes.
- No side-channels: each prompt is self-contained with the finding plus the full paper text plus the rubric.

## Rubric (reused verbatim from `templates/evaluate.md`)

### Axis 1 — `quote_verified`
| Value | Meaning |
|---|---|
| `yes` | Quote appears verbatim (or near-verbatim with insubstantial OCR cleanup) at the cited location and supports the claim's premise. |
| `partial` | Quote exists but is paraphrased / misplaced / truncated in a way that changes meaning, or the location anchor is wrong. |
| `no` | Quote is fabricated or grossly misrepresented — does not appear in the paper in any recognisable form. |

### Axis 2 — `calibration`
| Value | Meaning |
|---|---|
| `supported` | Evidence establishes the claim as stated. |
| `overclaimed` | Real issue but the finding overstates severity / scope / certainty, or packages unsupported sub-claims inside a real one. |
| `unsupported` | Evidence does not establish the claim (misreading, style complaint, over-promoted nit, or the real issue is already acknowledged in the paper's text). |

If `quote_verified == "no"`, set `calibration = "unsupported"` automatically.

## Annotator output (same schema as post-hoc eval)

```json
{
  "blind_id": "BF001",
  "quote_verified": "yes | partial | no",
  "calibration": "supported | overclaimed | unsupported",
  "notes": "one-paragraph rationale; required for overclaimed, unsupported, partial, or no; optional for yes/supported"
}
```

`notes` is **required** when either axis is not the green-light value. Overclaim demotion uses `notes` as the rewrite seed for the polish pass.

## Disposition rules — demote-on-doubt default

After each annotation is written, the orchestrator disposes of the finding according to this table (no room for interpretation):

| Annotator output | Action on the finding |
|---|---|
| `quote_verified: no` + `calibration: unsupported` | **Drop** from report. Record in `_calibration/dropped.json` with annotator notes. |
| `quote_verified: partial` | **Attempt one rewrite** with the polish pass (see below) against the real passage the annotator names. Re-annotate the rewrite with an **upgraded annotator** (see "Upgraded re-annotator" below). If clean pass → mark `calibrated_narrowed`, keep severity. If uncertain pass (any of the four triggers below) → `calibrated_narrowed` AND demote one tier (material → local, local → nit). If still partial or worse → **drop**. |
| `calibration: unsupported` (with verified quote) | **Drop**. The claim doesn't follow from the quote, and no polish rewrite can fix that. |
| `calibration: overclaimed` | **Attempt one rewrite** that narrows the claim per the annotator's `notes`. Re-annotate with the **upgraded annotator**. If clean pass → `calibrated_narrowed`, keep severity. If uncertain pass → `calibrated_narrowed` AND demote one tier (material → local, local → nit). If still overclaimed → **drop** (no further rewrites, no second demotion). |
| `calibration: supported` + `quote_verified: yes` | Pass through unchanged. |

### Upgraded re-annotator (added 2026-04-15 after A/B evidence of correlated-error)

The first-pass annotator is gpt-5.4-mini (volume model, ~38 rows per run, cheap, rubric-bounded). The polish rewrite fires on a small subset (~8 rows per run). On those ~8 rows ONLY, the re-annotator upgrades to **codex `gpt-5.4`** (full, not mini; fallback sonnet). Cost delta ~$1-2 per run — trivial. Rationale: two gpt-5.4-mini calls on the same rubric share blind spots; the A/B against coarse.ink found 7 of 28 shipped findings still read as overclaimed to a fresh judge, all of them rows where mini-then-mini re-annotation said supported. A stronger model on the re-annotation attacks the correlated-error root cause instead of papering over it with automatic demotion.

### Uncertainty triggers — hard spec, not vibes

Even a stronger re-annotator can return a technically-passing verdict that's actually hedged. Fall back to demote (not drop, not keep-original-tier) when ANY of these hold:

1. The upgraded re-annotator does not return an **unqualified** `supported` + `quote: yes`. A verdict like `supported` with `quote: partial`, or `supported` attached to a two-sentence "this is mostly right but..." note, counts as qualified.
2. The `notes` field contains hedging language: `ambiguous`, `unclear`, `partially`, `depends`, `borderline`, `missing`, `inferential`, `not explicit`. String match is sufficient — we don't parse meaning.
3. The cited support is indirect rather than sentence-level/text-grounded — i.e., the annotator points at "the overall framing of Section 3" rather than a specific passage.
4. Structured rubric fields disagree internally — e.g., `quote_verified: partial` with `calibration: supported`, or `quote_verified: yes` but the `notes` describe the quote as truncated.

Any one trigger fires the demote fallback. All four must be absent for the row to keep its original tier.

*Demote-on-doubt* applies to edge cases — if the annotator's notes contain hedging language ("arguably", "could be read as", "depends on interpretation") on an `overclaimed` judgement, the orchestrator treats it as overclaimed anyway and runs the rewrite. The bias is toward a tighter report with fewer concerns.

## Polish rewrite pass

When a finding is `partial` or `overclaimed`, a single polish call rewrites it. The rewrite model is **gemini-3.1-pro-preview** (fluid referee-letter prose, matches the editorial-pass role in Phase 6.5). Prompt:

```
You are rewriting ONE finding from a referee report. The finding was flagged by a blinded annotator as {partial|overclaimed} with the following notes:

<annotator.notes>

Here is the original finding: <finding JSON>

Here is the relevant paper text: <quote + surrounding 20 lines>

Your job: produce a rewritten claim that is as strong as the paper's text supports, no stronger. The new claim MUST:
- Quote the paper verbatim (no truncation, no paraphrase).
- Not include sub-claims the annotator called unsupported.
- Be phrased so that a second blinded annotator would rate it `supported`.
- Use the paper's own hedges (if the paper says "as long as the budget is small", you cannot strip that qualifier).

Output JSON with the same shape as the input, just a rewritten claim, quote, evidence, and (if relevant) surviving_text.
```

The rewrite is then re-annotated. Two annotations per finding in the worst case; most findings need one.

## Tickets

Each finding entering calibration produces one `calibrate` ticket (plus optionally one `polish` ticket if the first annotation fails). Default annotator: **codex with `gpt-5.4-mini`** (matches the 2026-04-12 baseline, cheap, fast). Fallback: claude-sonnet-4.6 when codex is rate-limited and the paper is long enough to need `>50K` tokens of context.

```json
{
  "calibrate_BF001": {
    "id": "calibrate_BF001",
    "type": "calibrate",
    "agent": "codex",
    "model": "gpt-5.4-mini",
    "family": "openai",
    "flags": {},
    "prompt_path": "_calibration/prompts/BF001.md",
    "inputs": ["_calibration/prompts/BF001.md"],
    "outputs": ["_calibration/annotations/BF001.json"],
    "depends_on": [],
    "status": "pending",
    "timeout_s": 900,
    "max_attempts": 2
  }
}
```

Run the sub-DAG with `agent-ctl run-dag <paper>/_calibration/tickets.json --cwd <paper> --concurrent 4`. After all `calibrate` tickets complete, the orchestrator applies disposition rules inline, emits any required `polish` tickets, re-runs them, and produces `_calibration/final_findings.json` — the calibrated set that feeds the final report.

## Directory layout

```
<paper>/_calibration/
├── manifest_blind.json          blind_id → true_id (private)
├── tickets.json                 calibration sub-DAG
├── prompts/<BF###>.md           one prompt per finding
├── annotations/<BF###>.json     annotator output
├── rewrites/<BF###>.json        polish pass output (if any)
├── sessions/<BF###>.log         session archive
├── final_findings.json          machine truth for the final report
├── dropped.json                 findings killed by calibration with reasons
├── demoted.json                 findings demoted with old_tier → new_tier
└── 00_calibration.md            human-readable scorecard
```

## Aggregator (inline, no ticket)

After all annotations and any rewrites complete:

1. Read every `_calibration/annotations/*.json` (and rewrite annotations if present).
2. Join with `manifest_blind.json` → recover `true_id` for each annotation.
3. Apply disposition rules → produce `final_findings.json`:

```json
{
  "kept": [{"true_id": "merged_002", "severity": "material", "calibration_verdict": "supported", "claim": "...", "quote": "...", ...}],
  "demoted": [{"true_id": "merged_027", "old_severity": "material", "new_severity": "local", "reason": "overclaimed → polish → re-annotation passed but uncertainty trigger (hedging language 'partially' in notes); auto-demoted one tier"}],
  "dropped": [{"true_id": "merged_019", "reason": "aggregated sub_findings failed verbatim check"}],
  "summary": {
    "entered_calibration": 16,
    "kept": 10, "demoted": 5, "dropped": 1,
    "overclaim_rate_pre":  0.562,
    "overclaim_rate_post": 0.05
  }
}
```

4. Write `_calibration/00_calibration.md` as a human-readable scorecard: kept/demoted/dropped counts, per-finding table, pre/post overclaim rate, link to `manifest_blind.json` for audit.

5. `final_findings.json` already contains the final-state panel rows plus the three `dropped_*` arrays — it is the machine truth. Phase 6 (`templates/emit_tickets.md` Wave 7 panel compilation) wraps it inline with `paper`, `engine`, `holistic_pass`, and `summary` metadata to produce `_artifacts/json/panel.json`. The render ticket reads `panel.json` only. `panel_rows_candidates.json` is upstream-only (merge Step 6's handoff into calibration); it is never read after Pass 1 starts. The input chain is `panel_rows_candidates.json → calibration (Pass 1 → gate → debate → Pass 2) → final_findings.json → panel.json`. Row shape is defined once in `templates/schemas/panel_row.md`; calibration adds fields to each row, it does not reshape the row.

## Relation to the post-hoc evaluation

Phase 7 post-hoc evaluation (old Phase 5, `templates/evaluation.md`) is no longer the calibration loop. It is now **A/B comparison only**: used to evaluate whether disputatio v5 beats disputatio v4 (or coarse, or Stanford Agentic) on the same paper. The post-hoc annotator sees the final report's content and scores it — but the content has already been calibrated in Phase 5. Post-hoc overclaim rate in v5 should be very low by construction (that's the whole point); if it is not, the Phase 5 annotator is under-demoting and needs tightening.

Running both Phase 5 and Phase 7 on the same run is fine — Phase 7 provides an independent check that the pre-report calibration actually worked. A large gap between Phase 5 and Phase 7 overclaim rates is a bug in one of them.
