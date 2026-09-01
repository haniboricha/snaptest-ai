# views/guide_view.py

import streamlit as st

def render_guide_tab():
    st.markdown("## 📖 How to Use SnapTest AI")
    st.write("SnapTest AI helps QA Engineers and Developers generate production-ready Playwright TypeScript end-to-end tests from visual screenshots and HTML DOM snippets.")

    st.markdown("### 📌 Step-by-Step Workflow")
    st.markdown("""
    1. **Enter API Key:** Provide your Gemini API key in the left sidebar.
    2. **Provide Form Input:** 
       * **Screenshot:** Upload a high-resolution PNG/JPG of the user interface.
       * **HTML Snippet (Optional but Recommended):** Paste the DOM/JSX snippet for maximum selector accuracy (`id`, `data-testid`, `aria-label`).
    3. **Set Target URL:** Input the URL where the form resides in your testing/staging environment.
    4. **Generate & Download:** Click **🚀 Generate Test Cases**, preview the test matrix and code, and download the `.spec.ts` file directly.
    """)

    st.divider()

    st.markdown("### 🔒 How to Test Forms Behind Admin Login / Authentication")
    st.write("If the form you are testing is inside an admin panel or requires an authenticated session, follow one of these two standard Playwright setups:")

    st.markdown("#### Option A: Using Global Storage State (Recommended)")
    st.code("""
import { defineConfig } from '@playwright/test';

export default defineConfig({
  use: {
    storageState: 'auth.json',
    baseURL: '[http://150.107.238.224:8080](http://150.107.238.224:8080)',
  },
});
""", language="typescript")

    st.markdown("#### Option B: Inline Authentication inside `admin-login.spec.ts`")
    st.code("""
import { test, expect } from '@playwright/test';

test.describe('Protected Admin Form Suite', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('[http://150.107.238.224:8080/admin-login](http://150.107.238.224:8080/admin-login)');
    await page.getByLabel('Email Address').fill('admin@expensetrack.com');
    await page.getByLabel('Password').fill('AdminPass123!');
    await page.getByRole('button', { name: 'Sign In' }).click();
    await page.waitForURL('**/dashboard');

    await page.goto('[http://150.107.238.224:8080/admin/settings](http://150.107.238.224:8080/admin/settings)');
  });

  test('TC_01: Verify protected form submission', async ({ page }) => {
    // Generated test steps execute here
  });
});
""", language="typescript")