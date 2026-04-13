# Method 4: Counterexample Construction

Take the paper's main result and try to find a case that satisfies its assumptions but violates its conclusion. If no counterexample exists, try to identify the hidden assumption that rules counterexamples out — that assumption is a lemma the paper relies on without stating.

## Procedure

1. **State the main result as a universal claim.** Rewrite the paper's main proposition in the form: *"For all X satisfying conditions Y, result Z holds."* Be precise about what X ranges over and what Y requires.

   Example: "For all X satisfying conditions A, B, and C, the paper's main result Z holds."

2. **Search the parameter space for violating cases.** Try, in order:
   - **Extreme values**: what happens as each parameter → 0 or → ∞?
   - **Degenerate cases**: what if a key variable is zero or one?
   - **Knife-edge cases**: what if a technical condition holds with equality rather than strict inequality?
   - **Cases excluded by the paper's examples**: try parameter values far from the paper's chosen calibration.

3. **For each candidate case, check whether it satisfies Y.** If it does not, the case is outside the claim's scope and cannot be a counterexample — move on. If it does, proceed.

4. **For each candidate case that satisfies Y, check whether Z holds.** Trace through the paper's proof. At which step does the proof either work or fail for this case?

5. **If Z fails**: you have a counterexample. This is a finding.

6. **If Z holds**: you have confirmation. But now ask: **why did Z hold?** The proof's logic for this case relies on some step. Was that step stated explicitly as an assumption? If not, it is a **hidden lemma** — a condition the paper relies on without making it a formal requirement. Hidden lemmas are themselves findings, because they mean the proposition is weaker than it appears.

7. **Repeat with degenerate cases.** Specifically test the cases where one of the assumptions holds only marginally. These are where hidden lemmas most often appear.

8. **Write each finding as an issue containing:**
   - The proposition as a universal claim
   - The candidate case (parameter values, assumed conditions)
   - Whether the case is a counterexample or required a hidden lemma
   - Which step of the paper's proof/argument is affected
   - The name the hidden lemma should have (if any)

## Output

Counterexamples and hidden lemmas are both concrete findings. A paper with no counterexamples and no hidden lemmas is robustly proved; a paper with either has a gap.

## Web search supports this method

The proof often references related results from the literature. Web search can be used to:
- Fetch the Internet Appendix where the full proof may live
- Verify that cited lemmas from other papers actually say what the proof claims they say
- Find counterexamples in related literature

## What it finds

- Propositions that are technically true but weaker than they appear
- Hidden assumptions smuggled into proofs
- Scope conditions the paper does not acknowledge
- Concrete violations at the boundary of the parameter space

## What it does not find

- Issues outside the proposition's scope (use Method 5 or 6)
- Rhetorical overclaiming where the formal result is correct but the interpretation stretches it (use Method 5)
