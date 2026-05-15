# CS2 Minneapolis — Plan de Implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reparar el módulo de zonificación existente (bug crítico de densidad + colores CS2) y añadir tres nuevos módulos de extracción OSM para red vial, servicios urbanos y transporte público.

**Architecture:** Cada módulo sigue el mismo patrón que el existente: un script Python `extract_X.py` consulta Overpass API usando `overpass_client.py`, clasifica los elementos y escribe un archivo `datos_X.js` que carga el visualizador `visualizer/X/index.html`. Todos los módulos nuevos comparten `overpass_client.py` sin modificarlo.

**Tech Stack:** Python 3.11+, uv, requests, tqdm, Leaflet.js 1.9.4 (CDN), OpenStreetMap Overpass API

---

## Mapa de Archivos

```
src/
  classifiers.py          ← MODIFICAR: simplificar classify_residential, añadir classify_apartment
  cs2_zones.py            ← MODIFICAR: nueva query apartments, label mixed_res_com
  extract_zoning.py       ← MODIFICAR: pipeline con apartment buildings directos
  patch_colors.py         ← CREAR: script one-shot para actualizar colores en visualizer/index.html
  vial_queries.py         ← CREAR: queries Overpass para red vial
  extract_vial.py         ← CREAR: pipeline extracción vial
  services_queries.py     ← CREAR: queries Overpass para servicios urbanos
  extract_services.py     ← CREAR: pipeline extracción servicios
  transport_queries.py    ← CREAR: queries Overpass para transporte
  extract_transport.py    ← CREAR: pipeline extracción transporte
  pyproject.toml          ← MODIFICAR: añadir entry points nuevos scripts

tests/
  test_classifiers.py     ← CREAR: tests unitarios para classifiers.py
  test_queries.py         ← CREAR: tests de sanidad para los builders de queries

visualizer/
  index.html              ← MODIFICAR: colores actualizados a CS2 (via patch_colors.py)
  vial/
    index.html            ← CREAR: visualizador red vial
  services/
    index.html            ← CREAR: visualizador servicios
  transport/
    index.html            ← CREAR: visualizador transporte
```

---

## PARTE 1 — Reparar Módulo de Zonificación

---

### Task 1: Tests para classifiers.py

**Files:**
- Create: `tests/test_classifiers.py`

- [ ] **Step 1: Crear directorio tests e inicializar**

```bash
cd src
mkdir -p ../tests
touch ../tests/__init__.py
```

- [ ] **Step 2: Escribir los tests**

Crear `tests/test_classifiers.py`:

```python
"""Tests para classifiers.py — ejecutar con: cd src && uv run pytest ../tests/test_classifiers.py -v"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from classifiers import (
    classify_residential,
    classify_apartment_building,
    classify_commercial,
    classify_parking,
)


# ── classify_residential ────────────────────────────────────────────────────

def test_residential_low_density_default():
    """Un polígono landuse=residential sin datos de pisos → baja densidad."""
    assert classify_residential({}) == "low"

def test_residential_low_density_explicit_single_floor():
    assert classify_residential({"building:levels": "1"}) == "low"

def test_residential_medium_density_three_floors():
    assert classify_residential({"building:levels": "3"}) == "medium"

def test_residential_medium_density_townhouse():
    assert classify_residential({"building": "townhouse"}) == "medium"

def test_residential_high_density_five_floors():
    assert classify_residential({"building:levels": "5"}) == "high"

def test_residential_high_density_apartments_tag():
    assert classify_residential({"residential": "apartments"}) == "high"

def test_residential_high_density_condo():
    assert classify_residential({"residential": "condominium"}) == "high"


# ── classify_apartment_building ─────────────────────────────────────────────

def test_apartment_building_high_five_floors():
    assert classify_apartment_building({"building:levels": "5"}) == "high"

def test_apartment_building_high_ten_floors():
    assert classify_apartment_building({"building:levels": "10"}) == "high"

def test_apartment_building_medium_three_floors():
    assert classify_apartment_building({"building:levels": "3"}) == "medium"

def test_apartment_building_medium_four_floors():
    assert classify_apartment_building({"building:levels": "4"}) == "medium"

def test_apartment_building_low_no_levels():
    """Edificio de apartamentos sin dato de pisos → baja densidad por defecto."""
    assert classify_apartment_building({}) == "low"

def test_apartment_building_uses_levels_fallback():
    """Acepta 'levels' como alternativa a 'building:levels'."""
    assert classify_apartment_building({"levels": "6"}) == "high"


# ── classify_commercial ─────────────────────────────────────────────────────

def test_commercial_high_four_floors():
    assert classify_commercial({"building:levels": "4"}) == "high"

def test_commercial_low_three_floors():
    assert classify_commercial({"building:levels": "3"}) == "low"

def test_commercial_low_default():
    assert classify_commercial({}) == "low"


# ── classify_parking ────────────────────────────────────────────────────────

def test_parking_ramp_multistorey():
    assert classify_parking({"parking": "multi-storey"}) == "ramp"

def test_parking_ramp_underground():
    assert classify_parking({"parking": "underground"}) == "ramp"

def test_parking_surface_default():
    assert classify_parking({}) == "surface"

def test_parking_surface_explicit():
    assert classify_parking({"parking": "surface"}) == "surface"
```

- [ ] **Step 3: Verificar que los tests FALLAN (las funciones aún no existen con las nuevas firmas)**

```bash
cd src && uv run pytest ../tests/test_classifiers.py -v
```

Resultado esperado: errores de `TypeError` o `ImportError` porque `classify_apartment_building` no existe aún y `classify_residential` tiene firma diferente.

---

### Task 2: Reparar classifiers.py

**Files:**
- Modify: `src/classifiers.py`

- [ ] **Step 1: Reescribir classifiers.py completo**

```python
"""
classifiers.py
Density classification logic: OSM tags → CS2 zone types.

v2 — Simplified strategy:
- classify_residential: uses only the tags of the landuse polygon itself.
  Without building-level cross-referencing (removed — was always returning 0
  due to ID mismatch between landuse polygons and building OSM objects).
- classify_apartment_building: classifies individual building=apartments
  footprints directly by their building:levels tag. These are queried
  separately in extract_zoning.py and added to the residential output.
"""


def classify_residential(tags: dict) -> str:
    """
    Classify a landuse=residential polygon into CS2 density tiers.

    Without spatial cross-referencing of building floors, this function
    relies solely on tags present on the landuse polygon itself.
    In practice, most landuse=residential polygons lack building:levels,
    so they default to LOW density — which is correct for suburban areas.
    High/medium density is captured by classify_apartment_building() instead.

    CS2 thresholds:
    - HIGH   (>=5 floors OR apartments/condo tag)
    - MEDIUM (>=3 floors OR terrace/townhouse tag)
    - LOW    (default)
    """
    tag_levels = int(tags.get("building:levels") or tags.get("levels") or 0)
    residential_subtype = tags.get("residential", "").lower()
    building_type = tags.get("building", "").lower()

    if (tag_levels >= 5
            or residential_subtype in ("apartments", "condominium", "condo")):
        return "high"

    if (tag_levels >= 3
            or building_type in ("terrace", "dormitory", "townhouse")
            or residential_subtype in ("townhouse", "dormitory", "semi")):
        return "medium"

    return "low"


def classify_apartment_building(tags: dict) -> str:
    """
    Classify a building=apartments footprint by its floor count.

    These are individual building polygons (not landuse areas) queried
    directly from OSM. Their building:levels tag is reliable and precise.

    CS2 thresholds (same as classify_residential):
    - HIGH   >= 5 floors
    - MEDIUM >= 3 floors
    - LOW    default (unlikely for tagged apartments, but safe fallback)
    """
    levels = int(tags.get("building:levels") or tags.get("levels") or 1)
    if levels >= 5:
        return "high"
    if levels >= 3:
        return "medium"
    return "low"


def classify_commercial(tags: dict) -> str:
    """
    Classify commercial zones into HIGH or LOW density.

    CS2 thresholds:
    - HIGH (>=4 floors) → North American High Density Commercial
    - LOW  (default)    → North American Low Density Commercial
    """
    levels = int(tags.get("building:levels") or tags.get("levels") or 1)
    return "high" if levels >= 4 else "low"


def classify_parking(tags: dict) -> str:
    """
    Distinguish structured parking (ramps) from surface lots.

    CS2 distinction:
    - RAMP    → Parking Garage / Ramp asset
    - SURFACE → Surface Parking Lot
    """
    parking_type = tags.get("parking", "").lower()
    if parking_type in ("multi-storey", "multistorey", "structure", "underground"):
        return "ramp"
    return "surface"
```

- [ ] **Step 2: Correr los tests — deben pasar todos**

```bash
cd src && uv run pytest ../tests/test_classifiers.py -v
```

Resultado esperado: `22 passed`

- [ ] **Step 3: Commit**

```bash
git add src/classifiers.py tests/test_classifiers.py tests/__init__.py
git commit -m "fix(classifiers): remove broken building_levels cross-ref, add classify_apartment_building"
```

---

### Task 3: Actualizar cs2_zones.py

**Files:**
- Modify: `src/cs2_zones.py`

- [ ] **Step 1: Añadir label mixed_res_com y query apartments a cs2_zones.py**

```python
"""
cs2_zones.py
Mapping between OSM landuse/building tags and Cities: Skylines 2 zone names.

These zone names correspond to the North American zone set in CS2 (base game).
If you're using a modded zone pack, adjust the values in CS2_LABELS accordingly.
"""

CS2_LABELS = {
    "res_high":      "North American High Density Residential",
    "res_med":       "North American Medium Density Residential",
    "res_low":       "North American Low Density Residential",
    "com_high":      "North American High Density Commercial",
    "com_low":       "North American Low Density Commercial",
    "retail":        "North American Retail Hub",
    "industrial":    "North American Industrial Zone",
    "prk_ramp":      "Parking Garage / Ramp",
    "prk_surface":   "Surface Parking Lot",
    "office":        "Office / Government Building",
    "mixed":         "Mixed-Use Development",
    "mixed_res_com": "Mixed Residential-Commercial",  # comercio abajo, aptos arriba
}

# Overpass QL query templates.
# BBOX format: "south,west,north,east" — standard for Overpass QL.
# Minneapolis full city bbox (with immediate border areas):
MINNEAPOLIS_BBOX = "44.86,-93.38,45.05,-93.17"


def build_queries(bbox: str) -> dict:
    """
    Build all Overpass QL queries for the given bounding box.

    Queries split by category for reliability (avoids timeouts on large bboxes).
    'apartments' query replaces the old 'buildings_levels' pre-pass:
    it returns full geometry so apartment buildings can be added directly
    to the residential output, solving the broken ID cross-reference.
    """
    return {
        # NEW: apartment building footprints with geometry (replaces buildings_levels)
        "apartments": f"""
[out:json][timeout:180];
(
  way["building"="apartments"]({bbox});
  way["building"="residential"]["building:levels"]({bbox});
);
out geom tags;
""".strip(),
        "residential": f"""
[out:json][timeout:180];
(
  way["landuse"="residential"]({bbox});
  relation["landuse"="residential"]({bbox});
);
out geom;
""".strip(),
        "commercial": f"""
[out:json][timeout:180];
(
  way["landuse"="commercial"]({bbox});
  relation["landuse"="commercial"]({bbox});
);
out geom;
""".strip(),
        "industrial": f"""
[out:json][timeout:180];
(
  way["landuse"="industrial"]({bbox});
  relation["landuse"="industrial"]({bbox});
  way["building"~"^(industrial|warehouse|factory)$"]({bbox});
);
out geom;
""".strip(),
        "retail": f"""
[out:json][timeout:180];
(
  way["landuse"="retail"]({bbox});
  relation["landuse"="retail"]({bbox});
);
out geom;
""".strip(),
        "parking": f"""
[out:json][timeout:180];
(
  way["amenity"="parking"]({bbox});
  relation["amenity"="parking"]({bbox});
);
out geom;
""".strip(),
        "office": f"""
[out:json][timeout:180];
(
  way["building"="office"]({bbox});
  relation["building"="office"]({bbox});
  way["office"]({bbox});
  relation["office"]({bbox});
  way["landuse"="office"]({bbox});
);
out geom;
""".strip(),
        "mixed": f"""
[out:json][timeout:180];
(
  way["landuse"="mixed"]({bbox});
  relation["landuse"="mixed"]({bbox});
  way["building"="mixed_use"]({bbox});
  relation["building"="mixed_use"]({bbox});
  way["building:use"="mixed"]({bbox});
  relation["building:use"="mixed"]({bbox});
);
out geom;
""".strip(),
        "mixed_res_com": f"""
[out:json][timeout:180];
(
  way["landuse"="commercial"]["residential"="yes"]({bbox});
  way["shop"]["residential"="yes"]({bbox});
  way["building"="mixed_use"]["residential"="yes"]({bbox});
);
out geom;
""".strip(),
    }
```

- [ ] **Step 2: Añadir test de sanidad de queries**

Crear `tests/test_queries.py`:

```python
"""Tests de sanidad para los builders de queries Overpass."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from cs2_zones import build_queries, CS2_LABELS

BBOX = "44.86,-93.38,45.05,-93.17"


def test_all_expected_query_keys_present():
    queries = build_queries(BBOX)
    expected = {"apartments", "residential", "commercial", "industrial",
                "retail", "parking", "office", "mixed", "mixed_res_com"}
    assert expected == set(queries.keys())

def test_all_queries_contain_bbox():
    queries = build_queries(BBOX)
    for key, q in queries.items():
        assert BBOX in q, f"Query '{key}' no contiene el bbox"

def test_all_queries_have_out_directive():
    queries = build_queries(BBOX)
    for key, q in queries.items():
        assert "out" in q, f"Query '{key}' no tiene directiva 'out'"

def test_cs2_labels_has_mixed_res_com():
    assert "mixed_res_com" in CS2_LABELS

def test_apartments_query_requests_geometry():
    queries = build_queries(BBOX)
    assert "out geom" in queries["apartments"]

def test_mixed_query_includes_building_use():
    queries = build_queries(BBOX)
    assert 'building:use"="mixed"' in queries["mixed"]
```

- [ ] **Step 3: Correr tests**

```bash
cd src && uv run pytest ../tests/test_queries.py -v
```

Resultado esperado: `6 passed`

- [ ] **Step 4: Commit**

```bash
git add src/cs2_zones.py tests/test_queries.py
git commit -m "feat(zones): add apartments query with geometry, add mixed_res_com label"
```

---

### Task 4: Reparar extract_zoning.py

**Files:**
- Modify: `src/extract_zoning.py`

- [ ] **Step 1: Reescribir extract_zoning.py**

```python
#!/usr/bin/env python3
"""
extract_zoning.py — CS2 Minneapolis Zoning Pipeline v2.0
=========================================================
Extracts real-world zoning polygons from OpenStreetMap via Overpass API
and exports them as a JavaScript data file ready to be loaded by the
Leaflet.js visualizer.

Changes from v1.0:
- Removed broken building_levels_index cross-reference (always returned 0)
- Added direct apartment building footprints as residential zones
- Added mixed_res_com (commercial+residential) zone type
- Improved mixed-use query to capture building:use=mixed

Usage:
    cd src
    uv run extract_zoning.py
    uv run extract_zoning.py --bbox "44.86,-93.38,45.05,-93.17"
    uv run extract_zoning.py --out ../visualizer/datos_zonificacion.js
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from overpass_client import query_with_retry
from classifiers import (
    classify_residential,
    classify_apartment_building,
    classify_commercial,
    classify_parking,
)
from cs2_zones import CS2_LABELS, MINNEAPOLIS_BBOX, build_queries


# ── Geometry helpers ─────────────────────────────────────────────────────────

def coords_from_way(element: dict) -> list | None:
    geom = element.get("geometry", [])
    if len(geom) < 3:
        return None
    return [[pt["lat"], pt["lon"]] for pt in geom]


def coords_from_relation(element: dict) -> list | None:
    members = element.get("members", [])
    outers = [
        m for m in members
        if m.get("role") == "outer"
        and len(m.get("geometry", [])) > 2
    ]
    if not outers:
        return None
    outers.sort(key=lambda m: len(m["geometry"]), reverse=True)
    return [[pt["lat"], pt["lon"]] for pt in outers[0]["geometry"]]


def extract_coords(element: dict) -> list | None:
    if element["type"] == "way":
        return coords_from_way(element)
    return coords_from_relation(element)


# ── Main pipeline ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Extract OSM zoning data for CS2")
    parser.add_argument(
        "--bbox",
        default=MINNEAPOLIS_BBOX,
        help=f"Bounding box 'south,west,north,east' (default: {MINNEAPOLIS_BBOX})"
    )
    parser.add_argument(
        "--out",
        default="../visualizer/datos_zonificacion.js",
        help="Output .js file path"
    )
    args = parser.parse_args()

    bbox = args.bbox
    out_path = Path(args.out)
    queries = build_queries(bbox)

    print(f"CS2 Minneapolis Zoning Extractor v2.0")
    print(f"Bounding Box : {bbox}")
    print(f"Output       : {out_path}\n")

    # ── Step 1: Download apartment building footprints ────────────────────────
    print("[1/3] Downloading apartment building footprints...")
    apt_data = query_with_retry(queries["apartments"], "apartments")
    print(f"      {len(apt_data.get('elements', []))} apartment buildings found\n")

    # ── Step 2: Download all landuse polygons ─────────────────────────────────
    LANDUSE_CATEGORIES = [
        "residential", "commercial", "industrial", "retail",
        "parking", "office", "mixed", "mixed_res_com"
    ]
    print("[2/3] Downloading landuse polygons (8 sequential queries)...")
    raw: dict[str, list] = {}
    for cat in LANDUSE_CATEGORIES:
        result = query_with_retry(queries[cat], cat)
        raw[cat] = result.get("elements", [])
        print(f"      {cat}: {len(raw[cat])} elements")

    # ── Step 3: Classify ──────────────────────────────────────────────────────
    print("\n[3/3] Classifying zones...")

    ALL_CATEGORIES = ["apartments"] + LANDUSE_CATEGORIES
    output: dict[str, list] = {cat: [] for cat in ALL_CATEGORIES}
    skipped = 0
    commercial_ids: set[int] = set()

    # Apartment buildings → direct residential classification
    for el in apt_data.get("elements", []):
        tags = el.get("tags") or {}
        coords = extract_coords(el)
        if not coords:
            skipped += 1
            continue
        zone = classify_apartment_building(tags)
        cs2_key = {"high": "res_high", "medium": "res_med", "low": "res_low"}[zone]
        output["apartments"].append({
            "id": el["id"],
            "name": tags.get("name", ""),
            "coords": coords,
            "zone": zone,
            "cs2": CS2_LABELS[cs2_key],
        })

    # Commercial must run first to build dedup set for office pass
    for el in raw["commercial"]:
        commercial_ids.add(el["id"])
        tags = el.get("tags") or {}
        coords = extract_coords(el)
        if not coords:
            skipped += 1
            continue
        zone = classify_commercial(tags)
        output["commercial"].append({
            "id": el["id"],
            "name": tags.get("name", ""),
            "coords": coords,
            "zone": zone,
            "cs2": CS2_LABELS[f"com_{zone}"],
        })

    for el in raw["residential"]:
        tags = el.get("tags") or {}
        coords = extract_coords(el)
        if not coords:
            skipped += 1
            continue
        zone = classify_residential(tags)
        cs2_key = {"high": "res_high", "medium": "res_med", "low": "res_low"}[zone]
        output["residential"].append({
            "id": el["id"],
            "name": tags.get("name", ""),
            "coords": coords,
            "zone": zone,
            "cs2": CS2_LABELS[cs2_key],
        })

    for el in raw["industrial"]:
        tags = el.get("tags") or {}
        coords = extract_coords(el)
        if not coords:
            skipped += 1
            continue
        output["industrial"].append({
            "id": el["id"],
            "name": tags.get("name", ""),
            "coords": coords,
            "zone": "industrial",
            "cs2": CS2_LABELS["industrial"],
        })

    for el in raw["retail"]:
        tags = el.get("tags") or {}
        coords = extract_coords(el)
        if not coords:
            skipped += 1
            continue
        output["retail"].append({
            "id": el["id"],
            "name": tags.get("name", ""),
            "coords": coords,
            "zone": "retail",
            "cs2": CS2_LABELS["retail"],
        })

    for el in raw["parking"]:
        tags = el.get("tags") or {}
        coords = extract_coords(el)
        if not coords:
            skipped += 1
            continue
        zone = classify_parking(tags)
        output["parking"].append({
            "id": el["id"],
            "name": tags.get("name", ""),
            "coords": coords,
            "zone": zone,
            "cs2": CS2_LABELS[f"prk_{zone}"],
        })

    for el in raw["office"]:
        if el["id"] in commercial_ids:
            continue
        tags = el.get("tags") or {}
        coords = extract_coords(el)
        if not coords:
            skipped += 1
            continue
        output["office"].append({
            "id": el["id"],
            "name": tags.get("name", ""),
            "coords": coords,
            "zone": "office",
            "cs2": CS2_LABELS["office"],
        })

    for el in raw["mixed"]:
        tags = el.get("tags") or {}
        coords = extract_coords(el)
        if not coords:
            skipped += 1
            continue
        output["mixed"].append({
            "id": el["id"],
            "name": tags.get("name", ""),
            "coords": coords,
            "zone": "mixed",
            "cs2": CS2_LABELS["mixed"],
        })

    for el in raw["mixed_res_com"]:
        tags = el.get("tags") or {}
        coords = extract_coords(el)
        if not coords:
            skipped += 1
            continue
        output["mixed_res_com"].append({
            "id": el["id"],
            "name": tags.get("name", ""),
            "coords": coords,
            "zone": "mixed_res_com",
            "cs2": CS2_LABELS["mixed_res_com"],
        })

    # ── Summary ───────────────────────────────────────────────────────────────
    total = sum(len(v) for v in output.values())
    apts = output["apartments"]
    res  = output["residential"]
    print(f"\n  Apartments   high/med/low : "
          f"{sum(1 for r in apts if r['zone']=='high')} / "
          f"{sum(1 for r in apts if r['zone']=='medium')} / "
          f"{sum(1 for r in apts if r['zone']=='low')}")
    print(f"  Residential  high/med/low : "
          f"{sum(1 for r in res if r['zone']=='high')} / "
          f"{sum(1 for r in res if r['zone']=='medium')} / "
          f"{sum(1 for r in res if r['zone']=='low')}")
    com = output["commercial"]
    print(f"  Commercial   high/low     : "
          f"{sum(1 for c in com if c['zone']=='high')} / "
          f"{sum(1 for c in com if c['zone']=='low')}")
    for cat in ["industrial", "retail", "parking", "office", "mixed", "mixed_res_com"]:
        print(f"  {cat:<16}        : {len(output[cat])}")
    print(f"  Skipped (no geometry)     : {skipped}")
    print(f"  TOTAL                     : {total}")

    # ── Write output ──────────────────────────────────────────────────────────
    ts = datetime.now(timezone.utc).isoformat()
    lines = [
        f"// Auto-generated by extract_zoning.py v2.0 — {ts}",
        f"// Minneapolis Zoning — bbox: {bbox}",
        f"// Total polygons: {total}",
        "",
    ]
    for cat in ALL_CATEGORIES:
        var = f"DATA_{cat.upper()}"
        lines.append(f"const {var} = {json.dumps(output[cat])};")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    size_mb = out_path.stat().st_size / (1024 * 1024)
    print(f"\nDone. {out_path} — {size_mb:.1f} MB — {total} polygons")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add src/extract_zoning.py
git commit -m "fix(zoning): replace broken density index with direct apartment building queries, add mixed_res_com"
```

---

### Task 5: Actualizar colores CS2 en el visualizador

**Files:**
- Create: `src/patch_colors.py`
- Modify: `visualizer/index.html` (via script)

- [ ] **Step 1: Crear script de parcheo de colores**

Crear `src/patch_colors.py`:

```python
#!/usr/bin/env python3
"""
patch_colors.py — Actualiza los colores del visualizador a la paleta CS2 oficial.
Uso: cd src && uv run patch_colors.py
"""
import re
from pathlib import Path

HTML_PATH = Path("../visualizer/index.html")

# Mapa de colores: nombre de zona → nuevo color CS2
CS2_COLORS = {
    # Residencial
    "res_high":      "#2E7D32",  # Verde oscuro
    "res_med":       "#4CAF50",  # Verde medio
    "res_low":       "#8BC34A",  # Verde claro
    # Comercial
    "com_high":      "#0277BD",  # Azul oscuro
    "com_low":       "#29B6F6",  # Azul claro
    "retail":        "#00BCD4",  # Celeste
    # Otros
    "office":        "#00ACC1",  # Turquesa
    "industrial":    "#FFC107",  # Amarillo ámbar
    "mixed":         "#00E5FF",  # Cian
    "mixed_res_com": "#80DEEA",  # Cian claro
    "prk_surface":   "#90A4AE",  # Gris claro
    "prk_ramp":      "#546E7A",  # Gris oscuro
}

def get_color_for_zone(zone_key: str) -> str:
    return CS2_COLORS.get(zone_key, "#CCCCCC")

def patch_html(html: str) -> str:
    """
    Reemplaza asignaciones de color en el JS del visualizador.
    Busca patrones como: zone === 'high' ? '#XXXXXX' o color: '#XXXXXX'
    asociados a cada tipo de zona.
    """
    patched = html

    # Patrón: zona residencial alta densidad
    # Busca el color asignado a 'high' en el bloque de DATA_RESIDENTIAL / DATA_APARTMENTS
    color_patterns = [
        # Residencial por densidad
        (r"(zone\s*===\s*['\"]high['\"]\s*\?\s*['\"])#[0-9A-Fa-f]{6}(['\"])", CS2_COLORS["res_high"], 3),
        (r"(zone\s*===\s*['\"]medium['\"]\s*\?\s*['\"])#[0-9A-Fa-f]{6}(['\"])", CS2_COLORS["res_med"], 3),
        # Colores directos por variable de capa — buscar hexadecimales comunes de Leaflet
        # junto a nombres de zona en comentarios o propiedades nearby
    ]

    # Estrategia alternativa: reemplazar por nombre de zona en objetos de estilo
    # Busca bloques como: { color: '#XXXXXX', fillColor: '#XXXXXX' } cerca de 'residential'
    # y reemplaza con los colores CS2 correctos.

    # Para cada zona, busca el patrón: "zone_key" ... color: '#HEX'
    zone_to_color_map = {
        "res_high":      CS2_COLORS["res_high"],
        "res_med":       CS2_COLORS["res_med"],
        "res_low":       CS2_COLORS["res_low"],
        "com_high":      CS2_COLORS["com_high"],
        "com_low":       CS2_COLORS["com_low"],
        "retail":        CS2_COLORS["retail"],
        "office":        CS2_COLORS["office"],
        "industrial":    CS2_COLORS["industrial"],
        "mixed":         CS2_COLORS["mixed"],
        "mixed_res_com": CS2_COLORS["mixed_res_com"],
        "prk_surface":   CS2_COLORS["prk_surface"],
        "prk_ramp":      CS2_COLORS["prk_ramp"],
    }

    for zone_key, new_color in zone_to_color_map.items():
        # Busca: 'zone_key': '#XXXXXX' o "zone_key": "#XXXXXX"
        pattern = rf"(['\"]){re.escape(zone_key)}\1\s*:\s*['\"]#[0-9A-Fa-f]{{6}}['\"]"
        replacement = rf"'{zone_key}': '{new_color}'"
        patched = re.sub(pattern, replacement, patched)

    return patched


def main():
    if not HTML_PATH.exists():
        print(f"Error: no se encuentra {HTML_PATH}")
        return

    original = HTML_PATH.read_text(encoding="utf-8")
    patched = patch_html(original)

    if patched == original:
        print("AVISO: No se encontraron patrones de color que reemplazar.")
        print("Inspecciona manualmente el HTML para identificar la estructura de colores.")
        print("\nColores CS2 objetivo:")
        for k, v in CS2_COLORS.items():
            print(f"  {k:<16} → {v}")
        return

    # Backup
    backup = HTML_PATH.with_suffix(".html.bak")
    backup.write_text(original, encoding="utf-8")
    print(f"Backup guardado en: {backup}")

    HTML_PATH.write_text(patched, encoding="utf-8")
    changed = sum(1 for a, b in zip(original.splitlines(), patched.splitlines()) if a != b)
    print(f"Colores actualizados. Líneas modificadas: {changed}")
    print("\nColores CS2 aplicados:")
    for k, v in CS2_COLORS.items():
        print(f"  {k:<16} → {v}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Ejecutar el script**

```bash
cd src && uv run patch_colors.py
```

- [ ] **Step 3: Verificar visualmente el resultado**

Abrir `visualizer/index.html` en el navegador. Verificar que:
- Zonas residenciales aparecen en tonos verdes (claro → oscuro según densidad)
- Zonas comerciales en tonos azules
- Industrial en amarillo ámbar
- Office en turquesa
- Estacionamientos en grises

Si el script reporta "No se encontraron patrones", abrir `visualizer/index.html` con un editor, buscar los colores actuales (probablemente definidos en un objeto como `ZONE_COLORS = { 'res_high': '#e74c3c', ... }`), y reemplazarlos manualmente con los valores de `CS2_COLORS` en el script.

- [ ] **Step 4: Actualizar pyproject.toml con nuevo entry point para extract_vial, etc.**

En `src/pyproject.toml`, actualizar la sección `[project.scripts]`:

```toml
[project]
name = "cs2-minneapolis-zoning"
version = "2.0.0"
description = "GIS pipeline: extract OpenStreetMap data for Cities Skylines 2"
requires-python = ">=3.11"
dependencies = [
    "requests>=2.31.0",
    "tqdm>=4.66.0",
]

[project.scripts]
extract-zoning    = "extract_zoning:main"
extract-vial      = "extract_vial:main"
extract-services  = "extract_services:main"
extract-transport = "extract_transport:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

- [ ] **Step 5: Regenerar datos reales y verificar**

```bash
cd src && uv run extract_zoning.py
```

Resultado esperado: El script descarga ~10-15 MB de datos (más que v1 por incluir apartment buildings). Verificar en el resumen que `Apartments high` muestra un número significativo (>50) — esto confirma que el bug de densidad está corregido.

- [ ] **Step 6: Commit**

```bash
git add src/patch_colors.py src/pyproject.toml visualizer/index.html visualizer/datos_zonificacion.js
git commit -m "fix(visualizer): update zone colors to CS2 palette, regenerate zoning data v2"
```

---

## PARTE 2 — Módulo Red Vial

---

### Task 6: Crear extract_vial.py y vial_queries.py

**Files:**
- Create: `src/vial_queries.py`
- Create: `src/extract_vial.py`

- [ ] **Step 1: Crear vial_queries.py**

```python
"""
vial_queries.py
Overpass QL queries for Minneapolis road network extraction.
"""

MINNEAPOLIS_BBOX = "44.86,-93.38,45.05,-93.17"


def build_vial_queries(bbox: str) -> dict:
    return {
        "motorway": f"""
[out:json][timeout:180];
(
  way["highway"="motorway"]({bbox});
  way["highway"="motorway_link"]({bbox});
);
out geom tags;
""".strip(),
        "primary": f"""
[out:json][timeout:180];
(
  way["highway"="primary"]({bbox});
  way["highway"="primary_link"]({bbox});
);
out geom tags;
""".strip(),
        "secondary": f"""
[out:json][timeout:180];
(
  way["highway"="secondary"]({bbox});
  way["highway"="secondary_link"]({bbox});
);
out geom tags;
""".strip(),
        "tertiary": f"""
[out:json][timeout:180];
(
  way["highway"="tertiary"]({bbox});
  way["highway"="tertiary_link"]({bbox});
);
out geom tags;
""".strip(),
        "bridges": f"""
[out:json][timeout:180];
(
  way["bridge"="yes"]["highway"]({bbox});
);
out geom tags;
""".strip(),
    }


VIAL_COLORS = {
    "motorway":  "#C62828",  # Rojo oscuro
    "primary":   "#EF6C00",  # Naranja
    "secondary": "#F9A825",  # Amarillo
    "tertiary":  "#9E9E9E",  # Gris
    "bridges":   "#1565C0",  # Azul oscuro
}

VIAL_WEIGHTS = {
    "motorway":  5,
    "primary":   3,
    "secondary": 2,
    "tertiary":  1,
    "bridges":   4,
}
```

- [ ] **Step 2: Crear extract_vial.py**

```python
#!/usr/bin/env python3
"""
extract_vial.py — CS2 Minneapolis Road Network Extractor v1.0
=============================================================
Extracts the road hierarchy from OpenStreetMap and exports it
as a JavaScript data file for the Leaflet.js road visualizer.

Usage:
    cd src
    uv run extract_vial.py
    uv run extract_vial.py --bbox "44.86,-93.38,45.05,-93.17"
    uv run extract_vial.py --out ../visualizer/vial/datos_vial.js
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from overpass_client import query_with_retry
from vial_queries import build_vial_queries, MINNEAPOLIS_BBOX, VIAL_COLORS, VIAL_WEIGHTS


def coords_from_way(element: dict) -> list | None:
    geom = element.get("geometry", [])
    if len(geom) < 2:
        return None
    return [[pt["lat"], pt["lon"]] for pt in geom]


def main():
    parser = argparse.ArgumentParser(description="Extract OSM road network for CS2")
    parser.add_argument("--bbox", default=MINNEAPOLIS_BBOX)
    parser.add_argument("--out", default="../visualizer/vial/datos_vial.js")
    args = parser.parse_args()

    bbox = args.bbox
    out_path = Path(args.out)
    queries = build_vial_queries(bbox)

    print("CS2 Minneapolis Road Network Extractor v1.0")
    print(f"Bounding Box : {bbox}")
    print(f"Output       : {out_path}\n")

    output: dict[str, list] = {cat: [] for cat in queries}
    skipped = 0

    for cat, query in queries.items():
        result = query_with_retry(query, cat)
        elements = result.get("elements", [])
        print(f"  {cat}: {len(elements)} ways")
        for el in elements:
            tags = el.get("tags") or {}
            coords = coords_from_way(el)
            if not coords:
                skipped += 1
                continue
            output[cat].append({
                "id":     el["id"],
                "name":   tags.get("name", tags.get("ref", "")),
                "coords": coords,
                "type":   cat,
                "color":  VIAL_COLORS[cat],
                "weight": VIAL_WEIGHTS[cat],
            })

    total = sum(len(v) for v in output.values())
    print(f"\n  Skipped (no geometry): {skipped}")
    print(f"  TOTAL: {total} road segments")

    ts = datetime.now(timezone.utc).isoformat()
    lines = [
        f"// Auto-generated by extract_vial.py — {ts}",
        f"// Minneapolis Road Network — bbox: {bbox}",
        f"// Total segments: {total}",
        "",
    ]
    for cat in queries:
        var = f"DATA_VIAL_{cat.upper()}"
        lines.append(f"const {var} = {json.dumps(output[cat])};")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    size_kb = out_path.stat().st_size / 1024
    print(f"\nDone. {out_path} — {size_kb:.0f} KB — {total} segments")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Ejecutar y verificar**

```bash
cd src && uv run extract_vial.py
```

Resultado esperado: genera `visualizer/vial/datos_vial.js` con segmentos viales. El número de motorway debería ser relativamente bajo (~50-100) y tertiary el más alto (~500-2000).

- [ ] **Step 4: Commit**

```bash
git add src/vial_queries.py src/extract_vial.py visualizer/vial/datos_vial.js
git commit -m "feat(vial): add road network extractor for CS2 reference map"
```

---

### Task 7: Crear visualizador de red vial

**Files:**
- Create: `visualizer/vial/index.html`

- [ ] **Step 1: Crear visualizer/vial/index.html**

```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>CS2 Mineapolis — Red Vial</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script src="datos_vial.js"></script>
  <style>
    html, body { margin: 0; padding: 0; height: 100%; background: #1a1a2e; }
    #map { height: 100vh; }
    .legend { background: rgba(0,0,0,0.8); color: #fff; padding: 10px 14px;
              border-radius: 6px; font-size: 13px; line-height: 2; }
    .legend-row { display: flex; align-items: center; gap: 8px; }
    .legend-line { width: 24px; height: 4px; border-radius: 2px; }
    #title { position: absolute; top: 12px; left: 50%; transform: translateX(-50%);
             background: rgba(0,0,0,0.7); color: #fff; padding: 6px 16px;
             border-radius: 20px; font-family: sans-serif; font-size: 14px;
             font-weight: bold; z-index: 1000; pointer-events: none; }
  </style>
</head>
<body>
<div id="title">🛣️ Red Vial — Minneapolis (CS2 Reference)</div>
<div id="map"></div>
<script>
  const map = L.map('map', { preferCanvas: true });
  map.fitBounds([[44.86, -93.38], [45.05, -93.17]]);

  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '© OpenStreetMap contributors © CARTO',
    maxZoom: 19
  }).addTo(map);

  const LAYERS = {
    "Autopistas (Motorway)":  { data: DATA_VIAL_MOTORWAY,  color: "#C62828", weight: 5 },
    "Avenidas Principales":   { data: DATA_VIAL_PRIMARY,   color: "#EF6C00", weight: 3 },
    "Calles Secundarias":     { data: DATA_VIAL_SECONDARY, color: "#F9A825", weight: 2 },
    "Calles Terciarias":      { data: DATA_VIAL_TERTIARY,  color: "#9E9E9E", weight: 1 },
    "Puentes":                { data: DATA_VIAL_BRIDGES,   color: "#1565C0", weight: 4 },
  };

  const overlays = {};

  Object.entries(LAYERS).forEach(([name, cfg]) => {
    const group = L.layerGroup();
    cfg.data.forEach(feat => {
      L.polyline(feat.coords, {
        color: cfg.color,
        weight: cfg.weight,
        opacity: 0.85
      })
      .bindPopup(`<b>${feat.name || 'Sin nombre'}</b><br>Tipo: ${feat.type}<br>OSM ID: ${feat.id}`)
      .addTo(group);
    });
    group.addTo(map);
    overlays[name] = group;
  });

  L.control.layers({}, overlays, { collapsed: false }).addTo(map);

  const legend = L.control({ position: 'bottomright' });
  legend.onAdd = () => {
    const div = L.DomUtil.create('div', 'legend');
    div.innerHTML = '<b>Red Vial</b><br>' +
      Object.entries(LAYERS).map(([name, cfg]) =>
        `<div class="legend-row">
          <div class="legend-line" style="background:${cfg.color};height:${cfg.weight+1}px"></div>
          <span>${name}</span>
        </div>`
      ).join('');
    return div;
  };
  legend.addTo(map);
</script>
</body>
</html>
```

- [ ] **Step 2: Abrir en el navegador y verificar**

Abrir `visualizer/vial/index.html` en el navegador. Verificar:
- Las autopistas I-35W e I-94 aparecen como líneas rojas gruesas cruzando la ciudad
- Hennepin Ave y Nicollet Mall aparecen como avenidas principales naranjas
- El grid de calles secundarias/terciarias cubre el área residencial
- Los puentes sobre el Mississippi son visibles en azul oscuro

- [ ] **Step 3: Commit**

```bash
git add visualizer/vial/index.html
git commit -m "feat(vial): add interactive road network visualizer"
```

---

## PARTE 3 — Módulo Servicios Urbanos

---

### Task 8: Crear extract_services.py y services_queries.py

**Files:**
- Create: `src/services_queries.py`
- Create: `src/extract_services.py`

- [ ] **Step 1: Crear services_queries.py**

```python
"""
services_queries.py
Overpass QL queries for Minneapolis urban services extraction.
"""

MINNEAPOLIS_BBOX = "44.86,-93.38,45.05,-93.17"


def build_services_queries(bbox: str) -> dict:
    return {
        "health": f"""
[out:json][timeout:180];
(
  node["amenity"="hospital"]({bbox});
  way["amenity"="hospital"]({bbox});
  node["amenity"="clinic"]({bbox});
  way["amenity"="clinic"]({bbox});
);
out geom tags;
""".strip(),
        "education": f"""
[out:json][timeout:180];
(
  node["amenity"="school"]({bbox});
  way["amenity"="school"]({bbox});
  node["amenity"="university"]({bbox});
  way["amenity"="university"]({bbox});
  node["amenity"="college"]({bbox});
  way["amenity"="college"]({bbox});
);
out geom tags;
""".strip(),
        "parks": f"""
[out:json][timeout:180];
(
  way["leisure"="park"]({bbox});
  relation["leisure"="park"]({bbox});
  way["natural"="water"]({bbox});
  relation["natural"="water"]({bbox});
);
out geom tags;
""".strip(),
        "police": f"""
[out:json][timeout:180];
(
  node["amenity"="police"]({bbox});
  way["amenity"="police"]({bbox});
);
out geom tags;
""".strip(),
        "fire": f"""
[out:json][timeout:180];
(
  node["amenity"="fire_station"]({bbox});
  way["amenity"="fire_station"]({bbox});
);
out geom tags;
""".strip(),
        "energy": f"""
[out:json][timeout:180];
(
  node["power"="plant"]({bbox});
  way["power"="plant"]({bbox});
  node["power"="substation"]({bbox});
  way["power"="substation"]({bbox});
);
out geom tags;
""".strip(),
        "water": f"""
[out:json][timeout:180];
(
  node["man_made"="water_works"]({bbox});
  way["man_made"="water_works"]({bbox});
  way["waterway"="river"]({bbox});
  way["waterway"="stream"]({bbox});
);
out geom tags;
""".strip(),
        "cemetery": f"""
[out:json][timeout:180];
(
  way["landuse"="cemetery"]({bbox});
  relation["landuse"="cemetery"]({bbox});
);
out geom tags;
""".strip(),
    }


SERVICE_COLORS = {
    "health":    "#E53935",
    "education": "#8E24AA",
    "parks":     "#43A047",
    "police":    "#1E88E5",
    "fire":      "#FF6F00",
    "energy":    "#F9A825",
    "water":     "#00BCD4",
    "cemetery":  "#B0BEC5",
}

SERVICE_LABELS = {
    "health":    "Salud (Hospitales / Clínicas)",
    "education": "Educación (Escuelas / Universidades)",
    "parks":     "Parques y Naturaleza",
    "police":    "Policía (MPD)",
    "fire":      "Bomberos (MFD)",
    "energy":    "Energía (Subestaciones)",
    "water":     "Agua (Ríos / Plantas)",
    "cemetery":  "Cementerios",
}
```

- [ ] **Step 2: Crear extract_services.py**

```python
#!/usr/bin/env python3
"""
extract_services.py — CS2 Minneapolis Urban Services Extractor v1.0
===================================================================
Extracts urban service locations (health, education, parks, emergency
services, energy, water, cemeteries) from OpenStreetMap.

Usage:
    cd src
    uv run extract_services.py
    uv run extract_services.py --out ../visualizer/services/datos_services.js
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from overpass_client import query_with_retry
from services_queries import (
    build_services_queries, MINNEAPOLIS_BBOX,
    SERVICE_COLORS, SERVICE_LABELS
)


def get_centroid(element: dict) -> tuple[float, float] | None:
    """Devuelve el centroide aproximado de un elemento OSM."""
    if element["type"] == "node":
        return element.get("lat"), element.get("lon")
    geom = element.get("geometry", [])
    if not geom:
        return None
    lats = [p["lat"] for p in geom]
    lons = [p["lon"] for p in geom]
    return sum(lats) / len(lats), sum(lons) / len(lons)


def get_polygon(element: dict) -> list | None:
    """Devuelve polígono para ways, None para nodes."""
    if element["type"] != "way":
        return None
    geom = element.get("geometry", [])
    if len(geom) < 3:
        return None
    return [[p["lat"], p["lon"]] for p in geom]


def main():
    parser = argparse.ArgumentParser(description="Extract OSM urban services for CS2")
    parser.add_argument("--bbox", default=MINNEAPOLIS_BBOX)
    parser.add_argument("--out", default="../visualizer/services/datos_services.js")
    args = parser.parse_args()

    bbox = args.bbox
    out_path = Path(args.out)
    queries = build_services_queries(bbox)

    print("CS2 Minneapolis Urban Services Extractor v1.0")
    print(f"Bounding Box : {bbox}")
    print(f"Output       : {out_path}\n")

    output: dict[str, list] = {cat: [] for cat in queries}
    skipped = 0

    for cat, query in queries.items():
        result = query_with_retry(query, cat)
        elements = result.get("elements", [])
        print(f"  {cat}: {len(elements)} elements")
        for el in elements:
            tags = el.get("tags") or {}
            centroid = get_centroid(el)
            polygon  = get_polygon(el)
            if not centroid and not polygon:
                skipped += 1
                continue
            entry = {
                "id":      el["id"],
                "type":    el["type"],
                "name":    tags.get("name", ""),
                "cat":     cat,
                "color":   SERVICE_COLORS[cat],
                "label":   SERVICE_LABELS[cat],
            }
            if centroid and centroid[0]:
                entry["lat"], entry["lon"] = centroid
            if polygon:
                entry["polygon"] = polygon
            output[cat].append(entry)

    total = sum(len(v) for v in output.values())
    print(f"\n  Skipped: {skipped}")
    print(f"  TOTAL: {total} service elements")

    ts = datetime.now(timezone.utc).isoformat()
    lines = [
        f"// Auto-generated by extract_services.py — {ts}",
        f"// Minneapolis Urban Services — bbox: {bbox}",
        f"// Total elements: {total}",
        "",
    ]
    for cat in queries:
        var = f"DATA_SVC_{cat.upper()}"
        lines.append(f"const {var} = {json.dumps(output[cat])};")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    size_kb = out_path.stat().st_size / 1024
    print(f"\nDone. {out_path} — {size_kb:.0f} KB — {total} elements")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Ejecutar y verificar**

```bash
cd src && uv run extract_services.py
```

Verificar en el resumen que `health` muestra al menos 5 hospitales/clínicas y `parks` muestra los parques principales (Chain of Lakes, Minnehaha, etc.).

- [ ] **Step 4: Commit**

```bash
git add src/services_queries.py src/extract_services.py visualizer/services/datos_services.js
git commit -m "feat(services): add urban services extractor (health, education, parks, emergency, energy, water, cemetery)"
```

---

### Task 9: Crear visualizador de servicios

**Files:**
- Create: `visualizer/services/index.html`

- [ ] **Step 1: Crear visualizer/services/index.html**

```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>CS2 Mineapolis — Servicios Urbanos</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script src="datos_services.js"></script>
  <style>
    html, body { margin: 0; padding: 0; height: 100%; background: #1a1a2e; }
    #map { height: 100vh; }
    .legend { background: rgba(0,0,0,0.8); color: #fff; padding: 10px 14px;
              border-radius: 6px; font-size: 12px; line-height: 1.9; }
    .legend-row { display: flex; align-items: center; gap: 8px; }
    .legend-dot { width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }
    #title { position: absolute; top: 12px; left: 50%; transform: translateX(-50%);
             background: rgba(0,0,0,0.7); color: #fff; padding: 6px 16px;
             border-radius: 20px; font-family: sans-serif; font-size: 14px;
             font-weight: bold; z-index: 1000; pointer-events: none; }
  </style>
</head>
<body>
<div id="title">🏥 Servicios Urbanos — Minneapolis (CS2 Reference)</div>
<div id="map"></div>
<script>
  const map = L.map('map', { preferCanvas: true });
  map.fitBounds([[44.86, -93.38], [45.05, -93.17]]);

  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '© OpenStreetMap contributors © CARTO',
    maxZoom: 19
  }).addTo(map);

  const SERVICE_LAYERS = {
    "Salud":        { data: DATA_SVC_HEALTH,    color: "#E53935", icon: "🏥" },
    "Educación":    { data: DATA_SVC_EDUCATION, color: "#8E24AA", icon: "🏫" },
    "Parques":      { data: DATA_SVC_PARKS,     color: "#43A047", icon: "🌳" },
    "Policía":      { data: DATA_SVC_POLICE,    color: "#1E88E5", icon: "🚔" },
    "Bomberos":     { data: DATA_SVC_FIRE,      color: "#FF6F00", icon: "🚒" },
    "Energía":      { data: DATA_SVC_ENERGY,    color: "#F9A825", icon: "⚡" },
    "Agua / Ríos":  { data: DATA_SVC_WATER,     color: "#00BCD4", icon: "💧" },
    "Cementerios":  { data: DATA_SVC_CEMETERY,  color: "#B0BEC5", icon: "⬜" },
  };

  const overlays = {};

  Object.entries(SERVICE_LAYERS).forEach(([name, cfg]) => {
    const group = L.layerGroup();
    cfg.data.forEach(feat => {
      const popup = `<b>${feat.name || 'Sin nombre'}</b><br>${feat.label}<br>OSM ID: ${feat.id}`;

      // Polígono si existe
      if (feat.polygon) {
        L.polygon(feat.polygon, {
          color: cfg.color,
          fillColor: cfg.color,
          fillOpacity: 0.35,
          weight: 2
        }).bindPopup(popup).addTo(group);
      }

      // Marcador de punto
      if (feat.lat !== undefined) {
        L.circleMarker([feat.lat, feat.lon], {
          radius: 7,
          color: cfg.color,
          fillColor: cfg.color,
          fillOpacity: 0.9,
          weight: 2
        }).bindPopup(popup).addTo(group);
      }
    });
    group.addTo(map);
    overlays[name] = group;
  });

  L.control.layers({}, overlays, { collapsed: false }).addTo(map);

  const legend = L.control({ position: 'bottomright' });
  legend.onAdd = () => {
    const div = L.DomUtil.create('div', 'legend');
    div.innerHTML = '<b>Servicios Urbanos</b><br>' +
      Object.entries(SERVICE_LAYERS).map(([name, cfg]) =>
        `<div class="legend-row">
          <div class="legend-dot" style="background:${cfg.color}"></div>
          <span>${cfg.icon} ${name}</span>
        </div>`
      ).join('');
    return div;
  };
  legend.addTo(map);
</script>
</body>
</html>
```

- [ ] **Step 2: Verificar en el navegador**

Abrir `visualizer/services/index.html`. Verificar:
- Hospitales aparecen como puntos rojos (Hennepin Healthcare, Abbott Northwestern)
- Chain of Lakes y Minnehaha aparecen como polígonos verdes
- El río Mississippi aparece como línea celeste

- [ ] **Step 3: Commit**

```bash
git add visualizer/services/index.html
git commit -m "feat(services): add interactive urban services visualizer"
```

---

## PARTE 4 — Módulo Transporte

---

### Task 10: Crear extract_transport.py y transport_queries.py

**Files:**
- Create: `src/transport_queries.py`
- Create: `src/extract_transport.py`

- [ ] **Step 1: Crear transport_queries.py**

```python
"""
transport_queries.py
Overpass QL queries for Minneapolis public transit and cycling infrastructure.
"""

MINNEAPOLIS_BBOX = "44.86,-93.38,45.05,-93.17"


def build_transport_queries(bbox: str) -> dict:
    return {
        "light_rail": f"""
[out:json][timeout:180];
(
  way["railway"="light_rail"]({bbox});
  way["railway"="subway"]({bbox});
  way["railway"="tram"]({bbox});
);
out geom tags;
""".strip(),
        "brt": f"""
[out:json][timeout:180];
(
  relation["route"="bus"]["network"~"Metro Transit",i]["name"~"BRT|Line|Rapid",i]({bbox});
);
out geom tags;
""".strip(),
        "bus_routes": f"""
[out:json][timeout:180];
(
  relation["route"="bus"]["network"~"Metro Transit",i]({bbox});
);
out geom tags;
""".strip(),
        "bus_stops": f"""
[out:json][timeout:180];
(
  node["public_transport"="stop_position"]["bus"="yes"]({bbox});
  node["highway"="bus_stop"]({bbox});
);
out geom tags;
""".strip(),
        "bus_depots": f"""
[out:json][timeout:180];
(
  node["amenity"="bus_depot"]({bbox});
  way["amenity"="bus_depot"]({bbox});
  node["amenity"="depot"]["operator"~"Metro Transit",i]({bbox});
  way["amenity"="depot"]["operator"~"Metro Transit",i]({bbox});
);
out geom tags;
""".strip(),
        "cycleway_greenway": f"""
[out:json][timeout:180];
(
  way["highway"="cycleway"]["segregated"="yes"]({bbox});
  way["highway"="cycleway"]["bicycle"="designated"]["foot"!="yes"]({bbox});
  way["lcn_ref"]({bbox});
);
out geom tags;
""".strip(),
        "cycleway_protected": f"""
[out:json][timeout:180];
(
  way["cycleway"="track"]({bbox});
  way["cycleway:left"="track"]({bbox});
  way["cycleway:right"="track"]({bbox});
  way["cycleway:both"="track"]({bbox});
);
out geom tags;
""".strip(),
        "cycleway_shared": f"""
[out:json][timeout:180];
(
  way["bicycle"="designated"]["highway"~"^(residential|unclassified|service)$"]({bbox});
  way["cycleway"="shared_lane"]({bbox});
);
out geom tags;
""".strip(),
    }


TRANSPORT_COLORS = {
    "light_rail":           "#F57F17",
    "brt":                  "#FB8C00",
    "bus_routes":           "#FF7043",
    "bus_stops":            "#FFA726",
    "bus_depots":           "#757575",
    "cycleway_greenway":    "#00C853",
    "cycleway_protected":   "#FFD600",
    "cycleway_shared":      "#448AFF",
}

TRANSPORT_LABELS = {
    "light_rail":           "Light Rail (Blue/Green Line)",
    "brt":                  "Bus Rapid Transit (A/C/D Line)",
    "bus_routes":           "Rutas de Bus (Metro Transit)",
    "bus_stops":            "Paradas de Autobús",
    "bus_depots":           "Cocheras / Depósitos",
    "cycleway_greenway":    "Ciclovías — Greenways",
    "cycleway_protected":   "Ciclovías — Carril Protegido",
    "cycleway_shared":      "Ciclovías — Ruta Compartida",
}
```

- [ ] **Step 2: Crear extract_transport.py**

```python
#!/usr/bin/env python3
"""
extract_transport.py — CS2 Minneapolis Transport Extractor v1.0
===============================================================
Extracts public transit (Light Rail, BRT, bus routes, stops, depots)
and cycling infrastructure from OpenStreetMap.

Note on bus routes: Overpass returns them as OSM relations, not simple
ways. This script reconstructs polylines from relation members.

Usage:
    cd src
    uv run extract_transport.py
    uv run extract_transport.py --out ../visualizer/transport/datos_transport.js
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from overpass_client import query_with_retry
from transport_queries import (
    build_transport_queries, MINNEAPOLIS_BBOX,
    TRANSPORT_COLORS, TRANSPORT_LABELS
)


def coords_from_way(element: dict) -> list | None:
    geom = element.get("geometry", [])
    if len(geom) < 2:
        return None
    return [[p["lat"], p["lon"]] for p in geom]


def coords_from_relation(element: dict) -> list[list] | None:
    """
    Extract all way geometries from a relation as a list of coordinate arrays.
    Each member way becomes its own polyline segment.
    Returns list of coord arrays (one per way member with geometry).
    """
    segments = []
    for member in element.get("members", []):
        if member.get("type") != "way":
            continue
        geom = member.get("geometry", [])
        if len(geom) < 2:
            continue
        segments.append([[p["lat"], p["lon"]] for p in geom])
    return segments if segments else None


def get_centroid_node(element: dict) -> tuple[float, float] | None:
    if element.get("type") == "node":
        lat = element.get("lat")
        lon = element.get("lon")
        if lat and lon:
            return lat, lon
    return None


def main():
    parser = argparse.ArgumentParser(description="Extract OSM transport data for CS2")
    parser.add_argument("--bbox", default=MINNEAPOLIS_BBOX)
    parser.add_argument("--out", default="../visualizer/transport/datos_transport.js")
    args = parser.parse_args()

    bbox = args.bbox
    out_path = Path(args.out)
    queries = build_transport_queries(bbox)

    print("CS2 Minneapolis Transport Extractor v1.0")
    print(f"Bounding Box : {bbox}")
    print(f"Output       : {out_path}\n")

    output: dict[str, list] = {cat: [] for cat in queries}
    skipped = 0

    for cat, query in queries.items():
        result = query_with_retry(query, cat)
        elements = result.get("elements", [])
        print(f"  {cat}: {len(elements)} elements")

        for el in elements:
            tags = el.get("tags") or {}
            el_type = el.get("type")

            # Nodes → puntos (paradas, depósitos)
            if el_type == "node":
                centroid = get_centroid_node(el)
                if not centroid:
                    skipped += 1
                    continue
                output[cat].append({
                    "id":    el["id"],
                    "type":  "point",
                    "cat":   cat,
                    "name":  tags.get("name", tags.get("ref", "")),
                    "lat":   centroid[0],
                    "lon":   centroid[1],
                    "color": TRANSPORT_COLORS[cat],
                    "label": TRANSPORT_LABELS[cat],
                })

            # Ways → líneas (vías de tren, ciclovías)
            elif el_type == "way":
                coords = coords_from_way(el)
                if not coords:
                    skipped += 1
                    continue
                output[cat].append({
                    "id":     el["id"],
                    "type":   "line",
                    "cat":    cat,
                    "name":   tags.get("name", tags.get("ref", "")),
                    "coords": coords,
                    "color":  TRANSPORT_COLORS[cat],
                    "label":  TRANSPORT_LABELS[cat],
                })

            # Relations → rutas de bus (múltiples segmentos)
            elif el_type == "relation":
                segments = coords_from_relation(el)
                if not segments:
                    skipped += 1
                    continue
                output[cat].append({
                    "id":       el["id"],
                    "type":     "multiline",
                    "cat":      cat,
                    "name":     tags.get("name", tags.get("ref", "")),
                    "segments": segments,
                    "color":    TRANSPORT_COLORS[cat],
                    "label":    TRANSPORT_LABELS[cat],
                })

    total = sum(len(v) for v in output.values())
    print(f"\n  Skipped: {skipped}")
    print(f"  TOTAL: {total} transport elements")

    ts = datetime.now(timezone.utc).isoformat()
    lines = [
        f"// Auto-generated by extract_transport.py — {ts}",
        f"// Minneapolis Transport — bbox: {bbox}",
        f"// Total elements: {total}",
        "",
    ]
    for cat in queries:
        var = f"DATA_TRP_{cat.upper()}"
        lines.append(f"const {var} = {json.dumps(output[cat])};")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    size_kb = out_path.stat().st_size / 1024
    print(f"\nDone. {out_path} — {size_kb:.0f} KB — {total} elements")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Ejecutar y verificar**

```bash
cd src && uv run extract_transport.py
```

Verificar: `light_rail` muestra 2 líneas (Blue/Green Line), `bus_stops` muestra cientos de paradas, `cycleway_greenway` muestra la Midtown Greenway.

- [ ] **Step 4: Commit**

```bash
git add src/transport_queries.py src/extract_transport.py visualizer/transport/datos_transport.js
git commit -m "feat(transport): add transit extractor (light rail, BRT, buses, stops, depots, cycleways)"
```

---

### Task 11: Crear visualizador de transporte

**Files:**
- Create: `visualizer/transport/index.html`

- [ ] **Step 1: Crear visualizer/transport/index.html**

```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>CS2 Mineapolis — Transporte</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script src="datos_transport.js"></script>
  <style>
    html, body { margin: 0; padding: 0; height: 100%; background: #1a1a2e; }
    #map { height: 100vh; }
    .legend { background: rgba(0,0,0,0.85); color: #fff; padding: 10px 14px;
              border-radius: 6px; font-size: 12px; line-height: 2; max-height: 80vh;
              overflow-y: auto; }
    .legend-row { display: flex; align-items: center; gap: 8px; }
    .legend-sym { width: 20px; text-align: center; font-size: 10px; flex-shrink: 0; }
    #title { position: absolute; top: 12px; left: 50%; transform: translateX(-50%);
             background: rgba(0,0,0,0.7); color: #fff; padding: 6px 16px;
             border-radius: 20px; font-family: sans-serif; font-size: 14px;
             font-weight: bold; z-index: 1000; pointer-events: none; }
  </style>
</head>
<body>
<div id="title">🚇 Sistema de Transporte — Minneapolis (CS2 Reference)</div>
<div id="map"></div>
<script>
  const map = L.map('map', { preferCanvas: true });
  map.fitBounds([[44.86, -93.38], [45.05, -93.17]]);

  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '© OpenStreetMap contributors © CARTO',
    maxZoom: 19
  }).addTo(map);

  // Definición de capas y sus datos
  const LAYERS = {
    "Light Rail":            { data: DATA_TRP_LIGHT_RAIL,         color: "#F57F17", weight: 4, icon: "🚋" },
    "BRT (Rapid Bus)":       { data: DATA_TRP_BRT,                color: "#FB8C00", weight: 3, icon: "🚌" },
    "Rutas de Bus":          { data: DATA_TRP_BUS_ROUTES,         color: "#FF7043", weight: 1, icon: "🚍" },
    "Paradas de Bus":        { data: DATA_TRP_BUS_STOPS,          color: "#FFA726", weight: 1, icon: "🛑" },
    "Cocheras":              { data: DATA_TRP_BUS_DEPOTS,         color: "#757575", weight: 1, icon: "🏭" },
    "Ciclovía Greenway":     { data: DATA_TRP_CYCLEWAY_GREENWAY,  color: "#00C853", weight: 3, icon: "🚴" },
    "Ciclovía Protegida":    { data: DATA_TRP_CYCLEWAY_PROTECTED, color: "#FFD600", weight: 2, icon: "🔐" },
    "Ciclovía Compartida":   { data: DATA_TRP_CYCLEWAY_SHARED,    color: "#448AFF", weight: 1, icon: "↔️" },
  };

  function renderLayer(feat, color, weight) {
    const popup = `<b>${feat.name || 'Sin nombre'}</b><br>${feat.label}<br>OSM ID: ${feat.id}`;

    if (feat.type === "point") {
      return L.circleMarker([feat.lat, feat.lon], {
        radius: 5, color, fillColor: color, fillOpacity: 0.9, weight: 2
      }).bindPopup(popup);
    }

    if (feat.type === "line") {
      return L.polyline(feat.coords, { color, weight, opacity: 0.9 }).bindPopup(popup);
    }

    if (feat.type === "multiline") {
      const group = L.layerGroup();
      feat.segments.forEach(seg => {
        L.polyline(seg, { color, weight, opacity: 0.7 })
          .bindPopup(popup)
          .addTo(group);
      });
      return group;
    }

    return null;
  }

  const overlays = {};

  Object.entries(LAYERS).forEach(([name, cfg]) => {
    const group = L.layerGroup();
    cfg.data.forEach(feat => {
      const rendered = renderLayer(feat, cfg.color, cfg.weight);
      if (rendered) {
        if (rendered instanceof L.LayerGroup) {
          rendered.eachLayer(l => l.addTo(group));
        } else {
          rendered.addTo(group);
        }
      }
    });
    group.addTo(map);
    overlays[name] = group;
  });

  L.control.layers({}, overlays, { collapsed: false }).addTo(map);

  const legend = L.control({ position: 'bottomright' });
  legend.onAdd = () => {
    const div = L.DomUtil.create('div', 'legend');
    div.innerHTML = '<b>Sistema de Transporte</b><br>' +
      Object.entries(LAYERS).map(([name, cfg]) =>
        `<div class="legend-row">
          <div class="legend-sym">${cfg.icon}</div>
          <span style="color:${cfg.color}">${name}</span>
        </div>`
      ).join('');
    return div;
  };
  legend.addTo(map);
</script>
</body>
</html>
```

- [ ] **Step 2: Verificar en el navegador**

Abrir `visualizer/transport/index.html`. Verificar:
- Las líneas de Light Rail (Blue/Green Line) aparecen como líneas amarillo-naranjas gruesas
- Las rutas de bus cubren la ciudad como una red naranja fina
- Las paradas de bus son puntos pequeños distribuidos por toda la ciudad
- La Midtown Greenway aparece como línea verde brillante de este a oeste

- [ ] **Step 3: Commit**

```bash
git add visualizer/transport/index.html
git commit -m "feat(transport): add interactive transport visualizer (light rail, bus, cycleways)"
```

---

## PARTE 5 — Documentación

---

### Task 12: Actualizar README.es.md

**Files:**
- Modify: `README.es.md`

- [ ] **Step 1: Añadir sección de nuevos módulos al README**

Añadir al final de `README.es.md`, antes de la sección `## Licencia`:

```markdown
## v2.0 — Módulos Adicionales

### Correcciones en Zonificación (v2.0)

Se corrigió un bug crítico en `classifiers.py` donde la clasificación de densidad residencial siempre devolvía "baja densidad" por un error de cross-referencia de IDs. Ahora los edificios de apartamentos se consultan directamente con sus polígonos completos y se clasifican por `building:levels`. Se añadió la zona **Mixed Residential-Commercial** (comercio en planta baja, apartamentos arriba).

### Módulo Red Vial

Extrae la jerarquía vial completa de Minneapolis desde OSM.

```bash
cd src && uv run extract_vial.py
# Abre: visualizer/vial/index.html
```

### Módulo Servicios Urbanos

Extrae salud, educación, parques, emergencias, energía, agua y cementerios.

```bash
cd src && uv run extract_services.py
# Abre: visualizer/services/index.html
```

### Módulo Transporte

Extrae Light Rail, BRT, rutas de bus, paradas, cocheras y ciclovías.

```bash
cd src && uv run extract_transport.py
# Abre: visualizer/transport/index.html
```

### Ejecución completa (todos los módulos)

```bash
cd src
uv run extract_zoning.py    # ~15 min
uv run extract_vial.py      # ~2 min
uv run extract_services.py  # ~3 min
uv run extract_transport.py # ~5 min
```
```

- [ ] **Step 2: Commit final**

```bash
git add README.es.md
git commit -m "docs: update README with v2.0 modules and bugfix notes"
git push origin main
```

---

## Verificación Final

- [ ] Ejecutar todos los extractores en secuencia y verificar que terminan sin errores
- [ ] Abrir los 4 visualizadores en el navegador y confirmar que muestran datos reales
- [ ] En `visualizer/index.html` (zonificación): verificar que el Downtown muestra alta densidad residencial (edificios de apartamentos en verde oscuro)
- [ ] En `visualizer/vial/index.html`: verificar I-35W e I-94 como líneas rojas gruesas
- [ ] En `visualizer/services/index.html`: verificar Chain of Lakes como polígonos verdes
- [ ] En `visualizer/transport/index.html`: verificar Midtown Greenway como línea verde E-O
