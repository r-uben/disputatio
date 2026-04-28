# Attack-surface index builder (v6)

After all three Phase 1 holistic-pass tickets complete, the orchestrator builds a **canonical attack-surface index** by unioning the three per-family `attack_surfaces[]` arrays into a single deduplicated list. This index is inputs to every Phase 2 discovery ticket and to the two-route escalation gate in Phase 4.

This is NOT a model call. It is a deterministic orchestrator-side step — Python inline in Claude Code between Wave 1.5 and Wave 2.

## Inputs

Three files produced by Phase 1:

- `_artifacts/json/holistic_claude.json`
- `_artifacts/json/holistic_codex.json`
- `_artifacts/json/holistic_gemini.json`

Each carries an `attack_surfaces[]` array per `templates/holistic.md`.

## Output

Single JSON file at `_artifacts/json/attack_surface_index.json`:

```json
{
  "generated_at": "2026-04-14T...",
  "family_source_count": 3,
  "surfaces": [
    {
      "id": "AS1",
      "type": "theory | empirics | identification | framing | robustness | exposition",
      "description": "one-paragraph description",
      "representative_question": "the concrete referee question for this surface",
      "priority": "high | medium | low",
      "paper_location": "section/page",
      "requires_deep_engagement": true,
      "supporting_families": ["anthropic", "openai"],
      "dedup_sources": [
        {"family": "anthropic", "original_id": "AS1", "description": "..."},
        {"family": "openai", "original_id": "AS2", "description": "..."}
      ]
    }
  ]
}
```

## Dedup procedure

Union the three per-family arrays into a flat list. Apply these rules in order:

### Rule 1 — exact type + location match → same surface

If two entries have identical `type` AND their `paper_location` matches at section level (e.g. both point to "Section 4.2" or both to "Proposition 2"), they are the same surface.

### Rule 2 — semantic match on representative_question

Two entries are the same surface if their `representative_question` fields are paraphrases of each other. The orchestrator uses a single low-cost opus call (or sonnet) with this prompt to batch-dedup:

```
Given these N referee questions, group them into equivalence classes where
two questions are equivalent iff answering one would also resolve the other.
Return JSON: [{"group_id": 1, "member_indices": [0, 2]}, ...]
```

Questions that fail to match by Rule 1 but match by Rule 2 are merged into the same surface.

### Rule 3 — independent surfaces remain separate

If Rules 1 and 2 both fail, the two surfaces are distinct and both enter the index with separate IDs. Do NOT force-merge by description similarity alone — two surfaces may touch the same passage but ask different questions.

## Priority aggregation

For each unified surface, compute its priority from the contributing families:

- If any family rated it `high`, the unified priority is `high`.
- Else if two or more families rated it `medium`, the unified priority is `medium`.
- Else `low`.

Single-family surfaces (no dedup matches) keep their original priority. This gives high-priority surfaces a cross-family corroboration signal: a surface that lands `high` in the unified index either had at least one family flag it high OR had multiple families concur.

## Description merging

When Rules 1 or 2 match, produce a merged `description` by concatenating the distinct informational content of the contributing descriptions — NOT by averaging or paraphrasing. If the contributing descriptions disagree substantively (e.g., one frames the surface as `theory`, another as `identification`), keep the richer framing and record the disagreement in a `dedup_notes` field on the unified surface.

`representative_question` is taken from the most specific contributing question (the one with the narrowest scope — longest + most concrete).

`paper_location` unions locations (if one family cited "Section 4.2" and another "Proposition 2", merge to "Section 4.2 / Proposition 2").

## Per-family supporting flag

Every unified surface carries `supporting_families: []` — the list of families whose holistic pass contributed to it. This is the corroboration signal consumed by the Phase 4 two-route escalation gate's "cross-family disagreement" condition.

## Novel surface allowance

If Phase 2 discovery produces a candidate finding with `attack_surface_id: "novel"` (the candidate did not fit any listed surface), the orchestrator appends a new surface to the index mid-run and re-flags the corresponding holistic pass for potential gap analysis. A surge of novel candidates (> 3 on one paper) is a signal that the holistic pass missed meaningful territory; log and address in the next iteration of `templates/holistic.md`.

## Expected index size

On a typical theory paper: 5–12 attack surfaces after dedup. On a mostly-empirical paper: 4–10.

Indices with <3 surfaces indicate a weak holistic pass — the agent may have produced a bland paper map. Investigate the prompt.

Indices with >20 surfaces indicate insufficient dedup — rerun Rule 2 with tighter thresholds or examine the agents' divergence.

## Failure modes

- **Rule 2 opus call fails / rate-limited**: fall back to Rule 1 only. Flag in the session log. Expect some surface duplication; merge will handle it downstream at higher cost.
- **All three families produce zero surfaces**: the paper may be too short or too specialized for the holistic pass to engage meaningfully. Continue to Phase 2 with an empty index and rely entirely on broad_critic + narrow_evidence. Note the anomaly in `review.md`.
- **Families disagree on type classification**: use the type from the family with `priority: high` on that surface. If priorities agree, alphabetical tiebreak (the classification dictates downstream track routing in `discover_narrow.md`).
