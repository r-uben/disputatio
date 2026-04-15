# 2026-04-14 — v6 upstream pivot: panel-first product, holistic pass, debate-as-escalation

## Why

After running v5 on Galeotti-Golub-Goyal (Econometrica 2020) and comparing head-to-head against a coarse-style single-shot baseline, two things became clear:

1. **Disputatio cannot win a pure "better referee letter" contest** against a strong single-shot model. The architecture favours single-shot: uniform voice, low latency, low cost. Coarse's $2/minutes benchmark is structurally cheaper than our $30-50/hours — we cannot close that gap by optimizing prose.

2. **The wedge is upstream decision support**, not prose. A single-shot review produces one polished opinion whose overclaim rate the reader cannot evaluate without doing the work themselves. A cross-architecture panel with calibration, provenance, and drop transparency produces a different object: a **list of concerns the reader knows how to act on**, with severity / confidence / priority labels that tell them which to fix, which to verify, and which to ignore.

The two primary use cases were under-specified in v5's framing ("referee report as THE deliverable"):

- **Author pre-submission review**: catch what referees will catch and fix it before submission.
- **Referee assistance**: draft and sharpen a first-round review before sending it to the editor.

v5 produced a referee letter as primary output. v6 pivots to produce a finding panel as primary, with prose memos as mode-specific secondary renderings.

Full strategic analysis in the v5 post-run summary and in the codex consultation captured at `docs/v6-upstream-plan.md`. This log entry records what changed structurally.

## What changed

### Product positioning

- **Primary deliverable**: finding panel (`panel.json` + `4_panel/panel.md`), not referee letter.
- **Secondary deliverables**: mode-specific prose memo (author or referee), optional revision plan (author) or referee-letter draft (referee). All derived from the panel; the writer cannot invent findings.
- **Two modes**, one engine: `--mode author` and `--mode referee` differ only in priority label vocabulary and memo framing. Same 9 discovery tickets, same calibration, same panel rows.
- **Dropped findings surfaced, not hidden**: every panel output shows which concerns were killed by debate defenders or dropped by calibration, with the reason. The system demonstrates restraint; prior versions hid drops.

### Architecture

- **Phase 1 holistic pass added** (new). Three agents × one holistic pass = 3 tickets that produce `paper_spine`, `main_claims`, `attack_surfaces`, `likely_referee_questions`, `evidence_heavy_zones`. Output fed into Phase 2 discovery as shared context. Closes the "conceptual-scope coverage" gap that single-shot readers exploit.
- **Phase 2 discovery cut from 18 tickets to 9**. Three tracks per family: holistic candidate generation, broad critic (absorbs former M0 + M2 + M5), narrow evidence-judgment (M3 + M4 + M6 on priority attack surfaces). Candidates are category-typed at write time (proof / empirics / identification / framing / robustness / interpretation / notation / other).
- **Evidence compiler inline**. Every candidate finding passes through a compiler that pins the verbatim quote, the location, and whether support is direct or derived. No finding progresses without an evidence object.
- **Phase 4 debate is escalation-only, not default**. Four-way gate: cross-family disagreement real, evidence on both sides, severity would change on verdict, finding would otherwise be user-visible. Most findings do not trigger debate. Two rounds maximum default (down from three).
- **Phase 6 rendering is single-writer, not fragment assembly**. One long-context call reads the entire panel and produces all three outputs (panel table, memo, optional auxiliary) in uniform voice. Fixes the prose-uniformity complaint from v5.

### Schema

The `final.json` from v5 is replaced by `panel.json`. Top-level includes paper metadata, engine metadata (version, mode, families), `holistic_pass` block, `findings[]` with per-row evidence / architecture support / debate trail / calibration verdict / mode-specific priority / suggested action, `dropped_findings[]` preserved with reasons, and a `summary` block with top priorities and memo pointers. Full schema in `docs/v6-upstream-plan.md` and `templates/render_panel.md`.

## Files touched

- `README.md` — landing page rewritten around two modes + finding panel + "not a polished letter" framing. No mention of external competitors on the landing page per user instruction.
- `SKILL.md` — top-level repositioning; "seven methods" section replaced with "three discovery tracks"; Phase 1 holistic pass added; Phase 2 discovery reduced to 9 tickets; Phase 4 debate re-scoped to escalation-only; Phase 6 final-report section rewritten as panel + renderer spec. Phase numbering shifted (0 orient, 1 holistic, 2 discovery, 3 merge+rank+verify, 4 debate, 5 calibrate, 6 panel, 7 A/B eval).
- `templates/holistic.md` (new) — holistic pass prompt: paper spine, main claims, attack surfaces, likely referee questions, evidence-heavy zones.
- `templates/render_panel.md` (new) — panel renderer prompt: single-writer, three outputs, calibration-transparent (dropped findings always surfaced), mode-specific rendering.

## What did NOT change yet

Deferred to follow-up passes:

- `templates/merge_and_rank.md` still describes an issue register; needs v6 rewrite to produce panel rows directly.
- `templates/emit_tickets.md` still describes 18 discovery tickets; needs v6 wave diff (Wave 2 becomes 3 holistic + 9 discovery = 12 tickets, Wave 4.5 baseline-diff may be retired).
- `templates/calibrate.md` still describes writing to `final_findings.json`; schema-compatible with v6 but the output-target language should be updated to "panel rows".
- `templates/prosecute.md` / `defend.md` / `synthesize.md` work unchanged for escalation-only debate; no edits strictly needed, but the "top-third of issues" framing in prosecute.md is now misleading.
- `templates/baseline.md`: the coarse-style baseline was a v5 safety net. v6's holistic pass supersedes part of its role — if the holistic pass closes the coverage gap, Tier 2 baseline-diff may be retired entirely. Measurement needed.
- `templates/polish.md` survives as the Phase 5 overclaim rewrite step; the Phase 5.5 editorial polish from v5 is replaced by `templates/render_panel.md`.
- `templates/final_report.md` is now legacy; render_panel.md replaces it.

## Testing

Not yet. The v6 scaffolding is committed as templates + SKILL + README. The next meaningful action is a v6 run on the Galeotti-Golub-Goyal paper using the new holistic pass + 9-ticket discovery, so we can measure:

1. Does the holistic pass catch the Section 5 framing / Ballester conflation / planner-G-knowledge concerns that coarse caught and disputatio missed in v3?
2. Does Phase 4 debate fire on fewer findings (5 or less) vs v5's 8?
3. Does the single-writer renderer produce more uniform prose than v5's fragment assembly?
4. Does calibration still drop ~25% of candidate report entries? (Over-dropping would mean the engine is being too conservative post-holistic.)
5. Final overclaim rate and user-visible support rate — should be comparable to or better than v5 (0% user-visible overclaim, 55-80% support).

If those hold, the pivot succeeded. If coverage regresses or debate escalates too often, iterate.

## Next

1. Update `templates/merge_and_rank.md` and `templates/emit_tickets.md` for the 9-ticket shape and panel-row output.
2. Update `templates/calibrate.md` output target language.
3. Run v6 on Galeotti-Golub-Goyal 2020 (reusing the archived paper.md + figures; fresh holistic/discovery/merge/verify/debate/calibrate/render passes).
4. Measure against the 5 criteria above.
5. Ship or iterate.
