from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "https://cp.forsaken-ro.net/"
SESSION_FILE = Path(__file__).resolve().parent / "forsaken_session.json"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)

    context = browser.new_context(
        storage_state=str(SESSION_FILE)
    )

    page = context.new_page()
    page.goto(URL)

    print("Current URL:", page.url)
    print("Page title:", page.title())
    print(
        "Cookies:",
        [
            cookie["name"]
            for cookie in context.cookies(
                [URL]
            )
        ],
    )

    input("Press ENTER to close...")

    browser.close()