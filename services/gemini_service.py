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
    """Strips Markdown code fences and parses raw JSON string."""
    cleaned = re.sub(r"```(?:json)?", "", raw_response_text, flags=re.IGNORECASE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        json_match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        raise ValueError("Failed to extract valid JSON output from response.")

def generate_test_suite(api_key: str, uploaded_image: Image.Image = None, html_snippet: str = "") -> dict:
    """
    Generates structured test cases using the Google GenAI SDK with gemini-2.5-flash.
    Includes explicit retry handling for temporary server busy state (429/503).
    """
    if not api_key or not api_key.strip():
        raise ValueError("Gemini API Key is missing. Please provide a valid key in the sidebar.")

    # Initialize client explicitly
    client = genai.Client(api_key=api_key.strip())
    
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

    # Force target model to gemini-2.5-flash
    target_model = GEMINI_MODEL if GEMINI_MODEL else "gemini-2.5-flash"

    max_retries = 3
    last_error = None

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=target_model,
                contents=contents,
                config=config
            )
            return clean_and_parse_json(response.text)
            
        except APIError as e:
            last_error = e
            # Retry on rate limit (429) or temporary server unavailability (503)
            if e.code in (429, 503) or "UNAVAILABLE" in str(e).upper():
                if attempt < max_retries - 1:
                    time.sleep(3 * (attempt + 1))
                    continue
            raise Exception(f"Gemini API Error ({e.code}): {e.message}")
            
        except Exception as e:
            last_error = e
            break

    raise Exception(f"Failed to generate tests due to server load: {last_error}")