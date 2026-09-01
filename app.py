# app.py

import streamlit as st
from views.generator_view import render_generator_tab
from views.guide_view import render_guide_tab

st.set_page_config(page_title="SnapTest AI", page_icon="🧪", layout="wide")
st.title("🧪 SnapTest AI")

gemini_api_key = st.sidebar.text_input("Gemini API Key", type="password")

if not gemini_api_key:
    st.info("Please enter your Gemini API key from Google AI Studio in the sidebar to get started.", icon="🔑")
    st.stop()

tab_generator, tab_guide = st.tabs(["🚀 Test Generator", "📖 How to Use & Documentation"])

with tab_generator:
    render_generator_tab(gemini_api_key)

with tab_guide:
    render_guide_tab()