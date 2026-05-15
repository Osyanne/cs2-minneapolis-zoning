# Toolkit Reorganization — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganizar `cs2-minneapolis-zoning` en un toolkit modular renombrado a `cs2-minneapolis-osm-toolkit`, con sub-paquetes Python por módulo, prebuilts JS distribuidos via GitHub Releases, y UI del visualizer con module pills + master toggles + control de fondo para alternar rápidamente entre vistas.

**Architecture:** Refactor en 5 fases secuenciales. Fase A muta la estructura del código Python (sub-paquetes + renames + imports). Fase B saca los prebuilts JS del git tracking. Fase C añade UI nueva al visualizer. Fase D reescribe documentación. Fase E ejecuta el rename de GitHub + carpeta local + cierre. Cada fase produce working software (los tests pasan al final de cada fase).

**Tech Stack:** Python 3.11 + uv | pytest | hatchling | Leaflet.js | localStorage API | git + gh CLI

**Spec:** [`docs/specs/2026-05-15-toolkit-reorg-design.md`](../specs/2026-05-15-toolkit-reorg-design.md)
**Predecesor:** [Sesión 2 — Módulo Vial](./2026-05-15-modulo-vial.md)

---

## Pre-flight

Crear branch dedicada para todo el refactor:

- [ ] **Step 0: Crear branch + verificar estado limpio**

```bash
cd "/c/Users/osyanne/Documents/Claude/Projects/Proyecto mineapolis/cs2-minneapolis-zoning"
git status --short                    # Expected: vacío (working tree clean)
git checkout -b refactor/toolkit-reorg
git branch --show-current             # Expected: refactor/toolkit-reorg
```

---

## Fase A — Refactor estructura Python

### Task A.1: Crear sub-packages con `__init__.py`

**Files:**
- Create: `src/shared/__init__.py`
- Create: `src/zoning/__init__.py`
- Create: `src/vial/__init__.py`

- [ ] **Step 1: Crear directorios**

```bash
cd src
mkdir -p shared zoning vial
```

- [ ] **Step 2: Crear `__init__.py` vacío en cada uno**

```bash
cd src
touch shared/__init__.py zoning/__init__.py vial/__init__.py
```

- [ ] **Step 3: Verificar**

```bash
ls -la src/shared/ src/zoning/ src/vial/
# Expected: cada uno tiene un __init__.py de 0 bytes
```

- [ ] **Step 4: Commit**

```bash
git add src/shared/__init__.py src/zoning/__init__.py src/vial/__init__.py
git commit -m "feat(toolkit): crear sub-packages shared/zoning/vial"
```

---

### Task A.2: Mover `overpass_client.py` a `src/shared/`

**Files:**
- Move: `src/overpass_client.py` → `src/shared/overpass_client.py`

- [ ] **Step 1: `git mv` para preservar history**

```bash
cd src
git mv overpass_client.py shared/overpass_client.py
```

- [ ] **Step 2: Verificar**

```bash
ls src/shared/
# Expected: __init__.py  overpass_client.py
```

- [ ] **Step 3: Commit (NO actualizar imports todavía — se hace en Task A.5)**

```bash
git commit -m "refactor(toolkit): mover overpass_client.py a src/shared/"
```

---

### Task A.3: Mover archivos de zoning y renombrar `cs2_zones.py` → `zones.py`, `extract_zoning.py` → `extract.py`

**Files:**
- Move: `src/classifiers.py` → `src/zoning/classifiers.py`
- Move: `src/cs2_zones.py` → `src/zoning/zones.py` (renamed)
- Move: `src/extract_zoning.py` → `src/zoning/extract.py` (renamed)
- Move: `src/patch_colors.py` → `src/zoning/patch_colors.py`
- Move: `src/extract_msbuildings.py` → `src/zoning/extract_msbuildings.py`

- [ ] **Step 1: `git mv` cada archivo**

```bash
cd src
git mv classifiers.py zoning/classifiers.py
git mv cs2_zones.py zoning/zones.py
git mv extract_zoning.py zoning/extract.py
git mv patch_colors.py zoning/patch_colors.py
git mv extract_msbuildings.py zoning/extract_msbuildings.py
```

- [ ] **Step 2: Verificar contenido de zoning/**

```bash
ls src/zoning/
# Expected:
# __init__.py  classifiers.py  extract.py  extract_msbuildings.py
# patch_colors.py  zones.py
```

- [ ] **Step 3: Commit**

```bash
git commit -m "refactor(toolkit): mover archivos de zoning a src/zoning/ (cs2_zones→zones, extract_zoning→extract)"
```

---

### Task A.4: Mover archivos de vial y renombrar `vial_zones.py` → `zones.py`, `vial_classifiers.py` → `classifiers.py`, `extract_vial.py` → `extract.py`

**Files:**
- Move: `src/vial_zones.py` → `src/vial/zones.py` (renamed)
- Move: `src/vial_classifiers.py` → `src/vial/classifiers.py` (renamed)
- Move: `src/extract_vial.py` → `src/vial/extract.py` (renamed)

- [ ] **Step 1: `git mv` cada archivo**

```bash
cd src
git mv vial_zones.py vial/zones.py
git mv vial_classifiers.py vial/classifiers.py
git mv extract_vial.py vial/extract.py
```

- [ ] **Step 2: Verificar**

```bash
ls src/vial/
# Expected:
# __init__.py  classifiers.py  extract.py  zones.py
```

- [ ] **Step 3: Commit**

```bash
git commit -m "refactor(toolkit): mover archivos de vial a src/vial/ (vial_*→sin prefijo)"
```

---

### Task A.5: Actualizar imports en todos los archivos Python

**Files:**
- Modify: `src/zoning/extract.py`
- Modify: `src/zoning/extract_msbuildings.py`
- Modify: `src/zoning/patch_colors.py`
- Modify: `src/zoning/classifiers.py` (probablemente no necesita cambios — pure functions)
- Modify: `src/zoning/zones.py` (probablemente no necesita cambios — pure data)
- Modify: `src/vial/extract.py`
- Modify: `src/vial/classifiers.py` (probablemente no — pure functions)
- Modify: `src/vial/zones.py` (probablemente no — pure data)

- [ ] **Step 1: Update `src/zoning/extract.py`**

Buscar y reemplazar los siguientes imports en el archivo:

```python
# ANTES
from overpass_client import query_with_retry
from classifiers import (
    classify_apartment,
    classify_residential_subtype,
    classify_landuse_residential,
    classify_commercial,
    classify_office,
    classify_parking,
    polygon_area_m2,
)
from cs2_zones import CS2_LABELS, MINNEAPOLIS_BBOX, build_queries

# DESPUÉS
from shared.overpass_client import query_with_retry
from zoning.classifiers import (
    classify_apartment,
    classify_residential_subtype,
    classify_landuse_residential,
    classify_commercial,
    classify_office,
    classify_parking,
    polygon_area_m2,
)
from zoning.zones import CS2_LABELS, MINNEAPOLIS_BBOX, build_queries
```

- [ ] **Step 2: Update `src/zoning/extract_msbuildings.py`**

Inspeccionar el archivo y reemplazar cualquier import de `overpass_client`, `cs2_zones`, o `classifiers`:

```python
# Buscar líneas tipo:
from overpass_client import ...
from cs2_zones import ...
from classifiers import ...

# Cambiar a:
from shared.overpass_client import ...
from zoning.zones import ...
from zoning.classifiers import ...
```

- [ ] **Step 3: Update `src/zoning/patch_colors.py`**

Mismo patrón:

```python
# ANTES
from cs2_zones import ...
# DESPUÉS
from zoning.zones import ...
```

(Si el archivo no tiene imports de los módulos refactorizados, no hace falta cambiar nada.)

- [ ] **Step 4: Update `src/vial/extract.py`**

```python
# ANTES
from overpass_client import query_with_retry
from vial_classifiers import classify_highway
from vial_zones import VIAL_LABELS, MINNEAPOLIS_BBOX, build_vial_query

# DESPUÉS
from shared.overpass_client import query_with_retry
from vial.classifiers import classify_highway
from vial.zones import VIAL_LABELS, MINNEAPOLIS_BBOX, build_vial_query
```

- [ ] **Step 5: Verificar que no quedaron imports viejos**

```bash
cd src
grep -rn "^from overpass_client\|^from cs2_zones\|^from classifiers\|^from vial_classifiers\|^from vial_zones" zoning/ vial/
# Expected: vacío (sin matches)
```

- [ ] **Step 6: Commit**

```bash
git add src/zoning/ src/vial/
git commit -m "refactor(toolkit): actualizar imports al nuevo layout de sub-packages"
```

---

### Task A.6: Actualizar `pyproject.toml` a sub-package layout

**Files:**
- Modify: `src/pyproject.toml`

- [ ] **Step 1: Reemplazar contenido completo de `src/pyproject.toml`**

```toml
[project]
name = "cs2-minneapolis-osm-toolkit"
version = "3.1.0"
description = "GIS toolkit modular: extract OpenStreetMap data for Cities: Skylines 2"
requires-python = ">=3.11"
dependencies = [
    "requests>=2.31.0",
    "tqdm>=4.66.0",
    "shapely>=2.0.0",
]

[dependency-groups]
dev = [
    "pytest>=7.0.0",
]

# Entry points por módulo
[project.scripts]
extract-zoning = "zoning.extract:main"
extract-vial   = "vial.extract:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

# Layout de sub-packages — hatchling empaqueta los directorios completos
[tool.hatch.build.targets.wheel]
packages = ["shared", "zoning", "vial"]
```

- [ ] **Step 2: Verificar sintaxis del TOML**

```bash
cd src
uv pip compile pyproject.toml --quiet 2>&1 | head -5
# Expected: sin errores de parsing del TOML
```

(Si `uv pip compile` da errores de otra naturaleza pero NO sobre el toml syntax, está OK.)

- [ ] **Step 3: Commit**

```bash
git add src/pyproject.toml
git commit -m "refactor(toolkit): pyproject.toml a sub-package layout (packages=[shared,zoning,vial])"
```

---

### Task A.7: Reorganizar `tests/` en sub-carpetas

**Files:**
- Move: `tests/test_classifiers.py` → `tests/zoning/test_classifiers.py`
- Move: `tests/test_queries.py` → `tests/zoning/test_queries.py`
- Move: `tests/test_vial.py` → `tests/vial/test_vial.py`
- Create: `tests/zoning/__init__.py`
- Create: `tests/vial/__init__.py`

- [ ] **Step 1: Crear sub-directorios**

```bash
mkdir -p tests/zoning tests/vial
```

- [ ] **Step 2: Crear `__init__.py` en cada uno**

```bash
touch tests/zoning/__init__.py tests/vial/__init__.py
```

- [ ] **Step 3: Mover los tests existentes con `git mv`**

```bash
git mv tests/test_classifiers.py tests/zoning/test_classifiers.py
git mv tests/test_queries.py tests/zoning/test_queries.py
git mv tests/test_vial.py tests/vial/test_vial.py
```

- [ ] **Step 4: Verificar**

```bash
ls tests/zoning/ tests/vial/
# Expected:
# tests/zoning/:  __init__.py  test_classifiers.py  test_queries.py
# tests/vial/:    __init__.py  test_vial.py
```

- [ ] **Step 5: Commit**

```bash
git add tests/zoning/__init__.py tests/vial/__init__.py
git commit -m "refactor(toolkit): reorganizar tests en sub-carpetas zoning/ y vial/"
```

---

### Task A.8: Actualizar imports en los tests

**Files:**
- Modify: `tests/zoning/test_classifiers.py`
- Modify: `tests/zoning/test_queries.py`
- Modify: `tests/vial/test_vial.py`

Los tests actuales usan un hack `sys.path.insert(0, ...)` para importar desde `src/`. Con sub-packages no hace falta el hack — `pytest` con `rootdir=...` (configurado en pyproject) hace los imports correctos via `pythonpath`.

- [ ] **Step 1: Update `tests/zoning/test_classifiers.py`**

Abrir el archivo y localizar el bloque inicial:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from classifiers import (
    classify_apartment,
    # ...
)
```

Reemplazar por:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from zoning.classifiers import (
    classify_apartment,
    # ... (mismo set de funciones)
)
```

(El `..` extra en el sys.path es porque el test ahora está en `tests/zoning/`, dos niveles abajo del root, no uno.)

- [ ] **Step 2: Update `tests/zoning/test_queries.py`**

Mismo patrón:

```python
# ANTES (top del archivo)
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from cs2_zones import build_queries, CS2_LABELS

# DESPUÉS
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from zoning.zones import build_queries, CS2_LABELS
```

- [ ] **Step 3: Update `tests/vial/test_vial.py`**

```python
# ANTES (top del archivo)
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Y dentro de cada test:
from vial_zones import VIAL_LABELS
from vial_classifiers import classify_highway
from extract_vial import linestring_from_way

# DESPUÉS (top)
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# Dentro de cada test:
from vial.zones import VIAL_LABELS
from vial.classifiers import classify_highway
from vial.extract import linestring_from_way
```

- [ ] **Step 4: Correr los tests**

```bash
cd src
uv run pytest ../tests/ -v 2>&1 | tail -15
```

Expected: 72 tests collected, **71 passed, 1 failed**. El fail es el pre-existing `test_mixed_apartments_uses_spatial_join` heredado de Sesión 1.6 (assert `around.comm:3` vs código `around.comm:5`). El refactor no debe romper ningún test pasante.

- [ ] **Step 5: Commit**

```bash
git add tests/zoning/ tests/vial/
git commit -m "refactor(toolkit): actualizar imports de tests al sub-package layout"
```

---

### Task A.9: Fix oportunista del test pre-existing roto

El reviewer de Sesión 2 lo flaggeó como tech debt. Como ya estamos tocando los tests, lo arreglamos aquí.

**Files:**
- Modify: `tests/zoning/test_queries.py`

- [ ] **Step 1: Verificar el código actual de `cs2_zones.py` (ahora `zones.py`)**

```bash
grep "around.comm" src/zoning/zones.py
# Expected: dos matches con "around.comm:5"
```

Esto confirma que el código usa `around.comm:5`, no `:3`.

- [ ] **Step 2: Update el assert en el test**

Abrir `tests/zoning/test_queries.py`. Localizar:

```python
def test_mixed_apartments_uses_spatial_join():
    """La query mixed_apartments debe usar around.comm para spatial join."""
    q = build_queries(BBOX)["mixed_apartments"]
    assert "around.comm:3" in q, "mixed_apartments debe hacer spatial join around.comm:3"
```

Reemplazar `around.comm:3` por `around.comm:5` en ambas líneas (assert + mensaje):

```python
def test_mixed_apartments_uses_spatial_join():
    """La query mixed_apartments debe usar around.comm para spatial join."""
    q = build_queries(BBOX)["mixed_apartments"]
    assert "around.comm:5" in q, "mixed_apartments debe hacer spatial join around.comm:5"
```

- [ ] **Step 3: Correr todos los tests**

```bash
cd src
uv run pytest ../tests/ -v 2>&1 | tail -5
```

Expected: **72 passed**, 0 failed.

- [ ] **Step 4: Commit**

```bash
git add tests/zoning/test_queries.py
git commit -m "fix(tests): alinear test_mixed_apartments al radio around.comm:5 actual"
```

---

## Fase B — Prebuilts fuera del repo

### Task B.1: Sacar prebuilts del git tracking

**Files:**
- Modify: `.gitignore`
- Remove from git tracking: `visualizer/datos_zonificacion.js`, `visualizer/datos_vial.js`

- [ ] **Step 1: Actualizar `.gitignore`**

Abrir `.gitignore`. Localizar el bloque actual:

```
# Generated data — el visualizer/datos_zonificacion.js SÍ se trackea (instant load)
datos_zonificacion.js
!data/sample_output.js
!visualizer/datos_zonificacion.js

# Sesión 1.8 — Microsoft Buildings augmentation (no se trackea, requiere descargar 96MB)
visualizer/datos_msbuildings.js
```

Reemplazar por:

```
# Generated data — los prebuilts JS se distribuyen via GitHub Releases, no en git
# (post-refactor 2026-05-15: ver docs/specs/2026-05-15-toolkit-reorg-design.md)
datos_zonificacion.js
datos_vial.js
visualizer/datos_zonificacion.js
visualizer/datos_vial.js
visualizer/datos_msbuildings.js
!data/sample_output.js
```

- [ ] **Step 2: Sacar los prebuilts del git tracking (preservar en disco)**

```bash
git rm --cached visualizer/datos_zonificacion.js
git rm --cached visualizer/datos_vial.js
```

`--cached` deja los archivos en disco — solo los saca del index. El visualizer seguirá cargándolos localmente hasta que el usuario los borre.

- [ ] **Step 3: Verificar**

```bash
git status --short
# Expected:
# D  visualizer/datos_vial.js          (deleted from index, still on disk)
# D  visualizer/datos_zonificacion.js
# M  .gitignore
```

- [ ] **Step 4: Verificar que los archivos siguen en disco**

```bash
ls -lh visualizer/datos_*.js
# Expected: ambos existen, ~25-27 MB cada uno
```

- [ ] **Step 5: Commit**

```bash
git add .gitignore visualizer/datos_zonificacion.js visualizer/datos_vial.js
git commit -m "refactor(toolkit): sacar prebuilts JS del git tracking — distribución via Releases"
```

---

### Task B.2: Crear `visualizer/README.md` con instrucciones

**Files:**
- Create: `visualizer/README.md`

- [ ] **Step 1: Crear el archivo**

```markdown
# CS2 Minneapolis OSM — Visualizer

Visualizador interactivo Leaflet del mapa de Minneapolis con overlays de zonificación y red vial.

## Quick start

```bash
# Servir el visualizer en localhost:8080
cd visualizer
python -m http.server 8080

# Abrir en navegador:
# http://localhost:8080/index.html
```

## Obtener prebuilts (datos pre-generados)

Los archivos `datos_zonificacion.js` (~27 MB) y `datos_vial.js` (~25 MB) NO están commiteados en el repo (son binarios grandes). Tienes dos opciones:

### Opción A: Descargar desde GitHub Releases (recomendado)

1. Ir a https://github.com/Osyanne/cs2-minneapolis-osm-toolkit/releases
2. Descargar `datos_zonificacion.js` y `datos_vial.js` desde la última release
3. Colocarlos en este directorio (`visualizer/`)

### Opción B: Regenerar localmente

```bash
cd src
uv run extract-zoning    # ~3-5 min — genera datos_zonificacion.js
uv run extract-vial      # ~30s    — genera datos_vial.js
```

Los archivos se escriben directamente a `../visualizer/`.

## Modo sin prebuilts

Si abres el visualizer sin los prebuilts, el código JavaScript detecta la ausencia automáticamente y:

- **Zonificación**: cae a modo live Overpass (descarga las 9 queries en paralelo, tarda ~2-3 min la primera vez, se cachea 24h en localStorage)
- **Red Vial**: simplemente no se renderea — el visualizer funciona pero solo con el módulo zoning

## Controles de UI

- **Module pills (arriba)**: toggle ON/OFF de cada módulo entero (Zoning / Vial / Servicios / Transporte)
- **Master toggle en leyenda**: espejo de las pills, mismo efecto
- **Control "Fondo"** (aparece si hay módulos en OFF): Ocultos / Atenuados / Completos
- **Layer Control** (esquina arriba derecha): toggle granular por zona / categoría vial individual
```

- [ ] **Step 2: Commit**

```bash
git add visualizer/README.md
git commit -m "docs(visualizer): añadir README con instrucciones para obtener prebuilts"
```

---

## Fase C — UI del visualizer (module pills + master toggles + control de fondo)

### Task C.1: Añadir CSS para las module pills

**Files:**
- Modify: `visualizer/index.html` (sección `<style>`)

- [ ] **Step 1: Añadir estilos al bloque CSS existente**

Localizar el bloque `<style>` en `visualizer/index.html` (alrededor de la línea 11). Justo antes del cierre `</style>`, añadir:

```css
/* ══ MODULE PILLS (Header arriba) ═════════════════════════════════════════════ */
#header-controls {
  position: fixed;
  top: 10px;
  right: 10px;
  display: flex;
  gap: 8px;
  align-items: center;
  z-index: 1000;
  background: rgba(10,13,26,0.93);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 9px;
  padding: 6px 10px;
  backdrop-filter: blur(8px);
}
.pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  border-radius: 16px;
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.3px;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.08);
  color: #ccc;
  cursor: pointer;
  user-select: none;
  transition: all 0.15s;
}
.pill:hover:not(.disabled) {
  background: rgba(255,255,255,0.10);
  border-color: rgba(255,255,255,0.15);
}
.pill.on {
  background: rgba(139, 195, 74, 0.18);
  border-color: rgba(139, 195, 74, 0.4);
  color: #C5E1A5;
}
.pill.disabled {
  opacity: 0.35;
  cursor: not-allowed;
}
.pill-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  border: 1.5px solid currentColor;
  background: transparent;
  transition: background 0.15s;
}
.pill.on .pill-dot {
  background: #8BC34A;
  border-color: #8BC34A;
  box-shadow: 0 0 6px rgba(139,195,74,0.5);
}

/* ══ FONDO CONTROL (dropdown a la derecha de las pills) ═════════════════════════ */
#fondo-control {
  display: none;            /* visible cuando hay ≥1 pill OFF */
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #aaa;
  padding-left: 10px;
  border-left: 1px solid rgba(255,255,255,0.08);
}
#fondo-control.visible { display: inline-flex; }
#fondo-select {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.10);
  color: #ddd;
  font-size: 11px;
  padding: 3px 6px;
  border-radius: 4px;
  cursor: pointer;
}

/* ══ MASTER TOGGLE EN LEYENDA (espejo de las pills) ══════════════════════════ */
.legend h4 {
  display: flex;
  align-items: center;
  gap: 8px;
}
.master-toggle {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 1.5px solid #555;
  background: transparent;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.15s;
}
.master-toggle.on {
  background: #8BC34A;
  border-color: #8BC34A;
  box-shadow: 0 0 6px rgba(139,195,74,0.4);
}
.master-toggle:hover {
  border-color: #888;
}

/* ══ MÓDULO ATENUADO (estado "Fondo: Atenuado") ═════════════════════════════ */
.module-faded path {
  opacity: 0.3 !important;
  fill-opacity: 0.15 !important;
}
```

- [ ] **Step 2: Verificar que el CSS no rompe nada visualmente**

Sin commit todavía — el CSS no afecta nada hasta que añadamos el HTML+JS. Solo verificar que no haya error de sintaxis CSS (las llaves `{}` están balanceadas).

- [ ] **Step 3: Commit**

```bash
git add visualizer/index.html
git commit -m "feat(visualizer): añadir CSS para module pills + master toggles + fondo control"
```

---

### Task C.2: Añadir HTML markup de las pills y control de fondo

**Files:**
- Modify: `visualizer/index.html` (sección `<body>`)

- [ ] **Step 1: Añadir el `<div>` del header justo después de la apertura de `<body>`**

Localizar el `<body>` en `visualizer/index.html`. Justo después de `<body>`, insertar:

```html
<!-- Header — module pills + control de fondo (Sesión post-2 refactor) -->
<div id="header-controls">
  <div class="pill on" data-module="zoning">
    <span class="pill-dot"></span>
    <span>Zoning</span>
  </div>
  <div class="pill on" data-module="vial">
    <span class="pill-dot"></span>
    <span>Vial</span>
  </div>
  <div class="pill disabled" data-module="servicios" title="Próximamente (Sesión 3)">
    <span class="pill-dot"></span>
    <span>Servicios</span>
  </div>
  <div class="pill disabled" data-module="transporte" title="Próximamente (Sesión 4)">
    <span class="pill-dot"></span>
    <span>Transporte</span>
  </div>
  <div id="fondo-control">
    <span>Fondo:</span>
    <select id="fondo-select">
      <option value="hidden">Oculto</option>
      <option value="faded">Atenuado</option>
      <option value="full">Completo</option>
    </select>
  </div>
</div>
```

- [ ] **Step 2: Verificar visualmente**

Servir el visualizer y abrir en navegador:

```bash
cd visualizer && python -m http.server 8080
# Abrir http://localhost:8080/index.html
```

Expected: aparecen las 4 pills arriba derecha (Zoning y Vial en verde "on", Servicios y Transporte en gris disabled). El control "Fondo" no se ve aún (correcto — está hidden por default).

- [ ] **Step 3: Commit**

```bash
git add visualizer/index.html
git commit -m "feat(visualizer): añadir HTML markup de pills y control de fondo"
```

---

### Task C.3: Implementar lógica JS de las module pills

**Files:**
- Modify: `visualizer/index.html` (sección `<script>`)

- [ ] **Step 1: Añadir el bloque de gestión de pills antes de `loadAll()`**

Localizar la línea con `// MAIN LOADER` en el script (alrededor de la línea 762). Justo ANTES de esa sección, insertar:

```javascript
// ══════════════════════════════════════════════════════════════════════════════
// MODULE PILLS + MASTER TOGGLES + FONDO CONTROL (post-Sesión 2 refactor)
// ══════════════════════════════════════════════════════════════════════════════

const MODULES = {
  zoning: {
    label: "Zoning",
    enabled: true,
    layerGroupsRef: () => Object.values(groups),
  },
  vial: {
    label: "Vial",
    enabled: true,
    layerGroupsRef: () => Object.values(vialGroups),
  },
  servicios: { label: "Servicios", enabled: false, layerGroupsRef: () => [] },
  transporte: { label: "Transporte", enabled: false, layerGroupsRef: () => [] },
};

// State persistido en localStorage
const VIEW_STATE_KEY = "cs2-mineapolis-view-state-v1";

function readViewState() {
  try {
    const raw = localStorage.getItem(VIEW_STATE_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch { return null; }
}

function writeViewState(state) {
  try {
    localStorage.setItem(VIEW_STATE_KEY, JSON.stringify(state));
  } catch (e) {
    console.warn("[view-state] no se pudo guardar:", e.message);
  }
}

// Estado inicial: cargar de localStorage, fallback a default (todo enabled = "on")
const savedState = readViewState();
const moduleStates = {};
for (const key of Object.keys(MODULES)) {
  if (savedState && savedState.pills && savedState.pills[key]) {
    moduleStates[key] = savedState.pills[key];
  } else {
    moduleStates[key] = MODULES[key].enabled ? "on" : "off";
  }
}
let fondoMode = (savedState && savedState.fondo) || "hidden";   // "hidden" | "faded" | "full"

// Helper recursivo: aplica setStyle a TODOS los polygons/polylines descendientes
// de un layerGroup, incluyendo sub-grupos anidados (zonas tier-based de Sesión 1.7
// tienen estructura groups[key] → [tieredLarge[key], tieredSmall[key]] → polígonos)
function eachPolygonDeep(layer, fn) {
  if (typeof layer.setStyle === "function" && typeof layer.eachLayer !== "function") {
    // Hoja: es un Path (polygon/polyline)
    fn(layer);
  } else if (typeof layer.eachLayer === "function") {
    // Rama: recursivo
    layer.eachLayer(sub => eachPolygonDeep(sub, fn));
  }
}

// Aplica el estado actual al DOM y al mapa
function applyModuleState(moduleKey) {
  const state = moduleStates[moduleKey];
  const module = MODULES[moduleKey];
  if (!module.enabled) return;   // módulos disabled no se tocan

  const layers = module.layerGroupsRef();

  if (state === "on" || fondoMode === "full") {
    // Visible completo
    for (const lg of layers) {
      if (!map.hasLayer(lg)) map.addLayer(lg);
      eachPolygonDeep(lg, p => p.setStyle({ opacity: 0.9, fillOpacity: 0.55 }));
    }
  } else if (state === "off" && fondoMode === "faded") {
    // Visible atenuado
    for (const lg of layers) {
      if (!map.hasLayer(lg)) map.addLayer(lg);
      eachPolygonDeep(lg, p => p.setStyle({ opacity: 0.3, fillOpacity: 0.15 }));
    }
  } else {
    // state === "off" && fondoMode === "hidden"
    for (const lg of layers) {
      if (map.hasLayer(lg)) map.removeLayer(lg);
    }
  }
}

function applyAllStates() {
  for (const key of Object.keys(MODULES)) {
    applyModuleState(key);
  }
}

// Sincroniza UI de pills + master toggles con moduleStates
function syncUI() {
  // Pills
  for (const pill of document.querySelectorAll(".pill")) {
    const key = pill.dataset.module;
    if (!MODULES[key]) continue;
    pill.classList.toggle("on", moduleStates[key] === "on");
  }
  // Master toggles en leyenda
  for (const mt of document.querySelectorAll(".master-toggle")) {
    const key = mt.dataset.module;
    if (!MODULES[key]) continue;
    mt.classList.toggle("on", moduleStates[key] === "on");
  }
  // Fondo control: visible si ≥1 enabled module está "off"
  const anyOff = Object.keys(MODULES).some(
    k => MODULES[k].enabled && moduleStates[k] === "off"
  );
  document.getElementById("fondo-control").classList.toggle("visible", anyOff);
  document.getElementById("fondo-select").value = fondoMode;
}

// Toggle un módulo (llamado desde pills o master toggles)
function toggleModule(key) {
  if (!MODULES[key] || !MODULES[key].enabled) return;
  moduleStates[key] = moduleStates[key] === "on" ? "off" : "on";
  applyModuleState(key);
  syncUI();
  writeViewState({ pills: moduleStates, fondo: fondoMode });
}

// Cambiar el modo de fondo
function setFondo(mode) {
  fondoMode = mode;
  applyAllStates();
  syncUI();
  writeViewState({ pills: moduleStates, fondo: fondoMode });
}

// Event listeners
function wireUpModuleControls() {
  for (const pill of document.querySelectorAll(".pill")) {
    pill.addEventListener("click", () => {
      const key = pill.dataset.module;
      toggleModule(key);
    });
  }
  for (const mt of document.querySelectorAll(".master-toggle")) {
    mt.addEventListener("click", () => {
      const key = mt.dataset.module;
      toggleModule(key);
    });
  }
  document.getElementById("fondo-select").addEventListener("change", e => {
    setFondo(e.target.value);
  });
}
```

- [ ] **Step 2: Llamar `wireUpModuleControls()` + `applyAllStates()` + `syncUI()` al final del bootstrap**

Localizar la línea `loadAll();` al final del script (cerca de la línea 947). Reemplazar:

```javascript
loadAll();
```

Por:

```javascript
loadAll().then(() => {
  wireUpModuleControls();
  applyAllStates();
  syncUI();
});
```

- [ ] **Step 3: Verificar que `loadAll` devuelve una promise**

Localizar la definición de `loadAll`:

```javascript
async function loadAll() { ... }
```

`async` ya devuelve una Promise, así que `.then()` funciona. Si está como `function loadAll()` (sin async), hay que cambiarlo a `async function loadAll()`. Verificar con:

```bash
grep -n "function loadAll" visualizer/index.html
# Expected: "async function loadAll()"
```

- [ ] **Step 4: Smoke test browser**

```bash
cd visualizer && python -m http.server 8080
```

Abrir `http://localhost:8080/index.html`. Esperar a que termine la carga.

Verificar manualmente:
1. Las 4 pills aparecen, Zoning y Vial en verde "on"
2. Click en pill "Vial" → las líneas viales desaparecen, el control "Fondo: Oculto ▼" aparece a la derecha
3. Cambiar "Fondo" a "Atenuado" → vial reaparece al 30% opacity
4. Cambiar a "Completo" → vial reaparece full
5. Click en pill "Zoning" → zoning desaparece (o se atenúa según el fondo)
6. Recargar la página → el estado anterior se restaura (localStorage funcionando)

- [ ] **Step 5: Commit**

```bash
git add visualizer/index.html
git commit -m "feat(visualizer): module pills toggleables + control de fondo (Oculto/Atenuado/Completo) con persistencia"
```

---

### Task C.4: Añadir master toggles a la leyenda

**Files:**
- Modify: `visualizer/index.html` (función `legend.onAdd` y `updateLegendCounts`)

- [ ] **Step 1: Localizar `legend.onAdd` y añadir el `<div class="master-toggle">` a cada `<h4>`**

Localizar (cerca de la línea 870):

```javascript
let html = "<h4>CS2 Zonificación</h4>";
```

Reemplazar por:

```javascript
let html = `<h4><span class="master-toggle on" data-module="zoning" title="Toggle Zoning"></span>CS2 Zonificación</h4>`;
```

Y localizar (cerca de la línea 884):

```javascript
html += `<h4 style="margin-top:14px">Red Vial</h4>`;
```

Reemplazar por:

```javascript
html += `<h4 style="margin-top:14px"><span class="master-toggle on" data-module="vial" title="Toggle Vial"></span>Red Vial</h4>`;
```

- [ ] **Step 2: Smoke test browser**

Recargar el visualizer. Verificar:
1. Los `<h4>` de la leyenda ahora tienen un círculo verde ● a la izquierda de cada título
2. Click en el círculo de "CS2 Zonificación" → zoning se oculta + la pill arriba también cambia a "off"
3. Click en el círculo de "Red Vial" → vial se oculta + la pill arriba también
4. Estado se mantiene tras recarga (localStorage)

- [ ] **Step 3: Commit**

```bash
git add visualizer/index.html
git commit -m "feat(visualizer): master toggles bidireccionales en la leyenda"
```

---

### Task C.5: Smoke test browser comprehensive

**Files:**
- Run: `python -m http.server 8080`
- Verify: behavior visual + console errors

- [ ] **Step 1: Arrancar el server**

```bash
cd visualizer && python -m http.server 8080
```

- [ ] **Step 2: Verificar todos los flujos**

Abrir DevTools del navegador, ir a Console. Probar:

1. **Estado inicial (primer load)**:
   - Ambas pills "on" (verde)
   - Ambos master toggles en leyenda "on" (verde)
   - Control "Fondo" NO visible
   - Mapa muestra overlay completo (zoning + vial)
   - Console: `[vial] rendered 108,825 features` sin errores

2. **Toggle pill Vial**:
   - Pill cambia a "off" (gris)
   - Master toggle de "Red Vial" en leyenda también cambia a "off"
   - Líneas viales desaparecen del mapa
   - Control "Fondo: Oculto ▼" aparece
   - Layer Control sigue mostrando las 6 categorías viales (pero todas ocultas)

3. **Cambiar fondo a "Atenuado"**:
   - Líneas viales vuelven a aparecer al ~30% opacidad
   - Pill sigue en "off"

4. **Toggle master toggle "Red Vial" en leyenda**:
   - Vial vuelve a "on" completo
   - Pill arriba también cambia a "on"
   - Control "Fondo" desaparece

5. **Toggle pill Zoning**:
   - Polígonos zoning desaparecen
   - Pill "off", master toggle leyenda "off"
   - Control "Fondo: Oculto" aparece

6. **Apagar ambos** (Zoning y Vial):
   - Mapa queda con solo basemap CartoDB Dark
   - Ambos controles "off"

7. **Persistencia**:
   - Apagar Vial, cambiar fondo a "Atenuado"
   - Recargar página (F5 / Ctrl+R)
   - Estado se restaura: Vial "off", fondo "Atenuado"

8. **Console**: sin errores en ningún flujo

- [ ] **Step 3: Si todo OK, apagar server**

Ctrl+C en la terminal del server.

- [ ] **Step 4: No hay commit — solo verificación**

Si encontraste regresiones, vuelve a las Tasks C.3 o C.4 y arregla. Si todo pasa, sigue a la siguiente fase.

---

## Fase D — Documentación + Branding

### Task D.1: Reescribir `README.md` (English)

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Reemplazar todo el contenido de `README.md`**

```markdown
# CS2 Minneapolis OSM Toolkit — v3.1

> Real-world GIS data from OpenStreetMap → Cities: Skylines 2
> Modular toolkit · 100% open source · Zero API keys · Interactive dark map

![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue)
![License MIT](https://img.shields.io/badge/License-MIT-green)
![OSM Data](https://img.shields.io/badge/Data-OpenStreetMap-orange)
![Tests](https://img.shields.io/badge/tests-72%20passing-success)

> 🇪🇸 Versión en español: [README.es.md](README.es.md)

## What This Does

A modular toolkit that extracts real-world infrastructure data from OpenStreetMap via the Overpass API and renders it on an interactive dark-mode Leaflet map. Built as a reference layer for players recreating Minneapolis 1:1 in Cities: Skylines 2.

Currently includes **two modules**, each with its own extractor and visualization layer:

### 🗺 Zoning Module
Classifies all building polygons into the **11 official Cities: Skylines 2 zone types** (Low/Medium/High Density Residential, Row Housing, Mixed Housing, Low Rent Housing, Low/High Density Business, Low/High Density Offices, Industrial Manufacturing). 81,732 polygons in the Minneapolis bbox.

Run: `cd src && uv run extract-zoning`
Output: `visualizer/datos_zonificacion.js` (~27 MB)

### 🛣 Road Network Module
Classifies all OSM roads into the **6 CS2 road categories** (Highway, Major Road, Minor Road, Local Street, Pedestrian Path, Bike Lane). Renders as LineString overlay. 108,825 features.

Run: `cd src && uv run extract-vial`
Output: `visualizer/datos_vial.js` (~25 MB)

### Coming next
- 🏥 Services Module (health, education, parks, police, fire, energy, water) — Sesión 3
- 🚌 Transit Module (Blue/Green Line, BRT, bus routes, bikeways) — Sesión 4

## Visualizer features

- **Module pills (top)**: toggle entire modules on/off in one click
- **Master toggles in legend**: same effect, mirrored in the sidebar
- **Background mode** (when modules are off): Hidden / Faded / Full
- **Layer Control** (top right): granular per-zone / per-road-category toggles
- **Canvas renderer**: smooth pan/zoom with 80k+ polygons + 108k linestrings
- **Tier-based hiding**: individual houses hide at zoom <14, blocks stay visible
- **CS2-faithful color palette**: 4 families (green/blue/purple/yellow) aligned to the game HUD
- **Dark theme**: CartoDB Dark Matter basemap
- **Persistence**: view state saved to localStorage

## Quick start

### Prerequisites
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (faster pip+venv replacement)

### Setup

```bash
git clone https://github.com/Osyanne/cs2-minneapolis-osm-toolkit.git
cd cs2-minneapolis-osm-toolkit/src
uv sync
```

### Get prebuilts

The prebuilt `datos_*.js` files (~50 MB total) are **not** in this repo. Two ways to get them:

**Option A — Download from GitHub Releases** (recommended):
1. Go to https://github.com/Osyanne/cs2-minneapolis-osm-toolkit/releases
2. Download `datos_zonificacion.js` and `datos_vial.js` from the latest release
3. Place them in `visualizer/`

**Option B — Regenerate locally**:
```bash
cd src
uv run extract-zoning    # ~3-5 min
uv run extract-vial      # ~30s
```

### Serve the visualizer

```bash
cd visualizer
python -m http.server 8080
# Open http://localhost:8080/index.html
```

## Project structure

```
src/
├── shared/
│   └── overpass_client.py    # Overpass API client with retry + endpoint rotation
├── zoning/
│   ├── zones.py              # CS2 zone model + Overpass queries
│   ├── classifiers.py        # OSM tag → CS2 zone classifier
│   ├── extract.py            # CLI pipeline
│   ├── patch_colors.py       # Color palette utility
│   └── extract_msbuildings.py  # Experimental MS Buildings augmentation
└── vial/
    ├── zones.py              # CS2 road model + Overpass query
    ├── classifiers.py        # OSM highway tag → CS2 road category
    └── extract.py            # CLI pipeline

tests/
├── zoning/                   # 61 tests (50 classifiers + 11 query sanity)
└── vial/                     # 11 tests

visualizer/
├── index.html                # Single-file Leaflet visualizer
└── README.md                 # How to get prebuilts

docs/
├── plans/                    # Session implementation plans
├── specs/                    # Design specs
└── adapting-to-other-cities.md
```

## Project stats

| | |
|---|---|
| **Modules** | 2 (Zoning, Road Network) — 2 more pending (Services, Transit) |
| **Bounding box** | `44.86,-93.38,45.05,-93.17` (Minneapolis + immediate borders) |
| **Total features** | 190,557 (81,732 zoning polygons + 108,825 road LineStrings) |
| **Tests** | 72 passing (50 zoning classifiers + 11 zoning queries + 11 vial sanity) |
| **Last extracted** | 2026-05-15 |

## Adapting to other cities

The bbox is parametric — point the extractors at a different `--bbox` and you get the same map for any city. See [`docs/adapting-to-other-cities.md`](docs/adapting-to-other-cities.md) for guidance.

## License

MIT. OSM data via OpenStreetMap contributors under ODbL.
```

- [ ] **Step 2: Verificar**

```bash
head -15 README.md
# Expected: empieza con "# CS2 Minneapolis OSM Toolkit — v3.1"
```

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs(toolkit): reescribir README.md con narrativa modular toolkit v3.1"
```

---

### Task D.2: Reescribir `README.es.md` (Spanish)

**Files:**
- Modify: `README.es.md`

- [ ] **Step 1: Reemplazar todo el contenido de `README.es.md`**

```markdown
# CS2 Minneapolis OSM Toolkit — v3.1

> Datos GIS reales de OpenStreetMap → Cities: Skylines 2
> Toolkit modular · 100% open source · Sin API keys · Mapa interactivo dark

![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue)
![License MIT](https://img.shields.io/badge/License-MIT-green)
![OSM Data](https://img.shields.io/badge/Data-OpenStreetMap-orange)
![Tests](https://img.shields.io/badge/tests-72%20passing-success)

> 🇬🇧 English version: [README.md](README.md)

## Preview

![Mineapolis completa a zoom 12](docs/screenshots/preview_full.png)

## ¿Qué hace este toolkit?

Un toolkit modular que extrae datos reales de infraestructura desde OpenStreetMap (vía Overpass API) y los renderea en un mapa Leaflet dark-mode interactivo. Sirve como referencia visual para construir Mineapolis 1:1 en Cities: Skylines 2.

Actualmente incluye **dos módulos**, cada uno con su propio extractor y capa de visualización:

### 🗺 Módulo Zonificación
Clasifica todos los polígonos de edificios en los **11 tipos de zona oficiales de Cities: Skylines 2** (Low/Medium/High Density Residential, Row Housing, Mixed Housing, Low Rent Housing, Low/High Density Business, Low/High Density Offices, Industrial Manufacturing). 81,732 polígonos en el bbox de Mineapolis.

Ejecutar: `cd src && uv run extract-zoning`
Salida: `visualizer/datos_zonificacion.js` (~27 MB)

### 🛣 Módulo Red Vial
Clasifica todas las vías OSM en las **6 categorías de carretera de CS2** (Highway, Major Road, Minor Road, Local Street, Pedestrian Path, Bike Lane). Se renderea como capa de LineStrings encima del mapa de zonificación. 108.825 features.

Ejecutar: `cd src && uv run extract-vial`
Salida: `visualizer/datos_vial.js` (~25 MB)

### Próximos
- 🏥 Módulo Servicios (salud, educación, parques, policía, bomberos, energía, agua) — Sesión 3
- 🚌 Módulo Transporte (Blue/Green Line, BRT, rutas de bus, ciclovías) — Sesión 4

## Features del visualizer

- **Module pills (arriba)**: toggle módulos enteros en un click
- **Master toggles en leyenda**: mismo efecto, espejado en la barra lateral
- **Modo de fondo** (cuando hay módulos apagados): Oculto / Atenuado / Completo
- **Layer Control** (arriba derecha): toggle granular por zona / categoría vial
- **Canvas renderer**: pan/zoom fluido con 80k+ polígonos + 108k linestrings
- **Tier-based hiding**: casas individuales se ocultan en zoom <14, bloques siempre visibles
- **Paleta fiel a CS2**: 4 familias (verde/azul/morado/amarillo) alineadas al HUD del juego
- **Tema oscuro**: basemap CartoDB Dark Matter
- **Persistencia**: estado de la vista guardado en localStorage

## Quick start

### Requisitos
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (reemplazo más rápido de pip+venv)

### Setup

```bash
git clone https://github.com/Osyanne/cs2-minneapolis-osm-toolkit.git
cd cs2-minneapolis-osm-toolkit/src
uv sync
```

### Obtener prebuilts

Los archivos prebuilt `datos_*.js` (~50 MB en total) **no están** en este repo. Dos opciones:

**Opción A — Descargar desde GitHub Releases** (recomendado):
1. Ir a https://github.com/Osyanne/cs2-minneapolis-osm-toolkit/releases
2. Descargar `datos_zonificacion.js` y `datos_vial.js` desde la última release
3. Colocarlos en `visualizer/`

**Opción B — Regenerar localmente**:
```bash
cd src
uv run extract-zoning    # ~3-5 min
uv run extract-vial      # ~30s
```

### Levantar el visualizer

```bash
cd visualizer
python -m http.server 8080
# Abrir http://localhost:8080/index.html
```

## Estructura del proyecto

```
src/
├── shared/
│   └── overpass_client.py    # Cliente Overpass con retry + rotación de endpoints
├── zoning/
│   ├── zones.py              # Modelo de zonas CS2 + queries Overpass
│   ├── classifiers.py        # Clasificador OSM tag → zona CS2
│   ├── extract.py            # Pipeline CLI
│   ├── patch_colors.py       # Utility de paleta
│   └── extract_msbuildings.py  # Augmentación experimental con MS Buildings
└── vial/
    ├── zones.py              # Modelo de vías CS2 + query Overpass
    ├── classifiers.py        # Clasificador OSM highway tag → categoría vial
    └── extract.py            # Pipeline CLI

tests/
├── zoning/                   # 61 tests (50 classifiers + 11 query sanity)
└── vial/                     # 11 tests

visualizer/
├── index.html                # Visualizer Leaflet single-file
└── README.md                 # Cómo obtener prebuilts

docs/
├── plans/                    # Planes de implementación por sesión
├── specs/                    # Specs de diseño
└── adapting-to-other-cities.md
```

## Stats del proyecto

| | |
|---|---|
| **Módulos** | 2 (Zonificación, Red Vial) — 2 pendientes (Servicios, Transporte) |
| **Bounding box** | `44.86,-93.38,45.05,-93.17` (Mineapolis + bordes inmediatos) |
| **Features totales** | 190.557 (81.732 polígonos de zonificación + 108.825 LineStrings viales) |
| **Tests** | 72 pasando (50 clasificador zonificación + 11 sanidad zoning + 11 sanidad vial) |
| **Última extracción** | 2026-05-15 |

## Adaptarlo a otras ciudades

El bbox es paramétrico — apunta los extractores a un `--bbox` distinto y obtienes el mismo mapa para cualquier ciudad. Ver [`docs/adapting-to-other-cities.md`](docs/adapting-to-other-cities.md).

## Licencia

MIT. Datos OSM via OpenStreetMap contributors bajo ODbL.
```

- [ ] **Step 2: Commit**

```bash
git add README.es.md
git commit -m "docs(toolkit): reescribir README.es.md con narrativa modular toolkit v3.1"
```

---

### Task D.3: Actualizar header de `METHODOLOGY.md`

**Files:**
- Modify: `METHODOLOGY.md`

- [ ] **Step 1: Localizar el header del archivo**

Abrir `METHODOLOGY.md`. Buscar la línea cerca del top que dice algo como:

```
Version 3.0 — This document covers the architecture as of Session 1.7
```

(O similar — el texto exacto puede variar.)

- [ ] **Step 2: Reemplazar la línea**

Cambiar la línea por:

```
Version 3.1 — This document covers the architecture as of Session 2 (Road Network Module) + the post-Sesión 2 toolkit reorganization.
```

- [ ] **Step 3: Si hay alguna otra referencia al nombre `cs2-minneapolis-zoning` o estructura vieja en METHODOLOGY.md, actualizar**

```bash
grep -n "cs2-minneapolis-zoning\|cs2_zones\|vial_classifiers\|vial_zones\|extract_zoning\|extract_vial" METHODOLOGY.md
```

Para cada match:
- Referencias a `cs2_zones` → `zoning.zones`
- Referencias a `vial_zones` → `vial.zones`
- Referencias a `vial_classifiers` → `vial.classifiers`
- Referencias a `extract_zoning` → `zoning.extract` (o `extract-zoning` para el CLI)
- Referencias a `extract_vial` → `vial.extract` (o `extract-vial` para el CLI)
- Referencias a `cs2-minneapolis-zoning` (nombre del repo) → `cs2-minneapolis-osm-toolkit`

- [ ] **Step 4: Commit**

```bash
git add METHODOLOGY.md
git commit -m "docs(toolkit): actualizar METHODOLOGY.md para reflejar v3.1 y nueva estructura"
```

---

### Task D.4: Actualizar los 6 Reddit drafts en el escritorio

**Files:**
- Modify: `C:\Users\osyanne\Desktop\reddit_01_CitiesSkylines2.md`
- Modify: `C:\Users\osyanne\Desktop\reddit_02_CitiesSkylines.md`
- Modify: `C:\Users\osyanne\Desktop\reddit_03_openstreetmap.md`
- Modify: `C:\Users\osyanne\Desktop\reddit_04_Python.md`
- Modify: `C:\Users\osyanne\Desktop\reddit_05_Minneapolis.md`
- Modify: `C:\Users\osyanne\Desktop\reddit_06_MapPorn.md`
- Modify: `C:\Users\osyanne\Desktop\reddit_00_INDEX.md`

- [ ] **Step 1: Para cada uno de los 7 archivos, hacer find-and-replace global**

Reemplazos a aplicar (con `Edit` tool o manualmente):

| Buscar | Reemplazar por |
|---|---|
| `cs2-minneapolis-zoning` | `cs2-minneapolis-osm-toolkit` |
| `Minneapolis Zoning Visualizer` | `Minneapolis OSM Toolkit` |
| `v3.0` | `v3.1` (donde se refiere a la versión del repo) |
| `github.com/Osyanne/cs2-minneapolis-zoning` | `github.com/Osyanne/cs2-minneapolis-osm-toolkit` |

- [ ] **Step 2: Para los drafts que mencionan SOLO zonificación (`reddit_01_CitiesSkylines2.md`, `reddit_02_CitiesSkylines.md`, etc.), añadir un párrafo o sección que mencione el nuevo módulo vial**

Por ejemplo, añadir cerca del top o en una sección "What's new in v3.1":

```markdown
**New in v3.1**: Now also includes a Road Network module overlay — 108,825 OSM roads classified into 6 CS2 categories (Highway / Major / Minor / Local / Pedestrian / Bike). Toggle modules on/off with the new pill UI.
```

- [ ] **Step 3: Verificar todos los archivos**

```bash
grep -l "cs2-minneapolis-zoning" "/c/Users/osyanne/Desktop"/reddit_*.md
# Expected: vacío (sin matches — todos fueron reemplazados)
```

- [ ] **Step 4: No hay commit — estos archivos están fuera del repo (escritorio)**

Los drafts viven en el escritorio del usuario, no en el repo. Solo update y listo.

---

## Fase E — GitHub rename + cierre

### Task E.1: Generar prebuilts limpios para la Release

**Files:**
- Generate: `visualizer/datos_zonificacion.js`
- Generate: `visualizer/datos_vial.js`

- [ ] **Step 1: Regenerar los prebuilts con la nueva estructura (verifica imports)**

```bash
cd src
uv run extract-zoning 2>&1 | tail -5
# Expected: termina con "Wrote ../visualizer/datos_zonificacion.js"
# y resumen de 13 categorías con counts
```

```bash
cd src
uv run extract-vial 2>&1 | tail -5
# Expected: termina con "[OK] Wrote ../visualizer/datos_vial.js"
# Total ~108k features
```

- [ ] **Step 2: Verificar tamaños**

```bash
ls -lh visualizer/datos_*.js
# Expected: ~27 MB zonificación, ~25 MB vial
```

Estos archivos NO se commitean (están en `.gitignore`). Se usan para Step 3.

---

### Task E.2: Rename del repo en GitHub

**Files:** N/A (operación en GitHub UI o via `gh`)

- [ ] **Step 1: Rename via `gh` CLI**

```bash
gh repo rename cs2-minneapolis-osm-toolkit --repo Osyanne/cs2-minneapolis-zoning --confirm
```

Si `gh` no está disponible o falla, hacer manualmente:
1. Ir a https://github.com/Osyanne/cs2-minneapolis-zoning/settings
2. Scroll hasta "Repository name"
3. Cambiar a `cs2-minneapolis-osm-toolkit`
4. Click "Rename"

GitHub mantiene redirects desde el nombre viejo, así que cualquier link existente sigue funcionando.

- [ ] **Step 2: Actualizar el remote local**

```bash
git remote set-url origin https://github.com/Osyanne/cs2-minneapolis-osm-toolkit.git
git remote -v
# Expected: origin con la URL nueva
```

- [ ] **Step 3: Verificar conectividad**

```bash
git fetch --dry-run
# Expected: sin errores (puede no decir nada, eso es OK)
```

---

### Task E.3: Push del refactor + crear GitHub Release v3.1

**Files:** Operaciones de git/GitHub

- [ ] **Step 1: Mergear `refactor/toolkit-reorg` a `main`**

```bash
git checkout main
git merge --no-ff refactor/toolkit-reorg -m "Merge: Toolkit reorganization v3.1 (sub-packages + module pills + Releases)"
```

- [ ] **Step 2: Push a GitHub**

```bash
git push origin main
```

Expected: push exitoso al repo renombrado.

- [ ] **Step 3: Crear el GitHub Release `v3.1` con los prebuilts como assets**

Via `gh` CLI:

```bash
gh release create v3.1 \
  visualizer/datos_zonificacion.js \
  visualizer/datos_vial.js \
  --title "v3.1 — Toolkit reorganization + Road Network Module" \
  --notes "$(cat <<'EOF'
## Highlights

- 🛣 **New Road Network module** (108,825 features in 6 CS2 categories: Highway / Major / Minor / Local / Pedestrian / Bike) added in Sesión 2
- 🎛️ **New UI**: Module pills + master toggles + background mode (Hidden / Faded / Full) for fast view switching
- 📦 **Modular structure**: Python sub-packages (\`shared/\`, \`zoning/\`, \`vial/\`)
- 🏷️ **Renamed**: \`cs2-minneapolis-zoning\` → \`cs2-minneapolis-osm-toolkit\` (redirects preserved)
- 🚀 **Prebuilts via Releases**: Lighter repo (50 MB → <2 MB), explicit versioning

## Downloads (prebuilts)

- \`datos_zonificacion.js\` — 81,732 polygons, ~27 MB
- \`datos_vial.js\` — 108,825 LineStrings, ~25 MB

Place both in \`visualizer/\` and open \`visualizer/index.html\`.

## Test stats

72 tests passing (50 zoning classifiers + 11 zoning queries + 11 vial sanity).

## What's next

- 🏥 Sesión 3 — Services Module (health, education, parks, police, fire, energy, water)
- 🚌 Sesión 4 — Transit Module (Blue/Green Line, BRT, bus, bikeways)
EOF
)"
```

Si `gh` no está disponible, hacer manualmente desde GitHub:
1. Ir a https://github.com/Osyanne/cs2-minneapolis-osm-toolkit/releases/new
2. Tag: `v3.1`
3. Title: "v3.1 — Toolkit reorganization + Road Network Module"
4. Adjuntar `visualizer/datos_zonificacion.js` y `visualizer/datos_vial.js` como assets
5. Pegar el contenido del `--notes` en la descripción

- [ ] **Step 4: Verificar la Release**

```bash
gh release view v3.1
# Expected: muestra los 2 assets adjuntados
```

O ir a https://github.com/Osyanne/cs2-minneapolis-osm-toolkit/releases/tag/v3.1

---

### Task E.4: Renombrar carpeta local + actualizar referencias

**Files:**
- Move: `C:\Users\osyanne\Documents\Claude\Projects\Proyecto mineapolis\cs2-minneapolis-zoning\` → `cs2-minneapolis-osm-toolkit\`
- Modify: Obsidian notes + memoria persistente

- [ ] **Step 1: Cerrar cualquier proceso usando la carpeta**

Confirmar que no hay terminales, IDEs, o procesos con la carpeta abierta. Si VS Code está corriendo, cerrarlo.

- [ ] **Step 2: Renombrar la carpeta**

```bash
cd "/c/Users/osyanne/Documents/Claude/Projects/Proyecto mineapolis"
mv cs2-minneapolis-zoning cs2-minneapolis-osm-toolkit
```

- [ ] **Step 3: Verificar que git sigue funcionando con la nueva carpeta**

```bash
cd "/c/Users/osyanne/Documents/Claude/Projects/Proyecto mineapolis/cs2-minneapolis-osm-toolkit"
git status
# Expected: working tree clean, on main
git remote -v
# Expected: origin con cs2-minneapolis-osm-toolkit URL
```

- [ ] **Step 4: Actualizar Obsidian (paths absolutos)**

Editar `C:\Users\osyanne\Documents\Brain\01-Proyectos\CS2-Mineapolis\🏙 CS2-Mineapolis (MOC).md`:

Buscar:
```
**Repo:** https://github.com/Osyanne/cs2-minneapolis-zoning (v3.0 push 2026-05-15)
**Carpeta local:** `C:\Users\osyanne\Documents\Claude\Projects\Proyecto mineapolis\cs2-minneapolis-zoning\`
```

Reemplazar por:
```
**Repo:** https://github.com/Osyanne/cs2-minneapolis-osm-toolkit (v3.1 push 2026-05-15)
**Carpeta local:** `C:\Users\osyanne\Documents\Claude\Projects\Proyecto mineapolis\cs2-minneapolis-osm-toolkit\`
```

- [ ] **Step 5: Actualizar memoria persistente**

Editar `C:\Users\osyanne\.claude\projects\C--Users-osyanne\memory\proyecto_cs2_mineapolis.md`:

Buscar:
```
**Repo:** https://github.com/Osyanne/cs2-minneapolis-zoning (público, v3.0 pusheado 2026-05-15)

**Workspace local:** `C:\Users\osyanne\Documents\Claude\Projects\Proyecto mineapolis\cs2-minneapolis-zoning\`
```

Reemplazar por:
```
**Repo:** https://github.com/Osyanne/cs2-minneapolis-osm-toolkit (público, v3.1 pusheado 2026-05-15, renombrado de cs2-minneapolis-zoning)

**Workspace local:** `C:\Users\osyanne\Documents\Claude\Projects\Proyecto mineapolis\cs2-minneapolis-osm-toolkit\`
```

- [ ] **Step 6: Cualquier otra mención al path/nombre viejo en Obsidian o memoria**

```bash
grep -r "cs2-minneapolis-zoning" "/c/Users/osyanne/Documents/Brain/01-Proyectos/CS2-Mineapolis/" 2>/dev/null
grep -r "cs2-minneapolis-zoning" "/c/Users/osyanne/.claude/projects/C--Users-osyanne/memory/" 2>/dev/null
```

Reemplazar cada match por `cs2-minneapolis-osm-toolkit`.

- [ ] **Step 7: No hay commit en el repo de código — estos cambios son en Obsidian/memoria personales**

Los archivos de Obsidian y memoria persistente NO viven en el repo del toolkit.

---

### Task E.5: Verificación final + cierre

- [ ] **Step 1: Correr tests una última vez**

```bash
cd "/c/Users/osyanne/Documents/Claude/Projects/Proyecto mineapolis/cs2-minneapolis-osm-toolkit/src"
uv run pytest ../tests/ -v 2>&1 | tail -5
# Expected: 72 passed in <1s
```

- [ ] **Step 2: Smoke test browser final**

```bash
cd "/c/Users/osyanne/Documents/Claude/Projects/Proyecto mineapolis/cs2-minneapolis-osm-toolkit/visualizer"
python -m http.server 8080
# Abrir http://localhost:8080/index.html
# Verificar: módulo pills + master toggles + fondo control funcionan
# Console: sin errores
```

Ctrl+C para apagar el server cuando termines.

- [ ] **Step 3: Verificar el remoto en GitHub**

```bash
gh repo view Osyanne/cs2-minneapolis-osm-toolkit
# Expected: muestra info del repo renombrado, branch main al día
```

- [ ] **Step 4: Borrar la branch `refactor/toolkit-reorg` localmente y en remoto**

```bash
git branch -d refactor/toolkit-reorg
git push origin --delete refactor/toolkit-reorg 2>/dev/null || echo "(remote branch ya no existe — OK)"
```

- [ ] **Step 5: Cierre — actualizar Obsidian con la nueva sesión**

Crear `C:\Users\osyanne\Documents\Brain\01-Proyectos\CS2-Mineapolis\📦 Sesión 2.5 — Toolkit Reorg.md` con:
- Objetivo cumplido
- Cambios estructurales
- Nueva UI del visualizer
- Próximo paso: Sesión 3 — Servicios

Actualizar `📋 Estado del Proyecto.md` añadiendo una sección "✅ Sesión 2.5 — Toolkit Reorganization (COMPLETADA 2026-05-15)".

- [ ] **Step 6: No hay commit en el repo — el refactor se termina aquí**

El último commit del repo es el merge en E.3 Step 1. Cualquier work futuro será en otra branch / sesión.

---

## Caveats / Decisiones

- **El refactor NO toca el código de Sesión 2 (vial)** — solo lo mueve y renombra. Funcionalidad sin cambios.
- **El XSS pre-existing en zoning popups** sigue ahí — se arregla en una sesión futura aparte (línea 599 y 755 de `index.html`).
- **El `_vialOverlayRendered` flag idempotency** sigue funcionando igual — no se toca.
- **Adapting-to-other-cities.md** podría querer actualización al nuevo nombre — fuera de scope estricto pero un sed -i lo arregla.
- **El `extract_msbuildings.py` queda en `zoning/`** aunque sea experimental — sigue el patrón existente.

---

## Comandos rápidos post-refactor

```bash
# Tests
cd src && uv run pytest ../tests/ -v

# Regenerar prebuilts
cd src && uv run extract-zoning
cd src && uv run extract-vial

# Servir visualizer
cd visualizer && python -m http.server 8080
```
