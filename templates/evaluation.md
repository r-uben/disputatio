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

1. Open `_artifacts/json/ranked_issues.json` and `_paper/paper.md` side-by-side.
2. For each finding: read the quote at the cited location in the paper; judge `quote_verified`. If `no`, set `calibration: unsupported` automatically and move on.
3. If `quote_verified ∈ {yes, partial}`: read the paper's surrounding context and the finding's `evidence` field. Judge `calibration`.
4. Record notes for every `overclaimed` or `unsupported` finding so the judgment is auditable.
5. When all findings annotated, compute aggregates in `00_evaluation.md`.

### Blinding (recommended)

If evaluating multiple review versions (V2, V3, coarse, reference) on the same paper, strip review-identity labels before annotating. Randomize order. Annotator should not know which finding came from which system until after all annotations are complete.

### Double annotation (recommended for publication)

For any ambiguous finding, get a second annotator and resolve disagreements. Report inter-annotator agreement.

## Output files

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
