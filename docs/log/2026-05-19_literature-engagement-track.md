# 2026-05-19 — Literature engagement track (closes #33)

## Why

End-to-end disputatio v6 run on a confidential AER pre-submission paper by Anthony Zhang ("Markets for Price Risk", AER MS#2026-0450) with post-hoc comparison against the actual AER Ref #2 report. Result:

- 4/7 main Ref #2 themes independently matched
- 2 partially matched
- **3 missed entirely — all in the "what is missing *around* the paper" category**

The 3 misses cluster cleanly:

| Miss | Ref #2 emphasis | Disputatio gap |
|---|---|---|
| Literature positioning | Named 8 specialised refs (Breon-Drish, Malamud-Trubowitz, HMT, Martin, Brennan-Cao, GPP, Rostek-Yoon, Elul) | Zero of these surfaced — closed-book pipeline, no retrieval layer |
| Quantitative anchoring | Asked for calibration / comp statics / commercial-vs-noncommercial position data | No quant-anchoring prior in the taxonomy |
| Expositional craft | Section ordering, Claim → Lemma renaming, unify inequalities, symbol table, length trim, running-example placement | Taxonomy has no "the paper would read better if X" slot |

The author's own evaluation of Ref #2 (public tweet, 2026-05-19) singled out "helpful old references I'd never heard of" + "great expositional comments" + "no requests for BS pointless extensions" as what made the report valuable. Disputatio missed exactly what the author found most valuable.

## Codex review (gpt-5.4, high effort)

Asked codex for a skeptical second opinion. Key pushbacks:

1. **The miss is a retrieval problem, not a cross-family reasoning problem.** Pure LLM recall overproduces canonical references and underproduces long-tail specialised adjacency. Don't fan out across three families' memories — fan in to one shared retrieval ticket with a graph or search backend.
2. **Place the literature lookup UPSTREAM of discovery, not as post-hoc panel rows.** A good old-reference set changes the agents' understanding of novelty, scope, comparators, and quantitative-anchoring expectations. That context should enter discovery.
3. **There's a real bug in the current prompts**: `templates/methods/m3_transformation.md` tells the agent to "look up the closest analogue" with web search support, but `templates/discover_narrow.md` runs closed-book. The architecture asked for literature analogy while denying retrieval budget. Zero hits was predictable.
4. **The deeper lesson is bigger than two patches.** Disputatio is optimised as an *auditor* (atomic supportable negative claims). Ref #2's strength is *librarian + developmental editor* (bundled, comparative, synthetic). The taxonomy and calibration architecture both optimise for the auditor objective and against the librarian objective.

## What this commit ships

**v1, low-friction:** new template `templates/literature_engagement.md` defining a single upstream ticket between Wave 1.5 (holistic) and Wave 2 (discovery). One agent — gemini with search grounding — plus optional `/chrome` for Google Scholar verification.

Key design choices:

- **One shared ticket, not three.** Per codex feedback — retrieval problem, not reasoning problem.
- **Upstream, not post-hoc.** Output `literature_engagement.json` becomes additional input context for Phase 2 discovery tickets. Panel-row emission is the secondary use, not the primary.
- **Browser + grounded search, no MCP scholar wrapper.** Google Scholar has no official API; every "Scholar API" wrapper is screen-scraping, so a third-party MCP server adds maintainer-dependency + a confidentiality hop for marginal capability gain. /chrome is your own browser session.
- **Confidentiality discipline as a hard rule.** Search queries use themes + keywords + already-cited works — never verbatim sentences from unpublished sections. `--lit-engagement [strict|relaxed]` exposes the choice; default strict.
- **Separate evidentiary contract.** This track does NOT enter `_calibration/post_pass1_panel_rows.json`. It runs its own lightweight inline check (candidate verifiability, bibliography dedup, passage-anchor verbatim match, engagement-obligation score ≥ 2). Same pattern as `scope_framing_calibration.md` (v8.2).
- **Separate render lane.** Panel rows emit into a new top-level array `literature_engagement_findings[]` alongside `findings[]` and `dropped_findings[]`. Renderer produces a "Suggested literature engagement" section in `panel.md`, the mode-specific memo, and the optional auxiliary output.

## What this commit does NOT ship

Deliberately out of scope; tracked for separate issues:

- **OpenAlex / Semantic Scholar API integration.** Defer until v1 is measured. If browser-driven Scholar underperforms on long-tail specialised refs, graduate to OpenAlex (real official API, no scraping fragility, comprehensive citation graph).
- **Quantitative-anchoring lane.** Separate roadmap item codex flagged; needs its own template + prompt + rubric.
- **Expositional craft track.** Per codex's pushback, this is the same pattern as `scope_framing_calibration.md` — a 5th evidentiary contract, not architectural surgery. But scope it narrowly (notation collisions, duplicated derivations, missing symbol tables, section-order dependency, label mismatch, absent running example) — skip taste-level restructuring advice or you build a pedantry generator. Separate issue.
- **Fix to the m3_transformation.md vs discover_narrow.md contradiction.** Codex flagged this as a real bug. Easy follow-up.

## Test plan

Re-run the Zhang paper with the literature_engagement ticket enabled. Measure how many of Ref #2's 8 named references the track surfaces.

- ≥ 4 hits → ship as default, close #33
- 1–3 hits → improve search vocabulary design before merging
- 0 hits → need OpenAlex API integration; v1 design is wrong

Expand to 2–3 more papers with sealed expert referee reports to make the measurement meaningful (n=1 is anecdote).

## Files

- `templates/literature_engagement.md` (new) — authoritative protocol
- `templates/emit_tickets.md` — Wave 1.75 entry added
- `SKILL.md` — Phase 1.75 entry added

Pending follow-ups (not in this commit):

- `templates/render_panel.md` — needs section for `literature_engagement_findings[]` rendering
- `templates/discover_*.md` (3 files) — add `literature_engagement.json` to declared inputs
- `templates/schemas/panel_row.md` — extend with the new top-level array
