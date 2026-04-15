# Discovery prompt — narrow evidence-judgment track (v6)

Produce **deep, evidence-heavy findings** targeted at the paper's highest-priority attack surfaces. This track fuses M3 (systematic transformation), M4 (counterexample construction), and M6 (causal disentangling) — the three methods that produce robust, defensible findings when applied to specific propositions rather than swept over the whole paper.

Runs once per model family in Wave 2. Unlike `discover_broad.md` (wide sweep) and `discover_holistic.md` (framing-level), this track spends its budget on a small number of targets with maximum rigour.

## Inputs

- Paper text: `{{paper_path}}`
- Your paper map: `{{paper_map_path}}`
- Your holistic pass: `{{holistic_pass_path}}`
- Canonical attack-surface index: `{{attack_surface_index_path}}` — you read this for priority
- Priority attack surfaces: the subset of the index with `priority == "high"` AND `requires_deep_engagement == true`

## Task

Select **2–4 priority attack surfaces** from the index and apply one or more of M3/M4/M6 to each. Do not try to cover every attack surface; depth beats breadth in this track.

### M3 — Systematic transformation

For each target proposition (theorem, corollary, empirical claim), run the 8 transforms:

- **Negate** — what if the opposite were true? Does the paper's argument still hold?
- **Strengthen** — can the claim be tightened without breaking? The paper may understate.
- **Weaken** — can the claim survive weaker assumptions? If not, why aren't the assumptions explicit?
- **Substitute** — swap a key assumption (L2 → L1 cost, symmetric → asymmetric network, rational agents → bounded rationality). Does the result survive?
- **Reverse** — reverse the causal direction. What breaks?
- **Consequence** — what does the result imply for cases the paper doesn't discuss?
- **Boundary** — evaluate at the domain boundary (C → 0, β → 0, n → ∞). What breaks first?
- **Analogy** — find the closest analogue in the literature. Does the paper acknowledge it?

Emit one finding per transform that produces a concrete weakness. Transforms that produce nothing are silent — do not pad.

### M4 — Counterexample construction

For each target proposition, try to construct a case satisfying the paper's stated assumptions but violating the conclusion. Three outcomes:

1. You construct a concrete counterexample — this is a high-value finding. The paper is wrong OR missing a hidden lemma.
2. You cannot construct a counterexample, but can identify what a counterexample *would require* — this exposes the hidden lemma explicitly. Emit as a finding with `category: proof` and the hidden lemma in the `claim` field.
3. The proof genuinely covers all cases satisfying the stated assumptions — no finding to emit.

Counterexamples need not be minimal; they need only satisfy the paper's assumptions.

### M6 — Causal disentangling

For each causal or comparative-static claim, enumerate the co-factors and co-effects the paper has not ruled out. Ask:

- What other variables could drive the outcome?
- What alternative mechanisms are consistent with the same evidence?
- Does the paper's headline mislead a reader who hasn't internalized the co-factors?

Each M6 finding records the main causal claim + the specific unaddressed co-factor(s) + a verbatim quote of the headline.

## Output

Single JSON file to `{{output_path}}`:

```json
{
  "track": "narrow_evidence",
  "agent": "<your family>",
  "issues": [
    {
      "id": "ne_<family>_001",
      "category": "proof | empirics | identification | framing | robustness | interpretation | notation | other",
      "method": "m3 | m4 | m6",
      "attack_surface_id": "AS1",
      "claim": "one-sentence falsifiable statement",
      "evidence": [
        {
          "quote": "verbatim passage from paper.md",
          "location": "section / page / equation anchor",
          "why": "one sentence explaining how the quote anchors the claim",
          "support_type": "direct_quote | derived_inference"
        }
      ],
      "m3_transform": "negate | strengthen | weaken | substitute | reverse | consequence | boundary | analogy",
      "m4_counterexample": "concrete counterexample OR hidden lemma required — null if method != m4",
      "m6_cofactors": ["list of unaddressed co-factors"],
      "falsifier": "what would withdraw this",
      "impact": "material | local | nit",
      "confidence": "high | medium | low",
      "needs_web_verification": false,
      "verification_query": null
    }
  ]
}
```

Only one of `m3_transform` / `m4_counterexample` / `m6_cofactors` is populated per finding, per the `method` field.

## Quality bar

- 3–8 findings total for this track. Depth over count. A single well-constructed counterexample is worth five weak transform observations.
- Every finding must trace to a specific proposition (not a vague "the paper's approach"). The target proposition's label (Theorem 1, Corollary OA3, Proposition 4) appears in the `claim` or `evidence.location`.
- M3 transform findings should name which transform applies in the `m3_transform` field. "Weaken" findings that just restate the assumption are noise; prefer weakenings that break the proof.

## Priority attack-surface targeting

The orchestrator ranks attack surfaces by `priority` in Phase 1. This track spends its budget on the `high`-priority ones first. If a `high`-priority attack surface has already been addressed by the holistic track, you may skip it — but check the holistic-track output for depth. A surface where holistic produced only a framing critique may benefit from deeper M3/M4/M6 engagement.

## OCR warning

Do NOT flag OCR artifacts. Garbled LaTeX goes to `ocr_concerns`.

## Web search

Not triggered in this phase. Note web-verifiable facts in `needs_web_verification: true` + `verification_query`; Phase 3 will handle them.
