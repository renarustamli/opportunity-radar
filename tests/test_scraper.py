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

from src.scraper import normalize_opportunity

def test_normalize_opportunity_extracts_expected_fields():
    result = normalize_opportunity(SAMPLE_RAW_HACKATHON)
    assert result["title"] == "Build with Gemini XPRIZE"
    assert result["source_id"] == 29541

def test_normalize_opportunity_strips_html_from_prize_amount():
    result = normalize_opportunity(SAMPLE_RAW_HACKATHON)
    assert "<span" not in result["prize_amount"]
    assert result["prize_amount"] == "$2,000,000"

