from google import genai
from dotenv import load_dotenv
import os
import json
import re

load_dotenv()

gemini_api = os.getenv("GEMINI_API_KEY")

class Agent:
  def __init__(self, file_path):
    self.file_path = file_path
    self.summary = self.make_summary()
    
  def make_summary(self):
    with open(self.file_path, "r") as f:
      data = json.load(f)
    summary_str = json.dumps(data)
    return summary_str

  def solve(self):
      client = genai.Client(api_key=gemini_api)
      prompt = f"""SYSTEM:
You are a pragmatic license-term generator for research artifacts (paper text, code, model weights, datasets). Your task: read the provided research paper summary and generate exactly **3 distinct** license templates tailored to that paper. Each license must be focused on the **royalties** field and must be consistent in structure and types across all three objects. Output **only** a JSON array (no explanation, no markdown, no extra text).

USER:
INPUT_SUMMARY:
{self.summary}

OUTPUT REQUIREMENTS (strict — must follow exactly):

1. Top-level output: a JSON array with exactly 3 objects.

2. Each object must include the following fields (names and types must match exactly):

- "license_id": string — unique short id (e.g., "REVSHARE-001").
- "license_name": string — human-friendly name.
- "license_type": string — one of: "open-attribution", "permissive-patent", "commercial-revenue-share", "saas-api", "dual-license", "contributor-revenue-split" (choose the best-fit label).
- "royalties": object containing:
    - "model": string — one of: "none", "percentage", "per_call_or_subscription", "flat_fee".
    - "value": number — if model is "percentage" use integer (0-100). If "flat_fee" use USD amount. If "per_call_or_subscription" use numeric per-call USD (e.g., 0.005) or 0 if variable.
    - "split": object or null — if present, keys are stakeholders and values are integers that sum to 100. If not applicable, set null.
    - "payment_interval_days": integer or null — days between payouts (e.g., 30, 90) or null.
    - "min_fee_usd": number or null — minimum payable fee in USD, or null.
    - "notes": string — short note about how royalties apply (1-2 sentences).

- "restrictions": array of strings — key restrictions/obligations (e.g., attribution, no redistribution of weights, reporting, telemetry).

3. Additional rules & constraints:
- All 3 licenses must be distinct (different "license_type" or different royalty models).
- Tailor each license to the input summary: reference relevant artifact types present in the summary (code repo, model weights, datasets, etc.) in "restrictions" or "notes" where appropriate.
- The "royalties" field must be prominent and realistic (e.g., common revenue-share values 5–30% or per-call pricing like 0.001–0.05 USD).
- If "split" is provided, the integer parts must sum to 100.
- Use "PERCENT" as currency when model is "percentage"; use "USD_PER_CALL" for per-call values.
- Do not output any additional fields beyond the specified schema.
- Output must be valid JSON (no trailing commas).

4. Ordering:
- Order the array by "popularity_for_deployment" inferred from the summary: most broadly adoptable license first, most restrictive/commercial last.


END.
"""

      resp = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt
      )
      
      cleaned_str = re.sub(r"^\s*```json\s*|\s*```\s*$", "", resp.text.strip(), flags=re.MULTILINE).strip()
      structured_output_dict = json.loads(cleaned_str)  
      
      return structured_output_dict