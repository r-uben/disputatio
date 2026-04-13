---
tags: [disputatio, final-report, targeting-interventions]
paper: "Targeting Interventions in Networks"
authors: [Andrea Galeotti, Benjamin Golub, Sanjeev Goyal]
venue: Econometrica
phase: complete
date: 2026-04-11
---

# Referee Report: Targeting Interventions in Networks

## Overall Assessment

This paper makes a genuine and elegant contribution by showing how the spectral decomposition of the adjacency matrix organizes the optimal intervention problem in network games. The main results (Theorem 1, Corollary 1, Propositions 1-2) are mathematically correct under the stated assumptions. However, two material concerns emerge from this review. First, the abstract and introduction overstate the scope of the results by claiming that interventions "place more weight on top PCs" without qualifying that this refers to the similarity ratio; the absolute similarity depends on the status quo, and the formal theorem requires an unstated genericity condition. Second, the PC decomposition is presented as a property of network targeting when it is jointly driven by the quadratic cost and welfare structures; the paper's own appendix extensions show that changing either element eliminates the PC structure entirely. Beyond these two material concerns, the paper contains a missing-square typo in Assumption 3, a Lagrangian display error, and multiple notation errors in the Online Appendix, none of which affect the proofs. The "simple intervention" narrative over-attributes convergence speed to the spectral gap when the formal bound depends equally on the status quo norm. The claim that Property A is "not essential" understates the qualitative change when it fails.

---

## Material Issues

### M1. Absolute vs. ratio ordering in the headline claims (Score: 14/15)

**Claim.** The abstract states that under strategic complements, "interventions place more weight on the top principal components." Corollary 1 proves that the similarity *ratio* $|r_\ell^*|$ is decreasing in $\ell$, not that the absolute similarity $|\rho(\mathbf{y}^*, \mathbf{u}^\ell)|$ is ordered. The theorem requires a genericity condition (all PC projections nonzero) that is absent from its formal statement.

**Evidence.** The proof adds:

> "We take a generic $\hat{\mathbf{b}}$ such that $\hat{\underline{b}}_\ell \neq 0$ for all $\ell$."
> --- Appendix A, Proof of Theorem 1

This condition is absent from the theorem statement and Corollary 1. When it fails, the headline claim reverses. Concrete counterexample: $G = \begin{bmatrix}0&1\\1&0\end{bmatrix}$, $\beta = 1/2$, $\hat{\mathbf{b}} = (1,-1)/\sqrt{2}$. Then $\hat{\underline{b}}_1 = 0$, so $\rho(\mathbf{y}^*, \mathbf{u}^1) = 0$ for all $C$. The optimal intervention is entirely in $\mathbf{u}^2$ (the bottom eigenvector) despite strategic complements. Three agents (Claude, Codex, Gemini) independently identified this gap via five different methods (m2, m3, m4, m5, m6).

The abstract's phrasing:

> "In games of strategic complements (substitutes), interventions place more weight on the top (bottom) principal components, which reflect more global (local) network structure."
> --- Abstract

suggests absolute weight ordering, which is stronger than what Corollary 1 establishes.

**Debate outcome.** Defense concedes the genericity condition should be in the theorem statement and that "weight" in the abstract should mean similarity ratio. The counterexample is measure-zero but exposes the gap.

**Suggestion.** Add the genericity condition to Theorem 1 and Corollary 1. Clarify in the abstract that "more weight" means higher amplification of the status quo projection (similarity ratio), not absolute similarity.

---

### M2. PC decomposition is quadratic-structure-dependent, not network-intrinsic (Score: 13/15)

**Claim.** The principal component characterization of optimal interventions is a joint consequence of the quadratic cost function $K(\mathbf{b}, \hat{\mathbf{b}}) = \sum_i (b_i - \hat{b}_i)^2$ and the quadratic welfare (Property A), not an intrinsic property of network targeting. The paper's own appendix extensions show this: under L1 cost (OA3.3), the optimal intervention targets a single individual; under linear welfare (OA2.1), Bonacich centrality replaces eigenvector centrality.

**Evidence.** The proof of Theorem 1 exploits quadratic separability:

> "K(b, b\_hat) = sum (b\_i - b\_hat\_i)^2 <= C"
> --- Section 2, IT Problem

The IT-PC reformulation becomes $\max \sum_\ell \alpha_\ell \underline{b}_\ell^2$ subject to $\sum_\ell \underline{y}_\ell^2 \leq C$. This separability into independent per-component problems is *entirely* due to (a) quadratic cost (producing $\sum \underline{y}_\ell^2 \leq C$) and (b) quadratic welfare (producing $\sum \alpha_\ell \underline{b}_\ell^2$). The paper's OA3.3 confirms:

> Under L1 cost, the optimal intervention targets a single individual rather than distributing across principal components (Proposition OA3).

And OA2.1 shows that linear welfare yields Bonacich centrality targeting, not eigenvector centrality.

**Debate outcome.** Defense correctly notes the paper solves a specific, economically motivated model, not a universal theorem. But the prosecution's point stands: the main text narrative attributes the PC result to "the network" while the quadratic structure is presented as "technically convenient" rather than as a co-driver.

**Suggestion.** Acknowledge in the main text that the PC structure of optimal interventions is jointly driven by the quadratic cost and welfare functions, not solely by network eigenstructure.

---

## Local Issues

### L1. Convergence-speed narrative over-attributes to spectral gap (Score: 12/15)

The paper's narrative in Section 4.2 attributes the speed of convergence to simple interventions primarily to the spectral gap. However, Proposition 2's bound is:

$$C > \frac{2\|\hat{\mathbf{b}}\|^2}{\epsilon}\left(\frac{\alpha_2}{\alpha_1 - \alpha_2}\right)^2$$

Doubling $\|\hat{\mathbf{b}}\|^2$ doubles the required budget as much as halving the spectral gap.

> "spectral gap measures the level of 'cohesiveness' of the network, and it is this property that dictates fast convergence to simple interventions."
> --- Section 4.2

**Suggestion.** Emphasize the joint dependence on both spectral gap and $\|\hat{\mathbf{b}}\|^2$ in the narrative.

### L2. Missing square in Assumption 3 (Score: 11/15)

Assumption 3 reads $C < \|\hat{\mathbf{b}}\|$ but should read $C < \|\hat{\mathbf{b}}\|^2$. The preceding paragraph uses the correct squared form:

> "when the budget is large enough, that is, $C \geq \|\hat{\mathbf{b}}\|^{2}$"
> --- Section 4, paragraph before Assumption 3

Found independently by Claude and Codex.

### L3. Property A "not essential" overstates robustness (Score: 10/15)

When Property A fails (OA3.1), the welfare gains a linear term, requiring a two-stage optimization. Non-strategic externalities can shift the large-budget target from $\mathbf{u}^1$ to $\mathbf{u}^2$.

> "While Property A facilitates analysis, it is not essential."
> --- Section 2

**Suggestion.** Replace "not essential" with a statement that the PC technique extends but the characterization changes materially.

### L4. Lagrangian display error (Score: 9/15)

The Lagrangian in the proof of Theorem 1 writes $\hat{\underline{b}}_\ell$ (linear) instead of $\hat{\underline{b}}_\ell^2$ (squared) in the objective term. The FOC (equation 10) is derived from the correct squared version.

### L5. Utilitarian welfare values dispersion (Score: 8/15)

Property A's $W = w \sum (a_i^*)^2$ favors action dispersion (for $w>0$). The paper derives this from primitives (correctly), but the "utilitarian welfare" framing may mislead readers into thinking the planner values equality.

### L6. Online Appendix notation errors (Score: 8/15)

11+ notation/transcription errors in the appendix, including: Lemma OA1 eigenvector entries ($\sqrt{n}$ instead of $1/\sqrt{n}$), $C$ instead of $\sqrt{C}$ in admissible range, mixed $i/i^*$ indices in Proposition OA3, beauty contest sign condition, and others. None affect the proofs.

### L7. Proposition 2 domain error (Score: 7/15)

The bound $\sqrt{1-\epsilon}$ is undefined for $\epsilon \geq 1$, but the proposition quantifies over "any $\epsilon > 0$."

---

## Dropped Issues

| ID | Claim | Reason |
|---|---|---|
| merged_007 | "Parsimony" claim overstated (same computational complexity as direct solution) | Dropped: contribution is interpretive parsimony, standard meaning of "characterize" in economic theory |

---

## Appendix Concerns (not debated)

| ID | Claim | Score |
|---|---|---|
| merged_011 | Proof of Prop 2 attributes bound to Corollary 1 rather than Theorem 1 | 7 |
| merged_012 | Proof of Prop 4 has $\text{Var}(b_{\ell'}^*) > \text{Var}(b_{\ell'}^*)$ (self-comparison) | 7 |
| merged_013 | Example 2 circular notation: $b_i = [\tau - b_i]/2$ | 7 |
| merged_014 | Prop 4 implies correlated shocks in central agents are welfare-improving (conflicts with macroprudential intuitions) | 7 |
| merged_015 | Assumption 2 distinctness is load-bearing for per-component uniqueness, not just eigenvector uniqueness | 7 |

---

## Methodology

| Metric | Value |
|---|---|
| Discovery sweeps | 16 (Claude: 6, Codex: 6, Gemini: 4) |
| Raw issues | 98 |
| After triage | 69 |
| Merged clusters | 15 |
| Debated | 8 |
| Debate rounds | 8 |
| Material findings | 2 |
| Local findings | 7 |
| Dropped | 1 |
| Appendix | 5 |
