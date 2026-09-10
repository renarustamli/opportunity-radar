import sys

from src.scraper import fetch_all_open_hackathons, normalize_opportunity
from src.storage import init_db, save_opportunity, get_active_opportunities
from src.matcher import Matcher
from src.user_profile import PROFILE

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

if __name__ == "__main__":
    if "--refresh" in sys.argv:
        fetched = refresh_data()
        print(f"Fetched {fetched} hackathons\n")

    total = report()
    print(f"{total} opportunities stored")
