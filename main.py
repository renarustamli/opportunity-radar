import sys

from src.scraper import fetch_all_open_hackathons, normalize_opportunity
from src.uk_scraper import fetch_uk_opportunities
from src.storage import (
    init_db,
    save_opportunity,
    get_active_opportunities,
    get_unnotified_opportunities,
    mark_notified,
)
from src.matcher import Matcher
from src.reranker import rerank
from src.notifier import send_digest
from src.user_profile import PROFILE

SHORTLIST_SIZE = 20

def refresh_data():
    """Fetch from every source. One source failing must not lose the others."""
    init_db()
    saved = 0

    for name, fetch in (("devpost", fetch_devpost), ("hackathons_uk", fetch_uk)):
        try:
            opportunities = fetch()
        except Exception as error:
            print(f"  {name} failed: {error}")
            continue

        for opportunity in opportunities:
            save_opportunity(opportunity)
        saved += len(opportunities)
        print(f"  {name}: {len(opportunities)} fetched")

    return saved


def fetch_devpost():
    return [normalize_opportunity(raw) for raw in fetch_all_open_hackathons()]


def fetch_uk():
    return fetch_uk_opportunities()

def report():
    matcher = Matcher(PROFILE["description"])

    opportunities = get_active_opportunities()
    ranked = matcher.rank(opportunities)

    for opp in ranked:
        score = matcher.score(opp)
        print(f"[{score:.3f}] {opp['title']}")
        print(f"    {opp['deadline_text']} | {opp['prize_amount']} | {opp['organization']}")
        print(f"    {opp['url']}")
        print()

    return len(ranked)

def reranked_report():
    matcher = Matcher(PROFILE["description"])

    opportunities = get_active_opportunities()
    shortlist = matcher.rank(opportunities)[:SHORTLIST_SIZE]

    rankings = rerank(shortlist, PROFILE["description"])
    by_id = {opp["id"]: opp for opp in shortlist}

    for ranking in sorted(rankings, key=lambda r: r.score, reverse=True):
        opp = by_id.get(ranking.id)
        if opp is None:
            continue

        print(f"[{ranking.score:3d}] {opp['title']}")
        print(f"    {opp['deadline_text']} | {opp['prize_amount']} | {opp['organization']}")
        print(f"    {ranking.reasoning}")
        print(f"    {opp['url']}")
        print()

    return len(rankings)

def notify():
    """Email a digest of opportunities not sent before, best matches first."""
    fresh = get_unnotified_opportunities()
    if not fresh:
        print("Nothing new to send")
        return 0

    matcher = Matcher(PROFILE["description"])
    shortlist = matcher.rank(fresh)[:SHORTLIST_SIZE]

    # Prefer the LLM's scores and reasoning, but a digest with embedding scores
    # is far better than no digest at all if the model call fails.
    try:
        rankings = {r.id: r for r in rerank(shortlist, PROFILE["description"])}
        scored = [
            (rankings[o["id"]].score, rankings[o["id"]].reasoning, o)
            for o in shortlist if o["id"] in rankings
        ]
        scored.sort(key=lambda row: row[0], reverse=True)
    except Exception as error:
        print(f"  re-ranking failed ({error}), falling back to embedding scores")
        scored = [(round(matcher.score(o), 3), None, o) for o in shortlist]

    send_digest(scored)
    mark_notified([opp for _, _, opp in scored])
    print(f"Sent digest with {len(scored)} opportunities")

    return len(scored)


if __name__ == "__main__":
    # Every entry point needs the schema to exist and be current, not just
    # --refresh: an older database would be missing later columns.
    init_db()

    if "--refresh" in sys.argv:
        fetched = refresh_data()
        print(f"Fetched {fetched} hackathons\n")

    if "--notify" in sys.argv:
        notify()
    elif "--rerank" in sys.argv:
        total = reranked_report()
        print(f"{total} opportunities re-ranked")
    else:
        total = report()
        print(f"{total} opportunities open")
