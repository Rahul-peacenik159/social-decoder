"""
Fetch LinkedIn company profile via ScrapingDog API.
Endpoint: GET https://api.scrapingdog.com/profile?api_key=KEY&type=company&id={slug}
Cost: 1 credit per call
"""

import requests
import json
import os


def fetch(slug: str, api_key: str) -> dict:
    """
    Fetch company profile. Returns parsed dict.
    slug: LinkedIn company slug, e.g. 'cyera' from linkedin.com/company/cyera
    """
    url = "https://api.scrapingdog.com/profile"
    params = {
        "api_key": api_key,
        "type": "company",
        "id": slug,
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()

    data = resp.json()

    # ScrapingDog may return a list or a dict depending on endpoint version
    if isinstance(data, list):
        return data[0] if data else {}
    return data


def extract_summary(profile: dict) -> dict:
    """
    Extract key fields from raw profile response into a clean summary.
    """
    return {
        "name": profile.get("name") or profile.get("companyName") or "",
        "tagline": profile.get("tagline") or "",
        "description": profile.get("description") or "",
        "website": profile.get("website") or profile.get("websiteUrl") or "",
        "industry": profile.get("industry") or "",
        "company_size": profile.get("companySize") or profile.get("employeeCount") or "",
        "follower_count": profile.get("followerCount") or profile.get("followersCount") or "",
        "headquarters": profile.get("headquartersCity") or profile.get("headquarters") or "",
        "founded": profile.get("foundedOn") or profile.get("founded") or "",
        "specialties": profile.get("specialties") or [],
        "logo_url": profile.get("logoUrl") or profile.get("logo") or "",
    }


if __name__ == "__main__":
    import sys
    slug = sys.argv[1] if len(sys.argv) > 1 else "cyera"
    key = os.environ.get("SCRAPINGDOG_API_KEY", "")
    profile = fetch(slug, key)
    print(json.dumps(extract_summary(profile), indent=2))
