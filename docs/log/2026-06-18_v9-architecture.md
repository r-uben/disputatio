# v9 architecture decision — consolidate the sprawl, add the argument graph as a targeter

**Issue:** #53 · **Branch:** `feat/53-refine-benchmark` · **Date:** 2026-06-18

Synthesises the 2026-06-17/18 working session into one target architecture. Inputs: the canonical pipeline map (`docs/pipeline-map.md`, consilium-reviewed, 8 spec-drift items), the Codex consolidation verdict (session 407), and the validated argument-graph experiment (`experiments/argument-graph/RESULTS.md`). This is the spine the rebuild is measured against; when it conflicts with SKILL.md, SKILL.md gets patched toward this, not the reverse.

## Goal (unchanged)

Beat the refine.ink benchmark (maximise unique VERIFIED, paper-grounded residual concerns — 28.1 / load-bearing 1.76 — at low overclaim), at a fraction of €50/paper via a big+small model mix, fully open.

## The problem this fixes

The pipeline sprawled across v6→v8.3 into 18 phases: **5 separate evidentiary calibrators** (3g/3v/3s/3e/5a), **4 opt-in audit tracks** (1.5/2.5/2.6/2.7) each a 3-substage triage→audit→integrate, and **8 internal spec contradictions**. Codex's verdict: *"a mistake as architecture, not as diagnosis"* — the blind spots are real, the implementation is accreted complexity. The edge that beats Refine is cross-architecture discovery + hard evidence anchoring + benchmark-aware narrowing + targeted red-teaming, not phase count.

## Decisions

### D1 — Collapse the 5 calibrators into ONE contract-parameterized node
`3g/3v/3s/3e/5a` → a single `evidence_contract_calibrate(claim_type)`. All five share the same skeleton (locate anchor, verify quote, test support, reject hallucination, assign severity, emit-or-drop). What is genuinely per-contract — gap (evidence-of-absence + satisfaction precheck), validity (present-object-wrong + minimal witness), framing (narrative surface + caveat handling), exposition (constructive fix + anti-pedantry), quote-supported (overclaim disposition) — survives as **contract-specific checklists inside the one calibrator**, not as five pipeline phases. Lost: a little per-rubric tuning ease. Worth it: five orchestration branches and five drift surfaces collapse to one.

### D2 — Fold the 4 audit tracks' orchestration into discovery, PRESERVING their detection checks
The v8 tracks exist because single-pass discovery under-detects absences (1.5), wrong-but-present errors (2.5), and framing overreach (2.6). Keep the *detection logic*, drop the separate opt-in DAG branches:
- 1.5 obligations → a `narrow_evidence` sub-task on load-bearing surfaces.
- 2.5 claim-validity → `narrow_evidence`.
- 2.6 scope-framing → `broad_critic` / holistic.
- 2.7 exposition → **cut from default** (pedantry/noise risk, weak on central-result tier) — but this is a *capability cut*, so it is gated on D4, not deleted on a hunch.

Merging plumbing ≠ dropping capability. The obligation/validity/framing checks become discovery sub-tasks; the unified calibrator (D1) adjudicates their output.

### D3 — Add the argument graph as a discovery TARGETER + severity prior (NOT an authority)
Validated on Galeotti: the argument-DAG **dominators predicted 6/7 material findings; raw centrality predicted 0** (`RESULTS.md`). Codex's frame holds: *"NetworkX will be right about the graph; the graph may still be wrong about the paper"* — exact computation on a noisy extracted graph is not exact evidence.
- **Phase 1.25 — argument-graph extraction** (frontier/mid LLM, ≥2 independent extractors for stability, evidence-anchored nodes/edges).
- **Phase 1.3 — graph analysis** (local networkx, ~free): dominators (single points of failure), ordinal heat buckets (NOT raw centrality — fragile on 40-60 node graphs), gap/cycle/disconnect flags as *hypotheses*.
- Outputs **aim** Phase 2 `narrow_evidence` / M8 / obligation search at the dominator + high-bucket nodes, and carry a `graph_prior` into Phase 3 merge as **metadata**.
- **Never** overrides Phase 4 debate or the unified calibrator. Cycles/gaps/framing flags are targeting hypotheses confirmed only by semantic calibration.
- Canvas/Mermaid heatmap = Phase 6 **audit UI**, not proof.
- **Signal = dominators, not centrality.**

### D4 — Measure before you cut (and before you promote)
Capability decisions are gated on the benchmark harness, not priors:
- Cutting 2.7 exposition and downgrading 2.6 framing → confirm they lose head-to-head residual matches before deleting.
- Promoting the argument graph from "targeter" to "core" → requires the result to hold on the **sealed multi-paper benchmark**, not one paper.

### D5 — Fix the 8 spec drifts as a CONSEQUENCE of the rewrite
Do not patch the drifting phases first (several get merged/deleted anyway). Patch SKILL.md once toward this v9 flow; the drifts (debate-execution omission, the 2.5/2.6 false-parallelism, the synth-model contradiction, the undocumented flags, etc.) resolve as a side effect. **Exception:** if anyone runs the current default before v9 lands, fix the two critical items now (debate-execution omission + the dependency lie) per `docs/pipeline-map.md`.

## Target v9 default pipeline

| # | Node | Model tier | Notes |
|---|---|---|---|
| 0 | Init / OCR / preflight | local | socr for PDFs |
| 1 | Orientation (3 maps) | small/local | independent, parallel |
| 2 | Holistic + attack-surface index | frontier/mid | 3 families |
| 3 | **Argument-graph extraction** (1.25) | frontier/mid | ≥2 extractors, evidence-anchored |
| 4 | **Graph analysis** (1.3) | local networkx | dominators + ordinal buckets |
| 5 | Literature-lite (1.75) | capped frontier + web | soft-fail, non-blocking (drop hard /chrome gate) |
| 6 | Discovery bundle (2) | mixed | holistic_candidates (small) · broad+framing (frontier) · narrow+M8+obligations+validity **targeted at graph dominators** (frontier) |
| 7 | Evidence compiler | deterministic/small | substring quote validation |
| 8 | Merge / rank / verify (3) | frontier merge · small retrieval | carry `graph_prior` as metadata |
| 9 | **Unified contract calibration** | small bulk · frontier re-annotator on material/borderline | replaces 3g/3v/3s/3e/5a |
| 10 | Gate + debate (4) | frontier | only material disputed / consensus-override survivors |
| 11 | Finalize (5b) | small | capture surviving_text |
| 12 | Panel + render + Canvas heatmap (6) | small/mid · frontier prose if needed | renderer cannot invent findings |
| — | `_benchmark` harness (dev) | small stages 1-5 · frontier judge · cost ledger | the dual ruler |

Reinvest the budget saved by collapsing phases into `narrow_evidence` + M8 coverage on the graph-flagged load-bearing nodes — not into more calibrator branches.

## Sequencing (order of operations)

1. **This doc** — the target. ✅
2. **Build the benchmark harness + cost ledger** (Phase A) — the ruler everything is measured against.
3. **Safe consolidation** — collapse calibrators (D1), fold track orchestration into discovery preserving checks (D2), wire the graph targeter (D3); patch SKILL.md to v9 (D5 resolves drift).
4. **Honest baseline** (Phase B) — measure the v9 default's verified residual yield + €/paper.
5. **Capability cuts + graph promotion** gated on the data (D4); reinvest in narrow/M8.

## Open questions (non-blocking)

- Graph "core" promotion needs the sealed multi-paper benchmark.
- Direct disputatio-vs-Refine match needs Refine's actual outputs (not released) — else beat the same field by a bigger margin.
- Stability of the argument-graph hot-spots across extractors is unconfirmed (the opus second extraction stalled on iCloud; re-run on a local paper).
