# Disputatio — what it is and why you might care

## The problem

Before you submit a paper, the dangerous critique is the one you do not know is coming.

A serious referee will catch:
- Required objects you forgot to define (a kernel without an initial condition; an algorithm without the complete-data density).
- Claims that look supported but aren't — the theorem is true, but it does not actually imply the property the abstract attributes to it.
- Framing that overstates what the formal evidence proves — "outperforms MCMC" when MCMC was run at default settings, "characterizes optimal intervention" when the proof requires a genericity condition the theorem statement omits.

You can rarely anticipate all three by re-reading your own draft. Asking a friendly colleague helps but is asymmetric — they read it once, fast, with goodwill.

## What disputatio does

Three independent LLM families (Claude, GPT, Gemini) read the paper, each producing a structured **finding panel** instead of generic prose feedback. The panel is the primary deliverable; a referee-style memo is rendered off it.

Each finding carries:
- A verbatim quote from the paper (or a precisely-located paraphrase)
- A category — proof / empirics / identification / framing / robustness / interpretation / notation
- A severity tier — material / local / nit
- The minimal correction the author would make
- An audit trail showing which families surfaced the concern and what was dropped

The system runs three independent audit layers:

- **Existence** — for every load-bearing claim or method, are the required objects actually specified in the paper?
- **Correctness** — given the present formal object, does it actually support the asserted property under the paper's own definitions?
- **Framing** — does the prose claim match what the formal evidence delivers, accounting for self-caveats?

## What the workflow looks like

1. Provide the paper (PDF or markdown).
2. Disputatio runs the audit (~2.5 hours wall clock, $0 marginal cost on Claude Pro / ChatGPT Pro / Gemini OAuth subscriptions).
3. You read the panel: 20–40 calibrated findings sorted by priority, plus a referee memo.
4. You decide what to revise, ignore, or investigate further.

Each shipped finding has been through cross-architecture audit, blinded calibration, and (for material concerns flagged by all three families) a Route-B red-team challenge that drops findings if the consensus turns out to be a shared misreading.

## What the panel contains

Findings group by failure mode:

- **Gap-class** — required object missing
- **Validity-class** — present object doesn't support the claim
- **Framing-class** — narrative overreaches the formal apparatus
- Plus method-based discovery (contradictions, scope mismatch, derivation traces)

Findings dropped at calibration or debate are preserved with reasons. The system shows what it killed.

## Worked example

A complete v8.0 panel on Galeotti, Golub & Goyal (2020), *Targeting Interventions in Networks* (Econometrica), is available at `<demo-link>`. This is a published paper, so it is not a "before submission" demo — it shows the current output format and critique level.

## Current evidence

Cross-system benchmark against [coarse.ink](https://coarse.ink) on four papers (econ network theory, popgen, computational neuroscience, info theory), refine.ink as reference review, gemini-3.1-pro single judge:

- Disputatio v8.0 on Galeotti: **5.8 / 6** (vs coarse 6.00 — closest tie disputatio has achieved; +0.8 over the v7.1 baseline)
- v7.1 drop-mini on Forney: 5.0 → 5.5 (+0.5)
- v7.1 drop-mini on Stephens: 2.5 → 3.5 (+1.0, codex judge)

Other layers (v8.1 wrong-but-present, v8.2 framing) are implemented and design-validated by an external review (codex 5.5 architectural critique across nine turns of discussion) but not yet broadly bench-measured.

The honest version: **n=4 papers, one full-pipeline v8.0 measurement, multiple within-paper deltas**. Directional evidence, not statistical proof.

## What this does not claim

- **Not a substitute for a referee.** A referee brings field knowledge and editorial judgment disputatio cannot replicate.
- **Not a proof checker.** It surfaces likely audit targets; it does not formally verify.
- **Not broadly validated across economics yet.** Bench corpus is four papers across four domains.
- **Operationally slow.** ~2.5 hours wall clock per paper. Some papers trigger Anthropic content filters and run on 2 of 3 families.
- **Single-judge bench.** All measurements use gemini-3.1-pro single-judge against a refine.ink reference. Cross-judge stress test pending.

## Who it is for

- Authors with a paper near submission who want a structured pre-submission audit.
- Advisors who want to give a coauthor a concrete starting point for a revision pass.
- Reviewers who have just been assigned a paper and want a structured first read before writing their report.

## What feedback would help

If you've looked at the demo panel: do the findings seem like real referee feedback, or like generic LLM critique with extra steps? Which ones are useful, which ones are wrong, which ones miss the point of what the paper is doing? Would you consider running this on a draft you're working on?

Feedback form: `<form-link>`. Five questions, ~5 minutes.
