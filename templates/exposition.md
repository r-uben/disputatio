# Exposition audit prompt (Phase 2.7b — new)

For each triaged candidate, produce a structured audit record. The audit answers: *given the paper's actual content, does the proposed editorial fix close a real reader-friction gap, and what is the constructive change?*

This is a *structural* audit: the witness must be a concrete pattern with anchors, not a taste-level complaint. The calibrator (Phase 3e) is permissive on subjectivity (these are editorial suggestions, not error claims) but strict on anti-pedantry — every audit must clear the "would a careful reader actually benefit, or is this nit-picking" guard.

## Inputs

- Paper text: `{{paper_path}}`
- Paper map (your own): `{{paper_map_path}}`
- Holistic pass (your own): `{{holistic_pass_path}}`
- Your family's triage output: `{{triage_path}}` (the per-family `EXP_TRIAGE_*` candidates)

## Task

For each candidate in `{{triage_path}}`, produce one audit record. Output a single JSON file at `{{output_path}}`:

```json
{
  "family": "anthropic | openai | google",
  "audits": [
    {
      "id": "EXP_AUDIT_001",
      "triage_id": "EXP_TRIAGE_001",
      "pattern_kind": "notation_collision | duplicated_derivation | missing_symbol_table | section_order_dependency | label_mismatch | absent_running_example",
      "present_object": {
        "description": "1–2 sentences describing the artifact (carried from triage, possibly refined)",
        "anchors": [
          {
            "quote": "verbatim quote from paper.md",
            "location": "section / page / equation anchor"
          }
        ]
      },
      "scope_correction": {
        "proposed_change": "a concrete, actionable editorial suggestion. For notation_collision: 'add a notation table mapping X to its three uses, or rename Δᵢ to Δ_inv to disambiguate from the demand-curve intercept.' For duplicated_derivation: 'factor steps 1–4 into a shared lemma, then state the two specialisations.' For section_order_dependency: 'move Section 5 before Section 3, or insert a forward pointer + 2-paragraph summary at the start of Section 3.' Etc.",
        "minimal_text_change": "the smallest concrete textual change that implements the proposed change (1-2 sentences). If the change requires substantive restructuring, say so explicitly — the calibrator will then check whether the change crosses into taste-level rewrite territory.",
        "alternative_change": "an alternative if the primary is too invasive (e.g. 'or, less invasively: footnote referencing where the symbol is reused')"
      },
      "reader_friction_witness": {
        "concrete_friction": "one concrete description of the friction the pattern causes a careful reader. Not 'this could be clearer' — name the specific cognitive cost: 'a reader of Section 6.2 must hold three distinct meanings of Δ in working memory while parsing equation (60); the notation table would remove that cost.'",
        "alternative_reader_response": "1 sentence on what a reader who does not adopt the fix would do — flip back, take on faith, skip. If the answer is 'shrug and continue with no real cost,' the audit is over-pedantic and should mark `verdict: no_audience_misdirection`."
      },
      "paper_self_handling": {
        "does_paper_acknowledge": "yes | no | partial",
        "where": "location of the acknowledgement if present (e.g. 'footnote 12 notes the symbol reuse')",
        "is_acknowledgement_adequate": "yes | no | partial — if yes, the audit should likely return `verdict: resolved_in_paper`",
        "notes": "1-2 sentences"
      },
      "anti_pedantry_check": {
        "would_careful_reader_benefit": "yes | no | borderline",
        "would_referee_omit_in_a_busy_report": "yes | no | borderline",
        "is_this_a_pattern_or_a_single_instance": "pattern | single_instance",
        "notes": "1-2 sentences — this is the load-bearing field for the calibrator's anti-pedantry guard"
      },
      "verdict": "reportable_exposition_finding | resolved_in_paper | no_audience_misdirection | taste_level_restructuring | single_instance_not_pattern | indeterminate"
    }
  ]
}
```

## How to work

### Per-pattern audit notes

The audit is a structured form; the prose of each field carries the substance. Per-pattern guidance:

#### notation_collision

- The audit must enumerate **every distinct meaning** of the colliding symbol, with a verbatim quote anchoring each meaning.
- `scope_correction.proposed_change` should propose either (a) a notation table, OR (b) a rename of one of the meanings. Specify which character set / convention the rename uses.
- Reader-friction witness: name a specific equation or sentence where a careful reader must context-switch between meanings.

#### duplicated_derivation

- The audit must cite **both** derivations with anchors and identify the structurally identical steps.
- `scope_correction.proposed_change` proposes either a shared lemma, an "analogous to (X)" footnote, or an algebraic recipe stated once with two instantiations.
- Reader-friction witness: a reader who has read derivation 1 should learn nothing new from derivation 2; if the second derivation has any informative content (different intermediate insight, different lemma), the audit is `verdict: single_instance_not_pattern`.

#### missing_symbol_table

- The audit must list the ≥ 20 distinct symbols and the sections they cross.
- `scope_correction.proposed_change` proposes a notation table at the end of the setup section, with one row per symbol giving (symbol, name, defining equation, first-use page).
- Reader-friction witness: name a specific section where a reader must flip back to recover a definition.

#### section_order_dependency

- The audit must trace the dependency: "Section N invokes object X (anchor: quote) without prior construction; Section M (later) constructs X (anchor: quote)."
- `scope_correction.proposed_change` is either a section reorder OR an explicit forward pointer + brief summary at the dependency site.
- Reader-friction witness: a reader of section N has to either take X on faith or flip to section M; name the specific point in section N where this bites.

#### label_mismatch

- The audit must count the references to the mis-labeled item across the paper. Cite each reference's location.
- `scope_correction.proposed_change` is a label change: "rename Claim N to Lemma N" (or Proposition N if the result is a substantive theorem-level claim).
- Reader-friction witness: a reader skimming for formal results may miss "Claim" labels; cite a passage where the Claim is invoked as if it were a lemma.

#### absent_running_example

- The audit must identify the example, count its appearances across the paper, and the current introduction point.
- `scope_correction.proposed_change` proposes introducing the example in the setup section (Section 2 or 3), with the formal apparatus subsequently re-illustrated by the example.
- Reader-friction witness: a reader of the abstract who sees the example referenced has no anchor until section 4; cite the abstract sentence and the late-introduction sentence.

### Verdict assignment

- **`reportable_exposition_finding`** — all four conditions hold: (1) the pattern is real and anchored, (2) the paper does not self-handle adequately, (3) a careful reader would genuinely benefit from the fix, (4) the fix is concrete and not taste-level restructuring.
- **`resolved_in_paper`** — the paper self-handles (e.g. has a notation table, has an explicit forward pointer, already calls the result a Lemma). Drop with reason.
- **`no_audience_misdirection`** — the pattern exists but a careful reader would not be meaningfully impeded. The anti-pedantry guard fired. Drop.
- **`taste_level_restructuring`** — on closer audit, the proposed fix is taste-level (rewrite-from-scratch territory). Drop. V1 of this track explicitly excludes taste-level work.
- **`single_instance_not_pattern`** — the candidate looked like a pattern but is one isolated instance. Drop (M0 close-reading handles single instances of typos and notation slips).
- **`indeterminate`** — cannot resolve from the paper alone. Rare. Drop with reason.

### Output discipline

- Every quote MUST be a substring of `paper.md` (whitespace-normalized).
- The `scope_correction.proposed_change` must be concrete enough that a copy editor could implement it. Vague suggestions ("improve clarity") fail.
- The `anti_pedantry_check.notes` field is mandatory and must specifically address why a competent referee would (or would not) raise this in a real referee report.

## OCR warning

Do NOT audit OCR artifacts. Garbled passages go to `ocr_concerns`, not to audits.

## Web search

Not triggered. Closed-book.
