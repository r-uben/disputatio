# Section brief — §6: auditable disposition trail

**Section title (working):** Pattern 5: Auditable disposition trail

**Word target:** 400–600 words. This is the shortest section in the note. Resist expansion — the pattern is structurally simple and the prose should reflect that.

**Output path:** `docs/research-notes/methodology-note/sections/06_disposition_trail.md`

## What the section must do

Establish the fifth architectural pattern: every candidate finding that did *not* ship to the final panel is preserved on disk with a structured drop reason. The pipeline's restraint becomes auditable. Show why this is a precision signal in its own right — a reviewer that can show its work on rejections is more trustworthy than one that only shows survivors.

This section is the shortest and the most mechanically simple. The trap is over-explaining. The pattern is "log every drop with reason" — the value is in *why that is load-bearing*, not in the implementation detail.

## Key claims the section must support

1. **What the disposition trail is.** A structured `dropped_findings[]` artifact recording every candidate that was rejected at any phase. Each drop carries: original candidate (verbatim quote + family + track that produced it), the phase where it was dropped (triage merge, Route B red-team, calibration Pass 1, polish-rewrite, re-annotation), the rule or annotator that dropped it, and a one-sentence reason. The trail is part of the published panel artifact, not an internal log.

2. **Why this is a precision signal, not just transparency.** A reader who can see what got rejected — and why — can calibrate how trustworthy the shipped findings are. The disposition trail makes the system's *restraint* visible. Reviewers that ship everything and hide the rejection criteria look more impressive but are less auditable. The architectural commitment is to make the rejection function inspectable.

3. **The Zhang empirical anchor.** Today's Zhang run produced 80 raw candidates across the nine discovery tickets, merged to 34 atomic findings, of which 25 shipped to the final panel and 9 dropped with structured reasons. The 9 drops include Pass-1-annotator misreads (the annotator flagged a finding as overclaiming, polish-rewrite attempt failed to narrow it, the finding dropped at re-annotation), Route-B mode-fired diagnoses (three consensus findings broken by surface-pattern overfit, notation collision, and surface-pattern overfit again — each named in the trail), and a small number of straight calibration drops (the candidate's verbatim quote did not actually substring-match the paper, killed by the programmatic validator). Use 2–3 of these as illustrative examples, do not enumerate all 9.

4. **Why the auditing party can be the same as the author of the manuscript.** Disposition trails serve two readers: the human referee or paper author reading the report, and the methodology auditor looking at the pipeline itself. For the first, the trail surfaces which concerns the system considered and rejected — useful for both confirming the author's own internal worries and surfacing concerns the human reader might have wanted raised. For the second, the trail is where systematic over-claiming or systematic under-claiming becomes visible.

## Source material

Required reading:

- `templates/calibrate.md` — calibration's drop-vs-demote-vs-rewrite branches are the dominant drop site
- `templates/synthesize.md` — Route B's `consensus_broken` branch is the second-largest drop site
- `templates/merge_and_rank.md` — the programmatic verbatim-quote validator is the third
- `docs/log/2026-05-20_strict-blind-discipline.md` — for the Zhang disposition numbers (80 → 34 → 25+9)
- `draft.md` §§1-5 for tone and to ensure no overlap with §§2-5

Optional:

- The `dropped_findings[]` block in any recent `4_panel/panel.json` for the actual field shape (do not invent fields the implementation does not produce)

## Domain-portability discussion

Two paragraphs at the end:

- **The trivial part:** any pipeline that has a drop site can write a structured record. Implementation cost is one log call per drop, plus a renderer that surfaces drops in the final artifact.
- **The hard part:** *using* the trail to tune the rubric. The interesting questions a domain forker can ask of their own trail — "is the system systematically dropping findings about X?", "is calibration over-pruning a particular finding category?" — require enough volume (multiple papers) to see patterns. A single review's trail is too small a sample for that diagnostic. The pattern enables analysis it does not perform.

## Anti-patterns to avoid

- Over-claiming that the trail itself catches errors. It does not. It makes them *inspectable*. The trail is a substrate for trust, not a mechanism that produces correctness.
- Enumerating all 9 Zhang drops. Two or three illustrative examples maximum.
- Citing internal file paths (`panel.json`, `dropped_findings[]`) without translating them to what they contain. The reader is a researcher in an adjacent field, not a disputatio user.
- Making the section longer than it needs to be. If a paragraph could be cut without losing a claim, cut it.

## Open questions to flag in your output (if relevant)

- Whether the drop schema is rich enough. Today the drop record has phase, rule/annotator, and one-sentence reason. Whether a richer schema (counterfactual: "would have shipped if X were true") would enable better diagnostics is unresolved.
- Whether drops should ever be re-elevated. Today the trail is one-way; a candidate dropped at calibration cannot be re-promoted by a later phase. The downstream-effects question of whether a calibrated-drop should still inform a related shipped finding's confidence weighting is open.
