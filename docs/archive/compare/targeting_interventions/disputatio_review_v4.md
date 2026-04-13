# Targeting Interventions in Networks

**Date**: 2026-04-12
**Domain**: social_sciences/economics

---

## Overall Feedback

**Central Claim**

This paper studies optimal budget-constrained intervention in linear-quadratic network games, in which a utilitarian planner changes individuals' standalone marginal returns subject to a quadratic budget on the shift. By decomposing the intervention into the principal components (eigenvectors) of the symmetric interaction matrix, the authors obtain a separable characterization of the optimal policy in the spectral basis. The central result (Theorem 1) expresses the optimal intervention as a weighted sum of principal components, with weights organized by a similarity ratio $r_\ell^*$ that trades off the network amplification factor $\alpha_\ell$ against the status-quo loading $\hat{\underline{b}}_\ell$ on each component. Under strategic complements, weight concentrates on the top eigenvector (eigenvector centrality); under substitutes, on the bottom. A companion large-budget result (Proposition 2) shows that interventions become 'simple', converging to a single principal component as the budget grows. A final section extends the mean characterization to partial information settings, decomposing welfare into mean-shift and variance-control channels.

**Main Areas for Reflection**

- **Theorem 1 silently requires a genericity condition $\hat{\underline{b}}_\ell \neq 0$ for every principal component; the proof divides by $\hat{\underline{b}}_\ell$ but the statement does not flag this, so the closed form is undefined on a non-negligible set of status quos.**

- **The abstract's 'components determined by the network, ordered by eigenvalues' framing does not survive the paper's own SVD extension to non-symmetric networks, where the target components depend jointly on $\bm{G}$ and $\beta$ and no analogue of the Corollary 1 monotonicity is established.**

- **Assumption 3's non-triviality cutoff is printed as $C < \|\hat{\bm{b}}\|$ but dimensional analysis and the proof of Theorem 1 both require $C < \|\hat{\bm{b}}\|^2$; a concrete $n=1$ counterexample shows that Theorem 1's proof is invalid under the printed cutoff.**

- **Lemma OA1 part 2 prints $u_i^1(\bm{G}) = \sqrt{n}$ but the unit-norm convention (Fact 1) and the lemma's own part 3 both require $1/\sqrt{n}$.**

- **Proposition 3's 'robustness to uncertainty' is driven by Assumption 4's restriction to deterministic shifts ($K = \infty$ for all stochastic policies); under this feasibility restriction the result is an accounting identity, not an optimization finding.**

- **Proposition 2's simplicity bound is proved only for $w > 0$; the abstract's unconditional simplicity claim silently excludes Example 2 (local public goods, $w = -1$), where the first-best intervention $y = -\hat{\bm{b}}$ is not a single principal component.**

- **Online Appendix OA3.2 prints the non-symmetric equilibrium formula as $\underline{a}_\ell^* = (1/s_\ell)\,b_\ell^2$; the SVD algebra and the surrounding $\alpha_\ell = 1/s_\ell^2$ definition both require $\underline{a}_\ell^* = (1/s_\ell)\,\underline{b}_\ell$ (linear, projected).**

- **The circle (Figure 1 / Example 3) and symmetric-hub (Figure 2) networks used as headline illustrations violate Assumption 2: the 14-node cycle has six pairs of repeated eigenvalues and the hub has repeated interior eigenvalues. The text asserts that Figure 2 satisfies Assumption 2, which is incorrect.**


**Overall Verdict**

The paper's central contribution — a principal-component characterization of optimal network interventions, extended with a mean/variance decomposition under uncertainty — is substantive and survives this review intact on the generic interior of the parameter space. The issues identified below are precise and largely surgical: an explicit genericity hypothesis for Theorem 1, a scoping qualifier on the abstract's 'network-determined, eigenvalue-ordered' framing to separate the symmetric benchmark from the non-symmetric extension, four narrowly-scoped clarifications (Assumption 3's norm exponent, Proposition 3's instrument class, Proposition 2's $w$-regime, the Figure 2 eigenvalue claim), correction of the OA3.2 equilibrium formula, and a careful proofreading pass over the Online Appendix. None of these undermine the main results; together they would strengthen an already important contribution.

## Detailed Comments

### 1. Theorem 1 silently requires a genericity condition on the status quo

Theorem 1 states the proportionality (5) for all principal components $\ell = 1, \ldots, n$ under only Assumptions 1–3 and Property A. Its proof, however, performs the change of variables $x_\ell = (\underline{b}_\ell - \hat{\underline{b}}_\ell)/\hat{\underline{b}}_\ell$, which requires $\hat{\underline{b}}_\ell \neq 0$ for every $\ell$. The proof acknowledges this step: 'We take a generic $\hat{b}$ such that $\underline{\hat{b}}_\ell \neq 0$ for all $\ell$.' The same condition is re-invoked when the KKT argument rules out $\mu = w \alpha_\ell$ by dividing by $2\hat{\underline{b}}_\ell^2 w \alpha_\ell$. Neither the theorem statement nor any corollary records this as a formal hypothesis, and the similarity ratio $r_\ell^* = \rho(\bm{y}^*, \bm{u}^\ell)/\rho(\hat{\bm{b}}, \bm{u}^\ell)$ is genuinely undefined (0/0) when $\hat{\underline{b}}_\ell = 0$. The zero-loading case is not pathological — it arises whenever the status quo inherits symmetries of the network (regular, bipartite, and cycle graphs with a uniform $\hat{\bm{b}}$ all produce zero projections onto some eigenvectors). The substantive consequence is narrower than the gap in statement might suggest: working directly in $y_\ell$ coordinates when $\hat{\underline{b}}_\ell = 0$, the first-order condition becomes $(w\alpha_\ell - \mu) y_\ell = 0$, and since the proof establishes $\mu > w\alpha_\ell$ for all $\ell$ (under the other hypotheses), the optimum places $y_\ell^* = 0$. The formalism breaks but the predicted zero investment agrees with direct optimization by continuity. The fix is one of statement: either add '$\hat{\underline{b}}_\ell \neq 0$ for all $\ell$' to the hypotheses of Theorem 1 (and Proposition 1), or include a boundary lemma deriving $y_\ell^* = 0$ on the zero-loading coordinates directly from the (IT-PC) Lagrangian without appealing to $r_\ell^*$.

### 2. Assumption 3 has a dimensionally inconsistent norm exponent

Assumption 3 is printed as $C < \|\hat{\bm{b}}\|$. The budget constraint $K(\bm{b},\hat{\bm{b}}) = \sum_i (b_i - \hat{b}_i)^2$ has units of (marginal return)$^2$, so an unsquared norm is dimensionally inconsistent. More concretely, a one-node ($n=1$) example with $\hat{b} = 0.5$ and $C = 0.3$ satisfies the printed Assumption 3 (since $0.3 < 0.5$) yet admits the bliss point at cost $(0.5)^2 = 0.25 < 0.3$; the budget is slack at the bliss point, the Lagrange multiplier is zero, and Theorem 1's proof — which explicitly uses $\sum_\ell \hat{\underline{b}}_\ell^2 > C$ at the line immediately following the budget constraint — is invalid. Reading the proof, the paper's motivating paragraph in Section 4, and Proposition 2's statement, the intended cutoff is uniformly $C < \|\hat{\bm{b}}\|^2$. A parallel prose error appears in Section 4.2, where the simplicity bound is described as 'proportional to $\|\hat{\bm{b}}\|$' rather than $\|\hat{\bm{b}}\|^2$. Correcting Assumption 3 and the Section 4.2 prose eliminates the inconsistency and makes the paper's own proof applicable to the case as stated.

### 3. Lemma OA1 part 2 contradicts the unit-norm convention (and itself)

Lemma OA1 part 2 asserts that under the constant-row-sum condition (Assumption OA1), the first eigenvector of $\bm{G}$ satisfies $u_i^1(\bm{G}) = \sqrt{n}$ for all $i$. This cannot hold under the unit-norm convention stated in Fact 1 ($\|\bm{u}^\ell\| = 1$ for all $\ell$), since it would imply $\|\bm{u}^1\|^2 = n \cdot n = n^2$ rather than $1$. The same lemma's part 3 provides an internal check: the identity $\sum_i a_i^* = (\sqrt{n}/(1-\beta)) \cdot \hat{\underline{b}}_1$ is arithmetically consistent only with $u_i^1 = 1/\sqrt{n}$ (so that $\sum_i a_i = \sqrt{n} \cdot \underline{a}_1$, which combined with $\underline{a}_1 = \hat{\underline{b}}_1/(1-\beta)$ gives the stated identity). The lemma thus directly contradicts itself under the printed part 2; this is not a convention choice but a typographical error. Correction: replace $u_i^1(\bm{G}) = \sqrt{n}$ with $u_i^1(\bm{G}) = 1/\sqrt{n}$.

### 4. Proposition 3's 'robustness' is driven by the feasibility restriction, not the optimization

Proposition 3 characterizes the optimal intervention under uncertainty as the same form as in Theorem 1 with the mean $\mathrm{E}[\hat{\bm{b}}]$ in place of $\hat{\bm{b}}$, and the paper summarizes this as robustness of the characterization to uncertainty. The drive of this result is Assumption 4, which assigns cost $K = \sum y_i^2$ only to deterministic mean-shift policies and $K = \infty$ to all stochastic or state-contingent policies. Under this feasibility restriction, the variance channel of welfare (equation (8)) is inert by construction: the planner has no lever on $\mathrm{Var}[\hat{\underline{b}}_\ell]$, and the optimization collapses to the deterministic problem at $\mathrm{E}[\hat{\bm{b}}]$. A state-contingent policy would dominate whenever $\alpha_\ell$ varies across components (which it does whenever the game is non-trivial). The robustness claim therefore describes a property of the deterministic-shift class, not a finding about the global optimum. A related issue is the paper's language on implementation (the optimum 'does not require knowing $\hat{\bm{b}}$'): the result is ex-post in $\hat{\bm{b}}$ but computing $y^*$ via Theorem 1 still requires full ex-ante knowledge of $\mathrm{E}[\hat{\bm{b}}]$. Fix: add a qualifier after Proposition 3 scoping it to deterministic, non-state-contingent instruments and clarifying the ex-ante distributional requirement.

### 5. The large-budget simplicity claim is not uniform across sign regimes of $w$

Proposition 2's simplicity bound — the only formal quantification in the paper of the large-budget simplicity result — is proved under the explicit hypothesis $w > 0$. The abstract and introduction restate the result without this qualifier ('for large budgets, optimal interventions are simple, involving a single principal component'). For $w < 0$ and large budgets (formally $C \geq \|\hat{\bm{b}}\|^2$), the first-best intervention is $\bm{y} = -\hat{\bm{b}}$, which lies in the direction of the status quo and is in general not a single principal component — exactly Example 2 (local public goods, $w = -1$). The body of the paper handles this case correctly by carving it out in Section 4; the issue lives in the abstract and introduction. The proof's bounding argument also depends on $x_\ell^* \geq 0$, which fails for $w < 0$. Fix: insert a qualifier in the abstract and introduction specifying that large-budget simplicity is established in the non-trivial optimization regime (equivalently, when the planner's bliss point is unattainable under the budget), or more tersely 'under strategic complements.' Optionally, a one-paragraph note acknowledging the first-best regime in Section 4.2 would make the scope explicit.

### 6. OA3.2 equilibrium formula has a spurious squared exponent

In Online Appendix OA3.2, after writing the SVD $\bm{M} = \bm{U}\bm{S}\bm{V}^\top$, the paper displays the equilibrium action in the non-symmetric case as $\underline{a}_\ell^* = (1/s_\ell)\,b_\ell^2$. The SVD inversion $\bm{M}\bm{a}^* = \bm{b}$ gives $\bm{V}^\top \bm{a}^* = \bm{S}^{-1}\bm{U}^\top \bm{b}$, which is linear in the projected vector $\underline{\bm{b}}$; the symmetric-case limit must agree with equation (4), which is also linear. The squared form is inconsistent with both. The immediately subsequent text defines $\alpha_\ell = 1/s_\ell^2$ and appeals to Theorem 1 under the substitution $\bm{V} \to \bm{U}$, which requires the objective to be quadratic in $\underline{\bm{b}}$ — a squared $\underline{a}_\ell^*$ would make it quartic. The notation is also inconsistent with the paper's underline convention (bar-b vs. $\underline{b}$). Fix: $\underline{a}_\ell^* = (1/s_\ell)\,\underline{b}_\ell$.

### 7. The non-symmetric SVD extension loses the headline 'network-determined' interpretation

The abstract commits to interventions being determined by principal components 'of the network' and ordered by eigenvalues; OA3.2 extends the formal machinery to non-symmetric $\bm{G}$ by diagonalizing $\bm{M} = \bm{I} - \beta \bm{G}$ via SVD. In the non-symmetric case the target components are the left singular vectors of $\bm{M}$, which depend on $\beta$ (they are generically different from the left and right eigenvectors of $\bm{G}$). The appendix acknowledges this implicitly ('$s_\ell$ are not equal to $1 - \beta \lambda_\ell$') but re-uses the Theorem 1 formalism without checking that the economic interpretation transfers. Two specific consequences: (i) the global/local distinction associated with top vs. bottom eigenvectors of $\bm{G}$ in the main text is not a direct property of singular vectors of $\bm{M}$ — they mix left and right structure, and left and right singular vectors differ when $\bm{G}$ is non-symmetric; (ii) Corollary 1's monotonicity — that higher-eigenvalue components receive larger weight under complements and smaller under substitutes — is re-used via $\alpha_\ell = 1/s_\ell^2$ without proving that singular values of $\bm{M}$ preserve the complement/substitute ordering induced by eigenvalues of $\bm{G}$. The extension delivers a decomposition that diagonalizes the welfare and the budget; it does not, as currently stated, preserve the 'network-determined, eigenvalue-ordered' economic narrative. Fix: in the abstract and the discussion of OA3.2, scope the 'network-determined' framing to the symmetric benchmark, and explicitly note that the SVD extension retains the decomposition but requires $\beta$-dependent singular vectors and does not establish an analogue of Corollary 1.

### 8. Illustrative networks (Figures 1 and 2) violate Assumption 2

Assumption 2 requires distinct non-zero eigenvalues of $\bm{G}$, which is invoked to make Theorem 1's principal-component basis canonically defined. Figure 1 (Example 3) is a 14-node cycle graph; circulant matrices have eigenvalues $2\cos(2\pi k/n)$, yielding six pairs of repeated eigenvalues for $n = 14$. Figure 2 is an 11-node symmetric hub, and its interior eigenvalues are also repeated; the paper asserts that Figure 2 'satisfies Assumption 2,' which is incorrect. For the circle, specific eigenvectors such as $\bm{u}^2(\bm{G})$ and $\bm{u}^{14}(\bm{G})$ are labeled and economically interpreted in the text, but within a repeated eigenspace the choice of basis is arbitrary up to rotation, so these labels are not canonical. The formal theorems are protected by their explicit scoping to Assumption 2, and the extreme eigenvectors invoked for the large-budget limit in Figure 2 remain simple, so the mathematical content is unaffected. The presentation, however, obscures how the theory applies to the symmetric networks (cycles, regular graphs, hubs) that are most common in economic applications. Fix: correct the Figure 2 claim, footnote Example 3 to acknowledge the basis-dependence of the interior components, and consider a separate remark for networks with repeated spectra.

### 9. Proposition 1 Part 2 needs a sign assumption on $\hat{\underline{b}}_1$

The paper's large-budget cosine-similarity result (Proposition 1 Part 2) states that $\rho(\bm{y}^*, \bm{u}^1) \to 1$ as $C \to \infty$. The derivation treats $\hat{\underline{b}}_1$ as positive; if $\hat{\underline{b}}_1 < 0$ the cosine similarity limit is $-1$, not $+1$. The correct statement is $|\rho(\bm{y}^*, \bm{u}^1)| \to 1$, or the proposition should carry a sign assumption on $\hat{\underline{b}}_1$.

### 10. Apparent role-swap of $(w_1, w_2)$ in the OA3.1 welfare-weight expansion

In the Online Appendix OA3.1, the expansion of $W = w(\bm{a}^*)^\top \bm{a}^*$ into the eigen-basis produces coefficients $(w_1, w_2)$ whose printed assignment appears to invert the roles of the standard monomials $m_4$ and $m_5$ that would arise from expanding $\sum_i (\sum_{j \neq i} a_j)^2$. A careful recheck of this expansion against the intended identity is warranted.

### 11. Assumption OA1 (constant row sums) is substantively restrictive

The extension 'beyond Property A' in OA3.1 retains the constant-row-sum condition OA1, which combined with symmetry reduces $\bm{G}$ to doubly stochastic matrices. This condition is more than 'technically convenient': it pins the first eigenvector to be uniform (Lemma OA1 part 2, once corrected) and is what allows the welfare decomposition to be clean. Most empirical interaction networks — those with heterogeneous degree — fall outside this class unless row-normalized, which changes the economic problem. It would help to restate the scope: 'A general characterization without Property A or Assumption OA1 remains open.'

### 12. Proposition 4's proof uses rotational invariance of the cost

The proof of Proposition 4 (variance control under uncertainty) uses an orthogonal change of basis that relies on Assumption 5's rotational invariance of the quadratic cost. Under anisotropic costs (e.g., per-agent heterogeneous cost weights), this invariance fails and the monotonicity claimed by the proposition does not obviously extend. Either Assumption 5 should be listed with Proposition 4's hypotheses, or a note should acknowledge that the result is special to rotationally-invariant cost structures.

### 13. Quadratic cost is load-bearing for the single-PC concentration result

The paper's canonical result — optimal interventions concentrate on a single principal component at large budgets — is driven jointly by the quadratic cost and quadratic welfare, not by network structure alone. The paper's own OA3.3 demonstrates that under linear separable costs the optimum targets a single node ('welfare centrality'), not a principal component. The 'simplicity' narrative should make the cost-curvature dependence explicit, since it materially changes the takeaway for applied work with non-quadratic cost structures.

### 14. OA3.4 subsidy cost has an extra factor

The displayed subsidy-cost term in OA3.4 on the $y_i > 0$ branch appears to carry an extra outer $1/2$, yielding $(1/4)\sum y_i^2$ rather than the intended $(1/2)\sum y_i^2$. This is a factor-of-two transcription error that should be corrected for consistency with the main-text budget.

### 15. Lemma OA2 denominator uses the wrong subscript

The denominator in Lemma OA2 uses $\hat{\underline{b}}_1^2$ inside a sum indexed by $\ell \geq 2$, where the intended expression is $\hat{\underline{b}}_\ell^2$. This appears to be a typographical slip but should be verified and corrected.

### 16. Proposition 2 prose has the wrong-sign denominator for substitutes

The prose gloss of Proposition 2 in Section 4.2 writes the substitutes bound with an $\alpha_{n-1} / (\alpha_{n-1} - \alpha_n)$ term, whose denominator has the wrong sign under the paper's eigenvalue ordering. The formal statement of Proposition 2 correctly uses $\alpha_n - \alpha_{n-1}$.

### 17. 'Proportional to $\|\hat{\bm{b}}\|$' should read $\|\hat{\bm{b}}\|^2$

The Section 4.2 prose describes the Proposition 2 bound as 'proportional to $\|\hat{\bm{b}}\|$'; the bound is proportional to $\|\hat{\bm{b}}\|^2$, consistent with the corrected Assumption 3 cutoff. This is a parallel error to item 2 above and should be fixed in the same pass.

### 18. Theorem OA1 strict ordering cannot hold on the degenerate branch

Theorem OA1 states a strict ordering $|x_2^*| > \ldots > |x_n^*|$. On the $w_1 = 0$ branch, however, all non-leading $x_\ell^*$ vanish, violating strict inequality. The statement should either exclude this branch or relax to $\geq$.

### 19. OA3.3 cost family admits negative-cost functions

OA3.3 refers to 'arbitrary' cost functions $c, c'$ in the single-lever linear-cost extension. Without a parameter restriction (e.g., non-negativity or convexity on a relevant domain), the family admits pathological cost structures for which the claimed targeting result fails. A restriction to non-decreasing, non-negative cost functions — or whatever class the paper actually has in mind — would close the gap.

### 20. Additional transcription and notation slips in the Online Appendix

Beyond the items listed above, the Online Appendix contains further localized transcription errors and notational inconsistencies (merged_012, 015–018, 021, 024, 025 in the internal register): index mismatches, underline omissions on vector symbols, and isolated subscript errors. Individually each is minor; collectively they indicate the appendix would benefit from a dedicated proofreading pass before final publication.
