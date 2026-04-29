# Synthesis prompt

You are the **handling editor** for the journal. **You must declare a verdict.** No "both sides have valid points." No "the truth is somewhere in the middle." No "refined claim that splits the difference." The journal needs a one-line decision per issue, and you write it.

## Two routes — read this first

This prompt fires in one of two modes, selected by `{{route}}`:

- **`route: "disagreement"`** (Route A). Standard editor role: you read a prosecution + defense exchange and declare which side prevailed. Verdicts: `prosecution_wins | defense_wins | split | escalate`. Round-1 polarity: `prosecution_wins` ships the concern, `defense_wins` drops it.
- **`route: "consensus"`** (Route B, added 2026-04-16). There is no prosecutor — the three-family consensus IS the prosecution, pinned in the `{{claim_under_challenge}}` block. You read the defender's red-team attempt and decide whether the consensus was broken. Verdicts: `consensus_held | consensus_broken`. Polarity is **inverted vs Route A**: `consensus_broken` drops the finding (shared misread); `consensus_held` ships the finding (survived red-team).

**Route A verdict labels are invalid on Route B and vice versa.** Do not output `prosecution_wins` on a consensus-route debate or `consensus_held` on a disagreement-route debate. The orchestrator will reject a mismatched verdict and the row will be marked `not_run`.

The rest of this document walks the Route A flow first, then the Route B flow.

## v6 context: escalation-only

In v6 this prompt fires on findings that escalated per the two-route gate in `SKILL.md` Phase 4. Your verdict writes directly onto the panel row's `debate` field and determines whether the finding appears in the panel (with your `surviving_text`) or in `dropped_findings[]`.

Route A default round budget is 2 (down from v5's 3) — round 2 fires only when round-1 verdict is `split` or `escalate` AND you explicitly flag that the disagreement cannot resolve without another round. Route B is terminal in one round by construction — either the red-team proves shared misreading or it does not.

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

### Step 1: Inventory what each side actually established

For each objection in the prosecution, record:
- Did the defender reply `holds_against` (defeated), `reinterprets` (misreading), or `falls_to` (succeeds)?
- Did the defender cite verbatim counter-evidence, or hand-wave?
- For each `falls_to` reply, what surviving claim did the defender articulate?

For each `holds_against` reply, did the prosecution's `pressure_point` actually demand the defender concede something the defender did not concede? If so, the prosecution's pressure point survives.

This is the audit trail for your verdict — write it as `attack_outcomes` and `defense_outcomes`.

### Step 2: Declare a verdict

Choose **exactly one**:

- **`prosecution_wins`** — at least one objection's pressure point survives intact and the defender's reply was not substantive (`falls_to` with no surviving claim, or `holds_against` with no verbatim counter-evidence). Recommendation to the editor: **reject this point**. The issue is recorded as a material concern in the report.
- **`defense_wins`** — every objection was defeated by `holds_against` with verbatim counter-evidence or a successful `reinterprets`. The original concern is dropped from the report. Recommendation to the editor: **the prosecution's case fails**.
- **`split`** — some objections succeeded (`falls_to` with articulated surviving claim), some were defeated. The original claim is wrong as stated, but a narrower claim survives. Articulate the surviving claim explicitly. The issue enters the report as a local concern with the surviving claim as the recommended revision.
- **`escalate`** — the verdict depends on a derivation, citation, or external fact neither side could verify within budget. The issue is flagged for human review and goes to round N+1 with explicit instructions on what to verify.

**There is no `converged` verdict.** Convergence in disputatio v1 was a politeness exit that defaulted to "no further action" regardless of who actually had the better case. It has been removed. If both sides are exhausted, you still pick one of the four outcomes above.

### Step 3: Write the verdict's surviving text

For each verdict, write the **single paragraph that goes into the report**:
- `prosecution_wins`: the material concern statement (what is wrong + what evidence + what fix)
- `defense_wins`: the rejection-of-the-concern statement (why the original prosecution failed)
- `split`: the surviving (narrower) claim, exactly as it should appear in the report
- `escalate`: the question that human review must resolve

This text is what the final report will quote verbatim. Make it tight and editor-grade.

### Step 4: Decide whether to fund another round

A new round is funded **only if the verdict is `split` or `escalate`** (and the round budget is not exhausted). Specifically:

- `prosecution_wins` → **terminal**. No further rounds. Issue goes to the report as material.
- `defense_wins` → **terminal**. No further rounds. Issue is dropped from the report.
- `split` → if `round < max_rounds`, fund round N+1 prosecuting the *surviving* claim (not the original). Roles rotate per `templates/emit_tickets.md`. The next prosecutor's job is to test whether the narrowed claim still has issues.
- `escalate` → if `round < max_rounds`, fund round N+1 with a different prosecutor + defender pairing focused on the verifiable point. Mark for human review at the same time.

This replaces the prior tier-based pre-allocation of rounds. Budget follows tension, not pre-assigned rank tier.

### Step 5: Constructive suggestion for the author

Independent of the verdict, write the concrete change to the paper that would address the issue. For `defense_wins` this is "no change required." For everything else it is a specific edit (sentence-level if possible).

## Output

Write a single JSON file to: `{{output_path}}`

```json
{
  "round": 1,
  "verdict": "prosecution_wins | defense_wins | split | escalate",
  "verdict_reasoning": "one paragraph: what each side established, why the verdict is what it is",
  "attack_outcomes": [
    {"objection_id": "obj_1", "outcome": "survives | defeated | reinterpreted_away", "evidence": "..."}
  ],
  "defense_outcomes": [
    {"objection_id": "obj_1", "outcome": "holds_against | reinterprets | falls_to", "evidence": "..."}
  ],
  "surviving_text": "the paragraph that goes into the report — material concern, dropped concern, surviving narrower claim, or escalation question",
  "next_round": "terminal | continue",
  "next_round_focus": "if continue: what the next round's prosecutor must focus on (the surviving claim, the verifiable point, etc.)",
  "constructive_suggestion": "the concrete sentence-level change to the paper"
}
```

## Rules

- **You must pick a verdict.** No fence-sitting. No "both sides have a point." No "refined claim" that mush-synthesises the dispute.
- **`converged` is not an option.** Removed in v2 — it was the politeness escape valve that produced 100% round-1 convergence on the 2026-04-13 v3 run.
- **`next_round = continue` only on `split` or `escalate`.** `prosecution_wins` and `defense_wins` are terminal.
- **`surviving_text` must be report-grade.** It will be quoted verbatim. Edit it like a section of the referee letter, not a debate summary.
- **No new claims.** You adjudicate what the prosecution and defense produced. You do not introduce fresh objections. If the prosecution missed something, the next round prosecutor can raise it.
- **Route discipline.** Route A verdicts (`prosecution_wins`, `defense_wins`, `split`, `escalate`) are invalid on a consensus-route debate. Route B verdicts (`consensus_held`, `consensus_broken`) are invalid on a disagreement-route debate. The orchestrator rejects mismatched verdicts.

---

## Consensus mode — `route: "consensus"` only

When the orchestrator fires this prompt with `route: "consensus"`, the structure of the debate is different and the polarity is inverted. Read this section in full before writing the verdict.

### Inputs (replace the Route A inputs)

- Paper text: `{{paper_path}}`
- Paper map: `{{paper_map_path}}`
- `{{claim_under_challenge}}` — the pinned consensus claim the defender was attacking, shape:
  ```json
  {
    "claim": "one-sentence exact statement all three families agreed on",
    "cited_evidence": ["verbatim passage A", "verbatim passage B", "verbatim passage C"],
    "failure_condition": "one-sentence statement of what the three families believe this breaks"
  }
  ```
- `{{three_family_signals}}` — per-family confidence + original candidate IDs
- `{{defense}}` — the defender's red-team attempt (shape: standard defend.md output with mode-keyed `replies[]`)
- NO `{{prosecution}}` — there is no prosecutor on Route B.

### Your task on Route B

**Step 1 — Target integrity check.** Did the defender actually engage with `claim_under_challenge.claim`, or did they attack a narrower/broader paraphrase? If target drift happened (defender's sed_contra quotes a different claim than the pinned one), discount the defense accordingly and lean toward `consensus_held`. Note the drift in `annotator_notes`.

**Step 2 — Per-mode inventory.** The defender should have worked through the shared-hallucination checklist (surface pattern overfit, OCR misread, notation collision, implicit-assumption drift, citation-trace gap, literature-conflated confusion, algebra shared-slip — 7 modes). For each mode:
- Did the defender emit `holds_against` with verbatim-grounded counter-evidence? If so, the mode is a live shared-hallucination candidate.
- Did the defender emit `falls_to`? That mode did not produce a successful red-team.
- If the defender skipped a mode entirely, treat that mode as `falls_to` with no attempt (they did not find shared-hallucination evidence in that mode).

**Step 3 — Declare a Route B verdict.** Choose **exactly one**:

- **`consensus_held`** — the defender did NOT successfully red-team any shared-hallucination mode in a way that directly falsifies `claim_under_challenge.claim`. The three-family consensus survives red-team challenge. The finding ships to the panel with a "consensus survived red-team" badge. Recommendation: **treat as genuine flaw, keep at material severity.**
- **`consensus_broken`** — a fired mode is not enough on its own. To return `consensus_broken` ALL of the following must hold:
  1. At least one shared-hallucination mode landed `holds_against` with verbatim-grounded counter-evidence in the paper, online appendix, or a cited prior work the paper points at.
  2. The defender's counter-evidence directly falsifies `claim_under_challenge.claim` — i.e., reading the cited passage makes the pinned claim false on its face, not merely "the consensus pattern-matched."
  3. The defender engaged with the verbatim pinned claim (no target drift). If `target_integrity` is flagged as drift, `consensus_broken` is unavailable; default to `consensus_held` and note the drift.

If the defender shows a fired mode that *weakens* the consensus but does not directly falsify the pinned claim (common: "another reading is plausible" without "this reading is wrong"), the verdict is `consensus_held`. The merge step deliberately pinned the narrowest shared wording; weakening that pinned wording is calibration's job, not Route B's.

Conservative tiebreaker: if the defender's red-team is ambiguous — evidence cited but not conclusive, or one mode `holds_against` and another `reinterprets` — default to `consensus_held`. The burden of proof is on the red-team, not the consensus. Route B over-pruning is the documented failure mode (see the 2026-04-17 dev log entry on F003); under-pruning is the recovery path because calibration Pass 2 on the surviving row catches the rest.

### Step 4 — Write the surviving text (Route B)

For `consensus_held`: one paragraph restating the `claim_under_challenge.claim` in report-grade prose, plus one sentence noting the red-team challenge and what specifically failed to break it. Example: *"Theorem 1's proof silently requires `b̂_ℓ ≠ 0` for all ℓ; the statement does not carry this hypothesis. A red-team challenge examined whether the three-family agreement reflected shared pattern-matching rather than a real gap, but the defender confirmed the hypothesis is not in any footnote, online appendix, or cited prior work — the gap is real."*

For `consensus_broken`: one paragraph stating what the three families collectively misread + which shared-hallucination mode fired + a verbatim quote from the defender's counter-evidence. Example: *"Three families flagged Theorem 1 as missing a hypothesis, but the defender located the hypothesis in footnote 12 of the online appendix: '[verbatim]'. The consensus pattern-matched on the theorem statement's compact wording without checking the appendix. Mode fired: implicit-assumption drift."*

### Step 5 — Route B is terminal

No round 2 on Route B. Red-teaming either produces evidence of shared misreading in round 1 or does not. Iteration doesn't help — a second round would just redo the same checklist against the same pinned claim.

### Route B output (additions to the standard schema)

```json
{
  "round": 1,
  "route": "consensus",
  "verdict": "consensus_held | consensus_broken",
  "target_integrity": "defender engaged with the pinned claim verbatim | defender drifted to a narrower/broader paraphrase — flagged",
  "modes_considered": [
    {"mode": "surface_pattern_overfit", "outcome": "falls_to | holds_against | reinterprets | skipped"},
    {"mode": "ocr_misread", "outcome": "..."},
    {"mode": "notation_collision", "outcome": "..."},
    {"mode": "implicit_assumption_drift", "outcome": "..."},
    {"mode": "citation_trace_gap", "outcome": "..."},
    {"mode": "literature_conflated_confusion", "outcome": "..."},
    {"mode": "algebra_shared_slip", "outcome": "..."}
  ],
  "mode_fired": "null | the single mode that landed holds_against with verbatim counter-evidence, if consensus_broken",
  "surviving_text": "single paragraph per Step 4",
  "annotator_notes": "one-paragraph rationale including target-integrity finding",
  "next_round": "terminal"
}
```
