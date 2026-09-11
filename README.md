# Opportunity Radar

Finds and tracks hackathons, ranks them against my interests, and emails me a digest of what is new — built as a learning project for AI/ML and software engineering skills.

## What it does

1. Scrapes hackathon listings from two sources
2. Stores them in SQLite, deduplicating against everything seen before
3. Drops anything whose deadline has passed
4. Ranks what remains by semantic similarity to a written profile
5. Sends the top matches to an LLM for relevance scores and one-line reasoning
6. Emails a digest containing only opportunities not sent before

Steps 1-4 run daily on GitHub Actions. The digest is currently sent by running
`--notify` locally; adding `RESEND_API_KEY` and `DIGEST_TO` as repository
secrets moves it into the scheduled run.

Steps 4 and 5 are a retrieval-then-rerank pipeline: embeddings are cheap and shallow, so they narrow the field; the LLM is expensive and precise, so it only judges the shortlist.

## Design notes

**Two-stage matching.** The first matcher scored by theme-tag overlap and gave every AI hackathon an identical score, because it could only count exact string matches. Embeddings separate them correctly — the model recognises "Agentic Cinema" as AI-related without the literal tag being present. The naive scorer is kept in `matcher.py` for comparison.

**Deduplication depends on choosing the right key.** `UNIQUE(source, source_id)` keeps re-runs idempotent. The UK source initially used the event URL as its identifier, which silently collapsed six editions of the same annual hackathon into one row, because recurring events reuse their domain year after year. Pairing the URL with the date fixed it.

**Failures are isolated and degraded, not fatal.** One source returning an error does not stop the others. If the LLM call fails or its quota is exhausted, the digest still goes out using embedding scores. Model calls retry with backoff, preferring the API's own `retry in Xs` hint over a fixed schedule, since the real reset window is tens of seconds.

**State lives in a workflow artifact.** GitHub Actions runners are destroyed after each job, so the database is uploaded at the end of a run and restored at the start of the next. That is what makes "only what is new" possible, and it keeps a binary file out of the git history.

## Sources

| Source | Access | Status |
|---|---|---|
| Devpost | Public JSON API | Blocked since September 2026 |
| hackathons.org.uk | HTML, `[data-event-card]` | Working, 88 events |

Devpost began returning 403 to all non-browser traffic, including `robots.txt`. The scraper is retained unchanged and would work again if the restriction lifts. Rather than defeating their bot protection, a second source was added. hackathons.org.uk permits crawling in its `robots.txt`, and the scraper honours the one-second crawl delay it asks for.

## Setup

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Three environment variables are needed for the LLM and email steps. The ranked-list commands work without them.

```
export GEMINI_API_KEY=...
export RESEND_API_KEY=...
export DIGEST_TO=you@example.com
```

## Usage

Print the ranked list from stored data, with no network calls:

```
python3 main.py
```

Fetch fresh listings first:

```
python3 main.py --refresh
```

Add LLM scores and reasoning:

```
python3 main.py --rerank
```

Email a digest of opportunities not sent before:

```
python3 main.py --notify
```

Edit `src/user_profile.py` to change what you are matched against. The `description` field is the text everything is ranked against; `themes` is used only by the older overlap scorer.

The embedding model downloads once (~90MB) and is cached, so later runs work offline.

## Project structure

```
main.py                  entry point and CLI flags
src/scraper.py           Devpost API client, normalization, date parsing
src/uk_scraper.py        hackathons.org.uk HTML scraper
src/storage.py           SQLite persistence, migrations, dedup
src/matcher.py           embedding and theme-overlap ranking
src/reranker.py          LLM scoring with retries and a validated schema
src/notifier.py          email digests
src/user_profile.py      profile config
.github/workflows/       daily scheduled run
tests/                   test suite
data/                    SQLite database (gitignored)
```

## Tests

```
python3 -m pytest
```

Use `python3 -m pytest` rather than a bare `pytest`, so the project root lands on the import path.

The suite runs entirely offline — no API calls, no network — using captured fixtures for both the Devpost response shape and real Gemini error messages. Writing the date-parsing tests immediately surfaced a crash on empty input that the existing error handling did not cover.
