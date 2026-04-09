# Method 3: Systematic Transformation

Take each major claim in the paper and run it through a fixed set of transformations. Each transformation that produces a problem becomes a candidate issue. This method is mechanical — it does not require creativity, only completeness.

## Procedure

For each major claim (main result, proposition, key empirical finding), apply **every** transformation below. Each transformation is a separate attack candidate. Write down what each transformation reveals, even if the answer is "the claim survives."

### The eight transformations

**1. Negate.**
Take the claim "X." Consider "not-X." Does the paper's overall logic still work if we replace X with not-X? If yes, the claim may be doing no work — the paper's argument does not actually depend on it.

**2. Strengthen.**
Replace the claim with the strongest version consistent with its wording. If the paper says "X weakly increases," replace with "X strictly increases." Would the paper accept the stronger version? If not, why is the weaker version sufficient? The gap between the strong and weak version may be doing hidden work.

**3. Weaken.**
Replace the claim with the weakest version the paper's argument still requires. If the paper says "θ > 0," try "θ ≥ 0." Does the argument go through? If the paper needs strict positivity, which passage exactly relies on it? Is that passage defended?

**4. Substitute terms.**
Replace a key concept with a near-synonym or sibling concept. "Stockholder" → "high-income household." "Market portfolio" → "equity index." Does the claim still hold? If the substitution breaks the claim, the original depends on a connotation that was never formalized.

**5. Reverse the direction.**
The paper claims A causes B. Consider B causes A. Has reverse causation been ruled out? How? Consider A and B both caused by C. Has this been ruled out? The method forces the paper to confront alternative causal structures.

**6. Consequence test.**
From the claim, derive a prediction the paper does not state. For example: if asset prices overshoot optimally, then a central bank that targets zero overshooting should produce worse outcomes. Does the paper verify this prediction in its data? If not, can the prediction be tested with available evidence?

**7. Boundary test.**
Find the parameter values at which the claim just barely holds. What happens infinitesimally past those values? Are the critical values inside or outside the paper's calibration range? If outside, how far outside? The paper's claim may depend on being comfortably inside a region, but the calibration may sit near the boundary.

**8. Analogy test.**
Has a similar claim been made in a related literature? Look up the closest analogue. Does the established version have qualifications the paper ignores? Does the established version conflict with the paper's claim? If so, the paper owes the reader a reconciliation.

## Output

For each transformation that revealed a problem, write an issue containing:
- Which transformation was applied
- What it revealed
- The specific passage in the paper that fails under the transformation
- What would resolve the problem

If a transformation reveals nothing, note that explicitly — "applied transformation N to claim X, no issue found." This prevents the reader from wondering whether the method was applied at all.

## Web search supports this method

Transformations 6, 7, and 8 benefit directly from web search:
- **Consequence test**: search for whether the derived prediction has been tested elsewhere
- **Boundary test**: search for empirical ranges of the parameter
- **Analogy test**: search for the closest related claim in the literature
