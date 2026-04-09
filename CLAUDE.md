## Disputatio

High-precision academic paper review via seven-method dialectic debate. This is a Claude Code skill, not a Python package — Claude Code is the runtime.

**Orchestration is ticket-based.** Every agent call is a ticket in a DAG (`<paper-folder>/_artifacts/tickets.json`). Claude generates tickets in waves; `agent-ctl run-dag` executes them. Session logs are auto-archived. The entire review is resumable, auditable, and reproducible. See `templates/emit_tickets.md` for the ticket schema and wave protocol.

**Obsidian is the workspace.** Every review is a self-contained folder inside the Obsidian vault at `notes/work/referee-reports/tests/<paper-slug>/`. Curated markdown lives in numbered folders (`00_review.md`, `10_paper/`, `20_orientation/`, ...); raw artifacts live in `_artifacts/` as non-markdown files. See `templates/obsidian_structure.md` and `templates/obsidian_render.md`.

### How it works

`/disputatio paper.pdf` runs a five-phase pipeline orchestrated as a ticket DAG. Claude generates tickets in waves; `agent-ctl run-dag` executes each wave; between waves Claude inspects outputs and emits the next wave.

0. **Orientation** — each of 3 agents reads the paper once and produces a neutral paper map (claims, equations, propositions, assumptions, parameters, citations). Paper maps are NOT merged — each agent uses its own as a cache to preserve model independence
1. **Discovery** — each agent runs all 5 generative methods (M2-M6) on the paper using its own cache. Fan-out-fan-out parallelism: 3 agents × 5 methods = 15 concurrent discovery sweeps
2. **Merge, rank, verify** — triage OCR artifacts, deduplicate across agents, rank by (centrality + 2×cross-agent-support + evidence specificity + severity), Gemini runs web verification on issues that need external facts
3. **Dialectic debate** — top N issues enter structured disputation (quaestio → objections → sed contra → respondeo → replies → synthesis). Roles rotate across agents each round. Aggressive short-circuit rules
4. **Final report** — structured final.json + live Obsidian note

### The seven methods

All seven are defined in `templates/methods/` as operational procedures. No philosopher names in the prompts — just mechanical steps the agents execute.

| # | Method | Role |
|---|--------|------|
| 1 | Structured disputation | Shapes every debate round |
| 2 | Interrogation by contradiction | Finds pairs of claims that can't both be true |
| 3 | Systematic transformation | 8 mechanical transforms per claim |
| 4 | Counterexample construction | Exposes hidden lemmas |
| 5 | Self-measured critique | Strongest method: finds paper violating its own commitments |
| 6 | Causal disentangling | Enumerates co-factors and co-effects |
| 7 | Iterative refinement | Synthesis across rounds |

### Structure

```
disputatio/
├── SKILL.md                         # full protocol
├── CLAUDE.md                        # this file
├── templates/
│   ├── emit_tickets.md              # ticket schema + wave protocol
│   ├── obsidian_structure.md        # per-paper Obsidian folder spec
│   ├── obsidian_render.md           # how Claude renders JSON → curated markdown
│   ├── orient.md                    # produce paper map
│   ├── discover.md                  # run all 5 generative methods
│   ├── merge_and_rank.md            # merge, dedupe, rank
│   ├── verify.md                    # Gemini web verification
│   ├── prosecute.md                 # pick 2-3 methods, build objections
│   ├── defend.md                    # structured disputation reply
│   ├── synthesize.md                # method 7 applied
│   └── methods/
│       ├── m1_disputation.md
│       ├── m2_contradiction.md
│       ├── m3_transformation.md
│       ├── m4_counterexample.md
│       ├── m5_immanent.md
│       ├── m6_disentangling.md
│       └── m7_refinement.md
└── .gitignore
```

A review lives inside the Obsidian vault, not this repo:

```
notes/work/referee-reports/tests/<paper-slug>/
├── 00_review.md                     # top-level index
├── 10_paper/paper.md
├── 20_orientation/                  # 3 paper maps as markdown
├── 30_discovery/                    # organized by method
├── 40_ranking/                      # issue_register.md is the source of truth
├── 50_debates/                      # one folder per debated issue
├── 60_final_report/referee_report.md
└── _artifacts/                      # tickets.json, prompts/, sessions/, json/
```

See `templates/obsidian_structure.md` for the full folder spec.

### Key design decisions

- **Ticket DAG orchestration** — every agent call is a ticket on disk. Claude plans, `agent-ctl run-dag` executes. Resumable, auditable, reproducible
- **No Python runtime** for the skill logic — Claude Code orchestrates, agents communicate via files, agent-ctl is the only moving part
- **Three independent readers** — each agent produces its own paper map; maps are never merged. Cross-agent consensus on issues is the strongest signal
- **Methods, not labels** — prompts describe procedures operationally. Agents execute the method without knowing its philosophical lineage
- **Five generative + one structural + one iterative = 7 methods** — every method has a natural slot, none is redundant
- **Web search is an on-demand specialty** — Gemini owns it; other agents flag issues for verification; web search is not sprayed across every discovery pass
- **Cross-agent support weighted ×2** — the strongest ranking signal (more robust than cross-method within one agent)
- **Pre-debate triage + round-1 early-kill + stalled-debate termination** — aggressive short-circuits keep runtime bounded
- **Role rotation with 3-round cap** — different agents prosecute, defend, synthesize across rounds
- **Deterministic ticket emission** — only Claude (via the wave protocol) emits new tickets. Agents never self-schedule more work

### Lessons from testing

- **Codex needs `--full-auto`** (now default in agent-ctl) to write files
- **Gemini CLI lacks `write_file`** — we parse stdout and save manually
- **Gemini hits server-side 429s** (capacity exhausted, not quota) — retry with backoff
- **Agents hallucinate file writes** — always verify the output file exists
- **OCR'd papers need explicit warnings** — hallucinated text blocks from unrelated documents get flagged as "errors" otherwise
- **Long prompts need temp files** — inline shell escaping breaks beyond a few KB
- **`$A wait <ids>` eliminates polling loops** — use it

### Prerequisites

- `codex` CLI installed and authenticated (ChatGPT Pro)
- `gemini` CLI installed and authenticated (Google OAuth)
- `agent-ctl` (`~/.claude/skills/agent_ctl.py`) with `wait`, `run-dag`, and `dag-status` subcommands, and `--full-auto` default for Codex
