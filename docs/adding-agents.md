# Adding new agents

How to extend disputatio beyond the current Claude / Codex / Gemini trio (e.g. Kimi, Ollama-served local models, OpenCode-wrapped models, etc.) without breaking the design properties that make the current pipeline work.

This is a **design brief** with proposed answers, not a finalized spec. Each question lists the constraint, the options, and the recommended choice. Diverge from the recommendation only with a stated reason.

---

## Question 1 — What counts as a new agent?

### Constraint

The merge step weights cross-agent support at **×2** in ranking because agreement across *different model architectures* is a much stronger signal than agreement across multiple methods on a single architecture (which is correlated by construction).

If you add five "agents" that are all GPT-family models with different system prompts, you're inflating the cross-agent count without adding real independence. The ranking would over-weight noise.

### Options

| Option | Pro | Con |
|---|---|---|
| Anything callable as an external CLI counts | Easy to add | Loses the architecture-independence signal |
| Only different model *families* count | Preserves the signal | Makes "add Kimi" require thinking about whether Kimi is sufficiently different from GPT |
| Tiered: count cross-family at full weight, cross-instance-of-same-family at half weight | Captures both kinds of independence | More complexity in ranking math |

### Recommendation

**Cross-family at full weight; cross-instance-of-same-family at half weight.** Implementation:

- Tag each agent with a `family`: `anthropic`, `openai`, `google`, `moonshot` (Kimi), `meta` (Llama via Ollama), `alibaba` (Qwen via Ollama), `mistral`, etc.
- A finding raised by N agents has cross-family count `f` (distinct families) and within-family count `w = N - f`.
- New cross-agent support score: `min(3, f + 0.5·w)` — keeps the 0–3 scale but credits within-family agreement at half weight.

For practical onboarding:

- **Kimi** (Moonshot K2.5): family `moonshot`. Counts independently.
- **Ollama-served Llama 3**: family `meta`. Counts independently.
- **Ollama-served Qwen**: family `alibaba`. Counts independently.
- **OpenCode**: it's a CLI wrapper, not a model. What counts is the *underlying model* OpenCode invokes — tag accordingly.

---

## Question 1b — What about *fewer* agents? (Reduced-mode runs)

### Constraint

Adding agents past 3 is one direction; running on fewer is the other. The default is 3 distinct families because:

- **Cross-architecture independence** is the load-bearing claim of the panel. Three teams trained different ways catch each other's blind spots; one or two cannot.
- **Route A / Route B math is calibrated for an odd number of voters.** With 2 voters, ties are unresolvable. With 1 voter, "consensus" is meaningless.
- **Discoverer redundancy** — if one model hallucinates a finding, the other two are the brake. With 2 voters, the brake is half-strength; with 1 it is gone.

But there are real reasons someone might want a degraded run: lower cost, faster wall-clock, only one or two CLIs authenticated, or a content filter blocking one family on a given paper (Anthropic occasionally blocks adversarial-debate prompts on certain manuscripts).

The question is: **support reduced-mode officially, or refuse to run below N=3?**

### Options

| Option | Pro | Con |
|---|---|---|
| (a) Refuse to run below N=3 | Protects the calibration story; one mode, one set of claims | Forces failure when one family is unavailable; loses users who can't authenticate all three CLIs |
| (b) Allow 2-family as a peer of 3-family | Maximum flexibility | Most users will pick the cheaper option; panel quality drops silently; "disputatio is mediocre" gets attributed to the wrong cause |
| (c) Allow 2-family as a *documented reduced mode* with explicit messaging | Lowers the entry barrier without lying about what it bought | More UI surface; risk of users ignoring the messaging |
| (d) Allow 1-family as a "rapid mode" | Even cheaper | Cross-architecture verification is zero; the whole pitch collapses |

### Recommendation

**(c) — 2-family is a documented reduced mode; 1-family is refused.**

Concretely:

- **Default config remains `--agents claude,codex,gemini`** (3 distinct families). Site, README, and outreach materials describe only this configuration.
- **`--agents claude,gemini` (or any 2 distinct families) is supported** but emits a startup banner:
  ```
  [reduced-mode] running on 2 families (anthropic, google).
  cross-architecture verification is partial — see docs/adding-agents.md §1b.
  ```
- **Panel metadata records the actual configuration.** Each run writes `engine_metadata.cross_arch_support: "3-family" | "2-family"` and `engine_metadata.families_present: [...]`. Downstream readers see what they got.
- **`--agents claude` (single family) is refused** with a hard error pointing at this section. The cross-architecture argument has no weakened-but-valid form for N=1.
- **Two instances of the same family count as one.** `--agents claude,sonnet,haiku` resolves to family set `{anthropic}` and is refused as 1-family.
- **Route B (consensus override) is disabled in 2-family mode.** Two-voter "consensus" is too weak to override a strong individual signal. Route A escalation is also weakened — ties are surfaced to the panel as `disagreement_unresolved` rather than auto-routed.

### Why this matters for outreach

The website never mentions reduced mode. An econ professor who lands there sees the 3-family default. Someone who finds the flag in `--help` sees the explicit warning and chooses with full information. Same pattern as the rest of the project — *show what was killed, show the support level, don't hide the degradation.*

---

## Question 2 — How does role rotation extend past 3 agents?

### Constraint

Debate is structured around three roles (prosecute / defend / synthesise) and three rounds with role rotation, ensuring every model plays every role across rounds. The 3×3 design is part of why no single model gets the last word.

With N>3 agents, the 3-role × 3-round structure no longer maps 1:1.

### Options

| Option | Pro | Con |
|---|---|---|
| (a) Sample 3 of N each round | Keeps the existing debate structure unchanged | Some agents never play in a given debate |
| (b) Add a 4th role (e.g. "second-opinion synthesizer") | Uses all N each round | Doubles synthesis cost; unclear how the second opinion gets resolved |
| (c) Parallel debates with different 3-tuples per issue, then meta-merge | Maximises signal per issue | N²-ish cost blowup |
| (d) Keep 3 agents in debate; use extra agents only in discovery + verification | No debate structure changes | Extra agents under-utilised |

### Recommendation

**(a) — sample 3 of N per round, with weighted selection.** Implementation:

- Each agent has per-role aptitude weights (e.g. `prosecute_weight`, `defend_weight`, `synthesize_weight`) — set heuristically based on the model's strengths. Opus prosecute = 1.0, gpt-5.4 defend = 1.0, gemini-pro synthesize = 1.0; Kimi prosecute = 0.7; Ollama Llama defend = 0.5; etc.
- Per round, sample one agent for each role weighted by aptitude × not-recently-played penalty.
- "Not recently played" enforces rotation across rounds (if Codex defended round 1, Codex's defend weight halves for round 2).
- Across 3 rounds and N agents, every agent should play at least once unless N is very large.

For very large N (>6), consider also (d) — cap debate at 3 agents per issue, use the rest for orthogonal discovery sweeps.

---

## Question 3 — How does cross-agent support scoring scale?

### Constraint

Current scoring: `0 = one agent, 1 = two, 2 = all three, 3 = all three via different methods`. Hard-codes N=3.

### Options

| Option | Pro | Con |
|---|---|---|
| Linear scale capped at 3 | Simple | Loses the "via different methods" bonus |
| Fractional support rate (`found_by / N`) × 3 | Cleanly scales | Threshold at "all agents" gets harder as N grows |
| Cross-family weighted (Q1 recommendation) + method bonus | Captures both signals | More complex rubric for the merge agent to follow |

### Recommendation

**Cross-family weighted score (from Q1) + method bonus**, capped at 3. Formula:

```
support = min(3, f + 0.5·w + (1 if cross_method else 0))
```

Where `f` = distinct families that found it, `w` = within-family duplicates, `cross_method` = found via at least 2 different M-numbers (M2..M6).

This handles N=3 (current) as a special case: `f` ≤ 3, `w` = 0, support ∈ {0, 1, 2, 3}. Same as before. With N>3 it generalises naturally.

---

## Question 4 — How does discovery cost scale?

### Constraint

Current: 3 agents × 6 methods (M0 + M2..M6) = 18 discovery sweeps per paper. ~15 min wall clock at `concurrent=3`. Adding agents multiplies this linearly.

### Options

| Option | Pro | Con |
|---|---|---|
| Run all N agents on all 6 methods | Maximum signal | Linear cost growth in N |
| Run all N agents on a subset of methods | Bounds cost | Some method-agent combos missing |
| Tier: 3 "primary" agents do full discovery; extra agents do M5 only (highest-value method) | Balances cost and signal | Extra agents under-utilised |

### Recommendation

**`--discovery-agents N` flag with default 3.** Users opt into wider discovery for higher-signal runs (e.g. for papers with stakes high enough to justify 5×6 = 30 sweeps), default stays at the proven 3-agent configuration.

When N>3, run extra agents on M5 (immanent critique — the strongest method) only by default; full-method-grid is available via `--discovery-grid full`.

This makes "add Kimi to discovery" a one-flag operation rather than a structural change.

---

## Question 5 — How does `agent_ctl` accommodate N agent types?

### Constraint

Currently `agent_ctl.cmd_start` has explicit branches for `codex` and `gemini`. Each new agent CLI requires:

- A `build_X_cmd()` function (CLI command construction).
- A dispatch branch in `cmd_start`.
- An entry in `DEFAULT_MODELS` and possibly `FALLBACK_MODELS`.
- Prompt-file routing in `_build_shell_cmd` (for prompts > size threshold).
- Multi-turn handling in `cmd_send`.
- Possibly `output_format: json_stdout` salvage logic.

Adding three new agents (Kimi, Ollama, OpenCode) as branches → three sets of code edits in five places each = 15 edit sites.

### Options

| Option | Pro | Con |
|---|---|---|
| Keep branches, add three more | Minimal change | Branches proliferate; new bugs introduced via copy-paste |
| Refactor to per-agent `AgentSpec` dataclass | Clean abstraction; new agents are one config block | Bigger upfront refactor; may reveal hidden coupling |
| Plugin loader (each agent in its own file under `agents/<name>.py`) | Most extensible | Overkill for the current scale |

### Recommendation

**Refactor to `AgentSpec`.** Single dataclass per agent capturing: family, default model, fallback model, command-builder callable, prompt-file pattern (inline vs stdin pipe), output-format hint, multi-turn protocol. Then `cmd_start` dispatches by registry lookup, not branches.

Suggested skeleton:

```python
@dataclass
class AgentSpec:
    name: str                              # "codex", "gemini", "kimi", ...
    family: str                            # "openai", "google", "moonshot", ...
    default_model: str
    fallback_model: str | None
    build_cmd: Callable[..., list[str]]    # build_codex_cmd, build_gemini_cmd, ...
    inline_prompt_threshold: int = 8192    # pipe via stdin above this
    output_format: str = "file"            # "file" or "json_stdout"
    supports_multi_turn: bool = True

AGENTS: dict[str, AgentSpec] = {
    "codex": AgentSpec(
        name="codex", family="openai", default_model="gpt-5.4",
        fallback_model="gpt-5.4-mini", build_cmd=build_codex_cmd,
    ),
    "gemini": AgentSpec(
        name="gemini", family="google", default_model="gemini-3.1-pro-preview",
        fallback_model="gemini-3-flash-preview", build_cmd=build_gemini_cmd,
        output_format="json_stdout",
    ),
    "kimi": AgentSpec(
        name="kimi", family="moonshot", default_model="k2.5",
        fallback_model=None, build_cmd=build_kimi_cmd,
    ),
    # ...
}
```

`cmd_start` becomes:

```python
spec = AGENTS.get(agent)
if spec is None:
    sys.exit(f"unknown agent '{agent}'")
agent_cmd = spec.build_cmd(...)
shell_cmd = _build_shell_cmd(spec, agent_cmd, args.prompt)
```

With this in place, **adding Kimi / Ollama / OpenCode is one new `build_X_cmd` per agent + one new `AGENTS` entry per agent.** Five edit sites collapse to two.

---

## Practical onboarding sequence

When the new session starts, suggested order:

1. **Refactor agent_ctl to AgentSpec** (Question 5). Validate by re-running an existing disputatio operation (e.g. just orientation on a test paper) to confirm Codex and Gemini still work through the new dispatch.
2. **Add Kimi support.** Easiest new agent — has its own CLI, single model. Ship a `build_kimi_cmd` + AGENTS entry. Test by invoking `agent-ctl start kimi "ping"`.
3. **Add Ollama support.** Trickier because the "model" is the loaded local model (qwen, llama3, etc.). Probably needs `--ollama-model <name>` mapping to family tag.
4. **Update merge ranking** (Question 3) — implement family-aware support scoring. Existing N=3 runs should produce identical scores as a sanity check.
5. **Update role rotation** (Question 2) — implement weighted aptitude sampling. Existing N=3 runs should still rotate Claude/Codex/Gemini in the canonical order as a sanity check.
6. **Add `--discovery-agents N` flag** (Question 4). Default stays at 3. Manual test with N=5 on a small paper.

Each step should be a separate commit with a passing smoke test.

---

## What stays unchanged

- The five-phase structure (orient → discover → merge & rank → debate → final report).
- The seven methods (M0 + M1 structural + M2..M6 generative + M7 synthesis-side).
- The ticket DAG, file layout, and resumability properties.
- The decision loop in the orchestrator.
- The judge.py / adapt.py evaluation harness.

The flexibility additions are **runtime** (more agents available) and **scoring math** (family-aware), not structural.
