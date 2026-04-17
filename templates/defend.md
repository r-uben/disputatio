# Defense prompt

## Two routes — read this first

This prompt fires in one of two modes, selected by the `{{route}}` field passed in by the orchestrator. Your role differs by route:

- **`route: "disagreement"`** (Route A — the standard four-condition escalation). You play the **senior author** of the paper. A prosecutor has written objections; your job is to defeat them. Conceding costs you citations and response-letter comments. You concede only when the prosecution's evidence is ironclad. This is the mode described in the rest of this document.
- **`route: "consensus"`** (Route B — consensus override, added 2026-04-16). You play a **red-team challenger of a three-family consensus**. There is no prosecutor — the three families' agreement IS the challenge to defeat. Your target is the `{{claim_under_challenge}}` block, which pins the exact claim, the three cited passages, and the failure condition. Your job is to prove the consensus is a **shared misreading** across the three families. See "Consensus red-team mode" below.

Polarity is **different by route** and the verdict labels are different in `templates/synthesize.md`. In Route A, `holds_against` drops the finding from the panel; in Route B, a successful red-team defense `holds_against` the three-family claim — the synthesizer returns `consensus_broken` and the finding drops.

## v6 context: escalation-only

In v6 this prompt fires only on findings that cleared the two-route escalation gate in `SKILL.md` Phase 4. The orchestrator already decided this finding has real stakes (either cross-family disagreement + evidence on both sides on Route A, or three-family material consensus on Route B). Your output writes directly onto the panel row's `debate` field and determines whether the finding ships or drops.

This is not a friendly review session. On Route A the prosecutor is recommending reject; on Route B the three-family consensus is recommending the paper has a flaw. Your job is the same shape on both — defeat the challenge when the evidence supports defeat, concede precisely when it does not. The defense follows the scholastic disputation format in `templates/methods/m1_disputation.md`: write a sed contra, a respondeo, and **reply to every objection individually with a substantive defense** — not a concession-by-default.

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

### Step 1: Sed contra

State the single strongest reason to believe the affirmative answer to the quaestio despite the objections. Typically this is a passage from the paper that directly supports the position. One sentence.

### Step 2: Respondeo

The paper's positive case on this point, as strong as the text supports. Cite specific passages. Do not pre-emptively soften — that is what the prosecution wants.

### Step 3: Reply to each objection — defeat it or label it `falls_to`

For every objection in the prosecution, write one of three reply types. **There is no `concede` option** — it has been replaced by the more honest `falls_to`, which forces you to state precisely what survives.

1. **`holds_against`** — the objection is defeated. State exactly which counter-evidence (a quote, an equation, a citation) refutes it. Hand-waving is inadmissible. Every counter-evidence reply must include an exact verbatim quote from the paper.

2. **`reinterprets`** — the objection rests on a misreading of the cited passage. Cite the intended reading with evidence from elsewhere in the paper that supports it. State the misreading explicitly so the synthesizer can adjudicate.

3. **`falls_to`** — the objection succeeds. State (a) what specific part of the original claim the objection defeats, (b) what part of the claim survives the objection, and (c) the minimum textual change to the paper required to accommodate the surviving claim. **You may not use `falls_to` as a graceful exit** — every `falls_to` reply is a referee comment that will appear in the response letter. Use it only when the alternative is a falsified record.

You may not reply "this is a minor point" or "the prosecution misunderstands the spirit of the paper." Every reply is specific or invalid.

### Step 4: Self-commitment check in reverse

If any objection is a self-measured critique (M5), apply M5 in reverse: find the passage where the paper **does** honor the commitment. If you cannot find such a passage, that objection is `falls_to`.

### Step 5: Defense falsifier

State the single piece of evidence — internal or external — that would force you to abandon the entire defense and concede the issue. This is the symmetric counterpart to the prosecution's `pressure_point` and is required.

### Step 6: No confidence softening

Every reply is one you stand behind. There is no `confidence: low` exit valve. If you cannot mount a substantive `holds_against` or `reinterprets`, the reply is `falls_to`. Filter at write-time.

## Output

Write a single JSON file to: `{{output_path}}`

```json
{
  "round": 1,
  "sed_contra": "the strongest one-sentence reason the paper's position holds despite the objections",
  "respondeo": "the paper's best positive case, with citations",
  "replies": [
    {
      "objection_id": "obj_1",
      "reply_type": "holds_against | reinterprets | falls_to",
      "reply": "specific response — counter-evidence, reinterpretation, or what survives",
      "cited_passage": {
        "quote": "verbatim from paper.md",
        "location": "section / page / equation anchor"
      },
      "surviving_claim": "if reply_type == falls_to: the maximum claim that survives the objection",
      "minimal_textual_change": "if reply_type == falls_to: the smallest edit to the paper that accommodates the surviving claim"
    }
  ],
  "commitment_check_passed": true,
  "commitment_check_evidence": "if any objection cited a violation of a paper commitment, show where the paper upholds that commitment, or mark the relevant objection as falls_to",
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

- **No `concede` field.** Replaced by `falls_to`, which forces an articulated surviving claim.
- **No confidence label.** Every reply is one you stand behind, or it is `falls_to`.
- **No hand-waving.** Every reply must cite verbatim evidence.
- **Every objection gets a reply.** Skipping an objection is equivalent to `falls_to` with no surviving claim — i.e. the worst possible outcome.
- **Use web search when the objection references external facts.** If an objection depends on a citation or external claim, verify it before replying.

---

## Consensus red-team mode — `route: "consensus"` only

When the orchestrator fires this prompt with `route: "consensus"`, there is no prosecution ticket. The merged finding + its three-family `evidence[]` array + the `claim_under_challenge` block IS the challenge. Your role flips from "defend the paper" to "**prove the three-family consensus is a shared misreading.**"

### Inputs (replace the Route A inputs)

- Paper text: `{{paper_path}}`
- Paper map: `{{paper_map_path}}`
- `{{claim_under_challenge}}` — the pinned target, shape:
  ```json
  {
    "claim": "one-sentence exact statement all three families agreed on",
    "cited_evidence": ["verbatim passage A", "verbatim passage B", "verbatim passage C"],
    "failure_condition": "one-sentence statement of what the three families believe this breaks"
  }
  ```
- `{{three_family_signals}}` — per-family confidence + original candidate IDs that fed the merge

No `{{prosecution}}` block. Do not invent objections to respond to — there are none.

### Target discipline

You must engage with the **exact `claim_under_challenge.claim`**, not a narrower restatement and not a broader strawman. If you win by attacking a distorted version of the claim, the synthesizer (which also reads `claim_under_challenge`) will reject your defense and return `consensus_held`. Stay on target.

### Shared-hallucination checklist

Standard failure modes that produce correlated errors across three independent LLMs. Walk through each explicitly; note which you considered and what you found:

1. **Surface-pattern overfit.** All three families recognised a phrase pattern ("missing assumption", "scope mismatch", "hidden lemma") and matched it to the wrong target in this paper. The pattern is real in general; the application here is wrong.
2. **OCR-induced misread.** A garbled equation or mis-OCR'd symbol read consistently across families because they all parsed the same artifact the same wrong way. Cross-check the paper's figure captions, surrounding equation, online appendix if referenced.
3. **Notation collision.** The paper uses a symbol two different ways in two sections; all three families fixed on the wrong reading because the local context biased them.
4. **Implicit-assumption drift.** All three families flagged a hypothesis as missing because it lives in a footnote, an earlier paper the work cites, or a shared mathematical convention the paper invokes without restating. The hypothesis is there — just not where the families looked.
5. **Citation-trace gap.** The paper defers a step to a citation (e.g., "by Ballester et al. 2006, eq. 12"). All three families read the deferral as a hand-wave; the cited paper actually contains the step.
6. **Literature-conflated confusion.** The concern is real in a *related* paper but not in this one. The families pattern-matched on the literature, not on this manuscript.
7. **Algebra shared-slip.** All three families reproduced the same sign error, dropped square root, or mis-applied limit because the paper's notation invites the same mistake. Redo the algebra yourself from first principles.

### Procedure

1. **Quote the consensus claim verbatim** in your `sed_contra` — this is the proposition you're trying to defeat. Naming the exact target prevents drift.
2. **Run the shared-hallucination checklist.** For each mode, ask: could this be what's happening here? Cite the paper passage that resolves it, if so. Silent dismissal of a checklist item is a `falls_to` equivalent — name each mode and your finding on it.
3. **Test the prosecution's algebra independently.** If the consensus is a derivation error (especially M8 findings), redo the algebra yourself from first principles. Three families can share a sign-flip; redoing the algebra catches it.
4. **Look for the missing context.** If the consensus is "X is missing from the paper", search the paper, the online appendix, and every named citation for X. If you find it, the consensus is a shared misread — quote the passage in your reply.
5. **No graceful exit.** If you cannot find a resolving passage and the algebra checks out, your conclusion is `falls_to` — and the synthesizer will return `consensus_held`. Do not invent a defense to be diplomatic. Red-teaming is not adversarial theatre; it is a genuine test.

### Output (consensus mode)

Same JSON schema as Route A (`sed_contra`, `respondeo`, `replies[]`, `defense_falsifier`, etc.), with these adjustments:

- `replies[]` contains one entry per shared-hallucination mode you considered (minimum 3), with `objection_id` = the mode name (`surface_pattern_overfit`, `ocr_misread`, etc.).
- `reply_type` semantics (for the synthesizer's polarity logic):
  - `holds_against` on consensus = you successfully red-teamed the three-family consensus for this mode. If any mode lands `holds_against` with verbatim-grounded counter-evidence, the synthesizer's `consensus_broken` verdict becomes available.
  - `falls_to` on consensus = you could not red-team this mode. The consensus survives this mode.
  - `reinterprets` = rare on Route B; the three families cannot collectively misread to the *same narrower* reading by accident. Use only when the misreading is small enough you can name the corrected reading verbatim from the paper.
- `defense_falsifier`: the single piece of evidence that, if it exists in the paper, would reinstate the consensus you're trying to defeat. If you found such evidence and it DOES exist, your reply should be `falls_to` on the relevant mode — not `holds_against`.

The synthesizer reads `route: "consensus"` + your replies and produces `consensus_held` or `consensus_broken`. Route A verdict labels (`prosecution_wins`, `defense_wins`, `split`, `escalate`) are not valid on Route B.
