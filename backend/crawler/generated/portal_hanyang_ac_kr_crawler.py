from playwright.sync_api import sync_playwright

def run_playwright():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto("https://portal.hanyang.ac.kr/sugang/sulg.do#!UDMxMDI4MiRAXnN1Z2FuZy8kQF4kQF5NMDA4OTU3JEBe7IiY6rCV7JWI64K0JEBeTTAwODk1NyRAXmU3NDBmYWExMjc0YmEyMDZjNGFjMTc5NWEzZWJhNDgzYTJkYjlmMjUxZmU4MWRiMDIzODdkMjcwZTY1MGJkYTgg", timeout=30000, wait_until="networkidle")
            content = page.inner_text("body")
            data = []
            try:
                data = eval(content.split('var CONTEXT = "";')[1].split(';')[0].strip().split('=')[1].strip().replace('"', '').replace(' ', '')
            except Exception as e:
                pass
        finally:
            browser.close()
    print(f"[{data}]")
run_playwright()