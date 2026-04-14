# Method 5: Self-Measured Critique

The strongest form of criticism. Never criticize the paper by external standards — the author can always say "you don't understand what I'm trying to do." Instead, find the paper's own commitments and show where the paper violates them. This criticism cannot be dismissed.

## Procedure

### Step 1: Enumerate the paper's commitments

A **commitment** is anything the paper explicitly or implicitly holds itself to. Read the paper twice — once to list explicit commitments, once to list implicit ones.

**Explicit commitments** to look for:
- **Assumptions stated in the setup.** "We assume agents are rational." "The central bank has no commitment device." "Prices are fully sticky."
- **Standards the paper claims to meet.** "We provide a microfoundation for X." "Our results are empirically identified." "The model is internally consistent."
- **Normative targets.** "Our policy recommendation maximizes welfare." "The optimum is Pareto efficient." "Our calibration targets empirical moments."
- **Methodological rules.** "We log-linearize around the steady state." "We assume no risk premium." "We use daily data."
- **Scope conditions.** "Our results apply to small deviations from steady state." "We focus on the recovery phase."
- **Definitions.** "By 'output gap' we mean the log-deviation of output from potential."

**Implicit commitments** to look for:
- **Unstated assumptions the proofs rely on.** (Often found by running Method 4 first.)
- **Standards the paper takes for granted from its field.** "Rational expectations" in a New Keynesian paper. "No-arbitrage" in an asset pricing paper.
- **Consistency between sections.** A paper that uses a model in Section II implicitly commits that Section III's empirical work is consistent with that model.

### Step 2: For each commitment, hunt for violations

For each commitment C, search the entire paper for passages where C is **abandoned, contradicted, or quietly relaxed**. Cases to look for:

- **Empirical violation of a theoretical assumption.** The paper defines a parameter as one thing in theory, then uses it as something different in the calibration.

- **Scope violation.** The paper claims a restrictive scope in the setup (e.g., "small deviations"), then applies the model to cases outside that scope.

- **Methodological violation.** The paper commits to a methodological rule in one section, then the analysis relies on something that violates that rule.

- **Normative drift.** The paper's welfare function penalizes X, but the policy recommendation would increase X.

- **Definitional drift.** A term is defined precisely in Section I and used loosely in Section III. The meaning has shifted without acknowledgment.

- **Standards violation.** The paper claims to provide a microfoundation but the "microfoundation" assumes the thing it was supposed to explain.

### Step 2b: Scope-mismatch checklist (v5, explicit)

The 2026-04-14 v4 run on Galeotti-Golub-Goyal missed a textbook M5 finding: Section 5 is titled *"Incomplete information"* but footnote 23 explicitly states *"the game individuals play is one of complete information."* That is a commitment-violation of the title by a footnote in the same section. coarse.ink's single-shot opus caught it; our M5 didn't elevate it reliably. To close that gap, walk this checklist for every paper:

- **Section title vs section body.** Does each section's title describe what the section actually proves? A section titled "Incomplete information" that proves a complete-information result is a commitment violation.
- **Abstract promise vs theorem condition.** The abstract typically states the main result without conditions. Does the theorem statement contain conditions the abstract doesn't mention? (e.g., "Property A", "generic b̂", "w > 0".) If yes, the abstract has committed to a broader claim than the theorems establish.
- **Footnote vs body.** Footnotes often walk back or qualify the body's claims. List every footnote that adds a condition, exclusion, or acknowledgment; then check whether the body (the thing a reader actually reads) honors it.
- **Introduction narrative vs formal statement.** Intro-section prose frames results informally. Compare each informal framing to the theorem's formal statement — if the intro says "for any network" and the theorem says "for any symmetric network with distinct eigenvalues", the commitment differs.
- **Generality promise vs extension scope.** If the paper claims a result "extends to general X" and the extension (usually in an online appendix) applies only under additional assumptions, that is a commitment violation unless the additional assumptions are flagged at the generality promise.
- **Caption vs figure content.** Figure captions sometimes claim the figure illustrates a "general feature" when the figure's specific setup is non-generic.
- **Assumption labeled "generic" or "technical" vs its actual effect.** Anything labeled merely "for technical convenience" that the proof critically depends on is a commitment violation — the paper understated its role.

Each checklist item is a potential finding. Do NOT invent violations; only report checklist items where you find a concrete text pair (commitment + violating passage) both quotable verbatim.

### Step 3: Write each violation as an issue

Every issue from this method must contain **two citations**:
- The commitment, with exact quote and location (the paper committing to X)
- The violation, with exact quote and location (the paper doing not-X)

And a formulation of the form: *"The paper commits to X in [passage A]; in [passage B] it does not-X. Either X must be dropped or passage B must be revised."*

## Output

Each finding from this method is maximally robust because the author cannot dismiss it. Their only options are:
- Drop the commitment (and rewrite the paper)
- Revise the violating passage (and acknowledge the fix)
- Argue that the violation is only apparent (and explain why)

## Web search supports this method

- Check whether the paper's cited sources actually make the commitments the paper attributes to them
- Verify that the paper's data sources have the properties the paper's methodology requires
- Fetch the Internet Appendix to see if it addresses the violation

## Note on defensive use

This method can also be used **by the defender** to show that the paper DOES honor its commitments. In that case, the defender enumerates the commitments and, for each one, cites the passages that uphold it. A defense using this method is stronger than one that simply asserts the paper is fine.
