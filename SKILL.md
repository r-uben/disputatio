---
name: disputatio
description: High-precision academic paper review via multi-agent dialectic debate
---

# Disputatio

Review an academic paper using dialectic debate between independent AI agents.

## Usage

```
/disputatio <path-to-paper>
```

## Protocol

### Phase 1 — Discovery (parallel, all models)

All three agents read the paper independently and find candidate issues. This prevents single-model attention blind spots.

1. Parse the paper to `workspace/<paper-slug>/paper.md`
2. Launch all three agents in parallel, each reading the full paper
3. Each agent writes issues to `workspace/discovery/<agent>/issue_NNN.json`
4. Merge and deduplicate across agents into `workspace/issues/issue_NNN.json`

Each issue is a **falsifiable hypothesis**, not a comment:

```json
{
  "id": "issue_NNN",
  "claim": "what is concretely wrong",
  "quote": "the passage in question",
  "evidence": "why this is wrong, with specific references",
  "falsifier": "what evidence would kill this claim",
  "impact": "material | local | unclear",
  "source": "claude | codex | gemini",
  "paragraph_index": 42
}
```

Do NOT flag style, readability, or subjective issues. Only flag things that are concretely wrong or misleading. See `references/criteria.md`.

### Phase 2 — Dialectic Rounds

Each issue enters a debate. Three roles rotate across three agents each round:

| Role | Job |
|------|-----|
| **Prosecutor** | Steelman the criticism. Say exactly what is wrong, why it matters, what evidence would kill the claim |
| **Defender** | Steelman the defense. Give the best exculpatory reading, cite resolving context, say what evidence would kill the defense |
| **Synthesizer** | Produce an updated issue state — not keep/drop, but a refined understanding |

**Rotation schedule:**

| Round | Prosecutor | Defender | Synthesizer |
|-------|-----------|----------|-------------|
| 1 | Claude | Codex | Gemini |
| 2 | Codex | Gemini | Claude |
| 3 | Gemini | Claude | Codex |

For each round:

1. Send issue state + paper context to **Prosecutor** using `templates/prosecute.md`
2. Send issue state + prosecution + paper context to **Defender** using `templates/defend.md`
3. Send issue state + prosecution + defense + paper context to **Synthesizer** using `templates/synthesize.md`
4. Synthesizer outputs the new issue state → becomes input for next round

**Issue state** (evolves each round):

```json
{
  "id": "issue_NNN",
  "round": 2,
  "current_claim": "best current formulation of the issue",
  "accepted_facts": ["what both sides now agree on"],
  "refuted_components": ["parts of the prior claim that died"],
  "open_disputes": ["what remains unresolved"],
  "impact": "material | local | none | unclear",
  "next_question": "what would most reduce uncertainty",
  "status": "continue | converged | split | escalate",
  "history": [
    {"round": 1, "prosecution": "...", "defense": "...", "synthesis": "..."}
  ]
}
```

**Fast path:** If round 1 synthesis produces `status: "converged"` with `impact: "none"`, skip further rounds.

**Split:** If synthesis determines the issue contains multiple independent propositions, it may `split` into separate issues that enter debate independently.

**Escalate:** If the dispute depends on external conventions, hidden derivations, or calculations agents cannot verify, mark `escalate` — these go to the final report with uncertainty preserved.

### Convergence

Stop when:
- Synthesis stops changing materially (same claim, same evidence, same impact) → `converged`
- Paper text directly resolves the dispute → `converged` with `impact: "none"`
- Budget cap reached (default: 3 rounds) → take last synthesis as final
- Issue was split → child issues enter debate independently

### Phase 3 — Final Synthesis

Collect all converged issue states. For each surviving issue (`impact` != `none`):

1. Render as a structured reviewer comment with the full dialectic history
2. Preserve uncertainty — if `escalate`, say so explicitly
3. Include constructive suggestion where possible ("this could be fixed by...")

Write final output to `workspace/final.json`.

## Workspace structure

```
workspace/<paper-slug>/
├── paper.md                          # parsed paper text
├── checkpoint.json                   # resumable session state
├── discovery/
│   ├── claude/issue_NNN.json         # claude's raw findings
│   ├── codex/issue_NNN.json          # codex's raw findings
│   └── gemini/issue_NNN.json         # gemini's raw findings
├── issues/
│   └── issue_NNN.json                # merged/deduplicated issues
├── rounds/
│   └── issue_NNN/
│       ├── round_1_prosecute.json    # prosecution argument
│       ├── round_1_defend.json       # defense argument
│       ├── round_1_synthesize.json   # synthesis (new issue state)
│       ├── round_2_prosecute.json
│       └── ...
└── final.json                        # surviving issues as reviewer comments
```

## Agent routing

| Agent | CLI | Model |
|-------|-----|-------|
| Claude | Claude Code (you) | opus/sonnet |
| Codex | `/codex` via agent-ctl | GPT-5.4 |
| Gemini | `/gemini` via agent-ctl | Gemini 2.5 Pro |

All three agents take all three roles across rounds. The key property is **model independence**: different architectures prevent correlated errors.

## Agent communication

Use `agent-ctl` to manage sessions:

```bash
A="python3 ~/.claude/skills/agent_ctl.py"

# Start agents (codex runs with --full-auto by default, can write files)
$A start codex "PROMPT" --cwd <workspace> --timeout 600
$A start gemini "PROMPT" --cwd <workspace> --timeout 600

# Wait for agents to finish (blocks until done — no polling needed)
$A wait 01 02

# Get results
$A result 01
$A result 02

# Claude executes its role directly (no agent-ctl needed)
```

**Context injection**: When sending prompts to Codex/Gemini, always include the relevant content inline in the prompt (paper text, issue state, prior arguments). Do NOT rely on agents being able to read workspace files — inject the content directly. Agents should ALSO write their output to workspace files, but the prompt must be self-contained.

**Output verification**: After each agent call, verify the output file exists. If missing, parse the result from `$A result <id>` and write it yourself. Agents may fail to write files due to sandbox or filesystem issues — always have a fallback.

**Retry logic**: If an agent fails (rate limits, timeout), retry once. If it fails again, default to KEEP and move on.

## Checkpointing

After each round completes for each issue, update `checkpoint.json` with:
- Which issues have been discovered and merged
- Which rounds have completed per issue
- Current issue states
- Which issues have converged / split / escalated

If the session is interrupted, read `checkpoint.json` and resume from the last completed step.

## Prompt templates

Role-agnostic templates are in `templates/`:
- `prosecute.md` — steelman the criticism
- `defend.md` — steelman the defense
- `synthesize.md` — produce updated issue state
- `discover.md` — find candidate issues (used for codex/gemini discovery)

## Live report (Obsidian)

Maintain a live Obsidian note that updates as the review progresses. This lets the user watch the debate unfold in real time.

**Location**: `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/notes/work/referee-reports/tests/<paper-slug>.md`

**Format**:

```markdown
---
tags: [referee-report, disputatio]
paper: "<full paper title>"
authors: "<authors>"
venue: "<journal>"
status: "<discovery|debate|complete>"
date: <YYYY-MM-DD>
---

# Referee Report: <short title>

## Status
<current phase and progress>

## Discovery
<summary of issues found by each agent, merged count>

## Debate

### Issue 1: <title>
**Original claim**: ...
**Round 1**: Prosecutor (Claude) | Defender (Codex) | Synthesizer (Gemini)
- Prosecution: <1-2 sentence summary>
- Defense: <1-2 sentence summary>
- Synthesis: <outcome — what was accepted, refuted, still open>
- Status: converged | continue | split | escalate

**Round 2** (if needed): ...

### Issue 2: <title>
...

## Final Assessment
<surviving issues rendered as reviewer comments>
```

Update the note after each step:
1. After discovery → write the discovery section
2. After each debate round → append the round summary
3. After final synthesis → write the final assessment and set status to `complete`

## Review criteria

The criteria for what constitutes a valid issue are in `references/criteria.md`.
