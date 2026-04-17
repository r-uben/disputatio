# M8 — Algebraic Derivation Trace

Re-derive a proof step-by-step and flag anywhere the paper's algebra loses a term, inverts a sign, drops a square root, or lands on an impossible value (negative Lagrange multipliers, negative variances, complex moduli, densities outside [0,1]).

This method closes a gap that M3/M4/M6 do not reliably catch. M3 transforms the claim; M4 looks for counterexamples at the assumption-scope level; M6 enumerates co-factors. None of them force the agent to walk the proof's own algebra end to end. The 2026-04-15 A/B against coarse.ink surfaced two material findings v6 missed that a line-by-line derivation would have caught: a missing √ in a feasibility interval, and a Theorem OA1 large-C limit formula that can yield a non-positive Lagrange multiplier.

## When to apply

Mandatory in the `narrow_evidence` track, at least once per selected attack surface whose `type ∈ {theory, proof}` and whose `paper_location` points at a specific theorem, proposition, corollary, or lemma. Optional in `broad_critic` if the close-reading pass flags a suspicious sign or dimensional inconsistency.

Not useful for pure framing / exposition / identification concerns — M8 needs explicit algebra to trace.

## Procedure

1. **Lock the target.** Pick one derivation: the proof of Theorem X, the first-order conditions for Proposition Y, a limit argument in Corollary Z, or a step inside a displayed equation chain. Quote the paper's final claim verbatim in `evidence[0].quote` so the target is pinned.

2. **Replay every step, in your own notation, on scratch.** Start from the stated assumptions + premises. Write every algebraic step the paper skips. Do not paraphrase the math — redo it. If the paper writes "and so the optimality condition is (8)", you derive (8) from scratch and check.

3. **Check at each step:**
   - **Signs**: did a `−` flip to `+` under a substitution? Do the variables the paper calls positive stay positive after each transformation?
   - **Squares / square roots**: if a constraint is `x² + y² = C`, does the paper write `x + y = C` or `x = √C`? Squared terms that become linear, or scalar constraints that forget the root, are the most common slip.
   - **Denominator positivity / nonzero**: does the paper divide by something it has not proved nonzero? Generic-`b̂` assumptions that live in proofs but not in statements belong here.
   - **Index consistency**: does a sum over `ℓ=1..n` lose one term on a re-indexing step? Is a Kronecker δ dropped on a substitution?
   - **Feasible set boundaries**: does the paper's final expression still live inside the stated feasibility region? (Example: a Lagrange multiplier on a binding inequality constraint must be `≥ 0`. An optimal choice of a probability must be `∈ [0,1]`. A norm must be `≥ 0`.)
   - **Limit positivity**: when the paper takes `C → ∞` or `β → 0`, does the resulting expression still satisfy the physical constraint it satisfied at finite values? A limit that produces a negative Lagrange multiplier is a proof bug.
   - **Dimensional / units consistency**: does each term carry the same units? This catches dropped factors of `n`, missing `1/σ²`, or added-together quantities that shouldn't be.

4. **If every step checks out**, M8 produces no finding — record the pass in the session log ("M8 trace of Prop 2 proof: clean") and move on.

5. **If a step breaks**, emit the finding with:
   - `method: "m8"`
   - `m8_derivation_trace`: the specific step that breaks, written out. Not prose — actual algebra, in the paper's notation, showing the paper's step on one line and the corrected step on the next. Max ~10 lines.
   - `claim`: "Proposition/Theorem/Lemma X's derivation at step Y contains <specific error>"
   - `evidence[0].quote`: the paper's exact line of algebra
   - `evidence[0].location`: section / page / equation anchor
   - `evidence[0].support_type`: `"direct_quote"` — the quote IS the wrong line
   - `falsifier`: "correct derivation of the same step yields a consistent result"
   - `impact`: `material` if the error propagates to the theorem's statement; `local` if it's a proof-internal slip that the theorem still survives; `nit` if it's a typo that any reader can mentally patch
   - `confidence`: `high` — the trace either shows the break or it doesn't

## Discipline

- **One step per finding.** If a proof has three algebra bugs, emit three findings. Do not bundle.
- **Show the corrected step.** Vague "the algebra doesn't work" is useless. Write the paper's step and the right step, side by side, in `m8_derivation_trace`.
- **Distinguish proof-internal slips from theorem-level errors.** A dropped √ inside a proof that still lands on a correct final expression is `local` at worst. A dropped √ that propagates to the theorem statement is `material`.
- **Negative-Lagrange test is mandatory for every optimisation paper.** When the paper solves `max f(x) s.t. g(x) ≤ C` with a binding constraint, check every expression for the multiplier and confirm `λ ≥ 0` at every stated solution, including in limits.
- **Do not invent algebra the paper doesn't contain.** If the paper handwaves a step, note it ("paper asserts Y without derivation; replaying gives Z; gap is material") but do not claim the paper wrote Z when it didn't.

## Relation to other methods

- **M0 (close reading)** flags isolated typos; M8 flags typos that break a derivation.
- **M3 (transformation)** asks what happens at the assumption boundary; M8 asks whether the paper's stated derivation is correct inside the stated assumptions.
- **M4 (counterexample)** constructs a case satisfying assumptions but violating the conclusion; M8 rejects the proof from the inside rather than attacking it from the outside.
- **M6 (causal disentangling)** adds external co-factors; M8 stays entirely inside the paper.

M8 is closest to M4 in spirit (both attack the proof) but narrower in execution: M4 is about the logical structure of the result; M8 is about the algebra of the argument.

## OCR warning

The narrow track already warns agents not to flag OCR artifacts as paper errors. This warning is doubly important for M8 — OCR commonly drops superscripts and confuses `0` with `O` inside equations. Before emitting an M8 finding, verify the suspect algebra by cross-reading the figure or surrounding text to rule out an OCR artefact. If in doubt, note the suspicion in `ocr_concerns` rather than in `issues`.
