# Section brief — §9: limitations and failure modes

**Section title (working):** Limitations and failure modes

**Word target:** 900–1200 words. The original target was 700–900, but the failure-modes catalogue now carries an additional four entries (post-§8), so the section will land closer to 1100 if every entry gets a single tight paragraph. Limitations sections that run longer than ~1200 words start to read as defensive; ones that run shorter than ~900 will under-cover the second half of the section. The middle range is where this lands honestly.

**Output path:** `docs/research-notes/methodology-note/sections/09_limitations.md`

## What the section must do

Catalogue what the note's claims do not yet support, what the architecture currently cannot do, and what a reader should not take away. The discipline is to consolidate limitations that have been surfaced *throughout* §§1–8 into one place a reader can find them — not to invent new ones, and not to soften the ones already named in earlier sections.

This section is the last analytical section before acknowledgements. It is also the one that earns the note's overall framing — "ship the pattern, not the performance claim." If §9 understates what is uncertain, the rest of the note loses its honesty premium.

## Key claims the section must consolidate

The section's role is consolidation, not generation. The five claims below are already established earlier in the note; §9 restates each in one place and ties them to the structural reason the limitation exists.

1. **n=1 prospective case study.** The empirical anchor for the whole note is the Han-Hu-Zhang run. One paper. The recall numbers from §5 (7/9 strict-blind), the 3-of-4 Route B catch from §3, the disposition trail volumes from §6 — none of these has been replicated on a second paper. The strict-blind discipline of §4 guarantees the *execution* on Zhang was clean; it does not manufacture a corpus. Issue #19 (3–5 sealed-report papers under a protocol frozen before reading any of them) is the right validation path and is not built.

2. **Design overfit on the archetype taxonomy.** §5 establishes this at length: the five archetypes were derived from Ref #2's exact phrasing. Zhang is therefore partly a design case for this taxonomy. The §9 restatement is short — point at §5 and note the resulting recall number cannot be read as a prospective claim.

3. **Three substantive concern types the holistic pass cannot generate.** The Zhang case study (§7) surfaces three categories of concern Ref #2 raised that disputatio's hardcoded attack-surface typology does not have axes for: structural-primitives questions about parameters that ought to be endogenous (κ_i, α_i), suggestions for back-of-envelope numerical exercises in theory papers, and Q-measure-heterogeneity / absence-of-arbitrage at the contract-price level. The structural fix is Issue #49 (generate concern-axes per paper rather than hardcoding them). Without it closed, every fork inherits the same blind-spot structure: whatever the hand-written typology omits, the discovery tracks systematically under-detect.

4. **Calibration relies on a within-family upgraded re-annotator.** The reference implementation uses codex `gpt-5.4-mini` on Pass 1 and codex `gpt-5.4` full on the polish re-annotation. The two annotators were trained on overlapping corpora and share architectural priors. The mitigation flagged in §8 — rotate the re-annotator to a different family from Pass 1 — has not been measured. The 0% post-calibration overclaim rate is an internal quality-gate number; external validation by domain experts is pending.

5. **Single-domain validation.** Everything we have observed is on theory economics papers. §8 lays out a three-layer adoptability model (invariant / tunable / specific), but the model is derived from imagining adjacent fields rather than from a fork that has actually been built and run. A serious cross-domain claim requires a forked implementation on at least one non-economics paper with its own sealed referee benchmark.

## Failure modes catalogue (additional to limitations)

This is the second half of §9. The four failure modes from §8 are restated here as a forker's reference, with the structural reason each persists:

- **Evaluation contamination at the orchestrator-context level.** The session graph, not the prompts, is the surface area that leaks. §4 walks through the worked example.
- **Shared hallucination at the multi-family-consensus level.** Three architectures can pattern-match the same wrong reading. §3 is the worked example; Route B is the mitigation.
- **Calibration overconfidence.** Within-family re-annotation is not architecturally distinct from Pass 1. Cross-family rotation is the fix; we have not measured the gain.
- **Pre-publication confidentiality leakage.** External API calls (Scholar, Semantic Scholar) on unpublished work are a confidentiality risk. The mitigation is that A3 queries derive from keyword stems, not verbatim sentences. A fork reviewing unpublished work needs to audit this surface explicitly.

These four are already named in §8. §9 does not re-explain them; it consolidates them as a single bulleted list a reader can scan, with a one-sentence pointer to where each is treated in depth.

### Additional failure modes (surfaced through continued operation, post-§8)

Four further failure modes have emerged from running the architecture on additional papers beyond the Zhang case. They are listed here at the same altitude as the four above — as architectural failure modes, not as new thesis claims. The §9 voice on each is descriptive: name the mode, name the structural reason, point at the fix if known.

- **Silent infrastructure-failure drops.** A polish-rewrite or re-annotation ticket can fail to produce output (CLI crash, empty model response, OAuth expiry mid-run, model capacity 429). After the retry budget is exhausted, the finding is dropped. The drop reason is logged honestly, but in the panel the result is structurally indistinguishable from a substantively-killed finding. A reader can see "dropped at Pass 2" without knowing whether judgment or infrastructure killed it. The architectural fix is to widen the drop reason vocabulary at calibration so infrastructure failures are tagged separately, and to add a one-tier-demote fallback rather than a hard drop when the polish step itself fails.

- **Route B kernel-loss when a broad consensus claim is broken.** The merge-time atomicity rule splits a broad finding into atomic siblings ideally, but the broadest framing of a real concern can still be the row Route B's red-team operates on. When the red-team breaks that framing, the row drops entirely — even if a narrower kernel of the same underlying concern would survive scrutiny. The narrower kernel survives only if it was independently emitted as a separate row at merge time. The architecture has no mechanism today to *narrow* a Route B row when the broad form fails; it can only ship or drop. The structural fix is to give the synthesizer a third Route B verdict — `consensus_narrowed` — that preserves a specifically-named survivor sub-claim rather than killing the row.

- **Unequal effective independence across the three families.** "Three-family consensus" is treated as a uniform precision signal. In practice the three families have very different effective coverage on a given paper: one family may produce twice the candidates of another, one family may flag almost everything at the same priority tier (low discrimination), one family may stay lean enough that its agreement is more of a concurrence-with-the-others than a third independent read. A Route B fire that rests on one family's depth plus two families' concurrence is a weaker independence signal than the architecture's framing suggests. The mitigation is to track per-family discrimination metrics (priority spread, coverage of the attack-surface index, candidate density) and surface them in the panel-render summary, so a reader can see whether a "consensus" was earned independently or absorbed by inheritance.

- **LLM-coding methodology in target papers is a class the architecture cannot yet audit at the right altitude.** When a target paper uses its own LLM pipeline to produce a structural empirical input — increasingly common in economics and political science — disputatio surfaces the pipeline as an attack surface and produces verbal critiques (prompt sensitivity not documented; aggregation rules not stress-tested; etc.). What it does *not* yet do is propose the principled fix: replace the LLM's structural-parameter synthesis step with a transparent econometric recovery (e.g., a graded-response or monotone-latent-index model fit to LLM-produced ordinal labels). Disputatio is one architectural step behind on the class of papers it most needs to handle, and the gap is not a prompt or coverage issue — it is that the system has no "here is the alternative architecture" move in its current repertoire. The structural fix is to add a sixth pattern to the methodology note (sketched in design-notes) once a fork has actually built and run such a recovery model on a real paper.

## What §9 must NOT do

- **Do not introduce new limitations the rest of the note does not establish.** If a limitation is real and material, it belongs in the section that surfaces it. §9 is consolidation, not first-mention.
- **Do not weaken claims §§1–8 made.** If §5 says the 7/9 result is not a prospective recall claim, §9 should not hedge it further toward "the result may not even be replicable on Zhang." Honest qualification is set in earlier sections; §9 holds the line, it does not push past it.
- **Do not list every open question from the per-section tail blocks.** Most of those questions are implementation-level. §9 covers limitations of the *claim*, not the to-do backlog.
- **Do not end on apology.** A limitations section that closes with "we hope future work addresses these gaps" reads as ritual. The closer should state the consequence of the limitations for the reader (what claims the note supports vs. what it does not), then stop.

## Tone-match anchors from §§1-8

- The §3 "we want to be careful here about what this result demonstrates" cadence is the dominant voice for this section.
- The §4 "this is not a story about a careless researcher" construction — translated to §9, "this is not a list of warnings about the architecture; it is a list of gaps in what we have measured."
- The §8 closer ("better instances are the point") — §9 can end on the same note from a different angle: better measurements are the point.

## Source material

Required reading:

- `draft.md` §§1–8 — the whole drafted note, in order. §9's job is to consolidate limitations already established earlier; the section is unworkable without a full read of what came before.
- `outline.md` ("Limitations explicitly acknowledged" block, "What this note is NOT good for" block) — the originally-planned scope.
- Open-questions blocks at the tail of `sections/05_lit_engagement.md`, `sections/06_disposition_trail.md`, `sections/08_adopt_adapt_guide.md` — for the unresolved questions the subagents flagged.

Optional:

- `docs/log/2026-05-20_strict-blind-discipline.md` (for the n=1 framing)
- `docs/log/2026-05-20_lit-engagement-v3-archetype.md` (for the design-overfit framing)

## Open questions to flag in your output (if relevant)

- Whether the section should include a forward pointer to a "v2" of this note that would issue once 3–5 sealed-report papers are processed. The argument for: it sets the reader's expectations correctly about what would update the claims. The argument against: it commits to a follow-up the project may not deliver on its current timeline.
- Whether the calibration-overconfidence limitation belongs in §9 or in §8's failure-modes paragraph. The current brief puts it in both — §8 as a forker-facing mode, §9 as a claim-level limitation. The duplication is intentional but the orchestrator may want to compress.
