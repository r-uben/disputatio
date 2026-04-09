## Disputatio

High-precision academic paper review via seven-method dialectic debate. This is a Claude Code skill, not a Python package — Claude Code is the runtime.

### How it works

`/disputatio paper.pdf` runs a five-phase pipeline:

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

### Key design decisions

- **No Python runtime** — Claude Code orchestrates, agents communicate via files
- **Three independent readers** — each agent produces its own paper map; maps are never merged. Cross-agent consensus on issues is the strongest signal
- **Methods, not labels** — prompts describe procedures operationally. Agents execute the method without knowing its philosophical lineage
- **Five generative + one structural + one iterative = 7 methods** — every method has a natural slot, none is redundant
- **Web search is an on-demand specialty** — Gemini owns it; other agents flag issues for verification; web search is not sprayed across every discovery pass
- **Cross-agent support weighted ×2** — the strongest ranking signal (more robust than cross-method within one agent)
- **Pre-debate triage + round-1 early-kill + stalled-debate termination** — aggressive short-circuits keep runtime bounded
- **Role rotation with 3-round cap** — different agents prosecute, defend, synthesize across rounds

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
- `agent-ctl` (`~/.claude/skills/agent_ctl.py`) with `wait` subcommand and `--full-auto` default for Codex
