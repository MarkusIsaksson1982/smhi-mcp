# smhi-mcp

An [MCP](https://modelcontextprotocol.io) server for Swedish weather data from **SMHI** (the Swedish Meteorological and Hydrological Institute). It lets an AI assistant fetch point forecasts, active weather warnings and live station observations for Sweden and the wider Nordic area.

- No API key and no account needed: it uses SMHI's public open-data APIs.
- Small: about 150 lines of Python. The SMHI client uses only the standard library, and the server needs only the official `mcp` SDK.
- Returns structured JSON and passes Swedish/English text through as published by SMHI.

## Tools

| Tool | Arguments | Returns |
|---|---|---|
| `get_forecast` | `lat`, `lon` (WGS84; lat 52–72, lon 2–35), `hours` (default 24) | Hourly rows: `time` (UTC), `temperature_c`, `wind_ms`, `gust_ms`, `precip_mm`, `humidity_pct`, `symbol_code` |
| `get_warnings` | `area` (optional, case-insensitive substring such as `"Skåne"`), `lang` (`"sv"` or `"en"`) | Active warnings, one row per warning area: `event`, `level`, `area_names`, `start`, `end`, `description` |
| `find_nearest_station` | `lat`, `lon`, `parameter` (default 1 = air temperature) | Nearest active station: `id`, `name`, `latitude`, `longitude`, `distance_km` |
| `get_observation` | `station_id`, `parameter` (default 1) | Latest-hour value: `station`, `parameter`, `unit`, `time` (UTC), `value` |

Errors such as out-of-range coordinates, unknown stations or network failures come back as `{"error": "..."}` instead of crashing the session.

Example question: *"Is it going to rain in Uppsala this afternoon, and are there any warnings for Uppsala län?"* The assistant calls `get_forecast(59.86, 17.64)` and `get_warnings(area="Uppsala")`.

`symbol_code` is SMHI's weather symbol (1 = clear sky … 27 = heavy snowfall). Parameter ids for `find_nearest_station` and `get_observation` follow SMHI's metobs API. For example, 1 is air temperature, 4 is wind speed, 6 is relative humidity and 7 is precipitation.

## Install and run

Requires Python 3.10 or newer.

```bash
git clone https://github.com/MarkusIsaksson1982/smhi-mcp.git
cd smhi-mcp
python -m venv .venv && . .venv/bin/activate
pip install -e .
smhi-mcp            # speaks MCP over stdio
```

MCP client configuration (Claude Desktop, Cursor and others):

```json
{
  "mcpServers": {
    "smhi": { "command": "smhi-mcp" }
  }
}
```

If `smhi-mcp` is not on your PATH, use the full path to the virtualenv's `bin/smhi-mcp`, or `"command": "python", "args": ["-m", "smhi_mcp.server"]`.

The server is also listed on [Smithery](https://smithery.ai/server/markusisaksson/smhi-mcp).

## Development

```bash
pip install -e '.[dev]'
pytest                          # offline tests (recorded SMHI responses, no network)
python scripts/smoke_live.py    # live smoke test: starts the server and calls all four tools against SMHI
```

## Data source and attribution

All weather data comes from **SMHI open data** ([opendata.smhi.se](https://opendata.smhi.se/)) and is licensed under [Creative Commons Attribution 4.0 (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/). If you display or redistribute the data, attribute it to **SMHI**. Each tool response includes `"source": "SMHI"` where practical.

This is an independent project. It is not affiliated with or endorsed by SMHI. Forecasts and warnings are provided as is, so for safety-critical decisions use SMHI's official channels ([smhi.se](https://www.smhi.se/)).

## License

The code is MIT licensed (see [LICENSE](LICENSE)). The SMHI data it returns is CC BY 4.0, as described above.
