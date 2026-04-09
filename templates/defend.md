# Defense prompt

You are defending an academic paper against a set of objections. The defense follows the scholastic disputation format described in `templates/methods/m1_disputation.md`: you must write a sed contra, a respondeo, and **reply to every objection individually**. You cannot dismiss the objections with a single general counter-argument.

## Inputs

- Paper text: `{{paper_path}}`
- Paper map: `{{paper_map_path}}`
- Issue state (injected inline)
- Prosecution (injected inline): the quaestio and the list of objections
- Prior rounds (if any, injected inline)

## Current issue state

{{issue_state}}

## Prosecution

{{prosecution}}

## Prior rounds (if any)

{{history}}

## Your task

### Step 1: Write the sed contra

State the single strongest reason to believe the affirmative answer to the quaestio despite the objections. Typically this is a passage from the paper that directly supports the position. One sentence.

### Step 2: Write the respondeo

Provide the paper's best case on this point. Ground it in specific passages. This is not a rebuttal of the objections — it is a positive statement of the author's position, as strong as it can honestly be.

### Step 3: Reply to each objection individually

**This is the most important step.** For every objection in the prosecution, write a specific reply. There are only four valid reply types:

1. **Concede** — the objection is correct. State this honestly. If you concede, note how the respondeo must be weakened to accommodate the concession.

2. **Answer with counter-evidence** — cite a specific passage, equation, or external source that directly refutes the objection. Hand-waving is not allowed. Every counter-evidence reply must include an exact quote.

3. **Answer by re-interpretation** — show that the objection is based on a misreading of the passage. Cite the intended reading with evidence from elsewhere in the paper that supports it.

4. **Survive** — the objection has force but does not defeat the core claim. Explain exactly what part of the claim the objection weakens and what part it leaves intact.

You may not reply "this is a minor point." Every reply must be specific.

### Step 4: Use the self-commitment check in reverse

If any objection is a self-measured critique (M5), apply M5 in reverse: find the passage where the paper **does** honor the commitment. If you cannot find such a passage, you must concede the objection.

### Step 5: State your honest confidence

For each reply, label your confidence in it: `high`, `medium`, or `low`. A labeled weak reply is better than an inflated strong one.

### Step 6: State what would break the defense

At the top level, state the single piece of evidence that would force you to concede the entire issue. This is the defense's falsifier — the equivalent of the prosecution's pressure point.

## Output

Write a single JSON file to: `{{output_path}}`

```json
{
  "round": 1,
  "sed_contra": "The strongest one-sentence reason the paper's position holds despite the objections",
  "respondeo": "The paper's best positive case, with citations",
  "replies": [
    {
      "objection_id": "obj_1",
      "reply_type": "concede | counter_evidence | reinterpret | survive",
      "reply": "specific response",
      "cited_passage": {
        "quote": "...",
        "location": "..."
      },
      "concession_notes": "if conceded, how the respondeo must be weakened",
      "confidence": "high | medium | low"
    }
  ],
  "commitment_check_passed": true,
  "commitment_check_evidence": "if the objection cited a violation of a paper commitment, show where the paper upholds that commitment",
  "defense_falsifier": "the single piece of evidence that would defeat the entire defense",
  "web_evidence": [
    {
      "source": "url or citation",
      "relevance": "how this supports the defense"
    }
  ]
}
```

## Rules

- **No hand-waving.** Every reply must cite evidence. "The paper addresses this" without a quote is invalid.
- **No inflated confidence.** If you cannot find counter-evidence, concede honestly. A weak defense is better than a false-confident one.
- **Every objection gets a reply.** Skipping an objection is equivalent to conceding it.
- **Use web search when the objection references external facts.** If the objection depends on a citation or external claim, verify it before replying.
