import os
import json
from google import genai
from pydantic import BaseModel

_client: genai.Client | None = None

SEVERITY_RUBRIC = """
Rate severity of the described event on a 0.0-1.0 scale using these anchors:
0.0-0.2 = routine/monitoring mention, no incident occurring
0.3-0.5 = tension or threat mentioned, no physical incident has occurred
0.6-0.8 = active incident (seizure, near-miss, strike, attack)
0.9-1.0 = sustained closure or blockade of a shipping corridor
"""

VALID_CORRIDORS = ["hormuz", "bab_el_mandeb", "red_sea_suez"]

SYSTEM_PROMPT = f"""You are a geopolitical risk analyst extracting structured
signals from a single news headline about global energy shipping.

{SEVERITY_RUBRIC}

Valid corridor values: {", ".join(VALID_CORRIDORS)}. If the headline does not
clearly reference one of these corridors, pick the single most plausible one
based on the geography/context mentioned — never invent a new corridor name.

Extract:
- corridor: one of the valid corridor ids above
- entities: list of named countries, organizations, or groups involved
- severity: float 0.0-1.0 per the rubric above

Be consistent: score the EVENT described, not the tone of the headline. A
calmly-worded report of an actual seizure is still 0.6-0.8, not 0.2.
"""


class RiskExtraction(BaseModel):
    corridor: str
    entities: list[str]
    severity: float


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _client


def extract_risk_signal(headline_title: str) -> RiskExtraction:
    client = _get_client()
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"Headline: {headline_title}",
        config={
            "system_instruction": SYSTEM_PROMPT,
            "response_mime_type": "application/json",
            "response_schema": RiskExtraction,
            "temperature": 0.1,  # low temp for consistent severity scoring
        },
    )
    data = json.loads(response.text)
    corridor = data.get("corridor")
    if corridor not in VALID_CORRIDORS:
        corridor = VALID_CORRIDORS[0]  # safe fallback, never crash the poll cycle
    return RiskExtraction(
        corridor=corridor,
        entities=data.get("entities", []),
        severity=max(0.0, min(1.0, float(data.get("severity", 0.0)))),
    )

def embed_text(text: str) -> list[float]:
    """Generates a 768-dimensional text embedding using Gemini."""
    client = _get_client()
    response = client.models.embed_content(
        model="gemini-embedding-2",
        contents=text,
        config={'output_dimensionality': 768}
    )
    return response.embeddings[0].values
