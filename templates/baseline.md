# Single-shot holistic cross-check (Wave 2.5)

A parallel single-shot Opus pass that runs alongside the three-family holistic + 9-ticket discovery. In v6 its purpose is **not** "catch what structured discovery misses" — that is what the Phase 1 holistic pass already does. The single-shot cross-check is a **coverage validator**: if it surfaces a conceptual-scope concern that the three-family holistic pass did not include in the attack-surface index, that is a signal the holistic pass needs strengthening, not a bug to route around.

## Why this still runs in v6

1. **Holistic-pass validation.** The v6 Phase 1 holistic pass is new; we do not yet have enough measurement to trust that it covers the conceptual-scope concerns a single-shot opus reader naturally surfaces. Running a parallel single-shot pass gives a per-run sanity check: if the holistic pass missed something obvious, we see it.
2. **Merge-over-aggregation detector.** Even with v5's atomicity validator, merge can still cluster two genuinely distinct concerns if their quotes overlap. The baseline-diff step in `templates/merge_and_rank.md` Step 2c catches these by forcing any baseline-unique finding into the debate queue rather than silently absorbing it.

Once the holistic pass has been measured on 3+ papers and shown to match a single-shot pass for conceptual-scope coverage, this wave can be retired. Until then, it costs ~$2 per run and earns its keep.

## Historical context

v5 introduced this pass after the v4 run on Galeotti-Golub-Goyal missed the Section 5 "incomplete information" framing critique that a single-shot opus caught. Post-hoc analysis showed structured discovery had actually surfaced it (claude_m2 flagged it), but merge_rank over-clustered and lost it. The baseline-diff mechanism was designed to prevent this class of error from reaching the report.

## What it does NOT do

- Does not replace discovery. Discovery's 18 sweeps produce far more candidate issues than a single-shot review. Baseline is a safety net, not the main channel.
- Does not enter ranking. Baseline findings that overlap with our merged set are discarded (we already have the concern). Baseline findings that are *unique* get forced into a targeted one-round debate.
- Does not change rank_score. The baseline's own internal ranking is ignored; we only care about the set of concerns it names.

## Ticket

One ticket, emitted in Wave 2 alongside discovery (does NOT depend on orientation — the baseline's entire purpose is to be a naive, independent read):

```json
{
  "baseline_review": {
    "id": "baseline_review", "type": "baseline",
    "agent": "claude", "model": "opus", "family": "anthropic", "flags": {},
    "prompt_path": "_artifacts/prompts/baseline_review.md",
    "inputs": ["_paper/paper.md"],
    "outputs": ["_artifacts/json/baseline_review.json"],
    "depends_on": [],
    "status": "pending", "timeout_s": 900
  }
}
```

Runs in parallel with orientation and discovery. Typically completes in 3-5 minutes (single long-context Opus call, no tool use beyond reading paper.md).

## Prompt body

The prompt is intentionally simple — mimicking what a single-shot "write me a referee report" call produces. No disputatio methodology, no discovery methods, no seven-method framing. The more it resembles coarse's generic prompt, the more useful the diff.

```markdown
# Single-shot referee review

You are an expert referee for a top economics journal. Read the paper below and write a structured referee report.

## Paper

{{paper_text}}

## Output

Write a JSON file to `_artifacts/json/baseline_review.json`:

{
  "overall": "one-paragraph assessment",
  "themes": [
    {
      "title": "short title for this concern",
      "concern": "one-paragraph description of the concern",
      "quote": "verbatim passage from the paper that anchors the concern",
      "quote_location": "section / page / equation",
      "severity": "material | local | cosmetic"
    }
  ],
  "detailed_comments": [
    {
      "title": "...",
      "concern": "...",
      "quote": "...",
      "quote_location": "..."
    }
  ]
}

Aim for 5-7 themes and 10-20 detailed comments. Use verbatim quotes. Do NOT invent concerns — if the paper is clean on some dimension, say so and move on.
```

## Diff step (inline, at merge time)

After `merge_rank` produces `ranked_issues.json` AND the baseline ticket completes, the orchestrator runs a matching pass:

```python
baseline = json.load(open("_artifacts/json/baseline_review.json"))
merged = json.load(open("_artifacts/json/ranked_issues.json"))["ranked_issues"]
baseline_items = baseline["themes"] + baseline["detailed_comments"]

coverage_matches = []   # baseline item matched by a merged issue
coarse_unique = []      # baseline item NOT matched (we missed it)

for b in baseline_items:
    match = find_matching_merged_issue(b, merged)  # see "matching rules" below
    if match:
        coverage_matches.append({"baseline": b, "merged": match})
    else:
        coarse_unique.append(b)

# Force coarse-unique findings into the pipeline as new merged issues
for b in coarse_unique:
    merged.append({
        "id": f"merged_baseline_{i}",
        "claim": b["concern"],
        "quote": b["quote"],
        "quote_location": b["quote_location"],
        "evidence": f"Surfaced by coarse-style single-shot baseline; not independently found by disputatio's 18-sweep discovery. Investigate whether this was a discovery miss or merge over-aggregation.",
        "falsifier": None,
        "rank_score": 8,  # conservative default; will not sit at the top
        "scores": {"centrality": 2, "cross_agent_support": 0, "evidence_specificity": 2, "severity": 2 if b["severity"] == "material" else 1},
        "status": "debate",  # force into debate — we need adjudication since cross-agent support is 0
        "status_reason": "baseline-unique; disputatio discovery did not independently surface this",
        "sources": [{"agent": "baseline", "method": "single_shot_opus", "issue_id": f"baseline_{i}"}],
        "needs_web_verification": False,
        "aggregated": False
    })

# Write updated file
open("_artifacts/json/ranked_issues.json", "w").write(json.dumps({"ranked_issues": merged}))
open("_artifacts/json/baseline_diff.json", "w").write(json.dumps({
    "coverage_matches": coverage_matches,
    "coarse_unique_added_to_debate": coarse_unique,
    "stats": {
        "baseline_items": len(baseline_items),
        "covered_by_disputatio": len(coverage_matches),
        "baseline_unique": len(coarse_unique),
        "coverage_rate": len(coverage_matches) / len(baseline_items) if baseline_items else 1.0
    }
}))
```

### Matching rules

A baseline item is "covered" by a merged issue if ANY of the following holds (checked in order):
1. **Same quote** — verbatim substring match on `baseline.quote` ⊆ `merged.quote` (or vice versa).
2. **Same location anchor** — `baseline.quote_location` matches `merged.quote_location` at the section/equation level AND the claims are semantically related (opus judgement call — a sub-step run against both `claim` fields).
3. **Semantic match on claim** — a short opus call (`"Are these two concerns about the same issue in the paper? Return yes/no/partial."`) returns `yes`. Use `partial` as a miss (force the diff).

The matching pass is a single opus call batched over all baseline items vs the merged set. Not expensive.

## Cost

- Baseline ticket: one opus call on ~140 KB paper text ≈ 120-200K tokens, ~$2-3.
- Diff matching call: one opus call to match ~20 baseline items vs ~30 merged issues ≈ 20K tokens, ~$0.25.
- Total per run: **~$2.50, ~5 minutes wall-clock** (runs in parallel with discovery).

## Failure modes and handling

- **Baseline fails (opus timeout, API error).** Log the failure in `_artifacts/sessions/baseline_review.log` and proceed without the diff. Not a pipeline stopper — disputatio can still ship the report, just without the coverage check.
- **Baseline returns garbage (no quotes, hallucinated concerns).** Diff step has a quote-verbatim check; items without a real quote are silently dropped before matching.
- **100% overlap.** Means our pipeline caught everything coarse-style catches. Good outcome; no baseline-unique issues added.
- **>50% baseline-unique.** Alarm: either discovery is broken, or merge_rank is over-aggregating catastrophically. Log the coverage rate to `_calibration/00_calibration.md` and flag for investigation.

## Relation to cross-version evaluation (Phase 6)

This runs inside a single pipeline execution. Phase 6 A/B evaluation (`templates/evaluation.md`) compares two *already-finalised* reports. The baseline mechanism is per-run coverage insurance; the Phase 6 evaluation is per-release quality comparison. They are not redundant — Phase 6 can still run on top of a v5 report that used Tier 2 baseline, to verify the combined system against coarse's actual published reports.
