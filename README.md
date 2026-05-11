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

The repo includes the `disputatio` skill plus pinned snapshots of three helpers it relies on at runtime: the `codex` and `gemini` second-opinion skills (under `vendor/skills/`) and the `agent_ctl.py` orchestrator (under `vendor/`). One script wires everything into `~/.claude/skills/` as symlinks:

```bash
git clone https://github.com/r-uben/disputatio.git
cd disputatio
./install.sh                  # disputatio + vendored helpers
./install.sh install --minimal   # disputatio only, keep your own helpers
```

Use `--minimal` if you already maintain your own `codex`/`gemini` skills or your own `agent_ctl.py`. The full install will replace those (after backing them up to `*.bak.<timestamp>`); `--minimal` leaves them alone and only links the disputatio skill itself.

The codex/gemini skills and agent_ctl.py under `vendor/` are pinned snapshots — they may drift behind their upstream sources between disputatio releases. If you need a newer version of those skills, use `--minimal` and install them yourself.

To remove the symlinks and restore backups:

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

Disputatio is in active evaluation. The architecture is built — finding panel as primary deliverable, prose memo as secondary, single-writer rendering for voice uniformity. Nine discovery tickets (three readers × three tracks: holistic, broad critic, narrow evidence-judgment). Debate runs escalation-only on contested findings, not by default. Calibration enforces a per-finding blinded annotator with demote-or-drop on overclaim.

What is **not** yet established: panel quality at scale, validated through author and referee feedback on real manuscripts. That is the open question this evaluation phase exists to answer. Pipeline history in [`CHANGELOG.md`](CHANGELOG.md) and dated entries under [`docs/log/`](docs/log/).

Known operational limitations:

- **Anthropic content filter** occasionally blocks verbatim quotation prompts on certain manuscripts (van Vreeswijk 1998 reliably triggers it). The graceful-degradation contract handles partial-family runs with reduced coverage.
- **Gemini OAuth** can silently expire mid-run; no automatic re-auth.
- **gemini-3.1-pro-preview** hits capacity 429 under load; manual retry or fallback.
- **Codex (ChatGPT Pro OAuth) weekly cap** — heavy users hit it after roughly one full run; `agent-ctl` currently supports only the OAuth path.

---

## Documentation map

- [`docs/architecture.md`](docs/architecture.md) — ticket DAG, agent routing, model routing, file layout, resumability, decision loop.
- [`docs/methods.md`](docs/methods.md) — the discovery methods folded into the three tracks (M0 close reading, M2 contradictions, M3 transformations, M5 self-measured critique, M6 causal disentangling, M8 algebraic derivation trace).
- [`docs/adding-agents.md`](docs/adding-agents.md) — design brief for extending the three-family panel to additional architectures.
- [`docs/log/`](docs/log/) — dated dev log entries.
- [`SKILL.md`](SKILL.md) — the formal protocol Claude Code reads when executing `/disputatio`.
- [`CLAUDE.md`](CLAUDE.md) — orientation for Claude Code (working directory conventions, design principles).

---

## License & contact

Personal toolkit; not currently licensed for redistribution. Open an issue or reach out if you want to pilot it on a real manuscript.

Build log: [`docs/log/`](docs/log/) — each non-trivial change comes with a dated entry recording decisions and rejected alternatives.
