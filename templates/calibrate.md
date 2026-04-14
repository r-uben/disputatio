# Calibration prompt (Phase 5, pre-report)

Calibration is a **blinded per-finding quality gate** that runs between debate and final-report. It catches overclaimed and unverifiable findings *before* they enter the referee letter, not after. Replaces the old post-hoc evaluation as the primary calibration mechanism for any candidate report content. The post-hoc evaluation (`templates/evaluation.md`) remains available for A/B comparison across review versions but is no longer the pipeline's calibration loop.

## Why this runs

The 2026-04-14 v4 run on Galeotti-Golub-Goyal shipped a report with 56.2% overclaim rate on its 16 report-entering findings (vs v3's 37.5% on the top-8 debated cohort). Diagnosis: the v4 redesign correctly routed strong-consensus issues away from the debate stage's closure ritual, but that ritual had been doing unacknowledged polish work — softening overclaimed raw merge_rank language into narrower, more defensible synthesizer `refined_claim` text. Removing debate on settled issues removed the softener. Phase 5 calibration restores the softener as a cheap single-model check, without the theatre cost of full dialectic.

## What this does NOT do

- Does not rediscover issues — if discovery missed something, calibration will not invent it (run the coarse-style baseline diff instead).
- Does not re-rank — `rank_score` from merge is preserved.
- Does not re-adjudicate debated issues — `prosecution_wins` and `defense_wins` verdicts stand. Calibration operates on the *surviving_text* of debated winners (prosecution_wins + split) and on the raw claim of settled issues; it can demote or rewrite but cannot overturn a debate verdict.

## Which findings enter calibration

**Every finding that would otherwise enter the final report**:
- All `status: settled` merged issues (they skipped debate — calibration is their only quality gate).
- All debated issues with verdict `prosecution_wins` (material concerns) — calibrate the synthesizer's `surviving_text`.
- All debated issues with verdict `split` (local concerns) — calibrate the narrower surviving claim.
- All debated issues with verdict `escalate` — calibrate the open question; overclaimed escalations get reworded to more cautious phrasing.
- Aggregated findings: calibrate each `sub_finding` independently (same rule as post-hoc evaluation).

**What does NOT enter calibration:**
- `defense_wins` debated issues (already dropped from report).
- Triaged findings (already gone at merge).
- `appendix_issues` (optional — run calibration on them if budget allows; otherwise ship with a note that calibration did not check them).

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
| `quote_verified: partial` | **Attempt one rewrite** with the polish pass (see below) against the real passage the annotator names. Re-annotate the rewrite once. If second annotation still partial or worse, drop. |
| `calibration: unsupported` (with verified quote) | **Drop**. The claim doesn't follow from the quote, and no polish rewrite can fix that. |
| `calibration: overclaimed` | **Attempt one rewrite** that narrows the claim per the annotator's `notes`. Re-annotate the rewrite once. If still overclaimed → **demote one tier** (material → local, local → appendix, appendix → drop). No more rewrites. |
| `calibration: supported` + `quote_verified: yes` | Pass through unchanged. |

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
  "kept": [{"true_id": "merged_002", "tier": "settled", "claim": "...", "quote": "...", ...}],
  "demoted": [{"true_id": "merged_027", "old_tier": "material", "new_tier": "local", "reason": "calibration overclaimed, rewrite retained overclaim on re-annotation"}],
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

5. The final-report ticket reads `final_findings.json` (not `ranked_issues_verified.json`) as its input source of truth.

## Relation to the post-hoc evaluation

Phase 7 post-hoc evaluation (old Phase 5, `templates/evaluation.md`) is no longer the calibration loop. It is now **A/B comparison only**: used to evaluate whether disputatio v5 beats disputatio v4 (or coarse, or Stanford Agentic) on the same paper. The post-hoc annotator sees the final report's content and scores it — but the content has already been calibrated in Phase 5. Post-hoc overclaim rate in v5 should be very low by construction (that's the whole point); if it is not, the Phase 5 annotator is under-demoting and needs tightening.

Running both Phase 5 and Phase 7 on the same run is fine — Phase 7 provides an independent check that the pre-report calibration actually worked. A large gap between Phase 5 and Phase 7 overclaim rates is a bug in one of them.
