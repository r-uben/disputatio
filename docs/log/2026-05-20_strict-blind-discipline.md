# 2026-05-20 — Strict-blind audit discipline (Phase 1.75 contamination fix)

## TL;DR

Re-running Phase 1.75 on Han-Hu-Zhang surfaced an orchestrator-context contamination bug that had inflated the headline recall metric. After fixing it by re-dispatching A3 as a separate Ref-#2-blind subagent, the strict-blind recall stabilises at **7 of 9** of Ref #2's named-and-not-already-cited references — up from the prior 5/8 strict-clean number, down from the contaminated 8/8 headline. The architectural lesson is that **model diversity is not enough — phase isolation matters.** The orchestrator session that runs the post-hoc comparison must not be the one that runs A3.

## The contamination

The day's run exposed a failure mode the v3 spec did not enumerate:

1. The orchestrator (Claude session driving the pipeline) read `_referee_aer/AER-2026-0450_Ref2.md` to produce the post-hoc comparison memo after Phase 6 completed.
2. The user then requested Phase 1.75 (literature engagement) be added.
3. The orchestrator wrote the A1 archetype-questions inline — using Ref #2 vocabulary it had just absorbed. First attempt was self-detected on a leak-check and archived to `_archive/2026-05-20_contaminated_a1/`.
4. A second A1 was dispatched as a fresh Claude subagent with explicit no-read instructions for `_referee_aer/`, `_calibration/`, and `4_panel/`. Clean.
5. A2 (codex gpt-5.4) received the clean A1. Codex never saw Ref #2. Clean.
6. A3 — Scholar / Semantic Scholar fill-in — was still being driven from the orchestrator session. The 2 Scholar queries the orchestrator ran were `"Malamud long run forward rates"` and `"variance swap general equilibrium pricing SVIX"`. Both targeted gaps the orchestrator knew about from reading Ref #2. Contamination via query-selection bias.

The 8/8 headline that the lit-engagement section initially claimed was a measurement of A2-blind (7 hits) + A3-orchestrator-informed (2 hits) — not strict-blind.

## The fix

A3 was re-dispatched as a separate Claude subagent with:

- Explicit read-allowlist: `literature_engagement_archetypes.json` from the clean A1 + `orient_anthropic.json` for bibliography dedup
- Explicit no-read: `_referee_aer/`, `_calibration/`, `4_panel/`, `_archive/2026-05-20_contaminated_a1/`, and crucially `literature_engagement_a2_codex.json` (so the blind A3 cannot "fill A2's gaps" — that's exactly the contamination vector the prior run had)
- Query-construction discipline: queries must derive from the archetype-question's keyword stem only; no specific paper title fragments; no author last names unless they appear in the question's own `paper_anchor` field (paper-cited works are admissible because the paper exposes them)
- A self-audit step before output write

The blind subagent ran all 13 archetype-questions through Semantic Scholar (Google Scholar was rate-limited on the IP from the prior session's use). Result: 47 unique papers across the top hits, but **0 new Ref #2 named refs beyond what A2 had already produced.** Q10 (isomorphic predecessor for two-sided gamma-netting via variance swaps) was skipped after off-domain noise persisted through two refinement attempts.

## Final strict-blind result

- **A2 codex blind** (training memory, no Ref #2 exposure): **7 of 9** Ref #2 named refs — Brennan-Cao 1996, Breon-Drish 2015, Elul 1999, Gârleanu-Pedersen-Poteshman 2009, Hugonnier-Malamud-Trubowitz 2012, Malamud-Trubowitz 2007, Martin 2017
- **A3 blind subagent**: 0 additional hits
- **A3 informed supplement** (orchestrator-picked queries): +2 (Malamud 2008, Martin 2013 "Simple Variance Swaps") — preserved transparently in a separate audit bucket, **excluded from the strict-blind metric**

## What the strict-blind result actually says

The 7/9 is genuinely good — better than the prior team's 5/8 strict-clean number. The improvement comes from the cleaner A1 archetype-questions: the new A1 (separate subagent, explicit no-read instructions) has tighter paper anchors (specific propositions, equation numbers) and broader archetype coverage (3 substitution + 2 same-instrument + 3 alternative-mechanism + 3 isomorphic + 2 general-theorem). A2 codex with better questions surfaces more load-bearing comparators from training memory.

The 2 strict-blind misses are also informative:

- **Malamud 2008** "Long run forward rates and long yields of bonds and options in heterogeneous equilibria" — a niche Finance & Stochastics paper that is not in codex's strong econ-finance training distribution. The archetype-question on CARA → LRT/CCRA substitution named the right lineage (codex returned Malamud-Trubowitz 2007 and Hugonnier-Malamud-Trubowitz 2012) but missed the specific 2008 long-run-forward-rates entry.
- **Martin 2013** "Simple Variance Swaps" (NBER WP / pub 2013) — codex returned Martin 2017 QJE (the more cited follow-up) but not the 2013 origin paper. The archetype-question Q04 (variance-swap pricing in different domains) named the right researcher and lineage.

Both misses are **paper-specificity gaps in A2's training memory**, not archetype-question gaps. The 5 archetypes the v3 architecture uses can reach these targets in principle via narrower archetype-question formulations, but the current 13-question set lacks the precision. This is an A1-question-shape issue, not an A2-recall issue.

## Architectural lessons

1. **Orchestrator-context leakage is a real failure mode.** It needs to be enumerated in `templates/literature_engagement.md` as a blind-discipline section. The simple statement "A1 is the Ref-#2-blind step" is necessary but not sufficient — A3 also needs blind discipline, and the orchestrator session must not be the one running A3 if it has read the comparison target.

2. **Post-hoc comparison belongs in `_evaluation/`, not in the live pipeline.** Today's run produced `_evaluation/ref_comparison.json` for the first time as a contracted artifact. Future runs should generate this without the orchestrator session reading the referee report directly.

3. **Strict-blind metrics are the only credible headline.** Any "X/N" claim should specify strict-blind explicitly. Numbers that include informed-supplement candidates ship with an explicit qualifier or in a separate audit bucket — never as the headline.

4. **The structural fix is encoded in issue #48.** The blind-discipline addendum on the Semantic Scholar API integration issue captures all of the above as required acceptance criteria for the API migration.

## Empirical-evidence table update

Add to `templates/literature_engagement.md` `## Empirical evidence` section:

| Architecture | Score | Notes |
|---|---|---|
| ... (prior rows unchanged) |
| **A1 clean + A2 codex + A3 blind subagent (2026-05-20 strict-blind re-run)** | **7 / 9 strict-blind** | Phase-isolated A3. A3-informed-supplement (+2: Malamud 2008, Martin 2013) separated into `informed_supplement[]`, excluded from headline. |

## Open questions

- Will a wider archetype-question set (20+ questions instead of 13) recover Malamud 2008 and Martin 2013 strict-blind? A more precise question shape like "what heterogeneous-equilibrium results characterize long-run pricing under non-CARA preferences in markets with options" might surface Malamud 2008.
- Should A1 itself be Ref-#2-blind by construction, not by subagent enforcement? E.g., A1 runs as a fresh codex session that never has filesystem access to the workspace's referee directory.
- Is the result reproducible on a second paper with a sealed report, or does it overfit to Zhang? The benchmark issue (#19) is the validation path.
