import streamlit as st
import json
import re
import pandas as pd
from google import genai
from google.genai import types
from PIL import Image

# 1. Page Configuration
st.set_page_config(page_title="SnapTest AI", page_icon="🧪", layout="wide")
st.title("🧪 SnapTest AI")
st.caption("Upload a screenshot and/or paste HTML/JSX to generate executable Playwright TypeScript tests.")

# 2. Sidebar API Key Input
gemini_api_key = st.sidebar.text_input("Gemini API Key", type="password")

if not gemini_api_key:
    st.info("Please enter your Gemini API key from Google AI Studio to get started.", icon="🔑")
    st.stop()

# Initialize Gemini Client
client = genai.Client(api_key=gemini_api_key)

# Robust JSON Cleaning Function
def clean_and_parse_json(raw_response_text: str) -> dict:
    cleaned = re.sub(r"```(?:json)?", "", raw_response_text, flags=re.IGNORECASE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        json_match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        raise

# 3. Transpiler Compiler Function
def compile_playwright_code(test_suite: dict, target_url: str = "[https://example.com/form](https://example.com/form)") -> str:
    code = [
        "import { test, expect } from '@playwright/test';",
        "",
        f"test.describe('{test_suite.get('suiteName', 'Form Test Suite')}', () => {{",
        f"  test.beforeEach(async ({{ page }}) => {{",
        f"    await page.goto('{target_url}');",
        f"  }});\n"
    ]

    for tc in test_suite.get("testCases", []):
        tc_id = tc.get("id", "TC")
        raw_title = tc.get("title", "").replace("'", "\\'")
        
        code.append(f"  test('{tc_id}: {raw_title}', async ({{ page }}) => {{")
        
        for step in tc.get("steps", []):
            action = step.get("action", "").lower()
            target = step.get("target", "").strip()
            val = step.get("value", "")

            if target.startswith("page."):
                if action == "fill":
                    code.append(f"    await {target}.fill('{val}');")
                elif action == "click":
                    code.append(f"    await {target}.click();")
                elif action == "select":
                    code.append(f"    await {target}.selectOption('{val}');")

            elif target.startswith("getBy"):
                if action == "fill":
                    code.append(f"    await page.{target}.fill('{val}');")
                elif action == "click":
                    code.append(f"    await page.{target}.click();")
                elif action == "select":
                    code.append(f"    await page.{target}.selectOption('{val}');")

            else:
                clean_target = target.replace("'", '"')
                if action == "fill":
                    code.append(f"    await page.fill('{clean_target}', '{val}');")
                elif action == "click":
                    code.append(f"    await page.click('{clean_target}');")
                elif action == "select":
                    code.append(f"    await page.selectOption('{clean_target}', '{val}');")

        exp = tc.get("expectedResult", "")
        code.append(f"    // Expectation: {exp}")
        
        if "valid" in raw_title.lower() and "admin" in raw_title.lower():
            code.append("    await expect(page).not.toHaveURL(/.*admin-login/);")
        else:
            code.append("    await expect(page.locator('body')).toBeVisible();")
            
        code.append("  });\n")

    code.append("});")
    return "\n".join(code)

# 4. Dual Input Setup (Visual + DOM Context)
st.subheader("1. Provide Form Inputs (Screenshot, DOM Snippet, or Both)")

col1, col2 = st.columns(2)

with col1:
    uploaded_file = st.file_uploader("Upload UI Screenshot (PNG/JPG)", type=["png", "jpg", "jpeg"])
    if uploaded_file:
        st.image(uploaded_file, caption="Uploaded Form UI Preview", use_container_width=True)

with col2:
    html_input = st.text_area(
        "Paste DOM / HTML / JSX Snippet (Optional)",
        height=220,
        placeholder="<form id=\"login-form\">\n  <input type=\"email\" id=\"admin-email\" name=\"email\" placeholder=\"Admin Email\" />\n  <button type=\"submit\" data-testid=\"submit-btn\">Sign In</button>\n</form>",
        help="Providing HTML/JSX allows the AI to extract exact IDs, names, aria-labels, and data-testids."
    )

target_url = st.text_input("Target Test URL", "[http://150.107.238.224:8080/admin-login](http://150.107.238.224:8080/admin-login)")

st.divider()

st.subheader("2. Generated Automation Tests")

# Require at least one input source
if uploaded_file is not None or html_input.strip():
    if st.button("🚀 Generate Test Cases", type="primary"):
        with st.spinner("Analyzing form context & generating Playwright tests..."):
            try:
                contents = []
                
                # Load image if supplied
                if uploaded_file is not None:
                    image = Image.open(uploaded_file)
                    contents.append(image)

                # Base prompt instructions
                prompt_instructions = """
                You are an expert QA Automation Engineer. Analyze the provided input sources (UI screenshot and/or DOM HTML/JSX snippet) to generate a Playwright test suite.

                SELECTOR PRECISION RULES:
                - If DOM/HTML code is provided, cross-reference visual elements with exact HTML attributes (`id`, `name`, `data-testid`, `aria-label`, `placeholder`, or text content).
                - Prefer explicit Playwright locator syntax:
                  * "page.getByTestId(\"submit-btn\")"
                  * "page.getByLabel(\"Email\")"
                  * "page.locator(\"#admin-email\")"
                  * "page.getByRole(\"button\", { name: \"Sign In\" })"

                TEST COVERAGE GUIDELINES:
                1. Happy Path: Valid form submission.
                2. Field Errors & Validation: Format/length checks.
                3. Missing Inputs: Empty field submissions.
                4. Interactive Elements & Navigation: Buttons, links, toggles.

                Return ONLY a valid JSON object matching this schema:
                {
                  "suiteName": "ExpenseTrack Admin Login Test Suite",
                  "summary": [
                    {
                      "ID": "TC_01",
                      "Title": "Submit form with valid admin details",
                      "Type": "Happy Path",
                      "Target Element": "Sign In Button",
                      "Expected Result": "User logs in successfully and redirects to dashboard"
                    }
                  ],
                  "testCases": [
                    {
                      "id": "TC_01",
                      "title": "Submit form with valid admin details",
                      "steps": [
                        {"action": "fill", "target": "page.locator(\"#admin-email\")", "value": "admin@expensetrack.com"},
                        {"action": "fill", "target": "page.getByLabel(\"Password\")", "value": "AdminPass123!"},
                        {"action": "click", "target": "page.getByTestId(\"submit-btn\")", "value": ""}
                      ],
                      "expectedResult": "User logs in successfully and is redirected to the admin dashboard."
                    }
                  ]
                }
                """

                # Append HTML text directly into the prompt payload if provided
                if html_input.strip():
                    prompt_instructions += f"\n\n--- TARGET DOM / HTML SNIPPET ---\n{html_input.strip()}\n--------------------------------"

                contents.append(prompt_instructions)

                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=contents,
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                        response_mime_type="application/json"
                    )
                )

                test_data = clean_and_parse_json(response.text)

                # 1. Render Summary Overview Table
                st.markdown("### 📊 Test Cases Overview")
                summary_data = test_data.get("summary", [])
                
                if not summary_data and "testCases" in test_data:
                    summary_data = [
                        {
                            "ID": tc.get("id", "N/A"),
                            "Title": tc.get("title", "N/A"),
                            "Expected Result": tc.get("expectedResult", "N/A")
                        }
                        for tc in test_data["testCases"]
                    ]

                if summary_data:
                    df = pd.DataFrame(summary_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)

                # 2. Render Playwright Code
                st.markdown("### 📋 Executable Playwright Code")
                playwright_code = compile_playwright_code(test_data, target_url)
                st.code(playwright_code, language="typescript")

                # 3. Download Button
                st.download_button(
                    label="📥 Download admin-login.spec.ts",
                    data=playwright_code,
                    file_name="admin-login.spec.ts",
                    mime="text/plain"
                )

            except Exception as e:
                st.error(f"Failed to process inputs: {str(e)}")
else:
    st.info("Please upload a form screenshot or paste a DOM HTML snippet above to generate test cases.")