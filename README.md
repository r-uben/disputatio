# disputatio

A cross-architecture paper review panel for the two moments that matter before publication: before an author submits, and before a referee writes the report.

The product is not a polished referee letter. The product is a **finding panel** — each concern carries an exact quote from the paper, support across model architectures, a contested-point debate trail, a calibration verdict, and a priority label tuned to the reader (author or referee). Claims that do not survive verification are shown with their drop reason instead of hidden. The point is knowing which concerns are real, which are stretched, and which are worth acting on before an editor or referee sees the paper.

This is a **Claude Code skill**, not a Python package. Claude Code is the runtime; the skill is a protocol for orchestrating multi-agent paper criticism.

---

## Who this is for

**Author mode — pre-submission review.** You are about to submit to a journal and want to know what a serious referee will catch. Run disputatio on your manuscript. For each surfaced concern you get: a verbatim quote, what is wrong, how it was tested, and a priority label — `fix_before_submit`, `watch_in_review`, or `can_ignore`. The optional revision plan maps priority findings to concrete sentence-level edits.

**Referee mode — review assistance.** You have been asked to referee a paper and are writing your first-round report. Run disputatio on the manuscript. For each candidate concern you get: the quote, cross-architecture support, whether it survived a challenge-response round, and a priority label — `endorse`, `verify_before_endorsing`, or `skip`. The optional referee-letter draft scaffolds prose you edit in your own voice.

Both modes share one engine. The difference is the priority label and the rendered summary memo.

---

## What it is not

- Not a replacement for the reviewer's or author's judgment. Every finding is there to be endorsed, narrowed, or rejected — the system shows its work.
- Not a speed play. A run takes hours, not minutes. You use it when stakes are high enough that "defend this concern in detail" matters more than "give me a plausible letter in thirty seconds."
- Not a benchmark judge. The calibration loop is internal discipline, not a scoreboard.

---

## Quick start

Inside Claude Code:

```
/disputatio /path/to/paper.pdf --mode author
/disputatio /path/to/paper.pdf --mode referee
```

Defaults:
- `--mode author` — produces `fix_before_submit / watch_in_review / can_ignore` priority labels plus an optional revision plan.
- `--mode referee` — produces `endorse / verify_before_endorsing / skip` labels plus an optional referee-letter draft.
- `--max-debate-rounds 2` — escalation-only debate on contested findings; most findings do not trigger debate.
- Web verification enabled — external claims are fact-checked before calibration.

A run on a typical economics or statistics paper takes **~2 hours wall clock** end-to-end.

### Prerequisites

- `claude` CLI authenticated (Claude Pro / Claude Code).
- `codex` CLI authenticated (ChatGPT Pro). Default model `gpt-5.4`.
- `gemini` CLI authenticated (Google OAuth). Default model `gemini-3.1-pro-preview`.
- An Obsidian vault to host the per-paper review folder at `notes/work/referee-reports/<paper-slug>/`.

### Install

The repo bundles three Claude Code skills (`disputatio`, `codex`, `gemini`) plus the `agent_ctl.py` orchestrator. One script wires them all into `~/.claude/skills/` as symlinks, so the repo is the single source of truth and edits propagate without manual sync:

```bash
git clone https://github.com/r-uben/disputatio.git
cd disputatio
./install.sh
```

The installer backs up any existing files at the destination (`*.bak.<timestamp>`) before linking — nothing is overwritten silently. To remove the symlinks and restore backups:

```bash
./install.sh uninstall
```

After install, restart Claude Code to pick up the new skills. Verify with `/disputatio --help` from inside Claude Code, or `python3 ~/.claude/skills/agent_ctl.py status` from the shell.

---

## The finding panel

Every run writes `_artifacts/json/panel.json` as the canonical output. Row shape is defined once in [`templates/schemas/panel_row.md`](templates/schemas/panel_row.md); the sketch below is illustrative — the schema file is authoritative. One entry per surviving finding:

```json
{
  "finding_id": "F003",
  "concern": "<one-sentence claim>",
  "category": "proof | empirics | identification | framing | robustness | interpretation | notation | other",
  "severity": "material | local | nit",
  "confidence": { "band": "high | medium | low" },
  "priority": {
    "author": "fix_before_submit | watch_in_review | can_ignore",
    "referee": "endorse | verify_before_endorsing | skip"
  },
  "evidence": [
    { "quote": "...", "location": "...", "why": "...", "support_type": "direct_quote | derived_inference" }
  ],
  "architecture_support": {
    "anthropic": { "supports": true, "methods": ["M5"] },
    "openai":    { "supports": true, "methods": ["M2"] },
    "google":    { "supports": false }
  },
  "debate": {
    "triggered": true,
    "verdict": "prosecution_wins | defense_wins | split | not_run",
    "what_survived": "..."
  },
  "calibration": {
    "verdict": "supported | overclaimed_narrowed | dropped",
    "quote_verified": "yes | partial | no"
  },
  "suggested_action": {
    "author":  { "fix": "..." },
    "referee": { "how_to_use": "..." }
  }
}
```

Findings dropped by calibration or by a defender in debate are preserved in the audit trail with drop reasons. The panel renderer (see below) shows them explicitly instead of hiding them.

---

## What you get on disk

A self-contained Obsidian folder per paper:

```
notes/work/referee-reports/<paper-slug>/
├── review.md                     ← top-level index, phase status, mode
├── _paper/paper.md               ← OCR'd source
├── 0_holistic/                   ← cross-architecture paper map and attack-surface index
├── 1_discovery/                  ← broad critic + narrow evidence-judgment sweeps
├── 2_ranking/                    ← merged atomic findings with verdict history
├── 3_debates/                    ← only contested findings that triggered escalation
├── 4_panel/                      ← panel.json + author memo + referee memo
├── _calibration/                 ← blinded per-finding annotations + demotion log
└── _artifacts/
    ├── tickets.json              ← the DAG (source of truth for orchestration)
    ├── prompts/                  ← every prompt sent
    ├── json/                     ← raw structured outputs
    └── sessions/                 ← raw agent reasoning traces
```

The panel is what a reader looks at first. The memo is a single-writer summary. The debate traces are provenance. Everything is replayable and resumable because every agent call is a ticket on disk.

---

## How it works (one paragraph)

Three model families (Claude, Codex, Gemini) produce a holistic conceptual pass per paper — paper spine, main claims, attack surfaces, likely referee questions. Nine discovery tickets (three holistic + three broad critic + three narrow evidence-judgment, one per family) generate candidate findings against that map, with each concern forced through an evidence compiler that pins a verbatim quote, location, and whether support is direct or inferred. Atomic merge clusters cross-family duplicates without bundling distinct concerns; a programmatic validator rejects any cluster whose quote does not substring-match the paper. Contested findings (cross-family disagreement with severity that would change on verdict) escalate to a structured prosecute-defend-synthesize round; everything else ships to calibration directly. A blinded annotator evaluates every candidate report entry; overclaimed findings are rewritten narrower or demoted one tier; unsupported findings are dropped before the user sees them. A single writer renders the panel into author or referee memo prose. The pipeline is resumable, auditable, and mode-agnostic — the same engine writes both packets.

---

## Status

Current shape (v7 shipped, v7.1 in PR review, v8.0 in design + first-paper bench validation): finding panel as primary deliverable, prose memo as secondary, single-writer rendering for voice uniformity. Nine discovery tickets (three readers × three tracks: holistic, broad critic, narrow evidence-judgment). Debate runs escalation-only on contested findings, not by default. Calibration enforces a per-finding blinded annotator with demote-or-drop on overclaim. Full pipeline history in [`CHANGELOG.md`](CHANGELOG.md) and dated entries under [`docs/log/`](docs/log/).

### v7 — coarse.ink head-to-head bench (4 papers)

Scored against [coarse.ink](https://coarse.ink)'s published gpt-5.4-high run, refine.ink as reference review, gemini-3.1-pro single judge on 4 axes (coverage / specificity / depth / consistency, 1–6). Bench corpus pulled from coarse-ink MIT snapshot (`docs/benchmark/coarse_corpus/`).

| Paper | coarse | disputatio v7 | Δ |
|---|---|---|---|
| Galeotti, Golub & Goyal 2020 (econ) | 6.00 | 5.5 | −0.50 |
| Stephens & Donnelly 2000 (popgen) | 5.62 | 4.5 | −1.12 |
| Van Vreeswijk & Sompolinsky 1998 (neuro) | 5.75 | 4.5 | −1.25 |
| Forney 1988 (info theory) | 5.38 | 5.0 | −0.38 |
| **Mean** | **5.69** | **4.88** | **−0.81** |

v7 loses on coverage and depth — coarse catches formal-spec gaps disputatio systematically misses (kernel definitions, complete-data densities, ascertainment). Specificity and consistency tied 5–6 across both systems. Full bench notes: [`docs/log/2026-04-27_coarse-bench-and-drop-mini.md`](docs/log/2026-04-27_coarse-bench-and-drop-mini.md).

### v7.1 — drop-mini ablation (PR open)

Upgrades `broad_critic` and `narrow_evidence` discovery to gpt-5.4 medium + gemini-3.1-pro-preview. Closes some of the formal-spec gap by surfacing more findings at panel stage. Stephens v7.1 catches the MCMC complete-data-density gap (= coarse comment #3) that v7 missed.

| Paper | v7 | v7.1 (clean) | Δ |
|---|---|---|---|
| Forney 1988 | 5.0 | 5.5 | +0.5 (gemini judge) |
| Stephens 2000 | 2.5 | 3.5 | +1.0 (codex judge — gemini OAuth dead mid-run) |

### v8.0 — obligation extraction (draft PR, n=1 measurement)

Adds three new pipeline phases between holistic and discovery: per-family obligation extraction → global integrator → gap-claim calibration. Targets the absence-of-required-object failure mode v7 misses systematically. New templates in `templates/obligations.md`, `templates/obligation_integrate.md`, `templates/gap_claim_calibration.md`. SKILL.md surgery wires Phase 1.5a/1.5b/3g + a graceful-degradation contract for partial-family runs (anthropic content filter, gemini OAuth expiry, etc.).

First measurement on Galeotti J (pure-addition test):

| Run | Galeotti score | vs coarse 6.00 |
|---|---|---|
| disputatio v7 | 5.5 | −0.50 |
| disputatio v7.1 | 5.0 | −1.00 (mode mismatch with v7) |
| **disputatio v8.0 J** | **5.8** | **−0.20** |

Closest disputatio has gotten to coarse on any paper. +0.8 over v7.1 baseline (referee-mode comparison) on a single change. Three more paper measurements pending before PR un-drafts. Backlog tickets for the failure modes v8.0 doesn't touch (correctness of present objects, framing overreach) live as #22 and #23.

**Known limitations** (full list in [`docs/roadmap.md`](docs/roadmap.md)):
- **Single-architecture failure modes**: papers can trigger Anthropic's content filter on verbatim text reproduction (van Vreeswijk 1998 reliably does). v8.0 graceful-degradation contract handles partial-family runs but reduces coverage.
- **Gemini OAuth silent expiry mid-run**. Documented; no automatic re-auth.
- **gemini-3.1-pro-preview capacity 429** under load. Documented; manual retry or fallback.
- **Codex (ChatGPT Pro OAuth) weekly cap**. Heavy users hit it after ~1 full v7.1 run; `agent-ctl` currently supports only the OAuth path.
- **Bench is n=4** — directional, not statistical. v8.1+ (#19) expansion ticketed.

---

## Evaluation

The internal evaluation harness lives under `docs/archive/compare/`:

- `docs/archive/compare/adapt.py` — flattens panel output into a compatible format for cross-system comparison.
- `docs/archive/compare/judge.py` — LLM-as-judge methodology with positional-bias mitigation.
- Per-finding blinded annotation pipeline in `_calibration/` — the primary internal quality gate.

For release gates we run: finding-level support rate, overclaim rate, user-visible overclaim escape rate, quote verification rate, and coverage against reference-reviewed benchmark papers. Slower human-in-the-loop studies (author utility, referee endorsement rate) are run once per major version.

Full methodology in [`docs/evaluation.md`](docs/evaluation.md).

---

## Documentation map

- [`docs/architecture.md`](docs/architecture.md) — ticket DAG, agent routing, model routing, file layout, resumability, decision loop.
- [`docs/methods.md`](docs/methods.md) — the discovery methods folded into the three tracks (M0 close reading, M2 contradictions, M3 transformations, M5 self-measured critique, M6 causal disentangling, M8 algebraic derivation trace).
- [`docs/evaluation.md`](docs/evaluation.md) — evaluation methodology, per-finding blinded annotation, release-gate metrics, human-study protocols.
- [`docs/adding-agents.md`](docs/adding-agents.md) — design brief for extending the three-family panel to additional architectures.
- [`docs/roadmap.md`](docs/roadmap.md) — known bugs, planned improvements, open questions.
- [`docs/log/`](docs/log/) — dated dev log entries.
- [`SKILL.md`](SKILL.md) — the formal protocol Claude Code reads when executing `/disputatio`.
- [`CLAUDE.md`](CLAUDE.md) — orientation for Claude Code (working directory conventions, design principles).

---

## License & contact

Personal toolkit; not currently licensed for redistribution. Open an issue or reach out if you want to pilot it on a real manuscript.

Build log: [`docs/log/`](docs/log/) — each non-trivial change comes with a dated entry recording decisions and rejected alternatives.
