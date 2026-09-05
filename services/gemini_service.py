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

    # 1. Attempt using primary model with retry loop on 503 errors
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=contents,
                config=config
            )
            return clean_and_parse_json(response.text)
        except Exception as e:
            error_msg = str(e)
            if ("503" in error_msg or "UNAVAILABLE" in error_msg) and attempt < max_retries - 1:
                time.sleep((2 ** attempt) + 1)  # Wait 2s, then 5s before retrying
                continue
            break

    # 2. Fallback attempt using fast model if primary model is overloaded
    fallback_model = "gemini-1.5-flash"
    try:
        response = client.models.generate_content(
            model=fallback_model,
            contents=contents,
            config=config
        )
        return clean_and_parse_json(response.text)
    except Exception as e:
        raise Exception(f"Gemini API is currently overloaded. Please wait a moment and try again. ({e})")