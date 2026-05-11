# [v8] Gap-claim calibration rubric

**Type**: design / extend existing component
**Priority**: high
**Origin**: 2026-04-25 head-to-head; codex 5.5 critique

## Problem

v7 calibration auto-kills **gap findings** even when correct. A finding like "the MH algorithm needs the complete-data density" has no supporting quote that *says* "we forgot the complete-data density." The supporting quote is the **incomplete spec itself**.

Current `quote_verified` rubric asks "does the cited quote say what the finding claims?" For a gap finding, it doesn't — the quote shows what's *present*, the finding talks about what's *missing*. So the calibrator marks `partial` or `unsupported` and the finding gets dropped.

This is a structural bias against absence claims, not a model failing.

## Proposal

Extend panel-row schema with a `claim_type` field:

```json
{
  "finding_id": "F003",
  "claim_type": "error | overclaim | gap | omission_of_caveat",
  ...
}
```

For `claim_type: gap`, the calibrator runs a **different rubric**:

```
Burden:    Does the cited text establish that the paper claims/uses X?
           (Supporting quote shows X being claimed or used.)
Obligation: Does X require the missing object Y to be executable/provable?
           (References issue #01 obligation index.)
Absence:   Does the audit establish Y is not found in the relevant scope?
           (References issue #02 section integrator's satisfaction check.)
Search trail: Was the audit thorough enough? List of locations checked.
```

Verdict logic:
- **Supported**: burden + obligation + scoped-absence all hold AND search trail covers ≥80% of the relevant scope.
- **Calibrated_narrowed**: burden + obligation hold; absence holds in *some* scope but the search trail is incomplete OR the obligation is `partial` (Y is mentioned somewhere but not where it's needed).
- **Overclaimed**: burden holds but obligation is contestable (paper didn't really need Y to make its claim) OR a partial substitute for Y exists.
- **Unsupported**: burden fails OR Y is satisfied within the relevant scope.

## What changes downstream

- The `evidence` array on a `gap` finding now includes a `search_trail` field with locations checked.
- The `annotator_notes` field carries the absence reasoning, not just a quote-check verdict.
- Demote-on-uncertainty rules apply uniformly: any qualified verdict → `calibrated_narrowed` + severity demotion, same as v6.

## Why "the author admits the gap" is the wrong test

Codex hammered this: requiring a confessional quote means we'd only catch gaps the authors flagged themselves. That's worse than useless — it filters for self-aware flaws and misses the kind of gaps a careful reviewer spots that the authors didn't.

## Open questions

- **Who runs gap calibration?** Probably the same codex/gpt-5.4-full annotator, but with a forked rubric template. The annotator detects `claim_type: gap` and switches rubric.
- **How thick is the search trail required to be?** Tunable; start at "sections containing the obligation's load-bearing terms + appendices." Tighten on later iterations.
- **Risk**: gap findings with weak search trails will pass calibration superficially. Pair with issue #02 integrator to enforce that the search trail came from the integrator, not free-form annotator search.

## Related

- Issue #01: Obligation extraction (defines `Y`, the required object)
- Issue #02: Section-extract → global-integrate (provides the search trail)
- Issue #04: Stronger discovery models

## Source critique

> "Treat gap verification as negative evidence, not quote verification. For `gap`, require: a positive burden (the paper claims/uses X), an obligation (X requires Y), scoped absence (Y not found in relevant areas), partial quote (X being used or incompletely defined), search trail. The verifier asks: 'Does the cited text establish the burden, and does the audit establish absence?' Not 'does the author admit the gap?'" — codex/gpt-5.5, 2026-04-25
