# Scope/framing triage prompt (v8.2, Phase 2.6a — new)

Select **narrative claims worth auditing** for downstream scope/framing audit. Cast over abstract, introduction, conclusion, section openings, and holistic main_claims. Retain only claims that **license a strong reader inference** AND have a plausible formal-evidence anchor or possible overreach. Output a capped candidate list with structured fields the audit consumes.

This phase exists because v8.2's scope/framing audit is sensitive to over-pedantry. Without triage, every assertive sentence in the paper would be a candidate, drowning the audit in routine narrative compression. Triage filters for claims that genuinely set the paper's contract with the reader — the kind whose overreach would mislead a competent referee.

## Inputs

- Paper text: `{{paper_path}}`
- Paper map (your own): `{{paper_map_path}}`
- Holistic pass (your own): `{{holistic_pass_path}}`
- Obligation ledger (cross-family from v8.0, optional but preferred): `{{obligation_ledger_path}}`
- Claim-validity ledger (cross-family from v8.1, optional but preferred): `{{claim_validity_ledger_path}}`

## Task

Produce a single JSON file at `{{output_path}}`:

```json
{
  "family": "anthropic | openai | google",
  "candidates": [
    {
      "id": "SF_TRIAGE_001",
      "narrative_claim": "the paper's prose claim, paraphrased",
      "prose_location": "abstract | intro §1 | intro §1.2 | conclusion §6 | section opening §3 | other",
      "prose_surface": "abstract_topline | intro_topline | section_opening | conclusion_topline | conclusion_caveat | discussion | other",
      "claimed_scope": {
        "domain": "what the prose claim asserts the result applies to (e.g., 'modern population genetics data', 'all band-limited coding schemes')",
        "strength": "how strong the prose phrases the claim (e.g., 'characterizes', 'outperforms', 'demonstrates')",
        "qualifiers_in_prose": "any qualifying language the prose itself uses ('typically', 'in most cases', 'we show that') — empty string if unqualified"
      },
      "reader_inference": "what a reader is licensed to infer from the prose alone, without reading the formal apparatus",
      "expected_formal_anchor": {
        "should_back": "what theorem/proposition/experiment the reader would expect to back this claim",
        "anchor_kind": "theorem | proposition | lemma | experiment | empirical_table | algorithm | none_clear"
      },
      "audit_priority": "high | medium | low",
      "audit_priority_reason": "1-2 sentences on why auditing this matters — what the reader would be misled into believing if the prose overreaches",
      "source": "abstract | intro | conclusion | section_opening | holistic_main_claims | manual_paper_scan",
      "source_id": "MC1 | direct paragraph anchor"
    }
  ],
  "dropped_because": [
    {
      "candidate_description": "1-line description of what was considered",
      "source": "where it came from",
      "drop_reason": "narrative_compression_normal | restated_in_passing | self_caveated_at_source | not_load_bearing | motivating_example | future_work_gesture | redundant_with_kept_candidate"
    }
  ]
}
```

## How to work

### Volume cap

Aim for **6–10 candidates per family per paper**. Hard cap at 14. Below 4 means triage is over-aggressive. The `dropped_because` list should typically have 8–20 entries — many sentences in any paper are normal narrative compression that doesn't license strong reader inference.

### What licenses a strong reader inference

A claim licenses a strong reader inference iff:

1. The prose makes an assertion at meaningful strength ("we characterize", "outperforms", "demonstrates", "establishes", "shows that").
2. The assertion is paper-internal-load-bearing — readers who skim only abstract/intro/conclusion would take it as the paper's takeaway.
3. There is a plausible mismatch between the prose's scope/strength and what the formal apparatus actually establishes.

If condition 3 is uncertain, retain — the audit will adjudicate.

### Prose surface taxonomy

Tag each candidate's `prose_surface`:

- **`abstract_topline`** — sentence in the abstract that states the contribution. Highest reader-impact; calibration treats this strictly.
- **`intro_topline`** — sentence in §1 introduction or first paragraph that frames the contribution.
- **`section_opening`** — first sentence(s) of a section's substantive prose, framing what that section achieves.
- **`conclusion_topline`** — first sentence(s) of the concluding section restating the achievement.
- **`conclusion_caveat`** — sentence in the conclusion that walks back or qualifies. Usually NOT audit candidates themselves; matter for the calibration's caveat-handling rule.
- **`discussion`** — exploratory or speculative language, often signaling future-work territory.
- **`other`** — body-of-section claims that don't fit above.

This tagging is consumed by the calibrator's pragmatic caveat rule — abstract/intro toplines are held to higher standards than section openings or discussion paragraphs.

### Use prior ledgers as authoritative anchor map

For each candidate, attempt to anchor the prose claim to formal apparatus using:

1. **v8.0 obligation ledger** — if a `unanimous_satisfied` cluster exists for the formal object the prose claims to use, that's the anchor.
2. **v8.1 claim-validity ledger** — if a `unanimous_valid` cluster exists for the formal object's correctness, that's the anchor.
3. **Direct paper search** — only as fallback if no ledger anchor exists. The audit may then perform direct search and mark `anchor_source: direct_search` with quotes.

The audit (`templates/scope_framing.md`) reads these anchor pointers, so triage's job is to identify the expected anchor — even if approximate. The audit then validates whether the formal evidence actually supports the prose claim's scope and strength.

### What to drop

- **`narrative_compression_normal`** — every paper compresses. "We propose a new method" doesn't need formal-evidence audit if "new" is uncontested and the method is described.
- **`restated_in_passing`** — same prose claim made multiple places; keep one canonical instance.
- **`self_caveated_at_source`** — the prose itself caveats sufficiently in the same paragraph (e.g., "for problems where X is satisfied, Y holds"). Note: this is different from caveats in *other sections* — those are calibration's job, not triage's.
- **`not_load_bearing`** — claim is peripheral to the paper's contribution.
- **`motivating_example`** — illustrative, not analytically used.
- **`future_work_gesture`** — paper itself flags as not-done.
- **`redundant_with_kept_candidate`** — stronger version is in the kept set.

### Per-family

Triage is a per-family pass. The cross-family integrator (`templates/scope_framing_integrate.md`) merges audits, not triage outputs.

### What this phase does not do

- It does not audit anything. Triage decides what's worth auditing; the audit is `templates/scope_framing.md`.
- It does not check whether claims are actually overreaching. Audit + calibration handle that.
- It does not handle caveat-elsewhere logic. That's the calibrator's job (pragmatic caveat handling per `templates/scope_framing_calibration.md`).

## Output validation

- Every candidate must have a `prose_location` anchor and a `prose_surface` tag.
- Every candidate's `audit_priority_reason` must name a specific reader takeaway.
- `dropped_because` is mandatory; an empty list is a triage failure.
- `expected_formal_anchor.anchor_kind: none_clear` is acceptable but flags the audit to investigate whether the prose claim has any formal support at all (which itself can be the overclaim).
