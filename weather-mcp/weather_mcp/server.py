"""STDIO weather MCP server for Obot UVX hosting.

Returns hardcoded demo weather data. No API key required.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("weather-mcp")

WEATHER = {
    "beijing": {
        "city": "Beijing",
        "condition": "Sunny",
        "temperature_c": 25,
        "humidity": 40,
        "wind": "NE 8 km/h",
        "forecast": [
            {"day": "today", "condition": "Sunny", "high_c": 26, "low_c": 16},
            {"day": "tomorrow", "condition": "Partly cloudy", "high_c": 24, "low_c": 15},
            {"day": "day_after", "condition": "Light rain", "high_c": 21, "low_c": 14},
        ],
    },
    "shanghai": {
        "city": "Shanghai",
        "condition": "Rainy",
        "temperature_c": 22,
        "humidity": 78,
        "wind": "E 12 km/h",
        "forecast": [
            {"day": "today", "condition": "Rainy", "high_c": 23, "low_c": 18},
            {"day": "tomorrow", "condition": "Overcast", "high_c": 24, "low_c": 19},
            {"day": "day_after", "condition": "Sunny", "high_c": 27, "low_c": 20},
        ],
    },
    "guangzhou": {
        "city": "Guangzhou",
        "condition": "Cloudy",
        "temperature_c": 29,
        "humidity": 70,
        "wind": "S 10 km/h",
        "forecast": [
            {"day": "today", "condition": "Cloudy", "high_c": 31, "low_c": 25},
            {"day": "tomorrow", "condition": "Thunderstorm", "high_c": 30, "low_c": 24},
            {"day": "day_after", "condition": "Cloudy", "high_c": 32, "low_c": 25},
        ],
    },
    "shenzhen": {
        "city": "Shenzhen",
        "condition": "Humid",
        "temperature_c": 28,
        "humidity": 82,
        "wind": "SE 9 km/h",
        "forecast": [
            {"day": "today", "condition": "Humid", "high_c": 30, "low_c": 25},
            {"day": "tomorrow", "condition": "Showers", "high_c": 29, "low_c": 24},
            {"day": "day_after", "condition": "Sunny", "high_c": 31, "low_c": 25},
        ],
    },
    "new york": {
        "city": "New York",
        "condition": "Cloudy",
        "temperature_c": 18,
        "humidity": 55,
        "wind": "W 15 km/h",
        "forecast": [
            {"day": "today", "condition": "Cloudy", "high_c": 19, "low_c": 12},
            {"day": "tomorrow", "condition": "Sunny", "high_c": 21, "low_c": 11},
            {"day": "day_after", "condition": "Windy", "high_c": 17, "low_c": 9},
        ],
    },
}

ALIASES = {
    "北京": "beijing",
    "上海": "shanghai",
    "广州": "guangzhou",
    "深圳": "shenzhen",
    "纽约": "new york",
    "newyork": "new york",
    "ny": "new york",
}


def _resolve_city(city: str) -> str | None:
    key = city.strip().lower()
    key = ALIASES.get(city.strip(), ALIASES.get(key, key))
    return key if key in WEATHER else None


@mcp.tool()
def list_cities() -> list[str]:
    """List cities that have demo weather data."""
    return [item["city"] for item in WEATHER.values()]


@mcp.tool()
def get_weather(city: str) -> dict:
    """Get current weather for a city. Data is hardcoded demo data.

    Args:
        city: City name, for example Beijing, Shanghai, Guangzhou, Shenzhen, New York.
              Chinese names 北京 / 上海 / 广州 / 深圳 / 纽约 are also accepted.
    """
    resolved = _resolve_city(city)
    if resolved is None:
        return {
            "ok": False,
            "error": "unknown_city",
            "city": city,
            "supported": [item["city"] for item in WEATHER.values()],
        }
    data = WEATHER[resolved]
    return {
        "ok": True,
        "city": data["city"],
        "condition": data["condition"],
        "temperature_c": data["temperature_c"],
        "humidity": data["humidity"],
        "wind": data["wind"],
    }


@mcp.tool()
def get_forecast(city: str) -> dict:
    """Get a 3-day forecast for a city. Data is hardcoded demo data.

    Args:
        city: City name, same as get_weather.
    """
    resolved = _resolve_city(city)
    if resolved is None:
        return {
            "ok": False,
            "error": "unknown_city",
            "city": city,
            "supported": [item["city"] for item in WEATHER.values()],
        }
    data = WEATHER[resolved]
    return {"ok": True, "city": data["city"], "forecast": data["forecast"]}


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
