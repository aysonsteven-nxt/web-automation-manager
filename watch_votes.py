import time
from playwright.sync_api import sync_playwright

VOTE_URL = "https://cp.forsaken-ro.net/?module=vote"
CHECK_INTERVAL = 5  # seconds

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    context = browser.new_context(
        storage_state="forsaken_session.json"
    )

    page = context.new_page()

    while True:
        try:
            page.goto(
                VOTE_URL,
                wait_until="domcontentloaded"
            )

            banners = page.locator('[id^="banner_"]')

            print("\n=== CHECK ===")

            for i in range(banners.count()):
                banner = banners.nth(i)

                banner_id = banner.get_attribute("id")
                text = " ".join(banner.inner_text().split())

                links = banner.locator("a")
                link_count = links.count()

                if link_count > 0:
                    print(f"\nAVAILABLE: {banner_id}")
                    print(f"TEXT: {text}")

                    for j in range(link_count):
                        link = links.nth(j)

                        print(
                            "HREF:",
                            link.get_attribute("href")
                        )

                        print(
                            "HTML:",
                            link.evaluate(
                                "(el) => el.outerHTML"
                            )
                        )
                else:
                    print(f"{banner_id}: {text}")

        except Exception as e:
            print("ERROR:", e)

        time.sleep(CHECK_INTERVAL)