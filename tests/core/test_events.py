import asyncio

import pytest

from automation.core.events import EventManager


@pytest.fixture
def event_manager():
    return EventManager()


# ============================================================
# connect()
# ============================================================


@pytest.mark.anyio
async def test_connect_returns_queue(
    event_manager,
):
    queue = await event_manager.connect()

    assert isinstance(
        queue,
        asyncio.Queue,
    )


@pytest.mark.anyio
async def test_connect_registers_queue(
    event_manager,
):
    queue = await event_manager.connect()

    assert queue in event_manager._queues


@pytest.mark.anyio
async def test_multiple_clients_can_connect(
    event_manager,
):
    queue_one = await event_manager.connect()
    queue_two = await event_manager.connect()

    assert queue_one in event_manager._queues
    assert queue_two in event_manager._queues
    assert len(event_manager._queues) == 2


# ============================================================
# broadcast()
# ============================================================


@pytest.mark.anyio
async def test_broadcast_sends_event_to_subscriber(
    event_manager,
):
    queue = await event_manager.connect()

    await event_manager.broadcast(
        "test_event",
        {
            "message": "hello",
        },
    )

    event = await queue.get()

    assert event == {
        "event": "test_event",
        "data": {
            "message": "hello",
        },
    }


@pytest.mark.anyio
async def test_broadcast_sends_event_to_all_subscribers(
    event_manager,
):
    queue_one = await event_manager.connect()
    queue_two = await event_manager.connect()

    await event_manager.broadcast(
        "automation_state",
        {
            "automationId": "test-automation",
            "credits": 10,
        },
    )

    event_one = await queue_one.get()
    event_two = await queue_two.get()

    expected = {
        "event": "automation_state",
        "data": {
            "automationId": "test-automation",
            "credits": 10,
        },
    }

    assert event_one == expected
    assert event_two == expected


@pytest.mark.anyio
async def test_broadcast_preserves_data(
    event_manager,
):
    queue = await event_manager.connect()

    data = {
        "automationId": "forsaken-ro",
        "availableCount": 3,
        "providers": [
            {
                "id": "1",
                "available": True,
            }
        ],
    }

    await event_manager.broadcast(
        "state_updated",
        data,
    )

    event = await queue.get()

    assert event["event"] == "state_updated"
    assert event["data"] == data


@pytest.mark.anyio
async def test_multiple_events_are_received_in_order(
    event_manager,
):
    queue = await event_manager.connect()

    await event_manager.broadcast(
        "event_one",
        {
            "value": 1,
        },
    )

    await event_manager.broadcast(
        "event_two",
        {
            "value": 2,
        },
    )

    await event_manager.broadcast(
        "event_three",
        {
            "value": 3,
        },
    )

    assert await queue.get() == {
        "event": "event_one",
        "data": {
            "value": 1,
        },
    }

    assert await queue.get() == {
        "event": "event_two",
        "data": {
            "value": 2,
        },
    }

    assert await queue.get() == {
        "event": "event_three",
        "data": {
            "value": 3,
        },
    }


@pytest.mark.anyio
async def test_broadcast_with_no_subscribers_does_not_fail(
    event_manager,
):
    await event_manager.broadcast(
        "test_event",
        {
            "message": "hello",
        },
    )

    assert len(event_manager._queues) == 0


# ============================================================
# disconnect()
# ============================================================


@pytest.mark.anyio
async def test_disconnect_removes_subscriber(
    event_manager,
):
    queue = await event_manager.connect()

    assert queue in event_manager._queues

    event_manager.disconnect(
        queue
    )

    assert queue not in event_manager._queues


@pytest.mark.anyio
async def test_disconnected_subscriber_does_not_receive_future_events(
    event_manager,
):
    queue = await event_manager.connect()

    event_manager.disconnect(
        queue
    )

    await event_manager.broadcast(
        "test_event",
        {
            "message": "hello",
        },
    )

    assert queue.empty()


@pytest.mark.anyio
async def test_disconnect_does_not_affect_other_subscribers(
    event_manager,
):
    queue_one = await event_manager.connect()
    queue_two = await event_manager.connect()

    event_manager.disconnect(
        queue_one
    )

    await event_manager.broadcast(
        "test_event",
        {
            "message": "hello",
        },
    )

    assert queue_one.empty()

    event = await queue_two.get()

    assert event == {
        "event": "test_event",
        "data": {
            "message": "hello",
        },
    }


@pytest.mark.anyio
async def test_disconnect_unknown_queue_is_safe(
    event_manager,
):
    queue = asyncio.Queue()

    event_manager.disconnect(
        queue
    )

    assert len(event_manager._queues) == 0