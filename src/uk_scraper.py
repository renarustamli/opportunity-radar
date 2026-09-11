"""
Scraper for hackathons.org.uk.

Unlike Devpost there is no API, so this parses the rendered HTML. Cards are
marked with a data-event-card attribute, which is a far more stable hook than
the Tailwind utility classes around them.

Their robots.txt allows crawling but disallows /api/ and asks for a 1 second
crawl delay, which CRAWL_DELAY honours.
"""

import re
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

SOURCE = "hackathons_uk"
EVENTS_URL = "https://www.hackathons.org.uk/events/"
HEADERS = {"User-Agent": "Mozilla/5.0"}
CRAWL_DELAY = 1

# "3 Oct 2026", or "7 Feb 2026 - 8 Feb 2026" for multi-day events.
DATE_PATTERN = re.compile(r"\d{1,2} [A-Za-z]{3} \d{4}")
FORMATS = {"Physical", "Digital", "Hybrid", "Online", "In-Person"}


def fetch_events_page():
    """Fetch the events listing. Raises if the site does not return 200."""
    response = requests.get(EVENTS_URL, headers=HEADERS, timeout=30)
    if response.status_code != 200:
        raise Exception(f"hackathons.org.uk returned {response.status_code}")

    time.sleep(CRAWL_DELAY)
    return response.text


def parse_uk_date(text):
    """Return the end date of a UK-site date string as ISO, or None."""
    matches = DATE_PATTERN.findall(text or "")
    if not matches:
        return None

    try:
        return datetime.strptime(matches[-1], "%d %b %Y").strftime("%Y-%m-%d")
    except ValueError:
        return None


def extract_card(card):
    """Pull one event out of a card element, or None if it has no usable title."""
    heading = card.find("h4")
    link = card.find("a", href=True)
    if heading is None or link is None:
        return None

    # Spans shift position depending on whether a partner badge is present, so
    # identify each by what it contains rather than where it sits.
    date_text = None
    event_format = None
    venue = None

    for span in card.find_all("span"):
        text = span.get_text(strip=True)
        if not text:
            continue
        if date_text is None and DATE_PATTERN.search(text):
            date_text = text
        elif event_format is None and text in FORMATS:
            event_format = text
        elif venue is None and text not in FORMATS and "Hackathons UK" not in text:
            if not DATE_PATTERN.search(text) and not text.startswith("-"):
                venue = text

    return {
        "title": heading.get_text(strip=True),
        "url": link["href"],
        "date_text": date_text,
        "format": event_format,
        "venue": venue,
    }


def normalize_uk_event(event):
    """Convert an extracted card into the shared opportunity schema."""
    # Recurring hackathons reuse the same URL every year (durhack.com hosts
    # DurHack 2022, 2022 v2 and 2026), so the URL alone is not unique. Pairing
    # it with the date keeps separate editions as separate rows.
    return {
        "source": SOURCE,
        "source_id": f"{event['url']}#{parse_uk_date(event['date_text']) or event['title']}",
        "title": event["title"],
        "url": event["url"],
        "location": event["venue"] or "United Kingdom",
        "deadline_text": event["date_text"],
        "deadline_date": parse_uk_date(event["date_text"]),
        "prize_amount": None,
        "organization": event["venue"],
        "themes": [event["format"]] if event["format"] else [],
    }


def fetch_uk_opportunities():
    """Fetch and normalize every event on the listing page."""
    soup = BeautifulSoup(fetch_events_page(), "html.parser")

    opportunities = []
    for card in soup.select("[data-event-card]"):
        event = extract_card(card)
        if event:
            opportunities.append(normalize_uk_event(event))

    return opportunities
