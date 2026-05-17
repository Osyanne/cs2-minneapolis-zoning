"""Tests del flag --city de extract-zoning (Featured Cities Pack)."""
import sys, os, json
from pathlib import Path
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from zoning.extract import resolve_city_args
from shared.registry import CityNotFoundError

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_extract_zoning_unknown_city_exits_with_error(tmp_path):
    """--city con slug no registrado debe exit-fail con mensaje claro."""
    cities_file = tmp_path / "cities.json"
    cities_file.write_text(json.dumps({
        "minneapolis": {
            "display_name": "Mpls", "country": "USA",
            "bbox": [44.86, -93.38, 45.05, -93.17],
            "center": [44.97, -93.27], "zoom": 12,
            "tagline": "test", "locale": "es"
        }
    }))
    with pytest.raises(CityNotFoundError, match="atlantis"):
        resolve_city_args(city="atlantis", bbox=None, slug=None, cities_file=cities_file)


def test_extract_zoning_city_resolves_bbox_and_slug(tmp_path):
    """--city minneapolis debe devolver bbox del registro + slug='minneapolis'."""
    cities_file = tmp_path / "cities.json"
    cities_file.write_text(json.dumps({
        "minneapolis": {
            "display_name": "Mpls", "country": "USA",
            "bbox": [44.86, -93.38, 45.05, -93.17],
            "center": [44.97, -93.27], "zoom": 12,
            "tagline": "test", "locale": "es"
        }
    }))
    bbox, slug = resolve_city_args(
        city="minneapolis", bbox=None, slug=None, cities_file=cities_file
    )
    assert bbox == "44.86,-93.38,45.05,-93.17"
    assert slug == "minneapolis"


def test_extract_zoning_escape_hatch_bbox_plus_slug(tmp_path):
    """--bbox X --slug Y (sin --city) debe usar valores crudos del usuario."""
    cities_file = tmp_path / "cities.json"
    cities_file.write_text(json.dumps({}))
    bbox, slug = resolve_city_args(
        city=None, bbox="10,20,11,21", slug="testopolis", cities_file=cities_file
    )
    assert bbox == "10,20,11,21"
    assert slug == "testopolis"


def test_extract_zoning_bbox_without_slug_raises(tmp_path):
    """--bbox solo (sin --city ni --slug) debe error: necesita slug para output path."""
    cities_file = tmp_path / "cities.json"
    cities_file.write_text(json.dumps({}))
    with pytest.raises(ValueError, match="slug"):
        resolve_city_args(
            city=None, bbox="10,20,11,21", slug=None, cities_file=cities_file
        )


def test_extract_zoning_no_args_raises(tmp_path):
    """Sin --city ni --bbox debe error."""
    cities_file = tmp_path / "cities.json"
    cities_file.write_text(json.dumps({}))
    with pytest.raises(ValueError, match="--city o --bbox"):
        resolve_city_args(
            city=None, bbox=None, slug=None, cities_file=cities_file
        )


def test_extract_zoning_city_plus_bbox_emits_warning(tmp_path, capsys):
    """--city + --bbox simultáneos: --city gana + warning a stderr."""
    cities_file = tmp_path / "cities.json"
    cities_file.write_text(json.dumps({
        "minneapolis": {
            "display_name": "Mpls", "country": "USA",
            "bbox": [44.86, -93.38, 45.05, -93.17],
            "center": [44.97, -93.27], "zoom": 12,
            "tagline": "test", "locale": "es"
        }
    }))
    bbox, slug = resolve_city_args(
        city="minneapolis", bbox="999,999,999,999", slug=None, cities_file=cities_file
    )
    # --city ganó: bbox del registro, slug del registro
    assert bbox == "44.86,-93.38,45.05,-93.17"
    assert slug == "minneapolis"
    # Warning a stderr
    captured = capsys.readouterr()
    assert "WARNING" in captured.err
    assert "999,999" in captured.err
    assert "minneapolis" in captured.err
