# Evaluation — per-finding annotation

Disputatio's quality is measured by judging **each finding on its own merits against the paper**, not by a holistic rubric score on the whole review. This protocol produces precision-like and calibration metrics that can discriminate between a debate-hardened review and an overconfident single-pass one.

## When this runs

**Post-hoc**, after `4_report/referee_report.md` is written and `2_ranking/issue_register.md` is frozen. Evaluation does NOT feed back into the pipeline. It is a separate, independently-annotated quality assessment.

## Atomic unit: the finding

Every finding in `_artifacts/json/ranked_issues.json` is a quadruple:

```json
{
  "id":             "merged_001",
  "claim":          "<what the finding asserts>",
  "quote":          "<verbatim excerpt from the paper>",
  "quote_location": "<section / page / equation anchor>",
  "evidence":       "<why the claim follows from the quote + paper structure>"
}
```

The evaluator judges **each quadruple independently** on two axes. No ground-truth issue register is required.

### Aggregated findings

If a finding has `aggregated: true` with a `sub_findings` array, annotate **each sub-finding as its own row** (e.g. `merged_099.a`, `merged_099.b`, ...). The top-level finding gets a summary calibration based on whether the *aggregate pattern claim* holds; each sub-finding gets its own `quote_verified` and `calibration`. Bundled findings without `sub_findings` must not exist — they are rejected at merge time per `templates/merge_and_rank.md` Step 2b.

## Rubric

### Axis 1: `quote_verified`

Does the quote actually exist in the paper at the cited location, saying what the finding claims it says?

| Value | Meaning |
|---|---|
| `yes` | Quote appears verbatim (or near-verbatim with insubstantial OCR cleanup) at the cited location, and supports the claim's premise. |
| `partial` | Quote exists but is paraphrased, misplaced, truncated in a way that changes meaning, or the location anchor is wrong. |
| `no` | Quote is fabricated, grossly misrepresented, or does not appear in the paper at all. |

### Axis 2: `calibration`

Given the quote is real, does the stated evidence actually establish the claim at its stated strength?

| Value | Meaning |
|---|---|
| `supported` | The evidence establishes the claim as stated. Concrete objections, counterexamples, or contradictions are demonstrable. |
| `overclaimed` | There is a real issue, but the finding overstates severity, scope, or certainty. The paper has a weakness here, but not the weakness as described. |
| `unsupported` | The evidence does not establish the claim. The finding is either a misreading of the paper, a style/taste complaint dressed as a substantive flaw, or a methodological nit promoted beyond its actual impact. |

**`overclaimed` is the most important value** — it is the metric that discriminates between a debate-hardened review (which walks back overconfident claims) and an aggressive single-pass review (which keeps them).

## Procedure

The evaluation phase runs after `final_report = done` and the orchestrator has not yet emitted any `evaluate` tickets. Wave-style emission, mirroring discovery.

1. Open `_artifacts/json/ranked_issues.json` and walk the merged-issues array.
2. For each issue, build a **payload JSON** at `_artifacts/json/eval_<finding_id>_payload.json` containing only `{claim, quote, quote_location, evidence}` — the four substantive fields. Do NOT include `agent`, `method`, `confidence`, `support_score`, `centrality`, or any merge metadata. The annotator must judge the finding on its own merits, not on which model surfaced it.
3. For each (finding × annotator) pair, emit one `evaluate` ticket pointing at the payload + the operational template `templates/evaluate.md`. The default annotator is **codex with `gpt-5.4-mini`** (cheap, fast, matches the manual baseline from 2026-04-13). One annotator per finding is enough for the first iteration; two-annotator double-blind is a follow-on.
4. Run the eval tickets through `agent-ctl run-dag`. Each produces one `_artifacts/json/eval_<finding_id>_<annotator>.json` with the two-axis annotation.
5. Aggregate inline: read all eval JSONs, deduplicate per finding, compute the scorecard, write `_evaluation/00_evaluation.md` and `_evaluation/annotations.md`. Aggregation is a Claude-inline step (no ticket); the inputs are deterministic and a third agent adds no value at the aggregation level.

### Aggregated findings

If a finding has `aggregated: true` with a `sub_findings` array, the orchestrator emits **one ticket per sub-finding** with payload IDs `eval_<finding_id>.<sub_letter>_payload.json`. The aggregate-level claim itself is not annotated separately — the rubric judges concrete quotes against the paper, and the aggregate-level claim does not have a single concrete quote (per `templates/merge_and_rank.md` Step 2b's atomicity rule). The aggregator computes per-sub scores and surfaces the average in the scorecard alongside the per-sub breakdown.

### Blinding

The pseudonymisation is automatic and minimal: the payload sent to the annotator already strips agent/method/confidence/support metadata. The finding's `id` (`merged_NNN`) is used as the ticket key but does not leak which model surfaced it (merge IDs are assigned post-merge in arrival order). No randomised pseudonym map is needed for single-review evaluation; the metadata strip is sufficient because there is no review-version contrast to bias against.

For cross-review comparison (out of scope for the first evaluation harness), randomised pseudonyms across reviews would be needed. Defer until that comparison is genuinely required.

### Double annotation (deferred)

Inter-annotator agreement requires two annotators per finding. Same ticket shape, different `agent`/`model`. Aggregator surfaces disagreements in `_evaluation/disagreements.md`. Not in v1; the protocol is unchanged when it lands.

## Output files

### `_artifacts/json/eval_aggregate.json` — machine source of truth

```json
{
  "annotator": "codex/gpt-5.4-mini",
  "n_findings": 27,
  "counts": {
    "quote_verified": {"yes": 22, "partial": 4, "no": 1},
    "calibration":    {"supported": 18, "overclaimed": 6, "unsupported": 3}
  },
  "rates": {
    "fabrication_rate":  0.037,
    "support_rate":      0.667,
    "overclaim_rate":    0.222,
    "unsupported_rate":  0.111
  },
  "per_finding": [
    {"finding_id": "merged_001", "quote_verified": "yes", "calibration": "supported", "notes": ""}
  ]
}
```

The markdown files below are projections of this JSON. If they disagree, the JSON wins. Re-running aggregation regenerates both atomically.

### `_evaluation/annotations.md`

Worksheet keyed by `finding_id`. Each row is self-contained and machine-parseable via frontmatter tables.

```markdown
---
tags: [disputatio, evaluation, <paper-slug>]
phase: evaluation
paper: "<paper title>"
review_version: <v2 | v3 | coarse | reference | ...>
annotator: <name>
blinded: true | false
date: YYYY-MM-DD
---

# Per-finding annotations — <review-version>

## merged_001 — <short name>
- **finding_id**: merged_001
- **claim**: <one-line restatement>
- **quote**: "<verbatim>"
- **quote_location**: <anchor>
- **quote_verified**: yes
- **calibration**: supported
- **notes**: <free text; required for overclaimed/unsupported>

## merged_002 — ...
...
```

### `_evaluation/00_evaluation.md`

Aggregate scorecard. The body is a single table; any commentary goes below it.

```markdown
---
tags: [disputatio, evaluation, <paper-slug>]
phase: evaluation
paper: "<paper title>"
date: YYYY-MM-DD
---

# Evaluation scorecard — <paper title>

| Metric | <v2> | <v3> | <coarse> |
|---|---|---|---|
| n findings                       |  |  |  |
| quote_verified = yes             |  |  |  |
| quote_verified = partial         |  |  |  |
| quote_verified = no              |  |  |  |
| calibration = supported          |  |  |  |
| calibration = overclaimed        |  |  |  |
| calibration = unsupported        |  |  |  |
| fabrication rate (quote ≠ yes)   |  |  |  |
| support rate (calibration = supported) |  |  |  |
| overclaim rate (calibration = overclaimed) |  |  |  |

## Notes

<free text: what the numbers show, caveats, disagreements between annotators, etc.>
```

### `_evaluation/comparison.md` (optional)

Side-by-side of the same finding across review versions, when versions are compared on the same paper. Useful for showing that V3's defense step narrows an overclaimed V2 finding into a supported one.

## Relation to `2_ranking/web_verification.md`

They are **distinct and non-overlapping**:

- `web_verification.md` — Gemini fact-checks claims **against external sources** (papers, databases, web). Produces pipeline input to ranking (boosts or penalizes issues before debate). Runs inside the pipeline.
- `_evaluation/annotations.md` — human (or blind-LLM) judgment of each finding **against the paper itself**. Produces quality metrics for the review. Runs outside the pipeline, post-hoc.

Keep them separate. Never merge their outputs.

## Why not a gold issue register + precision/recall?

Building a "gold answer key" of real issues in a paper requires a reference reviewer, doesn't scale, and doesn't measure what we actually care about: whether the system **overclaims**. The per-finding rubric sidesteps the answer-key problem — each finding is judged against the paper directly.

Cost: you cannot measure **recall** (what the system missed) without a gold register. That is acknowledged. For the claim "debate reduces overclaiming," precision and calibration are sufficient; recall is a separate evaluation we defer.
