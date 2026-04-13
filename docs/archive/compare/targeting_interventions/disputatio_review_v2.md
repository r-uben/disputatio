# Targeting Interventions in Networks

**Date**: 2026-04-11
**Domain**: social_sciences/economics
**Method**: Disputatio (seven-method dialectic debate), v2

---

## Overall Feedback

**Central Claim**
This paper studies optimal intervention in linear-quadratic network games where a utilitarian planner changes individuals' standalone marginal returns subject to a quadratic budget constraint. By decomposing interventions into the principal components (eigenvectors) of the symmetric adjacency matrix, the authors show that the planner's problem becomes separable across spectral components. The main result (Theorem 1) characterizes the optimal intervention in terms of cosine similarities to principal components, weighted by amplification factors that depend on eigenvalues and the strategic interaction parameter. A key implication is that under strategic complements, interventions concentrate on the top eigenvector (eigenvector centrality), while under strategic substitutes they concentrate on the bottom eigenvector. For large budgets, optimal interventions become "simple" -- proportional to a single principal component.

**Main Areas for Reflection**

- **Footnote 14 comparative static on $x_\ell/x_{\ell+1}$ contains a mathematical error**

Footnote 14 claims that "the ratio $x_\ell / x_{\ell+1}$ is increasing (decreasing) in $\beta$ for the case of strategic complements (substitutes)." Consider the small-budget limit $C \to 0$, where $\mu \to \infty$ and $x_\ell^*/x_{\ell+1}^* \to \alpha_\ell/\alpha_{\ell+1}$. Writing this out:

$$\frac{\alpha_\ell}{\alpha_{\ell+1}} = \left(\frac{1-\beta\lambda_{\ell+1}}{1-\beta\lambda_\ell}\right)^2.$$

Let $f(\beta) = (1-\beta\lambda_{\ell+1})/(1-\beta\lambda_\ell)$. Differentiating:

$$f'(\beta) = \frac{\lambda_\ell - \lambda_{\ell+1}}{(1-\beta\lambda_\ell)^2}.$$

Since eigenvalues are ordered $\lambda_\ell > \lambda_{\ell+1}$, the numerator is strictly positive. Under Assumption 2, $(1-\beta\lambda_\ell)^2 > 0$ for all admissible $\beta$. Hence $f'(\beta) > 0$, and since $f(\beta) > 0$ in the admissible region, the derivative of $f(\beta)^2 = \alpha_\ell/\alpha_{\ell+1}$ is $2f(\beta)f'(\beta) > 0$ for all admissible $\beta$ regardless of sign. The ratio is increasing in $\beta$ for both complements and substitutes.

The claim that the ratio is "decreasing in $\beta$" for substitutes appears to conflate monotonicity in $\beta$ with monotonicity in $|\beta|$. When $\beta < 0$, "increasing in $\beta$" means "decreasing in the intensity of substitutability $|\beta|$," which may be the intended economic statement but is not what the footnote says. It would be helpful to correct the comparative static or reformulate it in terms of $|\beta|$.

- **Lagrangian typo in the proof of Theorem 1**

The proof writes the Lagrangian as:

$$\mathcal{L}=w\sum_{\ell}\alpha_{\ell}(1+x_{\ell})^{2}\hat{\underline{b}}_{\ell}+\mu\left[C-\sum_{\ell}\hat{\underline{b}}_{\ell}^{2}x_{\ell}^{2}\right].$$

The objective function defined immediately above this display is $w\sum_\ell \alpha_\ell (1+x_\ell)^2 \hat{\underline{b}}_\ell^2$, with $\hat{\underline{b}}_\ell$ squared. The Lagrangian's first term uses $\hat{\underline{b}}_\ell$ linearly instead of $\hat{\underline{b}}_\ell^2$. This is inconsistent: differentiating the displayed Lagrangian with respect to $x_\ell$ would produce $2w\alpha_\ell(1+x_\ell)\hat{\underline{b}}_\ell$, but the first-order condition on the very next line correctly has $2\hat{\underline{b}}_\ell^2[w\alpha_\ell(1+x_\ell^*) - \mu x_\ell^*]$. The FOC matches the squared version, not the displayed Lagrangian. This is a typographical error that should be corrected for internal consistency.

- **Gap between Theorem 1's statement and proof regarding genericity of the status quo**

Theorem 1 states the proportionality (5) for "$\ell = 1, 2, \ldots, n$" -- all principal components -- under only Assumptions 1-3 and Property A. However, the proof performs the change of variables $x_\ell = (\underline{b}_\ell - \hat{\underline{b}}_\ell) / \hat{\underline{b}}_\ell$, which divides by $\hat{\underline{b}}_\ell$ and requires it to be nonzero for every $\ell$. The proof explicitly acknowledges this: "We take a generic $\hat{b}$ such that $\underline{\hat{b}}_\ell \neq 0$ for all $\ell$." But this genericity condition appears nowhere in the theorem statement, and the similarity ratio $r_\ell^* = \rho(\mathbf{y}^*, \mathbf{u}^\ell)/\rho(\hat{\mathbf{b}}, \mathbf{u}^\ell)$ is undefined (0/0) when $\hat{\underline{b}}_\ell = 0$.

However, the substantive consequence is narrower than it might first appear. Working directly in $y_\ell$ coordinates when $\hat{\underline{b}}_\ell = 0$, the first-order condition becomes $2w\alpha_\ell y_\ell = 2\mu y_\ell$, i.e., $(w\alpha_\ell - \mu)y_\ell = 0$. Since the theorem establishes $\mu > w\alpha_\ell$ for all $\ell$, this forces $y_\ell^* = 0$. The formula's prediction of zero investment in such components is correct -- the planner optimally puts zero budget into directions where the status quo has no loading, because the marginal return to amplifying a nonzero base always dominates starting from zero. The gap is therefore one of statement, not substance: the theorem should carry the genericity condition (or a remark should note that $y_\ell^* = 0$ at non-generic points, consistent with the formula by continuity).

- **Property A is substantially more restrictive than the text suggests**

The paper presents Property A ($W = w \cdot (\mathbf{a}^*)^\top \mathbf{a}^*$) as "technically convenient" and claims it "is not essential," citing OA3.1. However, Theorem OA1 requires Assumption OA1: constant row sums ($\sum_j g_{ij} = 1$ for all $i$), which combined with symmetry (Assumption 1) restricts to doubly stochastic interaction matrices. This structural condition is not merely convenient -- it pins the first eigenvector to be uniform (Lemma OA1), which is what allows the welfare function to decompose cleanly into principal components plus a correction involving only the first component. Without constant row sums, cross-terms between eigenvectors enter the objective, and the first-order conditions become a coupled system.

The claim "not essential" conventionally signals that a condition can be dropped at the cost of complication. In reality, without either Property A or Assumption OA1, the paper provides no characterization. Networks with heterogeneous degree distributions -- the primary motivation for spectral targeting methods -- fall outside both conditions unless row-normalized, which changes the economic problem. It would be helpful to restate the scope: "Property A can be replaced by Assumption OA1 (constant total interaction), which covers additional cases. A general characterization beyond these conditions remains open."

- **Large-budget results require qualification on two fronts**

The paper's most distinctive finding -- that optimal interventions converge to a single principal component as $C \to \infty$ -- requires two qualifications that the presentation underemphasizes.

First, Example 2 (local public good) has $w = -1 < 0$, so Assumption 3 requires $C < \|\hat{\mathbf{b}}\|^2$. The large-budget limit ($C \to \infty$) is therefore formally inapplicable to Example 2. Yet the paper presents Examples 1 and 2 side by side as "two canonical examples" sharing Property A, without flagging that the large-budget results apply only to Example 1 (and similar $w > 0$ games). This exclusion should be stated explicitly near Proposition 1 or in the discussion of Example 2.

Second, even for $w > 0$ games (Example 1 with substitutes), as $C$ grows the intervention $\mathbf{y}^* \to \sqrt{C}\,\mathbf{u}^n$ pushes some standalone returns $b_i$ negative, producing negative equilibrium actions. For the investment game, negative investment is economically meaningless. The paper's one-sentence caveat ("this constraint will be respected for all $C$ less than some $\hat{C}$") acknowledges the issue but never computes $\hat{C}$ for any example, and never checks whether the Proposition 2 budget thresholds exceed $\hat{C}$.

It would be helpful to compute $\hat{C}$ for the examples, or at minimum to note explicitly which of the headline results apply to which examples and in which budget ranges.

- **The single-PC convergence result is driven by quadratic cost, not network structure alone**

The abstract states: "For large budgets, optimal interventions are simple -- they involve a single principal component." This result depends critically on the quadratic cost function $K(\mathbf{b}, \hat{\mathbf{b}}) = \sum_i (b_i - \hat{b}_i)^2$, which is isotropic in the principal component basis by Parseval's theorem. The paper's own OA3.3 shows that under linear cost, the large-budget optimum targets a single individual (Proposition OA3), not a single principal component -- a qualitatively different form of "simplicity." The general-cost extension (Proposition OA1 under Assumption OA2) recovers only the small-budget characterization, not large-budget convergence. Qualifying the simplicity claim as specific to quadratic costs would clarify which features are robust.

---

## Detailed Comments (13)

### 1. Footnote 14 comparative static on $x_\ell/x_{\ell+1}$ is incorrect for substitutes

**Status**: Pending

**Quote**:
> It can be verified that the ratio for every $\ell \in \{1,\dots ,n - 1\}$, $x_{\ell} / x_{\ell +1}$ is increasing (decreasing) in $\beta$ for the case of strategic complements (substitutes)

**Feedback**:
The claim that $x_\ell/x_{\ell+1}$ is decreasing in $\beta$ for substitutes is incorrect. In the small-budget limit, $x_\ell^*/x_{\ell+1}^* \to \alpha_\ell/\alpha_{\ell+1} = ((1-\beta\lambda_{\ell+1})/(1-\beta\lambda_\ell))^2$. Setting $f(\beta) = (1-\beta\lambda_{\ell+1})/(1-\beta\lambda_\ell)$, the derivative $f'(\beta) = (\lambda_\ell - \lambda_{\ell+1})/(1-\beta\lambda_\ell)^2 > 0$ for all admissible $\beta$, since $\lambda_\ell > \lambda_{\ell+1}$ and $(1-\beta\lambda_\ell)^2 > 0$ under Assumption 2. Hence $d/d\beta[f(\beta)^2] = 2f(\beta)f'(\beta) > 0$, and the ratio is strictly increasing in $\beta$ regardless of its sign. By continuity, this extends beyond the small-budget limit for $C$ not too large. The parenthetical "(decreasing)" should be deleted, or the claim should be reformulated in terms of the intensity $|\beta|$.

---

### 2. Lagrangian in proof of Theorem 1 has a typographical error

**Status**: Pending

**Quote**:
> $\mathcal{L}=w\sum_{\ell}\alpha_{\ell}(1+x_{\ell})^{2}\hat{\underline{b}}_{\ell}+\mu\left[C-\sum_{\ell}\hat{\underline{b}}_{\ell}^{2}x_{\ell}^{2}\right]$

**Feedback**:
The first term should read $\hat{\underline{b}}_\ell^2$, not $\hat{\underline{b}}_\ell$. The optimization problem stated immediately above is $\max_x w\sum_\ell \alpha_\ell (1+x_\ell)^2 \hat{\underline{b}}_\ell^2$ subject to $\sum_\ell \hat{\underline{b}}_\ell^2 x_\ell^2 \leq C$. The first-order condition derived on the next line, $2\hat{\underline{b}}_\ell^2[w\alpha_\ell(1+x_\ell^*) - \mu x_\ell^*] = 0$, is consistent with the squared version but not with the displayed Lagrangian. Correct the exponent to remove the internal inconsistency.

---

### 3. Theorem 1 statement should carry genericity condition

**Status**: Pending

**Quote**:
> We take a generic $\hat{b}$ such that $\underline{\hat{b}}_\ell \neq 0$ for all $\ell$.

**Feedback**:
The proof's change of variables $x_\ell = y_\ell/\hat{\underline{b}}_\ell$ requires $\hat{\underline{b}}_\ell \neq 0$ for all $\ell$, yet this condition is absent from Theorem 1's statement. The similarity ratio $r_\ell^* = \rho(\mathbf{y}^*, \mathbf{u}^\ell)/\rho(\hat{\mathbf{b}}, \mathbf{u}^\ell)$ -- the central interpretive quantity in Corollary 1 -- is undefined (0/0) when $\hat{\underline{b}}_\ell = 0$. Working in $y_\ell$ coordinates directly shows $y_\ell^* = 0$ at such points (since $\mu > w\alpha_\ell$), so the formula is substantively correct by continuity, but the theorem as stated has a gap between its claimed scope (all $\ell$) and its proof's scope (generic $\hat{\mathbf{b}}$). Adding "for generic $\hat{\mathbf{b}}$" to the statement, or appending a remark that $y_\ell^* = 0$ when $\hat{\underline{b}}_\ell = 0$, would close this gap.

---

### 4. Property A claim of non-essentiality overstates proven generality

**Status**: Pending

**Quote**:
> While Property A facilitates analysis, it is not essential. Online Appendix Section OA3.1 extends the analysis to cover important cases where this property does not hold.

**Feedback**:
Theorem OA1 requires Assumption OA1 ($\sum_j g_{ij} = 1$ for all $i$), which combined with Assumption 1 (symmetry) yields doubly stochastic matrices. Lemma OA1 shows this pins $\mathbf{u}^1$ to be uniform and $\lambda_1 = 1$, which is structurally necessary for the decomposition -- not merely convenient. Without either Property A or constant row sums, cross-terms between eigenvectors enter the welfare function, and the problem does not decompose. The phrase "not essential" conventionally implies the condition can be dropped; here it must be replaced. Star networks, scale-free networks, and most empirical networks with heterogeneous degree are excluded by both conditions. State explicitly that Property A can be replaced by Assumption OA1 but that a general characterization remains open.

---

### 5. Example 2 is silently excluded from large-budget results by Assumption 3

**Status**: Pending

**Quote**:
> Note that as long as the status quo actions $\hat{\bm{b}}$ are positive, this constraint will be respected for all $C$ less than some $\hat{C}$, and so our approach will give information about the relative effects on various components for interventions that are not too large.

**Feedback**:
Example 2 (local public good) has $W = -(\mathbf{a}^*)^\top \mathbf{a}^*$, so $w = -1 < 0$. Assumption 3 then requires $C < \|\hat{\mathbf{b}}\|^2$, which precludes the $C \to \infty$ limit used in Proposition 1 part 2 and the large-$C$ regime of Proposition 2. The paper never flags this exclusion. A careful reader can deduce it from Assumption 3 (which appears pages earlier), but the presentation of Examples 1 and 2 as "two canonical examples" both satisfying Property A creates the impression that the full suite of results applies to both. Add a remark near Proposition 1 or Example 2 noting that the large-budget analysis requires $w > 0$, which excludes the public-good example.

---

### 6. Assumption 3 has a probable typo: $\|\hat{\mathbf{b}}\|$ should be $\|\hat{\mathbf{b}}\|^2$

**Status**: Pending

**Quote**:
> Either $w<0$ and $C<\|\hat{\bm{b}}\|$, or $w>0$.

**Feedback**:
The paragraph before Assumption 3 derives: "when the budget is large enough, that is, $C \geq \|\hat{\mathbf{b}}\|^2$." The bliss point ($\mathbf{b} = \mathbf{0}$) costs $\sum_i \hat{b}_i^2 = \|\hat{\mathbf{b}}\|^2$. The assumption should read $C < \|\hat{\mathbf{b}}\|^2$. When $\|\hat{\mathbf{b}}\| = 0.5$, the stated condition requires $C < 0.5$, but the bliss point is attainable at $C = 0.25$, leaving the nontrivial range $C \in [0.25, 0.5)$ incorrectly included. The proof of Theorem 1 uses the correct squared version ($\sum_\ell \hat{b}_\ell^2 > C$). Correct $\|\hat{\mathbf{b}}\|$ to $\|\hat{\mathbf{b}}\|^2$.

---

### 7. Quadratic cost is necessary for large-budget simplicity

**Status**: Pending

**Quote**:
> For large budgets, optimal interventions are simple — they involve a single principal component.

**Feedback**:
Under linear cost (OA3.3), Proposition OA3 shows the optimal large-budget intervention targets a single individual, not a single principal component. Under Assumption OA2 (general smooth costs), Proposition OA1 recovers only the small-budget characterization. The quadratic cost's isotropy in the eigenbasis -- $\sum_i y_i^2 = \sum_\ell \underline{y}_\ell^2$ by Parseval's theorem -- is what makes the budget constraint spherical and permits the clean separation. Any cost with directional asymmetry (e.g., weighted quadratic $\sum_i w_i y_i^2$ with heterogeneous $w_i$) couples principal components. The simplicity result is a property of the cost-objective interaction, not of network games per se. Qualify the abstract accordingly.

---

### 8. Circle network illustration violates Assumption 2

**Status**: Pending

**Quote**:
> Figure 1 depicts six of the eigenvectors/principal components of a circle network with 14 nodes.

**Feedback**:
The 14-node unweighted circle has eigenvalues $\lambda_k = 2\cos(2\pi k/14)$, $k = 0, \ldots, 13$, giving seven distinct values each with multiplicity 2 (except $\lambda_0 = 2$ and $\lambda_7 = -2$). This violates "all eigenvalues of $\mathbf{G}$ are distinct" (Assumption 2). The eigenvectors depicted are an arbitrary choice within each 2D eigenspace; rotating within the eigenspace of $(\lambda_1, \lambda_{13})$ would produce different "principal components" with different visual patterns. Use a perturbed circle to satisfy Assumption 2, or note explicitly that the illustration extends by continuity and any orthonormal basis within each eigenspace gives the same qualitative interpretation.

---

### 9. Sensitivity to network estimation error unaddressed despite spectral concentration

**Status**: Pending

**Quote**:
> Assumption 2 ensures that (2) is a necessary and sufficient condition for a solution, and also ensures the uniqueness and stability of the Nash equilibrium.

**Feedback**:
When $\beta \lambda_1 = 0.99$, the amplification factor is $\alpha_1 = 1/(0.01)^2 = 10{,}000$ while $\alpha_2$ may be moderate. The optimal intervention is almost entirely along $\mathbf{u}^1$, but a 2% error in $\beta$ pushes $\beta \lambda_1$ above 1, making the equilibrium non-existent. This is the network analogue of the Markowitz instability in portfolio theory: concentration on extreme eigenvectors amplifies estimation error. The paper recommends maximally aggressive targeting precisely where the model is most fragile. At minimum, discuss sensitivity to perturbations in $\mathbf{G}$ and $\beta$, and note that precise knowledge of both is required for the recommendations to be reliable.

---

### 10. Global/local eigenvector interpretation fails for general networks

**Status**: Pending

**Quote**:
> The "higher" principal components capture the more global structure of the network... The "lower" principal components capture the local structure of the network

**Feedback**:
For a network with two dense clusters connected by a bridge, $\mathbf{u}^2$ captures the community partition -- a global structural feature, not a local one. The monotone global-to-local frequency ordering holds for lattice-like topologies (circles, grids) but has no general guarantee. The formal results (amplification ordering in Corollary 1) do not depend on this interpretation. Replace "global/local" with "low-frequency/high-frequency" or qualify the interpretation as applicable primarily to lattice-like topologies.

---

### 11. "Complements implies eigenvector centrality" requires Property A, not just strategic structure

**Status**: Pending

**Quote**:
> In games of strategic complements, the optimal intervention is most similar to the first principal component – the familiar eigenvector centrality

**Feedback**:
Under linear welfare $W = w \sum_i a_i^*$, optimal targeting follows Bonacich centrality $[\mathbf{I} - \beta\mathbf{G}]^{-1}\mathbf{1}$, not eigenvector centrality $\mathbf{u}^1$ (as noted by Demange 2017 and in OA2.1). Under Theorem OA1 with $w_3 \neq 0$, the first principal component receives a correction driven by the linear welfare term. The mapping "complements $\to$ eigenvector centrality" holds under the conjunction of strategic complements, Property A, and quadratic cost -- not from complementarities alone. The introduction should qualify this.

---

### 12. Proposition 2 bound vacuous for weak interactions and small spectral gaps

**Status**: Pending

**Quote**:
> if $C>\frac{2\|\hat{\bm{b}}\|^{2}}{\epsilon}\left(\frac{\alpha_{2}}{\alpha_{1}-\alpha_{2}}\right)^{2}$, then $W^{*}/W^{s}<1+\epsilon$ and $\rho(\bm{y}^{*},\sqrt{C}\bm{u}^{1})>\sqrt{1-\epsilon}$.

**Feedback**:
For small $\beta$, $\alpha_\ell \approx 1 + 2\beta\lambda_\ell$, so $\alpha_2/(\alpha_1 - \alpha_2) \approx 1/(2\beta(\lambda_1 - \lambda_2))$, which diverges as $\beta \to 0$. With $\beta = 0.001$ and spectral gap 1, the bound requires $C > 500{,}000 \cdot \|\hat{\mathbf{b}}\|^2 / \epsilon$ -- vacuous for any practical budget. Yet when $\beta \to 0$, the game is essentially non-strategic and optimal intervention simply scales $\hat{\mathbf{b}}$: interventions are trivially "simple." The bound is vacuous in the regime where simplicity is easiest. For community-structured networks with near-degenerate top eigenvalues, the bound is also astronomical. Discuss the regime where Proposition 2 is informative vs. where it is not.

---

### 13. Proof gap in Proposition 2: $\tilde{x}_1 \geq x_1^*$ asserted without justification

**Status**: Pending

**Quote**:
> $\leq 1 + \frac{\sum_{\ell \neq 1} \hat{b}_{\ell}^{2} \alpha_{\ell} x_{\ell}^{*} (x_{\ell}^{*} + 2)}{\hat{b}_{1}^{2} \alpha_{1} \tilde{x}_{1} (\tilde{x}_{1} + 2) + \sum_{\ell} \alpha_{\ell} \hat{b}_{\ell}^{2}} \quad \text{as } \tilde{x}_{1} \geq x_{1}^{*}$

**Feedback**:
The one-line argument: the simple intervention allocates all budget to component 1, giving $\hat{b}_1^2 \tilde{x}_1^2 = C$. The optimal intervention distributes budget: $\hat{b}_1^2 (x_1^*)^2 + \sum_{\ell > 1} \hat{b}_\ell^2 (x_\ell^*)^2 = C$. Therefore $\hat{b}_1^2 (x_1^*)^2 \leq C = \hat{b}_1^2 \tilde{x}_1^2$, giving $|x_1^*| \leq |\tilde{x}_1|$. Since both are nonnegative under $w > 0$ and $\beta > 0$, we have $x_1^* \leq \tilde{x}_1$. Including this argument would fill the gap. The proof also implicitly requires $\hat{b}_1 \neq 0$ for $\tilde{x}_1 = \sqrt{C}/\hat{b}_1$ to be defined.
