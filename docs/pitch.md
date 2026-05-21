# Disputatio — what it is and why you might care

## The problem

Before you submit a paper, the dangerous critique is the one you do not know is coming.

A serious referee will catch:
- Required objects you forgot to define (a kernel without an initial condition; an algorithm without the complete-data density).
- Claims that look supported but aren't — the theorem is true, but it does not actually imply the property the abstract attributes to it.
- Framing that overstates what the formal evidence proves — "outperforms MCMC" when MCMC was run at default settings, "characterizes optimal intervention" when the proof requires a genericity condition the theorem statement omits.

You can rarely anticipate all three by re-reading your own draft. Asking a friendly colleague helps but is asymmetric — they read it once, fast, with goodwill.

## What disputatio does

Three independent LLM families (Claude, GPT, Gemini) read the paper. The deliverable is **not a referee report** — it is a folder of audit material that you use to write the report yourself. The folder contains:

- A **finding panel** — atomic concerns, each pinned to a verbatim quote (or precisely-located paraphrase) from the paper. The headline view.
- A **drop trail** — every concern that was raised and killed during calibration, with the reason. The system shows what it killed, not only what survived.
- **Per-phase intermediate work** — orientation maps, attack-surface index, candidate findings by track, debate transcripts where families disagreed.
- A **referee-style memo** rendered off the panel, in prose. You edit it in your own voice.

Each shipped finding carries:
- A verbatim quote (or precisely-located paraphrase)
- A category — `proof | empirics | identification | framing | robustness | interpretation | notation | other`
- A severity tier — `material | local | nit`
- The minimal correction the author would make
- The audit trail showing which families surfaced it and what was killed alongside

Findings are produced by three complementary modes of scrutiny that all contribute to the categories above:

- **Existence** — for every load-bearing claim or method, are the required objects actually specified in the paper?
- **Correctness** — given the present formal object, does it actually support the asserted property under the paper's own definitions?
- **Framing** — does the prose claim match what the formal evidence delivers, accounting for self-caveats?

The categories tell you what *kind* of thing a finding is; the three modes tell you how it was *found*. Both appear in the audit trail.

## What the workflow looks like

1. Provide the paper (PDF or markdown).
2. Disputatio runs the audit (~2.5 hours wall clock, runs on Claude Pro / ChatGPT Pro / Gemini OAuth subscriptions).
3. You read through the folder — panel, drop trail, debate transcripts — and decide which concerns you agree with, which you can defend rejecting, and which you want to investigate further.
4. You write the report (or revision plan) in your own voice, using the audit material as source.

Each shipped finding has been through cross-architecture audit, blinded calibration against the paper text, and — for material concerns flagged independently by all three families — a red-team challenge that drops the finding if the consensus turns out to be a shared misreading rather than a real defect.

## What the panel contains

Each surviving finding has one of the eight categories above, plus a severity tier, a priority label (mode-specific), the evidence array of verbatim quotes, and the audit trail of how it survived calibration. Findings dropped at calibration or debate are preserved with reasons in a parallel `dropped_findings` block. The system shows what it killed.

## Worked example

A complete panel on Galeotti, Golub & Goyal (2020), *Targeting Interventions in Networks* (Econometrica), is available on request — this is a published paper, so it is not a "before submission" demo, but it shows the current output format and critique level on a known target.

## Current status

Disputatio is in active evaluation. The architecture is built — three-family discovery, blinded calibration with demote-or-drop on overclaim, escalation-only debate, single-writer rendering. What is **not** yet established is panel quality at scale, validated through author and referee feedback on real manuscripts. That is the open question this outreach exists to answer.

## What this does not claim

- **Not a substitute for a referee.** A referee brings field knowledge and editorial judgment disputatio cannot replicate.
- **Not a proof checker.** It surfaces likely audit targets; it does not formally verify.
- **Not broadly validated yet.** The architecture has been exercised on a handful of papers; panel quality at scale is the open question.
- **Operationally slow.** ~2.5 hours wall clock per paper. Some papers trigger Anthropic content filters and run on 2 of 3 families.

## Confidentiality

Files are handled locally on the operator's machine, but during inference the paper text is sent to Anthropic, OpenAI, and Google through paid Pro subscriptions. **This is not a confidential channel.** Only send work you would be comfortable having processed by those providers under their data-handling terms. For referee work on a manuscript you did not author, check your journal's policy first — most journals prohibit submitting confidential review material to external AI services.

## Who it is for

- **Primary: authors** with a paper near submission who want a structured pre-submission audit on their own work.
- **Conditional: reviewers** who have been assigned a paper, only where journal policy permits external-AI assistance.
- Advisors who want to give a coauthor a concrete starting point for a revision pass.

## What feedback would help

If you've looked at a panel — yours or the worked example — the most useful questions to push on are: do the findings read like real referee feedback or like generic LLM critique with extra steps; which ones are useful, which ones are wrong, which ones miss what the paper is actually doing; and whether the calibration drop trail looks well-calibrated (i.e., the dropped findings really were the weak ones). Reactions on any of those are welcome at whatever length is convenient.
