# Referee Report: Inference in molecular population genetics

**Date**: 2026-04-12
**Domain**: Academic review

---

## Overall Feedback

**Central Assessment**
1. **Standard errors:** State that efficiency claims are validated only in empirically calibrated regions. Complete the GPD diagnostic for xi >= 0.5 and xi >= 1 cases.
2. **NSE data:** Acknowledge model misspecification (structured populations under single-population model) and discuss potential differential bias on IS versus MCMC.
3. **Infinite sites:** Clarify that the implementation is a heuristic adaptation whose success does not directly validate the pi-hat theory for countable-type models.
4. **IS-vs-MCMC:** Revise the abstract to clarify the practical asymmetry. Operationalize the "constrained tree space" criterion. Note that quantitative efficiency gaps on small datasets may narrow with tuned MCMC.
5. **Diagnostics:** Report ESS alongside iteration counts for all empirical examples, especially the NSE data.
6. **Typographical errors:** Correct the type space exponent (3 to 5), equation (33) index (l to s), and Proposition 1(d) proof conclusion (hat{pi} to tilde{pi}).
7. **Scaling:** Add a qualitative discussion of IS weight degeneracy at large n. Temper the Section 6.5 rhetoric to match the small-n evidence.

**Main Issues Identified**

- **Unverified finite-variance assumption undermines SE-based comparisons**: **Rank score: 14/15 | All three agents, six methods | Debate: converged, material**

- **Single-population coalescent applied to structured human populations**: **Rank score: 13/15 | All three agents | Debate: converged, material**

- **Infinite sites implementation departs from theoretical framework**: **Rank score: 11/15 | Gemini + Claude | Debate: converged, material**

- **IS loses to MCMC on the most realistic example**: **Rank score: 13/15 | All three agents, five methods | Debate: converged, local**

- **No formal approximation bound for pi-hat**: **Rank score: 12/15 | All three agents | Debate: converged, local**

- **MCMC benchmarks use flawed estimators and default parameters**: **Rank score: 12/15 | All three agents, seven methods | Debate: converged, local**

- **No scaling analysis despite large-dataset motivation**: **Rank score: 11/15 | Claude + Codex | Debate: converged, local**

- **Asymmetric driving-value analysis**: **Rank score: 10/15 | All three agents | Debate: converged, local**

- **IS advantage in infinite sites linked to finite variance**: The paper attributes IS success in infinite sites to "constrained" tree space:

- **Mutation matrix P assumed, not known**: > "the transition matrix P as known, and focus on inference for theta" (Section 2, p. 5)

- **Efficiency gains are regime-dependent**: > "Our approach substantially outperforms existing IS algorithms, with efficiency typically improved by several orders of magnitude." (Abstract)

- **Type space exponent error**: > "The type space is large (E = {0,1,...,19}^3)" (Section 5.4, p. 22)

- **Equation (33) index error**: The inner sum in equation (33) uses upper limit l (loci) but should use s (quadrature points, s=4):

- **Tautological proof conclusion**: The proof of Proposition 1(d) concludes with a tautology:

- **Proposition 2 assumes finite predecessor support**: The sampling procedure in Proposition 2 step (b) requires enumerating all beta with P_{beta,alpha} > 0:

## Detailed Comments (15)

### 1. Unverified finite-variance assumption undermines SE-based comparisons

**Rank score: 14/15 | All three agents, six methods | Debate: converged, material**

The standard errors in Table 1 and Figures 2-5 assume finite IS weight variance. The paper states this assumption:

> "assuming that the distribution of the weights has finite variance sigma^2, then (by the central limit theorem) the estimator (8) is asymptotically normal with variance sigma^2/M" (Section 5, p. 17)

but later admits it cannot verify it:

> "we could not prove finiteness of the variance of our weights, except in the special case of the infinite sites model where the number of possible histories is finite" (Section 6.4, p. 28)

The violation is empirically confirmed at theta=15, where the SE from 20,000 samples (1.39e-13) underestimates the true standard deviation by more than a factor of 10.

**What debate established:** The defense successfully showed the paper does include a caveat at the point of use: "Despite this important caveat, we quote standard errors..." (Section 5, p. 17). The defense also showed that theta=15 is not a hidden failure -- the paper explicitly uses it as a counterexample where SEs break down. However, the prosecution established two points the defense could not rebut: (1) the GPD diagnostic proposed in Section 6.4 is incomplete, providing no operational guidance when the fitted tail index xi >= 1 indicates infinite variance; (2) there is no systematic criterion for determining when SEs transition from reliable to unreliable across the parameter space.

**Refined claim:** While the paper acknowledges the lack of finite variance guarantees and uses empirical long-run calibrations to justify SEs in specific cases, it lacks a systematic reliability criterion and the GPD diagnostic is incomplete.

**Recommendation:** State that efficiency claims are validated only in empirically calibrated regions. Complete the GPD diagnostic by specifying actions for xi >= 0.5 (infinite variance) and xi >= 1 (infinite mean).

---

### 2. Single-population coalescent applied to structured human populations

**Rank score: 13/15 | All three agents | Debate: converged, material**

The paper commits to a single panmictic population at stationarity:

> "Now consider a random sample of n chromosomes, taken from the population at stationarity." (Section 2, p. 4)

The NSE dataset pools samples from three continents:

> "60 males from Nigeria, Sardinia and East Anglia, each typed at five microsatellite loci on the Y-chromosome" (Section 5.4, p. 21)

This violates the exchangeability assumption without acknowledgment. Extensions to structured populations are discussed in Section 6.2 but no caveat is attached to the NSE results.

**What debate established:** The defense successfully narrowed the paper's intent: the NSE analysis is a computational benchmark, not a biological inference, which nullifies the concern about invalid demographic conclusions. The prosecution conceded this framing. However, the prosecution established that (1) the misspecification is genuinely unacknowledged in Section 5.4 (defense conceded), and (2) unmodeled population structure may differentially penalize the IS proposal distribution compared to MCMC's local moves, potentially confounding the benchmark itself.

**Refined claim:** While the NSE analysis is legitimately framed as a computational benchmark, the paper fails to acknowledge that applying a panmictic model to heavily structured data violates its core exchangeability assumption. The unmodeled structure may differentially bias the IS-vs-MCMC comparison.

**Recommendation:** Add a brief acknowledgment in Section 5.4 that the NSE dataset violates the panmictic assumption, and discuss whether model misspecification might differentially impact IS versus MCMC efficiency.

---

### 3. Infinite sites implementation departs from theoretical framework

**Rank score: 11/15 | Gemini + Claude | Debate: converged, material**

The paper's theoretical arc (Theorem 1, Definition 1, Q^SD) does not extend to infinite sites:

> "for simplicity we adapt our earlier approach to this context by analogy with proposition 2" (Section 5.5, p. 23)

The resulting Q^SD is theta-independent and based on uniform-random chromosome selection:

> "This procedure defines an IS function Q^SD which we note is independent of theta, removing the need to specify a driving value." (Section 5.5, p. 24)

This is the paper's most successful application (Figure 7) yet its theoretical foundation is the weakest.

**What debate established:** The defense successfully showed the paper is transparent about the "analogy" and does not claim false mathematical unity -- refuting the accusation of deception. The defense also correctly noted the paper claims methodological unity (extending the IS framework) rather than strict theoretical unification. However, the prosecution established that (1) the best-performing application is genuinely disconnected from the core theoretical machinery, and (2) the theta-independence is an artifact of the heuristic construction, not a consequence of the general pi-hat theory.

**Refined claim:** The paper's best-performing empirical application is disconnected from its central theoretical contribution. Structural advantages like theta-independence are artifacts of the heuristic construction rather than consequences of the general framework.

**Recommendation:** Clarify that the infinite sites implementation, while inspired by the backward-sampling logic, is a heuristic adaptation whose strong performance does not directly validate the pi-hat approximations for the countable-type case.

---

### 4. IS loses to MCMC on the most realistic example

**Rank score: 13/15 | All three agents, five methods | Debate: converged, local**

The abstract claims IS:

> "compares favourably with existing MCMC methods in some problems, and less favourably in others" (Abstract)

For the NSE data:

> "Further investigation (more runs of each method) suggested that the curve obtained by using micsat is more accurate." (Section 5.4, p. 23)

The paper acknowledges this honestly in Section 6.1:

> "In the one larger and less constrained example that we considered here an MCMC scheme appeared to have an advantage, and we conjecture that this might be typical." (Section 6.1, p. 26)

**What debate established:** The defense refuted the original claim that the NSE result "directly contradicts" the abstract -- it does not, since the abstract explicitly acknowledges "less favourably" cases. The defense also showed Section 6.1 adequately qualifies the reversal. However, the prosecution established a practical asymmetry: IS wins on simulated toy problems but loses on the only real-world dataset. The paper's criterion for "constrained" tree space remains heuristic and loosely defined. The comparison is also confounded by untuned MCMC parameters, smoothing sensitivity, and a single IS driving value.

**Refined claim:** The abstract is accurate but obscures a practical asymmetry between simulated successes and real-world limitations. The "constrained tree space" criterion needs operationalization.

---

### 5. No formal approximation bound for pi-hat

**Rank score: 12/15 | All three agents | Debate: converged, local**

The approximation pi-hat is exact for PIM and for n=1 with reversible P. For the examples used (n=9 to 60):

> "Properties (a), (b) and (d) give grounds for optimism that hat{pi} is a sensible approximation of pi." (Section 4, Remark 1, p. 13)

**What debate established:** The defense successfully argued the paper does not claim formal bounds -- it explicitly relies on empirical validation and ensures the estimator remains consistent regardless of approximation quality (Appendix A: "is a valid IS function in its own right, and so leads to an estimator (9) which is consistent"). This refuted the implicit suggestion that lack of bounds invalidates the practical contribution. However, the prosecution established that for multi-locus models, two unbounded approximations compound (pi-hat for pi, plus Gaussian quadrature with s=4), and the paper omits ESS diagnostics for the NSE dataset where the method underperformed. The defense conceded this omission.

**Refined claim:** The method is valid and consistent, but its efficiency depends on unbounded approximations whose impact is not formally characterized. Reporting ESS is essential but absent for the challenging NSE case.

---

### 6. MCMC benchmarks use flawed estimators and default parameters

**Rank score: 12/15 | All three agents, seven methods | Debate: converged, local**

The Fluctuate comparison uses a fixed-driving-value approach with known infinite variance:

> "In fact Stephens (1999) has recently shown that for theta > 2*theta_0 the estimator has infinite variance." (Section 5.3, p. 20)

The micsat comparison uses untuned parameters:

> "although there are many ways in which our use of the MCMC scheme could be improved (for example, the parameters of the MCMC scheme could be tuned to achieve better mixing over theta; we used the default values)" (Section 5.4, p. 21)

**What debate established:** The defense successfully showed the paper adhered to its stated methodology of using "published general guidelines given by the authors" (Section 5, p. 17) and does not draw a blanket anti-MCMC conclusion -- it explicitly praises parameter-moving MCMC and finds MCMC superior on larger problems. This refuted the claim that handicapped comparisons led to unfairly dismissive conclusions. The prosecution's surviving point: the specific quantitative efficiency advantage on the small simulated dataset is weakened by the stark asymmetry in optimization.

**Refined claim:** The paper's overarching conclusion fairly recognizes complementary strengths, but the quantitative efficiency gap on the small simulated dataset is weakened by asymmetric tuning.

---

### 7. No scaling analysis despite large-dataset motivation

**Rank score: 11/15 | Claude + Codex | Debate: converged, local**

All examples use n <= 60. The discussion invokes large datasets:

> "many real data sets are at or beyond the computational limits of current algorithms. There is thus an urgent need for the continuing development of more efficient inference methods" (Section 6.5, p. 29-30)

**What debate established:** The defense showed the paper explicitly acknowledges its small-n focus and frames the method as a "useful yardstick for comparison" (Section 6.5), not a claim of scalability. This refuted the implication of deception. The prosecution established that the broad motivational rhetoric creates a presentational mismatch with the unproven scalability, and that no complexity analysis or ESS-vs-n characterization is provided.

**Refined claim:** The paper's motivational rhetoric in Section 6.5 risks implying a scalability that is neither theoretically nor empirically supported.

---

### 8. Asymmetric driving-value analysis

**Rank score: 10/15 | All three agents | Debate: converged, local**

Both IS and MCMC share the driving-value peaking vulnerability. The paper analyzes it visually for MCMC (Figure 2(c)) but concedes IS shares it in a single sentence:

> "In principle IS methods based on a driving value of theta will tend to share this undesirable property" (Section 6.1, p. 26)

**What debate established:** The defense showed the paper did not hide the shared vulnerability and had empirical justification for trusting its IS curve in Section 5.3 (a 10-million sample benchmark confirmed the IS surface). The prosecution's link to the theta=15 SE failure in Section 5.2 was cleanly refuted (that section uses matched-theta proposals, not a fixed driving value). The surviving point: the rhetorical asymmetry -- extensive visual analysis for MCMC, single sentence for IS -- risks misleading general readers.

**Refined claim:** The paper's rhetorical presentation is asymmetric, but the underlying empirical evidence supports differential treatment in the specific examples shown.

---

### 9. IS advantage in infinite sites linked to finite variance

The paper attributes IS success in infinite sites to "constrained" tree space:

> "IS methods remain practicable for reasonably large infinite sites data sets, presumably because the space of possible histories is smaller in this context." (Section 5.5, p. 25)

The more precise mechanism is that infinite sites has a finite number of consistent histories, guaranteeing finite IS weight variance -- the only case where the paper proves this holds. The paper's causal interpretation ("constraint leads to IS advantage") may conflate MCMC mixing difficulty with IS weight variance finiteness.

### 10. Mutation matrix P assumed, not known

> "the transition matrix P as known, and focus on inference for theta" (Section 2, p. 5)

For the NSE application:

> "the loci are each assumed to mutate independently at the same rate, theta/2, according to the stepwise model of mutation" (Section 5.4, p. 21)

The stepwise model is one of several competing microsatellite mutation models (two-phase, geometric, proportional slippage). Sensitivity to the choice of P is not investigated.

### 11. Efficiency gains are regime-dependent

> "Our approach substantially outperforms existing IS algorithms, with efficiency typically improved by several orders of magnitude." (Abstract)

At theta=2 (Table 1), Q^GT and Q^SD produce nearly identical estimates with an SE ratio of ~34x -- one order of magnitude, not "several." The massive gains (seven orders) are concentrated at high theta (theta >= 15) where Griffiths-Tavare histories involve huge numbers of superfluous mutations.

### 12. Type space exponent error

> "The type space is large (E = {0,1,...,19}^3)" (Section 5.4, p. 22)

With five loci, the exponent should be 5, not 3. The correct type space has 20^5 = 3.2 million elements.

### 13. Equation (33) index error

The inner sum in equation (33) uses upper limit l (loci) but should use s (quadrature points, s=4):

> "hat{pi}(beta|A_n) = sum_{alpha in A_n} sum_{i=1}^{l}..." (Appendix A, equation (33), p. 30)

### 14. Tautological proof conclusion

The proof of Proposition 1(d) concludes with a tautology:

> "and so hat{pi} = hat{pi}." (Section 4, proof of property (d), p. 14)

Should read "tilde{pi} = hat{pi}" to complete the uniqueness argument.

### 15. Proposition 2 assumes finite predecessor support

The sampling procedure in Proposition 2 step (b) requires enumerating all beta with P_{beta,alpha} > 0:

> "the backward transition probabilities... may be sampled from efficiently" (Section 4, Proposition 2, p. 15)

For dense mutation kernels on countable E, this enumeration may not be finite. All paper examples use finite E or sparse P, so this does not affect the presented results but requires an explicit regularity condition.

---
