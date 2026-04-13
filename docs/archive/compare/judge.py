"""Judge evaluation script — replicates coarse.ink's evaluation methodology.

Compares a generated review against a reference review using an LLM judge.
Supports single-judge and multi-judge panel evaluation with positional-bias
mitigation (swap ordering and average).

Uses the EXACT same prompts as coarse.ink for apples-to-apples comparison.

Usage:
    uv run judge targeting_interventions
    uv run judge targeting_interventions --panel
    uv run judge targeting_interventions --review disputatio_review.md
    uv run judge all --panel
"""
from __future__ import annotations

import argparse
import base64
import datetime
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import litellm
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

JUDGE_MODEL = "claude-opus-4-6"
COMPARE_DIR = Path(__file__).parent
PAPERS = [
    "targeting_interventions",
    "cortical_circuits",
    "coset_codes",
    "population_genetics",
]

# ---------------------------------------------------------------------------
# Pydantic models (mirror coarse exactly)
# ---------------------------------------------------------------------------

class DimensionScore(BaseModel):
    dimension: str
    score: float
    reasoning: str


class QualityReport(BaseModel):
    overall_score: float
    dimensions: list[DimensionScore]
    strengths: list[str]
    weaknesses: list[str]


# ---------------------------------------------------------------------------
# Judge prompts — verbatim from coarse.ink quality.py
# ---------------------------------------------------------------------------

JUDGE_SYSTEM = """\
You are an expert academic peer review evaluator. You have access to the \
original paper and two reviews labeled "Review A" and "Review B". One is a \
human-written reference and one is AI-generated. Your task is to assess \
Review B's quality primarily against the paper itself, using Review A \
for calibration.

IMPORTANT — Bias awareness:
- Do NOT favor a review because it is longer. A concise review that identifies \
real errors is better than a verbose review that pads with generic observations. \
Evaluate substance per comment, not total word count.
- Do NOT favor a review because it uses more confident or assertive language. \
A hedged but correct observation is better than a confident but wrong claim.
- Do NOT favor a review because it cites more sources or uses more technical \
jargon. Evaluate whether the technical content is correct, not whether it \
sounds impressive.
- USE THE FULL SCORING RANGE. A review with fabricated quotes or incorrect \
mathematical claims should score 1-2, not 3-4. Reserve scores of 3-4 for \
reviews that are mediocre but not actively wrong. Do not cluster scores in \
the middle of the scale.

Score each dimension from 1.0 to 6.0 in half-point increments \
(1, 1.5, 2, ..., 5, 5.5, 6). Use half-points to distinguish minor issues \
from major ones — e.g., one truncated quote out of 19 is a 4.5, not a 4.

The scale:
- 1.0-2.0: Major deficiencies — fabricated quotes, incorrect claims, \
missing the paper's central issues, or largely generic feedback
- 2.5-3.5: Partial quality — some valid points but significant gaps, \
errors in technical analysis, or mostly surface-level observations
- 4.0-4.5: Good but below reference — identifies real issues with \
some depth but misses important points or has minor inaccuracies
- 5.0: Matches the reference review in quality
- 5.5: Exceeds the reference — catches valid issues the reference missed, \
or provides deeper analysis on shared issues
- 6.0: Substantially exceeds the reference — identifies important errors or \
insights the reference missed entirely, with stronger evidence and reasoning

Award 5+ scores when Review B demonstrably surpasses Review A. \
This requires concrete evidence (e.g., found a real error the reference \
overlooked, provided a re-derivation where the reference only noted concern, \
or identified a cross-section inconsistency the reference missed).

Dimensions:
1. **coverage**: Does Review B identify the paper's most important \
issues? Evaluate this against the paper itself — what are the real strengths, \
weaknesses, and gaps? Review A may help calibrate what matters, but \
it is not the answer key. Credit Review B fully for finding valid \
issues Review A missed, and do not penalize it for omitting issues that \
are minor or debatable.
2. **specificity**: Are comments precise, with correct verbatim quotes from the \
paper and actionable guidance? Verify quotes against the paper text. Score 5 if \
every comment has an accurate quote and clear fix, 1 if comments are vague or \
quotes are fabricated. Score 5+ if quotes are more precise and fixes more \
concrete than Review A.
3. **depth**: Is the analysis substantive and technically rigorous? Does it \
engage with the paper's methodology, proofs, and assumptions at a deep level, \
or does it stay surface-level (notation complaints, formatting issues)? \
A long review full of surface observations scores LOWER than a short review \
with deep technical engagement. Score 5+ if the analysis provides deeper \
technical engagement than Review A \
(e.g., re-derivations, concrete counterexamples, numerical verification).
4. **consistency**: Does the review contradict the paper's own stated contributions \
or methodology without providing a concrete counterexample or derivation? \
Verify against the paper: if the paper claims to prove a result and the review \
asserts the opposite without a complete derivation, that is a consistency failure. \
Score 5 if every comment is consistent with the paper's claims (or provides \
explicit evidence when disagreeing). Score 1 if multiple comments directly assert \
the opposite of the paper's stated results without justification. Score 5+ if the \
review correctly identifies cases where the paper's own claims are internally \
inconsistent.

For each dimension, provide a brief reasoning string (1-2 sentences).

Also provide 2-3 strengths and 2-3 weaknesses of Review B as brief \
bullet strings.

Do not compute overall_score — it will be computed externally.
"""


def _build_user_prompt(
    reference: str,
    generated: str,
    paper_pdf: Path,
    swap: bool = False,
) -> str | list[dict]:
    """Build user prompt. Uses paper text (markdown) if available, else PDF."""
    if swap:
        review_a, review_b = generated, reference
    else:
        review_a, review_b = reference, generated

    # Prefer paper text (markdown) over PDF for text-based models
    paper_md = paper_pdf.parent / "paper.md"
    if paper_md.exists():
        paper_note = f"\n## Original Paper\n<paper>\n{paper_md.read_text()}\n</paper>\n\n"
        use_multimodal = False
    else:
        paper_note = (
            "\n## Original Paper\n"
            "The paper is attached as a PDF. Use it as the primary source of "
            "truth for verifying quotes and assessing coverage.\n\n"
        )
        use_multimodal = True

    prompt_text = f"""\
Evaluate Review B below. Use the paper as the primary source of truth \
and Review A for calibration (Review A is not an answer key).
{paper_note}\
## Review A (for calibration)
<review_a>
{review_a}
</review_a>

## Review B (evaluate this)
<review_b>
{review_b}
</review_b>

Score Review B on: coverage, specificity, depth, and consistency \
(each 1.0-6.0 in half-point increments, where 5.0 = matches Review A, \
5.5-6.0 = exceeds Review A).
Verify quotes against the paper text. Assess coverage and depth against the \
paper itself — does Review B find the paper's real issues and \
engage with its actual methodology and assumptions? Credit valid issues \
Review A missed — if Review B catches real errors Review A \
overlooked, that warrants a score above 5.0. Provide reasoning for each score, \
plus 2-3 strengths and 2-3 weaknesses.

Respond with valid JSON matching this schema:
{{
  "dimensions": [
    {{"dimension": "coverage", "score": <float>, "reasoning": "<string>"}},
    {{"dimension": "specificity", "score": <float>, "reasoning": "<string>"}},
    {{"dimension": "depth", "score": <float>, "reasoning": "<string>"}},
    {{"dimension": "consistency", "score": <float>, "reasoning": "<string>"}}
  ],
  "strengths": ["<string>", ...],
  "weaknesses": ["<string>", ...]
}}
"""
    if use_multimodal:
        pdf_b64 = base64.b64encode(paper_pdf.read_bytes()).decode()
        return [
            {"type": "text", "text": prompt_text},
            {
                "type": "image_url",
                "image_url": {"url": f"data:application/pdf;base64,{pdf_b64}"},
            },
        ]
    return prompt_text


# ---------------------------------------------------------------------------
# Panel judge personas — verbatim from coarse
# ---------------------------------------------------------------------------

JUDGE_PERSONAS = [
    "You are an expert in mathematical methodology and statistical theory. "
    "Focus especially on proof correctness, rate conditions, whether "
    "assumptions are internally consistent, and whether the review's claims "
    "are consistent with what the paper actually states.",
    "You are an expert in empirical research design and applied methodology. "
    "Focus especially on whether the paper's empirical implementation matches "
    "its theoretical claims, and whether simulations test the right properties.",
    "You are an expert in scientific communication and research impact. "
    "Focus especially on whether the review identifies the most important "
    "issues, whether comments are actionable, and whether coverage is complete.",
]

SYNTHESIS_SYSTEM = """\
You are a meta-evaluator synthesizing multiple independent quality assessments \
of an AI-generated academic paper review. You have received reports from a panel \
of expert judges, each with a distinct perspective (methodology, empirical design, \
communication).

Your task:
1. For each dimension (coverage, specificity, depth, consistency), determine a \
final consensus score (1.0-6.0 in half-point increments, where 5+ means exceeds \
the reference) that FAITHFULLY reflects the panel's actual scores. Your score \
must stay within the range of the judges' scores. Do NOT introduce your own \
independent assessment or dock points for issues the judges did not penalize. \
When judges disagree, weight toward the more critical judge.
2. Synthesize 3-5 key strengths from across all judges' reports (deduplicate).
3. Synthesize 3-5 key weaknesses (deduplicate and prioritize the most actionable).

For each dimension score, provide reasoning that references which judges agreed \
or disagreed and why you chose the final score.

Respond with valid JSON matching this schema:
{
  "dimensions": [
    {"dimension": "coverage", "score": <float>, "reasoning": "<string>"},
    {"dimension": "specificity", "score": <float>, "reasoning": "<string>"},
    {"dimension": "depth", "score": <float>, "reasoning": "<string>"},
    {"dimension": "consistency", "score": <float>, "reasoning": "<string>"}
  ],
  "strengths": ["<string>", ...],
  "weaknesses": ["<string>", ...]
}
"""


# ---------------------------------------------------------------------------
# LLM call helper
# ---------------------------------------------------------------------------

def _call_judge(
    system: str,
    user_content: str | list[dict],
    model: str = JUDGE_MODEL,
    max_tokens: int = 8192,
) -> dict:
    """Call LLM and parse JSON response.

    Some judge models (notably gemini-3.1-pro-preview) occasionally emit
    JSON with invalid LaTeX backslash escapes or extra commentary outside
    the JSON block. Try strict parse first; on failure, attempt a salvage
    pass before giving up.
    """
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_content},
    ]
    resp = litellm.completion(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.0,
        response_format={"type": "json_object"},
    )
    text = resp.choices[0].message.content

    # Strip markdown fences if present
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.split("\n")
        # Drop opening fence (and language tag) plus closing fence
        text = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])

    try:
        return json.loads(text)
    except json.JSONDecodeError as first_err:
        # Salvage: extract the largest balanced {...} block, clean LaTeX
        # backslash escapes, and retry. If that still fails, raise the
        # original error with context for debugging.
        salvaged = _salvage_judge_json(text)
        if salvaged is not None:
            return salvaged
        raise json.JSONDecodeError(
            f"{first_err.msg} (and salvage failed). "
            f"First 200 chars of judge response: {text[:200]!r}",
            first_err.doc,
            first_err.pos,
        )


def _salvage_judge_json(text: str) -> dict | None:
    """Best-effort JSON salvage for malformed judge output. Returns the
    parsed dict on success, None on failure.

    Strategy: find the outermost {...}, normalise runaway backslashes
    (collapse runs of 2+ to 2, then double remaining bare backslashes
    that precede invalid escape chars), strip control characters and
    trailing commas. Same logic as agent_ctl._clean_json_text.
    """
    import re as _re
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    candidate = text[start : end + 1]
    candidate = _re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", candidate)
    candidate = _re.sub(r"\\{2,}", r"\\\\", candidate)
    for _ in range(3):
        fixed = _re.sub(r'(?<!\\)\\(?!["\\/bfnrtu])', r'\\\\', candidate)
        if fixed == candidate:
            break
        candidate = fixed
    candidate = _re.sub(r",\s*([}\]])", r"\1", candidate)
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------------------
# Single-judge evaluation with positional-bias mitigation
# ---------------------------------------------------------------------------

def evaluate_single(
    generated: str,
    reference: str,
    paper_pdf: Path,
    model: str = JUDGE_MODEL,
) -> QualityReport:
    """Run judge twice (normal + swapped) and average scores."""

    def _run(swap: bool) -> dict:
        user = _build_user_prompt(reference, generated, paper_pdf, swap=swap)
        return _call_judge(JUDGE_SYSTEM, user, model=model)

    with ThreadPoolExecutor(max_workers=2) as pool:
        fut_normal = pool.submit(_run, False)
        fut_swapped = pool.submit(_run, True)
        result_normal = fut_normal.result()
        result_swapped = fut_swapped.result()

    # Build dimension lookup for swapped result
    swapped_dims = {d["dimension"]: d["score"] for d in result_swapped["dimensions"]}

    dims = []
    for d in result_normal["dimensions"]:
        normal_score = d["score"]
        dim_name = d["dimension"]
        if dim_name in swapped_dims:
            # Invert: if ref scored S vs gen, gen is 10-S (clamped to [1,6])
            inverted = max(1.0, min(6.0, 10.0 - swapped_dims[dim_name]))
            avg = round((normal_score + inverted) * 2) / 4
            avg = round(avg * 2) / 2  # nearest 0.5
        else:
            avg = normal_score
        dims.append(DimensionScore(
            dimension=dim_name,
            score=avg,
            reasoning=d["reasoning"],
        ))

    overall = sum(d.score for d in dims) / len(dims)
    return QualityReport(
        overall_score=round(overall * 100) / 100,
        dimensions=dims,
        strengths=result_normal.get("strengths", []),
        weaknesses=result_normal.get("weaknesses", []),
    )


# ---------------------------------------------------------------------------
# Panel evaluation
# ---------------------------------------------------------------------------

def evaluate_panel(
    generated: str,
    reference: str,
    paper_pdf: Path,
    model: str = JUDGE_MODEL,
) -> tuple[QualityReport, list[QualityReport]]:
    """Run 3-judge panel + synthesis. Returns (synthesized, individual)."""
    user_content = _build_user_prompt(reference, generated, paper_pdf)

    def _run_judge(persona: str) -> QualityReport:
        system = persona + "\n\n" + JUDGE_SYSTEM
        result = _call_judge(system, user_content, model=model)
        dims = [DimensionScore(**d) for d in result["dimensions"]]
        overall = sum(d.score for d in dims) / len(dims)
        return QualityReport(
            overall_score=round(overall * 100) / 100,
            dimensions=dims,
            strengths=result.get("strengths", []),
            weaknesses=result.get("weaknesses", []),
        )

    individual: list[QualityReport] = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(_run_judge, p) for p in JUDGE_PERSONAS]
        for f in futures:
            try:
                individual.append(f.result())
            except Exception as e:
                print(f"  Judge failed: {e}", file=sys.stderr)

    if not individual:
        raise RuntimeError("All judges failed")

    if len(individual) < 3:
        # Fallback: average
        return _average_reports(individual), individual

    # Synthesize
    labels = ["Methodology Judge", "Empirical Judge", "Communication Judge"]
    parts = []
    for i, report in enumerate(individual):
        dim_str = "\n".join(
            f"  - {d.dimension}: {d.score}/6 — {d.reasoning}"
            for d in report.dimensions
        )
        str_str = "\n".join(f"  + {s}" for s in report.strengths)
        weak_str = "\n".join(f"  - {w}" for w in report.weaknesses)
        parts.append(
            f"### {labels[i]} (Overall: {report.overall_score:.1f})\n"
            f"**Scores:**\n{dim_str}\n"
            f"**Strengths:**\n{str_str}\n"
            f"**Weaknesses:**\n{weak_str}"
        )

    synth_user = (
        "Synthesize the following quality assessments from a panel of 3 expert judges.\n\n"
        + "\n\n".join(parts)
        + "\n\nDetermine consensus scores, synthesize strengths/weaknesses."
    )
    synth_result = _call_judge(SYNTHESIS_SYSTEM, synth_user, model=model)
    synth_dims = [DimensionScore(**d) for d in synth_result["dimensions"]]
    overall = sum(d.score for d in synth_dims) / len(synth_dims)
    synthesized = QualityReport(
        overall_score=round(overall * 100) / 100,
        dimensions=synth_dims,
        strengths=synth_result.get("strengths", []),
        weaknesses=synth_result.get("weaknesses", []),
    )
    return synthesized, individual


def _average_reports(reports: list[QualityReport]) -> QualityReport:
    dim_scores: dict[str, list[float]] = {}
    for r in reports:
        for d in r.dimensions:
            dim_scores.setdefault(d.dimension, []).append(d.score)
    dims = [
        DimensionScore(
            dimension=name,
            score=round(sum(scores) / len(scores) * 2) / 2,
            reasoning=f"Average of {len(scores)} judge(s)",
        )
        for name, scores in dim_scores.items()
    ]
    overall = sum(d.score for d in dims) / len(dims) if dims else 0.0
    return QualityReport(
        overall_score=round(overall * 100) / 100,
        dimensions=dims,
        strengths=[s for r in reports for s in r.strengths][:5],
        weaknesses=[w for r in reports for w in r.weaknesses][:5],
    )


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------

def render_report(
    report: QualityReport,
    paper_name: str,
    review_name: str,
    reference_name: str,
    model: str,
    mode: str,
) -> str:
    timestamp = datetime.datetime.now().isoformat(timespec="seconds")
    dim_rows = "\n".join(
        f"| {d.dimension} | {d.score}/6 | {d.reasoning} |"
        for d in report.dimensions
    )
    strengths = "\n".join(f"- {s}" for s in report.strengths)
    weaknesses = "\n".join(f"- {w}" for w in report.weaknesses)

    return f"""\
# Quality Evaluation — {paper_name}

**Timestamp**: {timestamp}
**Review**: {review_name}
**Reference**: {reference_name}
**Judge model**: {model}
**Mode**: {mode}

## Overall Score: {report.overall_score:.2f}/6.0

## Dimensions

| Dimension | Score | Reasoning |
|-----------|-------|-----------|
{dim_rows}

## Strengths

{strengths}

## Weaknesses

{weaknesses}
"""


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Judge evaluation for disputatio comparison")
    parser.add_argument("paper", help="Paper name or 'all'")
    parser.add_argument("--review", default="disputatio_review.md",
                        help="Review file to evaluate (relative to paper dir)")
    parser.add_argument("--reference", default="reference_review.md",
                        help="Reference review file")
    parser.add_argument("--panel", action="store_true",
                        help="Use multi-judge panel instead of single judge")
    parser.add_argument("--model", default=JUDGE_MODEL,
                        help=f"Judge model (default: {JUDGE_MODEL})")
    parser.add_argument("--also-coarse", action="store_true",
                        help="Also evaluate coarse's review for direct comparison")
    args = parser.parse_args()

    papers = PAPERS if args.paper == "all" else [args.paper]

    for paper_name in papers:
        paper_dir = COMPARE_DIR / paper_name
        paper_pdf = paper_dir / "paper.pdf"
        reference_path = paper_dir / args.reference
        review_path = paper_dir / args.review

        if not paper_pdf.exists():
            print(f"SKIP {paper_name}: no paper.pdf", file=sys.stderr)
            continue
        if not review_path.exists():
            print(f"SKIP {paper_name}: no {args.review}", file=sys.stderr)
            continue

        reference = reference_path.read_text()
        generated = review_path.read_text()

        print(f"\n{'='*60}")
        print(f"Evaluating: {paper_name} / {args.review}")
        print(f"{'='*60}")

        mode = "panel" if args.panel else "single"

        if args.panel:
            report, individual = evaluate_panel(
                generated, reference, paper_pdf, model=args.model
            )
            # Save individual reports too
            for i, ind in enumerate(individual):
                label = ["methodology", "empirical", "communication"][i]
                out = render_report(
                    ind, paper_name, args.review, args.reference, args.model,
                    f"panel-{label}",
                )
                out_path = paper_dir / f"eval_{review_path.stem}_judge_{label}.md"
                out_path.write_text(out)
                print(f"  Saved {label} judge: {out_path.name}")
        else:
            report = evaluate_single(
                generated, reference, paper_pdf, model=args.model
            )

        # Save main report
        out = render_report(
            report, paper_name, args.review, args.reference, args.model, mode,
        )
        out_path = paper_dir / f"eval_{review_path.stem}_{mode}.md"
        out_path.write_text(out)

        # Print summary
        print(f"\n  Overall: {report.overall_score:.2f}/6.0")
        for d in report.dimensions:
            print(f"  {d.dimension:15s}: {d.score}/6")
        print(f"\n  Saved: {out_path.name}")

        # Also evaluate coarse if requested
        if args.also_coarse:
            coarse_path = paper_dir / "coarse_sonnet46.md"
            if coarse_path.exists():
                coarse_text = coarse_path.read_text()
                print(f"\n  --- Evaluating coarse (Sonnet 4.6) for comparison ---")
                if args.panel:
                    coarse_report, _ = evaluate_panel(
                        coarse_text, reference, paper_pdf, model=args.model
                    )
                else:
                    coarse_report = evaluate_single(
                        coarse_text, reference, paper_pdf, model=args.model
                    )
                coarse_out = render_report(
                    coarse_report, paper_name, "coarse_sonnet46.md",
                    args.reference, args.model, mode,
                )
                coarse_out_path = paper_dir / f"eval_coarse_sonnet46_{mode}.md"
                coarse_out_path.write_text(coarse_out)
                print(f"  Coarse Overall: {coarse_report.overall_score:.2f}/6.0")
                for d in coarse_report.dimensions:
                    print(f"  {d.dimension:15s}: {d.score}/6")
                print(f"  Saved: {coarse_out_path.name}")

    # Print comparison table if multiple papers
    print("\n" + "=" * 60)
    print("Done.")


if __name__ == "__main__":
    main()
