import sys

from src.scraper import fetch_all_open_hackathons, normalize_opportunity
from src.storage import init_db, save_opportunity, get_active_opportunities
from src.matcher import Matcher
from src.reranker import rerank
from src.user_profile import PROFILE

SHORTLIST_SIZE = 20

def refresh_data():
    init_db()
    hackathons = fetch_all_open_hackathons()
    for raw in hackathons:
        save_opportunity(normalize_opportunity(raw))
    return len(hackathons)

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
    by_source_id = {opp["source_id"]: opp for opp in shortlist}

    for ranking in sorted(rankings, key=lambda r: r.score, reverse=True):
        opp = by_source_id.get(ranking.source_id)
        if opp is None:
            continue

        print(f"[{ranking.score:3d}] {opp['title']}")
        print(f"    {opp['deadline_text']} | {opp['prize_amount']} | {opp['organization']}")
        print(f"    {ranking.reasoning}")
        print(f"    {opp['url']}")
        print()

    return len(rankings)

if __name__ == "__main__":
    if "--refresh" in sys.argv:
        fetched = refresh_data()
        print(f"Fetched {fetched} hackathons\n")

    if "--rerank" in sys.argv:
        total = reranked_report()
        print(f"{total} opportunities re-ranked")
    else:
        total = report()
        print(f"{total} opportunities open")
