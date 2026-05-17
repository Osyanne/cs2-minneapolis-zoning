"""Tests del flag --city de extract-services (Featured Cities Pack)."""
import sys, os, json
from pathlib import Path
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from services.extract import resolve_city_args
from shared.registry import CityNotFoundError


def _make_cities_json(tmp_path, slugs=("minneapolis",)):
    cities_file = tmp_path / "cities.json"
    entries = {}
    for s in slugs:
        entries[s] = {
            "display_name": s.title(), "country": "USA",
            "bbox": [44.86, -93.38, 45.05, -93.17],
            "center": [44.97, -93.27], "zoom": 12,
            "tagline": "t", "locale": "es"
        }
    cities_file.write_text(json.dumps(entries))
    return cities_file


def test_extract_services_unknown_city_raises(tmp_path):
    with pytest.raises(CityNotFoundError, match="atlantis"):
        resolve_city_args(city="atlantis", bbox=None, slug=None,
                          cities_file=_make_cities_json(tmp_path))


def test_extract_services_city_resolves_bbox_and_slug(tmp_path):
    bbox, slug = resolve_city_args(
        city="minneapolis", bbox=None, slug=None,
        cities_file=_make_cities_json(tmp_path)
    )
    assert bbox == "44.86,-93.38,45.05,-93.17"
    assert slug == "minneapolis"


def test_extract_services_escape_hatch(tmp_path):
    bbox, slug = resolve_city_args(
        city=None, bbox="10,20,11,21", slug="testopolis",
        cities_file=_make_cities_json(tmp_path)
    )
    assert (bbox, slug) == ("10,20,11,21", "testopolis")


def test_extract_services_bbox_without_slug_raises(tmp_path):
    with pytest.raises(ValueError, match="slug"):
        resolve_city_args(city=None, bbox="10,20,11,21", slug=None,
                          cities_file=_make_cities_json(tmp_path))


def test_extract_services_no_args_raises(tmp_path):
    with pytest.raises(ValueError, match="--city o --bbox"):
        resolve_city_args(city=None, bbox=None, slug=None,
                          cities_file=_make_cities_json(tmp_path))


def test_extract_services_city_plus_bbox_emits_warning(tmp_path, capsys):
    """--city + --bbox simultáneos: --city gana + warning a stderr."""
    bbox, slug = resolve_city_args(
        city="minneapolis", bbox="999,999,999,999", slug=None,
        cities_file=_make_cities_json(tmp_path)
    )
    assert bbox == "44.86,-93.38,45.05,-93.17"
    assert slug == "minneapolis"
    captured = capsys.readouterr()
    assert "WARNING" in captured.err
    assert "999,999" in captured.err
    assert "minneapolis" in captured.err
