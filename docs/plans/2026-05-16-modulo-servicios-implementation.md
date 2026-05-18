# Sesión 3 — Módulo Servicios — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar el Módulo Servicios — 5 capas alineadas a las solapas de servicios base de Cities: Skylines 2 (health, education, fire, admin, parks) extraídas de OpenStreetMap y renderizadas como overlay sobre el visualizador existente.

**Architecture:** Mismo patrón que vial (Sesión 2): sub-paquete Python en `src/services/` con tres módulos (`zones.py`, `classifiers.py`, `extract.py`) que produce un único `visualizer/datos_servicios.js` prebuilt. El visualizer extiende su Layer Control y leyenda con una nueva sección "Servicios" debajo de "Vías". Sin visualizer separado.

**Tech Stack:** Python 3.11 + uv | Overpass API (multi-endpoint via `shared.overpass_client`) | Leaflet.js (Canvas para polígonos, `L.divIcon` markers para puntos) | CartoDB Dark Matter basemap | pytest.

**Design spec:** [`docs/plans/2026-05-16-modulo-servicios.md`](./2026-05-16-modulo-servicios.md)

**Workspace:** `C:/Users/osyanne/Documents/Claude/Projects/Proyecto mineapolis/cs2-minneapolis-zoning/`

---

## File Structure

### Crear

| Archivo | Responsabilidad |
|---|---|
| `src/services/__init__.py` | Marca de paquete (vacío) |
| `src/services/zones.py` | `SERVICES_LABELS`, `SERVICES_COLORS`, `MINNEAPOLIS_BBOX` reexport, `build_services_query(bbox)` |
| `src/services/classifiers.py` | `TAG_TO_CATEGORY`, `NAME_REQUIRED_SUBTYPES`, `classify_service(tags, element_type)`, `infer_geometry_kind(element)` |
| `src/services/extract.py` | Pipeline CLI: query → classify → split nodes/ways → escribir JS |
| `tests/services/__init__.py` | Marca de paquete (vacío) |
| `tests/services/test_zones.py` | Tests: labels, colors, bbox, query builder |
| `tests/services/test_classifiers.py` | Tests: clasificación, filtros `name=*`, geometría |
| `tests/services/test_extract.py` | Tests: pipeline con fixture mock de Overpass |

### Modificar

| Archivo | Cambio |
|---|---|
| `src/pyproject.toml` | Entry point `extract-services` + añadir `services` al package list |
| `.gitignore` | Líneas `datos_servicios.js` y `visualizer/datos_servicios.js` |
| `visualizer/index.html` | Script tag + `SERVICES_TYPES` + `serviceGroups` + render functions + Layer Control + leyenda |
| `README.md` | Sección nueva "Módulo Servicios" |
| `README.es.md` | Sección nueva "Módulo Servicios" |
| `METHODOLOGY.md` | Sección 15 "Módulo Servicios" |

### No tocar

`src/shared/overpass_client.py`, `src/vial/*`, `src/zoning/*`, tests existentes.

---

## Tareas

### Tarea 1: Confirmar plan en disco y commitearlo

**Files:**
- Create: `docs/plans/2026-05-16-modulo-servicios-implementation.md` (este archivo)

- [ ] **Step 1: Confirmar que el plan existe en disco**

```bash
ls docs/plans/2026-05-16-modulo-servicios-implementation.md
```

Expected: el archivo existe (sin error).

- [ ] **Step 2: Commit**

```bash
git add docs/plans/2026-05-16-modulo-servicios-implementation.md
git commit -m "docs(services): plan de implementación Sesión 3 — Módulo Servicios"
```

---

### Tarea 2: Scaffold del paquete `src/services/` y `tests/services/`

**Files:**
- Create: `src/services/__init__.py`
- Create: `tests/services/__init__.py`

- [ ] **Step 1: Crear `src/services/__init__.py` vacío**

Crear archivo con contenido:
```python
"""Módulo Servicios CS2 (Sesión 3)."""
```

- [ ] **Step 2: Crear `tests/services/__init__.py` vacío**

Crear archivo con contenido:
```python
"""Tests del módulo services (Sesión 3)."""
```

- [ ] **Step 3: Verificar estructura**

```bash
ls src/services/__init__.py tests/services/__init__.py
```

Expected: ambos archivos existen.

- [ ] **Step 4: Commit**

```bash
git add src/services/__init__.py tests/services/__init__.py
git commit -m "feat(services): scaffold del paquete src/services/ y tests/services/"
```

---

### Tarea 3: `src/services/zones.py` — labels, colors, bbox y query builder

**Files:**
- Create: `src/services/zones.py`
- Test: `tests/services/test_zones.py`

- [ ] **Step 1: Crear test fallido `tests/services/test_zones.py`**

Crear archivo con el siguiente contenido:

```python
"""Tests del módulo services.zones (Sesión 3)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))


BBOX = "44.86,-93.38,45.05,-93.17"

# Las 5 capas de servicios CS2
EXPECTED_SERVICES_KEYS = {"health", "education", "fire", "admin", "parks"}


def test_services_labels_has_five_keys():
    from services.zones import SERVICES_LABELS
    assert set(SERVICES_LABELS.keys()) == EXPECTED_SERVICES_KEYS


def test_services_labels_are_human_readable():
    from services.zones import SERVICES_LABELS
    assert SERVICES_LABELS["health"]    == "Atención sanitaria y funeraria"
    assert SERVICES_LABELS["education"] == "Educación e investigación"
    assert SERVICES_LABELS["fire"]      == "Bomberos"
    assert SERVICES_LABELS["admin"]     == "Policía y administración"
    assert SERVICES_LABELS["parks"]     == "Parques"


def test_services_colors_match_labels():
    from services.zones import SERVICES_LABELS, SERVICES_COLORS
    assert set(SERVICES_LABELS.keys()) == set(SERVICES_COLORS.keys())


def test_services_colors_have_color_and_char():
    from services.zones import SERVICES_COLORS
    for key, entry in SERVICES_COLORS.items():
        assert "color" in entry, f"falta 'color' en {key}"
        assert "char" in entry, f"falta 'char' en {key}"
        assert entry["color"].startswith("#"), f"color de {key} no es hex"
        assert len(entry["char"]) == 1, f"char de {key} debe ser 1 caracter"


def test_services_chars_are_unique():
    from services.zones import SERVICES_COLORS
    chars = [entry["char"] for entry in SERVICES_COLORS.values()]
    assert len(chars) == len(set(chars)), f"chars duplicados: {chars}"


def test_bbox_reexport_matches_vial():
    from services.zones import MINNEAPOLIS_BBOX
    from vial.zones import MINNEAPOLIS_BBOX as VIAL_BBOX
    assert MINNEAPOLIS_BBOX == VIAL_BBOX


def test_build_services_query_contains_bbox():
    from services.zones import build_services_query
    q = build_services_query(BBOX)
    assert BBOX in q


def test_build_services_query_contains_all_amenities():
    from services.zones import build_services_query
    q = build_services_query(BBOX)
    for amenity in [
        "hospital", "clinic", "doctors", "funeral_directors", "crematorium",
        "school", "university", "college", "kindergarten", "research_institute",
        "fire_station",
        "police", "townhall", "courthouse", "prison",
        "library", "theatre", "arts_centre", "cinema",
    ]:
        assert amenity in q, f"falta amenity '{amenity}' en query"


def test_build_services_query_contains_leisure():
    from services.zones import build_services_query
    q = build_services_query(BBOX)
    for leisure in ["park", "nature_reserve", "garden", "playground", "sports_centre"]:
        assert leisure in q, f"falta leisure '{leisure}' en query"


def test_build_services_query_cemetery_only_ways():
    from services.zones import build_services_query
    q = build_services_query(BBOX)
    assert 'way["landuse"="cemetery"]' in q
    assert 'node["landuse"="cemetery"]' not in q


def test_build_services_query_contains_office_and_tourism():
    from services.zones import build_services_query
    q = build_services_query(BBOX)
    assert "office" in q
    assert "government" in q
    assert "research" in q
    assert "tourism" in q
    assert "museum" in q


def test_build_services_query_uses_out_body_geom():
    from services.zones import build_services_query
    q = build_services_query(BBOX)
    assert "out body geom" in q
    assert "[out:json]" in q
```

- [ ] **Step 2: Correr tests — deben fallar con ImportError**

```bash
cd src && uv run pytest ../tests/services/test_zones.py -v
```

Expected: todos los tests FAIL con `ModuleNotFoundError: No module named 'services.zones'`

- [ ] **Step 3: Implementar `src/services/zones.py`**

Crear archivo con el siguiente contenido:

```python
"""
services/zones.py — Modelo de servicios públicos CS2 (Sesión 3, 2026-05-16)
=============================================================================
5 capas alineadas a las solapas de servicios base de Cities: Skylines 2 con
buena cobertura OpenStreetMap:

  health      → Atención sanitaria y funeraria (hospitales + cementerios)
  education   → Educación e investigación (schools + research labs)
  fire        → Bomberos
  admin       → Policía y administración (incl. landmarks culturales)
  parks       → Parques (incl. playgrounds y sports centres)

Diseño de query:
  - UNA sola query Overpass cubre las 5 capas con regex sobre amenity/leisure
  - Incluye también office=government, office=research, tourism=museum
  - out body geom: cada way trae su geometría completa en una pasada
  - timeout 90s (esperado ~600-900 features en bbox de Minneapolis)
"""

SERVICES_LABELS = {
    "health":    "Atención sanitaria y funeraria",
    "education": "Educación e investigación",
    "fire":      "Bomberos",
    "admin":     "Policía y administración",
    "parks":     "Parques",
}

SERVICES_COLORS = {
    "health":    {"color": "#D81B60", "char": "H"},
    "education": {"color": "#FDD835", "char": "E"},
    "fire":      {"color": "#E64A19", "char": "B"},
    "admin":     {"color": "#1E88E5", "char": "A"},
    "parks":     {"color": "#43A047", "char": "P"},
}

# Reexport — pipelines de zoning, vial y services comparten bbox
MINNEAPOLIS_BBOX = "44.86,-93.38,45.05,-93.17"


def build_services_query(bbox: str) -> str:
    """
    Construir una query Overpass QL que devuelve todos los servicios en los
    5 buckets CS2 (health, education, fire, admin, parks), incluyendo nodes
    y ways con geometría completa.

    El splitting nodes/ways y la clasificación se hacen en pipeline, no en
    la query.
    """
    amenity_regex = (
        "hospital|clinic|doctors|funeral_directors|crematorium|"
        "school|university|college|kindergarten|research_institute|"
        "fire_station|"
        "police|townhall|courthouse|prison|library|theatre|arts_centre|cinema"
    )
    leisure_regex = "park|nature_reserve|garden|playground|sports_centre"

    return f"""
[out:json][timeout:90];
(
  node["amenity"~"^({amenity_regex})$"]({bbox});
  way["amenity"~"^({amenity_regex})$"]({bbox});

  node["leisure"~"^({leisure_regex})$"]({bbox});
  way["leisure"~"^({leisure_regex})$"]({bbox});

  way["landuse"="cemetery"]({bbox});

  node["office"~"^(government|research)$"]({bbox});
  way["office"~"^(government|research)$"]({bbox});

  node["tourism"="museum"]({bbox});
  way["tourism"="museum"]({bbox});
);
out body geom;
""".strip()
```

- [ ] **Step 4: Correr tests — deben pasar**

```bash
cd src && uv run pytest ../tests/services/test_zones.py -v
```

Expected: todos los tests PASS.

- [ ] **Step 5: Verificar que tests de vial y zoning siguen pasando**

```bash
cd src && uv run pytest ../tests/ -v
```

Expected: todos los tests pasan (vial, zoning y services).

- [ ] **Step 6: Commit**

```bash
git add src/services/zones.py tests/services/test_zones.py
git commit -m "feat(services): zones.py con labels, colors, bbox y query builder"
```

---

### Tarea 4: `src/services/classifiers.py` — TAG_TO_CATEGORY, classify_service, infer_geometry_kind

**Files:**
- Create: `src/services/classifiers.py`
- Test: `tests/services/test_classifiers.py`

- [ ] **Step 1: Crear test fallido `tests/services/test_classifiers.py`**

Crear archivo con el siguiente contenido:

```python
"""Tests del módulo services.classifiers (Sesión 3)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))


# ── classify_service ────────────────────────────────────────────────────────

def test_hospital_classifies_to_health():
    from services.classifiers import classify_service
    assert classify_service({"amenity": "hospital"}, "way") == "health"


def test_clinic_classifies_to_health():
    from services.classifiers import classify_service
    assert classify_service({"amenity": "clinic"}, "node") == "health"


def test_funeral_directors_classifies_to_health():
    from services.classifiers import classify_service
    assert classify_service({"amenity": "funeral_directors"}, "way") == "health"


def test_cemetery_way_is_health():
    from services.classifiers import classify_service
    assert classify_service({"landuse": "cemetery"}, "way") == "health"


def test_cemetery_node_is_rejected():
    from services.classifiers import classify_service
    assert classify_service({"landuse": "cemetery"}, "node") is None


def test_school_classifies_to_education():
    from services.classifiers import classify_service
    assert classify_service({"amenity": "school"}, "way") == "education"


def test_university_classifies_to_education():
    from services.classifiers import classify_service
    assert classify_service({"amenity": "university"}, "way") == "education"


def test_kindergarten_classifies_to_education():
    from services.classifiers import classify_service
    assert classify_service({"amenity": "kindergarten"}, "node") == "education"


def test_office_research_is_education():
    from services.classifiers import classify_service
    assert classify_service({"office": "research"}, "way") == "education"


def test_school_without_name_still_classified():
    """name=* NO requerido para schools (solo para culturales en admin)."""
    from services.classifiers import classify_service
    assert classify_service({"amenity": "school"}, "way") == "education"


def test_fire_station_classifies_to_fire():
    from services.classifiers import classify_service
    assert classify_service({"amenity": "fire_station"}, "way") == "fire"


def test_police_classifies_to_admin():
    from services.classifiers import classify_service
    assert classify_service({"amenity": "police"}, "way") == "admin"


def test_townhall_classifies_to_admin():
    from services.classifiers import classify_service
    assert classify_service({"amenity": "townhall"}, "way") == "admin"


def test_prison_classifies_to_admin():
    from services.classifiers import classify_service
    assert classify_service({"amenity": "prison"}, "way") == "admin"


def test_office_government_is_admin():
    from services.classifiers import classify_service
    assert classify_service({"office": "government"}, "way") == "admin"


def test_library_with_name_is_admin():
    from services.classifiers import classify_service
    assert classify_service({"amenity": "library", "name": "Hennepin Library"}, "way") == "admin"


def test_library_without_name_rejected():
    from services.classifiers import classify_service
    assert classify_service({"amenity": "library"}, "way") is None


def test_museum_with_name_is_admin():
    from services.classifiers import classify_service
    assert classify_service({"tourism": "museum", "name": "Walker Art Center"}, "way") == "admin"


def test_museum_without_name_rejected():
    from services.classifiers import classify_service
    assert classify_service({"tourism": "museum"}, "way") is None


def test_theatre_with_name_is_admin():
    from services.classifiers import classify_service
    assert classify_service({"amenity": "theatre", "name": "Guthrie"}, "way") == "admin"


def test_theatre_without_name_rejected():
    from services.classifiers import classify_service
    assert classify_service({"amenity": "theatre"}, "way") is None


def test_arts_centre_without_name_rejected():
    from services.classifiers import classify_service
    assert classify_service({"amenity": "arts_centre"}, "way") is None


def test_cinema_with_name_is_admin():
    from services.classifiers import classify_service
    assert classify_service({"amenity": "cinema", "name": "Uptown Theatre"}, "way") == "admin"


def test_park_classifies_to_parks():
    from services.classifiers import classify_service
    assert classify_service({"leisure": "park"}, "way") == "parks"


def test_playground_classifies_to_parks():
    from services.classifiers import classify_service
    assert classify_service({"leisure": "playground"}, "node") == "parks"


def test_sports_centre_classifies_to_parks():
    from services.classifiers import classify_service
    assert classify_service({"leisure": "sports_centre"}, "way") == "parks"


def test_garden_classifies_to_parks():
    from services.classifiers import classify_service
    assert classify_service({"leisure": "garden"}, "way") == "parks"


def test_nature_reserve_classifies_to_parks():
    from services.classifiers import classify_service
    assert classify_service({"leisure": "nature_reserve"}, "way") == "parks"


def test_irrelevant_amenity_is_none():
    from services.classifiers import classify_service
    assert classify_service({"amenity": "restaurant"}, "way") is None


def test_no_relevant_tag_is_none():
    from services.classifiers import classify_service
    assert classify_service({"building": "yes"}, "way") is None


def test_empty_tags_is_none():
    from services.classifiers import classify_service
    assert classify_service({}, "node") is None


# ── infer_geometry_kind ─────────────────────────────────────────────────────

def test_node_is_point():
    from services.classifiers import infer_geometry_kind
    assert infer_geometry_kind({"type": "node"}) == "point"


def test_closed_way_is_polygon():
    from services.classifiers import infer_geometry_kind
    el = {"type": "way", "geometry": [
        {"lat": 1.0, "lon": 1.0},
        {"lat": 1.0, "lon": 2.0},
        {"lat": 2.0, "lon": 2.0},
        {"lat": 1.0, "lon": 1.0},
    ]}
    assert infer_geometry_kind(el) == "polygon"


def test_open_way_is_point():
    from services.classifiers import infer_geometry_kind
    el = {"type": "way", "geometry": [
        {"lat": 1.0, "lon": 1.0},
        {"lat": 1.0, "lon": 2.0},
        {"lat": 2.0, "lon": 2.0},
    ]}
    assert infer_geometry_kind(el) == "point"


def test_short_way_is_point():
    from services.classifiers import infer_geometry_kind
    el = {"type": "way", "geometry": [
        {"lat": 1.0, "lon": 1.0},
        {"lat": 1.0, "lon": 2.0},
    ]}
    assert infer_geometry_kind(el) == "point"


def test_way_without_geometry_is_point():
    from services.classifiers import infer_geometry_kind
    el = {"type": "way"}
    assert infer_geometry_kind(el) == "point"
```

- [ ] **Step 2: Correr tests — deben fallar con ImportError**

```bash
cd src && uv run pytest ../tests/services/test_classifiers.py -v
```

Expected: todos los tests FAIL con `ModuleNotFoundError: No module named 'services.classifiers'`

- [ ] **Step 3: Implementar `src/services/classifiers.py`**

Crear archivo con el siguiente contenido:

```python
"""
services/classifiers.py — Clasificación de tags OSM → categoría CS2 (Sesión 3)
==============================================================================
Mapeo tabla → categoría. Sin heurísticas. El tag amenity/leisure/landuse/
office/tourism es suficiente para decidir.

Reglas especiales:
- landuse=cemetery solo cuenta si element_type=='way'
- Subtypes culturales en admin (library, theatre, museum, cinema, arts_centre)
  requieren tag name=*
"""

# Single source of truth — mapeo (key, value) → categoría
TAG_TO_CATEGORY = {
    # health (sanitaria + funeraria)
    ("amenity", "hospital"):           "health",
    ("amenity", "clinic"):             "health",
    ("amenity", "doctors"):            "health",
    ("amenity", "funeral_directors"):  "health",
    ("amenity", "crematorium"):        "health",
    ("landuse", "cemetery"):           "health",   # solo ways
    # education + research
    ("amenity", "school"):             "education",
    ("amenity", "university"):         "education",
    ("amenity", "college"):            "education",
    ("amenity", "kindergarten"):       "education",
    ("amenity", "research_institute"): "education",
    ("office",  "research"):           "education",
    # fire
    ("amenity", "fire_station"):       "fire",
    # admin (incluye landmarks culturales)
    ("amenity", "police"):             "admin",
    ("amenity", "townhall"):           "admin",
    ("amenity", "courthouse"):         "admin",
    ("amenity", "prison"):             "admin",
    ("amenity", "library"):            "admin",
    ("amenity", "theatre"):            "admin",
    ("amenity", "arts_centre"):        "admin",
    ("amenity", "cinema"):             "admin",
    ("office",  "government"):         "admin",
    ("tourism", "museum"):             "admin",
    # parks
    ("leisure", "park"):               "parks",
    ("leisure", "nature_reserve"):     "parks",
    ("leisure", "garden"):             "parks",
    ("leisure", "playground"):         "parks",
    ("leisure", "sports_centre"):      "parks",
}

# Subtypes que requieren name=* (solo culturales en admin)
NAME_REQUIRED_SUBTYPES = {
    ("amenity", "library"),
    ("amenity", "theatre"),
    ("amenity", "arts_centre"),
    ("amenity", "cinema"),
    ("tourism", "museum"),
}


def classify_service(tags: dict, element_type: str) -> str | None:
    """
    Devuelve la categoría ('health'|'education'|'fire'|'admin'|'parks') o
    None si los tags no clasifican.

    Reglas:
    - Itera los tags y devuelve la PRIMERA categoría matched (determinístico
      por orden de iteración de dict en Python 3.7+).
    - landuse=cemetery solo cuenta si element_type=='way' (cementerios sin
      polígono no aportan).
    - Subtypes culturales (library, theatre, museum, cinema, arts_centre)
      requieren tag name=*.
    """
    for key, value in tags.items():
        cat = TAG_TO_CATEGORY.get((key, value))
        if cat is None:
            continue
        # cementerios solo ways
        if (key, value) == ("landuse", "cemetery") and element_type == "node":
            return None
        # culturales requieren name
        if (key, value) in NAME_REQUIRED_SUBTYPES and not tags.get("name"):
            return None
        return cat
    return None


def infer_geometry_kind(element: dict) -> str:
    """
    Devuelve 'polygon' si el way está cerrado (>=4 nodos, primer==último),
    sino 'point'. Nodes siempre son 'point'. Ways sin geometría también 'point'.
    """
    if element["type"] != "way":
        return "point"
    geom = element.get("geometry", [])
    if len(geom) < 4:
        return "point"
    first, last = geom[0], geom[-1]
    if first["lat"] == last["lat"] and first["lon"] == last["lon"]:
        return "polygon"
    return "point"
```

- [ ] **Step 4: Correr tests — deben pasar**

```bash
cd src && uv run pytest ../tests/services/test_classifiers.py -v
```

Expected: todos los tests PASS.

- [ ] **Step 5: Correr todos los tests del repo**

```bash
cd src && uv run pytest ../tests/ -v
```

Expected: todos los tests pasan.

- [ ] **Step 6: Commit**

```bash
git add src/services/classifiers.py tests/services/test_classifiers.py
git commit -m "feat(services): classifiers.py con TAG_TO_CATEGORY y geometry inference"
```

---

### Tarea 5: `src/services/extract.py` — pipeline + make_feature + JS writer

**Files:**
- Create: `src/services/extract.py`
- Test: `tests/services/test_extract.py`

- [ ] **Step 1: Crear test fallido `tests/services/test_extract.py`**

Crear archivo con el siguiente contenido:

```python
"""Tests del pipeline services.extract (Sesión 3)."""
import sys, os, json, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))


def _make_fixture_response():
    """Mock de respuesta Overpass con 1 hospital way, 1 clinic node, 1 park way,
    1 library con name, 1 museum sin name (que debe rechazarse), 1 restaurant
    (irrelevante, debe rechazarse)."""
    return {
        "elements": [
            {
                "type": "way", "id": 1,
                "tags": {"amenity": "hospital", "name": "Hennepin Healthcare HCMC"},
                "geometry": [
                    {"lat": 44.97, "lon": -93.26},
                    {"lat": 44.97, "lon": -93.25},
                    {"lat": 44.98, "lon": -93.25},
                    {"lat": 44.98, "lon": -93.26},
                    {"lat": 44.97, "lon": -93.26},
                ],
            },
            {
                "type": "node", "id": 2,
                "tags": {"amenity": "clinic", "name": "MinuteClinic"},
                "lat": 44.95, "lon": -93.28,
            },
            {
                "type": "way", "id": 3,
                "tags": {"leisure": "park", "name": "Minnehaha Park"},
                "geometry": [
                    {"lat": 44.91, "lon": -93.20},
                    {"lat": 44.91, "lon": -93.21},
                    {"lat": 44.92, "lon": -93.21},
                    {"lat": 44.92, "lon": -93.20},
                    {"lat": 44.91, "lon": -93.20},
                ],
            },
            {
                "type": "way", "id": 4,
                "tags": {"amenity": "library", "name": "Hennepin Library Central"},
                "geometry": [
                    {"lat": 44.97, "lon": -93.27},
                    {"lat": 44.97, "lon": -93.26},
                    {"lat": 44.98, "lon": -93.26},
                    {"lat": 44.98, "lon": -93.27},
                    {"lat": 44.97, "lon": -93.27},
                ],
            },
            # Museum sin name — debe rechazarse
            {"type": "node", "id": 5, "tags": {"tourism": "museum"}, "lat": 1, "lon": 1},
            # Restaurant — irrelevante
            {"type": "node", "id": 6, "tags": {"amenity": "restaurant"}, "lat": 1, "lon": 1},
        ]
    }


def test_extract_writes_two_data_objects(tmp_path, monkeypatch):
    from services import extract
    monkeypatch.setattr(extract, "query_with_retry",
                        lambda q, label="services": _make_fixture_response())
    out_path = tmp_path / "datos_servicios.js"
    extract.run(bbox="44.86,-93.38,45.05,-93.17", out_path=out_path)

    content = out_path.read_text(encoding="utf-8")
    assert "DATA_SERVICES_POLYGONS" in content
    assert "DATA_SERVICES_POINTS" in content
    assert "DATA_SERVICES_META" in content


def test_extract_splits_polygons_and_points(tmp_path, monkeypatch):
    from services import extract
    monkeypatch.setattr(extract, "query_with_retry",
                        lambda q, label="services": _make_fixture_response())
    out_path = tmp_path / "datos_servicios.js"
    extract.run(bbox="44.86,-93.38,45.05,-93.17", out_path=out_path)

    content = out_path.read_text(encoding="utf-8")
    # El hospital (way cerrado) va a polygons.health
    assert "Hennepin Healthcare HCMC" in content
    # La clínica (node) va a points.health
    assert "MinuteClinic" in content
    # El park (way cerrado) va a polygons.parks
    assert "Minnehaha Park" in content
    # La library (way cerrado con name) va a polygons.admin
    assert "Hennepin Library Central" in content


def test_extract_skips_unclassified(tmp_path, monkeypatch):
    from services import extract
    monkeypatch.setattr(extract, "query_with_retry",
                        lambda q, label="services": _make_fixture_response())
    out_path = tmp_path / "datos_servicios.js"
    extract.run(bbox="44.86,-93.38,45.05,-93.17", out_path=out_path)

    content = out_path.read_text(encoding="utf-8")
    # restaurant id=6 no debe aparecer
    assert '"id":6' not in content
    # museum sin name id=5 tampoco
    assert '"id":5' not in content


def test_extract_preserves_subtype_in_feature(tmp_path, monkeypatch):
    from services import extract
    monkeypatch.setattr(extract, "query_with_retry",
                        lambda q, label="services": _make_fixture_response())
    out_path = tmp_path / "datos_servicios.js"
    extract.run(bbox="44.86,-93.38,45.05,-93.17", out_path=out_path)

    content = out_path.read_text(encoding="utf-8")
    # El subtype "hospital" y "clinic" deben estar en el output
    assert '"subtype":"hospital"' in content
    assert '"subtype":"clinic"' in content
    assert '"subtype":"library"' in content


def test_extract_meta_has_bbox_and_total(tmp_path, monkeypatch):
    from services import extract
    monkeypatch.setattr(extract, "query_with_retry",
                        lambda q, label="services": _make_fixture_response())
    out_path = tmp_path / "datos_servicios.js"
    extract.run(bbox="44.86,-93.38,45.05,-93.17", out_path=out_path)

    content = out_path.read_text(encoding="utf-8")
    # Meta debe tener bbox y total_features
    meta_match = re.search(r"const DATA_SERVICES_META\s*=\s*(\{[^;]+\});", content)
    assert meta_match, "DATA_SERVICES_META no encontrado"
    meta = json.loads(meta_match.group(1))
    assert meta["bbox"] == "44.86,-93.38,45.05,-93.17"
    # 4 features clasificados (hospital, clinic, park, library)
    assert meta["total_features"] == 4
    assert "generated_at" in meta


def test_extract_all_five_categories_present_even_if_empty(tmp_path, monkeypatch):
    from services import extract
    monkeypatch.setattr(extract, "query_with_retry",
                        lambda q, label="services": _make_fixture_response())
    out_path = tmp_path / "datos_servicios.js"
    extract.run(bbox="44.86,-93.38,45.05,-93.17", out_path=out_path)

    content = out_path.read_text(encoding="utf-8")
    # Las 5 claves siempre presentes en POLYGONS y POINTS, incluso vacías
    for key in ["health", "education", "fire", "admin", "parks"]:
        # Debe estar en al menos uno de los dos objetos
        assert f'"{key}":' in content, f"falta clave '{key}'"
```

- [ ] **Step 2: Correr tests — deben fallar**

```bash
cd src && uv run pytest ../tests/services/test_extract.py -v
```

Expected: todos los tests FAIL con `ModuleNotFoundError: No module named 'services.extract'`

- [ ] **Step 3: Implementar `src/services/extract.py`**

Crear archivo con el siguiente contenido:

```python
#!/usr/bin/env python3
"""
extract.py — CS2 Minneapolis Services Pipeline (Sesión 3)
==========================================================
Extrae los servicios públicos reales desde OpenStreetMap y los exporta como
un archivo JS listo para el visualizador Leaflet (overlay encima de los mapas
de zonificación y vial existentes).

Salida (`visualizer/datos_servicios.js`):
    const DATA_SERVICES_POLYGONS = {
      health:    [{ id, name, subtype, coords, tags }, ...],
      education: [...], fire: [...], admin: [...], parks: [...],
    };
    const DATA_SERVICES_POINTS = {
      health:    [{ id, name, subtype, coord, tags }, ...],
      education: [...], fire: [...], admin: [...], parks: [...],
    };
    const DATA_SERVICES_META = { bbox, generated_at, total_features };

Uso:
    cd src
    uv run extract-services
    uv run extract-services --bbox "44.86,-93.38,45.05,-93.17"
    uv run extract-services --out ../visualizer/datos_servicios.js
"""

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from shared.overpass_client import query_with_retry
from services.classifiers import classify_service, infer_geometry_kind
from services.zones import SERVICES_LABELS, MINNEAPOLIS_BBOX, build_services_query


# ── Feature assembly ─────────────────────────────────────────────────────────

def make_feature(element: dict, cat: str, kind: str) -> dict:
    """
    Construye el dict de feature para el output JS.

    Para kind='polygon': incluye 'coords' como lista de [lat, lon].
    Para kind='point': incluye 'coord' como [lat, lon] (centroide o primer nodo).
    """
    tags = element.get("tags") or {}
    subtype = (tags.get("amenity") or tags.get("leisure") or tags.get("landuse")
               or tags.get("office") or tags.get("tourism") or "")

    feat = {
        "id": element["id"],
        "name": tags.get("name", ""),
        "subtype": subtype,
        "tags": dict(tags),
    }

    if kind == "polygon":
        geom = element.get("geometry") or []
        feat["coords"] = [[pt["lat"], pt["lon"]] for pt in geom]
    else:  # point
        if element["type"] == "node":
            feat["coord"] = [element["lat"], element["lon"]]
        else:
            # way clasificado como point (geometría corta o no cerrada) —
            # usar primer nodo como anchor
            geom = element.get("geometry") or []
            if geom:
                feat["coord"] = [geom[0]["lat"], geom[0]["lon"]]
            else:
                feat["coord"] = [0.0, 0.0]  # fallback defensivo

    return feat


# ── Pipeline ─────────────────────────────────────────────────────────────────

def run(bbox: str, out_path: Path) -> dict:
    """
    Ejecuta el pipeline completo: query → classify → split → write.

    Devuelve dict de meta para tests/logging.
    """
    query = build_services_query(bbox)

    # Buckets: cat → {polygon: [...], point: [...]}
    polygons: dict[str, list] = defaultdict(list)
    points: dict[str, list] = defaultdict(list)
    skipped_class = 0

    result = query_with_retry(query, "services")
    elements = result.get("elements", [])

    for el in elements:
        tags = el.get("tags") or {}
        cat = classify_service(tags, el["type"])
        if cat is None:
            skipped_class += 1
            continue
        kind = infer_geometry_kind(el)
        feat = make_feature(el, cat, kind)
        if kind == "polygon":
            polygons[cat].append(feat)
        else:
            points[cat].append(feat)

    # Asegurar las 5 claves siempre presentes
    for key in SERVICES_LABELS:
        polygons.setdefault(key, [])
        points.setdefault(key, [])

    total = sum(len(v) for v in polygons.values()) + sum(len(v) for v in points.values())

    meta = {
        "bbox": bbox,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_features": total,
    }

    # ── Write output ─────────────────────────────────────────────────────────
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        f.write("// Auto-generated by extract-services — do not edit manually\n")
        f.write(f"// {meta['generated_at']} — {total} features — bbox {bbox}\n\n")
        f.write("const DATA_SERVICES_POLYGONS = ")
        json.dump(dict(polygons), f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n\n")
        f.write("const DATA_SERVICES_POINTS = ")
        json.dump(dict(points), f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n\n")
        f.write("const DATA_SERVICES_META = ")
        json.dump(meta, f, ensure_ascii=False)
        f.write(";\n")

    return {
        "polygons": polygons,
        "points": points,
        "meta": meta,
        "skipped_class": skipped_class,
    }


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Extract OSM public services for CS2 Minneapolis (Sesión 3)"
    )
    parser.add_argument(
        "--bbox",
        default=MINNEAPOLIS_BBOX,
        help=f"Bounding box 'south,west,north,east' (default: {MINNEAPOLIS_BBOX})",
    )
    parser.add_argument(
        "--out",
        default="../visualizer/datos_servicios.js",
        help="Output .js file path",
    )
    args = parser.parse_args()

    bbox = args.bbox
    out_path = Path(args.out)

    print("CS2 Minneapolis Services Extractor — Sesión 3")
    print(f"Bounding Box : {bbox}")
    print(f"Output       : {out_path}\n")

    print("[1/2] Downloading services from Overpass...")
    summary = run(bbox=bbox, out_path=out_path)

    print("\n[2/2] Splitting features into 5 CS2 buckets...")
    print()
    print(f"  {'category':<12}  polygons  points")
    print(f"  {'-'*12}  {'-'*8}  {'-'*6}")
    for key in SERVICES_LABELS:
        p = len(summary["polygons"].get(key, []))
        n = len(summary["points"].get(key, []))
        print(f"  {key:<12}  {p:>8}  {n:>6}")
    print(f"  {'-'*12}  {'-'*8}  {'-'*6}")
    total = summary["meta"]["total_features"]
    print(f"  {'TOTAL':<12}  {total:>17}")
    print(f"\n  skipped (no classifier): {summary['skipped_class']}")
    print(f"\n[OK] Wrote {out_path} ({out_path.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Correr tests — deben pasar**

```bash
cd src && uv run pytest ../tests/services/test_extract.py -v
```

Expected: todos los tests PASS.

- [ ] **Step 5: Correr todos los tests del repo**

```bash
cd src && uv run pytest ../tests/ -v
```

Expected: todos los tests del repo pasan (vial, zoning, services).

- [ ] **Step 6: Commit**

```bash
git add src/services/extract.py tests/services/test_extract.py
git commit -m "feat(services): extract.py pipeline con make_feature + JS writer"
```

---

### Tarea 6: Actualizar `src/pyproject.toml` — entry point y package list

**Files:**
- Modify: `src/pyproject.toml`

- [ ] **Step 1: Leer el archivo actual**

```bash
cat src/pyproject.toml
```

- [ ] **Step 2: Añadir entry point y package**

Modificar `src/pyproject.toml`:

En la sección `[project.scripts]`, añadir línea:
```toml
extract-services = "services.extract:main"
```

Queda así:
```toml
[project.scripts]
extract-zoning  = "zoning.extract:main"
extract-vial    = "vial.extract:main"
extract-services = "services.extract:main"
```

En la sección `[tool.hatch.build.targets.wheel]`, añadir `"services"` a packages:
```toml
[tool.hatch.build.targets.wheel]
packages = ["shared", "zoning", "vial", "services"]
```

- [ ] **Step 3: Regenerar uv.lock**

```bash
cd src && uv sync
```

Expected: `uv.lock` se actualiza sin errores.

- [ ] **Step 4: Verificar que el entry point se instaló**

```bash
cd src && uv run extract-services --help
```

Expected: imprime ayuda del CLI sin error.

- [ ] **Step 5: Commit**

```bash
git add src/pyproject.toml src/uv.lock
git commit -m "chore(services): entry point extract-services en pyproject.toml"
```

---

### Tarea 7: Actualizar `.gitignore` — datos_servicios.js

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Verificar el patrón existente**

```bash
grep "datos_" .gitignore
```

Expected output incluye `datos_zonificacion.js`, `datos_vial.js`, etc.

- [ ] **Step 2: Editar `.gitignore`**

Localizar el bloque:
```
datos_zonificacion.js
datos_vial.js
visualizer/datos_zonificacion.js
visualizer/datos_vial.js
visualizer/datos_msbuildings.js
```

Añadir las líneas:
```
datos_servicios.js
visualizer/datos_servicios.js
```

Queda así (orden alfabético):
```
datos_servicios.js
datos_vial.js
datos_zonificacion.js
visualizer/datos_msbuildings.js
visualizer/datos_servicios.js
visualizer/datos_vial.js
visualizer/datos_zonificacion.js
```

- [ ] **Step 3: Commit**

```bash
git add .gitignore
git commit -m "chore(services): ignorar datos_servicios.js (distribución via Releases)"
```

---

### Tarea 8: `visualizer/index.html` — script tag, constantes y serviceGroups

**Files:**
- Modify: `visualizer/index.html`

- [ ] **Step 1: Localizar el script tag de vial**

```bash
grep -n "datos_vial.js" visualizer/index.html
```

Expected: una línea como `<script src="datos_vial.js" onerror="window.__noVialPrebuilt=true"></script>`

- [ ] **Step 2: Añadir script tag de services justo debajo del de vial**

Después de la línea del script de vial, añadir:

```html
<script src="datos_servicios.js" onerror="window.__noServicesPrebuilt=true"></script>
```

- [ ] **Step 3: Localizar la sección de constantes de vial (VIAL_TYPES)**

```bash
grep -n "VIAL_TYPES" visualizer/index.html
```

- [ ] **Step 4: Añadir SERVICES_TYPES, threshold y serviceGroups justo después de VIAL_TYPES**

Insertar el siguiente bloque JavaScript después del bloque de VIAL_TYPES:

```javascript
// ── Servicios (Sesión 3) ──────────────────────────────────────────────────
const SERVICES_TYPES = {
  health:    { label: "Atención sanitaria y funeraria", color: "#D81B60", char: "H" },
  education: { label: "Educación e investigación",      color: "#FDD835", char: "E" },
  fire:      { label: "Bomberos",                        color: "#E64A19", char: "B" },
  admin:     { label: "Policía y administración",        color: "#1E88E5", char: "A" },
  parks:     { label: "Parques",                         color: "#43A047", char: "P" },
};

const SERVICES_POINT_ZOOM_THRESHOLD = 12;

const serviceGroups = {};
const servicePointLayers = {};  // refs separadas para tier-hiding
for (const key of Object.keys(SERVICES_TYPES)) {
  serviceGroups[key] = L.layerGroup();
  servicePointLayers[key] = [];
}
```

- [ ] **Step 5: Abrir visualizer y verificar que no rompe nada todavía**

```bash
start visualizer/index.html
```

Expected: el visualizer carga normalmente. En la consola del navegador, `window.SERVICES_TYPES` debe estar definido (verificable con DevTools).

Si `datos_servicios.js` no existe aún, la consola debe mostrar `[services] No prebuilt data` warning después de la próxima tarea (todavía no).

- [ ] **Step 6: Commit**

```bash
git add visualizer/index.html
git commit -m "feat(visualizer): añadir SERVICES_TYPES y serviceGroups en index.html"
```

---

### Tarea 9: `visualizer/index.html` — render functions

**Files:**
- Modify: `visualizer/index.html`

- [ ] **Step 1: Localizar la función `renderVialFeatures` (referencia)**

```bash
grep -n "renderVialFeatures" visualizer/index.html
```

- [ ] **Step 2: Añadir las cuatro funciones de render después de `renderVialFeatures`**

Insertar el siguiente bloque JavaScript:

```javascript
// ── Servicios — render (Sesión 3) ─────────────────────────────────────────

function makeServiceIcon(type) {
  return L.divIcon({
    className: "service-marker",
    html: `<div style="background:${type.color};color:white;border:2px solid rgba(255,255,255,0.7);
                       border-radius:50%;width:22px;height:22px;display:flex;align-items:center;
                       justify-content:center;font-weight:700;font-size:11px;font-family:sans-serif;
                       box-shadow:0 1px 3px rgba(0,0,0,0.6);">${type.char}</div>`,
    iconSize: [22, 22],
    iconAnchor: [11, 11],
    popupAnchor: [0, -11],
  });
}

function buildServicePopup(feat, key) {
  const type = SERVICES_TYPES[key];
  const name = feat.name ? escHtml(feat.name) : "<em>(sin nombre)</em>";
  const subtype = feat.subtype ? escHtml(feat.subtype) : "—";
  const tagsHtml = Object.entries(feat.tags || {})
    .map(([k, v]) => `<div><b>${escHtml(k)}</b>=${escHtml(String(v))}</div>`)
    .join("");
  return `
    <div style="font-size:12px;">
      <div style="font-weight:700;color:${type.color};margin-bottom:4px;">${name}</div>
      <div style="color:#666;margin-bottom:6px;">${escHtml(type.label)} · ${subtype}</div>
      <details><summary style="cursor:pointer;color:#888;">Tags OSM</summary>
        <div style="font-family:monospace;font-size:10px;margin-top:4px;">${tagsHtml}</div>
      </details>
    </div>`;
}

function renderServicesFeatures() {
  if (window.__noServicesPrebuilt) {
    console.warn("[services] No prebuilt data. Run extract-services.");
    return;
  }
  if (typeof DATA_SERVICES_POLYGONS === "undefined" ||
      typeof DATA_SERVICES_POINTS === "undefined") {
    console.warn("[services] datos_servicios.js cargado pero sin constantes esperadas");
    return;
  }

  // Polígonos: siempre visibles
  for (const [key, features] of Object.entries(DATA_SERVICES_POLYGONS)) {
    const type = SERVICES_TYPES[key];
    if (!type) continue;
    for (const feat of features) {
      const poly = L.polygon(feat.coords, {
        color: type.color,
        weight: 1.5,
        opacity: 0.9,
        fillColor: type.color,
        fillOpacity: 0.35,
        renderer: L.canvas(),
      });
      poly.bindPopup(buildServicePopup(feat, key));
      poly.addTo(serviceGroups[key]);
    }
  }

  // Markers (puntos): controlados por tier-hiding
  for (const [key, features] of Object.entries(DATA_SERVICES_POINTS)) {
    const type = SERVICES_TYPES[key];
    if (!type) continue;
    for (const feat of features) {
      const marker = L.marker(feat.coord, { icon: makeServiceIcon(type) });
      marker.bindPopup(buildServicePopup(feat, key));
      servicePointLayers[key].push(marker);
    }
  }

  applyServicesZoomVisibility();
}

function applyServicesZoomVisibility() {
  const zoom = map.getZoom();
  const showMarkers = zoom >= SERVICES_POINT_ZOOM_THRESHOLD;
  for (const key of Object.keys(SERVICES_TYPES)) {
    for (const marker of servicePointLayers[key]) {
      if (showMarkers) {
        if (!serviceGroups[key].hasLayer(marker)) marker.addTo(serviceGroups[key]);
      } else {
        if (serviceGroups[key].hasLayer(marker)) serviceGroups[key].removeLayer(marker);
      }
    }
  }
}
```

- [ ] **Step 3: Localizar el listener `map.on("zoomend"` existente (o crearlo)**

```bash
grep -n "zoomend" visualizer/index.html
```

- [ ] **Step 4: Añadir el listener para zoom visibility de services**

Si ya existe un `map.on("zoomend", ...)`, añadir dentro del callback la línea:
```javascript
applyServicesZoomVisibility();
```

Si no existe, añadir el bloque entero después de la creación del `map`:
```javascript
map.on("zoomend", () => {
  applyServicesZoomVisibility();
});
```

- [ ] **Step 5: Llamar a `renderServicesFeatures()` en el init**

Localizar la línea donde se llama `renderVialFeatures()` o el equivalente:
```bash
grep -n "renderVialFeatures()" visualizer/index.html
```

Justo después de esa línea, añadir:
```javascript
renderServicesFeatures();
```

- [ ] **Step 6: Verificación manual con DevTools**

```bash
start visualizer/index.html
```

En DevTools console:
- Sin `datos_servicios.js` existe aún → debe verse warning `[services] No prebuilt data`.
- `serviceGroups` y `servicePointLayers` deben estar definidos.
- `typeof renderServicesFeatures` debe ser `"function"`.

- [ ] **Step 7: Commit**

```bash
git add visualizer/index.html
git commit -m "feat(visualizer): renderServicesFeatures + makeServiceIcon + popup + zoom hiding"
```

---

### Tarea 10: `visualizer/index.html` — Layer Control y leyenda

**Files:**
- Modify: `visualizer/index.html`

- [ ] **Step 1: Localizar la sección "Vías" del panel lateral**

```bash
grep -n 'class="legend-section"\|Vías\|vial-section' visualizer/index.html
```

- [ ] **Step 2: Añadir sección "Servicios" en el panel lateral**

Justo debajo del bloque HTML de la sección "Vías" del panel lateral, insertar:

```html
<!-- Sección Servicios (Sesión 3) -->
<div class="legend-section" id="services-section">
  <div class="section-header">
    <label class="master-toggle">
      <input type="checkbox" id="services-master" checked />
      <span class="section-title">Servicios</span>
    </label>
  </div>
  <ul class="legend-list" id="services-legend"></ul>
</div>
```

- [ ] **Step 3: Añadir el código JS para poblar la lista y enganchar toggles**

Después de `renderServicesFeatures()` (al final del bloque de render), añadir:

```javascript
// ── Servicios — Layer Control + leyenda ───────────────────────────────────

function buildServicesLegend() {
  const ul = document.getElementById("services-legend");
  if (!ul) return;
  ul.innerHTML = "";
  for (const [key, type] of Object.entries(SERVICES_TYPES)) {
    const li = document.createElement("li");
    li.className = "legend-item";
    li.innerHTML = `
      <label style="display:flex;align-items:center;gap:8px;cursor:pointer;">
        <input type="checkbox" data-services-key="${key}" checked />
        <span style="display:inline-block;width:18px;height:18px;border-radius:50%;
                     background:${type.color};color:white;font-weight:700;font-size:10px;
                     text-align:center;line-height:18px;border:1.5px solid rgba(255,255,255,0.6);">${type.char}</span>
        <span>${escHtml(type.label)}</span>
      </label>
    `;
    ul.appendChild(li);
  }

  // Por defecto: añadir todos los grupos al mapa
  for (const key of Object.keys(serviceGroups)) {
    serviceGroups[key].addTo(map);
  }

  // Toggles individuales
  ul.querySelectorAll("input[data-services-key]").forEach(cb => {
    cb.addEventListener("change", (e) => {
      const key = e.target.dataset.servicesKey;
      if (e.target.checked) serviceGroups[key].addTo(map);
      else map.removeLayer(serviceGroups[key]);
      // Sincronizar master
      const allChecked = Array.from(ul.querySelectorAll("input[data-services-key]"))
        .every(c => c.checked);
      document.getElementById("services-master").checked = allChecked;
    });
  });

  // Master toggle
  const master = document.getElementById("services-master");
  if (master) {
    master.addEventListener("change", (e) => {
      const enabled = e.target.checked;
      ul.querySelectorAll("input[data-services-key]").forEach(cb => {
        cb.checked = enabled;
        const key = cb.dataset.servicesKey;
        if (enabled) serviceGroups[key].addTo(map);
        else map.removeLayer(serviceGroups[key]);
      });
    });
  }
}

// Construir leyenda después del render
buildServicesLegend();
```

- [ ] **Step 4: Verificación visual (todavía sin datos)**

```bash
start visualizer/index.html
```

- ✅ Sección "Servicios" aparece en el panel lateral debajo de "Vías"
- ✅ 5 entradas en la leyenda con círculo de color y char correcto
- ✅ Master toggle "Servicios" funciona (oculta/muestra todo)
- ✅ Toggles individuales funcionan
- ✅ Sin errores en DevTools console (warning de "No prebuilt data" es esperado)

- [ ] **Step 5: Commit**

```bash
git add visualizer/index.html
git commit -m "feat(visualizer): Layer Control y leyenda para sección Servicios"
```

---

### Tarea 11: Generar `datos_servicios.js` real y verificación visual

**Files:**
- Generate: `visualizer/datos_servicios.js` (gitignored)

- [ ] **Step 1: Correr extract-services con bbox de Minneapolis**

```bash
cd src && uv run extract-services
```

Expected output (números aproximados):
```
CS2 Minneapolis Services Extractor — Sesión 3
Bounding Box : 44.86,-93.38,45.05,-93.17
Output       : ../visualizer/datos_servicios.js

[1/2] Downloading services from Overpass...
        [services] -> overpass-api.de (round 1)
        [services] OK overpass-api.de (~800 elementos en 15-30s)

[2/2] Splitting features into 5 CS2 buckets...

  category      polygons  points
  ------------  --------  ------
  health              35      45
  education           80      35
  fire                15       5
  admin               40      25
  parks              250      10
  ------------  --------  ------
  TOTAL                       540

  skipped (no classifier): NNN

[OK] Wrote ../visualizer/datos_servicios.js (XX.X KB)
```

(Los números reales pueden variar. Aceptable: total entre 400 y 1200.)

- [ ] **Step 2: Confirmar que el archivo se generó**

```bash
ls -lh visualizer/datos_servicios.js
```

Expected: archivo existe, ~50-200 KB.

- [ ] **Step 3: Abrir el visualizer**

```bash
start visualizer/index.html
```

- [ ] **Step 4: Checklist de verificación visual**

En el navegador, verificar:
- [ ] Sección "Servicios" en panel lateral con 5 entradas
- [ ] Hennepin Healthcare HCMC aparece como polígono rosa-rojo (`#D81B60`)
- [ ] U of M campus aparece como polígono dorado (`#FDD835`)
- [ ] Minnehaha Park aparece como polígono verde (`#43A047`)
- [ ] Walker Art Center aparece como polígono azul royal (`#1E88E5`) en bucket admin
- [ ] Toggle "Servicios" master oculta/muestra los 5 buckets simultáneamente
- [ ] Toggles individuales funcionan
- [ ] En zoom alto (≥12): markers H/E/B/A/P son visibles en POIs (clínicas, fire stations sin polígono, etc.)
- [ ] En zoom bajo (<12): markers desaparecen, polígonos quedan
- [ ] Click en un polígono → popup con name + subtype + tags colapsables
- [ ] Click en un marker → mismo popup
- [ ] Sin errores en DevTools console
- [ ] Las capas existentes (zonificación, vial) siguen funcionando

- [ ] **Step 5: Si todo OK, no hay commit (el .js está gitignored)**

El archivo `visualizer/datos_servicios.js` queda fuera de git. Se distribuirá por GitHub Release.

---

### Tarea 12: Upload `datos_servicios.js` a GitHub Release v3.1

**Files:**
- Upload: `visualizer/datos_servicios.js` a release v3.1

- [ ] **Step 1: Verificar el tag actual del release**

```bash
gh release view v3.1
```

Expected: listado de assets incluyendo `datos_vial.js` y `datos_zonificacion.js`.

- [ ] **Step 2: Subir el nuevo asset**

```bash
gh release upload v3.1 visualizer/datos_servicios.js --clobber
```

Expected: `✓ uploading datos_servicios.js`.

- [ ] **Step 3: Verificar que aparece en el release**

```bash
gh release view v3.1
```

Expected: `datos_servicios.js` listado entre los assets descargables.

- [ ] **Step 4: Probar descarga**

```bash
gh release download v3.1 -p datos_servicios.js -D /tmp
diff visualizer/datos_servicios.js /tmp/datos_servicios.js
```

Expected: sin output (archivos idénticos).

```bash
rm /tmp/datos_servicios.js
```

---

### Tarea 13: Actualizar `README.md` y `README.es.md`

**Files:**
- Modify: `README.md`
- Modify: `README.es.md`

- [ ] **Step 1: Localizar la sección de módulos en README.es.md**

```bash
grep -n "Módulo Vial\|Módulo Zonificación\|Módulos disponibles" README.es.md
```

- [ ] **Step 2: Añadir entrada de Módulo Servicios en README.es.md**

Después del bloque del Módulo Vial (Sesión 2), añadir:

```markdown
### 🏥 Módulo Servicios (Sesión 3)

5 capas alineadas a las solapas de servicios base de Cities: Skylines 2 con buena cobertura OpenStreetMap:

- **H** Atención sanitaria y funeraria — hospitales, clínicas, cementerios, crematorios
- **E** Educación e investigación — schools, universities, research institutes
- **B** Bomberos — fire stations
- **A** Policía y administración — police HQ, city hall, courthouses, libraries, museos, teatros
- **P** Parques — parks, gardens, playgrounds, sports centres

**Generar prebuilt:**
```bash
cd src
uv run extract-services
```

**Descargar prebuilt:**
[`datos_servicios.js` v3.1](https://github.com/Osyanne/CitiesSkylines2-osm-toolkit/releases/download/v3.1/datos_servicios.js)

**Notas:**
- Polígonos siempre visibles. Markers (POIs sin polígono) se ocultan en zoom < 12.
- Bibliotecas, museos, teatros, arts centres, cinemas comparten el bucket `admin` con policía y oficinas de gobierno.
- Lugares de culto descartados (no presentes en estructura CS2 base).
- Electricidad, agua y residuos diferidos a Sesión 4 (requieren fuentes EIA + MN GIS, no OSM).
```

- [ ] **Step 3: Hacer lo mismo en `README.md` (versión EN)**

Equivalente en inglés:

```markdown
### 🏥 Services Module (Session 3)

5 layers aligned to the base service tabs of Cities: Skylines 2 with good OpenStreetMap coverage:

- **H** Healthcare & Deathcare — hospitals, clinics, cemeteries, crematoriums
- **E** Education & Research — schools, universities, research institutes
- **B** Fire — fire stations
- **A** Police & Administration — police HQ, city hall, courthouses, libraries, museums, theatres
- **P** Parks — parks, gardens, playgrounds, sports centres

**Generate prebuilt:**
```bash
cd src
uv run extract-services
```

**Download prebuilt:**
[`datos_servicios.js` v3.1](https://github.com/Osyanne/CitiesSkylines2-osm-toolkit/releases/download/v3.1/datos_servicios.js)

**Notes:**
- Polygons always visible. Markers (POIs without polygon) hide at zoom < 12.
- Libraries, museums, theatres, arts centres, cinemas share the `admin` bucket with police and government offices.
- Places of worship excluded (not in CS2 base game structure).
- Electricity, water, waste management deferred to Session 4 (require EIA + MN GIS sources, not OSM).
```

- [ ] **Step 4: Commit**

```bash
git add README.md README.es.md
git commit -m "docs(services): sección Módulo Servicios en READMEs"
```

---

### Tarea 14: Actualizar `METHODOLOGY.md` — sección 15

**Files:**
- Modify: `METHODOLOGY.md`

- [ ] **Step 1: Localizar el final de la sección 14 (Vial)**

```bash
grep -n "^## 14\|^## 15\|## 14\." METHODOLOGY.md
```

- [ ] **Step 2: Añadir sección 15**

Después del final de la sección 14, añadir:

```markdown
## 15. Servicios públicos (Sesión 3)

### Extracción

Una única query Overpass cubre 5 categorías alineadas a las solapas de servicios base de Cities: Skylines 2:

| Bucket | Tags OSM | Geometría esperada |
|---|---|---|
| `health` | `amenity=hospital\|clinic\|doctors\|funeral_directors\|crematorium` + `landuse=cemetery` | Mix polígono + punto |
| `education` | `amenity=school\|university\|college\|kindergarten\|research_institute` + `office=research` | Mayormente polígono |
| `fire` | `amenity=fire_station` | Mix |
| `admin` | `amenity=police\|townhall\|courthouse\|prison\|library\|theatre\|arts_centre\|cinema` + `office=government` + `tourism=museum` | Mix |
| `parks` | `leisure=park\|nature_reserve\|garden\|playground\|sports_centre` | Mayormente polígono |

### Filtros

- `landuse=cemetery` se acepta solo como `way` (los nodes se descartan — un cemetery sin polígono no aporta).
- Subtypes culturales dentro de `admin` (library, theatre, museum, cinema, arts_centre) requieren `name=*` para reducir ruido.
- Resto sin filtro.

### Geometría: polígono-preferido + punto-fallback

Cada entidad aparece UNA vez en el output. La función `infer_geometry_kind`:
1. Si `type=node` → `point`
2. Si `type=way` y la geometría tiene ≥4 nodos y primer==último → `polygon`
3. Sino → `point` (usa primer nodo como anchor)

### Rendering

- **Polígonos:** `L.polygon` con Canvas renderer, fill opacity 0.35, stroke 1.5px opacity 0.9. Siempre visibles.
- **Markers:** `L.divIcon` con círculo de 22px (color de bucket + char). Ocultos en `zoom < 12`, visibles en `zoom ≥ 12`. Tier-hiding via `map.on("zoomend")`.
- **Popups:** name (color del bucket) + label + subtype + tags raw colapsables. Todo escapado con `escHtml` (patrón XSS-safe del módulo zoning).

### Diferido a Sesión 4

Electricidad, agua y saneamiento, gestión de residuos requieren fuentes EIA + MN GIS Commons + opendata.minneapolismn.gov (no OSM). Ver `📦 Sesión 4 — Módulo Infraestructura.md` en Obsidian.

### Decisiones documentadas

Spec: [`docs/plans/2026-05-16-modulo-servicios.md`](docs/plans/2026-05-16-modulo-servicios.md)
Plan: [`docs/plans/2026-05-16-modulo-servicios-implementation.md`](docs/plans/2026-05-16-modulo-servicios-implementation.md)
```

- [ ] **Step 3: Actualizar el header de METHODOLOGY.md a v3.2 si tiene versión**

```bash
head -5 METHODOLOGY.md
```

Si el header dice "v3.1" o similar, actualizar a "v3.2" o agregar nota "+ Sesión 3 Servicios".

- [ ] **Step 4: Commit**

```bash
git add METHODOLOGY.md
git commit -m "docs(services): sección 15 Servicios en METHODOLOGY.md"
```

---

### Tarea 15: Obsidian — placeholder Sesión 4 + actualizar Estado del Proyecto

**Files:**
- Create: `C:/Users/osyanne/Documents/Brain/01-Proyectos/CS2-Mineapolis/📦 Sesión 4 — Módulo Infraestructura.md` (placeholder)
- Modify: `C:/Users/osyanne/Documents/Brain/01-Proyectos/CS2-Mineapolis/📋 Estado del Proyecto.md`
- Create: `C:/Users/osyanne/Documents/Brain/01-Proyectos/CS2-Mineapolis/📦 Sesión 3 — Módulo Servicios.md` (resumen de la sesión)

- [ ] **Step 1: Crear placeholder Sesión 4 en Obsidian**

Usar `mcp__obsidian__create-note` con:
- vault: `brain`
- folder: `01-Proyectos/CS2-Mineapolis`
- filename: `📦 Sesión 4 — Módulo Infraestructura.md`
- contenido:

```markdown
# 📦 Sesión 4 — Módulo Infraestructura

tags: #cs2-mineapolis #infraestructura #sesion4 #pendiente

← [[🏙 CS2-Mineapolis (MOC)]]

**Estado:** 📋 Pendiente — scope diferido desde Sesión 3.

## Scope

3 capas de infraestructura que requieren fuentes no-OSM:

| Capa CS2 | Tags OSM (insuficiente) | Fuente recomendada |
|---|---|---|
| **Electricidad** | `power=plant\|substation\|generator` (~30-50% cobertura) | **EIA** (US Energy Info Admin) — datos federales públicos |
| **Agua y saneamiento** | `man_made=water_works\|water_tower\|wastewater_plant` (parcial) | **MN GIS Commons** (estado de Minnesota) |
| **Gestión de residuos** | `amenity=recycling\|waste_disposal` (<20 features en OSM) | **opendata.minneapolismn.gov** (municipal) |

## Trabajo adicional vs Sesión 3

- Nuevo `src/services/sources/` con cliente por fuente (no solo overpass_client)
- Reproyección con `pyproj` (nueva dependencia) — MN State Plane → WGS84
- Reconciliación de duplicados OSM↔EIA cuando hay overlap
- Probablemente +1 sesión completa de trabajo

## Por qué se difirió

Sesión 3 cubrió las 5 capas CS2 con buena cobertura OSM (health, education, fire, admin, parks). Forzar Electricidad/Agua/Residuos con OSM-only generaba <30 features útiles. Diferimos para hacerlos bien con las fuentes correctas.

## Ver también

- [[📦 Sesión 3 — Módulo Servicios]] — predecesor
- [[🏥 Módulo Servicios]] — nota legacy con scope original (9 capas, antes del realineamiento CS2)
- Design spec: `docs/plans/2026-05-16-modulo-servicios.md`
```

- [ ] **Step 2: Crear nota de Sesión 3 en Obsidian (resumen)**

Usar `mcp__obsidian__create-note` con:
- vault: `brain`
- folder: `01-Proyectos/CS2-Mineapolis`
- filename: `📦 Sesión 3 — Módulo Servicios.md`
- contenido:

```markdown
# 📦 Sesión 3 — Módulo Servicios

tags: #cs2-mineapolis #servicios #sesion3 #completada

← [[🏙 CS2-Mineapolis (MOC)]]

**Estado:** ✅ Completada — 2026-05-16

## Resumen

Implementación del Módulo Servicios alineado a las solapas de servicios base de Cities: Skylines 2.

## Las 5 capas

| Bucket | Capa CS2 | Marker | Color |
|---|---|---|---|
| `health` | Atención sanitaria y funeraria | H | #D81B60 |
| `education` | Educación e investigación | E | #FDD835 |
| `fire` | Bomberos | B | #E64A19 |
| `admin` | Policía y administración | A | #1E88E5 |
| `parks` | Parques | P | #43A047 |

## Decisiones clave

- **Geometría mixta:** polígono-preferido + punto-fallback (cada entidad aparece UNA vez)
- **Tier-hiding:** polígonos siempre, markers solo en zoom ≥ 12
- **Bibliotecas/museos/teatros** entran en `admin` (no tienen solapa propia en CS2)
- **Lugares de culto descartados** (no en estructura CS2 base)
- **Electricidad/Agua/Residuos diferidos** a [[📦 Sesión 4 — Módulo Infraestructura]] (requieren EIA + MN GIS)

## Archivos producidos

**Python:**
- `src/services/__init__.py`
- `src/services/zones.py` (labels, colors, bbox, query builder)
- `src/services/classifiers.py` (TAG_TO_CATEGORY, classify_service, infer_geometry_kind)
- `src/services/extract.py` (pipeline CLI)

**Tests:** `tests/services/test_zones.py`, `test_classifiers.py`, `test_extract.py`

**Frontend:** `visualizer/index.html` ampliado con SERVICES_TYPES, render functions, Layer Control, leyenda.

**Prebuilt:** `visualizer/datos_servicios.js` (gitignored, distribuido via GitHub Release v3.1).

## Docs

- Design spec: `docs/plans/2026-05-16-modulo-servicios.md`
- Implementation plan: `docs/plans/2026-05-16-modulo-servicios-implementation.md`
- METHODOLOGY.md sección 15

## Próximo

[[📦 Sesión 4 — Módulo Infraestructura]] — Electricidad + Agua + Residuos con fuentes autoritativas.
```

- [ ] **Step 3: Actualizar `📋 Estado del Proyecto.md`**

Usar `mcp__obsidian__edit-note` para añadir filas a la tabla de sesiones:
- ✅ Sesión 3 — Módulo Servicios — Completada 2026-05-16
- 📋 Sesión 4 — Módulo Infraestructura — Pendiente

(Si la nota es larga, leer primero con `mcp__obsidian__read-note` para localizar la sección exacta a editar.)

- [ ] **Step 4: Actualizar el MOC `🏙 CS2-Mineapolis (MOC).md`**

Cambiar la línea `[[🏥 Módulo Servicios]] — ⏳ Sesión 3 pendiente` a `[[📦 Sesión 3 — Módulo Servicios]] — ✅ Sesión 3 completada`.

Añadir línea: `[[📦 Sesión 4 — Módulo Infraestructura]] — ⏳ Pendiente`.

- [ ] **Step 5: Actualizar memoria persistente `proyecto_cs2_mineapolis.md`**

Editar `C:/Users/osyanne/.claude/projects/C--Users-osyanne/memory/proyecto_cs2_mineapolis.md` para reflejar:
- Sesión 3 completada (en lugar de "pendiente")
- Sesión 4 ahora es Módulo Infraestructura (no Servicios)
- Quitar el bloque "Cuando arranque Sesión 3" (ya no aplica)
- Añadir bloque "Cuando arranque Sesión 4" con scope Infraestructura

- [ ] **Step 6: No requiere commit git**

Las notas de Obsidian y memory viven fuera del repo. Se sincronizan automáticamente por el hook Stop al cierre de sesión.

---

## Self-Review

### Spec coverage check
- ✅ 5 capas (health/education/fire/admin/parks) — Tareas 3, 4
- ✅ Polígono-preferido + punto-fallback — Tarea 4 (infer_geometry_kind) + Tarea 5 (make_feature)
- ✅ Filtros (cemetery solo ways, culturales con name) — Tarea 4 (classify_service)
- ✅ Marker style círculo + char — Tarea 9 (makeServiceIcon)
- ✅ Tier-hiding zoom ≥ 12 — Tarea 9 (applyServicesZoomVisibility)
- ✅ Popup XSS-safe con escHtml — Tarea 9 (buildServicePopup)
- ✅ Layer Control + leyenda — Tarea 10
- ✅ Reusa `shared.overpass_client.query_with_retry` — Tarea 5
- ✅ Entry point `extract-services` — Tarea 6
- ✅ `.gitignore` datos_servicios.js — Tarea 7
- ✅ GitHub Release upload — Tarea 12
- ✅ READMEs y METHODOLOGY — Tareas 13, 14
- ✅ Sesión 4 placeholder en Obsidian — Tarea 15

### Type consistency check
- `classify_service(tags: dict, element_type: str) -> str | None` — usado consistentemente en Tareas 4 y 5
- `infer_geometry_kind(element: dict) -> str` — devuelve `"polygon"` o `"point"`, usado en Tarea 5
- `make_feature(element, cat, kind) -> dict` — devuelve dict con `coords` si polygon o `coord` si point
- `SERVICES_TYPES[key]` tiene `{label, color, char}` — consistente entre Python (zones.py) y JS (index.html)
- `serviceGroups[key]` es `L.layerGroup`, `servicePointLayers[key]` es array de `L.marker` — separación intencional para tier-hiding

### No-placeholder scan
Ningún paso usa "TBD", "implementar después", "handle edge cases" sin código. Todo el código está completo.

### Scope check
15 tareas, cada una bite-sized (2-5 minutos por step). Una sola feature coherente (Módulo Servicios). No mezcla con scope de Sesión 4 (solo crea placeholder).

---

## Notas para el ejecutor

- **TDD estricto:** cada tarea con código sigue red → green → commit. No saltar el "correr test para verificar que FALLA antes de implementar".
- **Verificación visual manual** en Tareas 9, 10, 11 — no automatizable.
- **Tarea 11 corre Overpass real** — puede tardar 15-90s. No es bug. Si falla, `query_with_retry` reintenta 3 endpoints × 4 rounds.
- **Tarea 15 modifica memoria persistente** — el hook Stop la sincroniza a Obsidian al cierre. No requiere commit.
- **Commits frecuentes:** cada tarea termina con commit. NO acumular cambios entre tareas.
