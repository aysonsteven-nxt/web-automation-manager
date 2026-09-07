from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from automation.core import security as security_module
from automation.core.events import event_manager
from automation.core.manager import automation_manager
from automation.core.security import (
    require_api_token,
    require_automation_access,
    require_role,
    write_audit_event,
)
from automation.core.state import load_state

AUDIT_LOG_PATH = security_module.AUDIT_LOG_PATH


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
def automation_list(
    context: dict[str, Any] = Depends(
        require_role(
            "viewer",
            "operator",
            "admin",
            "service",
        )
    ),
):
    write_audit_event(
        "automation",
        principal=context["principal"],
        action="list_automations",
        status="success",
    )

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
    context: dict[str, Any] = Depends(require_api_token),
):
    require_automation_access(automation_id, context)
    write_audit_event(
        "automation",
        principal=context["principal"],
        action="status.read",
        automation_id=automation_id,
        status="success",
    )

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
    context: dict[str, Any] = Depends(require_api_token),
):
    require_automation_access(automation_id, context)
    write_audit_event(
        "automation",
        principal=context["principal"],
        action="pids.read",
        automation_id=automation_id,
        status="success",
    )

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
    context: dict[str, Any] = Depends(require_role("operator", "admin")),
):
    require_automation_access(automation_id, context)

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

        write_audit_event(
            "automation",
            principal=context["principal"],
            action="automation.start",
            automation_id=automation_id,
            status="success" if started else "failed",
            details={"started": started},
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
    context: dict[str, Any] = Depends(require_role("operator", "admin")),
):
    require_automation_access(automation_id, context)

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

        write_audit_event(
            "automation",
            principal=context["principal"],
            action="automation.stop",
            automation_id=automation_id,
            status="success" if stopped else "failed",
            details={"stopped": stopped},
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
    context: dict[str, Any] = Depends(require_role("operator", "admin")),
):
    require_automation_access(automation_id, context)

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

        write_audit_event(
            "automation",
            principal=context["principal"],
            action="automation.stop_all",
            automation_id=automation_id,
            status="success",
            details={"stopped": len(stopped_pids)},
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
    context: dict[str, Any] = Depends(require_api_token),
):
    require_automation_access(automation_id, context)

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

        write_audit_event(
            "automation",
            principal=context["principal"],
            action="state.read",
            automation_id=automation_id,
            status="success",
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
    context: dict[str, Any] = Depends(
        require_role(
            "service",
        )
    ),
):

    await event_manager.broadcast(
        "automation_state",
        state,
    )

    write_audit_event(
        "automation",
        principal=context["principal"],
        action="state.publish",
        automation_id=state.get("automationId"),
        status="success",
    )

    return {
        "received": True
    }


@app.get("/api/events")
async def events(
    context: dict[str, Any] = Depends(
        require_role(
            "viewer",
            "operator",
            "admin",
            "service",
        )
    ),
):
    write_audit_event(
        "automation",
        principal=context["principal"],
        action="event.stream.connect",
        status="success",
    )

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
async def test_event(
    context: dict[str, Any] = Depends(
        require_role(
            "operator",
            "admin",
        )
    ),
):
    write_audit_event(
        "automation",
        principal=context["principal"],
        action="event.test.send",
        status="success",
    )

    await event_manager.broadcast(
        "test",
        {
            "message": "SSE is working!"
        },
    )

    return {
        "sent": True
    }