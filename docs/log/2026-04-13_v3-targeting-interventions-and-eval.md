# 2026-04-13 — V3 run on targeting-interventions, evaluation against coarse, public claim updated

## What we did

End-to-end re-run of `/disputatio` on Galeotti, Golub & Goyal (2020) — *Targeting interventions in networks* (Econometrica), V3 of this paper (V2 was a single-model debate; V3 is the cross-model debate the current skill produces). Then evaluated the result two ways: per-finding blinded annotation (V2 vs V3) and LLM-as-judge against the Stanford reference (vs coarse Sonnet 4.6).

Pipeline outcome:
- 113 raw findings (Claude 62 / Codex 24 / Gemini 27) → 27 merged → top 8 debated → all 8 converged in round 1 → final report at `4_report/referee_report.md` (1,758 words).

Per-finding blinded annotation (Codex `gpt-5.4-mini`, blinded, n=42):
- V2: overclaim 0.333, support 0.467, fabrication 0.133.
- V3: overclaim 0.259, support 0.741, fabrication 0.000.
- All three V3 metrics improve. Headline gain is support rate (+0.274 absolute).

LLM-as-judge (Gemini 2.5 Pro, Stanford reference, positional-bias on, 5-sample single + 1 panel):
- Disputatio v4 auto-adapted: 6.00/6 mean (σ=0), 5.62/6 panel.
- Coarse Sonnet 4.6: 5.53/6 mean (σ=0.21), 5.12/6 panel.
- Gap +0.47 (single), +0.50 (panel). Disputatio every dimension ≥ coarse.

## Decisions and trade-offs

**Patched `agent-ctl` to skip claude-typed tickets.** `cmd_start`'s codex/else dispatch was misrouting Claude tickets to Gemini CLI with `model=sonnet`, which 404s. One-line patch in `_ticket_ready` returns False for `agent == "claude"` so `run-dag` never touches them; orchestrator runs them inline. Local fix; needs upstream.

**Skipped Phase 4 web verification** — none of the 27 merged issues flagged `needs_web_verification: true` (this is a pure theory paper; all findings are internal-consistency failures verifiable against the paper text alone). Copied `ranked_issues.json → ranked_issues_verified.json` and stamped the verify ticket done with a `skipped_reason`. Saved ~10 min of Gemini calls.

**Used cross-model debate role rotation** as designed (R1: Claude prosecute / Codex defend / Gemini synthesise; rotation across rounds). Earlier in the planning phase, considered fixed roles for "specialty routing" (Claude = close reading, Codex = math rigor, Gemini = web-aware synthesis). Rejected: rotation IS the implementation of "everyone does everything" and matches the design intent better than fixed specialty assignment, which would make the win attributable to one model rather than to debate.

**Re-built `disputatio_review_v4_auto.md` by patching the adapter, not by hand.** Initial attempt scored 5.50 because `compare/adapt.py`'s `_extract_issues` only matched the old `N. **Title** — summary` format and produced a near-empty review. Rebuilding by hand to score 6.00 was cheating (testing my ability to write a review, not the skill's). Patched the adapter (commit `30f2032`) to handle the current Material/Local heading formats and to extract appendix concerns; auto-adapted output then scored 6.00 with no manual intervention.

**Withdrew the population-genetics comparison.** The compare folder had a `report_copy.md` from earlier today (~02:21, before the cross-model debate skill version) that scored 5.75 vs coarse 5.67. Re-running judge on it today against the current coarse baseline mixed skill versions on the disputatio side. Withdrew the public number; updated `cases/population-genetics.html` with a DRAFT banner and "score pending re-run" panel; added the unfair eval artifacts to `_unfair_mixed_skill_versions/` with a README explaining why.

## Blockers hit and resolutions

1. **Gemini OAuth expired mid-run** during Phase 3 syntheses. Fatal authentication error appeared in session logs but `agent-ctl` reported only "outputs missing after max attempts." User re-ran `gemini -p ping` manually to re-auth; reset failed tickets to pending; relaunched `run-dag`. Documented as bug 2 in `docs/roadmap.md`.

2. **Synthesis prompts had `[[WILL BE INJECTED]]` placeholders.** I emitted them with the placeholder, intending to inject after each prosecute+defend completed, but never wrote the injection step. Gemini compensated by reading the dependency JSONs directly via `--yolo` tool access. The synthesis outputs reference specific objections and replies correctly, so the round-1 syntheses are valid — but the mechanism was accidental, not designed. Documented as bug 4.

3. **First adapter run produced 0 issues.** The auto-adapter expected `N. **Title** — summary` format but the current `templates/final_report.md` produces `### N. Title` for material issues. Patched.

4. **Judge.py crashed on Gemini 3.1 Pro outputs.** Tried switching from 2.5 Pro to 3.1 Pro to match coarse.ink's exact judge model. JSON parse errors on coarse evaluations. Reverted to 2.5 Pro for the multi-sample run; documented as bug 6.

## What I'd do differently next time

- **Render markdown between phases.** Skipping it saves time but leaves the final report's wikilinks broken. The Haiku model is cheap; mandate the rendering step.
- **Test the adapter before relying on it.** Should have caught the heading-format mismatch by running `adapt.py` once on a sample report before quoting any judge score.
- **Pre-flight check for OAuth liveness.** A `gemini -p ping` at the start of the run would have caught the expired OAuth before three syntheses queued up against a dead service.
- **Just-in-time prompt injection.** The synthesis prompt placeholder bug is exactly the kind of thing a JIT injection step in `agent-ctl` would have caught — fail loudly when a prompt contains `[[WILL BE INJECTED]]` at launch time.

## Outputs

- Workspace: `<obsidian-vault>/notes/work/referee-reports/targeting-interventions-v3/`
- Adapted review: `compare/targeting_interventions/disputatio_review_v4_auto.md`
- Eval scorecards: `compare/targeting_interventions/eval_disputatio_review_v4_auto_*.md`
- Per-finding annotation: `<workspace>/_evaluation/00_evaluation.md` + `comparison.md`
- Public website (live): `https://rubenfernandezfuertes.com/disputatio-ccc1a3e8/`
- Adapter fix commit: `30f2032` on `feat/deep-discovery`
- Website update commit: `566a8e7` on `gh-pages`

## What's next

Per `docs/roadmap.md` validation backlog: re-run pop-genetics (highest priority), then cortical-circuits + coset-codes for n=4, then cross-judge robustness check on targeting. Bugs 1–6 in `docs/roadmap.md` should be tackled in a V4 sprint before the next paper run.
