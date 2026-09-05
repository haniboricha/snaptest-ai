# services/gemini_service.py

import json
import re
import time
from PIL import Image
from google import genai
from google.genai import types
from google.genai.errors import APIError
from config import GEMINI_MODEL, SYSTEM_PROMPT_TEMPLATE

def clean_and_parse_json(raw_response_text: str) -> dict:
    cleaned = re.sub(r"```(?:json)?", "", raw_response_text, flags=re.IGNORECASE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        json_match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        raise

def generate_test_suite(api_key: str, uploaded_image: Image.Image = None, html_snippet: str = "") -> dict:
    client = genai.Client(api_key=api_key)
    contents = []

    if uploaded_image:
        contents.append(uploaded_image)

    prompt = SYSTEM_PROMPT_TEMPLATE
    if html_snippet.strip():
        prompt += f"\n\n--- TARGET DOM / HTML SNIPPET ---\n{html_snippet.strip()}\n--------------------------------"
    
    contents.append(prompt)

    config = types.GenerateContentConfig(
        temperature=0.2,
        response_mime_type="application/json"
    )

    # List of candidate models in order of priority
    models_to_try = [
        GEMINI_MODEL if GEMINI_MODEL else "gemini-2.5-flash",
        "gemini-2.5-flash",
        "gemini-1.5-flash-latest"
    ]
    
    # Remove duplicates while preserving order
    candidate_models = list(dict.fromkeys(models_to_try))

    last_error = None

    for model in candidate_models:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config
                )
                return clean_and_parse_json(response.text)
            except APIError as e:
                last_error = e
                # Check for 503 Server Unavailable or 429 Rate Limit
                if e.code in (503, 429) or "UNAVAILABLE" in str(e):
                    if attempt < max_retries - 1:
                        sleep_time = (2 ** attempt) * 3  # Wait 3s, then 6s, then 12s
                        time.sleep(sleep_time)
                        continue
                # If non-transient API error, jump to next candidate model
                break
            except Exception as e:
                last_error = e
                break

    raise Exception(f"Google Gemini servers are currently experiencing high demand. Please try clicking 'Generate Test Cases' again in 10-15 seconds. Details: {last_error}")