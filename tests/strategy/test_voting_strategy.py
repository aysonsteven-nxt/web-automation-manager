from unittest.mock import MagicMock

import pytest

from automation.types.web.strategies.config import (
    VotingStrategyConfig,
)
from automation.types.web.strategies.voting_strategy import (
    VotingStrategy,
)


@pytest.fixture
def strategy():
    return VotingStrategy(
        VotingStrategyConfig(
            action_delay_seconds=3,
        )
    )


@pytest.fixture
def automation():
    automation = MagicMock()

    automation.web_config.url = (
        "https://example.com/vote"
    )

    return automation


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
            automation,
        )


def test_initialize_navigates_to_configured_url(
    strategy,
    automation,
):
    page = MagicMock()
    automation.page = page

    strategy.initialize(
        automation,
    )

    page.goto.assert_called_once_with(
        "https://example.com/vote",
        wait_until="domcontentloaded",
    )


def test_strategy_config_returns_configured_values(
    strategy,
):
    assert (
        strategy.strategy_config.action_delay_seconds
        == 3
    )


def test_check_reads_credit_balance(
    strategy,
    automation,
):
    page = MagicMock()
    automation.page = page

    body = MagicMock()
    body.inner_text.return_value = (
        "Current Credit Balance 125"
    )

    banners = MagicMock()
    banners.count.return_value = 0

    def locator(selector):
        if selector == "body":
            return body

        if selector == '[id^="banner_"]':
            return banners

        raise AssertionError(
            f"Unexpected selector: {selector}"
        )

    page.locator.side_effect = locator

    state = strategy.check(
        automation,
    )

    assert state["credits"] == 125


def test_check_returns_provider_information(
    strategy,
    automation,
):
    page = MagicMock()
    automation.page = page

    body = MagicMock()
    body.inner_text.return_value = (
        "Current Credit Balance 125"
    )

    banners = MagicMock()
    banners.count.return_value = 0

    def locator(selector):
        if selector == "body":
            return body

        if selector == '[id^="banner_"]':
            return banners

        raise AssertionError(
            f"Unexpected selector: {selector}"
        )

    page.locator.side_effect = locator

    state = strategy.check(
        automation,
    )

    assert state == {
        "credits": 125,
        "totalCount": 0,
        "availableCount": 0,
        "providers": [],
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
            automation,
        )


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

    targets = strategy.get_targets(
        state,
    )

    assert targets == [
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
    assert strategy.get_targets({}) == []


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

    targets = strategy.get_targets(
        state,
    )

    assert targets == [
        {
            "id": "2",
            "available": True,
        }
    ]


def test_get_credit_balance_returns_credit_value():
    page = MagicMock()

    page.locator.return_value.inner_text.return_value = (
        "Current Credit Balance 250"
    )

    result = VotingStrategy._get_credit_balance(
        page,
    )

    assert result == 250


def test_get_credit_balance_is_case_insensitive():
    page = MagicMock()

    page.locator.return_value.inner_text.return_value = (
        "CURRENT CREDIT BALANCE 350"
    )

    result = VotingStrategy._get_credit_balance(
        page,
    )

    assert result == 350


def test_get_credit_balance_returns_zero_when_missing():
    page = MagicMock()

    page.locator.return_value.inner_text.return_value = (
        "No credit information available"
    )

    result = VotingStrategy._get_credit_balance(
        page,
    )

    assert result == 0


def test_get_credit_balance_returns_zero_on_error():
    page = MagicMock()

    page.locator.side_effect = Exception(
        "page error"
    )

    result = VotingStrategy._get_credit_balance(
        page,
    )

    assert result == 0


def test_get_cooldown_returns_text():
    banner = MagicMock()

    tr_locator = MagicMock()
    filtered_locator = MagicMock()

    row = MagicMock()
    row.count.return_value = 1

    strong_locator = MagicMock()
    strong = MagicMock()

    strong.count.return_value = 1
    strong.inner_text.return_value = "11 hour(s)"

    strong_locator.first = strong
    row.locator.return_value = strong_locator

    filtered_locator.first = row
    tr_locator.filter.return_value = filtered_locator
    banner.locator.return_value = tr_locator

    result = VotingStrategy._get_cooldown(
        banner,
    )

    assert result == "11 hour(s)"


def test_get_cooldown_returns_none_when_row_missing():
    banner = MagicMock()

    tr_locator = MagicMock()
    filtered_locator = MagicMock()

    row = MagicMock()
    row.count.return_value = 0

    filtered_locator.first = row
    tr_locator.filter.return_value = filtered_locator
    banner.locator.return_value = tr_locator

    result = VotingStrategy._get_cooldown(
        banner,
    )

    assert result is None


def test_get_cooldown_returns_none_when_strong_missing():
    banner = MagicMock()

    tr_locator = MagicMock()
    filtered_locator = MagicMock()

    row = MagicMock()
    row.count.return_value = 1

    strong_locator = MagicMock()
    strong = MagicMock()
    strong.count.return_value = 0

    strong_locator.first = strong
    row.locator.return_value = strong_locator

    filtered_locator.first = row
    tr_locator.filter.return_value = filtered_locator
    banner.locator.return_value = tr_locator

    result = VotingStrategy._get_cooldown(
        banner,
    )

    assert result is None


def test_get_cooldown_returns_none_on_error():
    banner = MagicMock()

    banner.locator.side_effect = Exception(
        "locator error"
    )

    result = VotingStrategy._get_cooldown(
        banner,
    )

    assert result is None


def test_get_vote_providers_finds_available_provider():
    page = MagicMock()

    banners = MagicMock()
    banners.count.return_value = 1

    banner = MagicMock()
    banner.get_attribute.return_value = (
        "banner_123"
    )

    link_locator = MagicMock()
    link = MagicMock()

    link.count.return_value = 1
    link.get_attribute.side_effect = [
        "https://vote.example.com",
        None,
    ]

    link_locator.first = link

    tr_locator = MagicMock()
    filtered_locator = MagicMock()

    row = MagicMock()
    row.count.return_value = 0

    filtered_locator.first = row
    tr_locator.filter.return_value = filtered_locator

    def banner_locator(selector):
        if selector == "a":
            return link_locator

        if selector == "tr":
            return tr_locator

        raise AssertionError(
            f"Unexpected banner selector: {selector}"
        )

    banner.locator.side_effect = banner_locator

    banners.nth.return_value = banner

    page.locator.return_value = banners

    result = VotingStrategy._get_vote_providers(
        page,
    )

    assert result == [
        {
            "id": "123",
            "available": True,
            "cooldown": None,
            "href": "https://vote.example.com",
        }
    ]


def test_get_vote_providers_finds_provider_without_link():
    page = MagicMock()

    banners = MagicMock()
    banners.count.return_value = 1

    banner = MagicMock()
    banner.get_attribute.return_value = (
        "banner_123"
    )

    link_locator = MagicMock()
    link = MagicMock()

    link.count.return_value = 0
    link_locator.first = link

    tr_locator = MagicMock()
    filtered_locator = MagicMock()

    row = MagicMock()
    row.count.return_value = 0

    filtered_locator.first = row
    tr_locator.filter.return_value = filtered_locator

    def banner_locator(selector):
        if selector == "a":
            return link_locator

        if selector == "tr":
            return tr_locator

        raise AssertionError(
            f"Unexpected banner selector: {selector}"
        )

    banner.locator.side_effect = banner_locator

    banners.nth.return_value = banner

    page.locator.return_value = banners

    result = VotingStrategy._get_vote_providers(
        page,
    )

    assert result == [
        {
            "id": "123",
            "available": False,
            "cooldown": None,
            "href": None,
        }
    ]


def test_get_vote_providers_detects_disabled_link():
    page = MagicMock()

    banners = MagicMock()
    banners.count.return_value = 1

    banner = MagicMock()
    banner.get_attribute.return_value = (
        "banner_123"
    )

    link_locator = MagicMock()
    link = MagicMock()

    link.count.return_value = 1
    link.get_attribute.side_effect = [
        "https://vote.example.com",
        "disabled",
    ]

    link_locator.first = link

    tr_locator = MagicMock()
    filtered_locator = MagicMock()

    row = MagicMock()
    row.count.return_value = 0

    filtered_locator.first = row
    tr_locator.filter.return_value = filtered_locator

    def banner_locator(selector):
        if selector == "a":
            return link_locator

        if selector == "tr":
            return tr_locator

        raise AssertionError(
            f"Unexpected banner selector: {selector}"
        )

    banner.locator.side_effect = banner_locator

    banners.nth.return_value = banner

    page.locator.return_value = banners

    result = VotingStrategy._get_vote_providers(
        page,
    )

    assert result == [
        {
            "id": "123",
            "available": False,
            "cooldown": None,
            "href": "https://vote.example.com",
        }
    ]


def test_get_vote_providers_ignores_invalid_banner_id():
    page = MagicMock()

    banners = MagicMock()
    banners.count.return_value = 2

    valid_banner = MagicMock()
    valid_banner.get_attribute.return_value = (
        "banner_123"
    )

    valid_link_locator = MagicMock()
    valid_link = MagicMock()

    valid_link.count.return_value = 1
    valid_link.get_attribute.side_effect = [
        "https://vote.example.com",
        None,
    ]

    valid_link_locator.first = valid_link

    valid_tr_locator = MagicMock()
    valid_filtered_locator = MagicMock()

    valid_row = MagicMock()
    valid_row.count.return_value = 0

    valid_filtered_locator.first = valid_row
    valid_tr_locator.filter.return_value = (
        valid_filtered_locator
    )

    def valid_banner_locator(selector):
        if selector == "a":
            return valid_link_locator

        if selector == "tr":
            return valid_tr_locator

        raise AssertionError(
            f"Unexpected banner selector: {selector}"
        )

    valid_banner.locator.side_effect = (
        valid_banner_locator
    )

    invalid_banner = MagicMock()
    invalid_banner.get_attribute.return_value = (
        "something_else"
    )

    banners.nth.side_effect = [
        valid_banner,
        invalid_banner,
    ]

    page.locator.return_value = banners

    result = VotingStrategy._get_vote_providers(
        page,
    )

    assert len(result) == 1
    assert result[0]["id"] == "123"


def test_get_vote_providers_returns_empty_when_no_banners():
    page = MagicMock()

    banners = MagicMock()
    banners.count.return_value = 0

    page.locator.return_value = banners

    result = VotingStrategy._get_vote_providers(
        page,
    )

    assert result == []


def test_execute_requires_started_automation(
    strategy,
):
    automation = MagicMock()
    automation.page = None
    automation.context = None

    with pytest.raises(
        RuntimeError,
        match="Web automation has not been started",
    ):
        strategy.execute(
            automation,
            {"id": "123"},
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
        {"id": "123"},
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
        {"id": "123"},
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
        {"id": "123"},
    )

    assert result is False


def test_execute_returns_true_when_credit_balance_increases(
    strategy,
):
    automation = MagicMock()

    page = MagicMock()
    context = MagicMock()
    popup = MagicMock()

    automation.page = page
    automation.context = context

    link = MagicMock()
    link.count.return_value = 1
    link.is_visible.return_value = True

    link.get_attribute.return_value = (
        "https://vote.example.com"
    )

    page.locator.return_value.first = link

    credit_values = iter(
        [
            100,
            101,
        ]
    )

    page.locator.return_value.inner_text.side_effect = (
        lambda: (
            "Current Credit Balance "
            f"{next(credit_values)}"
        )
    )

    context.expect_page.return_value.__enter__.return_value.value = (
        popup
    )

    result = strategy.execute(
        automation,
        {"id": "123"},
    )

    assert result is True

    link.click.assert_called_once()
    popup.close.assert_called_once()

    page.reload.assert_called_once_with(
        wait_until="domcontentloaded",
    )


def test_execute_returns_false_when_credit_balance_does_not_increase(
    strategy,
):
    automation = MagicMock()

    page = MagicMock()
    context = MagicMock()
    popup = MagicMock()

    automation.page = page
    automation.context = context

    link = MagicMock()
    link.count.return_value = 1
    link.is_visible.return_value = True
    link.get_attribute.return_value = (
        "https://vote.example.com"
    )

    page.locator.return_value.first = link

    credit_values = iter(
        [
            100,
            100,
        ]
    )

    page.locator.return_value.inner_text.side_effect = (
        lambda: (
            "Current Credit Balance "
            f"{next(credit_values)}"
        )
    )

    context.expect_page.return_value.__enter__.return_value.value = (
        popup
    )

    result = strategy.execute(
        automation,
        {"id": "123"},
    )

    assert result is False


def test_execute_returns_false_when_credit_balance_decreases(
    strategy,
):
    automation = MagicMock()

    page = MagicMock()
    context = MagicMock()
    popup = MagicMock()

    automation.page = page
    automation.context = context

    link = MagicMock()
    link.count.return_value = 1
    link.is_visible.return_value = True
    link.get_attribute.return_value = (
        "https://vote.example.com"
    )

    page.locator.return_value.first = link

    credit_values = iter(
        [
            100,
            90,
        ]
    )

    page.locator.return_value.inner_text.side_effect = (
        lambda: (
            "Current Credit Balance "
            f"{next(credit_values)}"
        )
    )

    context.expect_page.return_value.__enter__.return_value.value = (
        popup
    )

    result = strategy.execute(
        automation,
        {"id": "123"},
    )

    assert result is False


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
        "https://vote.example.com"
    )

    page.locator.return_value.first = link

    context.expect_page.side_effect = Exception(
        "popup failed"
    )

    result = strategy.execute(
        automation,
        {"id": "123"},
    )

    assert result is False


def test_execute_returns_false_when_reload_fails(
    strategy,
):
    automation = MagicMock()

    page = MagicMock()
    context = MagicMock()
    popup = MagicMock()

    automation.page = page
    automation.context = context

    link = MagicMock()
    link.count.return_value = 1
    link.is_visible.return_value = True
    link.get_attribute.return_value = (
        "https://vote.example.com"
    )

    page.locator.return_value.first = link

    page.reload.side_effect = Exception(
        "reload failed"
    )

    context.expect_page.return_value.__enter__.return_value.value = (
        popup
    )

    result = strategy.execute(
        automation,
        {"id": "123"},
    )

    assert result is False

    popup.close.assert_called_once()