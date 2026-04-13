# Evaluation

How we measure whether disputatio produces a better referee report than simpler baselines.

Two evaluation methodologies are used. They are independent and answer different questions.

---

## 1. LLM-as-judge against a reference review (`compare/judge.py`)

This replicates [coarse.ink](https://coarse.ink/)'s benchmark methodology so that disputatio's score is directly comparable to coarse.ink's published numbers.

**What it measures:** how a generated review stacks up against a known-good reference review (typically a human or Stanford Agentic Reviewer output) on four dimensions:

| Dimension | What it captures |
|---|---|
| Coverage | Does the review surface the issues the reference flagged, plus more? |
| Specificity | Does every claim cite a specific passage / equation / line? Are fixes actionable? |
| Depth | Does the review engage with the paper's logical structure, or stay at the surface? |
| Consistency | Are claims internally coherent and verified against the paper's text? |

Each dimension is scored 1.0–6.0 (coarse.ink displays this as `X/5` because their scale baseline is 5, but maximum is 6). The overall score is the mean of the four dimensions.

**Procedure:**

1. Adapt the disputatio output: `compare/adapt.py` flattens the structured Obsidian referee report into the flat-review format coarse.ink uses (Overall Feedback → Detailed Comments).
2. Optionally, generate a coarse baseline if one doesn't exist (`coarse_sonnet46.md` is a one-pass Sonnet 4.6 review of the same paper).
3. Run `compare/judge.py <paper>` — sends both reviews + the reference + (optionally) the paper PDF to the judge model.
4. Judge produces a JSON-structured `QualityReport` with per-dimension scores, reasoning, strengths, weaknesses.
5. By default, **positional-bias mitigation** is enabled: judge sees the same comparison twice with reviews A/B swapped, scores are inverted on the swap, and the two reports are averaged. This controls for "judge prefers whichever review it sees first."

**Modes:**

- `single` — one judge model (Gemini 2.5 Pro by default) with positional-bias swap. Two judge calls per review.
- `panel` (`--panel`) — three judge personas (methodology, empirical rigor, communication) each score, then a synthesis judge produces a single score from the three reports. Six judge calls per review.

**Multi-sample averaging:** judge.py outputs a single point estimate per run. Variance is non-trivial (σ ≈ 0.2 on coarse on the targeting paper), so multi-run averaging is needed for fine comparisons. The harness doesn't yet wrap a multi-run loop natively; it's done manually:

```bash
for i in {1..5}; do
  uv run python judge.py <paper> --review <review> --also-coarse \
    --model gemini/gemini-2.5-pro 2>&1 | grep "Overall:"
done
```

---

## Results on targeting-interventions

Galeotti, Golub & Goyal (2020), *Targeting interventions in networks*, Econometrica.

**Single-mode, 5 samples, Gemini 2.5 Pro judge, Stanford reference, positional-bias on:**

| Run | Disputatio v4 (auto-adapted) | Coarse (Sonnet 4.6 single-pass) |
|---:|---:|---:|
| 1 | 6.00 | 5.75 |
| 2 | 6.00 | 5.25 |
| 3 | 6.00 | 5.75 |
| 4 | 6.00 | 5.50 |
| 5 | 6.00 | 5.38 |
| **Mean** | **6.00** | **5.53** |
| **Stddev** | **0.00** | **0.21** |
| **Gap** | | **+0.47 (disputatio)** |

Every disputatio run hit ceiling (6.00). Every coarse run was below disputatio's worst. The 0.47 gap is more than 2× coarse's standard deviation.

**Panel-mode (3-persona synthesis), single sample:**

| | Disputatio | Coarse | Gap |
|---|---:|---:|---:|
| Overall | **5.62** | 5.12 | +0.50 |
| Coverage | 6.0 | 6.0 | 0 |
| Specificity | 5.5 | 4.5 | +1.0 |
| Depth | 6.0 | 6.0 | 0 |
| Consistency | 5.0 | 4.0 | +1.0 |

Panel mode produces lower absolute scores (more critical synthesis) but the gap is preserved or larger. Disputatio's advantage shows on specificity and consistency — exactly where the dialectical step would predict.

---

## What we cannot yet claim

- **Generalisation.** *n* = 1 paper. The targeting result does not establish that disputatio beats coarse on arbitrary papers. A second paper attempt (population-genetics) used a stale skill version on the disputatio side and was withdrawn pending re-run.
- **Cross-judge robustness.** All numbers are from Gemini 2.5 Pro. The same comparison with Opus or GPT-4 as judge has not been run. Could be a Gemini-specific preference.
- **Effort-matched comparison.** Coarse is one Sonnet pass (~30 s, ~$0.05 in API equivalent). Disputatio is ~2 h with three agents and many calls. They are not effort-matched. The fair claim is "given more compute and a structured protocol, you can produce a better review" — not "this is more efficient."
- **Adapter dependence.** The adapter `compare/adapt.py` is a confound. Different extraction choices (which sections to include, how to strip jargon) move the disputatio score by 0.5+ points without changing the underlying review. The current adapter (post-`30f2032`) is the one we benchmark with; different adapter choices would produce different numbers.

---

## 2. Per-finding blinded annotation (`templates/evaluation.md`)

A separate, complementary evaluation that doesn't compare reviews holistically. Instead, every individual finding from the merged issue register is annotated against the paper on two axes:

- **`quote_verified`** — does the cited quote actually exist in the paper, saying what the finding claims it says? (`yes` / `partial` / `no`)
- **`calibration`** — given the quote is real, does the evidence establish the claim at the stated strength? (`supported` / `overclaimed` / `unsupported`)

Aggregating across all findings produces three rates:

- **fabrication rate** = fraction with `quote_verified ≠ yes`
- **support rate** = fraction with `calibration = supported`
- **overclaim rate** = fraction with `calibration = overclaimed`

The overclaim rate is the discriminating metric — it captures whether a review walks back overconfident claims (low overclaim) or keeps them (high overclaim). The whole point of the dialectical step is to reduce overclaiming.

**Procedure:**

1. Strip identifying fields (`id`, `sources`, `rank_score`) from the merged issues. Shuffle. Assign blind IDs `BF001..BFNNN`.
2. Build a per-finding annotation prompt with the paper text + the blinded finding + the rubric.
3. Hand each prompt to a model (typically Codex `gpt-5.4-mini`, NOT Claude — to avoid same-model bias since Claude prosecuted the original disputatio findings).
4. Collect annotations, un-blind, compute rates.

**Blinding matters:** if the annotator can identify which review system produced a finding, they may rate generously or harshly accordingly. Stripping identity + shuffling + having a different model architecture annotate is the cheapest way to reduce this bias.

---

## Per-finding results: V2 vs V3 on targeting-interventions

This compares an earlier disputatio version (V2 — single-model debate) to the current cross-model debate (V3) on the same paper.

| Metric | V2 (single-model debate) | V3 (cross-model debate) | Δ |
|---|---:|---:|---:|
| n findings annotated | 15 | 27 | +12 |
| `quote_verified = yes` | 13 | 27 | +14 |
| `quote_verified = partial` | 2 | 0 | −2 |
| `quote_verified = no` | 0 | 0 | 0 |
| `calibration = supported` | 7 | 20 | +13 |
| `calibration = overclaimed` | 5 | 7 | +2 |
| `calibration = unsupported` | 3 | 0 | −3 |
| **fabrication rate** | 0.133 | 0.000 | **−0.133** |
| **support rate** | 0.467 | 0.741 | **+0.274** |
| **overclaim rate** | 0.333 | 0.259 | **−0.074** |

**Interpretation:**

- **Fabrication eliminated.** Every V3 finding cites a real quote at the stated location; V2 had two paraphrased quotes. Cross-agent dedup during merge plus the defender's requirement to reply to *exact quotes* filters paraphrase drift.
- **Support rate is the headline gain.** V3 produces substantively-supported findings 74% of the time vs 47% for V2 (+59% relative). Cross-model debate doesn't *mainly* reduce overclaims — it *mostly* surfaces supported issues that single-model V2 missed or under-weighted.
- **Overclaim rate dropped modestly** (0.333 → 0.259). The original target was ~0.15. The drop is real but smaller than hoped.

**Caveats:**

- *n* = 42 is small; differences are suggestive, not statistically significant.
- Single annotator (Codex `gpt-5.4-mini`); no double annotation, no inter-annotator reliability.
- Same annotator architecture (Codex) that served as V3's defender. A sensitivity check with a different annotator (Gemini, Opus) would strengthen the finding.

---

## Why two methodologies?

They answer different questions:

| Question | Methodology |
|---|---|
| Is this review better than other AI reviewers (against a human gold standard)? | LLM-as-judge (`judge.py`) |
| Are the findings inside this review actually correct against the paper? | Per-finding blinded annotation (`templates/evaluation.md`) |

The LLM-as-judge approach measures *holistic quality and competitive position*. The per-finding annotation measures *internal calibration*. A review can score well on the holistic judge while still containing several overclaimed findings; the blinded annotation surfaces this.

For publication-grade evidence on the disputatio thesis ("debate reduces overclaiming"), both methodologies should agree, on multiple papers, with multiple judges/annotators. We're at *n* = 1 for the holistic comparison and *n* = 1 paper × 2 versions for the blinded annotation. Multi-paper replication is the highest-priority next experiment.

---

## File reference

| File | Purpose |
|---|---|
| `compare/judge.py` | The LLM-as-judge harness. CLI: `judge.py <paper> [--review <file>] [--reference <file>] [--also-coarse] [--panel] [--model <model>]` |
| `compare/adapt.py` | Flattens disputatio's Obsidian referee report into coarse-compatible review format. CLI: `adapt.py [folder] [--report <path>] [-o <out>]` |
| `compare/<paper>/coarse_sonnet46.md` | Single-pass Sonnet 4.6 baseline review |
| `compare/<paper>/coarse_review.md` | An earlier coarse baseline |
| `compare/<paper>/reference_review.md` | Default reference (the one judge.py uses by default) |
| `compare/<paper>/reference_review_stanford.md` | Stanford Agentic Reviewer output |
| `compare/<paper>/eval_*.md` | Per-run scorecards from judge.py |
| `templates/evaluation.md` | The per-finding rubric |
| `<vault>/<paper-slug>/_evaluation/` | Per-paper blinded annotation outputs (manifest, prompts, annotations, scorecard) |
