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

import requests
import time


def fetch_hackathons(page: int = 1) -> list[dict]:
    url = f"https://devpost.com/api/hackathons?status[]=open&page={page}"

    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Devpost API returned {response.status_code}")
    
    hackathons = response.json()["hackathons"]
    return hackathons
    


def fetch_all_open_hackathons(max_pages: int = 10) -> list[dict]:
    all_hackathons = []

    for current_page in range(1, max_pages + 1):
      hackathon = fetch_hackathons(current_page)
      if not hackathon:
          break
      all_hackathons.extend(hackathon)
      time.sleep(1)
        
    return all_hackathons



def normalize_opportunity(raw: dict) -> dict:
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
