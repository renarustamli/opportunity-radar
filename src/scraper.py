"""
Devpost scraper — fetches open hackathons from Devpost's public API.

Reference: sample response shape (fetched 2026-07-14, may drift over time)

    GET https://devpost.com/api/hackathons?status[]=open&page=1
    Headers: {"User-Agent": "Mozilla/5.0"}   # required, plain requests gets blocked without it

    {
      "hackathons": [
        {
          "id": 29541,
          "title": "Build with Gemini XPRIZE",
          "displayed_location": {"icon": "globe", "location": "Online"},
          "url": "https://xprize.devpost.com/",
          "submission_period_dates": "May 19 - Aug 17, 2026",
          "themes": [{"id": 6, "name": "Machine Learning/AI"}, ...],
          "prize_amount": "$<span data-currency-value>2,000,000</span>",
          "registrations_count": 19430,
          "organization_name": "XPRIZE",
          ...
        },
        ...
      ]
    }

Notes for when you implement this:
- The API is paginated. Check what happens when you request a page past the last one
  (empty list? error? repeated results?) — decide how your loop should know when to stop.
- "submission_period_dates" is a human string, not ISO — you'll need to parse or store as-is for now.
- "prize_amount" has an HTML tag embedded in it — strip it before storing.
- Be a reasonable citizen: add a small delay between paginated requests.
"""


import requests
import time


def fetch_hackathons(page: int = 1) -> list[dict]:
    """
    TODO: call the Devpost API for the given page, return the raw list of
    hackathon dicts from the "hackathons" key.

    Raise a clear exception if the request fails or returns a non-200 status —
    don't let a network hiccup silently return an empty list.
    """

    url = f"https://devpost.com/api/hackathons?status[]=open&page={page}"

    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Devpost API returned {response.status_code}")
    
    hackathons = response.json()["hackathons"]
    return hackathons
    


def fetch_all_open_hackathons(max_pages: int = 10) -> list[dict]:
    """
    TODO: call fetch_hackathons() across pages until either max_pages is hit
    or the API stops returning new results. Return the combined raw list.
    """
    all_hackathons = []

    for current_page in range(1, max_pages + 1):
      hackathon = fetch_hackathons(current_page)
      if not hackathon:
          break
      all_hackathons.extend(hackathon)
      time.sleep(1)
        
    return all_hackathons



def normalize_opportunity(raw: dict) -> dict:
    """
    TODO: convert one raw Devpost hackathon dict into your normalized schema,
    e.g.:
        {
            "source": "devpost",
            "source_id": ...,
            "title": ...,
            "url": ...,
            "location": ...,
            "deadline_text": ...,      # raw string for now
            "prize_amount": ...,       # cleaned, no HTML
            "themes": [...],           # list of theme names
            "organization": ...,
        }

    Decide what "source_id" should be and why (hint: you'll need it later
    to avoid inserting duplicate rows when you re-run the scraper).
    """
    return {
        "source": "devpost",
        "source_id": raw["id"],
        "title": raw["title"],
        "url": raw["url"],
        "location": raw["displayed_location"]["location"],
        "deadline_text": raw["submission_period_dates"],
        "prize_amount": raw["prize_amount"].replace("<span data-currency-value>", "").replace("</span>", ""),
        "organization": raw["organization_name"],
        "themes": [t["name"] for t in raw["themes"]],
    }


if __name__ == "__main__":
    hackathons = fetch_all_open_hackathons()
    print(f"Fetched {len(hackathons)} hackathons")
    for h in hackathons[:3]:
        print(normalize_opportunity(h))
