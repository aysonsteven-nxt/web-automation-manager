from playwright.sync_api import sync_playwright

URL = "https://cp.forsaken-ro.net/"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)

    context = browser.new_context(
        storage_state="forsaken_session.json"
    )

    page = context.new_page()
    page.goto(URL)

    print("Current URL:", page.url)
    print("Page title:", page.title())

    input("Press ENTER to close...")

    browser.close()