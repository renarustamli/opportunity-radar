"""
Tests for src/reranker.py.

These cover the parts that need no network: the retry delay logic and the
prompt assembly. The model call itself is not exercised here — see the
storage/network mocking tests for that pattern.
"""

import pytest

from src.reranker import FALLBACK_DELAYS, rerank_prompt, retry_delay

# Real error text captured from the Gemini API, trimmed.
RATE_LIMIT_ERROR = (
    "You exceeded your current quota, please check your plan and billing details. "
    "* Quota exceeded for metric: generativelanguage.googleapis.com/"
    "generate_content_free_tier_requests, limit: 20, model: gemini-3.8-flash "
    "Please retry in 22.543584794s."
)
OVERLOAD_ERROR = (
    "gemini-3.8-flash is currently experiencing high demand, "
    "spikes in demand are usually temporary. Please try again later."
)

SAMPLE_OPPORTUNITIES = [
    {
        "id": 7,
        "source_id": 29969,
        "title": "RevenueCat Shipaton 2026",
        "themes": ["Design", "Gaming", "Mobile"],
    },
    {
        "id": 12,
        "source_id": 30317,
        "title": "Agents for Humans Hackathon",
        "themes": ["Machine Learning/AI", "Open Ended"],
    },
]


def test_retry_delay_uses_the_api_hint_when_present():
    # The API asked for 22.5s; a fixed 1/2/4 backoff would retry far too early.
    assert retry_delay(RATE_LIMIT_ERROR, 0) == pytest.approx(23.543584794)


def test_retry_delay_hint_beats_the_fallback_on_every_attempt():
    # The hint should win regardless of which attempt we are on.
    for attempt in range(4):
        assert retry_delay(RATE_LIMIT_ERROR, attempt) > FALLBACK_DELAYS[0]


@pytest.mark.parametrize("attempt, expected", list(enumerate(FALLBACK_DELAYS)))
def test_retry_delay_escalates_when_no_hint_is_given(attempt, expected):
    assert retry_delay(OVERLOAD_ERROR, attempt) == expected


def test_retry_delay_clamps_past_the_end_of_the_fallback_list():
    # More attempts than we have delays should reuse the last one, not crash.
    assert retry_delay(OVERLOAD_ERROR, 99) == FALLBACK_DELAYS[-1]


def test_rerank_prompt_includes_every_candidate_with_its_id():
    prompt = rerank_prompt(SAMPLE_OPPORTUNITIES, "AI agent hackathons")

    for opportunity in SAMPLE_OPPORTUNITIES:
        assert f"[{opportunity['id']}]" in prompt
        assert opportunity["title"] in prompt


def test_rerank_prompt_includes_the_profile_and_themes():
    prompt = rerank_prompt(SAMPLE_OPPORTUNITIES, "AI agent hackathons")

    assert "AI agent hackathons" in prompt
    assert "Machine Learning/AI" in prompt
