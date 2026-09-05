from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from automation.core.events import event_manager
from automation.core.manager import automation_manager
from automation.core.state import load_state


app = FastAPI(
    title="Automation Manager API",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/hello")
def hello():
    return {
        "message": "Automation API is working!"
    }


@app.get("/api/automations")
def automation_list():

    result = []

    for process in automation_manager.list():

        status = process.status()

        result.append(
            {
                "id": process.config.id,
                "name": process.config.name,
                "type": process.config.type,
                "strategy": process.config.strategy,
                "url": process.config.config.get("url"),
                "enabled": process.config.enabled,
                "status": status,
            }
        )

    return result


@app.get(
    "/api/automations/{automation_id}/status"
)
def automation_status(
    automation_id: str,
):

    try:
        return automation_manager.status(
            automation_id
        )

    except (KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


@app.get(
    "/api/automations/{automation_id}/pids"
)
def automation_pids(
    automation_id: str,
):

    try:

        pids = automation_manager.pids(
            automation_id
        )

        return {
            "automationId": automation_id,
            "count": len(pids),
            "pids": pids,
        }

    except (KeyError, ValueError) as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


@app.post(
    "/api/automations/{automation_id}/start"
)
async def start_automation(
    automation_id: str,
):

    try:

        started = automation_manager.start(
            automation_id
        )

        status = automation_manager.status(
            automation_id
        )

        if started:
            await event_manager.broadcast(
                "automation_status",
                status,
            )

        return {
            "started": started,
            **status,
        }

    except (KeyError, ValueError) as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@app.post(
    "/api/automations/{automation_id}/stop"
)
async def stop_automation(
    automation_id: str,
):

    try:

        stopped = automation_manager.stop(
            automation_id
        )

        status = automation_manager.status(
            automation_id
        )

        if stopped:
            await event_manager.broadcast(
                "automation_status",
                status,
            )

        return {
            "stopped": stopped,
            **status,
        }

    except (KeyError, ValueError) as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@app.post(
    "/api/automations/{automation_id}/stop-all"
)
async def stop_all_automation_workers(
    automation_id: str,
):

    try:

        stopped_pids = (
            automation_manager.stop_all(
                automation_id
            )
        )

        status = automation_manager.status(
            automation_id
        )

        await event_manager.broadcast(
            "automation_status",
            status,
        )

        return {
            "automationId": automation_id,
            "stopped": len(stopped_pids),
            "pids": stopped_pids,
            **status,
        }

    except (KeyError, ValueError) as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@app.get(
    "/api/automations/{automation_id}/state"
)
def automation_state(
    automation_id: str,
):

    try:

        process = automation_manager.get(
            automation_id
        )

        if not process.status().get(
            "running",
            False,
        ):
            raise HTTPException(
                status_code=409,
                detail="Worker is not active.",
            )

        state_file = (
            Path(__file__).resolve().parent
            / process.config.state_file
        )

        state = load_state(
            state_file
        )

        if state is None:

            raise HTTPException(
                status_code=404,
                detail=(
                    "No automation state "
                    "available yet."
                ),
            )

        return state

    except (KeyError, ValueError) as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


@app.post(
    "/api/internal/automation/state"
)
async def automation_state_update(
    state: dict[str, Any],
):

    await event_manager.broadcast(
        "automation_state",
        state,
    )

    return {
        "received": True
    }


@app.get("/api/events")
async def events():

    queue = await event_manager.connect()

    async def event_generator():

        try:

            while True:

                event = await queue.get()

                yield event

        finally:

            event_manager.disconnect(
                queue
            )

    return EventSourceResponse(
        event_generator()
    )


@app.post("/api/events/test")
async def test_event():

    await event_manager.broadcast(
        "test",
        {
            "message": "SSE is working!"
        },
    )

    return {
        "sent": True
    }