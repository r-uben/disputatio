# Polish prompt — calibration rewrite step (v6)

This prompt defines the **rewrite sub-step inside Phase 5 calibration**, not a separate phase. Called from `templates/calibrate.md` disposition rule: when a calibration annotator returns `quote_verified: partial` or `calibration: overclaimed`, the orchestrator fires one polish ticket per flagged finding to produce a narrower claim that preserves the verbatim quote but removes the overreach. The rewrite is then re-annotated once; if still failing, the finding is dropped or demoted.

The v5 "Phase 5.5 editorial polish" role (rewriting surviving_text into referee-letter prose) is **not** handled here in v6 — that is the single-writer render step, specified in `templates/render_panel.md`. Do not use this prompt for prose polishing; use `render_panel.md` instead.

## Why this step exists

Calibration annotators flag findings as `overclaimed` or `partial` when the claim stretches beyond what the paper's text supports, or when the quote is paraphrased / truncated in a way that changes meaning. Simply dropping every such finding would over-punish concerns that have a real kernel hidden behind overreaching framing. The polish rewrite step gives each flagged finding exactly one opportunity to produce a narrower, quote-verified version — phrased as strongly as the paper's text supports, no stronger.

Polish fires only when calibration flags a finding. Supported findings do not enter polish. Dropped findings do not enter polish. Only `overclaimed` and `partial` findings get the rewrite attempt, and only one attempt — if the rewrite's re-annotation still fails, the finding is demoted one tier or dropped outright per the calibrate.md disposition table.

## Scope — what polish can and cannot change

**Polish MUST preserve:**
- Every fact, quote, location anchor, and falsifier in the finding.
- The finding's scope (don't widen from "local" to "material" or vice versa).
- The paper's own qualifiers (don't strip "as long as the budget is small" from a quote).
- The suggested fix's specificity (sentence-level vs section-level).

**Polish MAY change:**
- Sentence structure, paragraph flow, word choice.
- The order of facts within the paragraph.
- Transitions (connecting words, rhetorical framing).
- Reframing "the paper hides X" → "the paper does not explicitly state X" when the paper's text actually discusses X (this is what Phase 4 calibration should have already caught; polish is a second safety net).

**Polish MUST NOT:**
- Remove the verbatim quote.
- Add new concerns or conflate findings.
- Change the verdict (prosecution_wins / split / settled / escalate).
- Invent citations or external claims not in the finding's evidence.

Polish is a *writing* step, not a *judging* step. If polish thinks the finding is wrong, that is a calibration failure — polish does not override it. Flag in the session log and ship the polished version anyway.

## Prompt body

For each surviving report-entering finding, write the prompt file to `_artifacts/prompts/polish_<true_id>.md`:

```markdown
# Editorial polish — finding {true_id}

You are rewriting one finding from a referee report into one paragraph of editor-grade prose. Your output will be pasted directly into a published referee letter. Not a bullet list, not a JSON summary, not a "here are the concerns" preamble — one paragraph that a journal editor would send to the author.

## Finding

```json
{finding_json}
```

## Relevant paper passage

{quote_context}

(context = the verbatim quote plus 10 lines before and 10 lines after, for you to check that your paraphrase does not stretch the paper's text.)

## Your task

Write ONE paragraph (4-8 sentences, ~150-250 words) that:
1. States the concern clearly and unhedged, using the paper's own terminology.
2. Quotes the paper verbatim where the finding cites it.
3. Explains why the concern is material (or local — match the tier).
4. Proposes the concrete edit that would address it (sentence-level where possible).
5. Avoids:
   - "The paper hides X" (unless calibration confirmed this phrasing).
   - "The paper fails to…" framing if the paper actually mentions the thing in passing.
   - Rhetorical flourishes, hedges beyond what the finding warranted, or ad-hominem.

Preserve every fact, every quote, every location anchor. Do not add new concerns. Do not strip the paper's qualifiers from the quote.

## Output

Write one markdown file to `4_report/polished/<true_id>.md` with:
- A level-3 markdown header (`### C1: <short title>` for material, `### L1: <short title>` for local, `### S1: <short title>` for settled).
- A location note (`**Location.** <section / page / equation>`).
- The verbatim quote in a block quote (`> ...`).
- The one-paragraph referee-letter prose.
- A `**Suggested fix.**` line with the concrete edit.
- A debate provenance footer (`*Debate trace:* [[3_debates/...]] · *Register entry:* `_artifacts/json/ranked_issues_verified.json#<true_id>``).

Do NOT output anything outside the markdown file.
```

## Ticket

One `polish` ticket per report entry, emitted after `final.json` is written but before `referee_report.md` is compiled. They run in parallel (concurrent=4), all to gemini-3.1-pro-preview:

```json
{
  "polish_merged_027": {
    "id": "polish_merged_027", "type": "polish",
    "agent": "gemini", "model": "gemini-3.1-pro-preview", "family": "google", "flags": {},
    "prompt_path": "_artifacts/prompts/polish_merged_027.md",
    "inputs": ["_artifacts/prompts/polish_merged_027.md"],
    "outputs": ["4_report/polished/merged_027.md"],
    "depends_on": ["final_report"],
    "status": "pending", "timeout_s": 600,
    "output_format": "json_stdout"
  }
}
```

(Note: gemini in agent-ctl writes to stdout reliably with `--yolo`; `output_format: json_stdout` is not strictly needed for markdown output, but the same salvage logic applies.)

## Render step

After all polish tickets complete, the orchestrator assembles `4_report/referee_report.md` by concatenating:

1. Frontmatter (from `final.json` overall assessment).
2. `## Summary` — one paragraph compiled by opus from `final.json.overall_assessment`.
3. `## Assessment` — 2-3 paragraphs, opus-written from `final.json`.
4. `## Material concerns` — each polished markdown file for material findings, in rank order.
5. `## Local concerns` — each polished markdown file for local findings.
6. `## Settled concerns` — each polished markdown file for settled findings, in rank order.
7. `## Dropped issues (tested in debate, defender prevailed)` — brief per-entry from `final.json.dropped_issues` (no polish needed, these are just provenance lines).
8. `## Dropped by calibration` — brief per-entry from `_calibration/dropped.json`.
9. `## Web-verified findings` — same-as-v4.
10. `## Method notes` — v5 pipeline stage count, coverage rate vs baseline, Phase 4 overclaim rate pre/post.
11. `## Provenance` — links to artifacts.

## Cost

- ~16 polish calls per paper (varies by report size), each on gemini-3.1-pro-preview at ~4K tokens input / ~500 tokens output ≈ $0.05-0.10 per call.
- Total per report: **~$1-2, ~5 minutes wall-clock** (parallel).
- Negligible vs the rest of the pipeline (~$30-50).
