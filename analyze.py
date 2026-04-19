#!/usr/bin/env python3
"""
social-decoder: Fetch LinkedIn company profile + posts, screenshot, and decode.

Usage:
  python analyze.py <linkedin_slug> [--max-posts N]

Examples:
  python analyze.py cyera
  python analyze.py descope --max-posts 10

Environment variables:
  SCRAPINGDOG_API_KEY   Required — your ScrapingDog API key
  ANTHROPIC_API_KEY     Optional — enables Claude social decode
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from tools import linkedin_profile, linkedin_posts, screenshots, report, claude_decode


def main():
    parser = argparse.ArgumentParser(description="Decode a LinkedIn company page")
    parser.add_argument("slug", help="LinkedIn company slug (e.g. cyera, descope)")
    parser.add_argument("--max-posts", type=int, default=10, help="Max posts to fetch")
    parser.add_argument(
        "--skip-screenshots", action="store_true", help="Skip Playwright screenshots"
    )
    parser.add_argument(
        "--skip-decode", action="store_true", help="Skip Claude decode"
    )
    args = parser.parse_args()

    api_key = os.environ.get("SCRAPINGDOG_API_KEY", "")
    if not api_key:
        print("ERROR: SCRAPINGDOG_API_KEY environment variable not set.")
        print("Get your key at https://www.scrapingdog.com/")
        sys.exit(1)

    slug = args.slug.strip().lower().replace("https://", "").replace("www.linkedin.com/company/", "").rstrip("/")
    run_id = datetime.utcnow().strftime("%Y%m%d-%H%M")

    output_dir = Path("output") / slug / run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    screenshots_dir = output_dir / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  Social Decoder: linkedin.com/company/{slug}")
    print(f"  Run ID: {run_id}")
    print(f"  Output: {output_dir}")
    print(f"{'='*60}\n")

    # ── Step 1: Fetch company profile ─────────────────────────────
    print("Step 1: Fetching company profile ...")
    raw_profile = {}
    profile_summary = {}
    try:
        raw_profile = linkedin_profile.fetch(slug, api_key)
        profile_summary = linkedin_profile.extract_summary(raw_profile)
        print(f"  ✓ {profile_summary.get('name', slug)} — {profile_summary.get('follower_count', '?')} followers")
        # Save raw
        (output_dir / "raw_profile.json").write_text(
            json.dumps(raw_profile, indent=2), encoding="utf-8"
        )
    except Exception as e:
        print(f"  ✗ Profile fetch failed: {e}")
        print("  Continuing with empty profile data ...")
        profile_summary = {"name": slug}

    # ── Step 2: Extract posts from profile response ────────────────
    print(f"\nStep 2: Extracting posts from profile data ...")
    posts = []
    try:
        posts = linkedin_posts.extract_from_profile(raw_profile, max_posts=args.max_posts)
        print(f"  ✓ {len(posts)} posts extracted")
        (output_dir / "raw_posts.json").write_text(
            json.dumps(posts, indent=2), encoding="utf-8"
        )
    except Exception as e:
        print(f"  ✗ Posts extraction failed: {e}")
        print("  Continuing with empty posts ...")

    # ── Step 3: Screenshots ────────────────────────────────────────
    if not args.skip_screenshots:
        print(f"\nStep 3: Taking post screenshots ...")
        company_name = profile_summary.get("name", slug)
        screenshot_paths = []
        for post in posts:
            path = screenshots.take_post_screenshot(
                post, company_name, screenshots_dir, total_posts=len(posts)
            )
            if path:
                screenshot_paths.append(path)
                print(f"  ✓ post-{post['index']:02d}.png")
            else:
                print(f"  ✗ post-{post['index']:02d} screenshot failed")
    else:
        print("\nStep 3: Screenshots skipped (--skip-screenshots)")

    # ── Step 4: Generate report ────────────────────────────────────
    print(f"\nStep 4: Generating social-report.md ...")
    report_path = report.generate(
        slug=slug,
        run_id=run_id,
        profile_summary=profile_summary,
        posts=posts,
        output_dir=output_dir,
    )

    # ── Step 5: Claude decode ──────────────────────────────────────
    if not args.skip_decode:
        print(f"\nStep 5: Running Claude social decode ...")
        decode_path = claude_decode.run(report_path, slug, output_dir)
    else:
        print("\nStep 5: Claude decode skipped (--skip-decode)")
        decode_path = None

    # ── Summary ────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("  DONE")
    print(f"  Output directory: {output_dir}")
    print(f"  Files:")
    for f in sorted(output_dir.rglob("*")):
        if f.is_file():
            size_kb = f.stat().st_size / 1024
            print(f"    {f.relative_to(output_dir)}  ({size_kb:.1f} KB)")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
