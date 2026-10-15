"""Hidden acceptance tests for smhi_core.py (offline: a fake fetch(url) is injected)."""
import pytest
from smhi_mcp import smhi_core as sc
from tests.fixtures_embedded import FIX

def router(url):
    if "metfcst" in url: return FIX["forecast"]
    if "warning" in url: return FIX["warnings"]
    if "/station/" in url and "data.json" in url: return FIX["obs"]
    if "metobs" in url: return FIX["stations"]
    raise AssertionError("unexpected url " + url)

def test_forecast_url_uses_snow1g_and_lon_lat_order():
    seen = []
    sc.forecast(59.33, 18.06, hours=3, fetch=lambda u: (seen.append(u), router(u))[1])
    assert "snow1g" in seen[0] and "/lon/18.06/lat/59.33/" in seen[0]

def test_forecast_rows():
    rows = sc.forecast(59.33, 18.06, hours=3, fetch=router)
    assert len(rows) == 3
    r = rows[0]
    for k in ("time", "temperature_c", "wind_ms", "gust_ms", "precip_mm", "symbol_code"):
        assert k in r
    assert r["temperature_c"] == FIX["forecast"]["timeSeries"][0]["data"]["air_temperature"]

def test_forecast_rejects_outside_nordics():
    with pytest.raises(ValueError):
        sc.forecast(10.0, 18.0, fetch=router)

def test_warnings_flatten_and_filter():
    all_ = sc.warnings(fetch=router)
    assert all_ and all(isinstance(x["area_names"], list) for x in all_)
    for k in ("id", "event", "level", "area_names", "start", "description"):
        assert k in all_[0]
    name = all_[0]["area_names"][0]
    assert all(name.lower() in " ".join(x["area_names"]).lower() for x in sc.warnings(area=name[:4], fetch=router))
    assert sc.warnings(area="Nowhereland", fetch=router) == []

def test_warnings_english():
    w = sc.warnings(lang="en", fetch=router)
    assert w[0]["level"] == FIX["warnings"][0]["warningAreas"][0]["warningLevel"]["en"]

def test_nearest_station_active():
    s = sc.nearest_station(59.34, 18.05, fetch=router)
    assert s["id"] == 98230 and s["distance_km"] < 5

def test_observation():
    o = sc.observation(98230, fetch=router)
    assert o["value"] == pytest.approx(float(FIX["obs"]["value"][-1]["value"]))
    assert o["unit"] == "celsius" and o["station"].startswith("Stockholm") and o["time"].endswith("Z")
