from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "https://cp.forsaken-ro.net/?module=account&action=login"
SESSION_FILE = Path(__file__).resolve().parent / "forsaken_session.json"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)

    context = browser.new_context()

    page = context.new_page()
    page.goto(URL)

    print("Please log in to ForsakenRO in the browser.")
    input("After you are logged in, press ENTER here...")

    cookies = context.cookies(
        ["https://cp.forsaken-ro.net/"]
    )

    context.storage_state(
        path=str(SESSION_FILE)
    )

    print("Current URL:", page.url)
    print("Page title:", page.title())
    print(
        "Cookies:",
        [cookie["name"] for cookie in cookies],
    )
    print("Session saved to:", SESSION_FILE)

    browser.close()