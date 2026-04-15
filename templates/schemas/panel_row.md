# Canonical v6 panel-row schema

**Single source of truth for the panel-row object.** Every stage from merge through render operates on the same row shape. When any other file disagrees with the shape declared here, fix the other file — do not redefine the row elsewhere.

## The row

```json
{
  "finding_id": "F001",
  "concern": "one-sentence falsifiable claim about the paper",
  "category": "proof | empirics | identification | framing | robustness | interpretation | notation | other",
  "severity": "material | local | nit",
  "confidence": { "band": "high | medium | low | not_calibrated" },
  "priority": {
    "author": "fix_before_submit | watch_in_review | can_ignore | null",
    "referee": "endorse | verify_before_endorsing | skip | null"
  },
  "evidence": [
    {
      "quote": "verbatim substring of _paper/paper.md",
      "location": "section / page / equation anchor",
      "why": "one sentence explaining how the quote anchors the claim",
      "support_type": "direct_quote | derived_inference"
    }
  ],
  "architecture_support": {
    "anthropic": { "supports": true, "methods": ["broad_critic"], "notes": "..." },
    "openai":    { "supports": true, "methods": ["narrow_evidence"], "notes": "..." },
    "google":    { "supports": false, "methods": [], "notes": "..." }
  },
  "debate_hint": {
    "cross_family_disagreement": "strong | moderate | none",
    "evidence_conflict_in_paper": "yes | no | unknown",
    "severity_sensitive": true
  },
  "calibration": {
    "verdict": "supported | calibrated_narrowed | overclaimed | unsupported | dropped",
    "quote_verified": "yes | partial | no",
    "annotator_notes": "one-paragraph rationale",
    "narrowing_notes": "if a polish rewrite occurred, what changed",
    "drop_reason": "if dropped, one-sentence reason"
  },
  "calibration_pass1": { "...same shape as calibration..." },
  "gate_decision": {
    "escalated": true,
    "reason": "all_conditions_met | cross_family_disagreement_not_strong | no_evidence_conflict_in_paper | severity_not_sensitive_to_verdict | calibration_pass1_verdict_not_user_visible:<verdict> | severity_not_user_visible:<severity>"
  },
  "debate": {
    "triggered": true,
    "reason": "gate-clearer reason string",
    "verdict": "prosecution_wins | defense_wins | split | escalate | not_run",
    "surviving_text": "synthesizer's report-grade paragraph if verdict != not_run",
    "what_survived": "summary of what the debate settled",
    "history": [
      { "stage": "candidate | merged | debated | calibrated", "claim": "...", "outcome": "kept | narrowed | dropped" }
    ]
  },
  "calibration_pass2": { "...same shape as calibration, populated only for debated rows..." },
  "suggested_action": {
    "author":  { "fix": "concrete sentence-level edit" },
    "referee": { "how_to_use": "what to do with this finding in your report" }
  },
  "audit": {
    "source_candidate_ids": ["hc_claude_007", "bc_gemini_003"],
    "prompt_trace_ids": ["_artifacts/prompts/discover_claude_holistic_candidates.md", "..."],
    "status": "survived | dropped"
  },
  "status": "survived | dropped_pass1 | dropped_by_defense | dropped_pass2 | dropped_at_merge"
}
```

## Invariants

The same row object persists from **merge → pass 1 → gate → debate → pass 2 → final_findings → panel**. Phases add fields, they do not reshape the row.

- `merge` sets: `finding_id`, `concern`, `category`, `severity`, `confidence.band` (= `"not_calibrated"` at this stage), `evidence`, `architecture_support`, `debate_hint`, `audit.source_candidate_ids`, `audit.prompt_trace_ids`, `audit.status` (= `"survived"` unless killed at merge).
- `calibration_pass1` writes: `calibration_pass1` and the current `calibration` fields (`calibration` is the authoritative verdict, `calibration_pass1` is the audit record).
- `gate_decision` is populated by the inline four-way gate helper (Wave 5b).
- `debate` is populated only for rows with `gate_decision.escalated: true`, and only after Wave 5c synthesis completes.
- `calibration_pass2` and an updated `calibration` verdict are populated only for rows that went through debate (Wave 5d).
- `priority` is populated by the render step (mode-dependent); untouched until Phase 6.
- `suggested_action` is populated by the render step.

## Authoritative verdict vs audit history

`calibration` holds the *current authoritative verdict* on the row. `calibration_pass1` and `calibration_pass2` hold the historical passes and are never mutated after they are written. If a row went through only Pass 1, `calibration` equals `calibration_pass1`. If a row went through both passes, `calibration` equals `calibration_pass2` (since Pass 2 reflects the latest narrowing).

This matters because render and downstream consumers read `calibration` — never `calibration_passN` directly.

## Files that reference this schema

The following files MUST describe the row shape consistently with this file. If they disagree, patch them toward here:

- `SKILL.md` — phase descriptions and explicit rules (especially the four-way gate)
- `templates/merge_and_rank.md` — row emission in Step 6
- `templates/calibrate.md` — two-pass flow and disposition
- `templates/emit_tickets.md` — Wave 5a/5b/5c/5d and panel compilation
- `templates/render_panel.md` — display rules and memo rendering
- `templates/evidence_compile.md` — field constraints on evidence[]
- `README.md` — overview (describe the shape loosely, link to this file for the detailed spec)

## panel.json vs final_findings.json vs panel_rows_candidates.json

Three files hold rows at different stages:

- `_artifacts/json/panel_rows_candidates.json` — rows written by merge Step 6, before calibration or debate. Shape: `{"survived": [row, ...], "dropped_at_merge": [row, ...]}`.
- `_calibration/final_findings.json` — rows after Pass 1, gate, debate (if any), and Pass 2. Shape: `{"findings": [row, ...], "dropped_pass1": [row, ...], "dropped_by_defense": [row, ...], "dropped_pass2": [row, ...]}`.
- `_artifacts/json/panel.json` — the orchestrator wraps `final_findings.json` with `paper`, `engine`, `holistic_pass`, and `summary` to produce the canonical panel artifact. Shape: full v6 panel JSON per `docs/v6-upstream-plan.md` with a `findings[]` array pointing at rows matching this schema.

The render step reads `panel.json` only. It does NOT read `panel_rows_candidates.json` or `final_findings.json` directly.
