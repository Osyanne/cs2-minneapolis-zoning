"""
Tests para shared/thumbnails.py — solo el discovery puro (sin playwright).

El path de captura via Chromium se valida manualmente porque requiere el binario
de Chromium instalado + acceso a red al deployed Pages.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import pytest

from shared.thumbnails import discover_missing
from shared.registry import CityNotFoundError


SAMPLE_CITIES = {
    "minneapolis": {"display_name": "Minneapolis, MN"},
    "amsterdam":   {"display_name": "Amsterdam"},
    "trondheim":   {"display_name": "Trondheim"},
}


# ── discover_missing — only_city path ───────────────────────────────────────

def test_only_city_returns_that_slug(tmp_path):
    slugs = discover_missing(SAMPLE_CITIES, tmp_path, force=False, only_city="amsterdam")
    assert slugs == ["amsterdam"]


def test_only_city_overrides_existing_png(tmp_path):
    """Aunque el PNG ya exista, --city lo incluye igual (idempotente regen)."""
    (tmp_path / "amsterdam.png").write_bytes(b"\x89PNG fake")
    slugs = discover_missing(SAMPLE_CITIES, tmp_path, force=False, only_city="amsterdam")
    assert slugs == ["amsterdam"]


def test_only_city_unknown_slug_raises(tmp_path):
    with pytest.raises(CityNotFoundError, match="atlantis"):
        discover_missing(SAMPLE_CITIES, tmp_path, force=False, only_city="atlantis")


# ── discover_missing — force path ───────────────────────────────────────────

def test_force_returns_all_slugs_sorted(tmp_path):
    # Aún con PNGs presentes, --force las regenera todas
    for slug in SAMPLE_CITIES:
        (tmp_path / f"{slug}.png").write_bytes(b"\x89PNG")
    slugs = discover_missing(SAMPLE_CITIES, tmp_path, force=True, only_city=None)
    assert slugs == sorted(SAMPLE_CITIES.keys())


# ── discover_missing — default (missing-only) path ──────────────────────────

def test_default_returns_only_missing(tmp_path):
    """PNG existente → skip; PNG missing → incluido."""
    (tmp_path / "minneapolis.png").write_bytes(b"\x89PNG")
    (tmp_path / "amsterdam.png").write_bytes(b"\x89PNG")
    # trondheim.png NO existe → debería ser el único en el output
    slugs = discover_missing(SAMPLE_CITIES, tmp_path, force=False, only_city=None)
    assert slugs == ["trondheim"]


def test_default_returns_empty_when_all_present(tmp_path):
    for slug in SAMPLE_CITIES:
        (tmp_path / f"{slug}.png").write_bytes(b"\x89PNG")
    slugs = discover_missing(SAMPLE_CITIES, tmp_path, force=False, only_city=None)
    assert slugs == []


def test_default_returns_all_when_none_present(tmp_path):
    slugs = discover_missing(SAMPLE_CITIES, tmp_path, force=False, only_city=None)
    assert slugs == sorted(SAMPLE_CITIES.keys())


def test_output_is_always_sorted_for_reproducibility(tmp_path):
    slugs_force = discover_missing(SAMPLE_CITIES, tmp_path, force=True, only_city=None)
    assert slugs_force == sorted(slugs_force)

    slugs_default = discover_missing(SAMPLE_CITIES, tmp_path, force=False, only_city=None)
    assert slugs_default == sorted(slugs_default)
