def score_opportunity(opp, profile):
    return len(set(opp["themes"]) & set(profile["themes"]))

def rank_opportunities(opps, profile):
    return sorted(opps, key=lambda opp:score_opportunity(opp, profile) , reverse=True)
