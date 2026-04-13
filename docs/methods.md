# The seven methods

Disputatio's discovery and debate phases run a fixed set of seven critical methods. Each is described in `templates/methods/m<N>_*.md` as an operational procedure — a sequence of mechanical steps an agent executes — not as a philosophical doctrine. Agents apply the method without needing to know its name or origin.

This document explains what each method detects, when it's most useful, and gives examples from the targeting-interventions run.

---

## M0 — Close reading

A mechanical proofreading pass. The agent goes passage by passage looking for typographical errors, notation inconsistencies, sign mistakes, formula rendering errors, broken cross-references, and similar surface defects. **Not for substantive critique**; only for things a careful copy-editor would catch.

**Strongest at:** technical papers with heavy notation. Math-heavy economics, statistics, formal CS.

**Risk:** flagging OCR artifacts as paper errors. The prompt explicitly warns against this and cites the orientation map's `ocr_corrupted_sections` field.

**Example finding (targeting-interventions):**
Assumption 3 prints `C < ‖b̂‖` but the budget is in squared units throughout the rest of the paper, and the proof uses `C < ‖b̂‖²`. A one-character missing exponent that breaks dimensional consistency.

---

## M1 — Structured disputation (the debate format)

Not a discovery method. M1 is the **structural framework** that shapes every debate round. It enforces:

```
quaestio          (the question under debate, stated as yes/no)
   ↓
objections        (the prosecutor's case — independent, with cited passages)
   ↓
sed contra        (the defender's strongest one-line counter)
   ↓
respondeo         (the defender's positive position)
   ↓
replies           (defender answers each objection individually — concede, counter-evidence, re-interpret, or survive)
   ↓
synthesis         (third party identifies what the round established, what was refuted, what remains open, and a refined claim)
```

This format is the only thing keeping a multi-round debate from devolving into restating positions. The defender cannot dismiss objections in bulk — every objection gets a specific, evidenced reply.

---

## M2 — Interrogation by contradiction

Find pairs of claims in the paper that cannot both be true. Three sub-types:

- **Direct contradictions**: two statements that flatly disagree.
- **Scope contradictions**: a result claimed in general but proved only on a subdomain.
- **Implicit contradictions**: claim X in section A and claim Y in section B that, when their consequences are followed, conflict.

**Strongest at:** papers with long bodies, multiple sections developing the same machinery from different angles, or main-text-vs-appendix mismatches.

**Example finding (targeting-interventions):**
Lemma OA1 part 2 states `u_i^1(G) = √n`, but Fact 1 (the unit-norm convention used everywhere else) requires `‖u^1‖ = 1`, which forces `u_i^1 = 1/√n`. Worse: part 3 of the same lemma is arithmetically consistent only with `1/√n`. The lemma contradicts itself.

---

## M3 — Systematic transformation

For each load-bearing claim in the paper, apply eight mechanical transforms and ask whether the paper rules each out:

| # | Transform | Question |
|---|---|---|
| T1 | Negate | Does the paper foreclose the negation? |
| T2 | Strengthen | Is the stronger version proved? Or only the weaker? |
| T3 | Weaken | If we weaken, does the result still go through, or is the strength load-bearing? |
| T4 | Substitute | Replace a key parameter / function / structure with a related one — does the result survive? |
| T5 | Reverse | Swap cause and effect / antecedent and consequent — what breaks? |
| T6 | Consequence | What testable consequence does this claim have? Has the paper checked it? |
| T7 | Boundary | What happens at the limits (zero, infinity, degenerate cases)? |
| T8 | Analogy | Is there a parallel result in adjacent literature? Has the paper engaged with it? |

**Strongest at:** results that look more general than they are. The negate / strengthen / boundary transforms are the most productive in practice.

**Example finding (targeting-interventions):**
T3 (weaken): Property A requires exact quadratic welfare. Even the weakest natural generalisation (`f(‖a*‖²)` for nonlinear f) breaks separability and the closed-form result. The paper presents Property A as "technically convenient" — the transform shows it's load-bearing.

---

## M4 — Counterexample construction

For each formal proposition, attempt to construct a case that satisfies all stated assumptions but violates the conclusion. If you succeed, the proposition is wrong (or its assumptions are incomplete). If you can't, but you find that you needed an unstated lemma to defend it, you've found a hidden assumption.

**Strongest at:** theorem-and-proof papers, especially when the proof is technical and the theorem statement is short. The proof often invokes conditions that don't appear in the formal statement.

**Example finding (targeting-interventions):**
Theorem 1 states a closed-form for the optimal intervention via the similarity ratio `r_ℓ* = ρ(y*, u^ℓ)/ρ(b̂, u^ℓ)`. The proof divides by `b̂_ℓ` (change of variables) and silently requires `b̂_ℓ ≠ 0` for every ℓ. Constructing a status quo aligned with a network symmetry (e.g. a uniform `b̂` on a bipartite or cyclic network) produces zero projections on some eigenvectors — the proof breaks. The theorem statement listed only Assumptions 1–3, never the genericity hypothesis. The proof acknowledges it ("we take a generic b̂ such that ..."); the theorem doesn't.

This was the highest-scoring finding of the run (15/15) — found by all three agents through M3, M4, and M5 independently.

---

## M5 — Self-measured critique (immanent critique)

The strongest method. Two-step procedure:

1. Extract the paper's own commitments — what it explicitly promises to deliver, what scope it claims, what it says is essential vs technical, what it claims is novel, what it cites as already known.
2. Hunt for passages where the paper fails its own standard.

A finding from M5 has the form: "the paper commits to X (here), but does Y (there)." It includes both the commitment quote and the violation quote.

**Strongest at:** papers with explicit framing claims (in the abstract, intro, or discussion). The contrast between framing-level promises and body-level execution is rich.

**Example finding (targeting-interventions):**
The paper opens Section 5 with a commitment to extend the analysis to settings "where the planner does not know the parameters." Assumption 4 immediately rules out every feasible policy except a deterministic shift by setting `K = ∞` for anything else. Proposition 3's "robustness to uncertainty" result is then logically guaranteed by the feasibility restriction — there's no variance lever to use. The paper's framing committed to a robustness *result*; the analysis delivers a robustness *artifact*.

M5's findings are the hardest to defend against because the defender cannot deny the commitment (it's quoted) or the violation (it's also quoted). The defender can only argue that one of the two doesn't mean what it appears to mean — which is exactly the kind of debate that produces a useful refined claim.

---

## M6 — Causal disentangling

For each causal or structural claim, enumerate co-factors and co-effects the paper hasn't ruled out. Three sub-types:

- **Co-factors**: alternative mechanisms that could produce the same observed pattern.
- **Confounds**: variables affecting both proposed cause and proposed effect.
- **Joint-product attributions**: when result R depends on both A and B, but the paper attributes R to A alone.

**Strongest at:** empirical papers, identification papers, and theoretical papers that interpret a mathematical result as evidence for one mechanism when another would produce the same math.

**Example finding (targeting-interventions):**
The paper attributes the "principal-component concentration" of optimal interventions at large budgets to network structure. The same result depends just as strongly on cost curvature: the paper's own OA3.3 shows that linear separable costs produce single-node targeting (welfare centrality) instead of single-PC concentration. The "PC structure" is a joint product of network *and* quadratic cost; the paper attributes it only to the network.

---

## M7 — Iterative refinement (the synthesis step)

Not a discovery method either. M7 is the **operational procedure** the synthesizer follows to produce a refined claim after each debate round. Steps:

1. Copy the issue's current claim verbatim.
2. Inventory what the attack established (which objections produced specific evidence; which the defender conceded; which survived the reply).
3. Inventory what the defense established (which replies produced counter-evidence; which objections died; whether the self-commitment check passed).
4. Identify surviving ground (facts both sides now agree on).
5. Identify refuted components (parts of the original claim neither side defends).
6. Identify open disputes (specific points that remain unresolved).
7. Construct the refined claim — strongest version consistent with accepted facts and not touched by refuted components. Hidden assumptions exposed by the attack must appear as explicit conditions.
8. Label materiality (`material` / `local` / `none`).
9. Decide next step: `continue` (new round with rotated roles), `converged` (stable), `split` (issue contained multiple sub-issues), or `escalate` (needs human review).
10. Write a constructive suggestion (concrete change to the paper that would address the refined claim).

The output of each M7 application is the input to the next round (or the final state if the round converges).

---

## When each method is most productive

A rough heuristic from the targeting-interventions run, where every method × every agent ran (18 total sweeps producing 113 raw findings):

| Method | Findings (Claude / Codex / Gemini) | Notes |
|---|---|---|
| M0 close reading | 12 / 7 / 7 | Catches typos and notation slips; high specificity, mostly local impact |
| M2 contradiction | 9 / 3 / 5 | Finds main-text vs appendix mismatches, internal inconsistencies |
| M3 transformation | 10 / 6 / 4 | Productive on every paper; mechanical transforms always produce candidates |
| M4 counterexample | 12 / 2 / 4 | Strongest on theorem-heavy papers; finds hidden assumptions |
| M5 immanent critique | 9 / 2 / 4 | Lowest count but highest impact — the material findings cluster here |
| M6 causal disentangling | 10 / 4 / 4 | Finds attribution gaps; useful for interpretive narratives |

Claude's findings are denser than Codex / Gemini's, partly because Sonnet handles long context better than `gpt-5.4-mini` / `gemini-3-flash-preview` (the discovery-tier models). The merge step weights cross-agent agreement at 2× to compensate — a finding raised by all three agents (regardless of count per agent) is the strongest signal.

---

## Anti-patterns (things the methods are not for)

- **Style critique.** "The paper could be written more clearly" is not an issue.
- **Suggestions for future work.** "It would be interesting to extend this to ..." is not an issue.
- **Methodological preferences.** "I would have used a different estimator" is not an issue unless the paper's choice produces an actual error.
- **Speculation.** Every finding requires a verbatim quote and a falsifier. No finding without both survives triage.

The triage step in Phase 2 explicitly drops findings that are presentation-only complaints, singletons with low confidence, OCR artifacts, or self-retracted by the discovery agent. On the targeting-interventions run, 16 of 113 raw findings were triaged at this step.
