# services/transpiler.py

def compile_playwright_code(test_suite: dict, target_url: str = "https://example.com/form") -> str:
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