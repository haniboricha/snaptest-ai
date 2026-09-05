# services/gemini_service.py

import json
import re
import time
from PIL import Image
from google import genai
from google.genai import types
from google.genai.errors import APIError
from config import SYSTEM_PROMPT_TEMPLATE

# Primary model and reliable fallback models in case of server traffic spikes
MODELS_TO_TRY = ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.0-flash"]

def clean_and_parse_json(raw_response_text: str) -> dict:
    cleaned = re.sub(r"```(?:json)?", "", raw_response_text, flags=re.IGNORECASE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        json_match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        raise ValueError("Failed to extract valid JSON output from response.")

def generate_test_suite(api_key: str, uploaded_image: Image.Image = None, html_snippet: str = "") -> dict:
    clean_key = api_key.strip() if api_key else ""
    if not clean_key:
        raise ValueError("Please enter a valid Gemini API Key in the sidebar.")

    client = genai.Client(api_key=clean_key)
    
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

    last_error = None

    # Try each model sequentially if Google's servers return a 503 (High Demand) or 429 (Rate Limit)
    for model_name in MODELS_TO_TRY:
        for attempt in range(2):  # Try 2 times per model with backoff
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=config
                )
                return clean_and_parse_json(response.text)
                
            except APIError as e:
                last_error = e
                # Server busy (503) or rate limit (429) -> retry or try fallback model
                if e.code in (503, 429) or "UNAVAILABLE" in str(e).upper():
                    time.sleep(2)
                    continue
                # If credentials or input errors occur, raise immediately
                raise Exception(f"Gemini API Error ({e.code}): {e.message}")
            except Exception as e:
                last_error = e
                break

    raise Exception(f"Google Gemini servers are currently experiencing severe high demand across all models. Please wait 1-2 minutes and try clicking 'Generate Test Cases' again. (Last Error: {last_error})")