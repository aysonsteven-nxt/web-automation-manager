import json
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import Depends, Header, HTTPException

VALID_API_ROLES = {
    "admin",
    "operator",
    "viewer",
    "service",
}

AUDIT_LOG_PATH = (
    Path(__file__).resolve().parents[2]
    / "logs"
    / "security_audit.log"
)


def write_audit_event(
    category: str,
    *,
    principal: str,
    action: str,
    status: str,
    automation_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    try:
        from api import AUDIT_LOG_PATH as api_audit_log_path
    except Exception:
        api_audit_log_path = None

    target_log_path = (
        Path(api_audit_log_path)
        if api_audit_log_path is not None
        else AUDIT_LOG_PATH
    )
    target_log_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "category": category,
        "principal": principal,
        "action": action,
        "status": status,
        "automationId": automation_id,
        "details": details or {},
    }

    with target_log_path.open(
        "a",
        encoding="utf-8",
    ) as log_file:
        log_file.write(
            json.dumps(payload, sort_keys=True)
            + "\n"
        )


def _parse_expiration(value: Any) -> datetime | None:
    if value is None or value == "":
        return None

    if isinstance(value, str):
        try:
            return datetime.fromisoformat(
                value.replace("Z", "+00:00")
            ).astimezone(timezone.utc)
        except ValueError:
            return None

    if isinstance(value, datetime):
        return value.astimezone(timezone.utc)

    return None


def _load_token_metadata() -> dict[str, dict[str, Any]]:
    token_map: dict[str, dict[str, Any]] = {}

    configured_token = os.getenv("AUTOMATION_API_TOKEN", "").strip()
    if configured_token:
        token_map[configured_token] = {
            "token": configured_token,
            "role": "admin",
            "principal": "local-service",
            "scopes": [],
            "expires_at": None,
            "revoked": False,
        }

    tokens_json = os.getenv("AUTOMATION_API_TOKENS", "")
    if not tokens_json.strip():
        return token_map

    try:
        entries = json.loads(tokens_json)
    except json.JSONDecodeError:
        return token_map

    if isinstance(entries, dict):
        for token_value, entry in entries.items():
            if not isinstance(entry, dict):
                continue

            token_key = str(token_value).strip()
            if not token_key:
                continue

            token_map[token_key] = {
                "token": token_key,
                "role": str(entry.get("role", "admin")).strip().lower(),
                "principal": str(entry.get("principal", "default")).strip(),
                "scopes": [
                    str(item).strip()
                    for item in entry.get("scopes", [])
                    if str(item).strip()
                ],
                "expires_at": _parse_expiration(entry.get("expires_at")),
                "revoked": bool(entry.get("revoked", False)),
            }
        return token_map

    if not isinstance(entries, list):
        return token_map

    for entry in entries:
        if not isinstance(entry, dict):
            continue

        token_value = str(entry.get("token", "")).strip()
        if not token_value:
            continue

        token_map[token_value] = {
            "token": token_value,
            "role": str(entry.get("role", "admin")).strip().lower(),
            "principal": str(entry.get("principal", "default")).strip(),
            "scopes": [
                str(item).strip()
                for item in entry.get("scopes", [])
                if str(item).strip()
            ],
            "expires_at": _parse_expiration(entry.get("expires_at")),
            "revoked": bool(entry.get("revoked", False)),
        }

    return token_map


def require_api_token(
    api_token: str | None = Header(
        default=None,
        alias="X-API-Token",
    ),
    api_role: str | None = Header(
        default=None,
        alias="X-API-Role",
    ),
    api_principal: str | None = Header(
        default=None,
        alias="X-API-Principal",
    ),
    api_scopes: str | None = Header(
        default=None,
        alias="X-API-Scopes",
    ),
) -> dict[str, Any]:
    if api_token is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API token.",
            headers={
                "WWW-Authenticate": "API token",
            },
        )

    token_map = _load_token_metadata()
    if not token_map:
        raise HTTPException(
            status_code=503,
            detail="API authentication is not configured.",
        )

    token_entry = token_map.get(api_token)
    if token_entry is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API token.",
            headers={
                "WWW-Authenticate": "API token",
            },
        )

    if token_entry.get("revoked"):
        raise HTTPException(
            status_code=401,
            detail="API token has been revoked.",
        )

    expires_at = token_entry.get("expires_at")
    if expires_at is not None and datetime.now(timezone.utc) >= expires_at:
        raise HTTPException(
            status_code=401,
            detail="API token has expired.",
        )

    role_name = (api_role or token_entry.get("role") or "admin").strip().lower()
    if role_name not in VALID_API_ROLES:
        raise HTTPException(
            status_code=401,
            detail="Invalid API role.",
        )

    principal_name = (api_principal or token_entry.get("principal") or "default").strip()
    token_scopes = list(token_entry.get("scopes") or [])
    scope_values: list[str] = []

    if api_scopes:
        scope_values = [
            item.strip()
            for item in api_scopes.split(",")
            if item.strip()
        ]
    else:
        scope_values = token_scopes

    return {
        "role": role_name,
        "principal": principal_name,
        "scopes": scope_values,
    }


def require_role(*allowed_roles: str):
    allowed = {role.lower() for role in allowed_roles}

    def dependency(
        context: dict[str, Any] = Depends(require_api_token),
    ) -> dict[str, Any]:
        role = context["role"]

        if role.lower() not in allowed:
            write_audit_event(
                "authorization",
                principal=context["principal"],
                action="resource_access",
                status="denied",
                details={
                    "required_roles": sorted(allowed),
                    "reason": "missing_role",
                },
            )
            raise HTTPException(
                status_code=403,
                detail="Insufficient privileges.",
            )

        return context

    return dependency


def require_automation_access(
    automation_id: str,
    context: dict[str, Any],
) -> dict[str, Any]:
    role = context["role"]
    scopes = set(context["scopes"])

    if role in {"admin", "service"}:
        return context

    required_scope = f"automation:{automation_id}"
    if required_scope not in scopes:
        write_audit_event(
            "authorization",
            principal=context["principal"],
            action="automation_access",
            status="denied",
            automation_id=automation_id,
            details={
                "role": role,
                "required_scope": required_scope,
                "scopes": sorted(scopes),
            },
        )
        raise HTTPException(
            status_code=403,
            detail="Insufficient privileges for this automation.",
        )

    return context
