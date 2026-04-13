# Evaluate prompt — single finding

This template is the **prompt body** sent to an annotator agent for one finding. It is the operational counterpart to `templates/evaluation.md`, which describes the evaluation protocol; this file is what Claude actually substitutes into per-finding tickets at emit time.

The annotator never sees the orchestrator's metadata: which agent surfaced the finding, which method (M0–M6) found it, the cross-agent support score, or the merge ranking. All of that is stripped before the prompt is built. The annotator gets the paper and the finding's substantive content (claim, quote, quote_location, evidence) and judges those against the paper alone.

## Inputs

- Paper text: `{{paper_path}}` (read this in full; do not skim)
- Finding payload: `{{payload_path}}` (one JSON file with the four fields below)

The payload is structured exactly as:

```json
{
  "claim":          "<one-sentence falsifiable statement of what the reviewer asserts>",
  "quote":          "<exact verbatim excerpt the reviewer pulled from the paper>",
  "quote_location": "<section / page / equation anchor the reviewer cited>",
  "evidence":       "<the reviewer's reasoning for why the claim follows from the quote>"
}
```

There is intentionally no `id`, no `agent`, no `method`, no `confidence`. Those are stripped at emit time. You are judging the finding on its own merits, not who made it.

## Your task

Produce one annotation JSON judging the finding on two axes. Be strict. Calibration matters more than charity.

### Axis 1 — `quote_verified`

Does the quote actually exist at the cited location, saying what the finding's premise needs it to say?

| Value | Meaning |
|---|---|
| `yes` | Quote appears verbatim (or near-verbatim with insubstantial OCR cleanup) at the cited location and supports the claim's premise. |
| `partial` | Quote exists but is paraphrased, misplaced, truncated in a way that changes meaning, or the location anchor is wrong. |
| `no` | Quote is fabricated, grossly misrepresented, or does not appear in the paper at all. |

Procedure: open the paper at the cited location. Match the quote against the paper text. If the location anchor is too vague to find, set `quote_verified = partial` and note it. If the quote is somewhere in the paper but the location is wrong, also `partial`. If the quote does not appear anywhere recognisable, `no`.

### Axis 2 — `calibration`

Given the quote is real, does the stated `evidence` actually establish the `claim` at its stated strength?

| Value | Meaning |
|---|---|
| `supported` | The evidence establishes the claim as stated. The objection, counterexample, or contradiction is demonstrable from the paper. |
| `overclaimed` | There is a real issue, but the finding overstates severity, scope, or certainty. The paper has a weakness here, but not the weakness as described. |
| `unsupported` | The evidence does not establish the claim. The finding is a misreading of the paper, a style/taste complaint dressed as a substantive flaw, or a methodological nit promoted beyond its actual impact. |

If `quote_verified == "no"`, set `calibration = "unsupported"` automatically — a finding without a real quote cannot be supported.

`overclaimed` is the value that earns its keep: it is what discriminates a debate-hardened review (which walks back overconfident claims) from an aggressive single-pass review (which keeps them). Use it whenever the quote is real and points at a real issue, but the claim is broader, sharper, or more severe than the evidence licenses.

## Output

Write a single JSON file to: `{{output_path}}`

```json
{
  "quote_verified": "yes | partial | no",
  "calibration":    "supported | overclaimed | unsupported",
  "notes":          "<short prose; required when calibration is overclaimed or unsupported, optional when supported>"
}
```

Notes:
- `notes` should be 1–4 sentences. For `overclaimed`, state what the actual weakness is and how the finding overstates it. For `unsupported`, state what the finding misreads. For `supported`, leave empty or note any caveat.
- Do not invent additional axes. The two-axis rubric is deliberate; an annotator that returns extra fields is rejected.
- If the paper's section anchors are sparse (long unnumbered prose), match by content rather than location and explain in `notes`.

## Constraints

- Read the paper. Do not annotate from the finding alone — the rubric requires checking the quote against the paper text.
- Do not use the paper's external citations to verify the finding. The rubric is "is the finding supported by the paper itself?", not "is the underlying claim true in the literature." External-fact verification is a separate phase (`2_ranking/web_verification.md`) that already ran.
- Do not consult other findings in the review. Each annotation is independent. If the rubric asks "is this supported?" the answer cannot depend on whether other findings in the same review are also supported.
- If the paper is OCR'd, OCR garbage in the quote does not by itself fail `quote_verified`. Match on substance, not on character-level fidelity.
