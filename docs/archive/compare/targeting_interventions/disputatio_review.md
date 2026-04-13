# Targeting Interventions in Networks

**Date**: 2026-04-11
**Domain**: social_sciences/economics
**Method**: Disputatio (seven-method dialectic debate)

---

## Overall Feedback

**Central Claim**
This paper studies optimal intervention in linear-quadratic network games where a utilitarian planner changes individuals' standalone marginal returns subject to a quadratic budget constraint. By decomposing interventions into the principal components (eigenvectors) of the symmetric adjacency matrix, the authors show that the planner's problem becomes separable across spectral components. The main result (Theorem 1) characterizes the optimal intervention in terms of cosine similarities to principal components, weighted by amplification factors that depend on eigenvalues and the strategic interaction parameter. A key implication is that under strategic complements, interventions concentrate on the top eigenvector (eigenvector centrality), while under strategic substitutes they concentrate on the bottom eigenvector. For large budgets, optimal interventions become "simple" -- proportional to a single principal component.

**Main Areas for Reflection**

- **Gap between Theorem 1's statement and proof regarding genericity of the status quo**

Theorem 1 states the proportionality (5) for "ell = 1, 2, ..., n" -- all principal components -- under only Assumptions 1-3 and Property A. However, the proof in Appendix A performs the change of variables $x_\ell = (\underline{b}_\ell - \hat{\underline{b}}_\ell) / \hat{\underline{b}}_\ell$, which divides by $\hat{\underline{b}}_\ell$ and requires it to be nonzero for every $\ell$. The proof explicitly acknowledges this: "We take a generic $\hat{b}$ such that $\underline{\hat{b}}_\ell \neq 0$ for all $\ell$." But this genericity condition appears nowhere in the theorem statement, and the similarity ratio $r_\ell^* = \rho(\mathbf{y}^*, \mathbf{u}^\ell)/\rho(\hat{\mathbf{b}}, \mathbf{u}^\ell)$ used in Corollary 1 involves $0/0$ when $\hat{\underline{b}}_\ell = 0$.

This is not a knife-edge case. A uniform status quo $\hat{b}_i = c$ for all $i$ on a non-regular network is orthogonal to all eigenvectors except $\mathbf{u}^1$, making $\hat{\underline{b}}_\ell = 0$ for all $\ell \geq 2$. More substantively, when $\hat{\underline{b}}_\ell = 0$ and $w > 0$, the welfare contribution from component $\ell$ is $w \alpha_\ell y_\ell^2$, which is strictly increasing in $|y_\ell|$. The planner benefits from allocating budget to that component, yet the proportionality formula predicts zero investment. The formula gives the wrong answer, not merely an undefined one, at these non-generic points.

It would be helpful to add the genericity condition to Theorem 1's statement, and to provide a separate characterization for the zero-projection case -- either as a remark or as an extension of the theorem that handles all components simultaneously.

- **Property A is substantially more restrictive than the text suggests**

The paper presents Property A ($W = w \cdot (\mathbf{a}^*)^\top \mathbf{a}^*$) as "technically convenient" and claims it "is not essential," citing OA3.1. However, the extension in Theorem OA1 requires Assumption OA1: constant row sums ($\sum_j g_{ij} = 1$ for all $i$), which restricts to doubly stochastic interaction matrices after accounting for symmetry. This excludes networks with heterogeneous degree distributions -- precisely the networks that are most empirically relevant and where spectral methods are most interesting.

Without Property A and without constant row sums, the paper provides no characterization of optimal interventions. Property A forces welfare to be separable across principal components (the squared-action form eliminates all cross-terms). Relaxing it to include linear terms ($w_3 \cdot \sum a_i^*$) or interaction-weighted welfare ($\sum_{i,j} g_{ij} a_i^* a_j^*$) would break the clean diagonal structure that makes Theorem 1 possible. The paper's most natural welfare function for externality-laden games -- one where the planner internalizes the externalities differently from equilibrium -- is not covered.

It would be helpful to restate the scope more precisely: "Property A is sufficient for our sharpest results. The extension in OA3.1 covers games with constant total interaction, but a general characterization for arbitrary externality structures remains open."

- **Large-budget headline results conflict with the papers' own motivating examples**

The paper's most distinctive finding -- that for large budgets, optimal interventions converge to a single principal component (Proposition 1, part 2) -- applies in the regime where the intervention pushes some standalone returns negative, producing negative equilibrium actions. The paper acknowledges this tension in a brief paragraph after Corollary 1: "as long as the status quo actions $\hat{\mathbf{b}}$ are positive, this constraint will be respected for all $C$ less than some $\hat{C}$."

Under strategic substitutes with large $C$, $\mathbf{y}^* \to \sqrt{C} \mathbf{u}^n$, where $\mathbf{u}^n$ has entries of alternating sign. For the local public good example (Example 2), this makes some $b_i$ negative, implying $\tilde{b}_i > \tau$ -- contradicting the model premise that $\tilde{b}_i < \tau$. For the investment game (Example 1) with substitutes, negative $b_i$ means negative standalone marginal returns to effort, which may lack economic meaning. The paper's large-budget asymptotics are most informative precisely in the regime where the unconstrained solution is likely economically infeasible.

It would be helpful to provide explicit bounds on $\hat{C}$ for Examples 1 and 2, or to solve the constrained version with $b_i \geq 0$ and characterize how the large-budget results change when nonnegativity binds.

- **Assumption 3 contains a probable typo that creates an internal inconsistency**

Assumption 3 states "Either $w < 0$ and $C < \|\hat{\mathbf{b}}\|$, or $w > 0$," but the paragraph immediately preceding it derives: "when the budget is large enough, that is, $C \geq \|\hat{\mathbf{b}}\|^2$, the planner can allocate resources to ensure that individuals have a zero target action." The budget constraint is $\sum_i (b_i - \hat{b}_i)^2 \leq C$, so setting $\mathbf{b} = \mathbf{0}$ costs $\|\hat{\mathbf{b}}\|^2$, not $\|\hat{\mathbf{b}}\|$. The assumption as stated fails to exclude the trivial case when $\|\hat{\mathbf{b}}\| > 1$: with $C = 0.8 \|\hat{\mathbf{b}}\|^2$ and $\|\hat{\mathbf{b}}\| = 2$, the assumption reads $C < 2$ but $C = 3.2$, yet the bliss point requires $C \geq 4$. Conversely, when $\|\hat{\mathbf{b}}\| < 1$, the stated condition is too strong. The proof of Theorem 1 in Appendix A uses the correct condition $C < \|\hat{\mathbf{b}}\|^2$.

It would be helpful to publish an erratum correcting $\|\hat{\mathbf{b}}\|$ to $\|\hat{\mathbf{b}}\|^2$ in Assumption 3.

- **The single-PC convergence result is driven by quadratic cost, not by network structure**

The paper's abstract states: "For large budgets, optimal interventions are simple -- they involve a single principal component." This result depends critically on the quadratic cost function $K(\mathbf{b}, \hat{\mathbf{b}}) = \sum_i (b_i - \hat{b}_i)^2$, which is isotropic in the principal component basis (Parseval's theorem). The paper's own OA3.3 shows that under linear cost, the optimal large-budget intervention targets a single individual (Proposition OA3), not a single principal component -- a qualitatively different "simple" form. Under convex costs with faster-than-quadratic growth (e.g., quartic), concentration on one component is penalized and the large-budget limit involves multiple components.

The general-cost extension (Proposition OA1 under Assumption OA2) recovers only the small-budget result: similarity ratios proportional to amplification factors. The large-budget convergence -- the paper's headline finding -- is not established for any cost function other than the quadratic. The main text presents simplicity as flowing from the strategic structure of the game, when in fact the cost functional form is an equally necessary co-factor.

It would be helpful to qualify the simplicity result explicitly: "Under quadratic intervention costs, for large budgets, optimal interventions are simple." Discussing how the result changes under alternative costs would clarify which features are robust and which are artifacts of the specific functional form.

- **The illustrative circle network violates the distinct-eigenvalues assumption**

The 14-node circle network in Example 3 (Figure 1) has eigenvalues $\lambda_k = 2\cos(2\pi k/14)$ for $k = 0, \ldots, 13$. These come in pairs: $\lambda_1 = \lambda_{13}$, $\lambda_2 = \lambda_{12}$, etc. Assumption 2 requires all eigenvalues of $\mathbf{G}$ to be distinct. The eigenvectors shown in Figure 1 are one arbitrary choice within each two-dimensional eigenspace; rotating within the eigenspace produces equally valid "principal components" with different visual patterns. The claim that "the second principal component splits the graph into two sides" is not a statement about a unique mathematical object but about a particular basis choice.

It would be helpful to use a slightly perturbed circle (with non-uniform edge weights) that satisfies Assumption 2, or to note explicitly that the illustration extends by continuity and that any orthonormal basis within each eigenspace gives the same qualitative interpretation.

- **No robustness analysis for network estimation error despite concentration on extreme eigenvectors**

The optimal intervention concentrates on eigenvectors corresponding to extreme eigenvalues -- precisely the eigenvectors most sensitive to perturbations in the adjacency matrix. This is the network analogue of a well-known problem in portfolio theory: the Markowitz mean-variance portfolio concentrates on extreme eigenvectors of the covariance matrix and is notoriously unstable under estimation error. The finance literature addresses this with shrinkage estimators and regularization; no analogous treatment appears here.

Near the stability boundary ($\beta \lambda_1$ close to 1), the amplification factor $\alpha_1 = 1/(1 - \beta \lambda_1)^2$ diverges, and the optimal intervention becomes nearly singular along $\mathbf{u}^1$. A small error in estimating $\beta$ or the spectral radius could push $\beta \lambda_1$ past 1, making the equilibrium non-existent. The paper's recommendation is maximally aggressive precisely where the model is most fragile.

It would be helpful to discuss sensitivity of the optimal intervention to perturbations in $\mathbf{G}$ and $\beta$, and to provide bounds on welfare degradation when eigenvectors are computed from a noisy adjacency matrix.

- **"Global vs. local" interpretation of eigenvectors does not hold for general networks**

The introduction claims that "higher" principal components capture "more global" structure while "lower" ones capture "local" structure. This global-to-local frequency ordering holds for lattice-like topologies (circles, grids) but fails for networks with community structure, where the second eigenvector captures the community partition -- a meso-scale or global property, not a local one. For dense random graphs, the last eigenvector need not produce any meaningful spatial partition, yet the formal results (Corollary 1, Proposition 1) still hold. The interpretive narrative is more restrictive than the formal results it accompanies.

It would be helpful to replace "global/local" with "low-frequency/high-frequency" or to qualify the interpretation as applicable primarily to lattice-like topologies, noting that the amplification ordering (Corollary 1) is valid regardless of whether the global-to-local correspondence holds.

## Detailed Comments (16)

### 1. Theorem 1 proportionality breaks down at non-generic status quo

**Status**: Pending

**Quote**:
> We take a generic $\hat{b}$ such that $\underline{\hat{b}}_\ell \neq 0$ for all $\ell$.

**Feedback**:
The change of variables $x_\ell = (\underline{b}_\ell - \hat{\underline{b}}_\ell)/\hat{\underline{b}}_\ell$ in the proof of Theorem 1 requires $\hat{\underline{b}}_\ell \neq 0$ for all $\ell$, yet this condition is absent from the theorem statement. When $\hat{\underline{b}}_\ell = 0$ for some $\ell$ with $w > 0$, the planner's objective includes $w \alpha_\ell y_\ell^2$, which is strictly increasing in $|y_\ell|$. The optimal $y_\ell^* \neq 0$, contradicting the formula's prediction $\rho(\mathbf{y}^*, \mathbf{u}^\ell) \propto 0$. This is not merely a 0/0 indeterminacy but an incorrect prediction at non-generic points. Add the genericity condition to the theorem statement and provide the characterization for the zero-projection case.

---

### 2. Property A presented as non-essential despite being load-bearing

**Status**: Pending

**Quote**:
> While Property A facilitates analysis, it is not essential. Online Appendix Section OA3.1 extends the analysis to cover important cases where this property does not hold.

**Feedback**:
Theorem OA1 requires Assumption OA1 ($\sum_j g_{ij} = 1$ for all $i$), restricting to constant-degree (doubly stochastic) networks. This excludes star networks, scale-free networks, and most empirical networks with heterogeneous interaction intensity. The claim that Property A is "not essential" overstates the generality of the extensions. Without Property A and without constant row sums, the welfare function has cross-terms across principal components, destroying the separability that enables the clean characterization. Restate the scope of the result honestly.

---

### 3. Large-budget results economically infeasible in motivating examples

**Status**: Pending

**Quote**:
> Note that as long as the status quo actions $\hat{\bm{b}}$ are positive, this constraint will be respected for all $C$ less than some $\hat{C}$, and so our approach will give information about the relative effects on various components for interventions that are not too large.

**Feedback**:
Under strategic substitutes, $\mathbf{y}^* \to \sqrt{C}\,\mathbf{u}^n$, where $\mathbf{u}^n$ has entries of alternating sign. In Example 2, this forces some $b_i < 0$, implying $\tilde{b}_i > \tau$, which contradicts the premise. In Example 1 with $\beta < 0$, large negative interventions on some agents create negative standalone returns to investment. The paper's most prominent asymptotic results are the ones most likely to be economically vacuous. Provide bounds on $\hat{C}$ or solve the constrained problem.

---

### 4. Assumption 3 inconsistent with its own derivation

**Status**: Pending

**Quote**:
> Either $w<0$ and $C<\|\hat{\bm{b}}\|$, or $w>0$.

**Feedback**:
The paragraph before Assumption 3 states: "when the budget is large enough, that is, $C \geq \|\hat{\mathbf{b}}\|^2$." The bliss point costs $\|\hat{\mathbf{b}}\|^2$ (setting $\mathbf{b} = \mathbf{0}$ requires $\sum_i \hat{b}_i^2 \leq C$). The assumption should read $C < \|\hat{\mathbf{b}}\|^2$. When $\|\hat{\mathbf{b}}\| = 0.5$, the stated condition requires $C < 0.5$, but the bliss point is attainable at $C = 0.25$. The proof of Theorem 1 in Appendix A uses the correct squared version ("$\sum_\ell \hat{b}_\ell^2 > C$"). This is either a typo or an OCR artifact that should be corrected.

---

### 5. Quadratic cost is necessary for large-budget simplicity

**Status**: Pending

**Quote**:
> For large budgets, optimal interventions are simple — they involve a single principal component.

**Feedback**:
Under the linear cost function (OA3.3), Proposition OA3 shows the optimal large-budget intervention targets a single individual, not a single principal component. Under Assumption OA2 (general smooth costs), Proposition OA1 recovers only the small-budget characterization. The quadratic cost's isotropy in the eigenbasis -- $\sum_i y_i^2 = \sum_\ell \underline{y}_\ell^2$ by Parseval's theorem -- is what makes the budget constraint spherical in the PC basis and permits the clean separation. Any cost with directional asymmetry (e.g., weighted quadratic $\sum_i w_i y_i^2$ with heterogeneous $w_i$) introduces cross-terms that couple principal components. The simplicity result is a property of the cost-objective interaction, not of network games per se.

---

### 6. Circle network illustration violates Assumption 2

**Status**: Pending

**Quote**:
> Figure 1 depicts six of the eigenvectors/principal components of a circle network with 14 nodes.

**Feedback**:
The 14-node unweighted circle has eigenvalues $\lambda_k = 2\cos(2\pi k/14)$, $k = 0, \ldots, 13$, giving seven distinct values each with multiplicity 2 (except $\lambda_0 = 2$ and $\lambda_7 = -2$). This violates "all eigenvalues of $\mathbf{G}$ are distinct" (Assumption 2). The eigenvectors depicted are an arbitrary choice within each 2D eigenspace. Rotating within the eigenspace of $(\lambda_1, \lambda_{13})$ would produce different "principal components" with different visual patterns. Use a perturbed circle, or state that the result extends to eigenspaces (not individual eigenvectors) by continuity.

---

### 7. Sensitivity to network estimation error and proximity to stability boundary

**Status**: Pending

**Quote**:
> Assumption 2 ensures that (2) is a necessary and sufficient condition for a solution, and also ensures the uniqueness and stability of the Nash equilibrium.

**Feedback**:
When $\beta \lambda_1 = 0.99$, we have $\alpha_1 = 1/(0.01)^2 = 10{,}000$ while $\alpha_2$ may be moderate. The optimal intervention is almost entirely along $\mathbf{u}^1$, but a 2% error in $\beta$ pushes $\beta \lambda_1$ above 1, making the equilibrium non-existent. This is the network analogue of the Markowitz instability: concentration on extreme eigenvectors amplifies estimation error. The paper should at minimum discuss the practical implication that precise knowledge of both $\mathbf{G}$ and $\beta$ is required for the recommendations to be reliable.

---

### 8. Global/local eigenvector interpretation fails for community-structured networks

**Status**: Pending

**Quote**:
> The "higher" principal components capture the more global structure of the network... The "lower" principal components capture the local structure of the network

**Feedback**:
For a network with two dense clusters connected by a bridge, $\mathbf{u}^2$ captures the two-cluster partition -- a global structural feature, not a local one. The monotone global-to-local ordering holds for lattice-like topologies (borrowed from signal processing: low-frequency vs. high-frequency spatial patterns) but has no general guarantee. The formal results (amplification ordering) do not depend on this interpretation, so the narrative should be qualified.

---

### 9. "Complements implies eigenvector centrality" requires Property A, not just strategic structure

**Status**: Pending

**Quote**:
> In games of strategic complements, the optimal intervention is most similar to the first principal component – the familiar eigenvector centrality

**Feedback**:
Under linear welfare $W = w \sum_i a_i^*$, optimal targeting follows Bonacich centrality $[\mathbf{I} - \beta\mathbf{G}]^{-1}\mathbf{1}$, not eigenvector centrality $\mathbf{u}^1$ (as noted by Demange 2017 and discussed in OA2.1). Under Theorem OA1's generalized welfare with $w_3 \neq 0$, the first principal component receives a correction driven by the linear term. The mapping "complements $\to$ eigenvector centrality" is specific to Property A's quadratic welfare form combined with the quadratic cost, not to complementarities alone. The introduction should qualify this.

---

### 10. Proposition 2 bound uninformative for weak interactions and small spectral gaps

**Status**: Pending

**Quote**:
> if $C>\frac{2\|\hat{\bm{b}}\|^{2}}{\epsilon}\left(\frac{\alpha_{2}}{\alpha_{1}-\alpha_{2}}\right)^{2}$, then $W^{*}/W^{s}<1+\epsilon$ and $\rho(\bm{y}^{*},\sqrt{C}\bm{u}^{1})>\sqrt{1-\epsilon}$.

**Feedback**:
For small $\beta$, $\alpha_\ell \approx 1 + 2\beta\lambda_\ell$, so $\alpha_2/(\alpha_1 - \alpha_2) \approx 1/(2\beta(\lambda_1 - \lambda_2))$, which diverges as $\beta \to 0$. With $\beta = 0.001$ and spectral gap 1, the bound requires $C > 500{,}000 \cdot \|\hat{\mathbf{b}}\|^2 / \epsilon$ -- vacuous for any practical budget. Yet when $\beta \to 0$, the game is essentially non-strategic and the optimal intervention simply scales $\hat{\mathbf{b}}$: interventions are trivially "simple." The bound is vacuous in the regime where simplicity is easiest. Additionally, the proof's step replacing $(2\alpha_1 - \alpha_2)/\alpha_1$ with 2 introduces a factor-of-2 looseness that matters most when the spectral gap is small.

---

### 11. SVD extension for directed networks lacks the clean PC interpretation

**Status**: Pending

**Quote**:
> In the Online Appendix we relax these restrictions and develop extensions of our approach to non-symmetric matrices of interaction.

**Feedback**:
For non-symmetric $\mathbf{G}$, the SVD $\mathbf{M} = \mathbf{U}\mathbf{S}\mathbf{V}^\top$ of $\mathbf{M} = \mathbf{I} - \beta\mathbf{G}$ yields left singular vectors ($\mathbf{U}$) and right singular vectors ($\mathbf{V}$) that are generally different. The intervention is decomposed in the $\mathbf{V}$-basis while welfare effects are measured in the $\mathbf{U}$-basis. There is no single basis that simultaneously diagonalizes both the budget constraint and the welfare function. No analogues of Propositions 1-2 are derived for the asymmetric case. The concluding claim of generality should be tempered.

---

### 12. Amplification factor terminology creates systematic ambiguity

**Status**: Pending

**Quote**:
> note that $a_{\ell}^{*} = \sqrt{\alpha_{\ell}} \underline{b}_{\ell}$ is the equilibrium action in the $\ell^{\mathrm{th}}$ principal component of $\boldsymbol{G}$ (see equation (4)).

**Feedback**:
The action amplification factor is $1/(1 - \beta\lambda_\ell) = \sqrt{\alpha_\ell}$, while $\alpha_\ell = 1/(1 - \beta\lambda_\ell)^2$ is the welfare amplification per unit $\underline{b}_\ell^2$. The introduction compounds this by stating "the network multiplier is an eigenvalue of the network" when the multiplier is $1/(1 - \beta\lambda_\ell)$, a function of both $\beta$ and $\lambda_\ell$. Consistently distinguishing "action multiplier" ($\sqrt{\alpha_\ell}$) from "welfare amplification" ($\alpha_\ell$) would prevent confusion about which quantity is being ordered in Corollary 1.

---

### 13. Certainty equivalence result (Proposition 3) is standard and nearly tautological

**Status**: Pending

**Quote**:
> The optimal intervention policy $\mathcal{B}^*$ is equal to $\mathcal{B}_{\boldsymbol{y}^*}$, where $\boldsymbol{y}^*$ is the optimal intervention in the deterministic problem with $\overline{\boldsymbol{b}} = \mathbb{E}[\hat{\boldsymbol{b}}]$ as the status quo vector of standalone marginal returns.

**Feedback**:
Expanding expected welfare: $\mathbb{E}[W] = w \sum_\ell \alpha_\ell \bigl((\mathbb{E}[\hat{\underline{b}}_\ell] + y_\ell)^2 + \text{Var}[\hat{\underline{b}}_\ell]\bigr)$. Since variance terms are $y$-independent, the optimization over $y$ reduces to the deterministic problem at the mean. This is standard certainty equivalence for quadratic objectives with additive uncertainty, requiring no network structure. Assumption 4 further constrains the planner to deterministic shifts, making the result closer to a definitional consequence than a substantive finding. Elevating this to a proposition overstates its novelty.

---

### 14. Proof gap in Proposition 2: inequality $\tilde{x}_1 \geq x_1^*$ asserted without justification

**Status**: Pending

**Quote**:
> $\leq 1 + \frac{\sum_{\ell \neq 1} \hat{b}_{\ell}^{2} \alpha_{\ell} x_{\ell}^{*} (x_{\ell}^{*} + 2)}{\hat{b}_{1}^{2} \alpha_{1} \tilde{x}_{1} (\tilde{x}_{1} + 2) + \sum_{\ell} \alpha_{\ell} \hat{b}_{\ell}^{2}} \quad \text{as } \tilde{x}_{1} \geq x_{1}^{*}$

**Feedback**:
The simple intervention allocates all budget to component 1: $\hat{b}_1^2 \tilde{x}_1^2 = C$. The optimal intervention distributes budget: $\hat{b}_1^2 (x_1^*)^2 + \sum_{\ell > 1} \hat{b}_\ell^2 (x_\ell^*)^2 = C$. Therefore $\hat{b}_1^2 (x_1^*)^2 \leq C = \hat{b}_1^2 \tilde{x}_1^2$, giving $|x_1^*| \leq |\tilde{x}_1|$. Since both are nonnegative ($w > 0$, $\beta > 0$ implies $x_\ell^* \geq 0$), $x_1^* \leq \tilde{x}_1$. This one-line argument should be included. The proof also implicitly requires $\hat{b}_1 \neq 0$ (for $\tilde{x}_1 = \sqrt{C}/\hat{b}_1$ to be defined), which is not stated.

---

### 15. Connectivity (irreducibility) needed for eigenvector centrality identification

**Status**: Pending

**Quote**:
> the optimal intervention is most similar to the first principal component — the familiar eigenvector centrality

**Feedback**:
The Perron-Frobenius theorem guarantees that $\mathbf{u}^1$ is entry-wise positive only when $\mathbf{G}$ is irreducible (the network is connected). Assumptions 1-2 do not imply connectivity. For disconnected networks, $\mathbf{u}^1$ may have zero entries for entire components. OA2.1 assumes "let the network be connected" but the main text makes the eigenvector centrality identification without this qualifier. For two nearly identical components joined by a weak link, $\mathbf{u}^1$ is extremely sensitive to the link weight, making "eigenvector centrality" a fragile guide.

---

### 16. Status quo alignment can dominate network structure for finite budgets

**Status**: Pending

**Quote**:
> the similarity ratio is greater, in absolute value, for the principal components $\ell$ with greater $\alpha_{\ell}$

**Feedback**:
The actual similarity $\rho(\mathbf{y}^*, \mathbf{u}^\ell)$ is proportional to $\rho(\hat{\mathbf{b}}, \mathbf{u}^\ell) \cdot w\alpha_\ell/(\mu - w\alpha_\ell)$, the product of two factors. If $\hat{\mathbf{b}}$ is nearly orthogonal to $\mathbf{u}^1$ and strongly aligned with $\mathbf{u}^2$, then $\rho(\mathbf{y}^*, \mathbf{u}^2) \gg \rho(\mathbf{y}^*, \mathbf{u}^1)$ for any finite budget, despite $\alpha_1 > \alpha_2$. The similarity ratio $r_\ell^*$ normalizes this away, but the actual intervention direction is what matters for policy. The paper's Figures 2B and 2D show this for small budgets but the narrative underemphasizes that practical intervention design requires measuring $\hat{\mathbf{b}}$, which is typically harder to observe than the network.
