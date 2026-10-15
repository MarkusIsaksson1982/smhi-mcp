"""Thin, dependency-free client for SMHI open data (forecasts, warnings, observations). No API key needed.

Every public function accepts ``fetch``: a callable ``fetch(url) -> parsed JSON``. It defaults to a urllib GET,
and tests inject a fake.
"""
from __future__ import annotations

import datetime as _dt
import json
import math
import urllib.request
from typing import Any, Callable

Fetch = Callable[[str], Any]
USER_AGENT = "smhi-mcp/0.1 (+https://github.com/MarkusIsaksson1982/smhi-mcp)"
FORECAST_URL = "https://opendata-download-metfcst.smhi.se/api/category/snow1g/version/1/geotype/point/lon/{lon}/lat/{lat}/data.json"
WARNINGS_URL = "https://opendata-download-warnings.smhi.se/ibww/api/version/1/warning.json"
METOBS_URL = "https://opendata-download-metobs.smhi.se/api/version/1.0/parameter/{parameter}"


def _fetch(url: str) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.load(resp)


def _num(x: float) -> str:
    return f"{round(float(x), 4):.4f}".rstrip("0").rstrip(".")


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p = math.pi / 180
    h = math.sin((lat2 - lat1) * p / 2) ** 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2
    return 12742 * math.asin(math.sqrt(h))


def forecast(lat: float, lon: float, hours: int = 24, fetch: Fetch | None = None) -> list[dict]:
    """Hourly point forecast (SMHI snow1g model). Coverage is roughly the Nordic region."""
    if not (52 <= lat <= 72 and 2 <= lon <= 35):
        raise ValueError("lat/lon outside SMHI forecast coverage (lat 52-72, lon 2-35)")
    data = (fetch or _fetch)(FORECAST_URL.format(lon=_num(lon), lat=_num(lat)))
    rows = []
    for t in data.get("timeSeries", [])[: max(0, int(hours))]:
        d = t.get("data", {})
        rows.append({
            "time": t.get("time"),
            "temperature_c": d.get("air_temperature"),
            "wind_ms": d.get("wind_speed"),
            "gust_ms": d.get("wind_speed_of_gust"),
            "precip_mm": d.get("precipitation_amount_mean"),
            "humidity_pct": d.get("relative_humidity"),
            "symbol_code": d.get("symbol_code"),
        })
    return rows


def warnings(area: str | None = None, lang: str = "sv", fetch: Fetch | None = None) -> list[dict]:
    """Active SMHI impact-based weather warnings, one row per warning area. ``area`` is a case-insensitive substring."""
    out = []
    for w in (fetch or _fetch)(WARNINGS_URL):
        event = w.get("event", {})
        for a in w.get("warningAreas", []):
            names = [x.get(lang) or x.get("sv") for x in a.get("affectedAreas", [])]
            names.append((a.get("areaName") or {}).get("sv"))
            names = [n for n in names if n]
            descs = a.get("descriptions") or []
            text = descs[0].get("text", {}) if descs else {}
            row = {
                "id": a.get("id"),
                "event": event.get(lang) or event.get("sv"),
                "level": (a.get("warningLevel") or {}).get(lang) or (a.get("warningLevel") or {}).get("sv"),
                "area_names": names,
                "start": a.get("approximateStart"),
                "end": a.get("approximateEnd"),
                "description": text.get(lang) or text.get("sv") or "",
            }
            if area is None or area.lower() in " ".join(names).lower():
                out.append(row)
    return out


def nearest_station(lat: float, lon: float, parameter: int = 1, active_only: bool = True, fetch: Fetch | None = None) -> dict:
    """Nearest SMHI observation station measuring ``parameter`` (1 = air temperature)."""
    data = (fetch or _fetch)(METOBS_URL.format(parameter=int(parameter)) + ".json")
    stations = [s for s in data.get("station", []) if s.get("active") or not active_only]
    if not stations:
        raise LookupError(f"no stations for parameter {parameter}")
    best = min(stations, key=lambda s: _haversine_km(lat, lon, s["latitude"], s["longitude"]))
    return {"id": best["id"], "name": best["name"], "latitude": best["latitude"], "longitude": best["longitude"],
            "distance_km": round(_haversine_km(lat, lon, best["latitude"], best["longitude"]), 2)}


def observation(station_id: int, parameter: int = 1, fetch: Fetch | None = None) -> dict:
    """Latest-hour observation for a station and parameter."""
    url = METOBS_URL.format(parameter=int(parameter)) + f"/station/{int(station_id)}/period/latest-hour/data.json"
    data = (fetch or _fetch)(url)
    values = data.get("value") or []
    if not values:
        raise LookupError(f"no recent values for station {station_id}, parameter {parameter}")
    last = values[-1]
    ts = _dt.datetime.fromtimestamp(last["date"] / 1000, _dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {"station": data["station"]["name"], "parameter": data["parameter"]["name"],
            "unit": data["parameter"]["unit"], "time": ts, "value": float(last["value"])}
