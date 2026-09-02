from unittest.mock import MagicMock, patch

import pytest

from automation.types.web.strategies.voting_strategy import (
    VotingStrategy,
)


@pytest.fixture
def strategy():
    return VotingStrategy()


# ============================================================
# initialize()
# ============================================================


def test_initialize_requires_started_automation(
    strategy,
):
    automation = MagicMock()
    automation.page = None

    with pytest.raises(
        RuntimeError,
        match="Web automation has not been started",
    ):
        strategy.initialize(
            automation
        )


def test_initialize_navigates_to_configured_url(
    strategy,
):
    automation = MagicMock()

    page = MagicMock()

    automation.page = page
    automation.web_config.url = (
        "https://example.com/vote"
    )

    strategy.initialize(
        automation
    )

    page.goto.assert_called_once_with(
        "https://example.com/vote",
        wait_until="domcontentloaded",
    )


# ============================================================
# check()
# ============================================================


def test_check_reads_credit_balance(
    strategy,
):
    automation = MagicMock()

    page = MagicMock()
    automation.page = page

    strategy._get_credit_balance = MagicMock(
        return_value=25
    )

    strategy._get_vote_providers = MagicMock(
        return_value=[]
    )

    result = strategy.check(
        automation
    )

    assert result["credits"] == 25
    assert result["totalCount"] == 0
    assert result["availableCount"] == 0
    assert result["providers"] == []


def test_check_returns_provider_information(
    strategy,
):
    automation = MagicMock()

    page = MagicMock()
    automation.page = page

    strategy._get_credit_balance = MagicMock(
        return_value=10
    )

    providers = [
        {
            "id": "1",
            "available": True,
            "cooldown": None,
            "href": "https://example.com/1",
        },
        {
            "id": "2",
            "available": False,
            "cooldown": "10 hour(s)",
            "href": None,
        },
    ]

    strategy._get_vote_providers = MagicMock(
        return_value=providers
    )

    result = strategy.check(
        automation
    )

    assert result == {
        "credits": 10,
        "totalCount": 2,
        "availableCount": 1,
        "providers": providers,
    }


def test_check_requires_started_automation(
    strategy,
):
    automation = MagicMock()
    automation.page = None

    with pytest.raises(
        RuntimeError,
        match="Web automation has not been started",
    ):
        strategy.check(
            automation
        )


# ============================================================
# get_targets()
# ============================================================


def test_get_targets_returns_available_providers(
    strategy,
):
    state = {
        "providers": [
            {
                "id": "1",
                "available": True,
            },
            {
                "id": "2",
                "available": False,
            },
            {
                "id": "3",
                "available": True,
            },
        ]
    }

    result = strategy.get_targets(
        state
    )

    assert result == [
        {
            "id": "1",
            "available": True,
        },
        {
            "id": "3",
            "available": True,
        },
    ]


def test_get_targets_returns_empty_list_when_no_providers(
    strategy,
):
    state = {
        "providers": []
    }

    result = strategy.get_targets(
        state
    )

    assert result == []


def test_get_targets_ignores_provider_without_available_flag(
    strategy,
):
    state = {
        "providers": [
            {
                "id": "1",
            },
            {
                "id": "2",
                "available": True,
            },
        ]
    }

    result = strategy.get_targets(
        state
    )

    assert result == [
        {
            "id": "2",
            "available": True,
        }
    ]


# ============================================================
# _get_credit_balance()
# ============================================================


def test_get_credit_balance_returns_credit_value(
    strategy,
):
    page = MagicMock()

    page.locator.return_value.inner_text.return_value = (
        "Current Credit Balance 123"
    )

    result = strategy._get_credit_balance(
        page
    )

    assert result == 123


def test_get_credit_balance_is_case_insensitive(
    strategy,
):
    page = MagicMock()

    page.locator.return_value.inner_text.return_value = (
        "current credit balance 456"
    )

    result = strategy._get_credit_balance(
        page
    )

    assert result == 456


def test_get_credit_balance_returns_zero_when_missing(
    strategy,
):
    page = MagicMock()

    page.locator.return_value.inner_text.return_value = (
        "Some unrelated page content"
    )

    result = strategy._get_credit_balance(
        page
    )

    assert result == 0


def test_get_credit_balance_returns_zero_on_error(
    strategy,
):
    page = MagicMock()

    page.locator.side_effect = Exception(
        "Browser error"
    )

    result = strategy._get_credit_balance(
        page
    )

    assert result == 0


# ============================================================
# _get_cooldown()
# ============================================================


def test_get_cooldown_returns_text(
    strategy,
):
    banner = MagicMock()

    row = MagicMock()
    strong = MagicMock()

    banner.locator.return_value.filter.return_value.first = row

    row.count.return_value = 1

    row.locator.return_value.first = strong

    strong.count.return_value = 1
    strong.inner_text.return_value = "11 hour(s)"

    result = strategy._get_cooldown(
        banner
    )

    assert result == "11 hour(s)"


def test_get_cooldown_returns_none_when_row_missing(
    strategy,
):
    banner = MagicMock()

    row = MagicMock()

    banner.locator.return_value.filter.return_value.first = row

    row.count.return_value = 0

    result = strategy._get_cooldown(
        banner
    )

    assert result is None


def test_get_cooldown_returns_none_when_strong_missing(
    strategy,
):
    banner = MagicMock()

    row = MagicMock()
    strong = MagicMock()

    banner.locator.return_value.filter.return_value.first = row

    row.count.return_value = 1

    row.locator.return_value.first = strong

    strong.count.return_value = 0

    result = strategy._get_cooldown(
        banner
    )

    assert result is None


def test_get_cooldown_returns_none_on_error(
    strategy,
):
    banner = MagicMock()

    banner.locator.side_effect = Exception(
        "Browser error"
    )

    result = strategy._get_cooldown(
        banner
    )

    assert result is None


# ============================================================
# _get_vote_providers()
# ============================================================


def test_get_vote_providers_finds_available_provider(
    strategy,
):
    with patch.object(
        VotingStrategy,
        "_get_cooldown",
        return_value=None,
    ):
        page = MagicMock()

        banners = MagicMock()

        page.locator.return_value = banners

        banners.count.return_value = 1

        banner = MagicMock()

        banners.nth.return_value = banner

        banner.get_attribute.return_value = (
            "banner_5"
        )

        link = MagicMock()

        link.count.return_value = 1

        link.get_attribute.side_effect = [
            "https://example.com/vote",
            None,
        ]

        banner.locator.return_value.first = link

        result = strategy._get_vote_providers(
            page
        )

        assert result == [
            {
                "id": "5",
                "available": True,
                "cooldown": None,
                "href": "https://example.com/vote",
            }
        ]


def test_get_vote_providers_finds_provider_without_link(
    strategy,
):
    with patch.object(
        VotingStrategy,
        "_get_cooldown",
        return_value=None,
    ):
        page = MagicMock()

        banners = MagicMock()

        page.locator.return_value = banners

        banners.count.return_value = 1

        banner = MagicMock()

        banners.nth.return_value = banner

        banner.get_attribute.return_value = (
            "banner_8"
        )

        link = MagicMock()

        link.count.return_value = 0

        banner.locator.return_value.first = link

        result = strategy._get_vote_providers(
            page
        )

        assert result == [
            {
                "id": "8",
                "available": False,
                "cooldown": None,
                "href": None,
            }
        ]


def test_get_vote_providers_detects_disabled_link(
    strategy,
):
    with patch.object(
        VotingStrategy,
        "_get_cooldown",
        return_value=None,
    ):
        page = MagicMock()

        banners = MagicMock()

        page.locator.return_value = banners

        banners.count.return_value = 1

        banner = MagicMock()

        banners.nth.return_value = banner

        banner.get_attribute.return_value = (
            "banner_10"
        )

        link = MagicMock()

        link.count.return_value = 1

        link.get_attribute.side_effect = [
            "https://example.com/vote",
            "disabled",
        ]

        banner.locator.return_value.first = link

        result = strategy._get_vote_providers(
            page
        )

        assert result == [
            {
                "id": "10",
                "available": False,
                "cooldown": None,
                "href": "https://example.com/vote",
            }
        ]


def test_get_vote_providers_ignores_invalid_banner_id(
    strategy,
):
    page = MagicMock()

    banners = MagicMock()

    page.locator.return_value = banners

    banners.count.return_value = 1

    banner = MagicMock()

    banners.nth.return_value = banner

    banner.get_attribute.return_value = (
        "something_else"
    )

    result = strategy._get_vote_providers(
        page
    )

    assert result == []


def test_get_vote_providers_returns_empty_when_no_banners(
    strategy,
):
    page = MagicMock()

    banners = MagicMock()

    page.locator.return_value = banners

    banners.count.return_value = 0

    result = strategy._get_vote_providers(
        page
    )

    assert result == []


# ============================================================
# execute()
# ============================================================


def test_execute_requires_started_automation(
    strategy,
):
    automation = MagicMock()

    automation.page = None
    automation.context = None

    target = {
        "id": "5"
    }

    with pytest.raises(
        RuntimeError,
        match="Web automation has not been started",
    ):
        strategy.execute(
            automation,
            target,
        )


def test_execute_requires_target_id(
    strategy,
):
    automation = MagicMock()

    automation.page = MagicMock()
    automation.context = MagicMock()

    with pytest.raises(
        ValueError,
        match="missing 'id'",
    ):
        strategy.execute(
            automation,
            {},
        )


def test_execute_returns_false_when_link_not_found(
    strategy,
):
    automation = MagicMock()

    page = MagicMock()
    context = MagicMock()

    automation.page = page
    automation.context = context

    link = MagicMock()

    link.count.return_value = 0

    page.locator.return_value.first = link

    result = strategy.execute(
        automation,
        {
            "id": "5"
        },
    )

    assert result is False


def test_execute_returns_false_when_link_not_visible(
    strategy,
):
    automation = MagicMock()

    page = MagicMock()
    context = MagicMock()

    automation.page = page
    automation.context = context

    link = MagicMock()

    link.count.return_value = 1
    link.is_visible.return_value = False

    page.locator.return_value.first = link

    result = strategy.execute(
        automation,
        {
            "id": "5"
        },
    )

    assert result is False


def test_execute_returns_false_when_link_has_no_href(
    strategy,
):
    automation = MagicMock()

    page = MagicMock()
    context = MagicMock()

    automation.page = page
    automation.context = context

    link = MagicMock()

    link.count.return_value = 1
    link.is_visible.return_value = True
    link.get_attribute.return_value = None

    page.locator.return_value.first = link

    result = strategy.execute(
        automation,
        {
            "id": "5"
        },
    )

    assert result is False


# ============================================================
# execute() - successful vote
# ============================================================


def test_execute_returns_true_when_credit_balance_increases(
    strategy,
):
    automation = MagicMock()

    page = MagicMock()
    context = MagicMock()

    automation.page = page
    automation.context = context

    link = MagicMock()

    link.count.return_value = 1
    link.is_visible.return_value = True
    link.get_attribute.return_value = (
        "https://example.com/vote"
    )

    page.locator.return_value.first = link

    strategy._get_credit_balance = MagicMock(
        side_effect=[
            100,
            101,
        ]
    )

    popup = MagicMock()

    context.expect_page.return_value.__enter__.return_value.value = (
        popup
    )

    result = strategy.execute(
        automation,
        {
            "id": "5"
        },
    )

    assert result is True

    link.click.assert_called_once()

    popup.close.assert_called_once()

    page.bring_to_front.assert_called_once()

    page.reload.assert_called_once_with(
        wait_until="domcontentloaded",
    )


def test_execute_returns_false_when_credit_balance_does_not_increase(
    strategy,
):
    automation = MagicMock()

    page = MagicMock()
    context = MagicMock()

    automation.page = page
    automation.context = context

    link = MagicMock()

    link.count.return_value = 1
    link.is_visible.return_value = True
    link.get_attribute.return_value = (
        "https://example.com/vote"
    )

    page.locator.return_value.first = link

    strategy._get_credit_balance = MagicMock(
        side_effect=[
            100,
            100,
        ]
    )

    popup = MagicMock()

    context.expect_page.return_value.__enter__.return_value.value = (
        popup
    )

    result = strategy.execute(
        automation,
        {
            "id": "5"
        },
    )

    assert result is False

    link.click.assert_called_once()

    popup.close.assert_called_once()

    page.bring_to_front.assert_called_once()

    page.reload.assert_called_once_with(
        wait_until="domcontentloaded",
    )


def test_execute_returns_false_when_credit_balance_decreases(
    strategy,
):
    automation = MagicMock()

    page = MagicMock()
    context = MagicMock()

    automation.page = page
    automation.context = context

    link = MagicMock()

    link.count.return_value = 1
    link.is_visible.return_value = True
    link.get_attribute.return_value = (
        "https://example.com/vote"
    )

    page.locator.return_value.first = link

    strategy._get_credit_balance = MagicMock(
        side_effect=[
            100,
            99,
        ]
    )

    popup = MagicMock()

    context.expect_page.return_value.__enter__.return_value.value = (
        popup
    )

    result = strategy.execute(
        automation,
        {
            "id": "5"
        },
    )

    assert result is False

    link.click.assert_called_once()

    popup.close.assert_called_once()

    page.bring_to_front.assert_called_once()

    page.reload.assert_called_once_with(
        wait_until="domcontentloaded",
    )


# ============================================================
# execute() - popup failure
# ============================================================


def test_execute_returns_false_when_popup_fails_to_open(
    strategy,
):
    automation = MagicMock()

    page = MagicMock()
    context = MagicMock()

    automation.page = page
    automation.context = context

    link = MagicMock()

    link.count.return_value = 1
    link.is_visible.return_value = True
    link.get_attribute.return_value = (
        "https://example.com/vote"
    )

    page.locator.return_value.first = link

    strategy._get_credit_balance = MagicMock(
        return_value=100
    )

    context.expect_page.side_effect = Exception(
        "Popup failed"
    )

    result = strategy.execute(
        automation,
        {
            "id": "5"
        },
    )

    assert result is False

    link.click.assert_not_called()


# ============================================================
# execute() - reload failure
# ============================================================


def test_execute_returns_false_when_reload_fails(
    strategy,
):
    automation = MagicMock()

    page = MagicMock()
    context = MagicMock()

    automation.page = page
    automation.context = context

    link = MagicMock()

    link.count.return_value = 1
    link.is_visible.return_value = True
    link.get_attribute.return_value = (
        "https://example.com/vote"
    )

    page.locator.return_value.first = link

    strategy._get_credit_balance = MagicMock(
        side_effect=[
            100,
        ]
    )

    popup = MagicMock()

    context.expect_page.return_value.__enter__.return_value.value = (
        popup
    )

    page.reload.side_effect = Exception(
        "Reload failed"
    )

    result = strategy.execute(
        automation,
        {
            "id": "5"
        },
    )

    assert result is False

    popup.close.assert_called_once()

    page.bring_to_front.assert_called_once()