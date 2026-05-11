# Dev log

Dated entries capturing decisions, design pivots, and validation runs as they happened. Useful as the historical record of why the architecture looks the way it does; less useful as a getting-started resource.

For the current architecture, see [`../architecture.md`](../architecture.md). For per-feature design rationales, see [`../design-notes/`](../design-notes/). For the formal pipeline protocol, see [`../../SKILL.md`](../../SKILL.md).

## Index

| Date | Entry | What it captures |
|---|---|---|
| 2026-04-11 | [E2E test + Gemini fix](2026-04-11_e2e-test-gemini-fix.md) | End-to-end smoke test; Gemini transport fix; model routing decisions. |
| 2026-04-13 | [V3 on targeting-interventions](2026-04-13_v3-targeting-interventions-and-eval.md) | First public run; comparison against coarse.ink; public claim update. |
| 2026-04-13 | [Branch cleanup + extension planning](2026-04-13_branch-cleanup-and-extension-planning.md) | `feat/deep-discovery` cleanup; design for multi-provider extension. |
| 2026-04-13 | [Ollama transport validation](2026-04-13_ollama-transport-validation.md) | Validating PR #4's ollama transport end-to-end on coset-codes. |
| 2026-04-14 | [Brutal dialectic redesign](2026-04-14_brutal-dialectic.md) | Tier-1 dialectic restructure. |
| 2026-04-14 | [v5 calibration + baseline + polish](2026-04-14_v5-calibration-baseline-polish.md) | v5 calibration phase, baseline sentinel, polish-rewrite, M5 tightening. |
| 2026-04-14 | [Upstream pivot plan](2026-04-14_upstream-pivot-plan.md) | Pushback on V5; design of the V6 upstream pivot. |
| 2026-04-14 | [v6 upstream pivot](2026-04-14_v6-upstream-pivot.md) | Panel-first product, holistic pass, debate-as-escalation. |
| 2026-04-14 | [v6 positioning + plan](2026-04-14_v6-upstream-positioning-and-plan.md) | Implementation plan for the v6 reshape. |
| 2026-04-17 | [v7 validation + launch plan](2026-04-17_v7-validation-and-launch-plan.md) | v7 validation results; handoff for the next session. |
| 2026-04-27 | [Coarse bench + drop-mini](2026-04-27_coarse-bench-and-drop-mini.md) | Head-to-head against coarse.ink corpus; v7.1 drop-mini ablation. |
| 2026-04-28 | [PR #20 spec reconciliation](2026-04-28_pr20-spec-reconciliation.md) | Codex review of PR #20; five spec-consistency blockers surfaced. |
| 2026-04-29 | [Forney v7.1 validation](2026-04-29_forney-v7-1-validation.md) | First production v7.1 run after the spec reconciliation. |

The bench numbers, comparisons, and claims in these entries are time-stamped snapshots — they reflect what was known when written. Subsequent reframes (notably the description-only public reframe in May 2026) supersede some of the load-bearing claims in earlier entries.
