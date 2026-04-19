"""
Generate social-report.md from profile + posts data.
"""

import json
from pathlib import Path
from datetime import datetime


def generate(
    slug: str,
    run_id: str,
    profile_summary: dict,
    posts: list,
    output_dir: Path,
) -> Path:
    """
    Write social-report.md to output_dir. Returns the path.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "social-report.md"

    lines = []
    lines.append(f"# Social Decode: {slug}")
    lines.append(f"**Run ID:** {run_id}")
    lines.append(f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("")

    # --- Company Profile ---
    lines.append("## Company Profile")
    lines.append("")
    name = profile_summary.get("name", slug)
    lines.append(f"**Company:** {name}")
    if profile_summary.get("tagline"):
        lines.append(f"**Tagline:** {profile_summary['tagline']}")
    if profile_summary.get("description"):
        lines.append(f"**Description:** {profile_summary['description']}")
    if profile_summary.get("industry"):
        lines.append(f"**Industry:** {profile_summary['industry']}")
    if profile_summary.get("company_size"):
        lines.append(f"**Company Size:** {profile_summary['company_size']}")
    if profile_summary.get("follower_count"):
        lines.append(f"**Followers:** {profile_summary['follower_count']}")
    if profile_summary.get("headquarters"):
        lines.append(f"**Headquarters:** {profile_summary['headquarters']}")
    if profile_summary.get("founded"):
        lines.append(f"**Founded:** {profile_summary['founded']}")
    if profile_summary.get("website"):
        lines.append(f"**Website:** {profile_summary['website']}")
    if profile_summary.get("specialties"):
        specs = profile_summary["specialties"]
        if isinstance(specs, list):
            specs = ", ".join(str(s) for s in specs)
        lines.append(f"**Specialties:** {specs}")
    lines.append("")

    # --- Posts ---
    lines.append(f"## Last {len(posts)} Posts")
    lines.append("")

    if not posts:
        lines.append("_No posts retrieved._")
        lines.append("")
    else:
        for post in posts:
            idx = post.get("index", "?")
            ptype = post.get("type", "text").upper()
            lines.append(f"### Post {idx} [{ptype}]")
            if post.get("urn"):
                lines.append(f"**URN/ID:** `{post['urn']}`")
            text = post.get("text", "").strip()
            if text:
                lines.append("")
                lines.append(text)
            lines.append("")

    # --- Raw JSON ---
    lines.append("## Raw Profile JSON")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(profile_summary, indent=2))
    lines.append("```")
    lines.append("")

    lines.append("## Raw Posts JSON")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(posts, indent=2))
    lines.append("```")
    lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  Report saved: {report_path}")
    return report_path
