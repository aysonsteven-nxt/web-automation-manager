import re
from typing import Any

from automation.strategy import AutomationStrategy


class ForsakenRoStrategy(AutomationStrategy):
    """
    ForsakenRO automation strategy.

    Contains all ForsakenRO-specific logic, including:
    - Reading the current credit balance
    - Discovering vote providers
    - Determining provider availability
    - Reading provider cooldown information
    - Executing a vote provider action
    """

    def check(self, page) -> dict[str, Any]:
        """
        Inspect the ForsakenRO vote page and return its current state.
        """

        credits = self._get_credit_balance(page)
        providers = self._get_vote_providers(page)

        available_count = sum(
            1
            for provider in providers
            if provider.get("available", False)
        )

        return {
            "credits": credits,
            "totalCount": len(providers),
            "availableCount": available_count,
            "providers": providers,
        }

    def execute(
        self,
        context,
        page,
        target: dict[str, Any],
    ) -> bool:
        """
        Execute a vote against a ForsakenRO vote provider.

        Returns:
            True  - if the credit balance increased
            False - if the vote could not be completed/verified
        """

        target_id = target.get("id")

        if not target_id:
            raise ValueError(
                "Vote provider target is missing 'id'"
            )

        selector = f"#banner_{target_id} a"

        link = page.locator(selector).first

        if link.count() == 0:
            print(
                f"Provider {target_id}: link not found",
                flush=True,
            )
            return False

        if not link.is_visible():
            print(
                f"Provider {target_id}: link is not visible",
                flush=True,
            )
            return False

        href = link.get_attribute("href")

        if not href:
            print(
                f"Provider {target_id}: link has no href",
                flush=True,
            )
            return False

        old_credits = self._get_credit_balance(page)

        print(
            f"Provider {target_id}: current credits = {old_credits}",
            flush=True,
        )

        popup = None

        try:
            # ForsakenRO opens the external voting provider in a new tab.
            with context.expect_page(timeout=10000) as page_info:
                link.click()

            popup = page_info.value

            try:
                popup.wait_for_load_state(
                    "domcontentloaded",
                    timeout=15000,
                )
            except Exception:
                # Some external providers may not finish loading normally.
                pass

            try:
                print(
                    f"Provider {target_id}: external URL = {popup.url}",
                    flush=True,
                )
            except Exception:
                pass

        except Exception as exc:
            print(
                f"Provider {target_id}: failed to open external page: "
                f"{exc}",
                flush=True,
            )

            return False

        finally:
            if popup is not None:
                try:
                    popup.close()
                except Exception:
                    pass

        try:
            page.bring_to_front()
        except Exception:
            pass

        try:
            page.reload(
                wait_until="domcontentloaded",
            )
        except Exception as exc:
            print(
                f"Provider {target_id}: failed to reload vote page: "
                f"{exc}",
                flush=True,
            )
            return False

        new_credits = self._get_credit_balance(page)

        print(
            f"Provider {target_id}: credits after vote = {new_credits}",
            flush=True,
        )

        if new_credits > old_credits:
            print(
                f"Provider {target_id}: vote verified successfully",
                flush=True,
            )
            return True

        print(
            f"Provider {target_id}: vote could not be verified",
            flush=True,
        )

        return False

    @staticmethod
    def _get_credit_balance(page) -> int:
        """
        Extract the current ForsakenRO credit balance from the page.
        """

        try:
            text = page.locator("body").inner_text()

            match = re.search(
                r"Current Credit Balance\s+(\d+)",
                text,
                re.IGNORECASE,
            )

            if match:
                return int(match.group(1))

        except Exception:
            pass

        return 0

    @staticmethod
    def _get_cooldown(banner) -> str | None:
        """
        Extract the cooldown displayed for a ForsakenRO provider.

        Expected HTML structure:

            <tr>
                <th>Vote in...</th>
                <td>
                    <strong>11 hour(s)</strong>
                </td>
            </tr>
        """

        try:
            row = banner.locator("tr").filter(
                has_text="Vote in"
            ).first

            if row.count() == 0:
                return None

            strong = row.locator("strong").first

            if strong.count() == 0:
                return None

            text = strong.inner_text().strip()

            return text or None

        except Exception:
            return None

    @classmethod
    def _get_vote_providers(
        cls,
        page,
    ) -> list[dict[str, Any]]:
        """
        Discover ForsakenRO vote provider banners.

        Expected banner structure:

            #banner_2
            #banner_8
            #banner_3
            ...

        Each provider may contain a cooldown row such as:

            Vote in...
            11 hour(s)
        """

        providers: list[dict[str, Any]] = []

        banners = page.locator('[id^="banner_"]')

        try:
            count = banners.count()
        except Exception:
            return providers

        for index in range(count):
            banner = banners.nth(index)

            try:
                banner_id = banner.get_attribute("id")

                if not banner_id:
                    continue

                if not banner_id.startswith("banner_"):
                    continue

                provider_id = banner_id.replace(
                    "banner_",
                    "",
                    1,
                )

                link = banner.locator("a").first

                if link.count() == 0:
                    providers.append(
                        {
                            "id": provider_id,
                            "available": False,
                            "cooldown": cls._get_cooldown(banner),
                            "href": None,
                        }
                    )
                    continue

                href = link.get_attribute("href")

                disabled_attribute = link.get_attribute(
                    "disabled"
                )

                available = (
                    href is not None
                    and href.strip() != ""
                    and disabled_attribute is None
                )

                cooldown = cls._get_cooldown(banner)

                providers.append(
                    {
                        "id": provider_id,
                        "available": available,
                        "cooldown": cooldown,
                        "href": href,
                    }
                )

            except Exception:
                continue

        return providers