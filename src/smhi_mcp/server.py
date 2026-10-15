"""smhi-mcp: MCP server exposing SMHI open data (forecasts, warnings, observations)."""
from __future__ import annotations

import urllib.error
from typing import Any

from mcp.server.mcpserver import MCPServer

from smhi_mcp import __version__, smhi_core

mcp = MCPServer(
    "smhi-mcp",
    version=__version__,
    instructions="Swedish weather data from SMHI open data (CC BY 4.0, source: SMHI). Coordinates are WGS84 decimal degrees.",
    website_url="https://github.com/MarkusIsaksson1982/smhi-mcp",
)


def _safe(fn, *args) -> dict[str, Any]:
    try:
        return fn(*args)
    except (ValueError, LookupError, urllib.error.URLError) as e:
        return {"error": str(e)}


@mcp.tool()
def get_forecast(lat: float, lon: float, hours: int = 24) -> dict[str, Any]:
    """Hourly SMHI weather forecast for a point (lat 52-72, lon 2-35): temperature, wind, gusts, precipitation, humidity, symbol code."""
    return _safe(lambda: {"lat": lat, "lon": lon, "forecast": smhi_core.forecast(lat, lon, hours), "source": "SMHI"})


@mcp.tool()
def get_warnings(area: str | None = None, lang: str = "sv") -> dict[str, Any]:
    """Active SMHI weather warnings. Optional area filter (substring, e.g. 'Skåne'); lang 'sv' or 'en'."""
    return _safe(lambda: {"warnings": smhi_core.warnings(area, lang), "source": "SMHI"})


@mcp.tool()
def find_nearest_station(lat: float, lon: float, parameter: int = 1) -> dict[str, Any]:
    """Nearest active SMHI observation station for a point. parameter: SMHI metobs parameter id (1 = air temperature)."""
    return _safe(smhi_core.nearest_station, lat, lon, parameter)


@mcp.tool()
def get_observation(station_id: int, parameter: int = 1) -> dict[str, Any]:
    """Latest-hour observed value at an SMHI station (parameter 1 = air temperature in °C)."""
    return _safe(smhi_core.observation, station_id, parameter)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
