# Section brief — §8: adopt-and-adapt guide

**Section title (working):** Adopting and adapting the pattern

**Word target:** 1200–1600 words. The longest of the architectural-pattern sections. This is the actual payoff for the reader — a researcher in an adjacent field who wants to build their own version. The other sections describe what disputatio is; this section tells the reader what they should do.

**Output path:** `docs/research-notes/methodology-note/sections/08_adopt_adapt_guide.md`

## What the section must do

Give a researcher in an adjacent field — legal-brief audit, biotech-protocol review, ML-paper assessment, social-science manuscript triage — a usable map for forking the architecture. Be honest about what generalises cleanly, what needs domain re-tuning, what is currently brittle in the reference implementation, and where the smallest viable starting point is.

This is the most original-prose section in the note. §§1-7 describe what we have built and observed. §8 is where we hand the pattern over.

## Key claims the section must support

1. **Three layers of adoptability.** Frame the section around a three-way split:
   - **Domain-invariant.** The architectural patterns themselves (§§2–6) — cross-architecture panel, Route B adversarial gate, strict-blind phase isolation, archetype-driven literature engagement, auditable disposition trail. These transfer without modification. The honesty discipline (verbatim quote + falsifier on every candidate finding) also transfers.
   - **Domain-tunable.** Components that have an obvious analogue in other fields but need re-parameterising. The attack-surface typology in `templates/holistic.md`. The discovery method bank (M0 close-reading generalises; M3 transformations, M6 disentangling, M8 derivation-trace need domain-aware adaptation). The literature-engagement backend (Scholar → PubMed / SSRN / arXiv / Westlaw / domain-specific). The suppress-canonical list. The model-family routing in `SKILL.md` (some domains have stronger Codex priors, others stronger Gemini priors).
   - **Domain-specific.** Components that essentially have to be rewritten. The five reasoning archetypes specifically (the *taxonomy structure* generalises, the *archetype mix* does not). The category vocabulary (proof / framing / robustness / identification / exposition / notation / interpretation is econ-theory-paper-shaped; a legal-brief reviewer would need a different category schema). The seven shared-hallucination modes in Route B (the mode list is field-influenced; legal review may add "precedent miscitation"; biotech may add "dosage transcription error").

2. **Currently brittle parts.** Honest catalogue of what does not yet work cleanly in the reference implementation:
   - Several Phase 1.5/2.5/2.6 audits documented in `SKILL.md` are designed but not wired into the orchestrator's execution checklist. A forker reading SKILL.md will see machinery that is not actually running.
   - The benchmark (Issue #19) is not built. Adopters will be running into the same n=1 problem we are. There is no shared evaluation corpus to compare implementations against.
   - The `/chrome` MCP backend used for some lit-engagement calls is rate-limit-prone in practice; the Semantic Scholar API replacement (Issue #48) is the in-flight fix. A new fork should default straight to Semantic Scholar.
   - The concern-axes generator (Issue #49) — generating attack-surface axes per paper instead of hardcoding the typology — would fix the documented "three missed concern types" from the Zhang case study (κ/α-style structural-primitives questions, empirical-anchoring-for-theory questions, formal-apparatus-internal-consistency questions). Without it, a fork will inherit the same hardcoded-typology blind spots.

3. **Where to start your fork — the smallest viable pipeline.** Five-step ramp-up, in order, each step adding a layer:
   1. Read `SKILL.md` end to end. It is the authoritative spec.
   2. Look at `templates/orient.md`, `templates/holistic.md`, `templates/discover_holistic.md`, `templates/discover_broad.md`, `templates/discover_narrow.md` to understand the discovery shape.
   3. Look at `templates/synthesize.md`'s consensus-mode section for the Route B red-team pattern.
   4. Look at `docs/log/2026-05-20_strict-blind-discipline.md` to see what evaluation contamination looks like in practice and how to architecturally fix it.
   5. Fork on a small scale first: one paper, one model family per role, no calibration, no Route B, no literature-engagement track. Then layer in calibration. Then Route B. Then the literature-engagement track. Each layer is independently runnable. Building all of it at once is how the architecture becomes incomprehensible.

4. **Failure modes a forker should expect.** The four categorical failure modes — eval contamination at orchestrator-context level (§4 in this note is the worked example), shared hallucination at the multi-family-consensus level (§3 is the worked example), calibration overconfidence (within-family annotators agreeing with each other for non-truth reasons), and pre-publication confidentiality leakage via external API calls (the lit-engagement track's Scholar / Semantic Scholar calls are the highest-risk surface here, and disputatio's discipline of A3 queries deriving from keyword stems rather than verbatim sentences is the mitigation). Walk through each in one short paragraph each. Do not enumerate — describe each one as a thing the forker will encounter, with detection guidance.

5. **The honest "do not fork this if..." paragraph.** Forking is not always the right answer. Explicit conditions under which the architecture is overkill or wrong-shaped:
   - If the review domain has structured, fully-machine-readable evaluation criteria (regulatory compliance, automated style-guide checks), single-LLM pipelines or rule-based systems are simpler and probably better.
   - If the domain has no notion of "specialised-comparator" literature (purely empirical-result review with no theoretical lineage), the literature-engagement track is dead weight.
   - If the cost of running three independent model families is prohibitive for the use case (high-throughput, low-stakes review), the cross-architecture panel is the wrong precision/cost trade-off — a single LLM with a self-critic loop may be a better fit. The pattern is for cases where false confidence is materially costly.

## Source material

Required reading:

- `SKILL.md` end to end — it *is* the authoritative spec the section is pointing the reader at
- `docs/log/2026-04-14_upstream-pivot-plan.md` — the product/architecture plan with the original audience and value framing
- `templates/orient.md`, `templates/holistic.md`, `templates/discover_*.md`, `templates/synthesize.md` — for the discovery-and-debate shape
- `outline.md` §8 ("Adopt-and-adapt guide") for the originally-planned shape — the brief expands this but the structure should remain recognisable
- `draft.md` §§1-7 for tone match and to ensure §8 does not redundantly re-explain patterns already covered

Optional:

- `docs/adding-agents.md` if it exists — for the N>3 generalisation discussion (Kimi, Ollama, OpenCode integration). If the forker wants to use four or five model families instead of three, this is the relevant pointer.

## Tone-match anchors from §§1-5

- §3's "we want to be careful here" pattern when naming competing interpretations
- §4's "this is not a story about a careless researcher" cadence when describing how things go wrong
- §5's "what this pattern gives a forker is therefore not X but Y" closer — use the same construction as a section closer
- The willingness throughout §§1-5 to point at the limits of what we have validated. §8 must do this — a forker should walk away knowing what is solid and what is held together with optimism

## Anti-patterns to avoid

- **Marketing the system.** No "disputatio enables", no "the framework provides", no "researchers can now". Use declarative descriptions of what is and what is not.
- **Step-by-step tutorial register.** This is not a quickstart guide. It is a map for a researcher deciding whether and how to fork. Implementation walk-throughs belong in the repo's docs, not here.
- **Re-litigating patterns from §§2-6.** Reference them, do not re-explain them. The reader has just finished §§5 and §7 — they remember.
- **False modesty.** The architecture has properties worth defending. Honest qualification is the discipline; performative under-claiming is not. The disposition trail (§6) and the Route B audit trail (§3) are real architectural contributions and the section can say so.
- **Promising the benchmark.** Issue #19 (adversarial benchmark) is not built. State that the n=1 limitation is not fixed by this note, and that adopters will face it too.

## Open questions to flag in your output (if relevant)

- Whether the three-family minimum (Anthropic / OpenAI / Google) is the right floor or whether a fourth family (Kimi, OpenCode, or a strong open-weights model) would meaningfully improve the consensus precision floor. We have not measured this.
- Whether the "domain-invariant / domain-tunable / domain-specific" three-way split holds when applied to a non-theory-paper domain. The split was derived from imagining adjacent fields, not from any forker who has actually done it.
- Whether the smallest-viable-pipeline ramp-up (one family → cross-architecture panel → calibration → Route B → lit-engagement) is the right ramp shape, or whether a forker should add Route B before calibration. We have not tested both orders.
