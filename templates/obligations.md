# Obligation extraction prompt (v8.0, new)

Extract the **specification obligations** the paper carries. For every load-bearing claim, method, theorem, algorithm, or worked construction, identify the objects (definitions, properties, conditions, intermediate lemmas, datasets, reference values) that **must exist and be specified for the claim to be executable or provable**. Then locate where each obligation is satisfied — or surface that it is not.

This phase exists because v7's discovery tracks (holistic / broad / narrow) under-detect **formal-specification gaps** — the kind of finding coarse.ink's adversarial-proof module catches: "MH algorithm needs a complete-data density," "kernel definition lacks initial conditions," "Lemma 5 hides a non-catastrophic encoder hypothesis." These are absences, not contradictions; the previous tracks look for what's *wrong*, not what's *missing*. The obligation pass produces an audit trail of *what must be there*, used downstream to surface unresolved obligations as gap-claims under the calibration rubric in `templates/gap_claim_calibration.md`.

The obligation phase is **not** a discovery step. It does not emit findings. It emits structured records that downstream stages convert into findings only after the global integrator (`templates/obligation_integrate.md`) merges per-family records and the gap-claim calibrator validates them.

## Inputs

- Paper text: `{{paper_path}}`
- Paper map (your own): `{{paper_map_path}}`
- Holistic pass (your own): `{{holistic_pass_path}}`

## Task

Produce a single JSON file at `{{output_path}}`:

```json
{
  "family": "anthropic | openai | google",
  "obligations": [
    {
      "id": "OBL_001",
      "claim_or_method": {
        "what": "verbatim or paraphrased statement of the load-bearing claim/method/theorem/algorithm",
        "kind": "claim | method | theorem | algorithm | construction | benchmark",
        "location": "section / page / equation anchor"
      },
      "required_object": {
        "name": "the specific object the claim/method requires (e.g. 'complete-data density f(A,θ)', 'transition matrix domain', 'Λ_0 closure under addition', 'identification assumption')",
        "type": "definition | property | bound | algorithm | proof_step | dataset | parameter_value | reference_calibration",
        "why_required": "1-2 sentences on what the claim/method cannot do without this object"
      },
      "where_it_should_be_defined": "where in a competent paper one would expect this object to be specified — section / theorem / appendix / supplement",
      "searched_locations": [
        "concrete locations you checked, e.g. 'Section 3.2 eq (8)', 'Appendix A.1', 'Definition 2'"
      ],
      "satisfied": "yes | partial | no | unclear",
      "satisfaction_evidence": {
        "found_at": "specific location where the object is satisfied (if satisfied=yes or partial); empty string if no",
        "quote_or_paraphrase": "what the paper says, verbatim if filter-safe; otherwise paraphrased",
        "support_type": "direct_quote | paraphrase | derived_inference"
      },
      "closest_partial_substitute": "if not fully satisfied: the closest thing the paper does provide (e.g. 'paper defines T(A) for stationary case but not for the conditional A_n case the method needs') — empty string if satisfied or no substitute exists",
      "missing_piece": "if satisfied=partial or no: 1-2 sentences naming the precise gap — what's missing from the closest substitute",
      "consequence_if_missing": "1-2 sentences on what breaks downstream if this obligation is unresolved (e.g. 'MH acceptance ratio cannot be computed', 'Theorem 1's normalization is not derivable in-paper', 'finite-variance claim has no proof outside the special case')",
      "confidence": "high | medium | low"
    }
  ]
}
```

## How to work

### What counts as a load-bearing claim/method

Anything the paper's argument or empirical results genuinely depend on. Not every sentence. Filter aggressively:

- **Yes**: theorems and propositions stated as results; methods/algorithms applied to the empirical analysis; identifying assumptions; benchmark calibrations the paper compares against; data definitions used to compute reported numbers.
- **No**: motivating examples, related-work summaries, future-work gestures, narrative scaffolding.

Aim for 8–15 obligations per paper. More than ~25 is a sign you're cataloguing rather than auditing.

### Identifying required objects

For each load-bearing claim/method, ask:

> *If a careful PhD student tried to execute or reproduce this, what would they need that's not on the page in front of them?*

Examples of typical required objects by kind:

- **algorithm** → complete-data density, proposal density, stopping rule, parameter values, initialization, convergence criterion
- **theorem/proposition** → assumption set, intermediate lemma, normalization constant, scope condition, regularity condition
- **construction** → domain of validity, closure properties, dimensional constraint, hidden hypothesis (e.g. non-catastrophic encoder, decomposability)
- **benchmark** → reference implementation choices, tuning regime, data definition, reproducibility seed/version
- **identifying assumption** → instrument validity condition, exclusion restriction, monotonicity, common support

### The audit, not the gotcha

You are not trying to maximize unsatisfied obligations. You are trying to produce an **honest audit** of what the paper does and does not specify. A paper can satisfy an obligation in a footnote, an appendix, a remark, or a citation. Search before declaring `satisfied: no`.

`searched_locations` is **mandatory** — it is the load-bearing evidence the downstream calibrator uses to validate scoped absence. A list of two locations is suspicious; expect 3–8 for serious obligations. Cite section anchors, not just "Section 3."

### Satisfaction states

- **`yes`** — object is fully specified at `found_at`, with a citable quote/paraphrase, sufficient for the claim to be executable/provable. `missing_piece` should be empty.
- **`partial`** — paper specifies the object but only under conditions narrower than the claim requires (e.g. PIM mutation only, infinite sites only, decomposable lattices only). `closest_partial_substitute` and `missing_piece` are mandatory.
- **`no`** — searched the load-bearing locations, did not find the object, and no close substitute exists. `searched_locations` must include at least 4 places. `consequence_if_missing` is mandatory.
- **`unclear`** — the paper text is ambiguous, OCR is corrupted, or the object would require domain expertise beyond what's on the page to evaluate. Use sparingly; this should be <5% of obligations.

### Verbatim quoting and the content filter

Some papers (notably van Vreeswijk & Sompolinsky 1998) trigger Anthropic's content filter when verbatim text is reproduced. If you are running on the anthropic family and detect a filter risk:

- Set `support_type: paraphrase` on every record.
- `satisfaction_evidence.quote_or_paraphrase` carries a paraphrased rendition with section/page locator.
- This is a documented graceful-degradation path, not a regression. The downstream global integrator and gap-claim calibrator must work without verbatim quotes.

### What this phase does not do

- It does not emit findings. The output is structured records, not panel-row candidates.
- It does not call methods M0–M8. Those run in Phase 2 discovery against the canonical attack-surface index.
- It does not interact with debate. Obligation records flow through the global integrator and gap-claim calibrator before any debate gate evaluates them.

### Length budget

Aim for 8–15 obligation records per paper. Each record's prose fields should be tight — 1–2 sentences per field, not a paragraph. The structured form is the point: downstream tooling depends on these fields being machine-readable and uniformly shaped, not on rhetorical polish.
