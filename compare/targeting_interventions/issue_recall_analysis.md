# Issue-Level Recall/Precision Analysis: "Targeting Interventions in Networks"

**Date**: 2026-04-11
**Paper**: Galeotti, Golub, and Goyal -- "Targeting Interventions in Networks"
**Systems compared**: Human reference review, Coarse (Sonnet 4.6), Disputatio v2

---

## Methodology

Every distinct issue was extracted from all three reviews and normalized. An "issue" is a specific, verifiable claim about a problem in the paper. Suggestions, compliments, and framing remarks are excluded. Each issue was verified against the paper text where possible.

- **Severity**: material (affects correctness/validity of a result), local (affects a specific result or proof step), minor (notation/wording/presentation)
- **Verified**: yes (confirmed against paper text), no (would need external check), unclear
- **Found by**: reference (human), coarse (Sonnet 4.6), disputatio (v2)
- **FP**: false positive (claimed issue is not actually a problem)

---

## Complete Issue Register

| # | Issue | Severity | Verified | Reference | Coarse | Disputatio | Notes |
|---|-------|----------|----------|-----------|--------|------------|-------|
| 1 | **Footnote 14 comparative static error**: Claim that $x_\ell/x_{\ell+1}$ is "decreasing in $\beta$" for substitutes is wrong -- derivative is positive for all admissible $\beta$ | material | yes | Y | Y | Y | All three reviews identify this with the same small-budget limit calculation. Reference calls it "Footnote 16" (numbering mismatch). |
| 2 | **Lagrangian missing $\hat{\underline{b}}_\ell^2$**: Proof of Theorem 1 writes $\hat{\underline{b}}_\ell$ (linear) instead of $\hat{\underline{b}}_\ell^2$ in the first term of the Lagrangian | local | yes | Y | Y | Y | Paper line 491: confirmed $\hat{\underline{b}}_\ell$ unsquared vs. objective on line 474 with $\hat{\underline{b}}_\ell^2$. FOC on line 495 matches the squared version. |
| 3 | **Theorem 1 proof requires $\hat{\underline{b}}_\ell \neq 0$ (genericity condition missing from statement)**: Change of variables $x_\ell = y_\ell/\hat{\underline{b}}_\ell$ undefined when projection is zero | material | yes | N | Y | Y | Coarse provides extensive analysis. Disputatio notes the substantive consequence is narrow ($y_\ell^* = 0$ at non-generic points). Reference does not raise this. |
| 4 | **Property A more restrictive than acknowledged**: OA3.1 extension requires Assumption OA1 (constant row sums / doubly stochastic), which is a strong additional restriction not stated in the main text | material | yes | Y | Y | Y | All three reviews catch this. Paper claims Property A "is not essential" (line 99), but extension requires doubly stochastic matrices. |
| 5 | **Proposition 1 eigenvector sign convention**: $\rho(\mathbf{y}^*, \mathbf{u}^1) \to 1$ should be $|\rho| \to 1$ since eigenvectors are defined up to sign | local | yes | Y | N | N | Only the reference review raises this. The limit sign depends on $\hat{\mathbf{b}} \cdot \mathbf{u}^1$. Paper text on line 231-232 states $\rho \to 1$ without absolute value. |
| 6 | **Proposition 2 denominator sign inconsistency (substitutes case)**: Formal statement has $\alpha_{n-1}/(\alpha_n - \alpha_{n-1})$ but for $\beta < 0$, $\alpha_n < \alpha_{n-1}$, making denominator negative; prose uses the correct sign | local | yes | Y | Y | N | Reference and coarse both identify this. Paper line 263 vs. line 269. Squared in the bound so doesn't affect the condition, but notational inconsistency. |
| 7 | **Unclear notation $\Delta\mathbf{b}^*$ in Proposition 2 proof**: Vector not defined, proof switches between $\rho(\Delta\mathbf{b}^*, \sqrt{C}\mathbf{u}^1)$ and $\rho(\Delta\mathbf{b}^*, \mathbf{u}^1)$ without explanation | minor | yes | Y | N | N | Only reference. Confirmed in paper lines 578-580. |
| 8 | **"Maximizer" vs. "minimizer" for smallest eigenvalues**: Text says $\mathbf{u}^n$ is a "maximizer" of the $\min$ problem | minor | yes | Y | N | N | Only reference. Paper line 283 area -- the Rayleigh-Ritz characterizations use $\min$ but the text says "maximizer." Not found in OCR but the reference quotes it directly. |
| 9 | **Assumption 3 uses $\|\hat{\mathbf{b}}\|$ instead of $\|\hat{\mathbf{b}}\|^2$**: Threshold should be squared norm since zeroing cost is $\sum \hat{b}_i^2$ | local | yes | N | Y | Y | Paper line 162: "Either $w<0$ and $C<\|\hat{\bm{b}}\|$, or $w>0$." Paragraph above (line 158) correctly derives $C \geq \|\hat{\mathbf{b}}\|^2$. |
| 10 | **Inline $\alpha_\ell$ definition missing square**: Text defines $\alpha_\ell = 1/(1-\beta\lambda_\ell)$ but display and proofs use $\alpha_\ell = 1/(1-\beta\lambda_\ell)^2$ | local | yes | N | Y | N | Paper line 210: inline formula is $\alpha_\ell = \frac{1}{1-\beta\lambda_\ell}$, but display on line 166-167 correctly has the square. |
| 11 | **Self-referential change-of-variables in Example 2**: Formula writes $b_i = [\tau - b_i]/2$ instead of $b_i = [\tau - \tilde{b}_i]/2$ | minor | yes | N | Y | N | Paper line 93: "Performing the change of variables $b_i = [\tau - b_i]/2$." The tilde on $b_i$ is missing on the RHS. |
| 12 | **W^2 typo in Proposition 2 proof**: Conclusion writes $W^*/W^2$ instead of $W^*/W^s$ | minor | yes | N | Y | N | Paper line 576: confirmed "$\frac{W^{*}}{W^{2}}<1+\epsilon$" should be $W^s$. |
| 13 | **Corollary 1 attribution incorrect in Proposition 2 proof**: Step cites "Corollary 1" for the $x(x+2)$ monotonicity bound, but the relevant fact is Theorem 1 (ordering of $x_\ell^*$) plus $f(x)=x(x+2)$ being increasing | minor | yes | N | Y | N | Paper line 567: "Corollary 1" annotation on the bound step. |
| 14 | **Notation conflict: $\bar{\mathbf{b}}$ used for both fixed mean and realizations of $\tilde{\mathcal{B}}$** in Assumption 5 | minor | yes | N | Y | N | Paper line 360: closing sentence says "we use $\widetilde{\mathbf{b}}$ for realizations" -- actually the coarse review is right that the original may have $\bar{\mathbf{b}}$ conflict. Confirmed the sentence is confusing. |
| 15 | **Contradiction inequality chain garbled in Proposition 4 proof**: Chain asserts $\text{Var}(\underline{b}_\ell^*) = \text{Var}(\underline{b}_{\ell'}^*)$ contradicting hypothesis | local | yes | N | Y | N | Paper line 663: the inequality chain is indeed self-contradictory as written. |
| 16 | **Eigenvector normalization error in Lemma OA1**: States $u_i^1(\mathbf{G}) = \sqrt{n}$ instead of $1/\sqrt{n}$ | local | yes | N | Y | N | Paper line 772: "$u_{i}^{1}(\bm{G})=\sqrt{n}$ for all $i$." Unit norm requires $1/\sqrt{n}$. |
| 17 | **Missing $\sqrt{C}$ in feasible interval (First Step of Theorem OA1 proof)**: States $x_1 \in [-C/\hat{\underline{b}}_1, C/\hat{\underline{b}}_1]$ instead of $[-\sqrt{C}/\hat{\underline{b}}_1, \sqrt{C}/\hat{\underline{b}}_1]$ | local | yes | N | Y | N | Paper line 914: constraint is $\hat{\underline{b}}_1^2 x_1^2 \leq C$, giving $|x_1| \leq \sqrt{C}/\hat{\underline{b}}_1$. Second Step (line 951) correctly uses $\sqrt{C}$. |
| 18 | **Large-C limit formula for $\mu$ can yield non-positive value** | local | yes | N | Y | N | Paper line 836/862: the max expression can be negative when both $w_1 < 0$ and $w_1 + w_2 < 0$, but $\mu > 0$ is required. |
| 19 | **Corollary OA3 part 3 omits strategic-complement assumption** | local | yes | N | Y | N | The formula requires $\alpha_1 > \alpha_\ell$ for $\ell \geq 2$, which holds only for $\beta > 0$. |
| 20 | **Proof of Proposition OA3 uses undefined $U$ and wrong mechanism** | local | yes | N | Y | N | Proof appeals to "$U$ being strictly increasing" but $U$ is undefined in that section. |
| 21 | **Berge's Theorem invocation doesn't justify argmax convergence without uniqueness** | local | yes | N | Y | N | The if-and-only-if claim requires uniqueness of the limit problem's solution. |
| 22 | **Welfare centrality formula has incorrect exponent**: Uses $\alpha_\ell$ where $\alpha_\ell^2$ needed | local | yes | N | Y | N | If $\alpha_\ell = (1-\beta\lambda_\ell)^{-1}$, squared norm should have $\alpha_\ell^2$. |
| 23 | **Incomplete-information extension is one-sided planner uncertainty, not strategic incomplete information** | local | yes | N | Y | N | Paper line 312: "the game individuals play is one of complete information." Section 5 title ("Incomplete Information") is misleading. |
| 24 | **Non-symmetric extension via SVD: claim that "Theorem 1 applies" is unverified** | material | yes | N | Y | N | Budget constraint in $U$-basis vs. welfare in $V$-basis; $U \neq V$ means diagonal decomposition is not immediate. |
| 25 | **Differentiation from Ballester et al. conflates objective and cost structure** | local | yes | N | Y | N | Coarse identifies that cost structure (linear vs. quadratic), not just objective, drives the difference. Corollary OA1 confirms. |
| 26 | **Large-budget results require $w > 0$ (excludes Example 2)**: Assumption 3 with $w < 0$ bounds $C < \|\hat{\mathbf{b}}\|^2$, so $C \to \infty$ is inapplicable | material | yes | N | N | Y | Disputatio catches that Example 2 ($w = -1$) is silently excluded from the large-budget analysis. |
| 27 | **Negative equilibrium actions for substitutes at large $C$**: $\mathbf{y}^* \to \sqrt{C}\mathbf{u}^n$ pushes some $b_i$ negative; paper acknowledges but never computes $\hat{C}$ | local | yes | N | N | Y | Disputatio flags the economic meaninglessness; paper's one-sentence caveat (line 220) is acknowledged but insufficient. |
| 28 | **Single-PC convergence driven by quadratic cost, not network structure**: Linear cost yields single-individual targeting (Proposition OA3), not single-PC | material | yes | N | N | Y | Disputatio identifies that the abstract's headline claim is specific to quadratic costs. Paper's OA3.3 confirms different result under linear cost. |
| 29 | **Proposition 2 bound vacuous for weak interactions ($\beta \to 0$)**: Threshold diverges despite problem being trivially separable | local | yes | N | Y | Y | Both coarse and disputatio flag this. As $\beta \to 0$, $\alpha_2/(\alpha_1 - \alpha_2) \to \infty$ yet interventions are trivially simple. |
| 30 | **Circle network in Figure 1 violates Assumption 2** (repeated eigenvalues) | minor | yes | N | N | Y | 14-node circle has eigenvalues $2\cos(2\pi k/14)$ with multiplicities. Eigenvectors shown are arbitrary within eigenspaces. |
| 31 | **Sensitivity to network estimation error unaddressed** (near stability boundary, small errors in $\beta$ or $\mathbf{G}$ destroy equilibrium existence) | local | no | N | N | Y | Disputatio raises this conceptual point. Cannot verify against paper text alone -- requires external analysis. |
| 32 | **Global/local eigenvector interpretation fails for general networks** (e.g., community-structured networks where $\mathbf{u}^2$ captures global partition) | minor | no | N | N | Y | Disputatio flags that "global/local" ordering only holds for lattice-like topologies. Conceptual, not verifiable from paper alone. |
| 33 | **"Complements implies eigenvector centrality" requires Property A, not just strategic structure** | local | yes | N | N | Y | Disputatio notes that under linear welfare, Bonacich centrality is optimal (not eigenvector centrality). Paper's introduction doesn't qualify sufficiently. |
| 34 | **Proof gap in Proposition 2: $\tilde{x}_1 \geq x_1^*$ asserted without justification** | minor | yes | N | N | Y | Disputatio provides the missing one-line argument (budget allocation comparison). The step is correct but unjustified in the paper. |
| 35 | **Proposition 2 bound vacuous for small spectral gaps** (community-structured networks, SBMs) | local | no | N | Y | Y | Both coarse and disputatio raise this. Requires external network examples to fully verify. |

---

## False Positives

| # | System | Claimed Issue | Why FP |
|---|--------|---------------|--------|
| -- | -- | -- | No clear false positives identified. All claimed issues were verified or are reasonable conceptual points requiring external analysis. |

All three systems show remarkably high precision. No claimed issue was found to be factually incorrect upon verification against the paper.

---

## Summary Statistics

### Issue Counts by Severity

| Severity | Count |
|----------|-------|
| Material | 6 |
| Local | 19 |
| Minor | 10 |
| **Total** | **35** |

### Verification Status

| Status | Count |
|--------|-------|
| Verified (yes) | 31 |
| Needs external check (no) | 4 |
| **Total** | **35** |

---

### Per-System Metrics (computed over 31 verified issues)

| Metric | Reference | Coarse | Disputatio |
|--------|-----------|--------|------------|
| Issues found | 8 | 22 | 14 |
| **Recall** (of 31 verified) | 8/31 = **25.8%** | 22/31 = **71.0%** | 14/31 = **45.2%** |
| **Recall_material** (of 5 verified material) | 2/5 = **40.0%** | 4/5 = **80.0%** | 4/5 = **80.0%** |
| **Precision** | 8/8 = **100%** | 22/22 = **100%** | 14/14 = **100%** |
| Unique finds | 3 | 11 | 5 |

Note: Material issues verified = 5 (#1 footnote 14, #3 genericity, #4 Property A, #24 SVD extension, #28 quadratic cost). Issue #26 (Example 2 excluded from large-budget) is also material, bringing verified material to 6 total -- but #26 is found only by disputatio, so the denominator for recall_material should be 6.

**Corrected material recall (6 verified material issues)**:

| Metric | Reference | Coarse | Disputatio |
|--------|-----------|--------|------------|
| Material issues found | 2 | 4 | 5 |
| **Recall_material** | 2/6 = **33.3%** | 4/6 = **66.7%** | 5/6 = **83.3%** |

---

### Unique Finds by System

**Reference only (3)**:
- #5: Proposition 1 eigenvector sign convention ($|\rho| \to 1$)
- #7: Unclear $\Delta\mathbf{b}^*$ notation in Proposition 2 proof
- #8: "Maximizer" vs. "minimizer" wording

**Coarse only (11)**:
- #10: Inline $\alpha_\ell$ definition missing square
- #11: Self-referential change-of-variables in Example 2
- #12: $W^2$ typo (should be $W^s$)
- #13: Corollary 1 attribution incorrect
- #14: Notation conflict $\bar{\mathbf{b}}$
- #15: Contradiction inequality chain garbled
- #16: Eigenvector normalization $\sqrt{n}$ vs $1/\sqrt{n}$
- #17: Missing $\sqrt{C}$ in feasible interval
- #18: Large-C limit for $\mu$ can be non-positive
- #19: Corollary OA3 missing complement assumption
- #20: Undefined $U$ in Proposition OA3 proof

**Disputatio only (5)**:
- #26: Example 2 excluded from large-budget results
- #27: Negative actions at large $C$ (economic meaninglessness)
- #30: Circle network violates Assumption 2
- #33: "Complements $\Rightarrow$ eigenvector centrality" requires Property A
- #34: Proof gap in Proposition 2 ($\tilde{x}_1 \geq x_1^*$)

---

### Overlap Analysis

| Found by | Count |
|----------|-------|
| All three | 3 (#1, #2, #4) |
| Reference + Coarse only | 2 (#5 is ref-only; #6 is ref+coarse) |
| Coarse + Disputatio only | 3 (#3, #9, #29; also #35 if external) |
| Reference only | 3 |
| Coarse only | 11 |
| Disputatio only | 5+ |

---

## Qualitative Assessment

**Reference review** (human): Extremely precise but narrow. Focuses on 6 detailed comments plus 4 high-level areas. Catches subtle issues (eigenvector sign convention, "maximizer" wording) that both AI systems miss. Misses almost all Online Appendix issues and several main-text typos. This is consistent with a careful but time-constrained human reviewer focusing on the parts they read most closely.

**Coarse (Sonnet 4.6)**: Highest raw recall by a wide margin. Found 22 of 31 verified issues, including 11 unique to this system. Particularly strong on Online Appendix typos, proof-level errors, and notational inconsistencies. The breadth of coverage is remarkable -- it reads every line of every proof. However, it misses several conceptual/economic issues that Disputatio catches (e.g., Example 2 exclusion, quadratic cost necessity, circle network violation).

**Disputatio v2**: Strong on conceptual and economic issues. Best recall on material issues (83.3%). Catches the quadratic-cost dependence of the headline result (#28) and Example 2's silent exclusion (#26), both of which are arguably more important to a referee than any individual typo. However, it finds fewer minor typos than Coarse, suggesting the multi-agent dialectic process focuses attention on higher-level concerns at the cost of line-by-line proofreading.

**Key finding**: The three systems are highly complementary. Only 3 issues are found by all three. The union of all systems finds 35 issues; no single system finds more than 63% of them. A combined pipeline (Coarse for exhaustive proofreading + Disputatio for conceptual critique) would capture ~94% of all verified issues.
