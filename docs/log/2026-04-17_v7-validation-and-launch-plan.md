# 2026-04-17 · v7 validation + launch plan

Handoff document for the next session. Captures v7 validation results, the
codex+gemini launch-strategy debate, and the concrete plan to execute before
going public with disputatio.

## TL;DR

- **v7 shipped.** Four amendments (calibrate upgraded re-annotator, M8
  algebraic trace, narrow yield floor, Route B consensus override) merged into
  `feat/v7-amendments`, PR #12 open against `main`, **not yet merged**.
- **Validated end-to-end** on Galeotti-Golub-Goyal 2020 (Econometrica).
  Blinded A/B vs coarse.ink: disputatio 100% supported / 0% overclaim vs
  coarse 36.4% / 27.3%. **But the 100% is suspicious** — our filter uses a
  stronger model (gpt-5.4 full) than the A/B judge (gpt-5.4-mini), so the
  result is partly artifact of filter-vs-judge asymmetry.
- **Website updated** with v7 architecture: new pipeline slideshow (7 Latin
  phases), 4 method/track panels, decision-tree section, validation scorecard,
  and a new `/compare.html` side-by-side vs coarse. Version strings stripped
  from public copy. Still `noindex`.
- **Launch plan decided** based on codex+gemini consultation: staggered
  soft-launch to ~10-20 technical researchers via DM. Don't publish 100%
  headline until a cross-judge stress test is run.

## Repo state

```
feat/v7-amendments     pushed, PR #12 open, 4 commits beyond main
main                   clean, synced to origin, has v6-core merged (PR #11)
```

Recent branch layout cleanup already done. Delete old `feat/v6-upstream` from
origin after v7-amendments merges.

Four commits on `feat/v7-amendments`:

- `cfe85ce` calibrate: upgraded re-annotator + hard-spec uncertainty triggers
- `30a587e` M8 algebraic derivation trace: close the algebra-checking gap
- `7d04cd6` narrow_evidence: floor yield at 6 (retry if <6, no surface_attempts)
- `71edb31` escalation gate: Route B consensus override (done right, not papered over)

## v7 validation artifacts

On disk at
`~/Library/Mobile Documents/iCloud~md~obsidian/Documents/notes/work/referee-reports/galeotti-golub-goyal-2020_v7/`:

- `_artifacts/json/panel.json` — 27 shipped findings (canonical output)
- `4_panel/panel.md` — finding table + 3 drop sub-tables (UI-primary)
- `4_panel/author_memo.md` — 1070-word memo
- `4_panel/revision_plan.md` — sentence-level edit table for fix+watch rows
- `_calibration/final_findings.json` — full calibration trail
- `_calibration/00_calibration.md` — scorecard (Pass 1 + polish + gate + debate + Pass 2)
- `_evaluation/results.json` — three-way blinded A/B machine truth
- `_evaluation/00_evaluation.md` — A/B scorecard (49 findings pool after
  consolidation: 27 disputatio + 22 coarse; original pool was 77 with v6
  included but that's internal)

### Key counts

```
110 raw candidates  (3 × 3 tracks × ~9-12 findings + 22 baseline)
 42 atomic merged rows  (after validator + atomic dedup)
 27 panel findings shipped
 46 dropped with audit trail
    13 dropped at calibration Pass 1
    31 dropped at merge
     2 dropped by Route B red-team (F003 Property A + F006 nonnegativity)
     0 dropped by Route A defense

  4 consensus rows entered Route B (F001/F002/F003/F006)
    2 consensus_held (F001 Theorem 1 genericity, F002 Prop 2 w<0 scope gap)
    2 consensus_broken (F003, F006)

  0 Route A debates triggered (no strong disagreement between families)
```

### Blinded A/B numbers

```
                    n   supported  overclaim  unsupported  quote-verify
disputatio         27    100.0%      0.0%       0.0%         88.9%
coarse.ink (s4.6)  22     36.4%     27.3%      36.4%         63.6%
```

Same paper, same annotator (codex gpt-5.4-mini), same rubric, seed 20260417.

**One confirmed false positive**: Route B dropped F003 as shared misread via
`surface_pattern_overfit`. But the blinded judge rated v6's F003 equivalent
`supported`. Route B over-pruned a real concern. Mechanism caught 2
concerns that needed scrutiny (F003, F006) but only F006 was genuinely
shared-hallucination; F003 was real.

## The 100%/0% credibility problem

**Filter is stricter than judge by construction.** v7's pipeline:

```
discovery → Pass 1 (gpt-5.4-mini) → polish → Pass 2 (gpt-5.4 FULL, strict triggers) → ship
                                                                                        ↓
                                                                             A/B judge (gpt-5.4-mini, laxer)
```

Anything that survives the stronger filter trivially passes the weaker judge.
The 100% is partly an artifact of this asymmetry, not just quality.

Under a stronger judge (opus or gpt-5.4 full), we'd expect some findings
called overclaimed. Not 25% like v6, but probably not 0% either. Maybe 5-12%.
**We haven't measured that yet.**

## Codex + gemini launch-strategy debate

Consulted both on 2026-04-17. Full responses in session transcript; summary:

### Where they converge (act on these)

1. **Don't launch 100%/0% as headline.**
   - codex: *"reads like benchmark laundering"*
   - gemini: *"100% screams methodological flaw... honest caveat in
     footnotes won't save you; the headline will trigger BS detectors
     instantly"*
   - **Action**: run cross-judge stress test with opus (or gpt-5.4 full) as
     blinded judge BEFORE public launch. Report a range. Publish the
     spread. Variance is the story.

2. **Reposition harder vs coarse.**
   - codex: *"not an AI referee letter, an evidence panel you can inspect"*
   - gemini: *"Coarse is fast food; Disputatio is a lab test. Clinical-grade
     precision for authors."*
   - **Action**: abandon cheap/accessible/ideological axis. Target user is
     a researcher submitting to a top journal who cares about false
     positives more than volume. Compete on /compare page, not homepage.

3. **Staggered soft-launch, not big-bang.**
   - Both: merge PR, clean site copy, run stress test, DM 10-20 high-signal
     researchers (econ/ML), iterate, THEN public. No Twitter, no Reddit, no
     HN initially.

4. **Lead with the F003 false positive, not bury it.**
   - Showing failure modes builds trust faster than hiding them.

### Where they disagree — distribution

- **codex**: ship a hosted upload flow ("upload paper, get finding panel"),
  even ugly and rate-limited. Legibility for non-agent users is the wedge.
- **gemini**: ship as Claude-Code-native skill. Installation friction as
  feature — filters to high-intent technical early adopters. Coarse owns
  mass market; disputatio owns power user. Don't bleed money on hosted.

**My lean**: gemini wins for this moment.
- We hit 94% weekly API cap recently. Hosted = we pay all LLM costs. Not viable.
- First 20 users are almost certainly AI-native already.
- /compare page + per-finding blinded verdicts solves codex's legibility
  concern at the artifact level — readers see quality without running the
  skill themselves.
- "Installation friction as filter" is right for first 20 users; wrong for
  public. Solve later, not tonight.

## Concrete plan — next session

### Before anything else

1. **Hard refresh the local preview** at
   `http://localhost:8765/disputatio-ccc1a3e8/` — version strings were
   already stripped from the file but the screenshot the user sent had
   stale cached content. Verify page looks right.

2. **Resolve the "design doesn't open correctly" complaint** that was never
   fully diagnosed — user reported it after the first subagent rewrite. May
   be browser cache, may be a real layout issue. Get specific feedback on
   what looks wrong (hero / pipeline scroll / methods scroll / decision tree
   / validation / mobile).

### Tonight (≤2 hours of work)

3. **Run cross-judge stress test.** Same 49-finding pool at
   `galeotti-golub-goyal-2020_v7/_evaluation/`, but judge = opus or gpt-5.4
   full instead of mini. Cost ~$5-10. Report cross-judge range (e.g.,
   `94-98% supported` instead of `100%`).

4. **Update headline stats** on `index.html` with the cross-judge range and
   new framing. Drop the literal 100%/0% from the top.

5. **Promote the F003 caveat.** Currently buried in one line at bottom of
   validation section. Make it bigger/harder. Show the failure mode
   explicitly — it's trust-building.

6. **Sharpen the hero tagline** toward clinical-grade/evidence-panel axis.
   Current is close; gemini's framing is sharper:
   - `"An evidence panel you can inspect. Not a referee letter."`
   - `"Three independent readers. A finding panel you can audit. Not a prose review."`

7. **Merge PR #12** once site copy is aligned with stress-test numbers.

### This week

8. **Soft-launch**: DM 10-20 technical researchers (economics + ML). Share
   the private URL `rubenfernandezfuertes.com/disputatio-ccc1a3e8/`. Pitch
   angle per gemini: *"I built a rigorous multi-agent paper reviewer. It
   produces verified finding panels, not prose. It's a pain to install
   (needs Claude Code + Gemini), but it caught 0% overclaims in a blinded
   benchmark. Want to run your working paper through it?"*

9. Keep `noindex` on. Gather feedback. Collect social-proof quotes.

### Later (after real signal, not speculation)

10. Remove `noindex`. Rename URL from `/disputatio-ccc1a3e8/` to
    `/disputatio/`. Add main-site nav link.

11. **Consider** PyPI CLI or hosted — only if 10+ people ask. Nobody has
    asked yet.

## Website current state

At
`~/Library/Mobile Documents/com~apple~CloudDocs/personal/website/disputatio-ccc1a3e8/`:

- `index.html` — 228 KB, 4720+ lines. Pipeline slideshow rebuilt to 7 Latin
  phases. Methods collapsed to 4 panels (3 tracks + reserved M1/M7). Demo
  section refreshed with v7 numbers. Decision-tree section added at line
  ~4247. Validation section has 2-row scorecard (disputatio/coarse).
- `compare.html` — 35 KB new file. 6 shared concerns + 3 disputatio-unique
  + 3 coarse-unique per-finding side-by-side. Each cell has a colored
  verdict pill (supported/overclaimed/unsupported/partial).
- `cases/targeting-interventions.html` — **STALE, needs v7 rewrite**.
  Flagged as v7.1 scope by subagent.
- `cases/population-genetics.html` — **STALE, "Score withdrawn"**. Also
  v7.1 scope.

Local preview server running at `http://localhost:8765/` (may need restart
on next session; spawn with `python3 -m http.server 8765` from the website
root).

### Stale content NOT touched

- `<title>` tag: `"disputatio · a dialectic engine for structured critique"`
  — fine, neutral, not version-stale.
- Footer tagline: `"A claim is only as good as the objections it survives"`
  — leans debate-centric. Sharp copy though; keep unless rebrand.
- Case study pages (see above).
- GPT icon SVG `<path d="...">` contains the substring `v7` in binary data.
  Not user-visible; ignore.

## Open v7.1 tickets (not blocking launch)

1. **Case study pages refresh** — `targeting-interventions.html` with v7
   artifacts, link from `compare.html`. `population-genetics.html` needs a
   full re-run at some point.
2. **Route B false-positive tuning** — F003 was dropped wrongly. Candidate
   fixes: require red-team defender to cite verbatim resolving text before
   breaking consensus (not just plausible reframing); require 2+ modes to
   fire before consensus_broken; flag rather than drop on consensus_broken
   and let human adjudicate.
3. **Polish discipline** — opus-inline polish rewrites during the v7 run
   introduced 3 `partial` quote-verify verdicts (3/27 = 11%). Tighten
   `templates/polish.md` to forbid any edit that moves the quote off
   verbatim.
4. **Re-annotate prompt template bug** — Wave 5a prompt generator had
   hardcoded `BF001` in the re-annotation template header. Patched in-flight
   during the run. Upstream fix is a separate commit against the generator
   in `emit_tickets.md`.
5. **Codex gpt-5.4 (full) flakiness** — ~50% first-pass failure rate on
   long-paper calibrate prompts during v7 run. All recovered on retry.
   Not urgent; `max_attempts: 2` already configured.

## Pointers

- PR #12: https://github.com/r-uben/disputatio/pull/12
- Full A/B scorecard:
  `notes/work/referee-reports/galeotti-golub-goyal-2020_v7/_evaluation/00_evaluation.md`
- Pipeline walkthrough (created earlier in this arc):
  `notes/projects/disputatio/pipeline-walkthrough.md`
- v7 followups docket:
  `notes/projects/disputatio/v7-followups/README.md`
  (now marked all-resolved after this run)

## Context for the next session

Fresh session should open with:

1. Read this file.
2. `cd` to the disputatio repo. Check `git status` — should be clean on
   `feat/v7-amendments` with nothing staged.
3. Decide which step from "Concrete plan" above to tackle first.
4. My top recommendation: **cross-judge stress test first**. Nothing else
   should ship to a public surface until we have a defensible cross-judge
   number to anchor the headline.

---

## Update — 2026-04-17 (later same day): stress test completed

### Consolidation pass first

Before running the stress test, scrubbed internal pipeline version strings
(v4/v5/v6/v7) from all user-facing surfaces and consolidated history into
`CHANGELOG.md`. Three surfaces cleaned: website (`index.html` line 3769),
repo README, and the panel renderer template (frontmatter was stamping
`version: v7` and splitting `_v7` suffixes out of paper-slugs as separate
tags). Product is now consistently named **disputatio** across all
user-visible output. Commit `3921a22`. Full scope in the commit message.

### Judge consultation

Consulted codex (`gpt-5.4`) and gemini (`3.1-pro-preview`) in parallel on
judge selection. Strong convergence — both independently picked
`gemini-3.1-pro-preview` as the single best addition to the existing
`gpt-5.4-mini` anchor. Both rejected:

- Kimi / Ollama — capability-insufficient for 30-page paper + verbatim
  quote verification. Produces noise, not signal.
- Gemini flash — adds noise, not insight.
- GPT-4.1 as second judge — same-family correlation risk; "degraded
  performance with correlated OpenAI biases" doesn't give independent
  signal.

### Stress test run

Pool: **49 findings** (27 disputatio + 22 coarse). V6's 28 internal-ablation
findings dropped per the consolidation principle — public comparison is
current disputatio vs current coarse, no ablation noise.

Judges: `gpt-5.4-mini` (anchor, existing) + `gemini-3.1-pro-preview` (new).
Same prompts, same rubric, same seed, identical blinded manifest.

Runtime: 49 gemini-pro tickets at 4-way concurrency, ~12 min, 0 failures.
Artifacts at `galeotti-golub-goyal-2020_v7/_evaluation_crossjudge/` —
annotations, tickets, manifest, `results_crossjudge.json`,
`00_crossjudge_evaluation.md`.

### Results

| source | judge | supported | overclaim | unsupported | quote yes |
|---|---|---:|---:|---:|---:|
| disputatio | gpt-5.4-mini | 100.0% (27/27) | 0.0% | 0.0% | 88.9% |
| disputatio | gemini-3.1-pro | **85.2%** (23/27) | 0.0% | 14.8% | 81.5% |
| coarse | gpt-5.4-mini | 36.4% (8/22) | 27.3% | 36.4% | 63.6% |
| coarse | gemini-3.1-pro | 36.4% (8/22) | 9.1% | 54.5% | 63.6% |

Inter-judge agreement on calibration verdict:

- disputatio: 23/27 findings got the same verdict from both judges (**85.2%**)
- coarse: 16/22 got the same verdict (**72.7%**)

### Reading the numbers

Good: the story holds honestly. **Disputatio: 85–100% supported, 0%
overclaimed** across both judges on 27 findings. **Coarse: 36.4%
supported, 9–27% overclaimed** across both judges on 22 findings. The
stronger grader (gemini) brought disputatio down 14.8pp on support but
did NOT bring disputatio near coarse's level — the gap is ~50pp either
way. The zero-overclaim claim is robust under both judges, which is
the single most defensible number we have.

Coarse's support rate is *identical* under both judges (36.4%). Both
graders converge that coarse is weaker. No "grader preference" excuse
for the gap.

### The 14.8pp delta traces to a real failure mode

Inspected the 4 findings where gpt-mini said supported and gemini said
unsupported. **All 4 share the same pattern: disputatio flags a concern
the paper itself already acknowledges elsewhere.**

| finding | failure |
|---|---|
| F035 | paper states "as long as the budget is small"; finding flags as hidden limitation |
| F020 | paper acknowledges p18 Assumption 5 "ensures our results are driven by the benefits side"; finding flags as hidden flaw |
| F022 | paper states "Property A facilitates analysis, it is not essential"; finding flags missing abstract signaling |
| F017 | paper has marginal "Corollary 1" / "Theorem 1" references; finding says "not cross-referenced" |

M5 "self-measured critique" evaluates findings against the pinned quote's
immediate context; the author's own acknowledgment elsewhere in the paper
slips through. gpt-mini misses this too as a judge because it evaluates
against the pinned quote, not the full text. Gemini catches it because
it reads integratively.

Rate: 4/27 = 14.8%. Localized to one failure mode, not a diffuse quality
gap. Fixable.

### GH issues filed

- **#13** — agent-ctl: add claude (sonnet/opus/haiku) as a launchable
  agent. Deferred infrastructure work that enables a 3-judge panel in
  the future.
- **#14** — calibration: detect self-acknowledged limitations before
  shipping a finding. Direct fix for the 14.8% failure mode. v7.1 scope.

### What the launch copy must say

Swap 100%/0% headline for: **"85–100% supported across two judge
families, 0% overclaimed (n=27). Where the judges disagreed, 4
findings traced to one specific failure mode — critiquing limitations
the paper already acknowledges. Failure mode published openly (GH #14),
fix in v7.1 scope."**

Comparison framing becomes: **"On this paper, disputatio support rate
was 49–64pp higher than coarse and overclaim rate 9–27pp lower, under
both judges."** Still flagged as n=1 paper, coarse at default
sonnet-4.6 (not its top tier), prose-vs-panel form difference. The real
axis is complementary deliverables (coarse writes a letter in minutes
for $2; disputatio writes an evidence panel in hours for $10–30), not
competitor displacement.

### Still pending before soft-launch

1. Update website copy (`index.html` validation scorecard + headline
   stats + `compare.html` scorecard) with the range, the failure-mode
   disclosure, and the two-judge context.
2. Merge PR #12 once website copy is aligned.
3. Rerun coarse at its top-tier model (Opus 4.6) for a fair comparison
   before the /compare page goes public beyond the private URL — codex
   and gemini both flagged this as a credibility requirement.
4. Reach out to coarse maintainer with the draft comparison before
   pushing publicly; invite correction. Integration question surfaces
   from that conversation, not from us.
