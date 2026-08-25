"""Test the MCP server over STDIO. Does not need Obot or localhost:8080.

Usage:
    .venv\\Scripts\\python.exe test_mcp_stdio.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parent


async def main() -> int:
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "card_verify_mcp.server"],
        cwd=str(ROOT),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            print("initialize:", init.serverInfo.name)

            listed = await session.list_tools()
            names = [tool.name for tool in listed.tools]
            print("tools:", ", ".join(names))
            expected = {"card_verify", "check_card_verify_config"}
            missing = expected - set(names)
            if missing:
                print("FAIL missing tools:", ", ".join(sorted(missing)))
                return 1

            result = await session.call_tool("check_card_verify_config", {})
            payload = result.content[0].text if result.content else ""
            print("check_card_verify_config:", payload)
            data = json.loads(payload)
            if "configured" not in data:
                print("FAIL unexpected config payload")
                return 1

            print("PASS  STDIO MCP handshake and tools work")
            if data.get("ok"):
                print("INFO  CARD_VERIFY_* env is set in this process")
            else:
                print("INFO  CARD_VERIFY_* not set; protocol still OK")
            return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
