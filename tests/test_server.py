"""Offline check that the server registers exactly the four documented tools with input schemas."""
import asyncio
from smhi_mcp.server import mcp


def test_tools_registered():
    tools = asyncio.run(mcp.list_tools())
    names = sorted(t.name for t in tools)
    assert names == ["find_nearest_station", "get_forecast", "get_observation", "get_warnings"]
    for t in tools:
        assert t.input_schema["type"] == "object" and t.description
