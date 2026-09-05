# services/gemini_service.py

import json
import re
import time
from PIL import Image
from google import genai
from google.genai import types
from google.genai.errors import APIError
from config import SYSTEM_PROMPT_TEMPLATE

# Supported active models only
MODELS_TO_TRY = ["gemini-2.5-flash", "gemini-2.5-flash-lite"]

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

    for model_name in MODELS_TO_TRY:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=config
                )
                return clean_and_parse_json(response.text)
                
            except APIError as e:
                last_error = e
                # Retry on busy server (503) or rate limit (429)
                if e.code in (503, 429) or "UNAVAILABLE" in str(e).upper():
                    time.sleep(2)
                    continue
                # If a model returns 404 or other errors, break loop to hit the next fallback model immediately
                break
            except Exception as e:
                last_error = e
                break

    raise Exception(f"Unable to process request with available models. Details: {last_error}")