"""Live smoke test: start the server over stdio and call all four tools against SMHI."""
import asyncio, json, sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main() -> int:
    params = StdioServerParameters(command=sys.executable, args=["-m", "smhi_mcp.server"])
    async with stdio_client(params) as (r, w), ClientSession(r, w) as s:
        await s.initialize()
        tools = sorted(t.name for t in (await s.list_tools()).tools)
        print("tools:", tools)
        ok = tools == ["find_nearest_station", "get_forecast", "get_observation", "get_warnings"]
        st = None
        for name, args in [("get_forecast", {"lat": 59.33, "lon": 18.06, "hours": 2}), ("get_warnings", {"lang": "en"}),
                           ("find_nearest_station", {"lat": 59.33, "lon": 18.06}), ("get_observation", None)]:
            if name == "get_observation": args = {"station_id": st}
            res = await s.call_tool(name, args)
            data = res.structured_content or json.loads(res.content[0].text)
            if name == "find_nearest_station": st = data.get("id")
            good = not res.is_error and "error" not in data
            ok &= good
            print(("OK  " if good else "FAIL"), name, json.dumps(data, ensure_ascii=False)[:200])
    return 0 if ok else 1

sys.exit(asyncio.run(main()))
