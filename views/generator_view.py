# views/generator_view.py

import streamlit as st
import pandas as pd
from PIL import Image
from services.gemini_service import generate_test_suite
from services.transpiler import compile_playwright_code

def render_generator_tab(api_key: str):
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

    target_url = st.text_input(
        label="Target Test URL",
        placeholder="https://your-app.com/login",
        help="Enter the exact URL of the page you want Playwright to navigate to before running tests."
    )

    st.divider()

    st.subheader("2. Generated Automation Tests")

    if uploaded_file is not None or html_input.strip():
        if st.button("🚀 Generate Test Cases", type="primary"):
            with st.spinner("Analyzing form context & generating Playwright tests..."):
                try:
                    pil_image = Image.open(uploaded_file) if uploaded_file else None
                    test_data = generate_test_suite(api_key, pil_image, html_input)

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

                    st.markdown("### 📋 Executable Playwright Code")
                    playwright_code = compile_playwright_code(test_data, target_url)
                    st.code(playwright_code, language="typescript")

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