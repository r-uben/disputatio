# Auditable Multi-Agent Paper Review: A Pattern Researchers Can Adopt

*Draft — sections 1–3 only. Sections 4–8 pending. Companion document to `methodology-note-outline.md`.*

*Last updated: 2026-05-20*

---

## 1. Why model diversity is not enough

The reflexive answer to "LLMs hallucinate" has become "use several of them and trust agreement." Across multi-agent systems for code review, research synthesis, and now paper review, the assumption is that errors are uncorrelated across model families — three different architectures reading the same document will tend to make three different mistakes, so the points on which they agree should be reliable.

This assumption is wrong in at least two distinct ways that matter for academic review, and the failures it produces have a common shape: they convert the multi-agent system's structure from a precision mechanism into a confidence laundromat.

The first failure mode is **shared misreading across architectures.** A paper's compact wording, OCR artifact, notation collision, or implicit assumption can pattern-match the same way across three independent training distributions. The cleanest example we have from our own work: on the Han, Hu, Zhang (2026) paper "Markets for Price Risk," four findings were flagged with high severity by all three model families (Anthropic, OpenAI, Google) acting independently. A red-team challenge run *against* the consensus broke three of those four findings as shared misreads — the defender located verbatim text in the paper that the three families had collectively missed. One of these (the alleged "constrained-efficiency relabel between §7.5 and §8") was broken by the paper's own "and separately" wording, kept distinct on adjacent lines, that none of the three independent agents noticed. Another (the claim that the paper's "markets for Greeks" construction "fails under non-Gaussian basis-risk") was broken by the footnote immediately above the cited equation, which already accommodates non-Gaussian shocks at the certainty-equivalent step. Three independent models pattern-matched on the same phrase, missed the same nearby qualifier, and produced the same wrong finding.

The second failure mode is **orchestrator-context leakage.** Even when individual agents have no access to the ground-truth referee report or any other comparison target, the human-or-LLM *orchestrator* that runs them often does. That orchestrator's choices — which Scholar queries to run, which prompt phrasings to use, which thresholds to set for merging candidate findings — get unconsciously informed by the comparison target. The system passes a phase-level blind audit ("each agent never read the referee report") while failing a research-design-level blind audit ("the queries the orchestrator picked were targeted at known gaps"). The first time we ran our literature-engagement track on Han-Hu-Zhang, this exact pattern inflated a "5 of 8" honest recall number into a "8 of 8" claim that we initially reported as the headline. Catching that — and structurally fixing it by isolating the orchestrator session from the comparison-target-reading session — is the contamination story we walk through in §4.

Neither failure mode is solved by better prompting. The shared-misreading mode is solved by an adversarial mechanism that treats agreement as suspicious rather than confirmatory. The orchestrator-leakage mode is solved by structural isolation of phases that read evaluation targets from phases that generate findings. Both are architectural moves, and both transfer cleanly to academic review in any field — legal-brief review, biotech-protocol audit, ML-paper assessment, social-science manuscript triage — because their underlying causes (correlated errors in shared training distributions; humans-and-LLMs implicitly leaking comparison knowledge) are not domain-specific.

The rest of this note documents five architectural patterns we have found useful in building an auditable multi-agent academic-review system, and an adopt-and-adapt guide for researchers who want to fork the reference implementation for their own domain. We deliberately do not lead with a performance claim. We have one prospective case study (Zhang) and three documented systematic blind spots, and a published-recall headline would either oversell what we have measured or undersell what we have learned. The interesting contribution is the pattern, not the number.

## 2. Pattern 1: Cross-architecture finding panel

The first pattern is a structural one. Three independent model families — in our reference implementation, Anthropic (Claude), OpenAI (Codex), and Google (Gemini) — each run the same paper through the same discovery tracks. Each family produces candidate findings independently, scored by category (proof, framing, robustness, identification, exposition, notation, interpretation, "other"), and each candidate must carry a verbatim quote from the paper plus a falsifier sentence describing what evidence would force its withdrawal.

The candidate findings are then **merged** rather than voted. The merge step is mechanical: candidates from different families that cite overlapping passages and would be addressed by the same paper edit get clustered into a single merged finding. Candidates that cite different passages or would require different edits stay separate. The merge step is not where truth gets decided; it is where the architecture's bookkeeping happens. Every merged finding carries an audit trail listing exactly which family-and-track produced each contributing candidate, so the source structure is preserved.

The output of the merge is a **panel** rather than a ranked list. Each panel row carries: the calibrated finding, the source candidates, a per-family `architecture_support` block recording which families flagged it, an evidence array with verbatim quotes, and (where the gate fires) a debate trail. The point of the panel is to make the structure of the agreement legible to a reader. A finding flagged by one family with high confidence and ignored by the other two is a different epistemic object from a finding flagged by all three independently. The panel's job is to surface that distinction, not to flatten it into a score.

The pattern's portability is high. Any review domain where you want LLM-side independence as a precision signal can use it: legal-brief audit, biotech-protocol review, ML-paper assessment. Two requirements: the candidate-finding shape must be structured enough to cluster (verbatim quote + location + category), and the model families must be genuinely architecturally distinct, not just three deployments of the same underlying weights. A three-family panel of (GPT-4, GPT-4-mini, GPT-4-vision) is not three architectures; it is one architecture sampled three ways, and the precision gain from "agreement" is correspondingly weaker. The three-family pattern we use (Anthropic / OpenAI / Google) is a minimum useful diversity floor.

What the cross-architecture panel does *not* do on its own is solve the shared-hallucination problem. The "Markets for Price Risk" run produced four findings flagged by all three families with high severity. By a naive agreement-is-truth rule, those four would have shipped as the strongest findings in the report. Three of them turned out to be wrong. The next pattern is the mechanism that catches those three.

## 3. Pattern 2: Adversarial red-team on consensus

The second pattern is an adversarial gate that fires specifically *because* of cross-architecture agreement. Its motivation is the empirical observation in §1: three independent LLM families can collectively misread the same paper in the same way, especially when the paper's wording invites a particular misinterpretation that maps onto a phrase pattern those models share. When the discovery panel produces a finding with maximum severity *and* unanimous family support, the system treats that combination as a flag for shared-hallucination risk rather than a confirmation of correctness, and routes the finding to a dedicated red-team challenge before it can ship.

We call this gate **Route B** to distinguish it from the system's other escalation route (Route A, which fires on cross-family disagreement rather than agreement). Route B's structure is asymmetric: the system pins the consensus claim verbatim — exact wording, exact cited evidence from each family, exact failure condition — into a `claim_under_challenge` block, and dispatches a *defender* whose role is to red-team that pinned claim. There is no prosecutor on Route B; the three-family agreement *is* the prosecution. The defender's job is to prove the consensus is wrong, not to defend the paper against an external accuser.

The defender works through a fixed checklist of seven shared-hallucination modes:

1. **Surface-pattern overfit.** Three families recognised the same phrase pattern ("missing assumption", "scope mismatch", "hidden lemma") and applied it to the wrong target in this paper.
2. **OCR-induced misread.** A garbled equation or mis-OCR'd symbol read consistently across families because they parsed the same artifact the same wrong way.
3. **Notation collision.** The paper uses a symbol two different ways in two sections; all three families fixed on the wrong reading.
4. **Implicit-assumption drift.** The hypothesis the families flag as missing is present — in a footnote, online appendix, or cited prior work the families looked past.
5. **Citation-trace gap.** The paper defers a step to a citation; the families read the deferral as a hand-wave; the cited paper actually contains the step.
6. **Literature-conflated confusion.** The concern is real in a related paper but not in this one; the families pattern-matched on the literature rather than the manuscript.
7. **Algebra shared-slip.** All three families reproduced the same sign error, dropped square root, or mis-applied limit because the paper's notation invites the same mistake.

The defender must produce one reply per mode, each tagged `holds_against` (the mode fired — verbatim counter-evidence found that falsifies the pinned claim), `reinterprets` (the consensus rests on a small misreading; here is the corrected reading), or `falls_to` (this mode did not produce a successful red-team). The defender may not use `falls_to` as a graceful exit, and may not respond to a paraphrased version of the consensus claim. Target integrity is enforced: if the defender attacks a narrower restatement of the pinned claim, the synthesizer rejects the defense by default.

A separate **synthesizer** then reads the defender's mode-by-mode output and renders a verdict on Route B's terms: `consensus_held` (the red-team failed to break the agreement; the finding ships to the panel with a "consensus survived red-team" badge and stays at material severity) or `consensus_broken` (a fired mode landed verbatim counter-evidence that directly falsifies the pinned claim; the finding drops to `dropped_findings[]` with the mode name surfaced for transparency). The Route B verdict labels are deliberately distinct from Route A's (`prosecution_wins`, `defense_wins`, `split`, `escalate`) because the polarity is inverted: on Route A, a winning defense ships the concern; on Route B, a winning defense kills the concern. Reusing Route A labels on Route B regresses the synthesizer because the training priors push in the wrong direction.

On the Han-Hu-Zhang run, four findings cleared the Route B gate (material severity + unanimous three-family flag). The verdicts came back as one `consensus_held` and three `consensus_broken`. The held finding (about the abstract's "approximate Arrow" framing) was later demoted at a separate calibration pass for an independent reason. The three broken findings each had a specific fired mode that the system surfaces in the audit trail: a notation-collision diagnosis on the Geanakoplos-Polemarchakis "constrained-efficiency" relabel; a surface-pattern overfit on the "markets for Greeks fails under non-Gaussian" claim, where the defender located verbatim text in the section immediately preceding the cited footnote that already accommodated non-Gaussian shocks; and a notation-collision on the alleged bundling of quasilinearity and non-storability, where the paper itself assigns the two assumptions distinct jobs in adjacent paragraphs.

We want to be careful here about what this result demonstrates. The 3-of-4 catch is a striking number, but it does not by itself prove that Route B is reliably calibrated. Two competing hypotheses are consistent with the data: (a) Route B is doing exactly what it was designed to do — catching shared hallucinations across architectures — and (b) Route B is over-pruning, breaking findings on technicalities that a human referee would still raise because the paper's compensating wording is too buried or too pragmatically insufficient to save the framing. Distinguishing these requires external validation: independent expert adjudication of dropped findings, ideally by the paper's referee. We are gathering that data on the Zhang case; for now, we treat Route B as a powerful audit mechanism rather than a proven accuracy gain.

What Route B unambiguously *does* give us, however, is a structured artifact: every dropped consensus finding ships with a fired-mode label and verbatim counter-evidence. A reader of the review can audit the red-team's work. This is the architectural contribution worth lifting, separate from any claim about Route B's accuracy. The pattern's value is making consensus-derived findings auditable, not making them automatically correct.

The pattern is also domain-portable, with one caveat. The seven shared-hallucination modes are field-agnostic in the sense that legal documents have OCR misreads, biotech protocols have notation collisions, ML papers have citation-trace gaps, social-science manuscripts have literature-conflated confusions. The defender model can be any architecture different from the consensus members. The caveat is that fields with much smaller literatures or much narrower notational conventions may see different mode-fire distributions; a legal-review fork might find `surface_pattern_overfit` dominant and `algebra_shared_slip` irrelevant. The checklist is a starting point, not a closed taxonomy.

## 4. Pattern 3: Strict-blind phase isolation

The third pattern is a structural rule about which sessions are allowed to read which artifacts. We need to lead with the failure mode it solves, because the rule sounds bureaucratic until the failure is concrete.

### The contamination

The literature-engagement track in our reference implementation has three passes. A1 generates archetype-driven research questions from the paper. A2 names candidate comparator papers from a language model's training memory in response to those questions. A3 confirms and supplements the candidate list via a literature-search backend (Scholar, Semantic Scholar, or equivalent). The architectural contract was that A1, A2, and A3 should all be Ref-#2-blind — none of them should read the sealed referee report that the system is being compared against in the post-hoc evaluation step.

We honoured the contract at the level of individual agent calls. A1 was dispatched to a fresh subagent with explicit no-read instructions for `_referee_aer/`, `_calibration/`, and `4_panel/`. A2 was dispatched to a fresh codex session that received only the archetype-questions and the paper context. Both passes never saw the referee report.

The problem was elsewhere. A3 — the Scholar fill-in pass — was driven from the *orchestrator session*. The orchestrator is the long-running session that coordinates the pipeline, holds the panel-building state, and (in our case) had also read the referee report to produce a post-hoc comparison memo immediately before the literature-engagement track ran. When the orchestrator picked the two Scholar queries that the A3 pass would run, the queries were `"Malamud long run forward rates yields bonds options heterogeneous"` and `"variance swap general equilibrium pricing SVIX"`. Both queries targeted papers that the orchestrator knew, from having read the referee report, were named references the system had not yet recovered.

The recall number this produced — eight of eight of the referee's named references hit on a "Ref-#2-blind" run — was the number we initially reported as the headline. The two papers that the A3 informed-supplement queries had recovered were Malamud (2008) "Long run forward rates" and Martin et al (2013) "Simple Variance Swaps." Both are unambiguously real, well-known references. Without orchestrator knowledge of the comparison set, neither would have been queried for by name. The first six refs surfaced from A2's training memory alone, and that part of the run *was* genuinely blind; the seventh (Martin 2017's QJE paper "What is the Expected Return on the Market?") also surfaced from A2. But the eighth and ninth — Malamud 2008 and Martin 2013 — only surfaced because the human-in-the-loop with the comparison set in hand picked the queries that would find them.

The honest strict-blind recall on this run, after we re-dispatched A3 as a separate Claude subagent with the same no-read rules as A1 and A2, is seven of nine. The blind subagent ran all thirteen archetype-questions through Semantic Scholar and surfaced zero additional Ref #2 references beyond what A2 had already produced from training memory. The two "informed-supplement" candidates were preserved transparently in a separate audit bucket — not deleted, but explicitly carved out of the headline metric and labelled with the contamination explanation.

This is not a story about a careless researcher. We had explicit blind-discipline rules, written down in the protocol, that we believed we were following. The leakage happened at a level the rules did not cover: not at the agent call, but at the orchestrator's choice of which queries to dispatch. That single-step removed unconsciously from the rule's surface area was enough to inflate a real seven-of-nine result into a fake eight-of-eight headline.

### The architectural fix

The fix has three components:

**Phase isolation by subagent dispatch.** Every phase that generates findings, queries, or candidate comparators must run in a session that has explicit read-allowlists for the artifacts it needs and explicit no-read for anything that might leak comparison-target knowledge. Subagent dispatch with allowlist enforcement is the simplest mechanism we have found; the alternative ("the orchestrator promises not to peek") relies on session-level discipline that fails in exactly the way ours did.

**Comparison artifacts live outside the live pipeline.** The post-hoc evaluation against a sealed referee report (or any other gold-standard target) writes to a separate directory — in our case `_evaluation/ref_comparison.json` — that the pipeline phases are forbidden to read. The artifact is generated by a comparison step that runs *after* all generation phases have completed, in a fresh session that has read access to both the pipeline output and the sealed target but writes only to `_evaluation/`. The pipeline phases get no read access to anything `_evaluation/` ever touches.

**Headline metrics are strict-blind by default.** Any "X of N" recall claim ships with explicit strict-blind framing. Informed-supplement candidates — found by queries that were targeted at known gaps — ship as a separate carve-out, never folded into the headline. This is a discipline of language as much as a discipline of architecture. A reader of the published report should be able to tell, from the wording alone, whether a hit was blindly recovered or post-hoc supplemented.

### Why this generalizes

The contamination mode is not unique to literature engagement or to our specific pipeline. Any multi-agent system that is evaluated against a held-out target has the same risk surface: an orchestrator (human or LLM) that has access to both the pipeline state and the evaluation target will unconsciously route information from the target into the pipeline's decisions. The leakage paths are subtle — choice of search queries, choice of merge thresholds, choice of which findings to escalate — and they are invisible from any single agent's transcript. They are only visible from the orchestrator's transcript, and only if someone is looking for them.

The pattern transfers to any held-out-evaluation setting. A code-review system evaluated against the merged version of a pull request has the same risk: an orchestrator that has seen the merged code will pick prompt phrasings that pre-load the bugs the merged version fixed. A medical-decision-support system evaluated against an outcome label has the same risk: an orchestrator with access to outcomes will weight the right symptoms higher. The architectural lesson is identical: isolate the phases that generate decisions from the phases that read evaluations, and make the isolation a property of the session graph, not a discipline of attention.

### What a forker needs to do differently

If you adopt this pattern for your own domain, the concrete steps are:

1. Identify every artifact your system uses for post-hoc evaluation against a gold-standard target. Make a list. Be paranoid — this includes referee reports, expert ratings, prior-publication revision histories, peer-review records, oracle annotations.
2. Audit which sessions in your orchestration ever read each of those artifacts. Most pipelines will discover that the orchestrator session ends up touching all of them at some point.
3. Re-architect so generation phases run in sessions that have never touched any artifact on the list. Subagent dispatch is the simplest mechanism. The allowlist must be enforced at the session level, not the prompt level.
4. Move the comparison step to a separate post-hoc artifact (`_evaluation/` in our naming convention; pick what fits your project). The comparison step runs after all generation phases close. It reads pipeline output and evaluation target; it writes only comparison numbers.
5. Audit every recall claim in your reports for whether it is strict-blind or informed-supplement. Surface the distinction in the published numbers.

The cost is mild: subagent dispatch is a few hundred milliseconds of overhead per phase, and the architectural discipline takes a few hours to retrofit on an existing pipeline. The benefit is that your evaluation numbers become trustworthy. The discipline is not optional. We learned this the way one usually learns these things.

---

## Sections 5–8 — pending

To be written:

- **§5** Archetype-driven literature engagement
- **§6** Auditable disposition trail
- **§7** Case study — Han-Hu-Zhang vs sealed AER Ref #2, with explicit design-overfit caveat and pending-author-validation flag
- **§8** Adopt-and-adapt guide for forking to other domains
- **Limitations** and failure modes
- **Acknowledgements**

See `methodology-note-outline.md` for the full section structure and writing-plan estimates.
