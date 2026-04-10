# Discovery prompt

You will run one generative method on the paper using your paper map as the cache.

## Inputs

- Paper text: `{{paper_path}}`
- Paper map: `{{paper_map_path}}`
- Method: {{method_content}}

## Your task

Apply the method's procedure to the paper, using the paper map as your starting index. Collect every finding into a single output file.

## Output

Write a single JSON file to: `{{output_path}}`

The file contains all issues found by this method:

```json
{
  "issues": [ ... ]
}
```

## Issue schema

Every issue uses the same schema:

```json
{
  "id": "m5_issue_003",
  "method": "m5",
  "claim": "a falsifiable statement of what is wrong",
  "quote": "exact quote from the paper",
  "quote_location": "section/paragraph reference",
  "evidence": "detailed reasoning for why the claim is correct, including any supporting quotes",
  "falsifier": "what evidence would force you to withdraw this issue",
  "impact": "material | local | unclear",
  "confidence": "high | medium | low",
  "paper_commitment": null,
  "paper_commitment_location": null,
  "needs_web_verification": false,
  "verification_query": null
}
```

Notes:
- `paper_commitment` and `paper_commitment_location` are used by Method 5 (self-measured critique) to record the specific commitment being violated. Other methods can leave them null.
- `needs_web_verification` should be `true` if the issue requires checking a citation, an external data source, or an institutional fact. In that case, `verification_query` should state what to search for. A later pass will run web verification.
- `confidence` is your own assessment: are you sure this is a real issue, or is it a candidate that deserves debate?

## OCR warning

The paper may contain OCR artifacts — hallucinated text blocks, garbled formulas, injected content from unrelated documents. These are **not paper content** and must not be treated as errors in the paper. If a suspicious passage could be an OCR artifact, do not flag it; instead note it in the paper map's `ocr_corrupted_sections` if it isn't already there.

## Method priority

All five methods must be run, but they have different strengths:
- **M2 (contradictions)**: best for papers with many interacting claims
- **M3 (transformations)**: mechanical, always productive, no creativity required
- **M4 (counterexamples)**: best for papers with formal propositions
- **M5 (self-measured)**: produces the highest-quality, most robust findings
- **M6 (causal disentangling)**: best for empirical/interpretive sections

Do not cut corners on any method. The value of disputatio comes from running all five.
