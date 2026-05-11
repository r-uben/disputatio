# [v8] Drop `gpt-5.4-mini` for narrow_evidence and broad_critic

**Type**: tactical / model routing
**Priority**: medium (codex calls this "blunt" — least structural fix; +5%, not the headline)
**Origin**: 2026-04-25 head-to-head

## Problem

SKILL.md routes:

| Task | Codex | Gemini |
|---|---|---|
| Discovery (all tracks) | `gpt-5.4-mini` | `gemini-3-flash-preview` |

Coarse's published bench used `gpt-5.4` at **high effort**. The model gap is real — mini misses the kind of detailed mathematical specification audit full models catch. Subscription cost is the same either way (we're on Pro plans, not API), so the cost arg is wall-clock only.

## Proposal

| Track | Codex | Gemini |
|---|---|---|
| holistic_candidates | gpt-5.4 | gemini-3.1-pro-preview |
| broad_critic | gpt-5.4 | gemini-3.1-pro-preview |
| narrow_evidence | **gpt-5.5** (or gpt-5.4 high-effort) | gemini-3.1-pro-preview |

Orient stays on mini/flash (it's structural extraction, not judgment).

## Why this is "blunt"

Per codex 5.5: stronger models will improve *recall* on existing methods but won't fix obligation-blindness. The structural fixes (issues #01, #02, #03) are the headline. This is a +5% complement, not a substitute.

## Cost

- Wall: ~2× current narrow_evidence wall time (mini is genuinely faster)
- Codex weekly cap: matters only if user is rate-limited; current user has the cap removed
- Quality: should add ~5–10% recall on formal-spec issues

## Open questions

- **Should we also upgrade the calibration first-pass annotator?** SKILL.md uses `gpt-5.4-mini` for Pass 1. Probably no — bulk annotation is rubric-bounded and benefits from speed; the re-annotator (`gpt-5.4` full) catches mini's blind spots.
- **What about Phase 1 holistic?** Already on `gpt-5.4` per SKILL.md routing table. Keep.

## Related

- Issue #01: Obligation extraction (where the real fix lives)
- Issue #05: Bench before committing

## Source critique

> "A: Reasonable but blunt. Full models may improve recall, but this is the least structural fix." — codex/gpt-5.5, 2026-04-25
