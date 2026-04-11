# Method 0: Close Reading

Mechanical line-by-line proofreading. No conceptual critique, no methodology analysis — just surface-level error detection. The goal is to catch every typo, notation inconsistency, sign error, and wording slip in the paper.

## Procedure

### Pass 1: Equations

For every numbered equation and every inline formula:

1. **Verify LHS = RHS after claimed operations.** If the paper says "substituting X into Y yields Z," perform the substitution yourself. Does it actually yield Z?
2. **Check exponents and squares.** A common error: claiming $\|x\|$ when the derivation requires $\|x\|^2$. Check every norm, every squared term, every exponent.
3. **Check subscripts and superscripts.** Does $x_\ell$ in one line match $x_\ell$ in the next, or did it silently become $x_{\ell+1}$?
4. **Differentiate stated Lagrangians.** If the paper displays a Lagrangian and then states the FOC, differentiate the Lagrangian yourself. Does your FOC match theirs?
5. **Verify change-of-variables.** If the paper defines $y = f(x)$ and then claims an expression in terms of $y$, substitute back and check.

### Pass 2: Cross-references

1. **Equation numbers.** When the text says "by equation (N)," does equation (N) actually say what the text claims?
2. **Proposition/theorem references.** When the text cites "Proposition K," check that Proposition K's statement supports the claim.
3. **Footnote claims.** Read every footnote. Verify any mathematical or factual claims in footnotes against the main text.
4. **Appendix consistency.** If the paper has an appendix, check that definitions and notation in the appendix match the main text.

### Pass 3: Notation consistency

1. **Symbol audit.** List every mathematical symbol and its definition. Flag any symbol used with two different meanings, or any meaning assigned to two different symbols.
2. **Convention consistency.** If the paper defines a convention (e.g., "boldface for vectors"), check it is followed everywhere.
3. **Definition-use alignment.** If a quantity is defined as $\alpha_\ell = (1-\beta\lambda_\ell)^{-2}$ in a display equation but written as $\alpha_\ell = (1-\beta\lambda_\ell)^{-1}$ inline, that is a finding.

### Pass 4: Prose accuracy

1. **Direction words.** When the paper says "increasing" or "decreasing," verify the sign of the relevant derivative. When it says "maximizer," verify it is not a minimizer.
2. **Quantifier accuracy.** "For all $\ell$" — does it really hold for all $\ell$, or are there exceptions?
3. **Scope modifiers.** "Under strategic complements" — does the claim also hold for substitutes? If so, the scope is understated. If not, is the restriction explicit?

## Output

Each finding is an issue with the standard schema. Impact guidance:

- **Sign error in a proof step**: local or material (depending on whether subsequent steps rely on it)
- **Missing square/exponent**: local (if it's a display issue) or material (if the proof depends on it)
- **Notation inconsistency between definition and use**: local
- **Direction word wrong (increasing/decreasing)**: local or material (if it's a comparative static claim)
- **Wording slip (maximizer/minimizer)**: minor
- **Cross-reference error**: minor (unless it invalidates an argument)
- **Pure typo with no mathematical consequence**: minor

## What this method finds

- Lagrangian/FOC mismatches
- Missing squares and exponents
- Sign errors in comparative statics
- Notation drift between sections
- Wrong direction words (increasing/decreasing/maximizer/minimizer)
- Cross-reference errors

## What this method does NOT find

- Conceptual issues (use M2-M6)
- Hidden assumptions (use M4, M5)
- Causal confounds (use M6)
- OCR artifacts (do NOT flag these)
