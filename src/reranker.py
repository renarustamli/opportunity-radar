from pydantic import BaseModel, Field
from google import genai

MODEL = "gemini-3.8-flash"


class Ranking(BaseModel):
    source_id: int = Field(description="The source_id of the hackathon being scored")
    score: int = Field(description="Relevance to the profile, 0 (irrelevant) to 100 (ideal match)")
    reasoning: str = Field(description="One sentence explaining the score")


class RankingList(BaseModel):
    rankings: list[Ranking]

def rerank(opportunities, profile_text):
    opp_list = []
    for opportunity in opportunities:
        themes = ", ".join(opportunity["themes"])
        opp_list.append(f"[{opportunity['source_id']}] {opportunity['title']} - {themes}")

    candidates = "\n".join(opp_list)

    prompt = f"""You are helping a student decide which hackathons to enter.
Score each candidate below on how well it matches the profile.

Profile:
{profile_text}

Candidates:
{candidates}

Rules:
- Score every candidate exactly once, identified by its source_id.
- Use the full 0-100 range. Reserve 80 and above for genuinely strong matches, and
  score clearly unrelated hackathons below 30. Do not cluster scores together.
- Judge on how well the topic matches the profile, not on prize size or prestige.
- Give one short sentence of reasoning for each score."""

    client = genai.Client()
    interaction = client.interactions.create(
        model=MODEL,
        input=prompt,
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": RankingList.model_json_schema(),
        },
    )

    return RankingList.model_validate_json(interaction.output_text).rankings
