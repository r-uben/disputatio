# Exposition triage prompt (Phase 2.7a — new)

Select **expositional patterns worth auditing** for downstream exposition-craft audit. This is a *structural* track: it surfaces concrete editorial problems a careful reader would flag (notation collisions, duplicated derivations, missing symbol tables, section-order dependency, label mismatch, absent running example), not taste-level restructuring advice.

This phase exists to close the "Other comments" gap surfaced by the 2026-05-19 Han-Hu-Zhang vs AER Ref #2 comparison. Anthony's public evaluation of Ref #2 singled out "great expositional comments" as a property that made the report valuable; disputatio's existing taxonomy has no slot for "the paper would read better if X." Codex's design review (high effort) recommended the same pattern as `templates/scope_framing.md` (v8.2) — a 5th evidentiary contract, narrowly scoped, with anti-pedantry guardrails.

## Inputs

- Paper text: `{{paper_path}}`
- Paper map (your own): `{{paper_map_path}}`
- Holistic pass (your own): `{{holistic_pass_path}}`
- Obligation ledger (cross-family from v8.0, optional but preferred): `{{obligation_ledger_path}}`
- Claim-validity ledger (cross-family from v8.1, optional but preferred): `{{claim_validity_ledger_path}}`
- Scope-framing ledger (cross-family from v8.2, optional but preferred): `{{scope_framing_ledger_path}}`

## Task

Produce a single JSON file at `{{output_path}}`:

```json
{
  "family": "anthropic | openai | google",
  "candidates": [
    {
      "id": "EXP_TRIAGE_001",
      "pattern_kind": "notation_collision | duplicated_derivation | missing_symbol_table | section_order_dependency | label_mismatch | absent_running_example",
      "present_object": {
        "description": "1–2 sentences describing the concrete artifact in the paper that exhibits the pattern",
        "anchors": [
          {
            "quote": "verbatim quote from paper.md",
            "location": "section / page / equation anchor"
          }
        ]
      },
      "proposed_change_shape": "1 sentence sketch of what a constructive editorial fix would look like (without writing the fix in detail — the audit step does that)",
      "audit_priority": "high | medium | low",
      "audit_priority_reason": "1–2 sentences on why this matters — what a careful reader would lose or have to recover by hand if the pattern stays",
      "source": "abstract | intro | section_opening | body_scan | appendix_scan | holistic_main_claims | reader_friction_self_observation",
      "source_id": "free text anchor"
    }
  ],
  "dropped_because": [
    {
      "candidate_description": "1-line description of what was considered",
      "source": "where it came from",
      "drop_reason": "taste_level_restructuring | minor_typo_handled_by_M0 | not_a_pattern_just_one_instance | already_handled_in_paper | length_or_style_complaint | author_preference_disagreement"
    }
  ]
}
```

## How to work

### Volume cap

Aim for **4–8 candidates per family per paper**. Hard cap at 12. Below 3 means triage is over-aggressive — most papers in the load-bearing literature have at least 3 of the 6 patterns somewhere. The `dropped_because` list should typically have 6–15 entries — many editorial observations fall into "taste-level restructuring" which is explicitly OUT of scope for v1.

### The six pattern kinds (v1 — narrowly scoped)

Each candidate must fit exactly one pattern_kind. If you cannot fit a finding to one of these six, **do not surface it** — that is what `dropped_because` is for.

#### 1. `notation_collision`

A single symbol is used in two or more distinct senses across the paper, without a notation table or explicit redefinition flagging the reuse. The Ref #2 Zhang example: "The symbol 'delta' is used in multiple senses (the Greek Δᵢ, the projection coefficient βᵢ, and informally the demand-curve intercept); a short symbol table would help."

What qualifies:
- Same character (Greek letter, Roman variable, subscript convention) used for ≥ 2 distinct mathematical objects in different sections, with no explicit "in this section, X denotes Y" passage in between.
- The collision creates real ambiguity — a careful reader must check context to know which sense applies.

What does NOT qualify:
- The same symbol used consistently across the paper (no collision).
- A symbol redefined within a single proof for a few lines, with the local redefinition explicit.
- Generic "every paper has lots of symbols" complaints.

#### 2. `duplicated_derivation`

Two or more parallel proofs / derivations in the paper that follow the same structural steps and could be unified or factored without loss of content. Ref #2 Zhang example: "some trimming, especially around parallel derivations for futures and variance swaps, would help."

What qualifies:
- Two derivations with identical structure (same setup → same intermediate steps → same algebraic moves), differing only in which symbol takes which role.
- The duplication adds pages without adding understanding; a reader of the second derivation does not learn anything they could not have inferred from the first.

What does NOT qualify:
- Two derivations that look similar but have substantively different intermediate steps (e.g., one uses a different lemma).
- A derivation followed by its specialization to a worked example (the example is content).
- "The paper is long" without a specific duplication pair.

#### 3. `missing_symbol_table`

Paper uses many distinct mathematical symbols without a dedicated symbol table, glossary, or notation section, and the proliferation is documented to confuse readers in the body of the paper itself (e.g., the same symbol is invoked across multiple sections with the reader expected to recall its definition from much earlier).

Heuristic indicator: paper uses ≥ 20 distinct mathematical symbols across body + appendix, AND has no "Notation" header.

What qualifies:
- The lack of a symbol table is concretely costing the reader work (you, the reader, had to flip back to the model setup multiple times to recover a definition).
- The paper would benefit from a 1-page notation table at the end of the setup section.

What does NOT qualify:
- Short papers with few symbols.
- Papers that already have a symbol table or a clear notation summary at the end of a setup section.
- "More symbol tables would be nice" without evidence of reader friction.

#### 4. `section_order_dependency`

Section M defines, proves, or constructs an object that Section N (N < M) already uses without forward-referencing. Ref #2 Zhang example: "Section 5 contains the central technical machinery; it could perhaps be moved earlier, with the spot-market analysis presented as an application."

What qualifies:
- A specific, traceable dependency: section N invokes object X without proof or definition; section M (later) is where X is constructed/proved.
- A reader of section N has to guess, take on faith, or flip forward to section M.
- The fix is concrete: move section M before N, or insert a forward pointer + brief summary.

What does NOT qualify:
- General "the paper would read better in a different order" without specific dependencies.
- A section invoking a result that is *cited from prior literature*, not constructed in the paper.
- Personal preference about whether method or application should come first.

#### 5. `label_mismatch`

A formal result the paper calls a "Claim" (or "Observation", "Fact", "Note") functions as a load-bearing Lemma — it is referenced in ≥ 3 subsequent proofs and the paper's argument cannot proceed without it. Ref #2 Zhang example: "The statements labeled Claim 1, 2, 3, 4, 6 are formal results used in subsequent arguments; standard practice is to call these Lemmas."

What qualifies:
- The mis-labeled item is cited as the grounding for ≥ 3 subsequent results (count references to its label or to its conclusion).
- The mis-label costs the reader: they may skim past a "Claim" expecting an informal observation, then later find proofs that depend on it.
- The fix is mechanical: rename "Claim N" to "Lemma N" or "Proposition N."

What does NOT qualify:
- A "Claim" that genuinely is an informal observation never relied on later.
- "Theorem" vs "Proposition" wording preferences (both are formal labels).
- Aesthetic preferences about the labeling system.

#### 6. `absent_running_example`

The abstract or introduction references a concrete example (a specific market, a named institution, a worked numerical setup), the example reappears in later sections, but the paper does not introduce the example as a running illustration in the setup. Ref #2 Zhang example: "The maker-taker example (Subsection 4.2) is a clean illustration; might it serve as the running example, introduced earlier?"

What qualifies:
- The same concrete example surfaces 3+ times across the paper.
- The example is well-suited to grounding the formal apparatus (it would help a reader anchor the math).
- The example is currently introduced late (section 4 or later), forcing the reader to absorb the formalism in the abstract first.

What does NOT qualify:
- A single passing mention of a concrete example (no running pattern).
- A paper that already uses the example in its setup section.
- Suggestions to add a new example the paper doesn't have.

### What gets dropped (anti-pedantry catalog)

These are common temptations that v1 of the track explicitly does NOT surface:

- **Taste-level restructuring** — "I think section X should be merged with section Y." If the fix is "rewrite from scratch with different structure," it is not a v1 candidate.
- **Minor typos** — already handled by M0 close-reading in `discover_broad`. If the issue is a single-character error, it is not exposition; it is notation discovery.
- **Single instances of a pattern** — one duplicated paragraph is a typo; three parallel derivations is a duplication pattern. Patterns require ≥ 2 occurrences and a fix that addresses the pattern, not the instance.
- **Already-handled-in-paper** — if the paper has a footnote, an appendix, or a section anchor that addresses the friction, it is not a missing artifact.
- **Length or style complaints** — "the paper is too long" without a specific duplication target is not v1 scope.
- **Author preference disagreement** — "I would have used a different convention" is not a defect of exposition.

### Output discipline

- Every `present_object.anchors[].quote` MUST be a substring of `paper.md` (whitespace-normalized).
- Every candidate must fit exactly one `pattern_kind`. If you cannot place it, drop it with reason.
- `proposed_change_shape` is a sketch — the audit step (Phase 2.7b) produces the detailed `scope_correction` equivalent.
- Triage is intentionally lossy. Putting a candidate in `dropped_because` with a clear reason is more useful than a low-quality candidate in `candidates`.

## OCR warning

Do NOT flag OCR artifacts as expositional patterns. Garbled LaTeX from OCR goes to `ocr_concerns`, not to the candidate list.

## Web search

Not triggered. Closed-book.
