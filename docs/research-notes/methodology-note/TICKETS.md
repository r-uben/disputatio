# Methodology-note writing — TICKETS

Section-by-section work breakdown for the disputatio methodology note. Mirrors the disputatio orchestration pattern: each pending section gets a brief, a subagent dispatch, and a status row. Sections are independent unless explicitly marked.

**Note source of truth:** `draft.md` (single consolidated draft). Individual sections may also exist under `sections/<NN>_<name>.md` as the subagent's working file; reconciled into `draft.md` by the orchestrator after each section ships.

**Subagent:** `methodology-section-writer` (see `.claude/agents/methodology-section-writer.md`). Same agent for every section; section-specific brief lives at `briefs/<NN>_<name>.md`.

**Style anchors:** §§1–4 in `draft.md` are the tone reference. Sentence shapes, level of qualification, willingness to surface our own mistakes. New sections should read as continuations of that voice.

---

## Status

| § | Title | Status | Subagent | Depends on | Brief | Section output | Notes |
|---|---|---|---|---|---|---|---|
| 1 | Why model diversity is not enough | **done** | — (drafted inline) | none | — | `draft.md` §1 | committed 2026-05-20 |
| 2 | Pattern: cross-architecture finding panel | **done** | — (drafted inline) | none | — | `draft.md` §2 | committed 2026-05-20 |
| 3 | Pattern: adversarial red-team on consensus (Route B) | **done** | — (drafted inline) | none | — | `draft.md` §3 | committed 2026-05-20 |
| 4 | Pattern: strict-blind phase isolation | **done** | — (drafted inline) | none | — | `draft.md` §4 | committed 2026-05-20 (contamination story) |
| 5 | Pattern: archetype-driven literature engagement | **done** | methodology-section-writer | none | `briefs/05_lit_engagement.md` | `sections/05_lit_engagement.md` | reconciled into `draft.md` 2026-05-20; Hirshleifer 1989 triangulation claim dropped after source verification — only GPP 2009 supported |
| 6 | Pattern: auditable disposition trail | **done** | methodology-section-writer | none | `briefs/06_disposition_trail.md` | `sections/06_disposition_trail.md` | reconciled into `draft.md` 2026-05-20; landed at ~640 words vs 600 target; subagent flagged spec gap — `templates/merge_and_rank.md` documents a verbatim-quote validator as a third drop site, but the panel artifact does not surface those rejections in `dropped_findings[]` (they happen pre-panel). Implementation gap to track separately from the section. |
| 7 | Case study: Han-Hu-Zhang vs sealed AER Ref #2 | **blocked** | methodology-section-writer | Anthony's reply on F003/F005/F009/F017 | `briefs/07_case_study.md` (TODO) | `sections/07_case_study.md` | author validation flips this from "pending findings" to "validated findings"; design-overfit caveat is non-negotiable |
| 8 | Adopt-and-adapt guide | **done** | methodology-section-writer | none | `briefs/08_adopt_adapt_guide.md` | `sections/08_adopt_adapt_guide.md` | reconciled into `draft.md` 2026-05-20; landed at 1706 words (over 1600 ceiling) — content density justified by the brief's non-negotiables; subagent flagged the "audit phases not observed end-to-end" wording for author confirmation (paraphrased from SKILL.md's Phase 1.75 skip note). |
| 9 | Limitations and failure modes | **pending** | methodology-section-writer | §§5-8 should be drafted first so limitations are concrete | `briefs/09_limitations.md` (TODO) | `sections/09_limitations.md` | lift from existing dev log + outline's "limitations explicitly acknowledged" |
| 10 | Acknowledgements | **pending** | — (inline, by author) | all sections complete | — | `sections/10_acknowledgements.md` | author writes this; not subagent work |

---

## Dispatch protocol

When a section's status is `pending` and its dependencies are resolved:

1. **Confirm the brief exists** at `briefs/<NN>_<name>.md`. If not, write it first.
2. **Dispatch** the methodology-section-writer subagent via the `Agent` tool with the brief path inlined. The subagent has read access to the whole repo; explicitly NO read access to anything under `_referee_aer/` in any paper workspace (same blind-discipline rules as the lit-engagement track).
3. **Section lands** at `sections/<NN>_<name>.md`. Orchestrator reads it and reconciles into `draft.md` if quality bar is met. If revision needed, send the subagent feedback and re-dispatch.
4. **Update TICKETS.md** — mark the section `done`, note any open questions raised by the subagent.
5. **Update PR #50** — push the new section + the TICKETS update.

§§5, 6, 8 can be dispatched **in parallel** since they are mutually independent. §7 waits on Anthony. §9 waits on §§5-8 content stabilising.

---

## Style invariants (every section must honor)

These are the constraints that make §§1-4 readable as one document; every new section needs to match them.

1. **Honesty discipline.** When a claim is not validated, the prose says so explicitly. "X is real" is reserved for things we have direct evidence for; everything else is "X is plausibly real" or "X is pending validation." The Route B "we don't know if it's catching hallucinations or over-pruning" caveat in §3 is the model.

2. **No marketing language.** No "we believe disputatio is..." or "the system enables..." constructions. Direct statements about what the architecture does, what we observed, what we still don't know.

3. **One concrete example per claim.** Every architectural pattern lands with a paper-specific example from the Han-Hu-Zhang run. Patterns without examples read as armchair theory.

4. **Surface the design-overfit caveat where relevant.** The 5 archetype taxonomy was derived from Ref #2's phrasing. §5 in particular must flag this; §7 must lead with it.

5. **No bullet-list-driven prose.** Sections are paragraphs. Bullet lists are used sparingly for enumerated mode lists (the 7 shared-hallucination modes; the 5 archetypes) but not as the section's main structure. §§2-4 are the model.

6. **The reader is a researcher in an adjacent field, not a disputatio user.** The audience is someone who wants to build their own version of this for their own domain. Domain-portability notes go at the end of each pattern section.

7. **Lift from existing material.** Every section has source material in the repo:
   - `SKILL.md` for architecture
   - `templates/<phase>.md` for procedure
   - `docs/log/2026-05-20_*.md` for the empirical findings
   - The outline file for the section-specific scope
   - The codex consultation output (agent-ctl session 71) for the strategic framing

   The subagent should read these and quote / paraphrase, not invent. Original prose only for transitions and synthesis.
