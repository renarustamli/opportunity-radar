from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

def score_opportunity(opp, profile):
    return len(set(opp["themes"]) & set(profile["themes"]))

def rank_opportunities(opps, profile):
    return sorted(opps, key=lambda opp:score_opportunity(opp, profile) , reverse=True)

class Matcher:
    def __init__(self, profile_text, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.profile_vector = self.model.encode(profile_text)
    
    def score(self,opp):
        text = opp["title"] + ". " + ", ".join(opp["themes"])
        encoded_text = self.model.encode(text)
        score = float(cos_sim(encoded_text, self.profile_vector))
        return score 
    
    def rank(self,opps):
        return sorted(opps, key = lambda opp:self.score(opp), reverse=True )