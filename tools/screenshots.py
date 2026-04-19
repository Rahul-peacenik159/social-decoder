"""
Take screenshots of LinkedIn posts.
- Text/image posts: render via a local HTML template + Playwright
- Video posts: use thumbnail image if available, else placeholder
"""

import os
import base64
import textwrap
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


POST_HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #f3f2ef;
    display: flex;
    justify-content: center;
    align-items: flex-start;
    padding: 24px;
    min-height: 100vh;
  }}
  .card {{
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 0 0 1px rgba(0,0,0,.12), 0 2px 4px rgba(0,0,0,.08);
    width: 560px;
    padding: 16px;
  }}
  .header {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 12px;
  }}
  .avatar {{
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: #0a66c2;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    font-weight: 700;
    font-size: 20px;
    flex-shrink: 0;
  }}
  .company-name {{
    font-weight: 600;
    font-size: 14px;
    color: #000;
  }}
  .meta {{
    font-size: 12px;
    color: #666;
  }}
  .body {{
    font-size: 14px;
    line-height: 1.6;
    color: #000;
    white-space: pre-wrap;
    word-break: break-word;
    margin-bottom: 12px;
  }}
  .media {{
    width: 100%;
    border-radius: 4px;
    margin-top: 8px;
    object-fit: cover;
    max-height: 300px;
  }}
  .video-badge {{
    background: #000;
    color: #fff;
    border-radius: 4px;
    padding: 40px;
    text-align: center;
    font-size: 32px;
    margin-top: 8px;
  }}
  .post-index {{
    font-size: 11px;
    color: #999;
    margin-top: 8px;
  }}
</style>
</head>
<body>
<div class="card">
  <div class="header">
    <div class="avatar">{initial}</div>
    <div>
      <div class="company-name">{company_name}</div>
      <div class="meta">Post #{post_index}</div>
    </div>
  </div>
  <div class="body">{text}</div>
  {media_html}
  <div class="post-index">Post {post_index} of {total}</div>
</div>
</body>
</html>"""


def _download_image(url: str, dest: Path) -> bool:
    """Download image to dest. Returns True on success."""
    if not url or not REQUESTS_AVAILABLE:
        return False
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        dest.write_bytes(resp.content)
        return True
    except Exception:
        return False


def take_post_screenshot(
    post: dict,
    company_name: str,
    output_dir: Path,
    total_posts: int,
) -> str:
    """
    Render a post card and take a screenshot.
    Returns the path to the saved PNG, or "" if failed.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    idx = post.get("index", 0)
    filename = f"post-{idx:02d}.png"
    out_path = output_dir / filename

    # Build media HTML
    media_html = ""
    if post.get("is_video"):
        media_html = '<div class="video-badge">▶ Video Post</div>'
    elif post.get("img_url"):
        # Try to embed image as base64 for reliable rendering
        img_cache = output_dir / f"img-{idx:02d}.jpg"
        if _download_image(post["img_url"], img_cache):
            b64 = base64.b64encode(img_cache.read_bytes()).decode()
            media_html = f'<img class="media" src="data:image/jpeg;base64,{b64}" />'
        else:
            media_html = f'<img class="media" src="{post["img_url"]}" />'

    text = post.get("text", "")[:600]
    # Escape HTML entities
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    html = POST_HTML_TEMPLATE.format(
        initial=(company_name[0].upper() if company_name else "C"),
        company_name=company_name,
        post_index=idx,
        total=total_posts,
        text=text,
        media_html=media_html,
    )

    html_path = output_dir / f"post-{idx:02d}.html"
    html_path.write_text(html, encoding="utf-8")

    if not PLAYWRIGHT_AVAILABLE:
        print(f"  [skip screenshot] Playwright not available — saved HTML: {html_path}")
        return str(html_path)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 608, "height": 800})
            page.goto(f"file://{html_path.resolve()}")
            page.wait_for_timeout(500)
            # Clip to just the card
            card = page.query_selector(".card")
            if card:
                box = card.bounding_box()
                page.screenshot(
                    path=str(out_path),
                    clip={
                        "x": box["x"] - 4,
                        "y": box["y"] - 4,
                        "width": box["width"] + 8,
                        "height": box["height"] + 8,
                    },
                )
            else:
                page.screenshot(path=str(out_path))
            browser.close()
        return str(out_path)
    except Exception as e:
        print(f"  Screenshot failed for post {idx}: {e}")
        return ""


def take_profile_screenshot(profile_url: str, output_dir: Path) -> str:
    """Take a full-page screenshot of the LinkedIn company profile page."""
    if not PLAYWRIGHT_AVAILABLE:
        return ""
    out_path = output_dir / "profile.png"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page.goto(profile_url, wait_until="networkidle", timeout=30000)
            page.screenshot(path=str(out_path), full_page=False)
            browser.close()
        return str(out_path)
    except Exception as e:
        print(f"  Profile screenshot failed: {e}")
        return ""
