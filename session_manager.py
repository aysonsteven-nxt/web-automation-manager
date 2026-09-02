from playwright.sync_api import sync_playwright

URL = "https://cp.forsaken-ro.net/?module=account&action=login"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)

    context = browser.new_context()

    page = context.new_page()
    page.goto(URL)

    print("Please log in to ForsakenRO in the browser.")
    input("After you are logged in, press ENTER here...")

    context.storage_state(path="forsaken_session.json")

    print("Session saved to forsaken_session.json")

    browser.close()