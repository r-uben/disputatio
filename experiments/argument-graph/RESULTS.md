# Argument-graph experiment — results

**Question (issue #53):** Does a paper's *argument dependency DAG* predict where referee concerns land? If yes, the graph is a cheap discovery-targeting + severity-prior substrate (extract once with an LLM, compute structure for ~free with networkx, aim expensive `narrow_evidence` / M8 at the hot-spots).

## Setup

- **Paper:** Galeotti, Golub & Goyal (2020), "Targeting Interventions in Networks" (Econometrica). Chosen because it's network economics, it's SKILL.md's reference paper, and it already has prior disputatio runs as ground truth.
- **Graph:** extracted **blind to the findings** by Codex/gpt-5.5 (`galeotti_graph_codex.json`, 57 nodes / 124 edges). A second Claude/opus extraction (`galeotti_graph_claude.json`) is the stability check.
- **Analysis:** `analyze.py` (dominators + ordinal heat buckets, per the 2026-06-17 Codex review). Report in `galeotti_codex_report.json`.
- **Ground truth:** the `_v71` run's 24 findings (`panel.json`): 7 material, 9 local, 8 nit. NB: this is disputatio's *own* output, a proxy — not independent human referees.

## Headline result

The graph's **dominator** hot-spots coincide with the material findings; raw centrality does not.

| Material finding | Paper object | Dominator? | gates |
|---|---|---|---|
| F003 (proof) — Thm 1 omits a genericity hypothesis | Theorem 1 | ✅ | 22 |
| F001 (framing) — abstract simplicity claim overstated | Proposition 1 | ✅ | **26** |
| F004 (robustness) — simple-intervention budget threshold | Proposition 2 | ✅ | 10 |
| F010 (framing) — variance result leans on Assumption 5 | Proposition 4 | ✅ | 3 |
| F012 (notation) — OA3.1 reparameterization denominator | Prop OA1 / OA3.1 | ✅ | 15 |
| F008 (notation) — Lemma OA1 Perron entries | OA3.1 region | ✅ adjacent | — |
| F005 (robustness) — methodological-contribution framing | headline contribution | (headline) | — |

- **6 / 7 material findings land on dominator nodes** (Theorem 1, Propositions 1/2/4, Prop OA1). The 7th is on the headline contribution.
- **0 / 7 material findings land on the raw-`|ancestors|` "load-bearing" setup nodes** (eq_1, eq_2, principal-component definitions).

## What this confirms (both were Codex's predictions, 2026-06-17)

1. **Dominators are signal.** Directed single-points-of-failure (which proposition/theorem gates the most downstream results) coincide with where the material concerns are. Aiming M8 / `narrow_evidence` at the top ~6 dominator nodes would have targeted Thm 1 and Props 1/2/4 — exactly the material findings.
2. **Raw centrality is theater.** `|ancestors|` just recovers the model setup ("the foundations are foundational"), which attracted zero material findings. The dominator fix (vs undirected cut-vertices) was load-bearing for this result.
3. **Cycles are extraction artifacts.** All 3 detected cycles involve Property A — convention errors in edge direction, not real circular reasoning. Confirmed.

## Caveats (do not over-read)

- **One paper.** This earns "keep as a discovery-targeter" (Codex option b), NOT "make it the v9 core." Core requires the sealed multi-paper benchmark.
- **Proxy ground truth** — disputatio's own findings, not human referees.
- **Stability pending** — result is from one extraction; the Claude/opus second extraction must reproduce the same hot regions (Thm 1 / Props 1,2,4) despite different node wording before we trust it.
- **Source mismatch** — Codex extracted from the arXiv version (local `paper.md` was an iCloud placeholder at run time); the findings reference the Econometrica OCR. Object-level dominators (Thm 1, Props) are source-invariant, so this does not affect the headline, but re-run on the materialized OCR to be clean.

## Verdict

Promote the argument graph to a **discovery-targeting + severity-prior substrate**, not an adjudication authority:
- **Phase 1.25** argument-graph extraction (frontier/mid, ≥2 independent extractors for stability) → **Phase 1.3** graph analysis (cheap, local networkx) → aim Phase 2 `narrow_evidence` / M8 / obligation search at the dominator + high-bucket nodes → carry `graph_prior` into Phase 3 merge as *metadata*. Never let graph metrics override Phase 5 calibration or Phase 4 debate. Canvas heatmap is a Phase 6 audit UI, not proof.
- **Signal = dominators (+ ordinal buckets), not raw centrality.**
- Gate on the sealed multi-paper benchmark before any "core" promotion.
