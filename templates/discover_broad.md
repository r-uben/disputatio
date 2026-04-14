# Discovery prompt — broad critic track (v6)

Scan the paper for **internal contradictions, scope mismatches, commitment violations, framing overclaims, and transcription errors.** This track fuses the v3/v4/v5 methods M0 (close reading), M2 (interrogation by contradiction), and M5 (self-measured critique) into a single sweep.

Runs once per model family in Wave 2. Paired with `discover_holistic.md` (conceptual-scope) and `discover_narrow.md` (deep evidence).

## Inputs

- Paper text: `{{paper_path}}`
- Your paper map: `{{paper_map_path}}`
- Your holistic pass: `{{holistic_pass_path}}`
- Canonical attack-surface index: `{{attack_surface_index_path}}`

## Task

Execute three mechanical passes over the paper and merge the output:

### Pass 1 — Close reading (M0)

Walk the paper sentence by sentence. Flag:

- typos in displayed equations (missing squares, wrong subscripts, flipped signs)
- notation inconsistencies (e.g., a symbol defined one way in the setup used another way in a proof)
- equation reference errors (e.g., "by equation (3)" where the argument requires (5))
- undefined symbols used without definition
- wording slips that change meaning (e.g., a quantifier swap)

Close reading is mechanical. Do NOT speculate about substantive errors — only surface what you can point to with a verbatim quote and a specific correction.

### Pass 2 — Interrogation by contradiction (M2)

Find pairs of claims in the paper that cannot both be true, or cases where an explicit claim contradicts an implicit assumption elsewhere. Categories to look for:

- section title vs section body (e.g., "Section 5 Incomplete Information" while footnote 23 admits the game is complete-info)
- abstract claim vs theorem conditions (abstract says X; theorem says X under restriction Y; restriction Y never flagged in abstract)
- footnote vs body (footnote walks back a body claim)
- assumption vs result (a result requires a condition stronger than stated assumptions)
- example vs general claim (the paper's own running example violates the general claim's scope)

Every contradiction needs TWO verbatim quotes: the commitment and the violation.

### Pass 3 — Self-measured critique (M5)

Enumerate the paper's commitments (scope conditions, standards it claims to meet, normative targets, methodological rules, definitions). For each commitment, hunt for passages where the paper violates it.

Walk the v6 scope-mismatch checklist from `templates/methods/m5_immanent.md`:

- Section title vs section body
- Abstract promise vs theorem condition
- Footnote vs body
- Introduction narrative vs formal statement
- Generality promise vs extension scope
- Caption vs figure content
- "Generic / technical" label vs actual effect

Each M5 finding records the commitment (verbatim + location) AND the violation (verbatim + location).

## Output

Single JSON file to `{{output_path}}`:

```json
{
  "track": "broad_critic",
  "agent": "<your family>",
  "issues": [
    {
      "id": "bc_<family>_001",
      "category": "proof | empirics | identification | framing | robustness | interpretation | notation | other",
      "pass": "m0 | m2 | m5",
      "attack_surface_id": "AS2",
      "claim": "one-sentence falsifiable statement",
      "evidence": [
        {
          "quote": "verbatim passage from paper.md",
          "location": "section / page / equation anchor",
          "why": "one sentence",
          "support_type": "direct_quote | derived_inference"
        }
      ],
      "falsifier": "what would withdraw this",
      "impact": "material | local | nit",
      "confidence": "high | medium | low",
      "paper_commitment": "the commitment this finding cites (null for M0 typo findings)",
      "paper_commitment_location": "where the commitment is stated",
      "needs_web_verification": false,
      "verification_query": null
    }
  ]
}
```

`pass` records which of the three passes produced the candidate. Downstream analysis can slice by pass to see the relative yield of each. `attack_surface_id` is optional for broad_critic candidates (M0 typos often don't map to any attack surface); use `"novel"` if the candidate genuinely doesn't fit.

## v6 atomicity enforcement

- One candidate = one claim. If you find a cluster of typos in the appendix, emit one candidate per typo with its own quote. Do NOT bundle "15 typos in OA3.1" as one candidate.
- Exception — only when the *pattern itself* is the finding: use `aggregated: true` with a `sub_findings[]` array, each sub-entry carrying its own verbatim quote.
- Summary quotes are banned. `"Multiple locations..."` and `"Various appendix passages..."` are inadmissible.
- Every quote MUST be a substring of `_paper/paper.md` (whitespace-normalized). The orchestrator's inline evidence compiler rejects candidates whose quotes do not substring-match at write time.

## Quality bar

- 10–25 candidates is normal for a paper of Econometrica length. M0 alone may produce 10+ typos; M2 and M5 together typically add 5–15.
- Prefer specific, verifiable findings over broad indictments. A single precise M5 finding beats five "the paper overclaims" complaints.

## OCR warning

Do NOT flag OCR artifacts as paper errors. Garbled LaTeX or hallucinated text from OCR go to `ocr_concerns`, not `issues`.

## Web search

Not triggered. Closed-book.
