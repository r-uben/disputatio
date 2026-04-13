# Evaluation — per-finding annotation

Disputatio's quality is measured by judging **each finding on its own merits against the paper**, not by a holistic rubric score on the whole review. This protocol produces calibration metrics that discriminate between a debate-hardened review and an overconfident single-pass one — in particular the `overclaim_rate`, which captures how often the review stretches a real issue into a stronger claim than the paper supports.

## When this runs

**Post-hoc**, after `4_report/referee_report.md` is written and `_artifacts/json/ranked_issues.json` (or `final.json`) is frozen. Evaluation is a self-contained sub-pipeline that lives entirely under `_evaluation/` inside the paper folder. It does NOT feed back into the pipeline; it is a separately-annotated quality assessment, recorded alongside the review for the human to read.

## The `_evaluation/` sub-DAG

Evaluation has its own ticket DAG, its own prompt store, and its own output tree — all under `_evaluation/` in the paper folder, cleanly separated from the main pipeline's `_artifacts/`.

```
<paper-folder>/_evaluation/
├── manifest_blind.json          ← blind_id → (true_version, true_id) map
├── tickets.json                 ← eval sub-DAG; one ticket per BF###
├── prompts/
│   └── BF001.md                 ← self-contained prompt (rubric + finding + paper + output path)
├── annotations/
│   └── BF001.json               ← annotator output (two-axis + notes)
├── sessions/
│   └── BF001.log                ← raw codex session capture (auto-archived)
├── results.json                 ← machine source of truth: rows + per-version summary
├── annotations_unblinded.csv    ← human-readable join of results + manifest
├── 00_evaluation.md             ← headline scorecard (markdown projection of results.json)
└── comparison.md                ← optional: side-by-side when >1 version evaluated
```

Isolating evaluation under `_evaluation/` (instead of mixing into `_artifacts/`) keeps the self-contained property sharp: the annotator's world is the prompt file and the paper; nothing in `_artifacts/json/` can leak version or agent identity into the judgement.

## Atomic unit: the finding

Every finding in `_artifacts/json/ranked_issues.json` (or `final.json`) is a quadruple the annotator judges:

```json
{
  "claim":          "<what the finding asserts>",
  "quote":          "<verbatim excerpt from the paper>",
  "quote_location": "<section / page / equation anchor>",
  "evidence":       "<why the claim follows from the quote + paper structure>"
}
```

### Aggregated findings

If a finding has `aggregated: true` with a `sub_findings` array, annotate **each sub-finding as its own blinded row** (`BF###` per sub-finding). The aggregate claim itself is not annotated separately — the rubric judges concrete quotes against the paper, and an aggregate claim does not have a single concrete quote (per `templates/merge_and_rank.md` Step 2b's atomicity rule). The aggregator surfaces per-sub scores in the scorecard alongside a sub-averaged summary.

## Blinding — randomised IDs, not metadata-strip

Every finding gets a randomised `BF###` identifier (zero-padded integers in random order). The orchestrator writes `_evaluation/manifest_blind.json`:

```json
[
  {"blind_id": "BF001", "true_version": "V2", "true_id": "merged_013"},
  {"blind_id": "BF002", "true_version": "V3", "true_id": "merged_024"}
]
```

The manifest is the ONLY place the `blind_id → true` mapping exists. The annotator never sees it. When the same paper has findings from multiple reviews (V2, V3, coarse, reference), they go into the same shuffled pool and get the same `BF###` naming scheme — the annotator cannot tell which review produced which finding, either by ID, by agent metadata (stripped), or by position in the list (randomised).

This is stronger blinding than metadata-stripping alone. Randomised IDs prevent the annotator from inferring that, say, `BF001..BF015` are V2 and `BF016..BF042` are V3 (which fixed ordering would leak).

Metadata-strip is still done on top: the payload inlined into each prompt contains only `{blind_id, claim, quote, quote_location, evidence}`. No `agent`, no `method`, no `confidence`, no `support_score`, no merge rank.

## Procedure

After `final_report = done` and no `_evaluation/tickets.json` exists:

1. **Collect findings** from every review version that will enter the evaluation. For single-review eval, that is just the current paper's `ranked_issues.json`. For cross-review eval, gather findings from each version's finalised issues (previous runs' artifacts under `_archive/`, or the comparison directory).
2. **Shuffle** all findings across all versions into one pool. Assign sequential `BF###` IDs in shuffled order.
3. **Write `_evaluation/manifest_blind.json`** with the `blind_id → (true_version, true_id)` mapping.
4. **Build one prompt per finding** at `_evaluation/prompts/<blind_id>.md`: inline the rubric, the finding JSON (with `blind_id` baked in but no version hint), the full paper text, and the output instruction (`write_file` to `_evaluation/annotations/<blind_id>.json`). See `templates/evaluate.md` for the exact prompt body.
5. **Emit one `evaluate` ticket per finding** into `_evaluation/tickets.json`. Default annotator: `codex` with `gpt-5.4-mini` (cheap, fast, matches the 2026-04-12 baseline). Inputs list is just the prompt file.
6. **Run the sub-DAG**: `agent-ctl run-dag <paper-folder>/_evaluation/tickets.json --cwd <paper-folder> --concurrent 4`. Each ticket produces one `_evaluation/annotations/<blind_id>.json`.
7. **Aggregate inline** (no ticket): read every `_evaluation/annotations/*.json`, join against `manifest_blind.json`, write `_evaluation/results.json` (machine source of truth), `_evaluation/annotations_unblinded.csv` (human-readable join), and `_evaluation/00_evaluation.md` (the scorecard markdown).

## Output files

### `_evaluation/results.json` — machine source of truth

```json
{
  "rows": [
    {
      "blind_id": "BF001",
      "version": "V2",
      "true_id": "merged_013",
      "quote_verified": "yes",
      "calibration": "supported",
      "notes": "..."
    }
  ],
  "summary": {
    "V2": {
      "n": 15,
      "qv_yes": 13, "qv_partial": 2, "qv_no": 0,
      "cal_supported": 7, "cal_overclaimed": 5, "cal_unsupported": 3,
      "fabrication_rate": 0.133,
      "support_rate": 0.467,
      "overclaim_rate": 0.333
    },
    "V3": {
      "n": 27,
      "qv_yes": 27, "qv_partial": 0, "qv_no": 0,
      "cal_supported": 20, "cal_overclaimed": 7, "cal_unsupported": 0,
      "fabrication_rate": 0.0,
      "support_rate": 0.741,
      "overclaim_rate": 0.259
    }
  }
}
```

- `rows` is flat; each row is one blinded annotation joined with its manifest entry. One source of truth; no nested per-version buckets inside `rows`.
- `summary` is computed at aggregation time and grouped by `version`. Derived from `rows`; if `rows` and `summary` ever disagree, recompute `summary` from `rows`.
- Rate definitions:
  - `fabrication_rate = (qv_partial + qv_no) / n`
  - `support_rate = cal_supported / n`
  - `overclaim_rate = cal_overclaimed / n`

### `_evaluation/annotations_unblinded.csv` — human-readable join

One row per finding, with all fields from `rows` flattened to columns. Useful for pasting into a spreadsheet or diffing two runs by hand. Optional but recommended.

### `_evaluation/00_evaluation.md` — scorecard markdown

Projection of `results.json`. Frontmatter plus one table with per-version columns:

```markdown
---
tags: [disputatio, evaluation, <paper-slug>]
phase: evaluation
paper: "<paper title>"
annotator: codex (gpt-5.4-mini)
blinded: true
date: YYYY-MM-DD
---

# Evaluation scorecard — <paper title>

| Metric                                        | V2    | V3    | Δ (V3 − V2) |
|-----------------------------------------------|------:|------:|------------:|
| n findings                                    |   15  |   27  |       +12   |
| quote_verified = yes                          |   13  |   27  |       +14   |
| quote_verified = partial                      |    2  |    0  |        −2   |
| quote_verified = no                           |    0  |    0  |         0   |
| calibration = supported                       |    7  |   20  |       +13   |
| calibration = overclaimed                     |    5  |    7  |        +2   |
| calibration = unsupported                     |    3  |    0  |        −3   |
| **fabrication rate** (quote ≠ yes)            | 0.133 | 0.000 | **−0.133**  |
| **support rate** (calibration = supported)    | 0.467 | 0.741 | **+0.274**  |
| **overclaim rate** (calibration = overclaimed)| 0.333 | 0.259 | **−0.074**  |

## Notes

<free text: what the numbers show, caveats, disagreements between annotators, etc.>
```

For single-review evaluation, drop the Δ column; the table has one version column plus the metric names.

### `_evaluation/comparison.md` (optional)

Side-by-side commentary when more than one version is evaluated on the same paper. Not generated automatically; written by hand when the user wants to narrate the delta.

## Double annotation (deferred)

Inter-annotator agreement requires two annotators per finding. Same ticket shape, different `agent`/`model`, same blinded prompt. Aggregator surfaces disagreements in `_evaluation/disagreements.md`. Not in v1; the protocol is unchanged when it lands — just emit two tickets per `BF###` with different annotators.

## Relation to `2_ranking/verification.md`

They are **distinct and non-overlapping**:

- `2_ranking/verification.md` — Gemini fact-checks claims **against external sources** (papers, databases, web). Produces pipeline input to ranking. Runs inside the pipeline.
- `_evaluation/00_evaluation.md` — annotator judgement of each finding **against the paper itself**. Produces quality metrics for the review. Runs outside the pipeline, post-hoc.

Keep them separate. Never merge their outputs.

## Why not a gold issue register + precision/recall?

Building a "gold answer key" of real issues in a paper requires a reference reviewer, doesn't scale, and doesn't measure what we actually care about: whether the system **overclaims**. The per-finding rubric sidesteps the answer-key problem — each finding is judged against the paper directly.

Cost: you cannot measure **recall** (what the system missed) without a gold register. That is acknowledged. For the claim "debate reduces overclaiming," precision-like metrics and calibration are sufficient; recall is a separate evaluation deferred until a reference pool of real issues exists.
