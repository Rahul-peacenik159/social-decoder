"""
Fetch last N LinkedIn company posts via ScrapingDog general scraper.
ScrapingDog free tier: 1000 credits/month.
Scraping a LinkedIn page costs ~5 credits. We fetch 1 page = ~10 posts.
"""

import requests
import json
import os
import re
from bs4 import BeautifulSoup


SCRAPINGDOG_SCRAPER_URL = "https://api.scrapingdog.com/scrape"


def _scrape_url(url: str, api_key: str, dynamic: bool = True) -> str:
    """Use ScrapingDog general scraper to fetch a URL."""
    params = {
        "api_key": api_key,
        "url": url,
        "dynamic": "true" if dynamic else "false",
    }
    resp = requests.get(SCRAPINGDOG_SCRAPER_URL, params=params, timeout=60)
    resp.raise_for_status()
    return resp.text


def _parse_posts_from_html(html: str) -> list:
    """
    Parse post cards from LinkedIn company posts page HTML.
    LinkedIn renders posts in <div data-id="..."> or similar containers.
    We look for common patterns and extract text content + metadata.
    """
    soup = BeautifulSoup(html, "lxml")
    posts = []

    # LinkedIn post containers — several selectors to try
    selectors = [
        "div.occludable-update",
        "div[data-urn]",
        "article",
        "div.feed-shared-update-v2",
    ]

    containers = []
    for sel in selectors:
        containers = soup.select(sel)
        if containers:
            break

    if not containers:
        # Fallback: grab all large text blocks
        containers = soup.find_all("p")

    for i, container in enumerate(containers[:10]):
        # Extract text
        text = container.get_text(separator=" ", strip=True)
        if len(text) < 30:
            continue

        # Try to find image
        img = container.find("img")
        img_url = img.get("src", "") if img else ""

        # Try to extract post URN / ID
        urn = (
            container.get("data-urn", "")
            or container.get("data-id", "")
            or container.get("id", "")
        )

        # Detect if video (look for video tag or common video keywords)
        is_video = bool(container.find("video")) or "video" in container.get("class", [])

        posts.append({
            "index": i + 1,
            "urn": urn,
            "text": text[:1000],
            "img_url": img_url,
            "is_video": is_video,
            "type": "video" if is_video else ("image" if img_url else "text"),
        })

    return posts


def fetch_posts_via_scraper(slug: str, api_key: str, max_posts: int = 10) -> list:
    """
    Scrape the LinkedIn company posts page.
    URL: https://www.linkedin.com/company/{slug}/posts/
    Returns list of post dicts.
    """
    url = f"https://www.linkedin.com/company/{slug}/posts/?feedView=all"
    print(f"  Scraping {url} ...")

    try:
        html = _scrape_url(url, api_key, dynamic=True)
    except requests.HTTPError as e:
        print(f"  ScrapingDog error: {e}")
        return []

    posts = _parse_posts_from_html(html)
    print(f"  Parsed {len(posts)} posts from HTML")
    return posts[:max_posts]


def fetch_post_detail(post_id: str, api_key: str) -> dict:
    """
    Fetch individual post via ScrapingDog /profile/post endpoint.
    Cost: 5 credits per call. Use sparingly on free tier.
    """
    url = "https://api.scrapingdog.com/profile/post"
    params = {
        "api_key": api_key,
        "id": post_id,
    }
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


if __name__ == "__main__":
    import sys
    slug = sys.argv[1] if len(sys.argv) > 1 else "cyera"
    key = os.environ.get("SCRAPINGDOG_API_KEY", "")
    posts = fetch_posts_via_scraper(slug, key)
    print(json.dumps(posts, indent=2))
