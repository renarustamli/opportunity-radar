"""
Tests for src/scraper.py.

Start with normalize_opportunity() — it's pure logic (no network calls),
so it's the easiest to test and the best place to build the testing habit.

A sample raw dict is provided below (trimmed from a real API response) to
use as fixture data, so you don't need network access to test normalization.
"""

SAMPLE_RAW_HACKATHON = {
    "id": 29541,
    "title": "Build with Gemini XPRIZE",
    "displayed_location": {"icon": "globe", "location": "Online"},
    "url": "https://xprize.devpost.com/",
    "submission_period_dates": "May 19 - Aug 17, 2026",
    "themes": [
        {"id": 6, "name": "Machine Learning/AI"},
        {"id": 19, "name": "Education"},
    ],
    "prize_amount": "$<span data-currency-value>2,000,000</span>",
    "registrations_count": 19430,
    "organization_name": "XPRIZE",
}

import pytest

from src.scraper import normalize_opportunity, parse_deadline

def test_normalize_opportunity_extracts_expected_fields():
    result = normalize_opportunity(SAMPLE_RAW_HACKATHON)
    assert result["title"] == "Build with Gemini XPRIZE"
    assert result["source_id"] == 29541

def test_normalize_opportunity_strips_html_from_prize_amount():
    result = normalize_opportunity(SAMPLE_RAW_HACKATHON)
    assert "<span" not in result["prize_amount"]
    assert result["prize_amount"] == "$2,000,000"


def test_normalize_opportunity_includes_parsed_deadline():
    result = normalize_opportunity(SAMPLE_RAW_HACKATHON)
    assert result["deadline_text"] == "May 19 - Aug 17, 2026"
    assert result["deadline_date"] == "2026-08-17"


@pytest.mark.parametrize("text, expected", [
    # Both dates carry a month; the year appears once at the end.
    ("Jul 31 - Oct 01, 2026", "2026-10-01"),
    # End date is a bare day, so the month is borrowed from the start date.
    ("Sep 05 - 06, 2026", "2026-09-06"),
    # Range spans a year boundary, so each date carries its own year.
    ("Jul 16, 2026 - Jan 15, 2027", "2027-01-15"),
    # Single date, no range at all.
    ("Sep 06, 2026", "2026-09-06"),
])
def test_parse_deadline_returns_end_date_as_iso(text, expected):
    assert parse_deadline(text) == expected


@pytest.mark.parametrize("text", [
    "total nonsense",
    "",
    "Notember 45, 2026",
])
def test_parse_deadline_returns_none_for_unparseable_input(text):
    assert parse_deadline(text) is None

