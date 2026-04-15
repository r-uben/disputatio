# 2026-04-14 — Brutal dialectic redesign (Tier 1)

## Why

The 2026-04-13 v3 run on Galeotti-Golub-Goyal 2020 produced 100% round-1 convergence on every debated issue and a 37.5% top-8 overclaim rate in blinded eval. Side-by-side with `coarse.ink` (single-shot Opus 4.6, $2, minutes), disputatio's report was strictly worse on prose quality and overlapped on 5/6 themes — paying ~10× cost for marginal additional content (the verification stage's one false-positive catch).

Codex diagnosis (2026-04-13): the system fights itself. The ranker double-weights cross-agent consensus → routes already-settled issues into debate → closure-seeking prompts collapse them in round 1. Three RLHF'd frontiers playing polite roles can't produce dialectic by construction. Rotation/escalation logic adds zero value when round 2 never fires.

## What changed (Tier 1, this branch)

**1. Status routing replaces score routing** (`templates/merge_and_rank.md`)
- Kept `rank_score = centrality + 2·cross_agent_support + evidence_specificity + severity` for report ordering.
- New `status` field on every merged issue: `drop | settled | debate`.
- `settled` = ≥2 families flagged AND evidence_specificity ≥ 2 AND web verification not inconclusive.
- `debate` = anything else that survived triage.
- Debate cohort = issues with `status: debate`, sorted by `rank_score`, capped at top-N.
- Zero `debate` issues → debate phase is **skipped entirely**.

**2. Adversarial personas in debate prompts**
- `templates/prosecute.md`: "you are the area editor recommending reject. Soft objections do not survive editorial review." Minimum 5 objections. No `confidence` softener. No `anticipated_defense` pre-concession.
- `templates/defend.md`: "you are the senior author. Your tenure case rests on this work holding up." `concede` field removed. Replaced with `falls_to` which forces explicit articulation of the surviving claim and minimal textual change.
- `templates/synthesize.md`: "you are the handling editor. You must declare a verdict." `converged` removed entirely. Verdicts: `prosecution_wins | defense_wins | split | escalate`.

**3. Tension-based budget replaces tier-based pre-allocation** (`SKILL.md`, `templates/emit_tickets.md`)
- Every issue starts with budget for round 1.
- Rounds 2-3 funded only on `split` or `escalate` verdicts.
- `prosecution_wins` and `defense_wins` are terminal.
- The "top third gets 3 rounds, middle 2, bottom 1" pre-allocation is removed.

**4. Final report schema updated** (`templates/final_report.md`)
- `material_issues` keyed off `verdict: prosecution_wins`.
- `local_issues` keyed off `verdict: split`.
- `dropped_issues` keyed off `verdict: defense_wins`.
- New `escalated_issues` and `settled_issues` sections.
- `surviving_text` (synthesizer's report-grade paragraph) replaces `claim`/`refined_claim` as the canonical body text.

**5. Rendering schema updated** (`templates/obsidian_render.md`)
- Issue register: `Status: settled | debate | escalated` and `Verdict: prosecution_wins | defense_wins | split | escalate` (debated only).

## Files touched

- `templates/merge_and_rank.md` — Step 3b added; Step 4 schema gets `status` field; Step 5 rewritten as status-driven.
- `templates/prosecute.md` — full rewrite, hostile persona.
- `templates/defend.md` — full rewrite, hostile persona, schema change.
- `templates/synthesize.md` — full rewrite, verdict-based, no `converged`.
- `templates/emit_tickets.md` — Wave 5 cohort selection rewritten; Wave 6+ verdict-driven funding.
- `templates/final_report.md` — Step 1 classification + JSON schema rewritten.
- `templates/obsidian_render.md` — issue register + final report sections updated.
- `SKILL.md` — short-circuit rules + budget tiering paragraphs rewritten.

## What did NOT change (yet)

Tier 2-5 from the redesign punch list:
- Single-shot baseline diff (would prove the value-add per run).
- Pre-publication blinded calibration (move Phase 5 before final report).
- Internal-verification methods for theory papers (M8 derivation replay, M9 notation audit, M10 theorem-scope audit).
- Drop role rotation as default.

These are deferred. Tier 1 alone should cut the politeness ritual; the next test run will tell us how much overclaim drops and whether `defense_wins`/`split` verdicts actually fire.

## Next test

Re-run on the same paper (Galeotti-Golub-Goyal 2020) with the new templates. Compare:
- How many issues get `status: settled` vs `debate`?
- Of debated issues, what's the verdict mix?
- Does any issue trigger round 2?
- Top-8 overclaim rate vs the v3 baseline of 37.5%?
- Report length / quality side-by-side with coarse.

If the new run still produces 100% round-1 termination, the templates aren't the issue — the models are too agreeable and we need to swap one of the three for something less RLHF'd.
