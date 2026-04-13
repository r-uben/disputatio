"""Format adapter: disputatio output → coarse-compatible review format.

Disputatio produces a rich dialectic with debate rounds, surviving/conceded
objections, and structured issue registers. Coarse expects a flat review with:
  - Overall Feedback section (summary + main issues)
  - Detailed Comments section (numbered, each with quote + feedback)

This adapter reads disputatio's output artifacts and flattens them.

It can work in two modes:
1. **Full mode**: reads the issue register + debate summaries from the Obsidian
   folder structure. Requires a completed disputatio run.
2. **Report mode**: reads just the final referee_report.md and flattens it.
   Less rich but works with just the final output.

Usage:
    uv run adapt <paper-folder>                     # full mode
    uv run adapt --report referee_report.md          # report mode
    uv run adapt --report referee_report.md -o out.md
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

COMPARE_DIR = Path(__file__).parent


def adapt_from_report(report_path: Path) -> str:
    """Flatten a disputatio referee_report.md into coarse review format."""
    text = report_path.read_text()

    # Extract sections. Templates vary on the exact heading wording
    # ("Material issues" vs "Material findings"; "Summary" vs "Overall
    # assessment"; "Overall verdict" vs "Overall verdict"). Try both.
    summary = (_extract_section(text, "Summary")
               or _extract_section(text, "Overall assessment"))
    material = (_extract_section(text, "Material issues")
                or _extract_section(text, "Material findings"))
    local = (_extract_section(text, "Local issues")
             or _extract_section(text, "Local findings"))
    appendix = (_extract_section(text, "Appendix concerns")
                or _extract_section(text, "Appendix findings"))
    verdict = _extract_section(text, "Overall verdict")

    # Strip wikilinks / provenance from summary and verdict so process
    # jargon doesn't bleed through.
    summary = _strip_process_jargon(summary)
    verdict = _strip_process_jargon(verdict)

    # Build Overall Feedback
    overall_parts = []
    overall_parts.append("## Overall Feedback\n")
    if summary:
        overall_parts.append(f"**Central Assessment**\n{summary}\n")
    if verdict:
        overall_parts.append(f"**Overall Verdict**\n{verdict}\n")

    # Extract individual issues from material, local, and appendix sections
    material_issues = _extract_issues(material, "Material") if material else []
    local_issues = _extract_issues(local, "Local") if local else []
    appendix_issues = _extract_appendix_issues(appendix) if appendix else []
    all_issues = material_issues + local_issues + appendix_issues

    # Add main areas to overall feedback
    if all_issues:
        overall_parts.append("**Main Issues Identified**\n")
        for i, issue in enumerate(all_issues, 1):
            overall_parts.append(f"- **{issue['title']}**: {issue['summary']}\n")

    # Build Detailed Comments
    comment_parts = []
    comment_parts.append(f"\n## Detailed Comments ({len(all_issues)})\n")

    for i, issue in enumerate(all_issues, 1):
        comment_parts.append(f"### {i}. {issue['title']}\n")
        if issue.get("quote"):
            comment_parts.append(f"> {issue['quote']}\n")
        comment_parts.append(issue["feedback"] + "\n")
        if issue.get("fix"):
            comment_parts.append(f"It would be helpful to {issue['fix']}.\n")

    # Combine (no process jargon in the header)
    header = f"# {_extract_title(text)}\n\n"
    header += f"**Date**: {_now()}\n"
    header += "**Domain**: Academic review\n\n---\n\n"

    return header + "\n".join(overall_parts) + "\n".join(comment_parts)


def _strip_process_jargon(text: str) -> str:
    """Remove disputatio-specific structural labels and wikilinks so the
    output reads as a natural review, not a pipeline artifact."""
    t = text
    # Remove bullet quotes pointing to internal artifacts
    t = re.sub(r"^>\s*.*?\n", "", t, flags=re.MULTILINE)
    # Strip Obsidian wikilinks
    t = re.sub(r"\[\[.+?\]\]", "", t)
    # Strip bold process labels
    for label in ("Refined claim", "Accepted facts", "Constructive fix",
                  "Provenance", "Status", "Defense established",
                  "Attack established"):
        t = re.sub(rf"\*\*{re.escape(label)}\.\*\*\s*", "", t)
    # Strip rank citations
    t = re.sub(r"\s*·\s*rank\s+\d+/\d+\.?", "", t)
    return t.strip()


def _extract_appendix_issues(section: str) -> list[dict]:
    """Extract appendix concerns. Templates vary between two formats:

    1) Bullet list keyed by internal id:
         - **merged_NNN** (short name): description.
    2) Numbered headings just like material/local:
         ### N. Title (rank X/15)
         body

    Try (1) first; fall back to _extract_issues for (2).
    """
    issues = []
    pat = re.compile(
        r"^\s*-\s+\*\*(merged_\d+)\*\*\s*\(([^)]+)\):\s*(.+?)(?=^\s*-\s+\*\*merged_|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    for m in pat.finditer(section):
        name = m.group(2).strip()
        body = m.group(3).strip().rstrip(".")
        title = name[0].upper() + name[1:] if name else "Appendix concern"
        issues.append({
            "title": title,
            "severity": "Appendix",
            "summary": body.split(".")[0][:160].strip() + ".",
            "feedback": body,
            "quote": "",
            "fix": "",
        })

    if not issues:
        # Fall back to material-style headings. Strip the trailing "(rank
        # X/15)" parenthetical from titles so the flat review reads clean.
        issues = _extract_issues(section, "Appendix")
        for it in issues:
            it["title"] = re.sub(r"\s*\(rank\s+\d+/\d+\)\s*$", "",
                                 it["title"]).strip()

    return issues


def adapt_from_folder(folder: Path) -> str:
    """Full mode: read issue register + debate summaries from Obsidian folder."""
    # Try to find key files
    issue_register = folder / "2_ranking" / "issue_register.md"
    final_report = folder / "4_report" / "referee_report.md"
    debates_dir = folder / "3_debates"

    if final_report.exists():
        # Start with report-mode output, then enrich with debate data
        base = adapt_from_report(final_report)
    else:
        base = ""

    # If we have debate summaries, enrich the detailed comments
    if debates_dir.exists():
        debate_summaries = sorted(debates_dir.glob("*/99_summary.md"))
        if debate_summaries:
            enrichments = []
            for summary_path in debate_summaries:
                summary_text = summary_path.read_text()
                enrichments.append(_extract_debate_enrichment(summary_text))
            # TODO: merge enrichments into base comments
            pass

    # If we have the issue register, use it for ranking info
    if issue_register.exists():
        register_text = issue_register.read_text()
        # TODO: extract ranking scores and cross-agent support
        pass

    # Also check for raw JSON artifacts
    json_dir = folder / "_artifacts" / "json"
    if json_dir.exists():
        # Try loading the merged/ranked issues
        merge_files = sorted(json_dir.glob("merge_rank*.json"))
        if merge_files:
            try:
                merged = json.loads(merge_files[-1].read_text())
                return _adapt_from_merged_json(merged, folder)
            except (json.JSONDecodeError, KeyError):
                pass

    return base if base else "Error: no disputatio output found"


def _adapt_from_merged_json(merged: dict | list, folder: Path) -> str:
    """Build coarse-format review from merged issue JSON + debate outputs."""
    issues = merged if isinstance(merged, list) else merged.get("issues", [])

    # Try to load debate synthesis for each issue
    debates_dir = folder / "3_debates"
    json_dir = folder / "_artifacts" / "json"

    header = "# Disputatio Review\n\n"
    header += f"**Date**: {_now()}\n"
    header += "**Method**: Seven-method dialectic debate (3 agents x 5 methods + structured disputation)\n\n---\n\n"

    # Overall Feedback
    parts = ["## Overall Feedback\n"]

    # Try to get summary from final report
    final_report = folder / "4_report" / "referee_report.md"
    if final_report.exists():
        summary = _extract_section(final_report.read_text(), "Summary")
        if summary:
            parts.append(f"**Central Assessment**\n{summary}\n")

    # List top issues
    parts.append("**Main Issues Identified**\n")
    for issue in issues:
        title = issue.get("title", issue.get("short_title", "Untitled"))
        severity = issue.get("impact", issue.get("severity", "unknown"))
        claim = issue.get("claim", issue.get("summary", ""))
        agents = issue.get("sources", issue.get("agents", []))
        agent_str = f" (found by {', '.join(agents)})" if agents else ""
        rank = issue.get("rank_score", "")
        rank_str = f" [rank: {rank}]" if rank else ""
        parts.append(f"- **{title}** ({severity}{rank_str}): {claim}{agent_str}\n")

    # Detailed Comments
    parts.append(f"\n## Detailed Comments ({len(issues)})\n")

    for i, issue in enumerate(issues, 1):
        title = issue.get("title", issue.get("short_title", f"Issue {i}"))
        parts.append(f"### {i}. {title}\n")
        parts.append("**Status**: [Pending]\n")

        # Quote
        quote = issue.get("quote", issue.get("evidence_quote", ""))
        location = issue.get("location", issue.get("section", ""))
        if quote:
            loc_str = f" ({location})" if location else ""
            parts.append(f"**Quote**{loc_str}:\n> {quote}\n")

        # Core claim/feedback
        claim = issue.get("claim", "")
        evidence = issue.get("evidence", issue.get("reasoning", ""))
        feedback = claim
        if evidence:
            feedback += f"\n\n{evidence}"

        # Enrich with debate outcome if available
        issue_id = issue.get("id", issue.get("issue_id", ""))
        debate_enrichment = _load_debate_outcome(issue_id, debates_dir, json_dir)
        if debate_enrichment:
            feedback += f"\n\n**Debate outcome**: {debate_enrichment}"

        parts.append(f"**Feedback**:\n{feedback}\n")

        # Fix suggestion
        fix = issue.get("constructive_fix", issue.get("suggestion", ""))
        falsifier = issue.get("falsifier", "")
        if fix:
            parts.append(f"It would be helpful to {fix}\n")
        elif falsifier:
            parts.append(f"This issue could be resolved by: {falsifier}\n")

        # Metadata
        methods = issue.get("methods", [])
        agents = issue.get("sources", issue.get("agents", []))
        confidence = issue.get("confidence", "")
        meta_parts = []
        if methods:
            meta_parts.append(f"Methods: {', '.join(methods)}")
        if agents:
            meta_parts.append(f"Agents: {', '.join(agents)}")
        if confidence:
            meta_parts.append(f"Confidence: {confidence}")
        if meta_parts:
            parts.append(f"*{' | '.join(meta_parts)}*\n")

        parts.append("---\n")

    return header + "\n".join(parts)


def _load_debate_outcome(
    issue_id: str, debates_dir: Path, json_dir: Path,
) -> str:
    """Try to load debate synthesis for an issue."""
    if not issue_id:
        return ""

    # Try debate summary markdown
    if debates_dir.exists():
        for debate_folder in debates_dir.iterdir():
            summary = debate_folder / "99_summary.md"
            if summary.exists() and issue_id in debate_folder.name:
                text = summary.read_text()
                verdict = _extract_section(text, "Status")
                refined = _extract_section(text, "Refined claim")
                if verdict or refined:
                    result = ""
                    if verdict:
                        result += verdict.strip()
                    if refined:
                        result += f" Refined claim: {refined.strip()}"
                    return result

    # Try JSON synthesis
    if json_dir.exists():
        synth_files = sorted(json_dir.glob(f"debate_{issue_id}*synthesize*.json"))
        if synth_files:
            try:
                data = json.loads(synth_files[-1].read_text())
                return data.get("refined_claim", data.get("synthesis", ""))
            except (json.JSONDecodeError, KeyError):
                pass

    return ""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_section(text: str, heading: str) -> str:
    """Extract content under a markdown heading."""
    pattern = rf"^##\s+{re.escape(heading)}.*?\n(.*?)(?=^##\s|\Z)"
    match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    if match:
        return match.group(1).strip()
    # Try with parenthetical like "## Material issues (3)"
    pattern = rf"^##\s+{re.escape(heading)}\s*\(.*?\)\s*\n(.*?)(?=^##\s|\Z)"
    match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""


def _extract_title(text: str) -> str:
    """Extract title from first H1."""
    match = re.search(r"^#\s+(.+)", text, re.MULTILINE)
    return match.group(1).strip() if match else "Review"


def _extract_issues(section: str, severity: str) -> list[dict]:
    """Extract numbered issues from a section.

    Handles two formats produced by templates/final_report.md:

    Material format: each issue is `### N. Title`, then a body containing
    `**Refined claim.** ... **Accepted facts.** ... **Constructive fix.** ...
    **Provenance.** ...` before the next `###` or end.

    Local format: each issue is a numbered list item `N. **Title.** body Fix:
    ... [[...]] · rank X/15.` with the whole item on a single line (no nested
    ###).
    """
    issues = []

    # Material format: "### N. Title\n\nbody..."
    material_pat = re.compile(
        r"^###\s+\d+\.\s+(.+?)\n(.+?)(?=^###\s+\d+\.|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    for m in material_pat.finditer(section):
        title = m.group(1).strip()
        body = m.group(2).strip()

        refined = _extract_bold_field(body, "Refined claim")
        fix = _extract_bold_field(body, "Constructive fix")
        # Strip provenance wikilinks from the feedback
        feedback = re.sub(r"\*\*Provenance\.\*\*.*$", "", body,
                          flags=re.DOTALL).strip()
        feedback = re.sub(r"\[\[.+?\]\]", "", feedback).strip()

        summary = refined if refined else feedback.split("\n")[0].strip()

        # Fix phrasing: adapter wraps as "It would be helpful to <fix>"
        fix_phrase = fix
        if fix_phrase:
            # Drop leading imperative ("Either ..., or ..." / "Add ...") into
            # a fragment that reads naturally after "It would be helpful to".
            fix_phrase = _to_fix_phrase(fix_phrase)

        issues.append({
            "title": title,
            "severity": severity,
            "summary": summary,
            "feedback": feedback,
            "quote": "",
            "fix": fix_phrase,
        })

    if issues:
        return issues

    # Local format: numbered list items, each entry on one logical line.
    # Match "N. **Title.** body..." until the next "N. " at line start or end.
    local_pat = re.compile(
        r"^\s*\d+\.\s+\*\*(.+?)\*\*\s*(.+?)(?=^\s*\d+\.\s+\*\*|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    for m in local_pat.finditer(section):
        title = m.group(1).strip().rstrip(".")
        body = m.group(2).strip()

        # Strip rank + wikilinks
        body_clean = re.sub(r"\[\[.+?\]\].*?rank\s+\d+/\d+\.?\s*$",
                            "", body, flags=re.DOTALL).strip()
        body_clean = re.sub(r"\[\[.+?\]\]", "", body_clean).strip()

        # Extract fix
        fix = ""
        fix_match = re.search(r"Fix:\s*(.+?)$", body_clean, re.DOTALL)
        if fix_match:
            fix = fix_match.group(1).strip().rstrip(".")
            body_clean = body_clean[:fix_match.start()].strip()
            fix = _to_fix_phrase(fix)

        issues.append({
            "title": title,
            "severity": severity,
            "summary": body_clean.split(".")[0].strip() + ".",
            "feedback": body_clean,
            "quote": "",
            "fix": fix,
        })

    return issues


def _extract_bold_field(body: str, field: str) -> str:
    """Pull the content of a '**Field.** ...' segment up to the next bold
    field or blank-paragraph break."""
    pat = rf"\*\*{re.escape(field)}\.\*\*\s*(.+?)(?=\n\n\*\*|\Z)"
    m = re.search(pat, body, re.DOTALL)
    return m.group(1).strip() if m else ""


def _to_fix_phrase(text: str) -> str:
    """Turn an imperative-form fix ('Add X', 'Either A or B') into a phrase
    suitable after 'It would be helpful to '. Keeps the original wording for
    non-imperatives."""
    t = text.strip()
    # Lowercase leading imperative verbs that we know about
    leading = re.match(r"^(Add|Replace|Correct|Insert|Update|Either|Consider|Drop|Print|Change|State|Qualify|Scope|Include|Note|Clarify|Restrict|Explicitly)\b",
                       t)
    if leading:
        verb = leading.group(1)
        rest = t[len(verb):]
        return verb.lower() + rest
    return t


def _extract_debate_enrichment(summary_text: str) -> str:
    """Extract key debate outcome from a debate summary."""
    verdict = _extract_section(summary_text, "Status")
    refined = _extract_section(summary_text, "Refined claim")
    accepted = _extract_section(summary_text, "Accepted facts")
    parts = []
    if verdict:
        parts.append(f"Verdict: {verdict}")
    if refined:
        parts.append(f"Refined claim: {refined}")
    if accepted:
        parts.append(f"Accepted: {accepted}")
    return " | ".join(parts) if parts else ""


def _now() -> str:
    import datetime
    return datetime.datetime.now().strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Adapt disputatio output to coarse review format")
    parser.add_argument("folder", nargs="?", help="Disputatio paper folder (Obsidian)")
    parser.add_argument("--report", help="Path to referee_report.md (report mode)")
    parser.add_argument("-o", "--output", help="Output path (default: stdout)")
    args = parser.parse_args()

    if args.report:
        result = adapt_from_report(Path(args.report))
    elif args.folder:
        result = adapt_from_folder(Path(args.folder))
    else:
        parser.error("Provide either a folder path or --report")

    if args.output:
        Path(args.output).write_text(result)
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(result)


if __name__ == "__main__":
    main()
