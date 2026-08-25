"""STDIO MCP server wrapping the id-vision cardVerify API.

Credentials and endpoint come from environment variables. Do not hardcode secrets.
Obot UVX only supports STDIO — do not start HTTP/SSE here.
"""

from __future__ import annotations

import os
import uuid
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("card-verify-mcp")

ENDPOINT_PATH = "/id-vision/v1/cardVerify"

ENV_BASE_URL = "CARD_VERIFY_BASE_URL"
ENV_APP_ID = "CARD_VERIFY_APP_ID"
ENV_API_KEY = "CARD_VERIFY_API_KEY"
ENV_TIMEOUT = "CARD_VERIFY_TIMEOUT_SECONDS"


def _read_config() -> tuple[dict[str, str] | None, dict[str, Any] | None]:
    base_url = os.environ.get(ENV_BASE_URL, "").strip().rstrip("/")
    app_id = os.environ.get(ENV_APP_ID, "").strip()
    api_key = os.environ.get(ENV_API_KEY, "").strip()
    missing = [
        name
        for name, value in (
            (ENV_BASE_URL, base_url),
            (ENV_APP_ID, app_id),
            (ENV_API_KEY, api_key),
        )
        if not value
    ]
    if missing:
        return None, {
            "ok": False,
            "error": "missing_config",
            "missing": missing,
            "hint": "Set these environment variables in Obot catalog Configuration.",
        }
    return {"base_url": base_url, "app_id": app_id, "api_key": api_key}, None


def _timeout_seconds() -> float:
    raw = os.environ.get(ENV_TIMEOUT, "60").strip() or "60"
    try:
        timeout = float(raw)
    except ValueError:
        return 60.0
    return timeout if timeout > 0 else 60.0


def _build_image_infos(
    image_url: str | None,
    sub_category: str,
    image_infos: list[dict[str, str]] | None,
) -> tuple[list[dict[str, str]] | None, dict[str, Any] | None]:
    if image_infos:
        normalized: list[dict[str, str]] = []
        for index, item in enumerate(image_infos):
            url = (item.get("imageUrl") or item.get("image_url") or "").strip()
            category = (
                item.get("subCategory") or item.get("sub_category") or ""
            ).strip()
            if not url or not category:
                return None, {
                    "ok": False,
                    "error": "invalid_image_infos",
                    "message": (
                        f"image_infos[{index}] needs subCategory and imageUrl."
                    ),
                }
            normalized.append({"subCategory": category, "imageUrl": url})
        return normalized, None

    if image_url and image_url.strip():
        return (
            [
                {
                    "subCategory": sub_category.strip() or "FRONT",
                    "imageUrl": image_url.strip(),
                }
            ],
            None,
        )

    return None, {
        "ok": False,
        "error": "missing_image",
        "message": "Provide image_url or image_infos.",
    }


@mcp.tool()
def check_card_verify_config() -> dict[str, Any]:
    """Check whether card verify environment variables are set. Does not print secrets."""
    configured = {
        ENV_BASE_URL: bool(os.environ.get(ENV_BASE_URL, "").strip()),
        ENV_APP_ID: bool(os.environ.get(ENV_APP_ID, "").strip()),
        ENV_API_KEY: bool(os.environ.get(ENV_API_KEY, "").strip()),
    }
    return {
        "ok": all(configured.values()),
        "configured": configured,
        "timeout_seconds": _timeout_seconds(),
    }


@mcp.tool()
def card_verify(
    category: str = "VEHICLE_LICENSE",
    image_url: str | None = None,
    sub_category: str = "FRONT",
    image_infos: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Verify a document image via the id-vision cardVerify API (e.g. vehicle license).

    Credentials are read from CARD_VERIFY_BASE_URL, CARD_VERIFY_APP_ID, and
    CARD_VERIFY_API_KEY. Pass either a single image_url or a full image_infos list.

    Args:
        category: Document category, for example VEHICLE_LICENSE.
        image_url: Image URL for the simple single-image case.
        sub_category: Image side when using image_url. Usually FRONT or BACK.
        image_infos: Full list, each item with subCategory and imageUrl.
    """
    config, config_error = _read_config()
    if config_error:
        return config_error

    infos, infos_error = _build_image_infos(image_url, sub_category, image_infos)
    if infos_error:
        return infos_error

    assert config is not None
    url = f"{config['base_url']}{ENDPOINT_PATH}"
    headers = {
        "Content-Type": "application/json",
        "X-Trace-Id": uuid.uuid4().hex,
        "X-App-Id": config["app_id"],
        "X-Api-Key": config["api_key"],
    }
    payload = {"category": category.strip() or "VEHICLE_LICENSE", "imageInfos": infos}

    try:
        response = httpx.post(
            url,
            json=payload,
            headers=headers,
            timeout=_timeout_seconds(),
        )
    except httpx.TimeoutException:
        return {"ok": False, "error": "timeout", "timeout_seconds": _timeout_seconds()}
    except httpx.RequestError as exc:
        return {"ok": False, "error": "request_failed", "message": str(exc)}

    result: dict[str, Any] = {
        "ok": response.is_success,
        "status_code": response.status_code,
        "trace_id": headers["X-Trace-Id"],
    }
    try:
        result["data"] = response.json()
    except ValueError:
        result["data"] = response.text
    return result


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
