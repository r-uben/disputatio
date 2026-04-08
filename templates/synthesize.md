# Synthesis prompt

You are synthesizing a dialectic round about an academic paper. A prosecutor argued the criticism is valid; a defender argued it is not. Your job is to produce **a refined understanding** — not pick a winner, but resolve the tension into something better than either side alone.

## Paper context

{{context}}

## Current issue state

{{issue_state}}

## This round

**Prosecution:**
{{prosecution}}

**Defense:**
{{defense}}

## Prior rounds (if any)

{{history}}

## Your task

Produce an updated issue state. This is NOT a verdict — it is a synthesis:

1. What facts are now **accepted** by both sides?
2. What components of the original claim have been **refuted**?
3. What **disputes remain** open?
4. What is the **best current formulation** of the issue, incorporating what both sides contributed?
5. What single question would **most reduce remaining uncertainty**?
6. Should the debate continue, or has it converged?

If the issue actually contains multiple independent propositions that are being conflated, you may **split** it — set status to `split` and provide the child issues.

If the dispute depends on information the agents cannot verify (external data, hidden derivations, field-specific conventions that require domain expertise), set status to `escalate`.

## Output

Write your response as JSON to: `{{output_path}}`

```json
{
  "current_claim": "best current formulation of the issue",
  "accepted_facts": ["what both sides now agree on"],
  "refuted_components": ["parts of the prior claim that died"],
  "open_disputes": ["what remains unresolved"],
  "impact": "material | local | none | unclear",
  "next_question": "what would most reduce uncertainty",
  "status": "continue | converged | split | escalate",
  "constructive_suggestion": "how the authors could fix this, if applicable",
  "split_into": null,
  "reasoning": "one-paragraph explanation of how you reached this synthesis"
}
```
