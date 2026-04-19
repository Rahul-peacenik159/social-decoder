# social-decoder

Fetch a LinkedIn company profile + last N posts via ScrapingDog, take screenshots, and run a Claude social intelligence decode.

## What it does

1. **Fetches company profile** — name, tagline, description, follower count, size, industry via ScrapingDog API
2. **Scrapes last 10 posts** — text, images, post type (text / image / video) via ScrapingDog general scraper
3. **Takes screenshots** — renders each post as a styled card via Playwright (video posts get a placeholder badge)
4. **Generates social-report.md** — structured markdown with all raw data
5. **Runs Claude decode** — deep social intelligence analysis: brand voice, content strategy, messaging patterns, competitive signals, top post breakdowns

## Setup

### Secrets needed
| Secret | Where to get |
|---|---|
| `SCRAPINGDOG_API_KEY` | [scrapingdog.com](https://www.scrapingdog.com/) — free tier = 1000 credits/month |
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) — optional, enables Claude decode |

Add these to your repo: **Settings → Secrets and variables → Actions → New repository secret**

### Credit cost (ScrapingDog free tier)
| Action | Credits |
|---|---|
| Company profile | 1 |
| Company posts page scrape | ~5 |
| **Total per run** | **~6 credits** |

At 6 credits/run you can run ~166 decodes per month on the free tier.

## Local usage

```bash
pip install -r requirements.txt
playwright install chromium

export SCRAPINGDOG_API_KEY=your_key
export ANTHROPIC_API_KEY=sk-ant-...  # optional

python analyze.py cyera
python analyze.py descope --max-posts 10
python analyze.py stripe --skip-decode
```

## GitHub Actions

Go to **Actions → Social Decode → Run workflow**

Inputs:
- `linkedin_slug` — the company slug from `linkedin.com/company/SLUG`
- `max_posts` — how many posts to fetch (default 10)

## Output structure

```
output/
  {slug}/
    {run_id}/
      social-report.md       ← structured data report
      social-decode.md       ← Claude analysis
      raw_profile.json       ← raw ScrapingDog profile response
      raw_posts.json         ← raw post data
      screenshots/
        post-01.png
        post-02.png
        ...
```
