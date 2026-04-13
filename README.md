# disputatio

High-precision academic paper review via seven-method dialectic debate, executed by three independent AI agents (Claude, Codex, Gemini) and orchestrated as a durable ticket DAG on disk.

This is a **Claude Code skill**, not a Python package. Claude Code is the runtime; the skill is a protocol for orchestrating multi-agent paper criticism.

---

## What it does

Given an academic paper, `disputatio` produces a top-journal-quality referee report by:

1. Reading the paper from three independent agents, each producing a structural map (no judgments yet).
2. Running five generative criticism methods × three agents = **fifteen discovery sweeps** in parallel, all closed-book.
3. Merging, deduplicating, and ranking findings; weighting cross-agent agreement at 2× because agreement across architectures is more meaningful than cross-method agreement within one architecture.
4. Subjecting the top *N* findings to **structured dialectic debate** with role rotation (Claude prosecutes round 1, Codex defends, Gemini synthesizes; rotates in subsequent rounds).
5. Writing a single referee report — the human-readable deliverable — plus a structured JSON record of every prompt, output, debate transcript, and decision.

The whole pipeline is **resumable, auditable, and replayable** because every agent call is a ticket on disk with its prompt path, inputs, outputs, timing, and session log preserved.

---

## Why it exists

Single-pass LLM reviews tend to overclaim: they identify real issues but inflate severity, miss hidden assumptions, and pattern-match to plausible-sounding flaws that don't survive scrutiny. The dialectical step exists to make every objection face a defender that must reply *to the specific objection*, with quotes, before a third party synthesizes what survived.

The hypothesis being tested: **debate-hardened reviews overclaim less and support claims more often than aggressive single-pass reviews.**

The current evidence on one paper is consistent with this — see [Evidence](#evidence-on-one-paper) below.

---

## Quick start

Inside Claude Code:

```
/disputatio /path/to/paper.pdf
```

Optional flags:
```
/disputatio paper.pdf --top-n 8 --max-rounds 3 --skip-web
```

Defaults:
- `--top-n 8` — debate the top 8 ranked issues; the rest become "appendix concerns" in the final report.
- `--max-rounds 3` — at most three dialectic rounds per issue. Aggressive short-circuits (round-1 early-kill, stalled-debate termination, budget tiering) usually end debates earlier.
- Web verification enabled — Gemini fact-checks any issue flagged `needs_web_verification: true`.

A run on a typical economics or statistics paper takes **~2 hours wall clock** end-to-end.

### Prerequisites

- `claude` CLI authenticated (Claude Pro / Claude Code).
- `codex` CLI authenticated (ChatGPT Pro). Default model `gpt-5.4`.
- `gemini` CLI authenticated (Google OAuth). Default model `gemini-3.1-pro-preview`.
- `agent-ctl` (ships with the user's Claude Code skills) for ticket DAG execution.
- An Obsidian vault to host the per-paper review folder. The skill writes everything inside `notes/work/referee-reports/<paper-slug>/`.

---

## What you get

A self-contained Obsidian folder per paper:

```
notes/work/referee-reports/<paper-slug>/
├── review.md                   ← top-level index, phase status
├── _paper/paper.md             ← OCR'd source
├── 0_orientation/              ← three paper maps (one per agent)
├── 1_discovery/m{0,2-6}/       ← findings organised by method
├── 2_ranking/                  ← merged + ranked issue register, triage notes
├── 3_debates/<NN>_<slug>/      ← one folder per debated issue (prosecute / defend / synthesise per round)
├── 4_report/referee_report.md  ← THE deliverable
└── _artifacts/
    ├── tickets.json            ← the DAG (source of truth for orchestration)
    ├── prompts/                ← every prompt sent
    ├── json/                   ← raw structured outputs
    └── sessions/               ← raw agent reasoning traces
```

The referee report is what you'd hand to a journal editor. Everything else is provenance.

---

## Evidence (on one paper)

Run on Galeotti, Golub & Goyal (2020), "Targeting interventions in networks" (Econometrica):

| Metric | Disputatio (this skill) | Coarse (single-pass Sonnet 4.6) |
|---|---:|---:|
| Judge score, mean of 5 runs | **6.00 / 6** | 5.53 / 6 |
| Stddev across 5 runs | 0.00 | 0.21 |
| Panel-mode score (3-persona synthesis) | **5.62** | 5.12 |

Judge: Gemini 2.5 Pro. Reference: Stanford reviewer. Positional-bias mitigation enabled. Adapter-flattened disputatio output (no manual rewriting). See [`docs/evaluation.md`](docs/evaluation.md) for the full methodology and per-finding blinded annotation results.

**Honest caveats** (also in [`docs/evaluation.md`](docs/evaluation.md)):
- *n* = 1. The win on this paper does not generalise without replication.
- Same judge family. Cross-judge robustness (Opus, GPT-4) untested.
- Coarse is one Sonnet pass (~30 s). Disputatio is ~2 h with three agents. They are not effort-matched.

A second-paper run (population-genetics) was attempted but used a stale skill version on the disputatio side — the comparison was withdrawn pending re-run.

---

## How it works (one paragraph)

Claude Code generates tickets in **waves**. After each wave, `agent-ctl run-dag <tickets.json>` executes everything ready in parallel up to a concurrency cap, blocks until the wave is done, and writes session logs back to disk. Claude Code then inspects outputs, renders curated markdown into the numbered folders, and emits the next wave. Claude-typed tickets (orientation by Claude, merge-and-rank, prosecution by Claude, final report) are executed inline; external tickets (Codex, Gemini) go through `agent-ctl`. Models are routed by task — Opus for merge / synthesis / final, Sonnet and `gpt-5.4-mini` and `gemini-3-flash-preview` for bulk discovery, Opus / `gpt-5.4` / `gemini-3.1-pro-preview` for the debate roles. See [`docs/architecture.md`](docs/architecture.md) for the full picture.

---

## The seven methods

| # | Method | Role |
|---|---|---|
| 1 | Structured disputation | Shapes every debate round (quaestio → objections → sed contra → respondeo → replies) |
| 2 | Interrogation by contradiction | Finds pairs of claims that cannot both be true |
| 3 | Systematic transformation | Eight mechanical transforms per claim (negate / strengthen / weaken / substitute / reverse / consequence / boundary / analogy) |
| 4 | Counterexample construction | Tries to construct a case satisfying the assumptions but violating the conclusion; exposes hidden lemmas |
| 5 | Self-measured critique | Finds the paper's own commitments, hunts for passages where the paper violates them. Strongest method |
| 6 | Causal disentangling | For each causal claim, enumerates co-factors and co-effects the paper has not ruled out |
| 7 | Iterative refinement | Operates in synthesis: produces the refined claim after each round |

Methods 2–6 are generative (they find issues). Method 1 is structural (it shapes each round). Method 7 is iterative (it refines claims across rounds). Every method has its own template under `templates/methods/` describing the operational procedure — not the philosophical lineage. Agents execute the procedure without needing to know its origin.

See [`docs/methods.md`](docs/methods.md) for a deeper breakdown.

---

## Documentation map

- [`docs/architecture.md`](docs/architecture.md) — ticket DAG, agent routing, model routing, file layout, resumability, decision loop.
- [`docs/methods.md`](docs/methods.md) — the seven methods, what each detects, when each is most useful, examples from the targeting-interventions run.
- [`docs/evaluation.md`](docs/evaluation.md) — the judge.py methodology (replicates coarse.ink), per-finding blinded annotation, results on targeting-interventions, what we cannot yet claim.
- [`docs/roadmap.md`](docs/roadmap.md) — known bugs, planned improvements, what V4 should fix.
- [`docs/log/`](docs/log/) — dated dev log entries with decisions and trade-offs from each working session.
- [`SKILL.md`](SKILL.md) — the formal protocol Claude Code reads when executing `/disputatio`.
- [`CLAUDE.md`](CLAUDE.md) — orientation for Claude Code (working directory conventions, design principles).

---

## Status

**Working end-to-end on theory papers.** The targeting-interventions run produced a 1,758-word referee report with 2 material findings, 6 local findings, 19 appendix concerns, and 16 triaged false positives, evaluated at 6.00/6 against the Stanford reference.

**Known limitations** (full list in [`docs/roadmap.md`](docs/roadmap.md)):
- The `agent-ctl` shipped today routes any non-`codex` agent through the Gemini CLI. Claude-typed tickets get misrouted to `gemini -m sonnet` and 404. A local one-line patch in `_ticket_ready` skips Claude tickets so the orchestrator runs them inline. Needs proper upstream fix.
- Gemini's OAuth silently expires mid-run with no error surfacing through `agent-ctl`. Long runs need to detect `FatalCancellationError` and halt the DAG with an actionable message.
- Gemini's JSON outputs frequently have runaway LaTeX escapes (`\\\\\\\\\\sum`) that the existing cleaner doesn't handle. A two-pass cleanup (collapse `\\{2,}` → `\\\\` first, then escape-fix) works.
- `templates/final_report.md` produces two heading formats (`### N. Title` for material, `N. **Title.**` for local). The downstream adapter `compare/adapt.py` only matched the second; one-shot extraction missed all material issues until patched. Fixed in commit `30f2032`.
- Synthesis prompts use `{{prosecution}}` / `{{defense}}` placeholders that should be just-in-time injected before each synthesis ticket runs. Currently they ship as literal `[[WILL BE INJECTED]]` markers; Gemini compensates by reading the JSON files directly via `--yolo`, but this is fragile.

---

## Provenance and evaluation harness

The benchmark harness lives under `compare/`:

- `compare/adapt.py` — flattens a disputatio referee report into the format used by [coarse.ink](https://coarse.ink/) for cross-system comparison.
- `compare/judge.py` — replicates coarse.ink's judging methodology (LLM-as-judge against a reference review with positional-bias mitigation; supports panel mode).
- `compare/<paper-name>/` — per-paper artifacts (paper.md, paper.pdf, reference reviews, coarse baselines, evaluation outputs).

To re-evaluate a finished disputatio run:

```bash
cd compare
uv run python adapt.py --report ../<vault>/<paper-slug>/4_report/referee_report.md \
    -o <paper-name>/disputatio_review_v4_auto.md
uv run python judge.py <paper-name> --review disputatio_review_v4_auto.md \
    --also-coarse --model gemini/gemini-2.5-pro
```

For multi-sample averaging, wrap the second command in a loop and aggregate the printed `Overall:` lines.

---

## License & contact

Personal toolkit; not currently licensed for redistribution. Open an issue or reach out if you want to use it.

Build log: [`docs/log/`](docs/log/) — each non-trivial change comes with a dated entry recording decisions and rejected alternatives.
