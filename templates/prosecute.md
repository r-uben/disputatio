# Prosecution prompt

You are prosecuting a specific issue about an academic paper in a formal debate. Your job is to produce **objections** that the defender will be forced to reply to individually. Follow the structured disputation format described in `templates/methods/m1_disputation.md`.

## Inputs

- Paper text: `{{paper_path}}`
- Paper map: `{{paper_map_path}}`
- Issue state: the current claim, evidence, and any history from previous rounds (injected inline below)
- Round number and previous history (injected inline)
- Method templates: `templates/methods/m2_contradiction.md` through `m6_disentangling.md`

## Current issue state

{{issue_state}}

## Prior rounds (if any)

{{history}}

## Your task

### Step 1: Formulate the quaestio

State the point under debate as a precise yes/no question. If this is round 1, the quaestio is derived from the issue's claim. If this is a later round, the quaestio is derived from the refined claim from the previous synthesis.

### Step 2: Pick 2-3 methods

Based on the type of issue, select **two methods** from M2-M6 that are most likely to produce strong objections. Add a third if the issue is in the top third of debated issues by rank score. Use this selection guide:

- **Internal inconsistency, text-vs-model mismatch**: M2 + M5
- **Theorem scope, boundary failure, hidden assumption**: M3 + M4
- **Causal identification, calibration, omitted variable, mechanism**: M5 + M6
- **Empirical proxy, variable construction, measurement**: M3 + M6
- **Overclaiming, rhetorical stretch, interpretive drift**: M5 + M3

State which methods you selected and why.

### Step 3: Apply each method to the issue

For each selected method, follow its procedure (see its template file) **focused on this specific issue**. You are not re-discovering the paper — you are deepening the attack on this particular point.

### Step 4: Produce independent objections

Combine the outputs of the selected methods into independent objections — as many as the issue warrants, but never fewer than the number of methods selected. Each objection must:
- Come from a different angle (not three restatements of the same point)
- Have its own chain of reasoning
- Cite a specific passage or equation in the paper
- State what would force the defender to concede (the "pressure point")

### Step 5: Anticipate the strongest defense

For each objection, write one sentence describing the best defense the author could offer. This is not part of the objection — it is a check that the objection is not vulnerable to a one-line rebuttal. If an objection has an easy defense, refine it before submitting.

### Step 6: State your honest confidence

For each objection, label your confidence: `high`, `medium`, or `low`. Do not inflate — a honestly-labeled weak objection is more useful than a falsely-confident strong one.

### Step 7: State your falsifier

For each objection, state what evidence from the paper or external sources would force you to withdraw the objection. This is required. An objection with no falsifier is rhetoric, not argument.

## Output

Write a single JSON file to: `{{output_path}}`

```json
{
  "round": 1,
  "quaestio": "precise yes/no question derived from the issue's claim",
  "methods_selected": ["m2", "m5"],
  "methods_selection_reasoning": "why these methods are the right tools for this issue type",
  "objections": [
    {
      "id": "obj_1",
      "objection": "...",
      "reasoning": "...",
      "cited_passage": {
        "quote": "...",
        "location": "..."
      },
      "pressure_point": "what evidence would force the defender to concede",
      "anticipated_defense": "the best defense the author could offer",
      "confidence": "high | medium | low",
      "falsifier": "what would make me withdraw this objection"
    }
  ],
  "web_evidence": [
    {
      "source": "url or paper citation",
      "relevance": "how this supports an objection"
    }
  ]
}
```

`web_evidence` is optional and only used if the prosecution incorporated web-verified external evidence.
