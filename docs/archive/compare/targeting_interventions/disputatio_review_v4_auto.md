# Referee Report: Targeting interventions in networks

**Date**: 2026-04-12
**Domain**: Academic review

---

## Overall Feedback

**Central Assessment**
The paper proposes a principal-component characterization of optimal budget-constrained interventions in linear-quadratic network games: the planner's optimal incentive shift decomposes into the spectral basis of the network, weighted by similarity ratios r_ℓ* that trade off the strategic amplification α_ℓ against the loading of the status quo b̂ on each component. The central mathematics is correct on the generic interior of the status-quo space, and the decomposition into mean-shift and variance-intervention channels (Section 5) is clean. Two material issues should be addressed before publication: Theorem 1's formal statement omits the genericity condition b̂_ℓ ≠ 0 that its proof invokes, and the abstract's unqualified "determined by the network, ordered by eigenvalues" framing does not survive the paper's own SVD extension to non-symmetric networks. Six further local issues involve printed typos, dimensionally incorrect norm exponents in Assumption 3, and scoping overstatements in the abstract and Proposition 3. None of these threaten the core contribution, but they merit attention in revision.

**Overall Verdict**
The paper's central contribution — a clean principal-component characterization of optimal network interventions, with a parallel mean/variance decomposition under uncertainty — survives the review intact. The required corrections are precise and surgical: an explicit genericity hypothesis on Theorem 1, a scoping qualifier on the abstract's "network-determined" framing to distinguish the symmetric benchmark from the non-symmetric extension, four narrowly-scoped clarifications (Assumption 3's norm, Proposition 3's instrument class, Proposition 2's w-regime, the Figure 2 eigenvalue claim), and a proofreading pass over the Online Appendix. None of these undermine the paper's main results; taken together they would strengthen an already substantive contribution.

**Main Issues Identified**

- **Theorem 1 silently requires a genericity condition on the status quo**: Theorem 1's closed-form characterization via the similarity ratio r_ℓ* relies on the unstated hypothesis that b̂_ℓ ≠ 0 for every principal component ℓ. Without it, the variable change x_ℓ = y_ℓ/b̂_ℓ used throughout the proof is undefined (0/0), and the KKT step ruling out μ = w·α_ℓ (which divides by 2·b̂_ℓ²·w·α_ℓ) collapses. The zero-loading case is not pathological — it arises naturally whenever the status quo exhibits the same symmetries as the network (regular, bipartite, and cycle graphs with uniform b̂ all produce zero projections onto some eigenvectors).

- **The non-symmetric extension loses the paper's headline economic interpretation**: The abstract asserts that optimal interventions target components "determined by the network and ordered according to their associated eigenvalues," reflecting global/local network structure. In the non-symmetric extension of Online Appendix OA3.2 the target components are the left singular vectors of M = I − βG rather than eigenvectors of G. These depend jointly on the network and the strategic parameter β, and the paper does not establish that the singular values of M preserve the complement/substitute monotonicity that Corollary 1 delivers in the symmetric case. The formal targeting machinery extends; the economic narrative that anchors the paper's contribution does not.

- **Assumption 3 is dimensionally incorrect as printed**: The statement "C < ‖b̂‖" is inconsistent with the quadratic budget K(b,b̂) = Σ (b_i − b̂_i)² and fails to exclude the slack-budget corner whenever ‖b̂‖ < 1 (e.

- **Lemma OA1 part 2 contradicts the paper's unit-norm convention**: As printed, u_i^1(G) = √n implies ‖u^1‖² = n², contradicting Fact 1's ‖u^ℓ‖ = 1.

- **Proposition 3's "robustness" framing overstates a reduction driven by Assumption 4**: Assumption 4 assigns infinite cost to any non-deterministic policy, so the optimum collapses to the deterministic problem at E[b̂] by fiat, not by optimization.

- **The abstract's large-budget simplicity claim is not uniform across regimes**: Proposition 2's simplicity bound is proved only for w > 0.

- **OA3.2 prints a spurious squared exponent in the equilibrium formula**: The displayed a̲_ℓ* = (1/s_ℓ)·b_ℓ² is both algebraically wrong (the correct SVD projection is linear in b̲_ℓ) and notationally inconsistent (missing underline).

- **The circle and symmetric-hub illustrations violate Assumption 2**: The 14-node cycle (Figure 1 / Example 3) has six pairs of repeated eigenvalues; the 11-node hub (Figure 2) also has repeated interior eigenvalues, yet the text asserts that Figure 2 satisfies Assumption 2.

- **Sign of b̂_1 in Proposition 1 Part 2**: when b̂_1 < 0 the cosine similarity limit is −1, not +1; the proposition needs an absolute-value framing or a sign assumption.

- **OA3.1 welfare-weight swap**: the printed (w_1, w_2) appear to invert the roles of m_4 and m_5 relative to the standard expansion of Σ_i (Σ_{j≠i} a_j)².

- **OA3.1 scope**: the extension "beyond Property A" still requires the constant-row-sum condition OA1, which excludes most empirical networks with heterogeneous degree.

- **Proposition 4 cost symmetry**: the orthogonal-rotation proof relies on Assumption 5's rotational invariance of the cost; under anisotropic costs the monotonicity breaks.

- **Cost curvature as co-factor**: the principal-component characterization is driven jointly by the quadratic cost and welfare; the paper's own OA3.

- **OA3.4 subsidy cost**: an extra outer 1/2 on the y_i > 0 branch would give (1/4)Σ y_i² rather than the stated (1/2)Σ y_i².

- **Lemma OA2 denominator**: b̂_1² appears inside a sum indexed by ℓ ≥ 2 where b̂_ℓ² is required.

- **Theorem OA1 strict ordering**: |x_2*| > … > |x_n*| cannot hold on the w_1 = 0 branch where all non-leading x_ℓ* vanish.

- **OA3.3 cost family**: calling c, c' "arbitrary" admits negative-cost counterexamples; a parameter restriction is required.

## Detailed Comments (17)

### 1. Theorem 1 silently requires a genericity condition on the status quo

**Refined claim.** Theorem 1's closed-form characterization via the similarity ratio r_ℓ* relies on the unstated hypothesis that b̂_ℓ ≠ 0 for every principal component ℓ. Without it, the variable change x_ℓ = y_ℓ/b̂_ℓ used throughout the proof is undefined (0/0), and the KKT step ruling out μ = w·α_ℓ (which divides by 2·b̂_ℓ²·w·α_ℓ) collapses. The zero-loading case is not pathological — it arises naturally whenever the status quo exhibits the same symmetries as the network (regular, bipartite, and cycle graphs with uniform b̂ all produce zero projections onto some eigenvectors).

**Accepted facts.** Theorem 1's statement lists only Assumptions 1–3 and Property A; the proof in Appendix A explicitly writes "We take a generic b̂ such that b̲̂_ℓ ≠ 0 for all ℓ" and uses this to define the transformed decision variable. The underlying principal-component program (IT-PC) remains well-posed when some b̲̂_ℓ = 0; only the r_ℓ* formalism breaks.

**Constructive fix.** Either (a) add "b̲̂_ℓ ≠ 0 for all ℓ" as an explicit hypothesis of Theorem 1 and Proposition 1, or (b) supply a boundary lemma showing from the Lagrangian of (IT-PC) that the optimum places zero mass on components with b̲̂_ℓ = 0, thereby extending the characterization by limit without ever evaluating r_ℓ*.

It would be helpful to either (a) add "b̲̂_ℓ ≠ 0 for all ℓ" as an explicit hypothesis of Theorem 1 and Proposition 1, or (b) supply a boundary lemma showing from the Lagrangian of (IT-PC) that the optimum places zero mass on components with b̲̂_ℓ = 0, thereby extending the characterization by limit without ever evaluating r_ℓ*..

### 2. The non-symmetric extension loses the paper's headline economic interpretation

**Refined claim.** The abstract asserts that optimal interventions target components "determined by the network and ordered according to their associated eigenvalues," reflecting global/local network structure. In the non-symmetric extension of Online Appendix OA3.2 the target components are the left singular vectors of M = I − βG rather than eigenvectors of G. These depend jointly on the network and the strategic parameter β, and the paper does not establish that the singular values of M preserve the complement/substitute monotonicity that Corollary 1 delivers in the symmetric case. The formal targeting machinery extends; the economic narrative that anchors the paper's contribution does not.

**Accepted facts.** The SVD diagonalization of the planner's objective is correct, so Theorem 1's formalism survives. The paper itself notes in OA3.2 that "the singular values s_ℓ of M are not equal to 1 − βλ_ℓ" and that the left and right singular vectors differ. The global/local interpretation and the eigenvalue-based ordering of Corollary 1 are never re-derived for the non-symmetric case.

**Constructive fix.** Qualify the abstract and the introduction so that the "network-determined, eigenvalue-ordered" framing is explicitly scoped to symmetric networks. In OA3.2, state clearly that while the decomposition method extends, (i) the target components depend on β as well as G and (ii) no analogue of Corollary 1's monotonicity is established.

It would be helpful to qualify the abstract and the introduction so that the "network-determined, eigenvalue-ordered" framing is explicitly scoped to symmetric networks. In OA3.2, state clearly that while the decomposition method extends, (i) the target components depend on β as well as G and (ii) no analogue of Corollary 1's monotonicity is established..

### 3. Assumption 3 is dimensionally incorrect as printed

The statement "C < ‖b̂‖" is inconsistent with the quadratic budget K(b,b̂) = Σ (b_i − b̂_i)² and fails to exclude the slack-budget corner whenever ‖b̂‖ < 1 (e.g., b̂ = 0.5, C = 0.3 admits the bliss point at cost 0.25). The proof in Appendix A and the motivating paragraph in Section 4 both use the correct ‖b̂‖².

It would be helpful to replace "‖b̂‖" with "‖b̂‖²" in Assumption 3, and correct the parallel prose gloss in Section 4.2.

### 4. Lemma OA1 part 2 contradicts the paper's unit-norm convention

As printed, u_i^1(G) = √n implies ‖u^1‖² = n², contradicting Fact 1's ‖u^ℓ‖ = 1. Part 3 of the same lemma (the identity Σ_i a_i* = (√n/(1−β))·b̲_1) arithmetically requires u_i^1 = 1/√n, confirming the typo.

It would be helpful to change √n to 1/√n.

### 5. Proposition 3's "robustness" framing overstates a reduction driven by Assumption 4

Assumption 4 assigns infinite cost to any non-deterministic policy, so the optimum collapses to the deterministic problem at E[b̂] by fiat, not by optimization. The paper's claim that implementation does not require knowing b̂ refers accurately to the ex-post realization, but computing the policy still requires full ex-ante knowledge of E[b̂].

It would be helpful to add a clarifying sentence after Proposition 3 scoping the result to deterministic, non-state-contingent instruments and noting the ex-ante distributional requirement.

### 6. The abstract's large-budget simplicity claim is not uniform across regimes

Proposition 2's simplicity bound is proved only for w > 0. In the w < 0 first-best regime (C ≥ ‖b̂‖², e.g., the local-public-good Example 2), the optimum is y = −b̂, which depends on the status quo and is not generally a single principal component. The paper's body correctly carves out this case in Section 4; the over-compression lives in the abstract and introduction.

It would be helpful to qualify those framings to the non-trivial regime.

### 7. OA3.2 prints a spurious squared exponent in the equilibrium formula

The displayed a̲_ℓ* = (1/s_ℓ)·b_ℓ² is both algebraically wrong (the correct SVD projection is linear in b̲_ℓ) and notationally inconsistent (missing underline). The surrounding text's definition α_ℓ = 1/s_ℓ² and its appeal to Theorem 1 require the linear form.

It would be helpful to print a̲_ℓ* = (1/s_ℓ)·b̲_ℓ.

### 8. The circle and symmetric-hub illustrations violate Assumption 2

The 14-node cycle (Figure 1 / Example 3) has six pairs of repeated eigenvalues; the 11-node hub (Figure 2) also has repeated interior eigenvalues, yet the text asserts that Figure 2 satisfies Assumption 2. The formal theorems are protected by their explicit scoping and the extreme eigenvectors used for the large-budget limit in Figure 2 remain simple, but the un-caveated illustration obscures how the theory applies to the symmetric networks most common in applications.

It would be helpful to correct the false claim about Figure 2 and footnote Example 3 to acknowledge the basis-dependence of the interior components.

### 9. Sign of b̂_1 in Proposition 1 Part 2

when b̂_1 < 0 the cosine similarity limit is −1, not +1; the proposition needs an absolute-value framing or a sign assumption

### 10. OA3.1 welfare-weight swap

the printed (w_1, w_2) appear to invert the roles of m_4 and m_5 relative to the standard expansion of Σ_i (Σ_{j≠i} a_j)²

### 11. OA3.1 scope

the extension "beyond Property A" still requires the constant-row-sum condition OA1, which excludes most empirical networks with heterogeneous degree

### 12. Proposition 4 cost symmetry

the orthogonal-rotation proof relies on Assumption 5's rotational invariance of the cost; under anisotropic costs the monotonicity breaks

### 13. Cost curvature as co-factor

the principal-component characterization is driven jointly by the quadratic cost and welfare; the paper's own OA3.3 shows that linear separable costs produce single-node ("welfare centrality") targeting

### 14. OA3.4 subsidy cost

an extra outer 1/2 on the y_i > 0 branch would give (1/4)Σ y_i² rather than the stated (1/2)Σ y_i²

### 15. Lemma OA2 denominator

b̂_1² appears inside a sum indexed by ℓ ≥ 2 where b̂_ℓ² is required

### 16. Theorem OA1 strict ordering

|x_2*| > … > |x_n*| cannot hold on the w_1 = 0 branch where all non-leading x_ℓ* vanish

### 17. OA3.3 cost family

calling c, c' "arbitrary" admits negative-cost counterexamples; a parameter restriction is required.

Remaining below-cutoff items (merged_012, 015–018, 021, 024, 025) are localized typographical or notational slips. A further 16 raw findings from the discovery phase were triaged at the ordinatio stage as singleton low/medium-confidence presentation-only concerns, self-retracted findings, or OCR artifacts; they are itemized in [[../_artifacts/json/triage|triage.json]]
