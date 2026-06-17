# Benchmark harness — data contracts

The harness reimplements refine.ink's 8-stage head-to-head faithfully (their rules), so "we beat them" holds on their own metric. Two contracts.

## Atomic concern (extract output)

The unit of comparison. disputatio's `panel_row` is already ~80% of this, so disputatio's own output skips Stage 1 (extract) — its panel rows ARE atomic concerns. Free-text baseline reviews get extracted into this shape.

```json
{
  "id": "X1",
  "title": "short description of exactly one issue",
  "specificity": "specific | general",
  "anchor": { "kind": "quote | section | equation | table | figure", "ref": "verbatim locator" },
  "body": "full explanation"
}
```
- `specific` requires an `anchor`; `general` is a high-level critique with none.
- Maps from `panel_row`: `concern`->title/body, `evidence[].quote`+`location`->anchor, `support_type` direct_quote/derived_inference -> specificity.

## 4-axis classification (classify output)

Per concern, judged on the concern's CONTENT (not the reviewer's wording — hedged and sharp prose get the same labels). Each axis carries a <=30-word reasoning field.

| Axis | Values |
|---|---|
| `scope` | `internal` (adjudicable from the paper alone) · `external_or_positioning` (needs outside lit / comparison) · `generic` (applies to most papers of this type) |
| `significance` | `load_bearing` (paper is wrong/weakly-identified until fixed) · `substantive_local` (improves it, stands without) · `cosmetic` (typo/format/prose) |
| `actionability` | `actionable` (names a specific change) · `vague` (raises an issue, no remedy) |
| `external_factual` | `yes` (hinges on a verifiable external fact) · `no` |

Maps from `panel_row`: `severity` material/local/nit ~ `significance` load_bearing/substantive_local/cosmetic (near 1:1); `category` + `needs_web_verification` inform `scope` and `external_factual`; `suggested_action` informs `actionability`.

## Downstream stage I/O (refine appendix)

- **anchor-check** -> `{anchored: true|false}` per concern (names a real paper feature; NOT "is the critique correct").
- **align** -> `{"matches":[{x_id,y_id,confidence,note}], "x_unmatched":[...], "y_unmatched":[...]}`.
- **rank** -> ordered residual ids per significance bucket.
- **judge** -> `{"winner":"X|Y|tie","reason":"...","pivotal_concerns":[...]}`, flip-averaged across both presentation orders, with the model-family self-bias filter (drop any judge whose family matches a contestant).

## Cost contract (every stage)

Each model call appends one line to the run's `usage.jsonl`:
```json
{"stage": "<stage>", "model": "<model>", "in": <input_tokens>, "out": <output_tokens>}
```
`cost_ledger.py` turns that into per-stage / per-model token + API-equivalent-USD totals (see README).
