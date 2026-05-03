# Gap-claim calibration prompt (v8.0, new)

Validate **gap claims** — findings that the paper fails to specify a required object — against the actual paper text and search trail. This calibrator runs as a sub-DAG fed by the obligation integrator's calibration queue (`templates/obligation_integrate.md` → calibration_queue.json). It is **distinct** from `templates/calibrate.md`, which handles quote-supported error/overclaim findings.

This phase exists because gap claims demand a different evidentiary contract from quote-supported findings. v7's `calibrate.md` asks "does the cited quote say what the finding claims?" — for a gap claim, the cited quote shows what the paper *does* present, not what it *fails* to specify. Gap calibration must verify scoped absence: paper claims/uses object X; X requires Y; Y is not found in the natural homes; consequence is concrete.

The calibrator does not generate findings. It validates obligation queue entries and decides which become reportable gap-class panel rows.

## Inputs

- Obligation calibration queue (one entry, blinded): `{{queue_entry_path}}`
- Paper text: `{{paper_path}}`

## Task

Produce a single JSON file at `{{output_path}}`:

```json
{
  "queue_entry_id": "OBL_GLOBAL_NNN",
  "blind_id": "BG###",
  "satisfaction_check": {
    "fired": true,
    "reason_fired": "obligation entered as disputed | any family said satisfied=yes/partial",
    "satisfies": "yes | partial | no | indeterminate",
    "checked_location": "the family-cited found_at, or the most-cited candidate location",
    "checked_quote_or_paraphrase": "what the location actually says (paraphrased if filter-blocked)",
    "defect_if_any": "if satisfies != yes: what is wrong or partial about the cited evidence — wrong object, incomplete definition, only informal prose, missing conditioning variables, not usable for the claimed result, etc.",
    "resolution": "resolved_satisfied | continue_as_partial | continue_as_unsatisfied | indeterminate"
  },
  "gap_rubric": {
    "fired": true,
    "burden": {
      "established": "yes | partial | no",
      "evidence": "where the paper claims/uses X — section + paraphrase",
      "notes": "1-2 sentences on whether burden is genuine"
    },
    "obligation": {
      "valid": "yes | partial | no",
      "object": "the required Y, restated in functional terms",
      "why_required": "1-2 sentences on why X requires Y to be executable/provable",
      "notes": "if partial: under what scope is the obligation genuine"
    },
    "scoped_absence": {
      "established": "yes | partial | no | indeterminate",
      "natural_homes": [
        "originating claim/method/result location",
        "notation/model setup section",
        "relevant method subsection",
        "proof/appendix/supplement",
        "cited algorithm/reference location (if paper delegates definition elsewhere)"
      ],
      "homes_searched": ["which natural homes the integrator's merged_searched_locations actually covered"],
      "homes_unsearched": ["natural homes that were not checked — empty if all covered"],
      "adequacy_judgment": "1-2 sentences on whether the search trail is adequate for scoped absence given this obligation's natural homes"
    },
    "substitute_evaluation": {
      "exists": "yes | no",
      "what_paper_provides": "if a partial substitute exists: what it is and where",
      "why_insufficient": "if substitute exists but obligation is partial/unsatisfied: precisely what's missing"
    },
    "consequence": {
      "concrete": "yes | no",
      "what_breaks": "1-2 sentences on what downstream claim/method/result fails or becomes incomputable if the obligation is unresolved"
    }
  },
  "verdict": "reportable_gap | resolved_satisfied | inadequate_search | indeterminate | not_a_gap",
  "verdict_notes": "1-3 sentences on the disposition rationale",
  "panel_row_payload": {
    "concern": "1-sentence statement of the gap, used as panel-row concern",
    "category": "proof | empirics | identification | framing | robustness | interpretation | notation | other",
    "claim_type": "gap",
    "severity": "material | local | nit",
    "evidence": [
      {
        "quote_or_paraphrase": "burden evidence — paper claiming/using X",
        "location": "section anchor",
        "support_type": "direct_quote | paraphrase | derived_inference",
        "role": "burden"
      },
      {
        "quote_or_paraphrase": "search-trail summary — natural homes searched, what wasn't found",
        "location": "merged across searched_locations",
        "support_type": "derived_inference",
        "role": "scoped_absence"
      }
    ],
    "suggested_action": {
      "author": {"fix": "what the author would add to satisfy the obligation"},
      "referee": {"how_to_use": "how a referee would phrase this concern in a letter"}
    }
  }
}
```

`panel_row_payload` is populated only when `verdict == reportable_gap`. Otherwise it is `null`.

## How to work

### Stage 1 — Satisfaction check (narrow, fires conditionally)

Fire the satisfaction check **iff**:
- The queue entry's `integrated_status` is any of: `split_satisfied_majority`, `split_unsatisfied_majority`, `split_3way`, `unanimous_partial`, OR
- Any `family_record` has `satisfied: yes` or `satisfied: partial`.

If the entry is `unanimous_unsatisfied` with no `yes`/`partial` family records, **skip** the satisfaction check (`fired: false`, all subfields null) and proceed directly to the gap rubric.

The satisfaction check answers exactly one question:

> *Does the cited evidence actually provide the required object in a usable form for the method/result?*

Inspect the cited `found_at` (or the most-cited candidate location across `family_records`). Read the surrounding paper text. Decide:

- **`satisfies: yes`** — the cited location provides the required object in a form the method/claim can use. Record the resolved status as `resolved_satisfied`. Verdict becomes `resolved_satisfied`. Panel row payload is null.
- **`satisfies: partial`** — the cited location partly defines the object but under narrower scope than the claim requires (e.g., PIM mutation only, infinite sites only, decomposable lattices only). Record `defect_if_any` precisely. Continue to gap rubric with the obligation re-typed as `partial`.
- **`satisfies: no`** — the cited evidence is the wrong object, informal prose, missing conditioning variables, or otherwise not usable for the claimed result. Record `defect_if_any`. Continue to gap rubric.
- **`satisfies: indeterminate`** — text is ambiguous, OCR corrupted, or evaluation requires domain expertise beyond what's on the page. Verdict becomes `indeterminate`. Panel row payload is null.

**Do not majority-vote.** One correct satisfied citation defeats the gap. One satisfied verdict with a bad citation does not suppress it. The check exists precisely to perform that adjudication.

### Stage 2 — Gap rubric (fires when satisfaction check did not resolve)

Five components, evaluated in order. A reportable gap requires **all five** to hold.

#### Burden

The paper genuinely claims or uses X. Cite the burden evidence with section anchor and paraphrase. If burden is `partial` (paper hints at X but does not actually rely on it), the obligation is downstream of a non-claim and cannot be a reportable gap.

#### Obligation

X requires Y to be executable/provable. State Y in functional terms (not lexical). The obligation must be genuine — would a competent reader of this paper actually need Y to use the method/claim, or is the requirement contestable? If contestable, mark `valid: partial` and explain.

#### Scoped absence

The integrator's merged search trail is the input. Compare against the obligation's **natural homes** for this paper:

- the originating claim/method/result location
- notation/model setup
- relevant method subsection
- proof/appendix/supplement
- cited algorithm/reference location, if the paper delegates definition elsewhere

There is **no hard floor on number of locations**. Some obligations need one decisive appendix search; others require model setup + method + notation + proof + supplement. Adequacy is per-obligation: did the search trail cover the obligation's natural homes for *this* paper?

If the obvious natural homes were not searched, set `established: no` and `adequacy_judgment` explains. Verdict becomes `inadequate_search` — the obligation does not ship as a gap, but the integrator should re-queue with expanded search.

If access or filter degradation prevented checking key natural homes (e.g., anthropic blocked verbatim quoting on a section that's the natural home), mark `established: indeterminate`, verdict becomes `indeterminate`.

#### Substitute evaluation

If the paper provides any partial substitute (a related but narrower object, an informal description, an analogy from a cited paper), record what it is and why it does not fully discharge the obligation. If no substitute exists, this section is short — but the gap rubric still requires it to be addressed.

#### Consequence

What breaks downstream if the obligation is unresolved? Concrete: "MH acceptance ratio cannot be computed" / "Theorem 1's normalization cannot be derived in-paper" / "finite-variance claim has no proof outside infinite sites." Vague consequences ("the proof is less rigorous") do not pass.

### Stage 3 — Verdict

Five outcomes:

- **`reportable_gap`** — burden + obligation + scoped_absence + consequence all hold; substitute (if any) is shown insufficient. Populate `panel_row_payload`. Severity: `material` if the consequence breaks a load-bearing claim or the main result, `local` if it weakens but does not break, `nit` for cosmetic specification gaps.
- **`resolved_satisfied`** — satisfaction check returned `satisfies: yes`. Drop from queue. `panel_row_payload: null`.
- **`inadequate_search`** — search trail did not cover the obligation's natural homes. Drop from queue with note that integrator should re-queue with expanded search. `panel_row_payload: null`.
- **`indeterminate`** — satisfaction check returned `indeterminate`, or scoped_absence was prevented by access/filter constraints, or burden/obligation is partial in a way that makes a reportable gap unsafe. Drop from queue. `panel_row_payload: null`.
- **`not_a_gap`** — burden or obligation failed validation; the paper does not actually rely on Y or X is not really required. Drop from queue. `panel_row_payload: null`.

### Severity calibration for reportable gaps

A gap-class finding's severity reflects what the unresolved obligation breaks:

- **`material`** — the gap blocks a load-bearing claim from being executable/provable. Examples: MH algorithm cannot be implemented; Theorem 1 cannot be derived in-paper; main efficiency claim has no finite-variance backing.
- **`local`** — the gap weakens a result but the claim survives in narrower form. Examples: Lemma 5 hidden non-catastrophic encoder hypothesis; Λ_0 closure proven only "ordinarily"; bounds derived only under PIM mutation.
- **`nit`** — the gap is cosmetic specification: undefined notation, missing dimensional constraint that's mechanically inferable, citation pointer instead of in-paper definition.

## What this template does not do

- It does not run on quote-supported findings. Those go through `templates/calibrate.md`.
- It does not generate obligations. Inputs come from the integrator queue.
- It does not interact with the v7 attack-surface index, debate gates, or method-based discovery. Gap-class panel rows merge with method-based panel rows in Phase 6 panel compilation.
- It does not cluster or normalize obligations. That is the integrator's job.

## Volume budget

Per paper:
- Calibration queue input: 5–12 obligations (per integrator's spec).
- Reportable gaps shipped: 2–7 expected on a well-specified paper, more on a paper with systematic specification gaps.
- Resolved-satisfied count: tracked in audit log; high counts are fine and expected.

If every queued obligation becomes a reportable gap, you are not exercising the satisfaction check honestly. If zero queued obligations become reportable, the satisfaction check is rubber-stamping or the integrator is over-clustering.
