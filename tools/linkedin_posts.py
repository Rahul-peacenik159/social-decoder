"""
Extract LinkedIn company posts from the profile API response.
ScrapingDog's /profile?type=company endpoint returns up to 10 posts
in the 'updates' field — no extra API calls needed.

For individual post detail (more fields), use /profile/post?id=POST_ID (5 credits each).
"""

import re
import requests
import json
import os


def extract_from_profile(raw_profile: dict, max_posts: int = 10) -> list:
    """
    Extract posts from the 'updates' field of a ScrapingDog company profile response.
    Each update has: text, article_posted_date, total_likes, article_title,
                     article_sub_title, article_link
    """
    updates = raw_profile.get("updates") or []
    posts = []

    for i, item in enumerate(updates[:max_posts]):
        if not isinstance(item, dict):
            continue

        text = str(item.get("text") or "").strip()
        if not text:
            continue

        # Extract post URN from article_link
        # e.g. .../posts/cyera_ai-is-moving-fast-activity-7450890859102867456-fQxG
        link = item.get("article_link") or ""
        urn = ""
        m = re.search(r"activity-(\d+)-", link)
        if m:
            urn = m.group(1)

        # Detect image or video from article metadata
        img_url = item.get("article_image") or item.get("image_url") or ""
        is_video = "video" in str(item.get("article_title", "")).lower()

        # Engagement
        likes = _parse_int(item.get("total_likes") or 0)
        comments = _parse_int(item.get("total_comments") or item.get("comments") or 0)
        shares = _parse_int(item.get("total_shares") or item.get("shares") or 0)

        # Post type
        has_article = bool(item.get("article_title") or item.get("article_sub_title"))
        ptype = "video" if is_video else ("article" if has_article else ("image" if img_url else "text"))

        posts.append({
            "index": i + 1,
            "urn": urn,
            "text": text[:1000],
            "img_url": img_url,
            "is_video": is_video,
            "type": ptype,
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "posted": item.get("article_posted_date") or "",
            "link": link,
            "article_title": item.get("article_title") or "",
            "article_subtitle": item.get("article_sub_title") or "",
        })

    return posts


def fetch_post_detail(post_id: str, api_key: str) -> dict:
    """
    Fetch individual post via ScrapingDog /profile/post endpoint.
    Cost: 5 credits per call. Use sparingly on free tier.
    post_id: the numeric activity ID extracted from the post URL.
    """
    url = "https://api.scrapingdog.com/profile/post"
    params = {"api_key": api_key, "id": post_id}
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            return data[0] if data else {}
        return data
    except Exception as e:
        print(f"  Post detail fetch failed for {post_id}: {e}")
        return {}


def _parse_int(val) -> int:
    try:
        return int(str(val).replace(",", "").strip())
    except Exception:
        return 0


if __name__ == "__main__":
    import sys
    profile_path = sys.argv[1] if len(sys.argv) > 1 else "output/cyera/raw_profile.json"
    with open(profile_path) as f:
        raw = json.load(f)
    posts = extract_from_profile(raw)
    print(json.dumps(posts, indent=2))
