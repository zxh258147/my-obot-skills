"""STDIO smoke test for the weather MCP server."""

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
        args=["-m", "weather_mcp.server"],
        cwd=str(ROOT),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = {tool.name for tool in (await session.list_tools()).tools}
            expected = {"get_weather", "get_forecast", "list_cities"}
            missing = expected - tools
            if missing:
                print("FAIL missing tools:", ", ".join(sorted(missing)))
                return 1
            listed = await session.call_tool("list_cities", {})
            cities = json.loads(listed.content[0].text)
            print("cities:", cities)
            weather = await session.call_tool("get_weather", {"city": "北京"})
            payload = json.loads(weather.content[0].text)
            print("beijing:", payload)
            if not payload.get("ok"):
                print("FAIL get_weather")
                return 1
            print("PASS  weather MCP STDIO tools work")
            return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
