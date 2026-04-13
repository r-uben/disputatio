# Evaluate prompt — single blinded finding

This template is the **prompt body** sent to the annotator for one finding under review. Operational counterpart to `templates/evaluation.md`; substituted into the per-finding `evaluate` ticket at emit time.

The annotator is blinded: it does not know which review version (V2, V3, coarse, reference) produced the finding, nor which agent surfaced it, nor the merge rank. The blind ID is the only handle — the true version and true `merged_NNN` live only in `_evaluation/manifest_blind.json` and are never shown to the annotator.

## Prompt shape

The prompt is one markdown file per finding, written by the orchestrator to `_evaluation/prompts/<blind_id>.md`. It contains, in order:

1. **The blinding preamble**: you are judging one finding against the paper, you do not know which system produced it, do not guess.
2. **The rubric**: the two axes and their values (same as below).
3. **The finding under review** — a JSON block with exactly these fields:
   ```json
   {
     "blind_id": "BF001",
     "claim": "<one-sentence falsifiable statement>",
     "quote": "<verbatim paper excerpt>",
     "quote_location": "<section / page / equation anchor>",
     "evidence": "<the reviewer's reasoning>"
   }
   ```
4. **The paper text** — inlined directly. The annotator must read it to check the quote.
5. **The output instruction**: write one JSON file to `_evaluation/annotations/<blind_id>.json`.

No paper-map path, no separate payload file — everything the annotator needs is in the prompt. Inputs list on the ticket is just the prompt file itself. This keeps the annotator's world closed: it cannot see `ranked_issues.json`, cannot see other findings, cannot see any metadata that would leak the review version.

## Rubric (what the annotator reads)

### Axis 1 — `quote_verified`

Does the quote actually exist at the cited location, saying what the finding's premise needs it to say?

| Value | Meaning |
|---|---|
| `yes` | Quote appears verbatim (or near-verbatim with insubstantial OCR cleanup) at the cited location and supports the claim's premise. |
| `partial` | Quote exists but is paraphrased, misplaced, truncated in a way that changes meaning, or the location anchor is wrong. |
| `no` | Quote is fabricated or grossly misrepresented — does not appear in the paper in any recognisable form. |

### Axis 2 — `calibration`

Given the quote is real, does the stated evidence actually establish the claim at its stated strength?

| Value | Meaning |
|---|---|
| `supported` | The evidence establishes the claim as stated. |
| `overclaimed` | There is a real issue, but the finding overstates severity, scope, or certainty. |
| `unsupported` | The evidence does not establish the claim (misreading, style complaint, over-promoted nit). |

If `quote_verified == "no"`, set `calibration = "unsupported"` automatically.

**`overclaimed` is the value that earns its keep**: it is what discriminates a debate-hardened review (which walks back overconfident claims) from an aggressive single-pass one (which keeps them).

## Annotator output

Annotator writes a JSON file to `_evaluation/annotations/<blind_id>.json` with exactly this schema:

```json
{
  "blind_id": "BF001",
  "quote_verified": "yes | partial | no",
  "calibration": "supported | overclaimed | unsupported",
  "notes": "one-paragraph rationale; required for overclaimed and unsupported; optional otherwise"
}
```

No extra fields. Annotations with additional keys are accepted but the extras are ignored by the aggregator.

## Constraints

- **Read the paper.** Judgment against the finding alone is rejected; the rubric requires checking the quote against the inlined paper text.
- **Do not use external citations.** The rubric asks "is the finding supported by the paper?", not "is the underlying claim true in the literature." External-fact verification is a separate phase (`2_ranking/verification.md`).
- **Do not consult other findings.** Each annotation is independent. Correctness cannot depend on whether other findings in the same review are supported.
- **Do not try to identify the review version.** Blind IDs are intentionally uniform. Style-guessing the source is bias, not judgment.
- **OCR garbage in the quote does not by itself fail `quote_verified`.** Match on substance, not on character-level fidelity.
