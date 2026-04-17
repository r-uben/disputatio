# Changelog

All notable changes to disputatio. This is the one canonical place for pipeline
version history — user-facing docs, the website, and rendered artifacts do not
carry version strings by design. Dated dev log entries with full reasoning live
under [`docs/log/`](docs/log/).

The pipeline is numbered internally (v3 → v4 → v5 → v6 → v7) for contributor
bookkeeping. These are not product release names.

## Unreleased

- Consolidation pass: stripped internal version references (v4, v5, v6, v7)
  from user-facing surfaces — README, panel renderer, website. Version history
  lives in this file only.
- Render template now forbids `version`, `n_findings`, or any extra frontmatter
  field in `panel.md` / memo outputs, and strips `_v\d+` suffixes from paper
  slugs before emission.

## 2026-04-17 — v7 amendments

Four amendments on top of v6, validated end-to-end on Galeotti, Golub & Goyal
(2020, *Econometrica*). See
[`docs/log/2026-04-17_v7-validation-and-launch-plan.md`](docs/log/2026-04-17_v7-validation-and-launch-plan.md)
for full validation and the honest caveats on the benchmark.

- **Calibration**: upgraded re-annotator + hard-spec uncertainty triggers.
- **Narrow evidence track**: floor yield at 6 per ticket; retry under floor, no
  `surface_attempts` escape hatch.
- **Method M8**: algebraic derivation trace made mandatory on every theory /
  proof surface. Closes the algebra-checking gap that leaked across v5 and v6.
- **Escalation gate**: Route B consensus-override path fixed. Three-family
  consensus now enters a red-team round rather than auto-passing.

**Benchmark (single paper, artifact-flagged headline).** 27 findings shipped
from 110 raw candidates. Blinded A/B judge (codex `gpt-5.4-mini`) rated 100%
supported / 0% overclaimed vs a coarse single-agent baseline at 36.4% / 27.3%
on the same paper under the same rubric. The calibration filter uses a
stronger model than the judge — some of the 100%/0% spread reflects filter-
vs-judge asymmetry rather than pure quality. A cross-judge stress test under a
stronger grader is the next validation step before publishing this as a
headline number.

## 2026-04-14 — v6 upstream pivot

See
[`docs/log/2026-04-14_v6-upstream-pivot.md`](docs/log/2026-04-14_v6-upstream-pivot.md)
and
[`docs/log/2026-04-14_v6-upstream-positioning-and-plan.md`](docs/log/2026-04-14_v6-upstream-positioning-and-plan.md).

- **Product**: repositioned from "referee report as primary deliverable" to
  "finding panel as primary deliverable, prose memo as secondary." The writer
  renders the panel; it cannot invent findings.
- **Discovery**: cut from 18 tickets (3 agents × 6 methods) to 9 tickets
  (3 agents × 3 tracks: holistic, broad critic, narrow evidence-judgment).
  Methods fold into tracks instead of each owning a ticket.
- **Holistic pass**: new upfront phase. Each family produces a paper spine +
  main claims + attack surfaces + likely referee questions. Unioned into a
  canonical attack-surface index shared across discovery.
- **Debate**: escalation-only, gated on cross-family disagreement + evidence
  on both sides + severity-would-change + user-visible. Most findings skip
  debate entirely.
- **Rendering**: single long-context writer per panel replaces fragment
  assembly for prose uniformity.

## 2026-04-14 — v5 calibration, baseline, polish

See [`docs/log/2026-04-14_v5-calibration-baseline-polish.md`](docs/log/2026-04-14_v5-calibration-baseline-polish.md).

- **Calibration loop**: blinded per-finding annotator. Overclaimed findings
  demoted one tier or rewritten narrower; unsupported findings dropped with
  audit trail. First release with user-visible overclaim escape rate as a
  release gate.
- **Merge atomicity**: programmatic validator enforcing that every merged
  finding's `quote` substring-matches `_paper/paper.md`. Cluster-split rules
  enforced.
- **Baseline (coverage sentinel)**: single-shot opus pass in parallel with
  discovery. Not a router — signals whether discovery missed a conceptual
  concern.
- **Polish sub-step**: one rewrite attempt per flagged finding before drop.
- **Benchmark (Galeotti 2020)**: 0% fabrication (down from 18.8% in v4),
  22% pre-demote overclaim rate (down from 56%), 0% user-visible overclaim
  after demotion.

## 2026-04-14 — v4 brutal dialectic

See [`docs/log/2026-04-14_brutal-dialectic.md`](docs/log/2026-04-14_brutal-dialectic.md).

- **Debate**: replaced v3's 8/8-converged collapse pattern with a structured
  prosecution-defense-synthesis round that produces real verdict diversity.
  v4 run on Galeotti 2020: 5 defense_wins, 3 split, 1 prosecution_wins.
- **Known regression vs v3**: fabrication rate and overclaim rate moved in
  the wrong direction under the harsher debate — motivating the v5
  calibration loop.

## 2026-04-13 — v3 cross-model debate

See [`docs/log/2026-04-13_v3-targeting-interventions-and-eval.md`](docs/log/2026-04-13_v3-targeting-interventions-and-eval.md).

- **Architecture**: first cross-model (Claude + Codex + Gemini) debate, up
  from v2's single-model dialectic.
- **Evaluation**: per-finding blinded annotation pipeline (v2 vs v3) and
  LLM-as-judge against the Stanford Agentic Reviewer reference vs coarse
  Sonnet 4.6.
