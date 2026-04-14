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
- `agent-ctl` installed at `~/.claude/skills/agent_ctl.py` for ticket DAG execution. A vendored snapshot lives in [`vendor/agent_ctl.py`](vendor/agent_ctl.py); install with:
  ```bash
  mkdir -p ~/.claude/skills
  cp vendor/agent_ctl.py ~/.claude/skills/agent_ctl.py
  chmod +x ~/.claude/skills/agent_ctl.py
  ```
- An Obsidian vault to host the per-paper review folder at `notes/work/referee-reports/<paper-slug>/`.

---

## The finding panel

Every run writes `_artifacts/json/panel.json` as the canonical output. One entry per surviving finding:

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
├── 0_holistic/                   ← cross-architecture paper map and attack-surface index (NEW in v6)
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

**v6 upstream pivot in progress (2026-04-14).** Product repositioned from "referee report as primary deliverable" to "finding panel as primary deliverable, prose memo as secondary." Discovery tickets cut from 18 (3 agents × 6 methods) to 9 (3 agents × 3 tracks). Holistic pass added upfront. Debate moved from default-on-top-N to escalation-only on contested findings. Single-writer rendering replaces fragment assembly for prose uniformity.

**v5 calibration results on Galeotti-Golub-Goyal 2020 (Econometrica):** 0% fabrication rate (down from 18.8% in v4), 22% pre-demote overclaim rate (down from 56% in v4), 0% user-visible overclaim after demotion by construction. 27 atomic merged findings passed verbatim-quote validation. See [`docs/log/`](docs/log/) for full run history.

**Known limitations** (full list in [`docs/roadmap.md`](docs/roadmap.md)):
- Codex (ChatGPT Pro OAuth) enforces a weekly cap. High-volume users need a direct API-key transport; `agent-ctl` currently supports only the OAuth path.
- Gemini's OAuth silently expires mid-run with no error surfacing through `agent-ctl`. Long runs need to detect `FatalCancellationError` and halt the DAG with an actionable message.
- The v6 holistic pass is new and its effect on final finding precision has not yet been measured on a benchmark. Expect early runs to surface more framing/scope concerns than prior versions.

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

- [`docs/v6-upstream-plan.md`](docs/v6-upstream-plan.md) — the v6 pivot: product, pipeline diff, schema, metrics, positioning copy.
- [`docs/architecture.md`](docs/architecture.md) — ticket DAG, agent routing, model routing, file layout, resumability, decision loop.
- [`docs/methods.md`](docs/methods.md) — the discovery methods that survive in v6 (M0 close reading, M2 contradictions, M3 transformations, M5 self-measured critique, M6 causal disentangling plus the new M8 holistic scope-mismatch pass).
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
