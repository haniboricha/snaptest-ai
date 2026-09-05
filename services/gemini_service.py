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

    # Clean list of valid Gemini model identifiers in order of priority
    candidate_models = ["gemini-2.5-flash", "gemini-1.5-flash"]
    if GEMINI_MODEL and GEMINI_MODEL not in candidate_models:
        candidate_models.insert(0, GEMINI_MODEL)

    last_error = None

    for model_name in candidate_models:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=config
                )
                return clean_and_parse_json(response.text)
            except APIError as e:
                last_error = e
                # Retry on 503 Server Unavailable or 429 Rate Limit
                if e.code in (503, 429) or "UNAVAILABLE" in str(e):
                    if attempt < max_retries - 1:
                        time.sleep((2 ** attempt) * 2 + 1)  # Waits 3s, 5s, 9s
                        continue
                # If model is not found or non-transient, switch to the next candidate
                break
            except Exception as e:
                last_error = e
                break

    raise Exception(f"Google Gemini servers are temporarily busy. Please wait a moment and try again. Details: {last_error}")