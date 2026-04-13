# Disputatio vs Coarse.ink — Comparison

Benchmark comparison of disputatio (seven-method dialectic debate) against
coarse.ink (multi-agent single-pass review) using coarse's own evaluation
methodology and test papers.

## Test papers

| Paper | Domain | PDF |
|-------|--------|-----|
| targeting_interventions | Economics | Optimal intervention in linear-quadratic network games |
| cortical_circuits | Computational neuroscience | Chaotic balanced state in cortical circuits |
| coset_codes | Information theory | Coset codes — introduction and geometrical classification |
| population_genetics | Population genetics | Inference in molecular population genetics |

All papers, reference reviews, and coarse's reviews sourced from
[Davidvandijcke/coarse](https://github.com/Davidvandijcke/coarse).

## Coarse.ink benchmark scores (Sonnet 4.6 vs refine reference, Gemini 3.1 Pro judge)

| Paper | Overall | Coverage | Specificity | Depth |
|-------|---------|----------|-------------|-------|
| targeting_interventions | 5.83 | 6.0 | 5.5 | 6.0 |
| cortical_circuits | 5.33 | 5.5 | 5.0 | 5.5 |
| coset_codes | 5.50 | 5.5 | 5.0 | 6.0 |
| population_genetics | 5.67 | 6.0 | 5.0 | 6.0 |

Scale: 1-6, where 5.0 = matches human reference review, 5+ = exceeds it.

## Results: targeting_interventions (Claude Opus 4.6 judge)

| Dimension | Disputatio | Coarse (Sonnet 4.6) |
|-----------|-----------|---------------------|
| Coverage | **5.5** | **5.5** |
| Specificity | 5.0 | 5.0 |
| Depth | **5.5** | **5.5** |
| Consistency | 5.0 | 5.0 |
| **Overall** | **5.25** | **5.25** |

**Tie on raw scores.** Both systems exceed the human reference review on coverage and depth while matching it on specificity and consistency.

### What disputatio found that coarse missed
- Assumption 3 mathematical error (||b_hat|| vs ||b_hat||^2)
- Quadratic cost as necessary condition for simplicity (not just convenient)
- Parseval's theorem insight about cost isotropy in eigenbasis
- Circle network violating the paper's own Assumption 2

### What coarse found that disputatio missed
- Footnote 16 comparative static calculation error
- Lagrangian typo in proof of Theorem 1
- Maximizer/minimizer wording slip in substitutes discussion

### What both found independently
- Genericity gap in Theorem 1 (b_hat orthogonal to eigenvector)
- Property A more restrictive than claimed
- Large-budget results economically infeasible (nonnegativity)
- SVD extension for directed networks lacks clean PC interpretation

## Issue-level recall (the real comparison)

Holistic scoring (coverage/depth/specificity) is judge-dependent and fuzzy. Issue-level recall is objective: did the system find this specific, verified problem?

**35 distinct issues identified across all systems. 31 verified against paper text.**

| Metric | Human Reference | Coarse (Sonnet 4.6) | Disputatio v2 |
|--------|----------------|---------------------|---------------|
| Issues found | 8 | 22 | 14 |
| **Recall** (of 31 verified) | 25.8% | **71.0%** | 45.2% |
| **Recall on material issues** (of 6) | 33.3% | 66.7% | **83.3%** |
| **Precision** | 100% | 100% | 100% |
| Unique finds | 3 | 11 | 5 |

**Coarse dominates on total recall** (71% vs 45%) — it reads every line of every proof and catches 11 unique typos/errors in the Online Appendix that disputatio misses entirely.

**Disputatio dominates on material issues** (83% vs 67%) — the multi-method dialectic surfaces conceptual problems that single-pass review misses:
- Example 2 silently excluded from the paper's headline large-budget results
- The simplicity result depends on quadratic cost, not budget size
- "Complements → eigenvector centrality" requires Property A, not just strategic structure

**Only 3 issues found by all three systems.** The systems are highly complementary. A combined pipeline would capture ~94% of all verified issues.

Full analysis: [`targeting_interventions/issue_recall_analysis.md`](targeting_interventions/issue_recall_analysis.md)

### Caveats
- **Judge**: Claude Opus 4.6 (not Gemini 3.1 Pro as in coarse's published benchmarks)
- **Disputatio ran single-model**: Codex and Gemini CLIs failed during orientation (fixed post-run). Discovery used 5 Claude subagents instead of 3 independent models x 5 methods. Cross-agent independence was absent.
- **No debate phase**: Issues were merged and ranked but not put through structured disputation. A full run would stress-test each issue adversarially.
- **First run**: No prompt tuning or iteration. Coarse has been through multiple development phases.

## Evaluation methodology

- **Judge**: Claude Opus 4.6 (subagent, zero API keys)
- **Dimensions**: Coverage, Specificity, Depth, Consistency (1-6 scale)
- **Reference review**: Human expert referee report
- **Coarse's published methodology** (for their benchmarks): Gemini 3.1 Pro judge, positional-bias swap, 3-judge panel with synthesis

## Directory structure

```
compare/
├── README.md
├── judge.py                    # Evaluation script (replicates coarse methodology)
├── adapt.py                    # Format adapter: disputatio → coarse review format
├── <paper>/
│   ├── paper.pdf               # Test paper
│   ├── reference_review.md     # Human referee report
│   ├── reference_review_stanford.md
│   ├── coarse_review.md        # Coarse's best review (phase3)
│   ├── coarse_sonnet46.md      # Coarse's Sonnet 4.6 review
│   ├── coarse_best_score.md    # Coarse's best evaluation score
│   └── disputatio_review.md    # Disputatio's review (after running)
```
