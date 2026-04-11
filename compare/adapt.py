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

    # Extract sections
    summary = _extract_section(text, "Summary")
    material = _extract_section(text, "Material issues")
    local = _extract_section(text, "Local issues")
    verdict = _extract_section(text, "Overall verdict")

    # Build Overall Feedback
    overall_parts = []
    overall_parts.append("## Overall Feedback\n")
    if summary:
        overall_parts.append(f"**Central Assessment**\n{summary}\n")
    if verdict:
        overall_parts.append(f"**Overall Verdict**\n{verdict}\n")

    # Extract individual issues from material and local sections
    material_issues = _extract_issues(material, "Material") if material else []
    local_issues = _extract_issues(local, "Local") if local else []
    all_issues = material_issues + local_issues

    # Add main areas to overall feedback
    if all_issues:
        overall_parts.append("**Main Issues Identified**\n")
        for i, issue in enumerate(all_issues, 1):
            overall_parts.append(f"- **{issue['title']}** ({issue['severity']}): {issue['summary']}\n")

    # Build Detailed Comments
    comment_parts = []
    comment_parts.append(f"\n## Detailed Comments ({len(all_issues)})\n")

    for i, issue in enumerate(all_issues, 1):
        comment_parts.append(f"### {i}. {issue['title']}\n")
        comment_parts.append(f"**Status**: [Pending]\n")
        if issue.get("quote"):
            comment_parts.append(f"**Quote**:\n> {issue['quote']}\n")
        comment_parts.append(f"**Feedback**:\n{issue['feedback']}\n")
        if issue.get("fix"):
            comment_parts.append(f"It would be helpful to {issue['fix']}\n")
        comment_parts.append("---\n")

    # Combine
    header = f"# {_extract_title(text)}\n\n"
    header += f"**Date**: {_now()}\n"
    header += "**Domain**: Academic review\n"
    header += "**Method**: Disputatio (seven-method dialectic debate)\n\n---\n\n"

    return header + "\n".join(overall_parts) + "\n".join(comment_parts)


def adapt_from_folder(folder: Path) -> str:
    """Full mode: read issue register + debate summaries from Obsidian folder."""
    # Try to find key files
    issue_register = folder / "40_ranking" / "issue_register.md"
    final_report = folder / "60_final_report" / "referee_report.md"
    debates_dir = folder / "50_debates"

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
    debates_dir = folder / "50_debates"
    json_dir = folder / "_artifacts" / "json"

    header = "# Disputatio Review\n\n"
    header += f"**Date**: {_now()}\n"
    header += "**Method**: Seven-method dialectic debate (3 agents x 5 methods + structured disputation)\n\n---\n\n"

    # Overall Feedback
    parts = ["## Overall Feedback\n"]

    # Try to get summary from final report
    final_report = folder / "60_final_report" / "referee_report.md"
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
    """Extract numbered issues from a section."""
    issues = []
    # Pattern: "1. **title** — summary\n   - Constructive fix: ...\n"
    pattern = r"\d+\.\s+\*\*(.+?)\*\*\s*[—–-]\s*(.+?)(?=\n\d+\.|\Z)"
    for match in re.finditer(pattern, section, re.DOTALL):
        title = match.group(1).strip()
        body = match.group(2).strip()

        # Try to extract fix
        fix = ""
        fix_match = re.search(r"Constructive fix:\s*(.+?)(?:\n|$)", body)
        if fix_match:
            fix = fix_match.group(1).strip()
            body = body[:fix_match.start()].strip()

        # Try to extract quote
        quote = ""
        quote_match = re.search(r">\s*(.+?)(?:\n|$)", body)
        if quote_match:
            quote = quote_match.group(1).strip()

        issues.append({
            "title": title,
            "severity": severity,
            "summary": body.split("\n")[0].strip(),
            "feedback": body,
            "quote": quote,
            "fix": fix,
        })

    return issues


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
