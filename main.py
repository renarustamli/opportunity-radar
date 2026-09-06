import sys

from src.scraper import fetch_all_open_hackathons, normalize_opportunity
from src.storage import init_db, save_opportunity, get_all_opportunities
from src.matcher import rank_opportunities, score_opportunity
from src.user_profile import PROFILE

def refresh_data():
    init_db()
    hackathons = fetch_all_open_hackathons()
    for raw in hackathons:
        save_opportunity(normalize_opportunity(raw))
    return len(hackathons)

def report():
    opportunities = get_all_opportunities()
    ranked = rank_opportunities(opportunities, PROFILE)

    for opp in ranked:
        score = score_opportunity(opp, PROFILE)
        print(f"[{score}] {opp['title']}")
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
