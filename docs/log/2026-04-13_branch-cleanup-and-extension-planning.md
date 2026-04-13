# 2026-04-13 — branch cleanup + multi-provider extension planning

Follow-on to the same-day V3/V4 evaluation log. Two deliverables: clean up the `feat/deep-discovery` branch before it merges to main, and design the path for extending beyond the Claude/Codex/Gemini trio to support user-chosen model teams (Kimi, Ollama-served local models, OpenCode-wrapped providers).

## What was done

### Branch cleanup on `feat/deep-discovery`

The branch had accumulated nine modified tracked files and a large pile of untracked run artifacts. Triaged into six atomic commits:

1. **Folder schema rename** (`6427cac`). Dropped the `00_/10_/.../60_` numeric-prefix scheme plus the experimental `tests/` parent. The canonical per-paper Obsidian layout is now `review.md`, `_paper/`, `0_orientation/`, `1_discovery/`, `2_ranking/`, `3_debates/`, `4_report/`, `_artifacts/`, `_evaluation/`. Touches every path reference across CLAUDE.md, SKILL.md, TICKETS.md, and the four templates that emit or consume paths.
2. **Atomicity rule in `merge_and_rank.md`** (`5a81757`). Added Step 2b: merged issues must have a single verbatim quote and a single location. Bundled findings like "various locations in Appendix A" are rejected here, since the per-finding evaluation protocol in `templates/evaluation.md` cannot annotate them. Genuine aggregate patterns carry an explicit `aggregated: true` flag plus a `sub_findings` array, so the top-level quote always points at one concrete passage.
3. **`adapt.py` heading fallbacks** (`7ac6015`). The flatten-for-coarse adapter now tolerates both "Material issues"/"Material findings", both "Summary"/"Overall assessment", and both bullet-list vs heading-style appendix sections. This makes the adapter robust to `final_report.md` template drift.
4. **`.gitignore` updates** (`2863792`). Added `TODO.md` (session-local scratch) and the three runtime-state paths that appear when `/disputatio` or `agent-ctl` runs from the repo root (`.claude/`, `_artifacts/`, `output/`).
5. **Per-finding evaluation template** (`8c81c25`). Committed `templates/evaluation.md` as the intended replacement for the current Gemini holistic judge. Scores each finding against the paper independently, producing precision-like and calibration metrics rather than a single rubric number.
6. **V4 eval outputs** (`66eba51`, `74fecb0`). Captured the V3/V4 run artifacts (disputatio review, adapted review, judge scorecards, coarse baseline) for targeting-interventions and the cross-model gemini-judge artifact for population-genetics. The `_unfair_mixed_skill_versions/` folder documents why the earlier population-genetics number was withdrawn.

Deleted: `index.html` at repo root (stray "Inertial Scroll Slideshow" prototype, not the actual website), `paper_copy.md`/`report_copy.md` duplicates under `compare/`.

### Multi-provider extension: design review

Reviewed `docs/adding-agents.md` (committed in `3b3b3cc`). Pushed back on three things before endorsing the 6-step sequence:

**1. Judge miscalibration is the real blocker.** The brief's steps 4–5 (family-weighted cross-agent support, aptitude-weighted role rotation) implicitly rely on being able to measure whether adding agents helps or hurts. The current Gemini judge rewards aggressive claims over calibrated ones (per the prior-session memory), so tuning those scoring tweaks against it is tuning against a broken yardstick. Sequenced the precision/recall judge (T-EVAL) to land *in parallel* with the refactor, not after.

**2. OpenCode is a gateway, not a model.** Confirmed via `opencode --help` that it exposes `opencode run --prompt "..." -m provider/model` and can route to Kimi, Ollama-served local models, Anthropic, OpenAI, and Google. The brief treats OpenCode as "a CLI wrapper" in passing; the stronger move is to make OpenCode *the* backend for every non-Claude/Codex/Gemini model. One `build_opencode_cmd` + a provider→family map replaces three separate integrations (Kimi, Ollama, OpenCode-as-wrapper). Tradeoff to verify: OpenCode may inject its own system prompt or reshape tool calls, so output quality needs a smoke test against native CLIs on a discovery pass before committing to it.

**3. Stage the refactor.** Don't bundle the six brief steps. First branch is `feat/agent-spec-refactor`: extract the `AgentSpec` dataclass, move `cmd_start` dispatch onto a registry, validate by rerunning orientation on a known paper and diffing outputs. Then `feat/opencode-backend` for the actual provider expansion. The family-weighted scoring math and N>3 role rotation can wait until someone actually configures a 5-agent team — until then they're premature generality.

### Session scratchpad

Created `TODO.md` (gitignored) capturing merge blockers, the V4 bug backlog (5 bugs worked around in-session but not upstreamed), the judge redesign, the extension branches with CLI research items for OpenCode/Ollama/Kimi, and the website mobile follow-ups. Intended as a session-local planning document, not a shipped artifact.

## Decisions and trade-offs

**Merged V4 runtime commits to the branch without waiting for T-EVAL.** V4 scores come from a judge known to reward style over accuracy. Committed the artifact set with an explicit note in the commit message ("Scores here are from the current holistic Gemini judge and should be read as proxy, not ground truth"). The alternative — hold the merge until precision/recall scoring exists — would have blocked the extension work on a dependency that's itself several sessions away. Better to ship the runtime and re-judge in place.

**Kept the `_unfair_mixed_skill_versions/` folder rather than deleting it.** It's archival evidence of why apples-to-apples skill-version matching matters. The README inside explains the asymmetry. Cheap to keep, and "why did the population-genetics number move?" is the kind of question a future reader will ask.

**T6 closed as "already done" rather than rewritten.** The 2026-04-11 log (`e2e-test-gemini-fix.md`) already satisfies the T6 acceptance criteria; writing a separate `comparison-run.md` would duplicate content. Updated TICKETS.md to point at the existing logs.

**Did not delete `compare/**/referee_report.md`.** It's the flattened V4 disputatio output used by the adapter — part of the eval artifact set, not a duplicate. Confusion on first pass; corrected.

## Blockers hit

None substantive. The iCloud-based repo layout makes some `git` operations slow on the first touch of a path, but nothing failed.

## What's next

Per `TODO.md`:

1. Decide whether to merge `feat/deep-discovery` → `main` now (runtime live, V4 scores labelled as proxy) or hold until T-EVAL lands.
2. Branch `feat/agent-spec-refactor` for step 1 of the brief.
3. In parallel: prototype `templates/evaluation.md` end-to-end on one paper so the precision/recall judge has a working implementation before the extension changes land.
4. Branch `feat/opencode-backend` once the refactor is validated; start with `opencode run -m provider/model` smoke tests against a known paper's discovery pass.
5. Upstream the five V4 bugs into the vendored `agent_ctl.py` in this repo.

## Outputs

- Commits on `feat/deep-discovery`: `6427cac`, `5a81757`, `7ac6015`, `2863792`, `8c81c25`, `66eba51`, `74fecb0`.
- Session scratchpad: `TODO.md` (gitignored).
- Design brief: `docs/adding-agents.md` (pre-existing, reviewed and annotated with staging recommendations above).
