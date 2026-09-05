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

    def __init__(
        self,
        config: VotingStrategyConfig,
    ) -> None:
        self.config = config

    # ========================================================
    # Configuration
    # ========================================================

    @property
    def strategy_config(
        self,
    ) -> VotingStrategyConfig:
        return self.config

    # ========================================================
    # Lifecycle
    # ========================================================

    def initialize(
        self,
        automation: WebAutomation,
    ) -> None:
        page = automation.page

        if page is None:
            raise RuntimeError(
                "Web automation has not been started."
            )

        page.goto(
            automation.web_config.url,
            wait_until="domcontentloaded",
        )

        self._ensure_authenticated(page)
        self._wait_for_vote_page(page)

    # ========================================================
    # Check
    # ========================================================

    def check(
        self,
        automation: WebAutomation,
    ) -> dict[str, Any]:
        page = automation.page

        if page is None:
            raise RuntimeError(
                "Web automation has not been started."
            )

        # Always refresh the voting page before reading its
        # state. This prevents stale provider/cooldown data
        # from remaining in the long-running browser page.
        self._refresh_vote_page(page)

        credits = self._get_credit_balance(
            page
        )

        providers = self._get_vote_providers(
            page
        )

        available_count = sum(
            1
            for provider in providers
            if provider.get(
                "available",
                False,
            )
        )

        return {
            "credits": credits,
            "totalCount": len(providers),
            "availableCount": available_count,
            "providers": providers,
        }

    # ========================================================
    # Targets
    # ========================================================

    def get_targets(
        self,
        state: dict[str, Any],
    ) -> list[dict[str, Any]]:
        return [
            provider
            for provider in state.get(
                "providers",
                [],
            )
            if provider.get(
                "available",
                False,
            )
        ]

    # ========================================================
    # Execute
    # ========================================================

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

        selector = (
            f"#banner_{target_id} a"
        )

        link = page.locator(
            selector
        ).first

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

        href = link.get_attribute(
            "href"
        )

        if not href:
            print(
                f"Provider {target_id}: "
                "link has no href",
                flush=True,
            )
            return False

        old_credits = (
            self._get_credit_balance(
                page
            )
        )

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
                "failed to open external page: "
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

            self._wait_for_vote_page(
                page
            )

        except Exception as exc:
            print(
                f"Provider {target_id}: "
                "failed to reload vote page: "
                f"{exc}",
                flush=True,
            )
            return False

        new_credits = (
            self._get_credit_balance(
                page
            )
        )

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

    # ========================================================
    # Page Refresh
    # ========================================================

    @staticmethod
    def _refresh_vote_page(
        page,
    ) -> None:
        """
        Reload the voting page before every state check.

        The worker is long-running, so relying on the existing
        DOM can result in stale cooldown/provider information.
        """

        try:
            page.reload(
                wait_until="domcontentloaded",
            )

            VotingStrategy._ensure_authenticated(page)
            VotingStrategy._wait_for_vote_page(
                page
            )

        except Exception as exc:
            raise RuntimeError(
                "Failed to refresh voting page: "
                f"{exc}"
            ) from exc

    @staticmethod
    def _ensure_authenticated(page) -> None:
        url = str(page.url).lower()

        if "action=login" in url:
            raise RuntimeError(
                "Web session is not authenticated. "
                "Run session_manager.py to create a new session."
            )

        try:
            text = page.locator("body").inner_text().lower()

        except Exception:
            return

        if "please log-in to vote" in text:
            raise RuntimeError(
                "Web session is not authenticated. "
                "Run session_manager.py to create a new session."
            )

    @staticmethod
    def _wait_for_vote_page(
        page,
    ) -> None:
        """
        Wait until the voting provider containers exist.

        domcontentloaded only guarantees that the document has
        been parsed. The provider elements may still be loading.
        """

        banners = page.locator(
            '[id^="banner_"]'
        )

        banners.first.wait_for(
            state="attached",
            timeout=15000,
        )

    # ========================================================
    # Credit Balance
    # ========================================================

    @staticmethod
    def _get_credit_balance(
        page,
    ) -> int:
        try:
            text = page.locator(
                "body"
            ).inner_text()

            match = re.search(
                r"Current Credit Balance\s+(\d+)",
                text,
                re.IGNORECASE,
            )

            if match:
                return int(
                    match.group(1)
                )

        except Exception:
            pass

        return 0

    # ========================================================
    # Cooldown
    # ========================================================

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
            row = banner.locator(
                "tr"
            ).filter(
                has_text="Vote in"
            ).first

            if row.count() == 0:
                return None

            strong = row.locator(
                "strong"
            ).first

            if strong.count() == 0:
                return None

            text = strong.inner_text().strip()

            return text or None

        except Exception:
            return None

    # ========================================================
    # Vote Providers
    # ========================================================

    @classmethod
    def _get_vote_providers(
        cls,
        page,
    ) -> list[dict[str, Any]]:
        providers: list[
            dict[str, Any]
        ] = []

        banners = page.locator(
            '[id^="banner_"]'
        )

        try:
            count = banners.count()

        except Exception:
            return providers

        for index in range(count):
            banner = banners.nth(
                index
            )

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

                link = banner.locator(
                    "a"
                ).first

                if link.count() == 0:
                    providers.append(
                        {
                            "id": provider_id,
                            "available": False,
                            "cooldown": (
                                cls._get_cooldown(
                                    banner
                                )
                            ),
                            "href": None,
                        }
                    )

                    continue

                href = link.get_attribute(
                    "href"
                )

                disabled_attribute = (
                    link.get_attribute(
                        "disabled"
                    )
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