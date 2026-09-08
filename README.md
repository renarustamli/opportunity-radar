# Opportunity Radar

Finds and tracks hackathons/competitions, matches them against my profile, and notifies me — built as a learning project for AI/ML + SWE engineering skills.

## Status

Working end to end: scrapes open hackathons, stores them in SQLite with deduplication, ranks them by semantic similarity to a profile, and prints an apply-list with links.

Built so far:

- Ingestion — paginated Devpost API client with error handling and rate-limit courtesy
- Persistence — SQLite schema with a `UNIQUE(source, source_id)` constraint so re-runs never duplicate rows
- Matching — sentence-transformer embeddings (`all-MiniLM-L6-v2`) with cosine similarity, so ranking follows meaning rather than exact tag matches

The naive theme-overlap scorer is kept alongside the embedding matcher for comparison. It scored every AI hackathon identically; the embedding version separates them correctly.

Planned:

- Deadline parsing, so expired hackathons are filtered out
- MLH as a second source, exercising the multi-source schema
- LLM re-ranking of the top matches, with relevance scores and reasoning
- Scheduled runs via GitHub Actions, with email or Telegram notifications

### A note on Devpost

As of September 2026 Devpost began returning 403 to all non-browser traffic, including `robots.txt`. The scraper is retained and unchanged — it worked against their public endpoint until that point, and would work again if the restriction is lifted — but fresh fetches currently fail. Adding MLH as a second source is the planned response, rather than working around the block.

## Setup

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

Print the ranked list from data already stored (no network calls):

```
python3 main.py
```

Fetch fresh listings from Devpost first, then print:

```
python3 main.py --refresh
```

Edit `src/user_profile.py` to change what you want to match against. The `description` field is the text the embedding model ranks everything against; `themes` is used by the older overlap scorer.

The embedding model downloads once (~90MB) on first run and is cached locally, so subsequent runs work offline.

## Project structure

```
main.py               entry point, wires the pipeline together
src/scraper.py        Devpost API client and normalization
src/storage.py        SQLite persistence
src/matcher.py        scoring and ranking
src/user_profile.py   profile config
tests/                test suite
data/                 SQLite database (gitignored)
```

## Run tests

```
python3 -m pytest
```

Note: use `python3 -m pytest` rather than a bare `pytest`, so the project root ends up on the import path.
