# Featured Cities Pack Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pivotar el toolkit de Mpls-specific a multi-city: 4 ciudades nuevas (Manhattan, Tokyo, Amsterdam, Madison) zoning-only + Minneapolis preserva los 3 módulos. Visualizer hosteado en GitHub Pages con `?city=<slug>` y landing con galería.

**Architecture:** Registro `cities.json` (slug→metadata) + `manifest.json` per-city (qué módulos generados). Pipeline Python gana flag `--city <slug>`. Visualizer refactor: `index.html` → landing + `map.html` (data-driven, manifest-driven module loading, sin live-Overpass).

**Tech Stack:** Python 3.11 + uv, Leaflet.js, vanilla HTML/CSS, GitHub Pages (estático), pytest.

**Spec:** [docs/specs/2026-05-17-featured-cities-pack-design.md](../specs/2026-05-17-featured-cities-pack-design.md)

**Branch:** `feature/featured-cities-pack` (ya creada, commit del spec `65391fb`)

---

## File Structure

**Created:**
- `cities.json` (root) — registro single source of truth
- `src/shared/registry.py` — load_cities/get_city + manifest IO
- `src/shared/landing.py` — generador de `index.html`
- `tests/shared/__init__.py`, `tests/shared/test_registry.py`, `tests/shared/test_landing.py`
- `visualizer/cities/<slug>/manifest.json` (5 files) + `datos_*.js` regenerados ahí
- `visualizer/index.html` (NUEVO — landing) — el existente se mueve a `map.html`
- `visualizer/map.html` (era `index.html`, refactorizado)
- `visualizer/assets/thumbnails/<slug>.png` (5 archivos, screenshots manuales)
- `.github/ISSUE_TEMPLATE/city-request.yml`

**Modified:**
- `src/zoning/extract.py` — add `--city` flag, output path con slug, escribe manifest
- `src/vial/extract.py` — idem
- `src/services/extract.py` — idem
- `src/zoning/zones.py` — remove `MINNEAPOLIS_BBOX` constant
- `src/vial/zones.py` — idem
- `src/services/zones.py` — idem
- `src/pyproject.toml` — add `generate-landing` entry-point, bump version 3.1.0 → 3.3.0
- `README.md`, `README.es.md` — multi-city note, v3.3 badge, deferred rename
- `METHODOLOGY.md` — nueva sección sobre multi-city
- Tests existentes que referencian `MINNEAPOLIS_BBOX` o paths viejos

**Deleted (después de migración):**
- `visualizer/datos_zonificacion.js` (movido a `visualizer/cities/minneapolis/`)
- `visualizer/datos_vial.js` (movido)
- `visualizer/datos_servicios.js` (movido)

---

## Cities bbox/center reference

Estos valores se usan en Task 2 y Task 9 al poblar `cities.json`:

| Slug | display_name | bbox `[s,w,n,e]` | center `[lat,lon]` | zoom |
|------|--------------|-------------------|---------------------|------|
| `minneapolis` | Minneapolis, MN | `[44.86, -93.38, 45.05, -93.17]` | `[44.97, -93.27]` | 12 |
| `manhattan` | Manhattan, NYC | `[40.700, -74.020, 40.880, -73.910]` | `[40.790, -73.965]` | 12 |
| `tokyo` | Tokyo (Central) | `[35.620, 139.680, 35.740, 139.840]` | `[35.680, 139.760]` | 12 |
| `amsterdam` | Amsterdam | `[52.320, 4.830, 52.420, 4.970]` | `[52.370, 4.900]` | 13 |
| `madison` | Madison, WI | `[43.030, -89.500, 43.130, -89.300]` | `[43.080, -89.400]` | 12 |

---

## Task 1: Registry loader (`cities.json` IO)

**Files:**
- Create: `src/shared/registry.py`
- Create: `tests/shared/__init__.py`
- Create: `tests/shared/test_registry.py`

- [ ] **Step 1: Create `tests/shared/__init__.py`**

Empty file:
```python
```

- [ ] **Step 2: Write failing test for `load_cities`**

Create `tests/shared/test_registry.py`:
```python
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
```

- [ ] **Step 3: Run tests to verify they fail**

Run from `src/`:
```bash
cd src
uv run pytest ../tests/shared/test_registry.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'shared.registry'`

- [ ] **Step 4: Implement `src/shared/registry.py`**

Create `src/shared/registry.py`:
```python
"""Registro de ciudades (cities.json) + manifest per-city.

Single source of truth para qué ciudades existen y qué módulos están generados.
`cities.json` define qué ciudades son seleccionables; `manifest.json` per-city
declara qué módulos (zoning/vial/services) hay en disco para esa ciudad.
"""
import json
from pathlib import Path
from typing import Any


REQUIRED_CITY_FIELDS = {
    "display_name", "country", "bbox", "center", "zoom", "tagline", "locale",
}


class RegistryError(Exception):
    """cities.json malformado o entries inválidas."""


class CityNotFoundError(Exception):
    """Slug no presente en el registro."""


def load_cities(path: Path) -> dict[str, dict[str, Any]]:
    """Lee y valida cities.json. Devuelve dict {slug: metadata}."""
    if not Path(path).exists():
        raise RegistryError(f"cities.json no existe en {path}")
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise RegistryError(f"cities.json no es JSON válido: {e}") from e
    if not isinstance(data, dict):
        raise RegistryError("cities.json debe ser dict {slug: metadata}")
    for slug, entry in data.items():
        if not isinstance(entry, dict):
            raise RegistryError(f"Entry {slug!r} no es dict")
        missing = REQUIRED_CITY_FIELDS - set(entry.keys())
        if missing:
            raise RegistryError(
                f"Entry {slug!r} le faltan campos: {sorted(missing)}"
            )
        bbox = entry["bbox"]
        if not (
            isinstance(bbox, list)
            and len(bbox) == 4
            and all(isinstance(x, (int, float)) for x in bbox)
        ):
            raise RegistryError(
                f"Entry {slug!r}: bbox debe ser [s,w,n,e] de 4 floats"
            )
        s, w, n, e = bbox
        if s >= n:
            raise RegistryError(f"Entry {slug!r}: bbox inválido (south>=north)")
        if w >= e:
            raise RegistryError(f"Entry {slug!r}: bbox inválido (west>=east)")
    return data


def get_city(cities: dict, slug: str) -> dict:
    """Devuelve entry de la ciudad o lanza CityNotFoundError."""
    if slug not in cities:
        raise CityNotFoundError(
            f"Slug {slug!r} no está en el registro. "
            f"Disponibles: {sorted(cities.keys())}"
        )
    return cities[slug]
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd src
uv run pytest ../tests/shared/test_registry.py -v
```

Expected: PASS — 8 tests passed

- [ ] **Step 6: Commit**

```bash
git add src/shared/registry.py tests/shared/__init__.py tests/shared/test_registry.py
git commit -m "feat(shared): registry.py — load/validate cities.json

Implementa load_cities() y get_city() con validación de schema
(REQUIRED_CITY_FIELDS, bbox shape, bbox geometría sensata). Tests: 8.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Create `cities.json` root file with 5 entries

**Files:**
- Create: `cities.json`
- Modify: `tests/shared/test_registry.py` — add regression test for real file

- [ ] **Step 1: Write failing test that validates the real cities.json**

Append to `tests/shared/test_registry.py`:
```python


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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd src
uv run pytest ../tests/shared/test_registry.py::test_real_cities_json_loads_with_5_entries -v
```

Expected: FAIL with `RegistryError: cities.json no existe`

- [ ] **Step 3: Create `cities.json` at repo root**

Create `cities.json` (in the repo root, not inside `src/`):
```json
{
  "minneapolis": {
    "display_name": "Minneapolis, MN",
    "country": "USA",
    "bbox": [44.86, -93.38, 45.05, -93.17],
    "center": [44.97, -93.27],
    "zoom": 12,
    "tagline": "Ciudad hero — fully featured",
    "locale": "es"
  },
  "manhattan": {
    "display_name": "Manhattan, NYC",
    "country": "USA",
    "bbox": [40.700, -74.020, 40.880, -73.910],
    "center": [40.790, -73.965],
    "zoom": 12,
    "tagline": "Grilla densa de rascacielos",
    "locale": "es"
  },
  "tokyo": {
    "display_name": "Tokyo (Central)",
    "country": "Japan",
    "bbox": [35.620, 139.680, 35.740, 139.840],
    "center": [35.680, 139.760],
    "zoom": 12,
    "tagline": "Super-blocks y densidad mixta",
    "locale": "es"
  },
  "amsterdam": {
    "display_name": "Amsterdam",
    "country": "Netherlands",
    "bbox": [52.320, 4.830, 52.420, 4.970],
    "center": [52.370, 4.900],
    "zoom": 13,
    "tagline": "Canales y bike-first urbanism",
    "locale": "es"
  },
  "madison": {
    "display_name": "Madison, WI",
    "country": "USA",
    "bbox": [43.030, -89.500, 43.130, -89.300],
    "center": [43.080, -89.400],
    "zoom": 12,
    "tagline": "Isthmus capital — mid-size americana",
    "locale": "es"
  }
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd src
uv run pytest ../tests/shared/test_registry.py -v
```

Expected: PASS — 10 tests passed (8 unit + 2 regression sobre cities.json real)

- [ ] **Step 5: Commit**

```bash
git add cities.json tests/shared/test_registry.py
git commit -m "feat: cities.json registry con 5 entries (mpls + manhattan + tokyo + amsterdam + madison)

Bbox de Minneapolis preservado del histórico. 4 ciudades nuevas con
bboxes seleccionados para cubrir downtown + áreas inmediatas, ~14km de lado
en promedio. Centers y zooms calibrados manualmente.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Manifest IO (`manifest.json` per-city)

**Files:**
- Modify: `src/shared/registry.py` — agregar funciones manifest
- Modify: `tests/shared/test_registry.py` — agregar tests manifest

- [ ] **Step 1: Write failing tests for manifest IO**

Append to `tests/shared/test_registry.py`:
```python


from shared.registry import (
    load_manifest, save_manifest_entry, manifest_path, hash_file, VALID_MODULES,
)


def test_manifest_path_structure(tmp_path):
    p = manifest_path(tmp_path, "manhattan")
    assert p == tmp_path / "cities" / "manhattan" / "manifest.json"


def test_load_manifest_returns_none_if_missing(tmp_path):
    assert load_manifest(tmp_path, "ghost") is None


def test_load_manifest_reads_valid(tmp_path):
    p = manifest_path(tmp_path, "manhattan")
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps({
        "modules": {"zoning": {"hash": "abc123", "features": 100}},
        "generated_at": "2026-05-17T00:00:00+00:00",
    }))
    m = load_manifest(tmp_path, "manhattan")
    assert m["modules"]["zoning"]["features"] == 100


def test_load_manifest_malformed_raises(tmp_path):
    p = manifest_path(tmp_path, "manhattan")
    p.parent.mkdir(parents=True)
    p.write_text("not json")
    with pytest.raises(RegistryError):
        load_manifest(tmp_path, "manhattan")


def test_save_manifest_entry_creates_file(tmp_path):
    data_file = tmp_path / "fake_data.js"
    data_file.write_text("const X = 1;")
    manifest = save_manifest_entry(tmp_path, "manhattan", "zoning", data_file, 42)
    assert manifest["modules"]["zoning"]["features"] == 42
    assert len(manifest["modules"]["zoning"]["hash"]) == 8
    assert "generated_at" in manifest
    # Verifica que se persistió a disco
    on_disk = load_manifest(tmp_path, "manhattan")
    assert on_disk == manifest


def test_save_manifest_entry_preserves_other_modules(tmp_path):
    # Setup: manifest existente con zoning
    p = manifest_path(tmp_path, "minneapolis")
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps({
        "modules": {"zoning": {"hash": "old", "features": 1}},
        "generated_at": "2026-05-01T00:00:00+00:00",
    }))
    # Agregar vial
    data_file = tmp_path / "fake_vial.js"
    data_file.write_text("const Y = 2;")
    manifest = save_manifest_entry(tmp_path, "minneapolis", "vial", data_file, 99)
    # Tanto zoning (viejo) como vial (nuevo) deben estar
    assert "zoning" in manifest["modules"]
    assert "vial" in manifest["modules"]
    assert manifest["modules"]["zoning"]["features"] == 1  # preservado
    assert manifest["modules"]["vial"]["features"] == 99


def test_save_manifest_entry_invalid_module_raises(tmp_path):
    data_file = tmp_path / "x.js"
    data_file.write_text("x")
    with pytest.raises(ValueError, match="módulo"):
        save_manifest_entry(tmp_path, "x", "invalid_module", data_file, 1)


def test_hash_file_deterministic(tmp_path):
    p = tmp_path / "f.js"
    p.write_text("hello")
    h1 = hash_file(p)
    h2 = hash_file(p)
    assert h1 == h2
    assert len(h1) == 8
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd src
uv run pytest ../tests/shared/test_registry.py -v -k "manifest or hash"
```

Expected: FAIL with `ImportError: cannot import name 'load_manifest'`

- [ ] **Step 3: Extend `src/shared/registry.py` with manifest IO**

Append to `src/shared/registry.py`:
```python


# ── Manifest IO ──────────────────────────────────────────────────────────────

import hashlib
from datetime import datetime, timezone


VALID_MODULES = {"zoning", "vial", "services"}


def manifest_path(visualizer_root: Path, slug: str) -> Path:
    """Devuelve la ruta esperada del manifest para una ciudad."""
    return Path(visualizer_root) / "cities" / slug / "manifest.json"


def load_manifest(visualizer_root: Path, slug: str) -> dict | None:
    """Lee manifest.json de la ciudad. Devuelve None si no existe."""
    p = manifest_path(visualizer_root, slug)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise RegistryError(f"manifest.json malformado para {slug}: {e}") from e


def hash_file(path: Path, length: int = 8) -> str:
    """sha256 trunco a `length` chars para cache busting."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:length]


def save_manifest_entry(
    visualizer_root: Path,
    slug: str,
    module: str,
    file_path: Path,
    features: int,
) -> dict:
    """Agrega/actualiza entry de `module` en manifest.json de la ciudad.

    Preserva entries de otros módulos. Crea directorio si no existe.
    Devuelve el manifest completo tras el merge.
    """
    if module not in VALID_MODULES:
        raise ValueError(
            f"módulo debe ser uno de {sorted(VALID_MODULES)}, no {module!r}"
        )
    manifest = load_manifest(visualizer_root, slug) or {"modules": {}}
    manifest.setdefault("modules", {})
    manifest["modules"][module] = {
        "hash": hash_file(file_path),
        "features": int(features),
    }
    manifest["generated_at"] = datetime.now(timezone.utc).isoformat()
    p = manifest_path(visualizer_root, slug)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd src
uv run pytest ../tests/shared/test_registry.py -v
```

Expected: PASS — 18 tests total (10 anteriores + 8 nuevos)

- [ ] **Step 5: Commit**

```bash
git add src/shared/registry.py tests/shared/test_registry.py
git commit -m "feat(shared): manifest IO (load/save/merge per-city)

manifest.json declara qué módulos hay generados para una ciudad y su hash
sha256 trunco a 8 chars (para cache busting). save_manifest_entry preserva
otros módulos al actualizar uno (clave para promover ciudades a fully-featured
sin perder zoning ya generado). Tests: 8 nuevos.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Add `--city` flag to `extract-zoning`

**Files:**
- Modify: `src/zoning/extract.py` — add --city flag, resolve via registry, write manifest, output path con slug
- Modify: `tests/zoning/test_classifiers.py` (si referencia MINNEAPOLIS_BBOX) — postpone a Task 7

**Context:** El script actual acepta `--bbox` con default `MINNEAPOLIS_BBOX`. Agregar `--city <slug>` que lee `cities.json` desde repo root, deriva bbox + escribe a `visualizer/cities/<slug>/datos_zonificacion.js` + actualiza manifest. `--bbox`+`--slug` como escape hatch para ciudades no registradas.

- [ ] **Step 1: Write failing test for --city resolution**

Create `tests/zoning/test_extract_city.py`:
```python
"""Tests del flag --city de extract-zoning (Featured Cities Pack)."""
import sys, os, json, subprocess
from pathlib import Path
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_extract_zoning_unknown_city_exits_with_error(tmp_path, monkeypatch):
    """--city con slug no registrado debe exit-fail con mensaje claro."""
    from zoning.extract import resolve_city_args
    from shared.registry import CityNotFoundError
    
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
    from zoning.extract import resolve_city_args
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
    from zoning.extract import resolve_city_args
    cities_file = tmp_path / "cities.json"
    cities_file.write_text(json.dumps({}))
    bbox, slug = resolve_city_args(
        city=None, bbox="10,20,11,21", slug="testopolis", cities_file=cities_file
    )
    assert bbox == "10,20,11,21"
    assert slug == "testopolis"


def test_extract_zoning_bbox_without_slug_raises(tmp_path):
    """--bbox solo (sin --city ni --slug) debe error: necesita slug para output path."""
    from zoning.extract import resolve_city_args
    cities_file = tmp_path / "cities.json"
    cities_file.write_text(json.dumps({}))
    with pytest.raises(ValueError, match="slug"):
        resolve_city_args(
            city=None, bbox="10,20,11,21", slug=None, cities_file=cities_file
        )


def test_extract_zoning_no_args_raises(tmp_path):
    """Sin --city ni --bbox debe error."""
    from zoning.extract import resolve_city_args
    cities_file = tmp_path / "cities.json"
    cities_file.write_text(json.dumps({}))
    with pytest.raises(ValueError, match="--city o --bbox"):
        resolve_city_args(
            city=None, bbox=None, slug=None, cities_file=cities_file
        )
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd src
uv run pytest ../tests/zoning/test_extract_city.py -v
```

Expected: FAIL with `ImportError: cannot import name 'resolve_city_args' from 'zoning.extract'`

- [ ] **Step 3: Add `resolve_city_args` to `src/zoning/extract.py`**

In `src/zoning/extract.py`, after the existing imports, add this helper (just below the import block, before any other function):

```python
from shared.registry import load_cities, get_city


def resolve_city_args(
    city: str | None,
    bbox: str | None,
    slug: str | None,
    cities_file: Path,
) -> tuple[str, str]:
    """Resuelve los argumentos CLI a (bbox, slug) finales.

    Modos:
    - --city <slug>: lee cities.json, deriva bbox del registro
    - --bbox X --slug Y: escape hatch sin tocar registro
    - Ambos --city y --bbox: --city gana (con warning)
    - Solo --bbox: error (necesita --slug)
    - Nada: error
    """
    if city is not None:
        cities = load_cities(cities_file)
        entry = get_city(cities, city)
        s, w, n, e = entry["bbox"]
        return (f"{s},{w},{n},{e}", city)
    if bbox is not None:
        if slug is None:
            raise ValueError(
                "Si pasas --bbox debes pasar también --slug "
                "(usado para el output path visualizer/cities/<slug>/)"
            )
        return (bbox, slug)
    raise ValueError("Debes pasar --city o --bbox+--slug")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd src
uv run pytest ../tests/zoning/test_extract_city.py -v
```

Expected: PASS — 5 tests passed

- [ ] **Step 5: Update `main()` in `src/zoning/extract.py` to use `resolve_city_args` and write to new path**

In `src/zoning/extract.py`, find the `def main()` function. Locate the argparse section (currently has `--bbox` with default `MINNEAPOLIS_BBOX`). Replace the argparse block + the bbox/output handling. The current shape is approximately:

```python
def main():
    parser = argparse.ArgumentParser(...)
    parser.add_argument("--bbox", default=MINNEAPOLIS_BBOX, ...)
    parser.add_argument("--out", default="...", ...)
    args = parser.parse_args()
    bbox = args.bbox
    out_path = Path(args.out)
    queries = build_queries(bbox)
    # ... rest of pipeline
```

Replace with:
```python
def main():
    parser = argparse.ArgumentParser(
        description="Extract OSM zoning data → visualizer prebuilt JS"
    )
    parser.add_argument("--city", help="Slug de cities.json (ej. minneapolis, manhattan)")
    parser.add_argument("--bbox", help="Escape hatch: bbox 's,w,n,e' (requiere --slug)")
    parser.add_argument("--slug", help="Output slug cuando se usa --bbox sin --city")
    parser.add_argument(
        "--cities-file",
        default=None,
        help="Path a cities.json (default: <repo_root>/cities.json)",
    )
    parser.add_argument(
        "--visualizer-root",
        default=None,
        help="Path a visualizer/ (default: <repo_root>/visualizer)",
    )
    args = parser.parse_args()

    # Resolver paths
    repo_root = Path(__file__).resolve().parents[2]
    cities_file = Path(args.cities_file) if args.cities_file else repo_root / "cities.json"
    vis_root = Path(args.visualizer_root) if args.visualizer_root else repo_root / "visualizer"

    bbox, slug = resolve_city_args(args.city, args.bbox, args.slug, cities_file)
    out_dir = vis_root / "cities" / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "datos_zonificacion.js"

    queries = build_queries(bbox)

    print(f"CS2 OSM Toolkit — Zoning Extractor")
    print(f"City         : {slug}")
    print(f"Bounding Box : {bbox}")
    print(f"Output       : {out_path}")

    # ... resto del pipeline (sin cambios hasta el final, ver Step 6)
```

Keep everything from `queries = build_queries(bbox)` to the file-writing logic, but at the end (after writing the .js file) add the manifest update — see Step 6.

- [ ] **Step 6: Add manifest write after the .js file is written**

In `src/zoning/extract.py`, locate where the script writes `out_path` (look for `out_path.write_text(...)` or `f.write(...)` and an inferred features count). Right after the file is finalized, add:

```python
    from shared.registry import save_manifest_entry
    total_features = sum(len(v) for v in zoning_polygons.values())  # adjust to actual var
    save_manifest_entry(
        visualizer_root=vis_root,
        slug=slug,
        module="zoning",
        file_path=out_path,
        features=total_features,
    )
    print(f"Manifest      : {vis_root / 'cities' / slug / 'manifest.json'}")
```

**Note:** El nombre exacto de la variable con el conteo de features depende del código actual. Si no existe, calcular en el momento (`total_features = N` derivado de lo que ya se conoce al final del pipeline).

- [ ] **Step 7: Smoke-test the modified extract-zoning by running it for Minneapolis**

```bash
cd src
uv run extract-zoning --city minneapolis
```

Expected output (resumido):
```
CS2 OSM Toolkit — Zoning Extractor
City         : minneapolis
Bounding Box : 44.86,-93.38,45.05,-93.17
Output       : ...\visualizer\cities\minneapolis\datos_zonificacion.js
[...overpass progress...]
Manifest     : ...\visualizer\cities\minneapolis\manifest.json
```

Verify outputs exist:
```bash
ls "C:/Users/osyanne/Documents/Claude/Projects/Proyecto mineapolis/cs2-minneapolis-zoning/visualizer/cities/minneapolis/"
```

Expected: `datos_zonificacion.js` + `manifest.json`

- [ ] **Step 8: Commit**

```bash
git add src/zoning/extract.py tests/zoning/test_extract_city.py
git commit -m "feat(zoning): --city flag + output a cities/<slug>/ + manifest

extract-zoning ahora resuelve bbox vía cities.json registry. Output va
a visualizer/cities/<slug>/datos_zonificacion.js. Escribe/actualiza
manifest.json con hash sha256 y feature count. Mantiene --bbox+--slug
como escape hatch. Tests: 5 nuevos.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: Add `--city` flag to `extract-vial`

**Files:**
- Modify: `src/vial/extract.py` — mismos cambios que Task 4 pero para vial
- Create: `tests/vial/test_extract_city.py` — análogo a `tests/zoning/test_extract_city.py`

**Context:** El patrón es idéntico al Task 4. Solo cambia el módulo (`vial` en lugar de `zoning`), el output filename (`datos_vial.js`), y el manifest module key (`"vial"`).

- [ ] **Step 1: Create `tests/vial/test_extract_city.py`**

Copy `tests/zoning/test_extract_city.py` y cambiar todos los `zoning` → `vial`. El contenido completo:

```python
"""Tests del flag --city de extract-vial (Featured Cities Pack)."""
import sys, os, json
from pathlib import Path
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

REPO_ROOT = Path(__file__).resolve().parents[2]


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


def test_extract_vial_unknown_city_raises(tmp_path):
    from vial.extract import resolve_city_args
    from shared.registry import CityNotFoundError
    with pytest.raises(CityNotFoundError, match="atlantis"):
        resolve_city_args(
            city="atlantis", bbox=None, slug=None,
            cities_file=_make_cities_json(tmp_path)
        )


def test_extract_vial_city_resolves_bbox_and_slug(tmp_path):
    from vial.extract import resolve_city_args
    bbox, slug = resolve_city_args(
        city="minneapolis", bbox=None, slug=None,
        cities_file=_make_cities_json(tmp_path)
    )
    assert bbox == "44.86,-93.38,45.05,-93.17"
    assert slug == "minneapolis"


def test_extract_vial_escape_hatch(tmp_path):
    from vial.extract import resolve_city_args
    bbox, slug = resolve_city_args(
        city=None, bbox="10,20,11,21", slug="testopolis",
        cities_file=_make_cities_json(tmp_path)
    )
    assert (bbox, slug) == ("10,20,11,21", "testopolis")


def test_extract_vial_bbox_without_slug_raises(tmp_path):
    from vial.extract import resolve_city_args
    with pytest.raises(ValueError, match="slug"):
        resolve_city_args(
            city=None, bbox="10,20,11,21", slug=None,
            cities_file=_make_cities_json(tmp_path)
        )


def test_extract_vial_no_args_raises(tmp_path):
    from vial.extract import resolve_city_args
    with pytest.raises(ValueError, match="--city o --bbox"):
        resolve_city_args(
            city=None, bbox=None, slug=None,
            cities_file=_make_cities_json(tmp_path)
        )
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd src
uv run pytest ../tests/vial/test_extract_city.py -v
```

Expected: FAIL — `ImportError: cannot import name 'resolve_city_args' from 'vial.extract'`

- [ ] **Step 3: Apply identical changes to `src/vial/extract.py`**

In `src/vial/extract.py`:

(a) Add this import + helper (after existing imports):
```python
from shared.registry import load_cities, get_city


def resolve_city_args(
    city: str | None,
    bbox: str | None,
    slug: str | None,
    cities_file: Path,
) -> tuple[str, str]:
    """Idéntico a zoning.extract.resolve_city_args — ver docstring allí."""
    if city is not None:
        cities = load_cities(cities_file)
        entry = get_city(cities, city)
        s, w, n, e = entry["bbox"]
        return (f"{s},{w},{n},{e}", city)
    if bbox is not None:
        if slug is None:
            raise ValueError(
                "Si pasas --bbox debes pasar también --slug"
            )
        return (bbox, slug)
    raise ValueError("Debes pasar --city o --bbox+--slug")
```

(b) Update `main()`: replace argparse block (currently `--bbox` with default `MINNEAPOLIS_BBOX`) con el mismo bloque que zoning, pero con output filename `datos_vial.js`:

```python
def main():
    parser = argparse.ArgumentParser(description="Extract OSM road network → JS prebuilt")
    parser.add_argument("--city")
    parser.add_argument("--bbox")
    parser.add_argument("--slug")
    parser.add_argument("--cities-file", default=None)
    parser.add_argument("--visualizer-root", default=None)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    cities_file = Path(args.cities_file) if args.cities_file else repo_root / "cities.json"
    vis_root = Path(args.visualizer_root) if args.visualizer_root else repo_root / "visualizer"

    bbox, slug = resolve_city_args(args.city, args.bbox, args.slug, cities_file)
    out_dir = vis_root / "cities" / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "datos_vial.js"

    query = build_vial_query(bbox)
    print(f"CS2 OSM Toolkit — Vial Extractor")
    print(f"City         : {slug}")
    print(f"Bounding Box : {bbox}")
    print(f"Output       : {out_path}")
    # ... resto del pipeline existente sin cambios
```

(c) Después de escribir el .js file, agregar:
```python
    from shared.registry import save_manifest_entry
    save_manifest_entry(
        visualizer_root=vis_root,
        slug=slug,
        module="vial",
        file_path=out_path,
        features=total,  # `total` ya existe en este script
    )
    print(f"Manifest     : {vis_root / 'cities' / slug / 'manifest.json'}")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd src
uv run pytest ../tests/vial/test_extract_city.py -v
```

Expected: PASS — 5 tests passed

- [ ] **Step 5: Smoke-test extract-vial against Minneapolis**

```bash
cd src
uv run extract-vial --city minneapolis
```

Verify outputs:
```bash
ls "C:/Users/osyanne/Documents/Claude/Projects/Proyecto mineapolis/cs2-minneapolis-zoning/visualizer/cities/minneapolis/"
```

Expected: `datos_zonificacion.js` + `datos_vial.js` + `manifest.json` (con ambas keys ahora)

Verify manifest:
```bash
cat "C:/Users/osyanne/Documents/Claude/Projects/Proyecto mineapolis/cs2-minneapolis-zoning/visualizer/cities/minneapolis/manifest.json"
```

Expected: JSON con `modules.zoning` y `modules.vial` ambos presentes.

- [ ] **Step 6: Commit**

```bash
git add src/vial/extract.py tests/vial/test_extract_city.py
git commit -m "feat(vial): --city flag + output a cities/<slug>/ + manifest

Mismo patrón que Task 4 (zoning). Smoke-test verifica que el manifest
preserva zoning al agregar vial. Tests: 5 nuevos.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: Add `--city` flag to `extract-services`

**Files:**
- Modify: `src/services/extract.py` — mismos cambios que Task 4 para services
- Create: `tests/services/test_extract_city.py` — análogo

**Context:** Patrón idéntico a Tasks 4 y 5.

- [ ] **Step 1: Create `tests/services/test_extract_city.py`**

Copy contents from `tests/vial/test_extract_city.py` y reemplazar `vial` → `services` en todos los imports y mensajes:

```python
"""Tests del flag --city de extract-services (Featured Cities Pack)."""
import sys, os, json
from pathlib import Path
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))


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
    from services.extract import resolve_city_args
    from shared.registry import CityNotFoundError
    with pytest.raises(CityNotFoundError, match="atlantis"):
        resolve_city_args(city="atlantis", bbox=None, slug=None,
                          cities_file=_make_cities_json(tmp_path))


def test_extract_services_city_resolves_bbox_and_slug(tmp_path):
    from services.extract import resolve_city_args
    bbox, slug = resolve_city_args(
        city="minneapolis", bbox=None, slug=None,
        cities_file=_make_cities_json(tmp_path)
    )
    assert bbox == "44.86,-93.38,45.05,-93.17"
    assert slug == "minneapolis"


def test_extract_services_escape_hatch(tmp_path):
    from services.extract import resolve_city_args
    bbox, slug = resolve_city_args(
        city=None, bbox="10,20,11,21", slug="testopolis",
        cities_file=_make_cities_json(tmp_path)
    )
    assert (bbox, slug) == ("10,20,11,21", "testopolis")


def test_extract_services_bbox_without_slug_raises(tmp_path):
    from services.extract import resolve_city_args
    with pytest.raises(ValueError, match="slug"):
        resolve_city_args(city=None, bbox="10,20,11,21", slug=None,
                          cities_file=_make_cities_json(tmp_path))


def test_extract_services_no_args_raises(tmp_path):
    from services.extract import resolve_city_args
    with pytest.raises(ValueError, match="--city o --bbox"):
        resolve_city_args(city=None, bbox=None, slug=None,
                          cities_file=_make_cities_json(tmp_path))
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd src
uv run pytest ../tests/services/test_extract_city.py -v
```

Expected: FAIL — `ImportError: cannot import name 'resolve_city_args' from 'services.extract'`

- [ ] **Step 3: Apply identical changes to `src/services/extract.py`**

In `src/services/extract.py`:

(a) Add import + helper after existing imports:
```python
from shared.registry import load_cities, get_city


def resolve_city_args(
    city: str | None,
    bbox: str | None,
    slug: str | None,
    cities_file: Path,
) -> tuple[str, str]:
    """Idéntico a zoning.extract.resolve_city_args — ver docstring allí."""
    if city is not None:
        cities = load_cities(cities_file)
        entry = get_city(cities, city)
        s, w, n, e = entry["bbox"]
        return (f"{s},{w},{n},{e}", city)
    if bbox is not None:
        if slug is None:
            raise ValueError(
                "Si pasas --bbox debes pasar también --slug"
            )
        return (bbox, slug)
    raise ValueError("Debes pasar --city o --bbox+--slug")
```

(b) Update `main()` con argparse block + output path análogo a Task 5, pero output filename `datos_servicios.js`. La función `run(bbox, out_path)` existente se mantiene.

(c) Después de la llamada a `run()` y antes del print final, agregar:
```python
    from shared.registry import save_manifest_entry
    save_manifest_entry(
        visualizer_root=vis_root,
        slug=slug,
        module="services",
        file_path=out_path,
        features=summary["total"],  # `summary` lo devuelve run()
    )
    print(f"Manifest     : {vis_root / 'cities' / slug / 'manifest.json'}")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd src
uv run pytest ../tests/services/test_extract_city.py -v
```

Expected: PASS — 5 tests passed

- [ ] **Step 5: Smoke-test extract-services against Minneapolis**

```bash
cd src
uv run extract-services --city minneapolis
```

Verify manifest now has all 3 modules:
```bash
cat "C:/Users/osyanne/Documents/Claude/Projects/Proyecto mineapolis/cs2-minneapolis-zoning/visualizer/cities/minneapolis/manifest.json"
```

Expected: `modules.zoning`, `modules.vial`, `modules.services` todos presentes con hashes y feature counts.

- [ ] **Step 6: Commit**

```bash
git add src/services/extract.py tests/services/test_extract_city.py
git commit -m "feat(services): --city flag + output a cities/<slug>/ + manifest

Mismo patrón que Tasks 4-5. Minneapolis ahora tiene los 3 módulos
generados al nuevo path visualizer/cities/minneapolis/. Tests: 5 nuevos.
Total tests del pack: 18 nuevos (suite ahora ~145 total).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 7: Remove `MINNEAPOLIS_BBOX` constants

**Files:**
- Modify: `src/zoning/zones.py` — quitar constante
- Modify: `src/vial/zones.py` — idem
- Modify: `src/services/zones.py` — idem
- Modify: tests que la importen (probablemente `tests/zoning/test_classifiers.py`, etc.)

**Context:** Ahora que el pipeline lee bbox del registro, `MINNEAPOLIS_BBOX` ya no es default de nadie. Es deuda técnica.

- [ ] **Step 1: Verificar dónde se usa todavía**

```bash
cd "C:/Users/osyanne/Documents/Claude/Projects/Proyecto mineapolis/cs2-minneapolis-zoning"
```

Use Grep tool con pattern `MINNEAPOLIS_BBOX` en paths `src/` y `tests/`. Listar todos los matches con número de línea.

Expected: matches en `src/zoning/zones.py`, `src/vial/zones.py`, `src/services/zones.py` (declaración) y posiblemente en tests (uso).

- [ ] **Step 2: Run full test suite — baseline para verificar regresión 0 al final**

```bash
cd src
uv run pytest .. -v
```

Expected: PASS — ~145 tests (los 127 históricos + 18 nuevos del Pack). Anotar el count exacto.

- [ ] **Step 3: Remove `MINNEAPOLIS_BBOX` from `src/zoning/zones.py`**

In `src/zoning/zones.py`, find the line:
```python
MINNEAPOLIS_BBOX = "44.86,-93.38,45.05,-93.17"
```

Delete that line completely (and the blank line after if redundant).

- [ ] **Step 4: Remove `MINNEAPOLIS_BBOX` from `src/vial/zones.py` and `src/services/zones.py`**

Same operation — delete the constant from both files.

- [ ] **Step 5: Run full test suite to identify breakages**

```bash
cd src
uv run pytest .. -v
```

Expected: Posibles FAILs por `ImportError: cannot import name 'MINNEAPOLIS_BBOX'`. Anotar los archivos de test que fallan.

- [ ] **Step 6: Fix test imports**

For each failing test file (likely `tests/zoning/test_classifiers.py`, `tests/zoning/test_queries.py`, `tests/services/test_zones.py`, `tests/services/test_extract.py`, `tests/vial/test_vial.py`):

- Eliminar `MINNEAPOLIS_BBOX` del import statement
- Si el test usa `MINNEAPOLIS_BBOX` como bbox literal, reemplazar in-place con `"44.86,-93.38,45.05,-93.17"` (string literal)

Example refactor en un test:
```python
# Antes:
from zoning.zones import CS2_LABELS, MINNEAPOLIS_BBOX, build_queries

def test_query_uses_bbox():
    q = build_queries(MINNEAPOLIS_BBOX)
    ...

# Después:
from zoning.zones import CS2_LABELS, build_queries

MPLS_BBOX = "44.86,-93.38,45.05,-93.17"

def test_query_uses_bbox():
    q = build_queries(MPLS_BBOX)
    ...
```

- [ ] **Step 7: Also remove `MINNEAPOLIS_BBOX` from imports in extract.py files**

The previous tasks (4, 5, 6) added new imports but didn't remove `MINNEAPOLIS_BBOX` from the existing import line. Now:

In `src/zoning/extract.py`:
```python
# Antes:
from zoning.zones import CS2_LABELS, MINNEAPOLIS_BBOX, build_queries
# Después:
from zoning.zones import CS2_LABELS, build_queries
```

Idem en `src/vial/extract.py` y `src/services/extract.py`.

- [ ] **Step 8: Run full test suite to verify all pass**

```bash
cd src
uv run pytest .. -v
```

Expected: PASS — mismo count que en Step 2 (sin regresión).

- [ ] **Step 9: Commit**

```bash
git add src/zoning/zones.py src/vial/zones.py src/services/zones.py \
        src/zoning/extract.py src/vial/extract.py src/services/extract.py \
        tests/
git commit -m "refactor: remove MINNEAPOLIS_BBOX constants — registry es source of truth

Constante histórica deprecada por cities.json registry. Tests refactorizados
para usar string literal local cuando lo necesitan. Sin regresión: ~145
tests siguen pasando.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 8: Migrate Minneapolis prebuilts to new location + delete old

**Files:**
- Delete: `visualizer/datos_zonificacion.js`
- Delete: `visualizer/datos_vial.js`
- Delete: `visualizer/datos_servicios.js`
- (Los archivos en `visualizer/cities/minneapolis/` ya existen de Tasks 4/5/6)

**Context:** Después de Tasks 4-6, los prebuilts de Mpls ya están duplicados (uno en la raíz viejo, uno en cities/minneapolis/ nuevo). Limpiar la raíz.

- [ ] **Step 1: Verificar que los archivos en cities/minneapolis/ están completos**

```bash
ls -la "C:/Users/osyanne/Documents/Claude/Projects/Proyecto mineapolis/cs2-minneapolis-zoning/visualizer/cities/minneapolis/"
```

Expected:
- `datos_zonificacion.js` (~27 MB)
- `datos_vial.js` (~25 MB)
- `datos_servicios.js` (~1.3 MB)
- `manifest.json` (con 3 modules entries)

Si alguno falta, re-correr el extract correspondiente (`uv run extract-X --city minneapolis`).

- [ ] **Step 2: Delete old prebuilts from `visualizer/` root**

```bash
rm "C:/Users/osyanne/Documents/Claude/Projects/Proyecto mineapolis/cs2-minneapolis-zoning/visualizer/datos_zonificacion.js"
rm "C:/Users/osyanne/Documents/Claude/Projects/Proyecto mineapolis/cs2-minneapolis-zoning/visualizer/datos_vial.js"
rm "C:/Users/osyanne/Documents/Claude/Projects/Proyecto mineapolis/cs2-minneapolis-zoning/visualizer/datos_servicios.js"
```

- [ ] **Step 3: Commit (delete only, no code change)**

```bash
git add visualizer/datos_zonificacion.js visualizer/datos_vial.js visualizer/datos_servicios.js \
        visualizer/cities/minneapolis/
git commit -m "chore: migrate Minneapolis prebuilts to visualizer/cities/minneapolis/

Los datos_*.js viejos en visualizer/ raíz se borran (ahora viven en
cities/<slug>/). Manifest.json declara los 3 módulos. visualizer/index.html
sigue refiriendo a los paths viejos — eso se arregla en Task 11.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 9: Generate zoning for the 4 new cities

**Files:**
- Create (vía pipeline): `visualizer/cities/manhattan/datos_zonificacion.js` + `manifest.json`
- Create: `visualizer/cities/tokyo/...`
- Create: `visualizer/cities/amsterdam/...`
- Create: `visualizer/cities/madison/...`

**Context:** Cuatro runs del pipeline, una por ciudad. Cada uno toma ~5-15 min dependiendo de tamaño y salud de Overpass. **Espaciar para no triggear rate limit.**

- [ ] **Step 1: Generate Madison (más chica primero, smoke test del pipeline)**

```bash
cd src
uv run extract-zoning --city madison
```

Expected: completes in ~3-8 min. Output:
- `visualizer/cities/madison/datos_zonificacion.js`
- `visualizer/cities/madison/manifest.json` con `modules.zoning`

Verify file size razonable (5-20MB esperable):
```bash
ls -lh "C:/Users/osyanne/Documents/Claude/Projects/Proyecto mineapolis/cs2-minneapolis-zoning/visualizer/cities/madison/datos_zonificacion.js"
```

- [ ] **Step 2: Generate Amsterdam**

```bash
cd src
uv run extract-zoning --city amsterdam
```

Expected: completes in ~5-10 min. Size ~10-25MB esperable.

- [ ] **Step 3: Generate Manhattan**

```bash
cd src
uv run extract-zoning --city manhattan
```

Expected: completes in ~10-15 min (denso). Size potencialmente 40-80MB.

**Si el archivo excede 100MB:** GH Pages no lo servirá. Mitigación: editar `cities.json` para reducir el bbox de Manhattan (ej. solo `[40.700, -74.020, 40.820, -73.960]` cubriendo Lower + Midtown), borrar el archivo generado, y re-correr.

- [ ] **Step 4: Generate Tokyo (último, mayor riesgo de tag mismatch)**

```bash
cd src
uv run extract-zoning --city tokyo
```

Expected: completes in ~10-15 min. Size ~20-50MB.

**Smoke check de clasificación japonesa:** abrir `datos_zonificacion.js` con un editor y buscar features. Si la mayoría caen en una sola categoría (típicamente "uncategorized" o "res_low_house" por convenciones JP distintas), flaggear como "tag mismatch detectado en Tokyo" y crear un Issue para revisar classifiers — no bloquea Phase 1 pero documenta el riesgo del spec §9.1.

- [ ] **Step 5: Verify all 4 manifests exist**

```bash
ls "C:/Users/osyanne/Documents/Claude/Projects/Proyecto mineapolis/cs2-minneapolis-zoning/visualizer/cities/"
```

Expected: `manhattan/`, `tokyo/`, `amsterdam/`, `madison/`, `minneapolis/` (5 directorios). Cada uno con `datos_zonificacion.js` + `manifest.json`. Solo `minneapolis/` debe tener además `datos_vial.js` y `datos_servicios.js`.

- [ ] **Step 6: Commit los prebuilts**

```bash
git add visualizer/cities/
git commit -m "feat: prebuilts zoning para Manhattan, Tokyo, Amsterdam, Madison

4 ciudades nuevas zoning-only. Manifests generados. Minneapolis preserva
los 3 módulos. Total storage del pack: ~Y MB (rellenar tras Step 5).

Caveats verificables:
- Tokyo: revisar si tag mismatch JP/US afecta clasificación (Issue futuro
  si feedback de smoke test lo confirma).
- Manhattan: si dataset >50MB considerar splittear.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 10: Landing page generator (`src/shared/landing.py`)

**Files:**
- Create: `src/shared/landing.py` — script `generate-landing`
- Create: `tests/shared/test_landing.py`
- Modify: `src/pyproject.toml` — agregar entry-point + bump version a 3.3.0

- [ ] **Step 1: Write failing test for landing generation**

Create `tests/shared/test_landing.py`:
```python
"""Tests del generador de landing (index.html)."""
import sys, os, json
from pathlib import Path
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from shared.landing import build_landing_html


def _city_entry(name="Test", country="USA", tagline="t"):
    return {
        "display_name": name, "country": country,
        "bbox": [44.86, -93.38, 45.05, -93.17],
        "center": [44.97, -93.27], "zoom": 12,
        "tagline": tagline, "locale": "es"
    }


def test_landing_html_has_one_card_per_city():
    cities = {
        "minneapolis": _city_entry("Minneapolis, MN"),
        "manhattan": _city_entry("Manhattan, NYC"),
    }
    manifests = {
        "minneapolis": {"modules": {"zoning": {"hash": "a", "features": 100},
                                     "vial": {"hash": "b", "features": 200},
                                     "services": {"hash": "c", "features": 50}}},
        "manhattan": {"modules": {"zoning": {"hash": "d", "features": 500}}},
    }
    html = build_landing_html(cities, manifests)
    # Una card por ciudad
    assert html.count('class="city-card"') == 2
    # Slugs en los links
    assert 'href="map.html?city=minneapolis"' in html
    assert 'href="map.html?city=manhattan"' in html
    # Display names
    assert "Minneapolis, MN" in html
    assert "Manhattan, NYC" in html


def test_landing_html_shows_module_badges():
    cities = {
        "minneapolis": _city_entry("Mpls"),
        "manhattan": _city_entry("Man"),
    }
    manifests = {
        "minneapolis": {"modules": {"zoning": {"hash":"a","features":1},
                                     "vial": {"hash":"b","features":1},
                                     "services": {"hash":"c","features":1}}},
        "manhattan": {"modules": {"zoning": {"hash":"d","features":1}}},
    }
    html = build_landing_html(cities, manifests)
    # Minneapolis: los 3 badges
    mpls_section = html[html.index("Mpls"):html.index("Man")]
    assert "Zoning" in mpls_section
    assert "Vial" in mpls_section
    assert "Servicios" in mpls_section
    # Manhattan: solo Zoning
    man_section = html[html.index("Man"):]
    assert "Zoning" in man_section
    assert "Vial" not in man_section
    assert "Servicios" not in man_section


def test_landing_html_shows_feature_counts():
    cities = {"madison": _city_entry("Madison")}
    manifests = {"madison": {"modules": {"zoning": {"hash":"x","features":12345}}}}
    html = build_landing_html(cities, manifests)
    assert "12" in html  # algún formato del count, ej. "12,345" o "12k"


def test_landing_html_handles_city_without_manifest():
    """Ciudad en registro pero sin manifest (ej. recién agregada, no extraída aún)."""
    cities = {"future_city": _city_entry("Future")}
    manifests = {}  # no entry
    html = build_landing_html(cities, manifests)
    assert "Future" in html
    # No crash; mostrar badge "Sin datos" o similar
    assert "Sin datos" in html or "pending" in html.lower()


def test_landing_html_includes_request_city_cta():
    cities = {"madison": _city_entry("Madison")}
    manifests = {"madison": {"modules": {"zoning": {"hash":"x","features":1}}}}
    html = build_landing_html(cities, manifests)
    # CTA link al Issue template
    assert "city-request" in html.lower() or "request" in html.lower()
    assert "github.com" in html.lower() or "issues/new" in html.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd src
uv run pytest ../tests/shared/test_landing.py -v
```

Expected: FAIL — `ImportError: cannot import name 'build_landing_html' from 'shared.landing'`

- [ ] **Step 3: Implement `src/shared/landing.py`**

Create `src/shared/landing.py`:
```python
"""Generador de landing page (visualizer/index.html) desde cities.json + manifests."""
import argparse
import html
import json
from pathlib import Path

from shared.registry import load_cities, load_manifest


# Mapping de slug de módulo → label display (para badges)
MODULE_LABELS = {
    "zoning": "Zoning",
    "vial": "Vial",
    "services": "Servicios",
}

REPO_URL = "https://github.com/Osyanne/cs2-minneapolis-osm-toolkit"
ISSUE_NEW_URL = f"{REPO_URL}/issues/new?template=city-request.yml"


def _format_count(n: int) -> str:
    """Format feature count humanizado: 12345 → '12.3k', 1500000 → '1.5M'."""
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}k"
    return str(n)


def _card_html(slug: str, entry: dict, manifest: dict | None) -> str:
    """Genera el <div class='city-card'> de una ciudad."""
    name = html.escape(entry["display_name"])
    country = html.escape(entry["country"])
    tagline = html.escape(entry["tagline"])

    if manifest is None or not manifest.get("modules"):
        badges_html = '<span class="badge badge-pending">Sin datos</span>'
        total = 0
    else:
        mods = manifest["modules"]
        badges_html = " ".join(
            f'<span class="badge">{html.escape(MODULE_LABELS.get(m, m))}</span>'
            for m in ["zoning", "vial", "services"]
            if m in mods
        )
        total = sum(d.get("features", 0) for d in mods.values())

    return f'''
    <a href="map.html?city={html.escape(slug)}" class="city-card">
      <div class="thumb"
           style="background-image: url('assets/thumbnails/{html.escape(slug)}.png')"></div>
      <div class="city-info">
        <h2>{name}</h2>
        <p class="country">{country}</p>
        <p class="tagline">{tagline}</p>
        <div class="badges">{badges_html}</div>
        <p class="stats">{_format_count(total)} features</p>
      </div>
    </a>'''


def build_landing_html(cities: dict, manifests: dict) -> str:
    """Construye el HTML de la landing completo.

    Args:
        cities: dict {slug: entry} desde load_cities()
        manifests: dict {slug: manifest_dict or None} (puede faltar entries)
    """
    cards = "\n".join(
        _card_html(slug, entry, manifests.get(slug))
        for slug, entry in cities.items()
    )

    return f'''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CS2 OSM Toolkit — Featured Cities</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0; padding: 0;
      font-family: -apple-system, BlinkMacSystemFont, sans-serif;
      background: #0d1117; color: #c9d1d9;
      min-height: 100vh;
    }}
    header {{
      padding: 3rem 1rem 2rem; text-align: center;
      border-bottom: 1px solid #30363d;
    }}
    header h1 {{ margin: 0; font-size: 2rem; }}
    header p {{ margin: 0.5rem 0; color: #8b949e; }}
    main {{
      max-width: 1400px; margin: 0 auto; padding: 2rem 1rem;
    }}
    .cities-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 1.5rem;
    }}
    .city-card {{
      display: block; text-decoration: none; color: inherit;
      background: #161b22; border: 1px solid #30363d;
      border-radius: 6px; overflow: hidden;
      transition: transform 0.15s, border-color 0.15s;
    }}
    .city-card:hover {{ transform: translateY(-2px); border-color: #58a6ff; }}
    .thumb {{
      height: 180px;
      background-size: cover; background-position: center;
      background-color: #21262d;
    }}
    .city-info {{ padding: 1rem; }}
    .city-info h2 {{ margin: 0 0 0.25rem; font-size: 1.1rem; }}
    .country {{ margin: 0; color: #8b949e; font-size: 0.85rem; }}
    .tagline {{ margin: 0.5rem 0; font-size: 0.9rem; }}
    .badges {{ display: flex; gap: 0.3rem; flex-wrap: wrap; margin: 0.5rem 0; }}
    .badge {{
      background: #1f6feb; color: white;
      padding: 0.1rem 0.5rem; border-radius: 3px;
      font-size: 0.75rem;
    }}
    .badge-pending {{ background: #6e7681; }}
    .stats {{ margin: 0.5rem 0 0; color: #8b949e; font-size: 0.8rem; }}
    footer {{
      max-width: 1400px; margin: 3rem auto 2rem; padding: 0 1rem;
      text-align: center; color: #8b949e; font-size: 0.9rem;
    }}
    footer a {{ color: #58a6ff; }}
  </style>
</head>
<body>
  <header>
    <h1>🏙 CS2 OSM Toolkit</h1>
    <p>Mapas de zonificación reales para creadores de Cities: Skylines 2</p>
  </header>
  <main>
    <div class="cities-grid">
{cards}
    </div>
  </main>
  <footer>
    <p>
      ¿Tu ciudad no está? 
      <a href="{ISSUE_NEW_URL}" target="_blank" rel="noopener">Pedila acá</a>
      · 
      <a href="{REPO_URL}" target="_blank" rel="noopener">Código en GitHub</a>
    </p>
  </footer>
</body>
</html>
'''


def main():
    parser = argparse.ArgumentParser(
        description="Generate landing index.html from cities.json + manifests"
    )
    parser.add_argument(
        "--cities-file", default=None,
        help="Path a cities.json (default: <repo_root>/cities.json)",
    )
    parser.add_argument(
        "--visualizer-root", default=None,
        help="Path a visualizer/ (default: <repo_root>/visualizer)",
    )
    parser.add_argument(
        "--out", default=None,
        help="Path al index.html de salida (default: <visualizer_root>/index.html)",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    cities_file = Path(args.cities_file) if args.cities_file else repo_root / "cities.json"
    vis_root = Path(args.visualizer_root) if args.visualizer_root else repo_root / "visualizer"
    out_path = Path(args.out) if args.out else vis_root / "index.html"

    cities = load_cities(cities_file)
    manifests = {slug: load_manifest(vis_root, slug) for slug in cities}

    html_content = build_landing_html(cities, manifests)
    out_path.write_text(html_content, encoding="utf-8")

    # Copiar cities.json a visualizer/ — necesario porque GH Pages sirve
    # solo desde /visualizer (no puede acceder a ../cities.json).
    # El root cities.json sigue siendo source of truth; este es deployment artifact.
    deployed_registry = vis_root / "cities.json"
    deployed_registry.write_text(
        json.dumps(cities, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print(f"Landing generada: {out_path}")
    print(f"Registro deployado: {deployed_registry}")
    print(f"Cities incluidas: {sorted(cities.keys())}")
```

- [ ] **Step 4: Add entry-point to `src/pyproject.toml`**

In `src/pyproject.toml`, find the `[project.scripts]` block:
```toml
[project.scripts]
extract-zoning = "zoning.extract:main"
extract-vial   = "vial.extract:main"
extract-services = "services.extract:main"
```

Add the new entry:
```toml
[project.scripts]
extract-zoning = "zoning.extract:main"
extract-vial   = "vial.extract:main"
extract-services = "services.extract:main"
generate-landing = "shared.landing:main"
```

Also bump version:
```toml
# Antes:
version = "3.1.0"
# Después:
version = "3.3.0"
```

- [ ] **Step 5: Reinstall package so entry-point is registered**

```bash
cd src
uv sync
```

Expected: re-sync sin errores.

- [ ] **Step 6: Run tests to verify they pass**

```bash
cd src
uv run pytest ../tests/shared/test_landing.py -v
```

Expected: PASS — 5 tests passed

- [ ] **Step 7: Commit**

```bash
git add src/shared/landing.py src/pyproject.toml tests/shared/test_landing.py
git commit -m "feat(landing): script generate-landing — index.html desde cities.json

Genera la landing page de 5 cards a partir del registro + manifests
per-city. Badges de módulos disponibles (zoning/vial/services) y feature
counts. CTA al Issue template para city requests. Dark theme con CSS
inline (sin frameworks). Version bump 3.1.0 → 3.3.0. Tests: 5 nuevos.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 11: Refactor visualizer (`index.html` → `map.html`, multi-city)

**Files:**
- Modify (rename): `visualizer/index.html` → `visualizer/map.html`
- Modify (heavy refactor): `visualizer/map.html`

**Context:** Este es el task más grande del plan (~300 líneas modificadas). El visualizer actual es single-city hardcoded a Mpls. Refactor: leer `?city=`, fetch `cities.json` + `manifest.json`, inyectar scripts dinámicamente, eliminar código de live-Overpass fallback (~200 líneas menos), actualizar Layer Control para ocultar capas no presentes.

**Smoke-test obligatorio:** Después del refactor, verificar manualmente que las 5 ciudades cargan correctamente.

- [ ] **Step 1: Rename `index.html` → `map.html` (git mv para preservar history)**

```bash
git mv "C:/Users/osyanne/Documents/Claude/Projects/Proyecto mineapolis/cs2-minneapolis-zoning/visualizer/index.html" \
       "C:/Users/osyanne/Documents/Claude/Projects/Proyecto mineapolis/cs2-minneapolis-zoning/visualizer/map.html"
```

- [ ] **Step 2: Refactor — parse `?city=` from URL al top del `<script>` principal**

Open `visualizer/map.html`. Find la línea ~292 donde está `const BBOX = "44.86,-93.38,45.05,-93.17";` (la constante hardcoded). Reemplazar el bloque inicial del script principal con:

```html
<script>
// ════════════════════════════════════════════════════════════════════
// Multi-city loader — lee ?city=<slug> de URL, fetch cities.json +
// manifest.json, inyecta scripts de los módulos presentes.
// ════════════════════════════════════════════════════════════════════

const params = new URLSearchParams(window.location.search);
const CITY_SLUG = params.get("city");

if (!CITY_SLUG) {
  // Sin parámetro → redirect a landing
  window.location.replace("index.html");
  // Halt todo el script
  throw new Error("no city slug, redirecting to landing");
}

let CITY_META = null;       // entry de cities.json
let CITY_MANIFEST = null;   // manifest.json per-city

async function bootstrap() {
  try {
    // 1. cities.json — copia deployada por generate-landing a visualizer/cities.json
    //    (el original vive en repo root pero GH Pages no puede acceder a ../cities.json)
    const cities = await (await fetch("cities.json")).json();
    if (!(CITY_SLUG in cities)) {
      window.location.replace("index.html");
      return;
    }
    CITY_META = cities[CITY_SLUG];

    // 2. manifest.json
    const manifestResp = await fetch(`cities/${CITY_SLUG}/manifest.json`);
    if (!manifestResp.ok) {
      showError(`City data corrupted: manifest.json missing for ${CITY_SLUG}`);
      return;
    }
    CITY_MANIFEST = await manifestResp.json();

    // 3. Inyectar scripts solo para módulos presentes
    const modules = Object.keys(CITY_MANIFEST.modules || {});
    const moduleToFile = {
      zoning: "datos_zonificacion.js",
      vial: "datos_vial.js",
      services: "datos_servicios.js",
    };
    await Promise.all(modules.map(m => {
      const hash = CITY_MANIFEST.modules[m].hash;
      const src = `cities/${CITY_SLUG}/${moduleToFile[m]}?v=${hash}`;
      return loadScript(src);
    }));

    // 4. Renderizar (mismo código de antes, ahora usa CITY_META y los globals
    //    DATA_ZONING / DATA_VIAL / DATA_SERVICES que se setearon)
    renderMap();
  } catch (e) {
    showError(`Failed to load city: ${e.message}`);
  }
}

function loadScript(src) {
  return new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = src;
    s.onload = resolve;
    s.onerror = () => reject(new Error(`Failed to load ${src}`));
    document.body.appendChild(s);
  });
}

function showError(msg) {
  document.body.innerHTML = `
    <div style="padding: 2rem; font-family: sans-serif; color: #c9d1d9; background: #0d1117; min-height: 100vh;">
      <h1>⚠ Error</h1>
      <p>${msg}</p>
      <p><a href="index.html" style="color: #58a6ff;">← Volver a landing</a> · 
         <a href="https://github.com/Osyanne/cs2-minneapolis-osm-toolkit/issues/new" 
            style="color: #58a6ff;" target="_blank">Report issue</a></p>
    </div>`;
}
</script>
```

**Sobre el path de `cities.json`:** GitHub Pages se sirve desde `/visualizer` (no puede acceder a `../cities.json`). Por eso `generate-landing` (Task 10) escribe una copia a `visualizer/cities.json` cuando se ejecuta. El root `cities.json` sigue siendo source of truth del pipeline; el de `visualizer/` es deployment artifact y NO se edita a mano — siempre se regenera con `generate-landing`.

- [ ] **Step 3: Refactor — el código de rendering pasa a `renderMap()`**

Todo el código existente entre la inicialización de Leaflet (`L.map(...)`) y el final del script principal va dentro de `function renderMap() { ... }`. Las referencias a `BBOX` se reemplazan por `bboxFromMeta(CITY_META.bbox)`:

```javascript
function renderMap() {
  // BBOX y bounds desde el registro
  const [s, w, n, e] = CITY_META.bbox;
  const BBOX = `${s},${w},${n},${e}`;       // si algo del código viejo aún lo usa
  const BOUNDS = [[s, w], [n, e]];
  const CENTER = CITY_META.center;
  const ZOOM = CITY_META.zoom;

  // Actualizar title + footer desde metadata
  document.title = `CS2 OSM Toolkit — ${CITY_META.display_name}`;
  document.querySelector(".logo").textContent = `🏙 ${CITY_META.display_name}`;
  const titleCtrl = document.getElementById("title-ctrl");
  if (titleCtrl) titleCtrl.textContent = `🗺 ${CITY_META.display_name}`;

  // Mapa
  const map = L.map("map", { preferCanvas: true }).setView(CENTER, ZOOM);
  map.setMaxBounds(BOUNDS);

  // ... resto del código existente de Leaflet (basemap, layer groups, etc.)
  // ... pero SOLO procesar los módulos que existieron en el manifest:

  const hasZoning = !!(CITY_MANIFEST.modules?.zoning) && typeof DATA_ZONING !== "undefined";
  const hasVial = !!(CITY_MANIFEST.modules?.vial) && typeof DATA_VIAL !== "undefined";
  const hasServices = !!(CITY_MANIFEST.modules?.services) && typeof DATA_SERVICES_POLYGONS !== "undefined";

  if (hasZoning) {
    // ... código existente que renderiza zoning ...
  }
  if (hasVial) {
    renderVialOverlay();  // función ya existente
  }
  if (hasServices) {
    // ... código existente de services ...
  }

  // Layer Control + leyenda: solo añadir secciones para módulos cargados.
  // Ejemplo:
  if (hasZoning) addZoningLegendSection();
  if (hasVial) addVialLegendSection();
  if (hasServices) addServicesLegendSection();
}

// Lanzar todo
bootstrap();
</script>
```

**Esto requiere bracketear el código zoning/vial/services existente con condiciones `if (hasX)`.** El refactor concreto:
1. Identificar dónde arranca el código de cada módulo (buscar comentarios tipo `// === ZONING ===`, `// === VIAL ===`, `// === SERVICES ===`).
2. Envolver cada bloque dentro de `if (hasX) { ... }`.
3. Mover toda la lógica que dependía de `BBOX` constante para que use `CITY_META.bbox`.

- [ ] **Step 4: Eliminar el código de live-Overpass fallback**

Buscar y borrar todas las referencias a fetch directo a Overpass desde el browser (los inline queries `[out:json][timeout:90]...`). El spec § 4 dice "Code path live-Overpass en visualizer: Eliminado (no oculto) — ~200 líneas menos".

Las funciones típicas a eliminar:
- `loadFromOverpass()` o similar
- Los objetos `QUERIES` con strings inline de Overpass
- El fallback path en `loadAll()` que dispara Overpass si no hay prebuilt

**Cuidado:** No borrar el código que renderiza datos ya cargados — solo el que va a Overpass.

- [ ] **Step 5: Smoke test local de Minneapolis (manualmente en browser)**

Abrir un servidor estático local apuntando a `visualizer/`:
```bash
cd "C:/Users/osyanne/Documents/Claude/Projects/Proyecto mineapolis/cs2-minneapolis-zoning/visualizer"
python -m http.server 8000
```

Luego en browser: `http://localhost:8000/map.html?city=minneapolis`

Verificar:
- [ ] Mapa carga centrado en Minneapolis con bounds correctos
- [ ] Las 3 capas (zoning, vial, services) cargan
- [ ] Layer Control muestra las 3 secciones (Zonificación / Vías / Servicios)
- [ ] Leyenda muestra los 3 grupos
- [ ] Popups funcionan en zoning, vial y services
- [ ] Console sin errores rojos

- [ ] **Step 6: Smoke test local de Manhattan (zoning-only)**

`http://localhost:8000/map.html?city=manhattan`

Verificar:
- [ ] Mapa carga centrado en Manhattan
- [ ] SOLO zoning aparece (sin vial, sin services)
- [ ] Layer Control NO muestra secciones Vías ni Servicios
- [ ] Leyenda NO muestra grupos Vías ni Servicios
- [ ] No console errors (especialmente ningún 404 por `datos_vial.js`)

- [ ] **Step 7: Smoke test de las otras 3 ciudades**

Para tokyo, amsterdam, madison: mismo check que Manhattan. Anotar cualquier issue visual (colores raros, polígonos cortados, etc.).

- [ ] **Step 8: Smoke test del caso "slug inválido"**

`http://localhost:8000/map.html?city=atlantis`

Verificar: redirect transparente a `index.html` (que aún no existe formalmente — generaremos en Task 12; por ahora cae a una landing default del server).

- [ ] **Step 9: Commit**

```bash
git add visualizer/map.html
git commit -m "refactor(visualizer): map.html multi-city, manifest-driven, sin live-Overpass

- index.html renamed to map.html (la nueva index.html será landing en T12)
- Lee ?city=<slug>, fetch cities.json + manifest.json
- Script injection dinámica solo para módulos presentes
- Layer Control + leyenda ocultan secciones de módulos faltantes
- Title/bounds/center desde cities.json
- ELIMINADO ~200 líneas de live-Overpass fallback (decisión consciente:
  solo prebuilt mode)

Smoke tests pasaron: Mpls (3 modules), Manhattan/Tokyo/Amsterdam/Madison
(zoning-only).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 12: Generate the landing page (`visualizer/index.html`)

**Files:**
- Create (vía script): `visualizer/index.html`

- [ ] **Step 1: Run `generate-landing`**

```bash
cd src
uv run generate-landing
```

Expected output:
```
Landing generada: ...\visualizer\index.html
Registro deployado: ...\visualizer\cities.json
Cities incluidas: ['amsterdam', 'madison', 'manhattan', 'minneapolis', 'tokyo']
```

- [ ] **Step 2: Smoke test landing en browser**

`http://localhost:8000/` (el server de Task 11 sigue corriendo, o re-lanzarlo).

Verificar:
- [ ] Se ven 5 cards
- [ ] Cada card tiene nombre, country, tagline
- [ ] Mpls muestra 3 badges (Zoning · Vial · Servicios)
- [ ] Las otras 4 muestran solo badge "Zoning"
- [ ] Feature counts visibles
- [ ] Click en una card → navega a `map.html?city=<slug>` y carga ese mapa
- [ ] Thumbnails NO se muestran aún (son fondo gris) — se agregan en Task 13
- [ ] CTA "Pedila acá" linkea al Issue template (URL existe aunque template aún no — Task 14)

- [ ] **Step 3: Commit**

```bash
git add visualizer/index.html visualizer/cities.json
git commit -m "feat(landing): visualizer/index.html + cities.json deployment artifact

Genera con \`uv run generate-landing\`. Cards muestran badges de módulos
disponibles (Mpls: 3, otras: 1). Thumbnails placeholders (asset PNGs vienen
en T13). CTA al Issue template (template viene en T14). cities.json se
copia a visualizer/ porque GH Pages no puede acceder a ../cities.json.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 13: Generate thumbnail PNGs (5 cities)

**Files:**
- Create: `visualizer/assets/thumbnails/minneapolis.png`
- Create: `visualizer/assets/thumbnails/manhattan.png`
- Create: `visualizer/assets/thumbnails/tokyo.png`
- Create: `visualizer/assets/thumbnails/amsterdam.png`
- Create: `visualizer/assets/thumbnails/madison.png`

**Context:** Screenshots manuales del visualizer para cada ciudad. Apuntar a 16:9 o 4:3, ~600×400px target, comprimir a PNG ~150-250KB c/u.

- [ ] **Step 1: Create thumbnails directory**

```bash
mkdir -p "C:/Users/osyanne/Documents/Claude/Projects/Proyecto mineapolis/cs2-minneapolis-zoning/visualizer/assets/thumbnails"
```

- [ ] **Step 2: For each city, capture screenshot**

Para cada slug en `["minneapolis", "manhattan", "tokyo", "amsterdam", "madison"]`:

1. Abrir `http://localhost:8000/map.html?city=<slug>` en browser
2. Esperar que cargue completamente (todas las capas visibles)
3. Para Mpls: dejar zoning + vial visibles, services apagado (para no saturar)
4. Para las otras: solo zoning está disponible
5. Capturar screenshot del área del mapa (~600×400 o similar). Recortar header/leyenda si conviene.
6. Guardar como `visualizer/assets/thumbnails/<slug>.png`
7. Comprimir si >300KB (usar https://tinypng.com o equivalente)

**Tip:** En Chrome DevTools, modo responsive → setear viewport a 600×400 para captura uniforme.

- [ ] **Step 3: Verify thumbnails load in landing**

Recargar `http://localhost:8000/` y verificar que las 5 cards ahora muestran imágenes (no fondo gris).

- [ ] **Step 4: Commit**

```bash
git add visualizer/assets/thumbnails/
git commit -m "assets: 5 thumbnail PNGs para landing cards

Screenshots manuales del visualizer para cada ciudad, ~600x400px,
comprimidos a ~150-250KB c/u. Total ~1MB.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 14: GitHub Issue template (`city-request.yml`)

**Files:**
- Create: `.github/ISSUE_TEMPLATE/city-request.yml`

- [ ] **Step 1: Create the directory if needed**

```bash
mkdir -p "C:/Users/osyanne/Documents/Claude/Projects/Proyecto mineapolis/cs2-minneapolis-zoning/.github/ISSUE_TEMPLATE"
```

- [ ] **Step 2: Write the template**

Create `.github/ISSUE_TEMPLATE/city-request.yml`:
```yaml
name: City Request
description: Request a new city for the CS2 OSM Toolkit Featured Cities Pack
title: "[City Request] "
labels: ["city-request"]
body:
  - type: markdown
    attributes:
      value: |
        ¡Gracias por pedir una ciudad! Por favor llená todos los campos.
        Tiempo estimado para agregar (zoning-only): 30-60 min después de aceptada.

  - type: input
    id: display_name
    attributes:
      label: City display name
      description: "Nombre completo de la ciudad como debería mostrarse (ej. 'São Paulo, Brazil')"
      placeholder: "Madison, WI"
    validations:
      required: true

  - type: input
    id: slug
    attributes:
      label: Proposed slug
      description: "Identificador URL: lowercase, solo letras/números/guiones bajos, sin acentos (ej. 'sao_paulo', 'madison')"
      placeholder: "madison"
    validations:
      required: true

  - type: input
    id: country
    attributes:
      label: Country / region
      placeholder: "USA, Japan, Netherlands, etc."
    validations:
      required: true

  - type: input
    id: bbox
    attributes:
      label: Bounding box
      description: |
        Formato `south,west,north,east` (4 floats). 
        Usá [bboxfinder.com](http://bboxfinder.com/) para obtenerlo visualmente.
        Recomendado: 10-20 km de lado, foco en downtown + áreas inmediatas.
      placeholder: "43.030,-89.500,43.130,-89.300"
    validations:
      required: true

  - type: textarea
    id: motivation
    attributes:
      label: ¿Por qué esta ciudad?
      description: "Urban form interesante, builder popular que la pidió, demanda local, etc."
      placeholder: "Capital state pequeña con isthmus + lagos, urban form única."
    validations:
      required: true

  - type: checkboxes
    id: modules
    attributes:
      label: Módulos solicitados
      description: |
        Default: solo zoning (cubre 95% del valor del toolkit, rápido de generar).
        Vial/services son ampliación on-demand — marcarlos solo si tu uso requiere infraestructura específica.
      options:
        - label: Zoning (siempre)
          required: true
        - label: Vial (opcional — agrega ~30 min al pipeline)
        - label: Services (opcional — agrega ~30 min)
```

- [ ] **Step 3: Verify yaml is valid (no formal lint, but visual inspection)**

Open the file. Verify:
- 2-space indent consistente
- `validations` con `required: true` en campos obligatorios
- No tabs

- [ ] **Step 4: Commit**

```bash
git add .github/ISSUE_TEMPLATE/city-request.yml
git commit -m "feat(github): Issue template para City Request

Form structured con display_name, slug, country, bbox, motivación,
checkboxes de módulos. Default: zoning-only (consistente con scope
Phase 1). El CTA del landing apunta acá.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 15: Update READMEs (en + es) — v3.3 + multi-city

**Files:**
- Modify: `README.md`
- Modify: `README.es.md`

**Context:** Bump badge a v3.3 + agregar sección "Featured Cities" + nota sobre deferred rename.

- [ ] **Step 1: Read current README.md to understand structure**

Open `README.md`. Look for:
- Top badge section (probably mentions version)
- Quickstart section
- A list of modules / features

- [ ] **Step 2: Update version badge in `README.md`**

Find any reference to `v3.1` or `v3.2` o `3.1.0` y reemplazar con `v3.3`/`3.3.0` donde corresponda en el header.

- [ ] **Step 3: Add "Featured Cities" section to `README.md`**

Después del header/intro, agregar (o reemplazar si existe sección similar):

```markdown
## 🌆 Featured Cities (v3.3)

The toolkit now supports **5 cities** out-of-the-box, accessible via the hosted viewer at:

**https://osyanne.github.io/cs2-minneapolis-osm-toolkit/**

| City | Country | Modules |
|------|---------|---------|
| Minneapolis, MN | USA | Zoning + Vial + Services (hero, fully featured) |
| Manhattan, NYC | USA | Zoning |
| Tokyo (Central) | Japan | Zoning |
| Amsterdam | Netherlands | Zoning |
| Madison, WI | USA | Zoning |

Vial + services for the 4 newer cities are **on-demand**: open a [City Request issue](https://github.com/Osyanne/cs2-minneapolis-osm-toolkit/issues/new?template=city-request.yml) requesting them, and we'll generate.

### Adding your city

Open a [City Request issue](https://github.com/Osyanne/cs2-minneapolis-osm-toolkit/issues/new?template=city-request.yml) with the bbox + name. We'll generate the zoning prebuilt and publish (~30-60 min turnaround when active).

### Repo rename — pending

This repo will eventually be renamed `cs2-osm-toolkit` to reflect multi-city support. Rename is deferred until current Reddit traffic decays. Existing links and clones continue to work via GitHub redirects.
```

- [ ] **Step 4: Mirror same changes in `README.es.md`**

Translate the Featured Cities section to Spanish, add to README.es.md in equivalent position. Bump version badge.

- [ ] **Step 5: Run a quick sanity check**

```bash
grep -n "v3.1\|v3.2\|3\.1\.0\|3\.2\.0" "C:/Users/osyanne/Documents/Claude/Projects/Proyecto mineapolis/cs2-minneapolis-zoning/README.md" \
                                         "C:/Users/osyanne/Documents/Claude/Projects/Proyecto mineapolis/cs2-minneapolis-zoning/README.es.md"
```

Expected: any matches found should be in changelog/history sections (legitimate references to past versions). Header/current-state references should all say v3.3.

- [ ] **Step 6: Commit**

```bash
git add README.md README.es.md
git commit -m "docs: READMEs v3.3 — Featured Cities Pack section

Añade sección \"Featured Cities\" en ambos READMEs (en + es) listando las
5 ciudades con sus módulos disponibles. Link al hosted viewer GitHub
Pages. CTA al Issue template para nuevas ciudades. Nota sobre rename
diferido del repo.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 16: Update `METHODOLOGY.md`

**Files:**
- Modify: `METHODOLOGY.md`

- [ ] **Step 1: Read current METHODOLOGY.md to identify the latest section number**

```bash
grep -n "^## Section\|^## Sección\|^### Session" "C:/Users/osyanne/Documents/Claude/Projects/Proyecto mineapolis/cs2-minneapolis-zoning/METHODOLOGY.md" | tail -10
```

Identify the next available section number. The memory says it had "13 secciones detalladas" antes, vial added 14, services 15. So next is **§16**.

- [ ] **Step 2: Add Section 16 — Multi-city architecture**

Append to `METHODOLOGY.md`:

```markdown

---

## Sección 16 — Multi-city architecture (v3.3, mayo 2026)

Tras Sesiones 1-3 con scope Minneapolis-only, el toolkit se generalizó para
soportar múltiples ciudades via Featured Cities Pack.

### Cambios estructurales

- **Registro `cities.json`** (raíz del repo): single source of truth para qué
  ciudades existen, con bbox + center + zoom + tagline + locale por entry.
- **Manifest per-city** (`visualizer/cities/<slug>/manifest.json`): declara qué
  módulos están generados para esa ciudad y sus hashes (sha256 trunco para
  cache busting). Se actualiza automáticamente cada vez que un extract corre.
- **Pipeline `--city` flag**: los 3 extracts (zoning/vial/services) aceptan
  `--city <slug>` que resuelve bbox desde el registro. `--bbox X --slug Y`
  queda como escape hatch para ciudades no registradas.
- **Visualizer refactor**: `index.html` legacy → `map.html` (lee `?city=`,
  inyecta scripts dinámicamente desde `manifest.json`). Nueva `index.html` es
  landing page generada por `generate-landing` script.

### Scope Phase 1

- Minneapolis preserva los 3 módulos (hero/legacy).
- 4 ciudades nuevas (Manhattan, Tokyo, Amsterdam, Madison) entran solo con
  zoning. Vial y services on-demand vía GitHub Issues post-launch.

### Deferreds (Phase 2+)

- Rename del repo a `cs2-osm-toolkit` (espera caída de tráfico Reddit v3.2).
- Heightmap generation pipeline (Phase 3 — valida demanda con Featured
  Cities primero).
- Promoción de las 4 ciudades a fully-featured (cuando acumulen 5+ requests
  por vial/services).

Ver spec: `docs/specs/2026-05-17-featured-cities-pack-design.md`
Ver plan: `docs/plans/2026-05-17-featured-cities-pack.md`
```

- [ ] **Step 3: Update the header date / version reference**

Si el header de METHODOLOGY.md dice "as of Session 3" o similar, actualizar a "as of v3.3 — Featured Cities Pack (mayo 2026)".

- [ ] **Step 4: Commit**

```bash
git add METHODOLOGY.md
git commit -m "docs(methodology): §16 Multi-city architecture (v3.3)

Documenta cambios estructurales del Featured Cities Pack: registro
cities.json, manifest per-city, --city flag en pipeline, visualizer
refactor. Incluye scope Phase 1 y deferreds (rename, heightmap,
promoción a fully-featured).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 17: Enable GitHub Pages + verify deployment

**Files:**
- (Configuración en GitHub UI, no en el repo)

**Context:** Habilitar Pages servido desde branch `main` directorio `/visualizer`. PERO estamos en `feature/featured-cities-pack`. Plan: hacer un push de prueba de la feature branch para validar Pages config funciona, luego mergear a main en Task 18.

**Alternativa más segura:** habilitar Pages servido desde `feature/featured-cities-pack` primero (rama temporal), verificar, luego cuando se mergee a main cambiar la config a `main`.

- [ ] **Step 1: Push the feature branch to remote**

```bash
git -C "C:/Users/osyanne/Documents/Claude/Projects/Proyecto mineapolis/cs2-minneapolis-zoning" push -u origin feature/featured-cities-pack
```

Expected: branch pushed sin errores.

- [ ] **Step 2: Enable GitHub Pages via the GitHub UI**

Open `https://github.com/Osyanne/cs2-minneapolis-osm-toolkit/settings/pages` in browser.

Config:
- Source: **Deploy from a branch**
- Branch: **feature/featured-cities-pack**
- Folder: **/visualizer**

Save.

GitHub will show a "Your site is live at https://osyanne.github.io/cs2-minneapolis-osm-toolkit/" después de ~1-2 min.

- [ ] **Step 3: Verify deployment**

Open `https://osyanne.github.io/cs2-minneapolis-osm-toolkit/` (puede tardar 1-5 min en propagar).

Expected: landing page con 5 cards.

- [ ] **Step 4: Verify resource fetches work**

The `map.html` does `fetch("cities.json")` (mismo dir, copia deployada por generate-landing).

Open browser DevTools → Network tab → load `https://osyanne.github.io/cs2-minneapolis-osm-toolkit/map.html?city=minneapolis`.

Verify:
- Request a `https://osyanne.github.io/cs2-minneapolis-osm-toolkit/cities.json` → status **200** (no 404)
- Request a `https://osyanne.github.io/cs2-minneapolis-osm-toolkit/cities/minneapolis/manifest.json` → **200**
- 3 requests a `https://osyanne.github.io/cs2-minneapolis-osm-toolkit/cities/minneapolis/datos_*.js?v=<hash>` → todos **200**

Si alguno retorna 404: verificar que `visualizer/cities.json` existe (debió generarse en Task 12 con `generate-landing`). Si no existe, correr `cd src && uv run generate-landing && git add visualizer/cities.json && git commit -m "fix: deploy cities.json" && git push`.

- [ ] **Step 5: Smoke test all 5 cities on deployed URL**

For each slug:
- `https://osyanne.github.io/cs2-minneapolis-osm-toolkit/map.html?city=minneapolis`
- `https://osyanne.github.io/cs2-minneapolis-osm-toolkit/map.html?city=manhattan`
- `https://osyanne.github.io/cs2-minneapolis-osm-toolkit/map.html?city=tokyo`
- `https://osyanne.github.io/cs2-minneapolis-osm-toolkit/map.html?city=amsterdam`
- `https://osyanne.github.io/cs2-minneapolis-osm-toolkit/map.html?city=madison`

Verify cada uno carga, console limpia, mapa renderea.

- [ ] **Step 6: Verify slug-inválido redirect**

`https://osyanne.github.io/cs2-minneapolis-osm-toolkit/map.html?city=atlantis`

Expected: redirect a landing.

- [ ] **Step 7: Si todo OK, commit final note in plan progress**

(No git commit needed for this step — solo verificación.)

---

## Task 18: Open PR `feature/featured-cities-pack` → main

**Files:**
- (Operación en GitHub, no en el repo)

- [ ] **Step 1: Check all changes are committed locally**

```bash
git -C "C:/Users/osyanne/Documents/Claude/Projects/Proyecto mineapolis/cs2-minneapolis-zoning" status
```

Expected: clean working tree on `feature/featured-cities-pack`.

- [ ] **Step 2: Push any remaining commits**

```bash
git -C "C:/Users/osyanne/Documents/Claude/Projects/Proyecto mineapolis/cs2-minneapolis-zoning" push
```

- [ ] **Step 3: Open PR via `gh` CLI**

```bash
gh pr create --title "Featured Cities Pack (v3.3) — multi-city support" --body "$(cat <<'EOF'
## Summary

- Pivot del toolkit: Minneapolis-specific → multi-city (5 ciudades)
- 4 ciudades nuevas (Manhattan, Tokyo, Amsterdam, Madison) zoning-only
- Minneapolis preserva los 3 módulos (hero)
- Registro `cities.json` + `manifest.json` per-city
- Visualizer refactor: landing (index.html) + viewer multi-city (map.html)
- GH Pages activo en `https://osyanne.github.io/cs2-minneapolis-osm-toolkit/`

Ver spec completo: `docs/specs/2026-05-17-featured-cities-pack-design.md`
Ver plan ejecutado: `docs/plans/2026-05-17-featured-cities-pack.md`

## Test plan

- [x] 145+ pytest tests pasando (127 históricos + 18 nuevos)
- [x] Smoke test local de las 5 ciudades
- [x] Smoke test del deploy en GH Pages (las 5 URLs)
- [x] Slug inválido → redirect a landing
- [x] Mpls muestra 3 módulos, otras 4 solo zoning (Layer Control oculta secciones missing)
- [ ] Reviewer: verificar visualmente al menos 2 ciudades en el deploy

## Out of scope (deferred — ver §10 del spec)

- Heightmap generation (Phase 3)
- Vial+services para las 4 ciudades nuevas
- Rename del repo
- Backend / SaaS / monetización

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 4: After PR is open, switch GitHub Pages source to `main`**

Una vez el PR sea reviewed/merged a main, volver a `https://github.com/Osyanne/cs2-minneapolis-osm-toolkit/settings/pages`:

- Cambiar branch a **main**
- Folder: **/visualizer**
- Save

- [ ] **Step 5: Verify deployment on main**

Recargar `https://osyanne.github.io/cs2-minneapolis-osm-toolkit/`. Esperar 1-5 min.

Expected: misma landing + las 5 ciudades funcionan.

---

## Notas finales

- **Si Tokyo classifier sale roto** (Step 4 de Task 9): documentar como Issue separado tras Phase 1 launch, NO retrasar el deploy.
- **Si Manhattan zoning >100MB**: re-bbox a área más chica (Lower Manhattan + Midtown), re-generar, commit nuevo, push.
- **Si GH Pages se rompe en Task 17 Step 4**: rollback es trivial — revert el commit problemático y re-push.

Plan estimado total: **2-3 sesiones de trabajo** (~10-15h totales).
