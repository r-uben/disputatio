# Methodology-note outline — disputatio as an adoptable pattern

**Status:** outline. Drafted 2026-05-20 after codex gpt-5.5 launch-readiness consultation. Replaces the prior "empirical performance" launch frame with a "forkable architecture" frame.

## Working title

> **Auditable Multi-Agent Paper Review: A Pattern Researchers Can Adopt**

Subtitle option: *"Cross-architecture panels, adversarial consensus gates, and strict-blind evaluation discipline — with the Han-Hu-Zhang case as worked example."*

## What this note IS

- A description of an architectural pattern for multi-agent academic review
- A worked case study (Han-Hu-Zhang vs sealed AER Ref #2)
- A fork-and-adapt guide for researchers in adjacent domains (legal review, biotech protocols, ML papers, social science, etc.)
- An honest catalogue of failure modes including the contamination incident from 2026-05-20

## What this note is NOT

- A validated performance claim. The case study is n=1 *prospective* (Zhang is also partly a design case — see §"Design overfit" below). A real recall headline requires 3-5 sealed-report papers under a protocol frozen before reading any of them.
- A product pitch. The repo is the reference implementation, not a service.
- A benchmark. Issue #19 (adversarial benchmark) is the right path to that; this note is upstream of it.

## Audience

1. **Primary**: researchers wanting to build LLM-assisted review tooling for their own domain who do not want to repeat the architectural mistakes single-LLM and ensemble-LLM reviewers have already made.
2. **Secondary**: editors / journal staff curious whether AI-assisted referee tooling has a credible architecture (it does, if done carefully).
3. **Tertiary**: ML/agent researchers interested in adversarial-gate patterns and eval contamination as a first-class concern.

## Structure (eight sections)

### 1. Motivation: why model diversity is not enough

The reflexive answer to "LLMs hallucinate" is "use multiple LLMs and trust agreement." That's wrong in two distinct ways that matter for academic review:

- **Cross-architecture agreement can encode shared misreadings.** A paper's compact wording, OCR artifact, notation collision, or implicit assumption can pattern-match the same way across three independent training distributions. Today's Zhang run produced four high-severity findings where all three model families agreed; a red-team challenge broke three of them as shared misreads (see §4).
- **"Blind" evaluation leaks through orchestrator-context.** Even when individual agents have no access to the ground-truth referee report, the human-or-LLM orchestrator that runs them often does. That orchestrator unconsciously selects queries, prompt phrasings, or merge thresholds informed by the comparison target. Today's contamination incident (see §6) is the worked example.

These are not problems prompt engineering solves. They need architectural moves.

### 2. Pattern 1: Cross-architecture finding panel

What it is: independent discovery passes by ≥ 3 LLM families (Anthropic / OpenAI / Google in the reference implementation), each producing candidate findings with verbatim-quote evidence. Findings cluster by cross-family agreement. Multi-family findings go through a different gate than single-family ones.

What it isn't: majority vote. Agreement is a signal, not a verdict.

Domain-portability notes:
- Generalizes to any review domain where you want LLM-side independence as a precision signal.
- Requires that the candidate-finding shape is structured enough to cluster (verbatim quote + location + category).
- Three families is a minimum; more is better but with diminishing returns.

### 3. Pattern 2: Adversarial red-team on consensus

What it is: when ≥ 3 architectures agree on a material finding (Route B), a separate defender plays red-team specifically against the consensus claim, walking through 7 shared-hallucination modes (surface-pattern overfit, OCR misread, notation collision, implicit-assumption drift, citation-trace gap, literature-conflated confusion, algebra shared-slip). Verdict: `consensus_held` ships the finding with a "survived red-team" badge; `consensus_broken` drops it with mode-fired explanation.

Worked example: Zhang's four high-severity-consensus findings. One survived (F001, later demoted at calibration Pass 2 on a separate axis). Three broken — defender located verbatim counter-evidence the three families had collectively missed (Section 8 "and separately" wording for F004; footnote 5 acknowledging non-Gaussian z-CEs exist for F007; the paper's distinct treatment of quasilinearity vs non-storability for F008).

Caveat (per codex 2026-05-20 review): Route B may over-prune. Today's 3-of-4 catch is a strong signal but could also reflect red-team aggressiveness rather than ground-truth shared hallucination. External validation of dropped findings is the right calibration data; we don't have it yet.

Domain-portability notes:
- The 7 shared-hallucination modes are domain-general (legal docs OCR-misread the same way; biotech protocols have notation collisions; ML papers have citation-trace gaps).
- Defender model can be any architecture different from the consensus members.

### 4. Pattern 3: Strict-blind phase isolation

What it is: the orchestrator session that reads the post-hoc evaluation target (a sealed referee report, a ground-truth label set, etc.) must not also drive any generation phase. Phase isolation is enforced by subagent dispatch with explicit read-allowlists.

The contamination story: today's literature-engagement pass had A1 (archetype questions) and A2 (training-memory reference finder) dispatched correctly to fresh subagents with no Ref #2 read access. But A3 (Scholar fill-in) was driven from the orchestrator session. The orchestrator had read Ref #2 to write the comparison memo. The 2 Scholar queries it picked were `"Malamud long run forward rates"` and `"variance swap general equilibrium pricing SVIX"` — both targeting gaps it knew about from the referee report. The 8/8 headline this produced was not strict-blind. The corrected strict-blind result (A3 re-dispatched as a separate subagent with explicit no-read for `_referee_aer/`, `_calibration/`, and `4_panel/`) is 7/9.

The architectural fix: make the post-hoc comparison artifact live in `_evaluation/`, not in the live pipeline. Subagent dispatch with read-allowlists is the enforcement mechanism.

Domain-portability notes:
- Applies to any setting where evaluation targets exist: gold labels in NLP benchmarks, expert ratings, prior-publication revision histories, peer-review records.
- The lesson is not "be more careful with prompts." It is "make the orchestrator structurally incapable of leaking — use isolated sessions."

### 5. Pattern 4: Archetype-driven literature engagement

What it is: instead of querying citation graphs or LLM training-memory recall by topic, generate questions from the paper itself along five reasoning archetypes that captures *how a senior referee picks comparator papers*:

| Archetype | Question shape |
|---|---|
| Substitution-of-assumption | "Paper assumes X; what relaxations of X have been studied?" |
| Same-instrument, different-domain | "Paper uses X in domain D; where has X been analyzed in domain D'?" |
| Alternative-mechanism, same-conclusion | "Paper gets Y via mechanism M; what other mechanisms deliver Y?" |
| Mechanism-isomorphic predecessor | "Paper's construction K; predecessors structurally isomorphic to K?" |
| General theorem behind specific result | "Paper proves Z; what general theorem does Z specialize?" |

Three passes: A1 generates archetype-questions (closed-book on the paper), A2 names comparator papers from training memory (no specific topic seeding), A3 confirms via Semantic Scholar with strict-blind discipline.

Empirical evidence on Zhang: 7/9 of the human referee's named-and-not-already-cited references surfaced under strict blind discipline. (See §"Design overfit caveat" below — Zhang is partly a design case for this taxonomy.)

Domain-portability notes:
- The 5 archetypes are field-agnostic — they describe how referees in *any* field generate comparator picks.
- The specific Scholar / Semantic Scholar backend is replaceable per field (PubMed for biotech, SSRN for econ/finance, arXiv for ML/physics, Westlaw for legal).
- The candidate paper list a forked implementation would target depends on the field's typical referee literacy.

### 6. Pattern 5: Auditable disposition trail

What it is: every candidate finding that did not ship to the final panel is preserved with drop reason. The pipeline produces a `dropped_findings[]` array showing what was rejected at triage, what was rejected at calibration, what was dropped by Route B red-team, and what was killed at re-annotation. The pipeline's restraint is visible.

Why it matters: a reader of a multi-agent review can trust the shipped findings more if the system can show its work on the unshipped ones. The disposition trail also lets a domain expert spot the kind of finding the system systematically over- or under-claims.

Today's Zhang example: 80 raw candidates → 34 merged → 25 shipped + 9 dropped. The 9 drops are itemized with annotator notes (Pass 1 misreads), polish-rewrite outcomes (still overclaiming after one narrow attempt), and Route B mode-fired diagnoses (which shared-hallucination mode the red-team broke each consensus on).

Domain-portability notes:
- Trivial to implement: every drop site writes to a structured record.
- The hard part is **using** the disposition trail to tune the calibration rubric. Issue #14 (detect self-acknowledged limitations) is one example of the analysis a disposition trail enables.

### 7. Case study: Han-Hu-Zhang (with explicit caveats)

#### What disputatio surfaced

- 4 material findings (F003 Proposition 5 = two-parameter-Gaussian identity; F005 welfare formula leading-order Taylor; F009 quadratic technology load-bearing; F017 markets-for-price-risk scope overreach)
- 12 local concerns + 9 nits
- 40 ranked literature-engagement candidates including all 7 strict-blind hits against Ref #2's named refs
- 9 transparent drops with reasons

#### What disputatio missed vs Ref #2

Three substantive concerns the human referee raised that disputatio's holistic-pass typology did not surface:
1. Endogeneity of risk-bearing capacity κ_i and risk aversion α_i as model primitives (how they might co-arise via entry, infrastructure, capital constraints)
2. Suggestion for a calibrated numerical exercise or back-of-envelope using commercial / non-commercial position data
3. Q-measure heterogeneity + absence-of-arbitrage at the contract-price level

All three are paper-anchor-level concerns the current hardcoded attack-surface typology (theory / empirics / identification / framing / robustness / exposition) doesn't have axes for. Issue #49 (generate concern-axes per paper instead of hardcoding) is the structural fix.

#### Design overfit caveat (CRITICAL)

The 5 archetype-question taxonomy in §5 was derived (by the prior development team) from reading Ref #2's exact phrasing patterns. Zhang is therefore partly a design case for this taxonomy, not a fully held-out test. Today's strict-blind discipline ensures the execution is leak-free, but the protocol itself was shaped against Zhang's referee report.

This does not invalidate the architectural insight. It does mean the 7/9 number should not be read as a *prospective* recall claim. Prospective validation needs 3-5 papers with sealed referee reports under a protocol frozen before reading any of them.

#### What we don't know yet

- Author validation of the 4 material findings. An email is out asking for one-line "yes / no" calls. Could be 4/4 real, could be 2/4. The range is wide and matters.
- Reproducibility on a second paper. Issue #19 (adversarial benchmark) is the right validation path.

### 8. Adopt-and-adapt guide

If you're considering forking disputatio for your own domain:

**What's domain-invariant**
- The architectural patterns in §2-§6. All five generalize.
- The discipline of "verbatim quote + location + falsifier" on every candidate finding.
- The strict-blind audit pattern.

**What needs re-tuning per domain**
- The attack-surface typology in `templates/holistic.md`. Domain-specific. Soon to be paper-generated per issue #49.
- The discovery methods in `templates/discover_*.md`. M0 close-reading generalizes; M3-M8 transformations need domain-aware adaptation.
- The literature-engagement backend (Scholar vs PubMed vs SSRN vs Westlaw).
- The model family routing in SKILL.md. Different domains have different strong / weak models per task.

**What's currently brittle**
- Phase 1.5 (obligation extraction), Phase 2.5 (claim-validity audit), Phase 2.6 (scope-framing audit), Phase 3g/3v/3s (their calibrators) are designed in SKILL.md but not all wired into the orchestrator's execution checklist yet. Forking now means accepting that subset is documented-but-not-running.
- The benchmark is not built (#19). You will be running into the same n=1 problem.
- The `/chrome` MCP backend for A3 is rate-limit-prone; the Semantic Scholar API replacement (#48) is the in-flight fix.

**Where to start your fork**
1. Read `SKILL.md` end to end. It is the authoritative spec.
2. Look at `templates/orient.md`, `templates/holistic.md`, and `templates/discover_*.md` to see how the discovery shape works.
3. Look at `templates/synthesize.md`'s "Consensus mode" section for the Route B red-team pattern.
4. Look at `docs/log/2026-05-20_strict-blind-discipline.md` to see what eval contamination looks like in practice and how to fix it.
5. Fork on a small scale first: one paper, one model family per role, no calibration. Then layer in calibration, then Route B, then the literature-engagement track.

## Failure modes a forker should expect

- **Eval contamination** at the orchestrator-context level (today's incident). Detection: post-hoc audit of which sessions read what.
- **Shared hallucination** at the multi-family-consensus level. Detection: Route B red-team gate.
- **Calibration overconfidence** — the calibrator may agree with the discovery agent because both were trained on similar corpora. Detection: upgraded re-annotator on flagged rows breaks correlated errors (today's run: codex gpt-5.4-mini Pass 1 + codex gpt-5.4 full re-annotation).
- **Pre-publication confidentiality**. If you're reviewing unpublished work, the lit-engagement track's Scholar / external-API calls are the highest-risk surface. Disputatio's blind-discipline rules require A3 queries derive from keyword stems only, not verbatim sentences.

## Limitations explicitly acknowledged

- n=1 prospective case study under strict-blind discipline.
- Design overfit on the archetype taxonomy.
- Three substantive concern types the holistic pass cannot generate (κ/α-style structural-primitives questions, empirical-anchoring-for-theory-paper questions, formal-apparatus-internal-consistency questions). Issue #49 fixes this.
- Calibration relies on a within-family upgraded re-annotator (codex mini → codex full). The 0% post-cal overclaim rate is an internal quality-gate number; external validation is pending.
- Single domain (theory economics). Adaptation to other domains is the explicit point of §8, but no other-domain validation has been run.

## What this note is good for

- Showing other researchers an architectural pattern that, with appropriate adaptation, lets them build a better paper reviewer than they would from "throw the paper at GPT-4" or "use o3 deep research."
- Documenting the contamination incident as a worked example of how to detect and fix eval leakage.
- Establishing language ("Route B red-team", "strict-blind phase isolation", "archetype-driven literature engagement") for follow-up work.

## What this note is NOT good for

- Claiming validated performance.
- Anchoring product pricing.
- Replacing peer review.

---

## Writing plan

| Section | Effort | Notes |
|---|---|---|
| §1 motivation | 2-3 hours | Distill from existing dev logs |
| §2-§6 architectural patterns | 8-10 hours | Each section ≈ 1.5 pages; lift heavily from existing template prose |
| §7 case study with caveats | 3-4 hours | Pull from today's panel.md, memo, ref_comparison.json |
| §8 adopt-and-adapt | 4-5 hours | Most original prose; this is the value-add for the audience |
| Limitations + failure modes | 2 hours | Distill from open issues + dev logs |
| Polish + figures | 4-6 hours | One figure per pattern minimum (architecture diagrams) |
| Total | ≈ 25-30 hours | Realistic to draft in 2-3 weeks part-time |

## Adjacent work this note motivates

- **README rewrite.** Current framing is "Claude Code skill." Should shift to "auditable multi-agent review architecture; this repo is the reference implementation." The skill aspect is the convenience layer.
- **Website reframing.** Same shift. Lead with the architecture, not the demo.
- **One-page diagram.** A pipeline figure showing the 7 phases + the cross-architecture panel + the Route B gate + the strict-blind separation. This is the figure people will share when discussing the work.
- **Adversarial benchmark (#19).** Closes the n=1 problem.
- **Concern-axes generator (#49).** Closes the documented misses.

## Posting venues to consider

In rough order of fit:

1. **arXiv (cs.CL or stat.ML)** — methodology note positioning works well here. Reproducibility expectations are aligned with the repo-is-reference-implementation framing.
2. **SSRN (Methodology section)** — fits if framed for economists; the Zhang case study would resonate.
3. **Personal blog + open-source community announcement** — informal companion to the formal note. Lower stakes, broader reach.
4. **A LessWrong or Alignment-Forum post** — the eval contamination + Route B story is exactly the kind of failure-mode worked example that audience reads carefully.

Avoid: top-tier venue submission as a primary launch artifact. The work isn't ready for that (n=1, no benchmark, no formal validation).
