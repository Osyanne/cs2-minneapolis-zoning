"""Tests del registro de ciudades (cities.json) y manifest per-city."""
import sys, os, json
import pytest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from shared.registry import (
    load_cities, get_city, CityNotFoundError, RegistryError,
)


def _valid_entry():
    return {
        "display_name": "Test City",
        "country": "USA",
        "bbox": [44.86, -93.38, 45.05, -93.17],
        "center": [44.97, -93.27],
        "zoom": 12,
        "tagline": "test",
        "locale": "es",
    }


def test_load_cities_reads_valid_json(tmp_path):
    p = tmp_path / "cities.json"
    p.write_text(json.dumps({"minneapolis": _valid_entry()}))
    cities = load_cities(p)
    assert "minneapolis" in cities
    assert cities["minneapolis"]["bbox"] == [44.86, -93.38, 45.05, -93.17]


def test_load_cities_missing_file_raises(tmp_path):
    with pytest.raises(RegistryError, match="no existe"):
        load_cities(tmp_path / "missing.json")


def test_load_cities_malformed_json_raises(tmp_path):
    p = tmp_path / "cities.json"
    p.write_text("not json {")
    with pytest.raises(RegistryError, match="JSON"):
        load_cities(p)


def test_load_cities_missing_required_field_raises(tmp_path):
    p = tmp_path / "cities.json"
    broken = {"display_name": "X"}  # missing bbox, center, etc.
    p.write_text(json.dumps({"broken": broken}))
    with pytest.raises(RegistryError, match="bbox"):
        load_cities(p)


def test_load_cities_invalid_bbox_shape_raises(tmp_path):
    p = tmp_path / "cities.json"
    e = _valid_entry()
    e["bbox"] = [44.86, -93.38, 45.05]  # 3 floats instead of 4
    p.write_text(json.dumps({"broken": e}))
    with pytest.raises(RegistryError, match="4 floats"):
        load_cities(p)


def test_load_cities_inverted_bbox_raises(tmp_path):
    p = tmp_path / "cities.json"
    e = _valid_entry()
    e["bbox"] = [45.05, -93.17, 44.86, -93.38]  # south > north
    p.write_text(json.dumps({"broken": e}))
    with pytest.raises(RegistryError, match="south>=north"):
        load_cities(p)


def test_get_city_returns_entry():
    cities = {"madison": _valid_entry()}
    c = get_city(cities, "madison")
    assert c["display_name"] == "Test City"


def test_get_city_unknown_raises():
    cities = {"madison": _valid_entry()}
    with pytest.raises(CityNotFoundError, match="atlantis"):
        get_city(cities, "atlantis")


def test_real_cities_json_loads_with_5_entries():
    """Regression test: el cities.json del repo debe tener exactamente 5 entries válidas."""
    repo_root = Path(__file__).resolve().parents[2]
    p = repo_root / "cities.json"
    cities = load_cities(p)
    expected = {"minneapolis", "manhattan", "tokyo", "amsterdam", "madison"}
    assert set(cities.keys()) == expected, f"Esperaba {expected}, got {set(cities.keys())}"


def test_real_cities_json_minneapolis_bbox_unchanged():
    """Regression: el bbox histórico de Mpls no debe cambiar (rompería prebuilts viejos)."""
    repo_root = Path(__file__).resolve().parents[2]
    cities = load_cities(repo_root / "cities.json")
    assert cities["minneapolis"]["bbox"] == [44.86, -93.38, 45.05, -93.17]
