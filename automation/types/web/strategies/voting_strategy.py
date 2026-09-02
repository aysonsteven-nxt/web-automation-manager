import re
from typing import Any

from automation.core.strategy import AutomationStrategy
from automation.types.web.automation import WebAutomation
from automation.types.web.strategies.config import (
    VotingStrategyConfig,
)


class VotingStrategy(AutomationStrategy):
    """
    Generic web voting automation strategy.

    Handles:
    - Reading the current credit balance
    - Discovering vote providers
    - Determining provider availability
    - Reading provider cooldown information
    - Executing a vote provider action
    - Verifying the vote through the updated credit balance
    """

    def initialize(
        self,
        automation: WebAutomation,
    ) -> None:
        page = automation.page

        if page is None:
            raise RuntimeError(
                "Web automation has not been started."
            )

        self._automation = automation

        page.goto(
            automation.web_config.url,
            wait_until="domcontentloaded",
        )

    @property
    def strategy_config(
        self,
    ) -> VotingStrategyConfig:
        if not hasattr(self, "_automation"):
            raise RuntimeError(
                "Voting strategy has not been initialized."
            )

        return VotingStrategyConfig(
            action_delay_seconds=(
                self._automation.config.config[
                    "strategy"
                ]["action_delay_seconds"]
            )
        )

    def check(
        self,
        automation: WebAutomation,
    ) -> dict[str, Any]:
        page = automation.page

        if page is None:
            raise RuntimeError(
                "Web automation has not been started."
            )

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

    def get_targets(
        self,
        state: dict[str, Any],
    ) -> list[dict[str, Any]]:
        return [
            provider
            for provider in state.get("providers", [])
            if provider.get("available", False)
        ]

    def execute(
        self,
        automation: WebAutomation,
        target: dict[str, Any],
    ) -> bool:
        page = automation.page
        context = automation.context

        if page is None or context is None:
            raise RuntimeError(
                "Web automation has not been started."
            )

        target_id = target.get("id")

        if not target_id:
            raise ValueError(
                "Vote provider target is missing 'id'"
            )

        selector = f"#banner_{target_id} a"

        link = page.locator(selector).first

        if link.count() == 0:
            print(
                f"Provider {target_id}: "
                "link not found",
                flush=True,
            )
            return False

        if not link.is_visible():
            print(
                f"Provider {target_id}: "
                "link is not visible",
                flush=True,
            )
            return False

        href = link.get_attribute("href")

        if not href:
            print(
                f"Provider {target_id}: "
                "link has no href",
                flush=True,
            )
            return False

        old_credits = self._get_credit_balance(page)

        print(
            f"Provider {target_id}: "
            f"current credits = {old_credits}",
            flush=True,
        )

        popup = None

        try:
            with context.expect_page(
                timeout=10000
            ) as page_info:
                link.click()

            popup = page_info.value

            try:
                popup.wait_for_load_state(
                    "domcontentloaded",
                    timeout=15000,
                )
            except Exception:
                pass

            try:
                print(
                    f"Provider {target_id}: "
                    f"external URL = {popup.url}",
                    flush=True,
                )
            except Exception:
                pass

        except Exception as exc:
            print(
                f"Provider {target_id}: "
                f"failed to open external page: "
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
                f"Provider {target_id}: "
                f"failed to reload vote page: "
                f"{exc}",
                flush=True,
            )
            return False

        new_credits = self._get_credit_balance(page)

        print(
            f"Provider {target_id}: "
            f"credits after vote = {new_credits}",
            flush=True,
        )

        if new_credits > old_credits:
            print(
                f"Provider {target_id}: "
                "vote verified successfully",
                flush=True,
            )
            return True

        print(
            f"Provider {target_id}: "
            "vote could not be verified",
            flush=True,
        )

        return False

    @staticmethod
    def _get_credit_balance(page) -> int:
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
    def _get_cooldown(
        banner,
    ) -> str | None:
        """
        Expected HTML:
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
        providers: list[dict[str, Any]] = []

        banners = page.locator(
            '[id^="banner_"]'
        )

        try:
            count = banners.count()

        except Exception:
            return providers

        for index in range(count):
            banner = banners.nth(index)

            try:
                banner_id = banner.get_attribute(
                    "id"
                )

                if not banner_id:
                    continue

                if not banner_id.startswith(
                    "banner_"
                ):
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
                            "cooldown": cls._get_cooldown(
                                banner
                            ),
                            "href": None,
                        }
                    )
                    continue

                href = link.get_attribute(
                    "href"
                )

                disabled_attribute = (
                    link.get_attribute("disabled")
                )

                available = (
                    href is not None
                    and href.strip() != ""
                    and disabled_attribute is None
                )

                cooldown = cls._get_cooldown(
                    banner
                )

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