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
    Handles ScrapingDog's actual field names from /profile?type=company endpoint.
    """
    # about field may be a string or dict
    about = profile.get("about") or ""
    if isinstance(about, dict):
        about = ""

    specialties = profile.get("specialties") or ""
    if isinstance(specialties, list):
        specialties = ", ".join(str(s) for s in specialties)

    return {
        "name": profile.get("company_name") or profile.get("name") or "",
        "tagline": profile.get("tagline") or "",
        "description": about,
        "website": profile.get("website") or "",
        "industry": profile.get("industry") or profile.get("industries") or "",
        "company_size": profile.get("company_size") or profile.get("company_size_on_linkedin") or "",
        "follower_count": profile.get("follower_count") or "",
        "headquarters": profile.get("headquarters") or profile.get("location") or "",
        "founded": profile.get("founded") or "",
        "specialties": specialties,
        "logo_url": profile.get("profile_photo") or "",
        "funding": profile.get("last_round_funding") or "",
        "funding_round": profile.get("last_round_type") or "",
    }


if __name__ == "__main__":
    import sys
    slug = sys.argv[1] if len(sys.argv) > 1 else "cyera"
    key = os.environ.get("SCRAPINGDOG_API_KEY", "")
    profile = fetch(slug, key)
    print(json.dumps(extract_summary(profile), indent=2))
