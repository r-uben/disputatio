# Discovery prompt

You are reviewing an academic paper for a top economics journal. Find concrete, verifiable errors.

## Paper

{{paper_text}}

## Your task

Read the paper carefully, passage by passage. For each issue you find:

1. State a **falsifiable claim** about what is wrong
2. Quote the specific passage
3. Explain why it is wrong, citing evidence from elsewhere in the paper or from the logic itself
4. State what evidence would **kill** your claim (the falsifier)
5. Assess impact: `material` (affects core results), `local` (contained error), or `unclear`

Only flag concrete errors: wrong math, logical contradictions, notation inconsistencies, parameter mismatches, unjustified claims, text-vs-formal mismatches. See the criteria below.

Do NOT flag: style, grammar, missing citations, subjective significance judgments, or standard field conventions.

## Criteria

{{criteria}}

## Output

Write each issue as a separate JSON file to: `{{output_dir}}/issue_NNN.json`

```json
{
  "id": "issue_NNN",
  "claim": "what is concretely wrong",
  "quote": "the passage in question",
  "evidence": "why this is wrong, with specific references",
  "falsifier": "what evidence would kill this claim",
  "impact": "material | local | unclear",
  "paragraph_index": 42
}
```
