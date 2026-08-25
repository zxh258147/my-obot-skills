"""Verify package imports and card_verify behavior using the local .venv.

Usage:
    .venv\\Scripts\\python.exe verify.py
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any
from unittest.mock import patch

FAILED = 0
PASSED = 0


def ok(message: str) -> None:
    global PASSED
    PASSED += 1
    print(f"PASS  {message}")


def fail(message: str) -> None:
    global FAILED
    FAILED += 1
    print(f"FAIL  {message}")


def check(condition: bool, message: str) -> None:
    if condition:
        ok(message)
    else:
        fail(message)


def test_imports() -> None:
    import httpx
    import mcp
    from mcp.server.fastmcp import FastMCP

    from card_verify_mcp import server

    check(hasattr(httpx, "post"), "httpx imported")
    check(mcp.__name__ == "mcp", "mcp imported")
    check(isinstance(server.mcp, FastMCP), "FastMCP instance created")
    check(callable(server.card_verify), "card_verify importable")
    check(callable(server.check_card_verify_config), "check_card_verify_config importable")
    check(
        os.path.basename(sys.prefix) in {".venv", "venv"}
        or ".venv" in sys.prefix.replace("\\", "/"),
        f"running inside venv ({sys.prefix})",
    )


def test_helpers() -> None:
    from card_verify_mcp.server import (
        ENV_API_KEY,
        ENV_APP_ID,
        ENV_BASE_URL,
        _build_image_infos,
        _read_config,
        check_card_verify_config,
    )

    saved = {
        ENV_BASE_URL: os.environ.get(ENV_BASE_URL),
        ENV_APP_ID: os.environ.get(ENV_APP_ID),
        ENV_API_KEY: os.environ.get(ENV_API_KEY),
    }
    try:
        for key in saved:
            os.environ.pop(key, None)

        config, error = _read_config()
        check(config is None, "missing env returns no config")
        check(error is not None and error.get("error") == "missing_config", "missing_config error")
        check(
            error is not None
            and set(error.get("missing", [])) == {ENV_BASE_URL, ENV_APP_ID, ENV_API_KEY},
            "all three env vars reported missing",
        )

        status = check_card_verify_config()
        check(status["ok"] is False, "check_card_verify_config ok=False without env")
        check(status["configured"][ENV_API_KEY] is False, "API key is not reported as set")
        check(
            all(isinstance(flag, bool) for flag in status["configured"].values()),
            "config check reports booleans, not secret values",
        )

        os.environ[ENV_BASE_URL] = "https://example.test/"
        os.environ[ENV_APP_ID] = "demo-app"
        os.environ[ENV_API_KEY] = "demo-key"
        config, error = _read_config()
        check(error is None and config is not None, "config loads when env is set")
        check(config["base_url"] == "https://example.test", "trailing slash stripped")
        check(config["api_key"] == "demo-key", "api key read from env")
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    infos, error = _build_image_infos(None, "FRONT", None)
    check(infos is None and error is not None and error["error"] == "missing_image", "image required")

    infos, error = _build_image_infos("https://img.example/a.jpg", "FRONT", None)
    check(
        error is None and infos == [{"subCategory": "FRONT", "imageUrl": "https://img.example/a.jpg"}],
        "single image_url normalized",
    )

    infos, error = _build_image_infos(
        None,
        "FRONT",
        [{"sub_category": "BACK", "image_url": "https://img.example/b.jpg"}],
    )
    check(
        error is None and infos == [{"subCategory": "BACK", "imageUrl": "https://img.example/b.jpg"}],
        "image_infos snake_case accepted",
    )


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict[str, Any]) -> None:
        self.status_code = status_code
        self._payload = payload
        self.is_success = 200 <= status_code < 300
        self.text = json.dumps(payload)

    def json(self) -> dict[str, Any]:
        return self._payload


def test_mocked_http() -> None:
    from card_verify_mcp.server import ENV_API_KEY, ENV_APP_ID, ENV_BASE_URL, card_verify

    saved = {
        ENV_BASE_URL: os.environ.get(ENV_BASE_URL),
        ENV_APP_ID: os.environ.get(ENV_APP_ID),
        ENV_API_KEY: os.environ.get(ENV_API_KEY),
    }
    os.environ[ENV_BASE_URL] = "https://example.test"
    os.environ[ENV_APP_ID] = "demo-app"
    os.environ[ENV_API_KEY] = "demo-key"
    captured: dict[str, Any] = {}

    def fake_post(url: str, json: dict[str, Any], headers: dict[str, str], timeout: float) -> _FakeResponse:
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        captured["timeout"] = timeout
        return _FakeResponse(200, {"code": 0, "message": "mocked"})

    try:
        with patch("card_verify_mcp.server.httpx.post", side_effect=fake_post):
            result = card_verify(
                category="VEHICLE_LICENSE",
                image_url="https://img.example/front.jpg",
                sub_category="FRONT",
            )
        check(result["ok"] is True, "mocked card_verify ok")
        check(result["status_code"] == 200, "mocked status_code 200")
        check(captured["url"] == "https://example.test/id-vision/v1/cardVerify", "POST path is cardVerify")
        check(captured["headers"]["X-App-Id"] == "demo-app", "X-App-Id comes from env")
        check(captured["headers"]["X-Api-Key"] == "demo-key", "X-Api-Key comes from env")
        check(captured["headers"]["Content-Type"] == "application/json", "JSON content type")
        check(bool(captured["headers"].get("X-Trace-Id")), "X-Trace-Id generated")
        check(
            captured["json"]["category"] == "VEHICLE_LICENSE"
            and captured["json"]["imageInfos"][0]["subCategory"] == "FRONT",
            "request body matches tool args",
        )
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def test_live_api() -> None:
    from card_verify_mcp.server import ENV_API_KEY, ENV_APP_ID, ENV_BASE_URL, card_verify

    needed = [ENV_BASE_URL, ENV_APP_ID, ENV_API_KEY]
    if any(not os.environ.get(name, "").strip() for name in needed):
        print("SKIP  live API (set CARD_VERIFY_BASE_URL / CARD_VERIFY_APP_ID / CARD_VERIFY_API_KEY)")
        return

    image_url = os.environ.get("CARD_VERIFY_TEST_IMAGE_URL", "").strip()
    if not image_url:
        print("SKIP  live API (set CARD_VERIFY_TEST_IMAGE_URL)")
        return

    result = card_verify(
        category=os.environ.get("CARD_VERIFY_TEST_CATEGORY", "VEHICLE_LICENSE"),
        image_url=image_url,
        sub_category=os.environ.get("CARD_VERIFY_TEST_SUB_CATEGORY", "FRONT"),
    )
    check("status_code" in result or result.get("error") in {"timeout", "request_failed"}, "live call returned")
    if result.get("ok"):
        ok(f"live API HTTP {result.get('status_code')}")
    else:
        fail(
            "live API not successful: "
            f"status={result.get('status_code')} error={result.get('error')}"
        )
    # Never print headers, keys, or signed image URLs.
    data = result.get("data")
    if isinstance(data, dict):
        summary = {k: data[k] for k in list(data)[:6]}
        print("INFO  live response keys:", ", ".join(data.keys()))
        print("INFO  live response excerpt:", json.dumps(summary, ensure_ascii=False, default=str)[:500])


def main() -> int:
    print(f"python={sys.executable}")
    test_imports()
    test_helpers()
    test_mocked_http()
    test_live_api()
    print(f"\n{PASSED} passed, {FAILED} failed")
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
