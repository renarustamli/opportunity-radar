import re
import time

from pydantic import BaseModel, Field
from google import genai

# Private import: the interaction errors inherit from GenAiError, which the SDK
# does not re-export publicly. google.genai.errors.APIError does NOT cover them.
# If a future SDK version moves this, the import fails loudly at startup, which
# is preferable to silently catching nothing.
from google.genai._gaos.errors.genaierror import GenAiError

MODEL = "gemini-3.8-flash"
MAX_ATTEMPTS = 4
FALLBACK_DELAYS = [5, 20, 60]


class Ranking(BaseModel):
    source_id: int = Field(description="The source_id of the hackathon being scored")
    score: int = Field(description="Relevance to the profile, 0 (irrelevant) to 100 (ideal match)")
    reasoning: str = Field(description="One sentence explaining the score")


class RankingList(BaseModel):
    rankings: list[Ranking]


def retry_delay(error, attempt):
    """Seconds to wait before retrying. Prefers the API's own hint when it gives one."""
    match = re.search(r"retry in ([\d.]+)s", str(error))
    if match:
        return float(match.group(1)) + 1

    return FALLBACK_DELAYS[min(attempt, len(FALLBACK_DELAYS) - 1)]


def call_model(prompt):
    """Call the model, retrying on transient failures and rate limits."""
    client = genai.Client()

    for attempt in range(MAX_ATTEMPTS):
        try:
            return client.interactions.create(
                model=MODEL,
                input=prompt,
                response_format={
                    "type": "text",
                    "mime_type": "application/json",
                    "schema": RankingList.model_json_schema(),
                },
            )
        except GenAiError as error:
            if attempt == MAX_ATTEMPTS - 1:
                raise

            delay = retry_delay(error, attempt)
            print(f"  model call failed ({type(error).__name__}), retrying in {delay:.0f}s")
            time.sleep(delay)


def rerank_prompt(opportunities, profile_text):
    """Build the scoring prompt. Kept separate from the API call so it can be tested."""
    opp_list = []
    for opportunity in opportunities:
        themes = ", ".join(opportunity["themes"])
        opp_list.append(f"[{opportunity['source_id']}] {opportunity['title']} - {themes}")

    candidates = "\n".join(opp_list)

    return f"""You are helping a student decide which hackathons to enter.
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


def rerank(opportunities, profile_text):
    interaction = call_model(rerank_prompt(opportunities, profile_text))

    return RankingList.model_validate_json(interaction.output_text).rankings
