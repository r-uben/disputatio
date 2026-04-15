# 2026-04-14 — v6 upstream positioning and implementation plan

## What changed

Wrote `docs/v6-upstream-plan.md` to re-anchor disputatio around the actual wedge:

- pre-submission author review
- referee assistance

The key change is product-level, not cosmetic. The primary output is now specified as a finding panel with evidence, cross-family support, debate history, calibration verdict, and mode-specific action routing. A referee-letter draft remains useful, but only as a secondary renderer over the same finding rows.

## Why

The repo's current center of gravity is still "seven-method debate that writes a referee report." That was pulling positioning, schema, and pipeline design toward the wrong product. The user's correction is right: the commercially relevant question is not whether we can write a better revision memo after review. It is whether we help authors catch referee-grade concerns before submission, and help referees write sharper first-round reports.

That shift changes the right unit of truth. The unit is not the final paragraph. It is the atomic finding with provenance and calibrated disposition.

## Main decisions

1. Add a holistic conceptual pass before discovery. Coverage is still the main risk, and a paper-level attack-surface map is the cheapest way to reduce blind spots.
2. Shrink discovery from the current method-heavy 18-ticket shape to a smaller architecture-by-role layout. The old design over-invests in correlated generation and under-invests in evidence handling.
3. Keep debate, but only as escalation court for contested or high-impact findings. Default debate on a top-N ranked set is expensive and often solves the wrong problem.
4. Keep calibration and quote validation. Those are not ancillary. They are now part of the product story because they create visible drop transparency.
5. Replace `final.json` with a run object whose core payload is a list of finding rows. Mode-specific outputs render from the same row set.

## Pushback recorded

Two parts of the requested framing needed tightening:

- A user-facing `0-100 confidence` number implies more precision than we have unless calibration is tested on held-out papers. Keep the scalar internally, but present it as calibrated estimate plus band until validated.
- Cross-family agreement is not "truth by vote." It is a support signal. The decisive artifact is still the evidence-backed finding after narrowing or drop.

## Rejected alternatives

- Keeping the current primary deliverable as a referee letter and only adding panel metadata around it. Rejected because it preserves the wrong center of gravity and keeps prose quality over decision support.
- Keeping the full 18-sweep discovery design and only adding a holistic pass on top. Rejected because the extra method theater is expensive and likely still too correlated to justify itself.
- Removing debate entirely. Rejected because the contested-case audit trail is part of the differentiation, but it should be exceptional rather than default.
