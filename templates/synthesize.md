# Synthesis prompt

You are synthesizing a completed debate round. Follow the iterative refinement procedure described in `templates/methods/m7_refinement.md` exactly. Your output is the input to the next round (or the final state if this round converges).

## Inputs

- Paper text: `{{paper_path}}`
- Paper map: `{{paper_map_path}}`
- Issue state before the round (injected inline)
- Prosecution from this round (injected inline)
- Defense from this round (injected inline)
- Prior rounds (if any, injected inline)

## Current issue state

{{issue_state}}

## This round's prosecution

{{prosecution}}

## This round's defense

{{defense}}

## Prior rounds (if any)

{{history}}

## Your task

Execute Method 7 (Iterative Refinement). Do not skip steps.

### Step 1: Write down the original claim

Copy the issue's current claim as it entered this round. Not paraphrased — exact.

### Step 2: Inventory what the attack established

For each objection in the prosecution:
- Did the objection produce **specific evidence** (a quote, an equation, a citation)? If yes, that evidence is now on the record.
- Did the defender **concede** the objection? If yes, the concession is now on the record.
- Did the objection **survive the reply**? If yes, the objection is live.

List these as `attack_established`.

### Step 3: Inventory what the defense established

For each reply in the defense:
- Did the reply produce **specific counter-evidence**? If yes, that evidence is on the record.
- Did the reply **successfully answer** the objection (by re-interpretation or counter-evidence)? If yes, that objection dies.
- Did the reply **concede**? If yes, the respondeo is weakened at that point and the concession is on the record.
- Did the defense pass the **self-commitment check**? If yes, the paper demonstrably honors the commitment the objection claimed it violated.

List these as `defense_established`.

### Step 4: Identify surviving ground

List facts **both sides now agree on**. This is `accepted_facts`. These should be precise statements backed by evidence that neither side contests.

### Step 5: Identify refuted components

List parts of the original claim that **neither side defends** after the round. This is `refuted_components`. It may include:
- Parts the defense conceded and the prosecution dropped
- Parts the defense disproved and the prosecution abandoned
- Overstatements both sides now agree were too strong

### Step 6: Identify open disputes

List disputes that **remain unresolved** after the round. This is `open_disputes`. Each entry is a one-sentence statement of a specific point both sides still disagree on.

### Step 7: Write the refined claim

Construct the strongest version of the original claim that is consistent with `accepted_facts` and not touched by `refuted_components`. Rules:
- The refined claim must be **honest**, not rhetorically strong
- Hidden assumptions exposed by the attack must appear as **explicit conditions** in the refined claim
- If the scope of the original was too broad, the refined claim must **narrow the scope**
- If the core mechanism survived, **preserve it**; do not abandon it just because the periphery was weakened

### Step 8: Assess materiality

Label the refined claim's impact:
- `material` — affects the paper's central results or main interpretation
- `local` — affects a specific passage or calibration but not the core
- `none` — the debate resolved the issue; nothing further needed

### Step 9: Decide next step

Choose exactly one:
- `continue` — the refined claim is materially different from the original and new objections can be raised. A new round begins with rotated roles.
- `converged` — the refined claim is stable. Both sides have established their positions. Debate ends.
- `split` — the original issue contained multiple independent propositions. Split them into child issues that each enter debate independently. List the child issues in `split_into`.
- `escalate` — the debate depends on information neither side can verify. Mark for human review.

### Step 10: Write a constructive suggestion

For the author: what concrete change to the paper would address the refined claim? This is not "the paper is wrong" — it is "this would fix it." Even if the refined claim has `impact: none`, a constructive presentation improvement may still be worth stating.

## Output

Write a single JSON file to: `{{output_path}}`

```json
{
  "round": 1,
  "original_claim": "...",
  "attack_established": [
    {"item": "...", "evidence": "..."}
  ],
  "defense_established": [
    {"item": "...", "evidence": "..."}
  ],
  "accepted_facts": ["..."],
  "refuted_components": ["..."],
  "open_disputes": ["..."],
  "refined_claim": "the strongest honest version of the claim",
  "impact": "material | local | none",
  "status": "continue | converged | split | escalate",
  "constructive_suggestion": "how the author could fix this",
  "split_into": null,
  "reasoning": "one paragraph explaining how the refinement was constructed"
}
```

## Rules

- **Do not pick a winner.** You are not judging. You are producing a refined understanding that incorporates what both sides established.
- **Be honest about weakening.** A refined claim weaker than the original is correct — a weaker true claim is worth more than a stronger false one.
- **Do not hand-wave.** Every item in `attack_established` and `defense_established` must cite specific evidence from the prosecution or defense.
- **Do not synthesize into mush.** "Both sides have a point" is not a synthesis. You must produce a concrete refined claim.
