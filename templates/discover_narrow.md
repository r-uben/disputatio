# Discovery prompt — narrow evidence-judgment track (v6)

Produce **deep, evidence-heavy findings** targeted at the paper's highest-priority attack surfaces. This track fuses M3 (systematic transformation), M4 (counterexample construction), M6 (causal disentangling), and M8 (algebraic derivation trace) — the four methods that produce robust, defensible findings when applied to specific propositions rather than swept over the whole paper.

Runs once per model family in Wave 2. Unlike `discover_broad.md` (wide sweep) and `discover_holistic.md` (framing-level), this track spends its budget on a small number of targets with maximum rigour.

## Inputs

- Paper text: `{{paper_path}}`
- Your paper map: `{{paper_map_path}}`
- Your holistic pass: `{{holistic_pass_path}}`
- Canonical attack-surface index: `{{attack_surface_index_path}}` — you read this for priority
- Priority attack surfaces: the subset of the index with `priority == "high"` AND `requires_deep_engagement == true`

## Task

Take every attack surface in the index marked `priority == "high"` AND `requires_deep_engagement == true`. If the resulting set still leaves you with too few engagement targets to produce a depth-rich track output, extend into `priority == "medium"` until the set is wide enough — you, the agent, judge how wide that needs to be given the paper. Do not pad with low-priority surfaces; do not skip a high-priority surface to economise.

For each selected surface, apply one or more of M3/M4/M6/M8 — at minimum one M8 attempt on every selected surface whose `type ∈ {theory, proof}`. The 2026-04-15 A/B vs coarse.ink had narrow_evidence emit only 4 findings per family under the prior "2–4 surfaces" framing, leaving real algebra gaps unaddressed; the lesson is "engage every priority surface deeply", not "hit a fixed surface count".

**Engagement contract.** Discovery is closed-book. The orchestrator's audit rule is documented in `templates/emit_tickets.md` ("Narrow-evidence engagement audit") and checks surface coverage, M8 outcomes, and engagement — not issue count. Your job here is to engage every selected surface until method application is exhausted, not to hit a number. Padding to clear a count is explicitly disallowed (and the merge atomicity validator will drop padded findings anyway).

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

### M8 — Algebraic derivation trace

Walk a specific proof end to end, in your own notation, and flag any step where the paper loses a term, inverts a sign, drops a square root, or lands on an impossible value (negative Lagrange multiplier on a binding constraint, probability outside [0,1], etc.). See `templates/methods/m8_derivation.md` for the full procedure.

**Mandatory for every selected attack surface whose `type ∈ {theory, proof}` and whose `paper_location` pins a specific theorem / proposition / corollary / lemma.** At least one M8 attempt per such surface — either a finding, or a session-log note saying the trace is clean. M0 catches typos; M3 attacks the claim from outside; M8 rejects the proof from the inside.

Skip for surfaces typed `framing` / `identification` / `robustness` / `exposition` — M8 needs explicit algebra to trace.

Negative-Lagrange test is mandatory on every optimisation paper: for every stated solution including limits, verify the multiplier on each binding inequality constraint is `≥ 0`.

## Output

Single JSON file to `{{output_path}}`:

```json
{
  "track": "narrow_evidence",
  "agent": "<your family>",
  "surface_attempts": [
    {
      "attack_surface_id": "AS1",
      "type": "theory | proof | empirics | identification | framing | robustness | exposition",
      "methods_attempted": ["m3", "m4", "m6", "m8"],
      "m8_required": true,
      "m8_outcome": "finding_emitted | clean_trace | not_applicable",
      "engagement_outcome": "finding_emitted | engaged_no_finding",
      "issues_emitted": ["ne_<family>_001", "ne_<family>_002"],
      "notes": "one sentence per surface — what you tried, what landed, why M8 is clean if no finding"
    }
  ],
  "issues": [
    {
      "id": "ne_<family>_001",
      "category": "proof | empirics | identification | framing | robustness | interpretation | notation | other",
      "method": "m3 | m4 | m6 | m8",
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
      "m8_derivation_trace": "the specific proof step that breaks, written in the paper's notation: paper's step on one line, corrected step on the next. Max ~10 lines. Null if method != m8.",
      "falsifier": "what would withdraw this",
      "impact": "material | local | nit",
      "confidence": "high | medium | low",
      "needs_web_verification": false,
      "verification_query": null
    }
  ]
}
```

Only one of `m3_transform` / `m4_counterexample` / `m6_cofactors` / `m8_derivation_trace` is populated per finding, per the `method` field.

`surface_attempts[]` is mandatory. Every selected attack surface gets one entry — including surfaces that produced zero findings. Two outcome fields:

- `m8_outcome` applies only to `theory`/`proof` surfaces. `m8_required` is `true` for those (contract violation to set it `false`); `false` otherwise. Allowed values when required: `finding_emitted`, `clean_trace`. Allowed value when not required: `not_applicable`. A clean M8 trace MUST appear as `clean_trace` with a one-sentence note; otherwise the orchestrator cannot distinguish a clean trace from a skipped one.
- `engagement_outcome` applies to every surface regardless of type. Allowed values: `finding_emitted` (one or more issues in `issues_emitted`), `engaged_no_finding` (every relevant method tried, no finding survived honest engagement). The audit treats `engaged_no_finding` as a clean engagement; `not_attempted` is not a legal value here.

## Quality bar

- **Engage every selected surface fully.** The agent picks the surface set; the agent does not pick the depth — depth is "until M3/M4/M6/M8 stop producing concrete weaknesses on this surface." A surface that yields zero findings after honest engagement is a `surface_attempts[]` entry with empty `issues_emitted`, not a reason to switch to a thinner surface.
- **No padding.** A weak transform observation written to clear a count fails the merge atomicity check (it lacks a falsifier-bearing claim) and gets dropped at merge anyway. Do not pad.
- Every finding must trace to a specific proposition (not a vague "the paper's approach"). The target proposition's label (Theorem 1, Corollary OA3, Proposition 4) appears in the `claim` or `evidence.location`.
- M3 transform findings should name which transform applies in the `m3_transform` field. "Weaken" findings that just restate the assumption are noise; prefer weakenings that break the proof.

## Priority attack-surface targeting

The orchestrator ranks attack surfaces by `priority` in Phase 1. This track spends its budget on the `high`-priority ones first. **You may not skip a high-priority surface even if the holistic track already addressed it** — the audit (see `templates/emit_tickets.md`) rejects narrow_evidence outputs that omit high-priority surfaces. If holistic produced a framing critique, your job here is the deeper M3/M4/M6/M8 engagement holistic did not do; record that in the `surface_attempts[]` entry's `notes` field. The only legitimate way for a high-priority surface to absent itself from `surface_attempts[]` is for it not to exist in the attack-surface index, which is upstream of this track.

## OCR warning

Do NOT flag OCR artifacts. Garbled LaTeX goes to `ocr_concerns`.

## Web search

Not triggered in this phase. Note web-verifiable facts in `needs_web_verification: true` + `verification_query`; Phase 3 will handle them.
