# Claim validity audit prompt (v8.1, Phase 2.5b — new)

For each triaged candidate, audit whether the paper's present formal object actually supports the claimed property **under the paper's own definitions**. This is the wrong-but-present pass — the paper provides the object; the audit asks whether the object does the work.

This template runs once per family on the candidates that survived triage (`templates/claim_triage.md`). The output is structured per-claim audit records that feed the global integrator (`templates/claim_validity_integrate.md`) and ultimately the calibrator (`templates/claim_validity_calibration.md`).

## Inputs

- Paper text: `{{paper_path}}`
- Triage output (your own): `{{triage_path}}` — list of audit-worthy candidates with `present_object`, `claim`, `object_location`, etc.
- Paper map (your own): `{{paper_map_path}}` — for cross-referencing definitions and propositions

## Task

Produce a single JSON file at `{{output_path}}`:

```json
{
  "family": "anthropic | openai | google",
  "audits": [
    {
      "id": "CV_001",
      "candidate_id": "CV_TRIAGE_NNN",
      "claim": "the asserted property the paper makes",
      "claim_location": "section / theorem / equation anchor",
      "present_object": "the formal object the paper provides",
      "object_location": "where the formal object lives",
      "asserted_property": "what the paper says the object establishes",
      "required_inference": "the logical step from object to claim — what would have to be true for the present object to actually support the asserted property",
      "paper_definitions_used": [
        {
          "name": "the definition / lemma / axiom name from the paper",
          "location": "section / equation anchor",
          "quote_or_paraphrase": "what the paper actually says (paraphrase if filter-blocked)"
        }
      ],
      "validity_status": "valid | partial | invalid | unclear",
      "failure_mode": "wrong_conditioning | aggregation_error | topology_order_confound | likelihood_loglikelihood_mismatch | equivalence_only_restates | hidden_quantifier_shift | novelty_exceeds_formal | scope_creep | other",
      "failure_mode_other_description": "if failure_mode == other: name the pattern in 1 sentence",
      "minimal_witness": "the smallest concrete construction showing the failure — counterexample within the paper's own setup, redefinition, computation that contradicts the claim, or unanticipated case the claim does not cover",
      "consequence_if_wrong": "1-2 sentences on what downstream claim/method/result fails or weakens",
      "benign_interpretation_considered": "1-2 sentences on the most charitable reading of the paper that would save the claim, and why that reading does not apply",
      "confidence": "high | medium | low"
    }
  ]
}
```

## How to work

### Primary instruction

For each triaged candidate, ask:

> **Given the paper's stated definitions, does the present formal object actually support the claimed property?**

Use the paper's own definitions, lemmas, axioms — not external machinery. The audit's authority comes from the paper's internal logic. If you have to import a definition the paper does not use, the audit is invalid.

### Failure-mode probes (look for, don't restrict to)

These eight patterns are common, not exhaustive. If you detect a different pattern, set `failure_mode: other` and name it in `failure_mode_other_description`.

- **`wrong_conditioning`** — the present object conditions on too much or too little (Stephens #8 example: non-varying-sites paragraph conditions on a richer event than it should).
- **`aggregation_error`** — counts or sums aggregate two distinct things (Stephens #10 example: tree count mixes topology with merger order).
- **`topology_order_confound`** — combinatorial accounting confuses set membership with ordering or labeling.
- **`likelihood_loglikelihood_mismatch`** — argument is correct on one scale but the paper uses the other; constants, monotonicity, or asymptotics shift.
- **`equivalence_only_restates`** — paper claims novelty but the formula/derivation is equivalent to a known result (Stephens #12 example: formula 8 recasts rather than replaces).
- **`hidden_quantifier_shift`** — the proof needs ∀ where the claim says ∃ (or vice versa); slipped quantifier under the rug.
- **`novelty_exceeds_formal`** — the formal result is narrower than the novelty claim around it.
- **`scope_creep`** — the present object is correct in the regime the proof addresses; the paper applies it outside that regime without re-derivation.

### Validity states

- **`valid`** — the present object straightforwardly supports the claim under the paper's own definitions. The required inference holds. No defect found.
- **`partial`** — the object supports a *narrower* version of the claim than the paper asserts. State exactly the narrower version and why the broader claim doesn't follow.
- **`invalid`** — the present object does not support the claim under the paper's own definitions. There is a minimal witness — concrete counterexample within the paper's setup, or a derivation step that breaks under the paper's stated conditions.
- **`unclear`** — the paper text is ambiguous, OCR-corrupted, or the audit requires domain expertise beyond what's on the page. Use sparingly.

### `paper_definitions_used` is mandatory

Every audit record must cite at least one paper-internal definition. The downstream calibrator validates that all cited definitions actually exist at the cited locations (anti-hallucination check). An audit with empty `paper_definitions_used` is rejected.

### Minimal witness

For `validity_status: invalid` or `partial`, the minimal witness is the smallest concrete demonstration of the failure. Examples:

- A 2-node network where the formula breaks (Galeotti-style)
- An explicit substitution that yields a contradiction
- A specific case the claim purports to cover but does not (e.g., $w<0$ when the proof requires $w>0$)
- A computation that contradicts a stated value

Vague witnesses ("the proof has a gap somewhere") are not acceptable. Calibrator drops audits without concrete witnesses.

### Benign interpretation

For non-`valid` verdicts, you must explicitly consider the most charitable reading of the paper that would save the claim, and explain why that reading does not apply. This is the anti-pedantry guardrail — many papers compress notation or rely on conventions the reader is expected to fill in. The audit is reportable only if the charitable reading does not save the claim.

### Verbatim quoting and content filters

If the anthropic family run encounters Anthropic's content filter on verbatim text reproduction (van Vreeswijk-style), use paraphrased `quote_or_paraphrase` fields. The downstream integrator and calibrator handle paraphrased evidence. Set `support_type: paraphrase` if you have it; otherwise the absence of verbatim quotes is acceptable for the v8.1 audit (unlike v8.0 obligation extraction, which records support_type explicitly).

### Length budget

Triage caps candidates at 8–12 per family. The audit produces one record per candidate, so output is 8–12 audit records per family. Each record's prose fields are tight — 1–2 sentences per field. Verbose records suggest the audit is rambling rather than focusing.

## What this template does not do

- It does not run on free-form discovery. Inputs come from triage.
- It does not adjudicate between families. The integrator (`templates/claim_validity_integrate.md`) handles cross-family merge.
- It does not assign panel-row severity. The calibrator (`templates/claim_validity_calibration.md`) does.
- It does not interact with v8.0 obligation extraction beyond reading the ledger via triage. Obligation flow and claim-validity flow merge at panel-row level only.
