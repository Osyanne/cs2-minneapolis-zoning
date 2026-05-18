# Toolkit Reorganization — Design Spec

**Fecha:** 2026-05-15
**Workspace actual:** `cs2-minneapolis-zoning/` (será renombrado)
**Predecesor:** [Sesión 2 — Módulo Vial](../plans/2026-05-15-modulo-vial.md)

---

## Motivación

Tras Sesión 2, el repo mezcla código de dos módulos (`zoning` y `vial`) en `src/` sin separación clara, el nombre `cs2-minneapolis-zoning` ya no refleja el alcance del proyecto, y los prebuilts JS suman 52 MB en el repo (creciendo a 100+ MB tras Sesiones 3 y 4).

Adicionalmente, el visualizer no permite cambiar rápidamente entre vistas: para ver "solo zoning" o "solo vial" el usuario tiene que ir al Layer Control de Leaflet y togglar 13 ó 6 checkboxes individualmente.

## Goal

Reorganizar el proyecto en tres dimensiones:

1. **Estructura del repo** — sub-paquetes Python por módulo, tests paralelos, prebuilts fuera del repo.
2. **Branding** — renombrar repo a `cs2-osm-toolkit`.
3. **Visualizer UX** — añadir "module pills" multi-select + master toggles en leyenda + control de fondo (3 estados) para alternar rápidamente entre vistas.

Sin regresión de funcionalidad existente. Los 72 tests deben seguir pasando.

---

## Sección 1 — Estructura nueva del repo

```
cs2-osm-toolkit/
├── README.md                    # rewritten — "toolkit GIS modular para CS2"
├── README.es.md                 # idem en español
├── METHODOLOGY.md               # actualizado (cabecera + sección general)
├── LICENSE                      # sin cambios
├── .gitignore                   # añade `visualizer/datos_*.js` + `.cache/`
│
├── src/
│   ├── pyproject.toml           # actualizado a sub-package layout
│   ├── shared/
│   │   ├── __init__.py
│   │   └── overpass_client.py   # ← movido (compartido por todos los módulos)
│   ├── zoning/
│   │   ├── __init__.py
│   │   ├── zones.py             # ← renamed from `cs2_zones.py`
│   │   ├── classifiers.py
│   │   ├── extract.py           # ← renamed from `extract_zoning.py`
│   │   ├── patch_colors.py
│   │   └── extract_msbuildings.py
│   └── vial/
│       ├── __init__.py
│       ├── zones.py             # ← renamed from `vial_zones.py`
│       ├── classifiers.py       # ← renamed from `vial_classifiers.py`
│       └── extract.py           # ← renamed from `extract_vial.py`
│
├── tests/
│   ├── zoning/
│   │   ├── test_classifiers.py
│   │   └── test_queries.py
│   └── vial/
│       └── test_vial.py
│
├── visualizer/
│   ├── index.html               # actualizado con pills + master toggles + fondo
│   └── README.md                # nuevo: cómo obtener prebuilts (regenerar / Releases)
│
├── docs/
│   ├── plans/                   # history preserved via `git mv`
│   ├── specs/
│   │   └── 2026-05-15-toolkit-reorg-design.md   # este archivo
│   ├── screenshots/
│   └── adapting-to-other-cities.md (etc.)
│
└── scripts/
    └── publish_release.sh       # helper para generar prebuilts + crear GitHub Release
```

### Cambios de imports

```python
# ANTES
from overpass_client import query_with_retry
from cs2_zones import build_queries, CS2_LABELS
from classifiers import classify_apartment
from vial_classifiers import classify_highway
from vial_zones import build_vial_query, VIAL_LABELS

# DESPUÉS
from shared.overpass_client import query_with_retry
from zoning.zones import build_queries, CS2_LABELS
from zoning.classifiers import classify_apartment
from vial.classifiers import classify_highway
from vial.zones import build_vial_query, VIAL_LABELS
```

### Entry-points en `pyproject.toml`

```toml
[project.scripts]
extract-zoning = "zoning.extract:main"
extract-vial   = "vial.extract:main"

[tool.hatch.build.targets.wheel]
packages = ["shared", "zoning", "vial"]
```

(El layout antiguo de `only-include` con archivos sueltos se reemplaza por `packages` que incluye los directorios completos.)

### Prebuilts (`visualizer/datos_*.js`)

- Se sacan del repo con `git rm --cached`.
- Se añaden a `.gitignore`.
- Se suben como assets del GitHub Release `v3.1` (que se crea como parte de este refactor).
- El visualizer ya tiene la lógica `onerror="window.__noPrebuilt=true"` — si el archivo no existe, cae a modo Overpass live (zoning) o muestra mapa sin vías (vial). Sin regresión.

**Manual del usuario para obtener prebuilts** (documentado en `visualizer/README.md`):
- Opción A: descargar desde el Release v3.1 y colocar en `visualizer/`.
- Opción B: regenerar localmente:
  ```bash
  cd src && uv run extract-zoning
  cd src && uv run extract-vial
  ```

### Tests

- `pytest` corre con `cd src && uv run pytest ../tests/`
- Cada subcarpeta `tests/zoning/` y `tests/vial/` tiene su `__init__.py`
- Los `sys.path.insert(...)` en los tests actuales se reemplazan por imports limpios desde el package layout

---

## Sección 2 — UI del visualizer

### Layout final

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  🎯 CS2 Minneapolis OSM     [● Zoning] [● Vial] [○ Servicios] [○ Transp.]   │  ← module pills
│                                                                  [Fondo ▼]   │  ← solo si ≥1 oculto
├──────────────────────────────────────────────────────────────────────────────┤
│ ┌────────────────────────────┐                                               │
│ │ ●  CS2 Zonificación    ▼  │   ← master toggle (espejo de la pill)         │
│ │  RESIDENCIAL               │                                               │
│ │  · Low Density   63,697   │                                                │
│ │  · Medium Row     1,719   │           [mapa Leaflet]                       │
│ │  ...                      │                                                │
│ │                           │                                                │
│ │ ●  Red Vial           ▼  │                                                │
│ │  ESTRUCTURALES            │                                                │
│ │  · Highway        2,450   │                                                │
│ │  ...                      │                                                │
│ └────────────────────────────┘                              [⊞ Capas]        │  ← Layer Control existente
└──────────────────────────────────────────────────────────────────────────────┘
```

### Componentes

#### Module Pills (arriba derecha del header)

```javascript
const MODULES = {
  zoning: {
    label: "Zoning",
    state: "on",          // "on" | "off"
    enabled: true,        // false si el módulo no existe aún (Servicios, Transporte)
    layerGroups: () => Object.values(groups),    // referencia a los layer groups
  },
  vial: {
    label: "Vial",
    state: "on",
    enabled: true,
    layerGroups: () => Object.values(vialGroups),
  },
  servicios: { label: "Servicios", state: "off", enabled: false },
  transporte: { label: "Transporte", state: "off", enabled: false },
};
```

**Comportamiento:**
- Cada pill es un `<button>` toggleable
- ● = state "on" (módulo visible), ○ = state "off" (módulo oculto)
- Pills con `enabled: false` se renderizan con opacity 0.4 y son no-clickeable
- Click cambia el estado y actualiza:
  - La opacidad/visibilidad de los layer groups del módulo correspondiente
  - El master toggle correspondiente en la leyenda (espejo)
  - Mostrar/ocultar el control "Fondo" (aparece si ≥1 módulo está "off")

#### Master Toggle en leyenda

- Cada section header de la leyenda ("CS2 Zonificación", "Red Vial") tiene un círculo ● a la izquierda
- Click toggle el módulo entero
- Espejo bidireccional con la pill correspondiente (cualquier cambio se sincroniza)
- Visualmente:
  - Estado "on": círculo verde lleno (#8BC34A)
  - Estado "off": círculo gris outlined (#555)

#### Control de Fondo

Pequeño dropdown que aparece a la derecha de las pills **solo cuando ≥1 módulo está "off"**.

```
[Fondo: Oculto ▼]
       Atenuado
       Completo
```

**Estados:**
- **Oculto** (default) — los módulos "off" se eliminan completamente del mapa
- **Atenuado** — los módulos "off" se renderean con opacity 0.3 (CSS class `.module-faded` aplicada a los polígonos/líneas correspondientes)
- **Completo** — los módulos "off" se renderean con opacity normal (equivale a tenerlos "on")

**Implementación:** en lugar de `removeLayer/addLayer` (caro con 108k features), aplicar/quitar una CSS class al canvas renderer y usar `setStyle` para cambiar `opacity` y `fillOpacity` en batch.

### Persistencia (localStorage)

El estado de las pills + control de fondo se guarda en localStorage para que la próxima carga recuerde la última vista del usuario.

```javascript
const VIEW_STATE_KEY = "cs2-mineapolis-view-state-v1";
// {
//   pills: { zoning: "on", vial: "on", servicios: "off", transporte: "off" },
//   fondo: "oculto"
// }
```

Si no hay state guardado, default: todos los módulos enabled están "on", fondo "oculto".

### Capas existentes (Layer Control de Leaflet)

**Sin cambios.** El Layer Control de Leaflet (esquina arriba derecha) sigue mostrando las 13 zonas + 6 categorías viales para fine-tune granular. Las pills y el master toggle son una **capa de abstracción por encima** que opera en bulk.

**Interacción importante:** si el usuario apaga "Zoning" con la pill y luego enciende manualmente una zona específica desde el Layer Control, el estado del Layer Control gana (la zona individual aparece) pero el master toggle de zoning vuelve a estado "mixto" (representado con un círculo ● a medio rellenar). Click en el master toggle "mixto" → resetea a "on" (todas las zonas visibles).

---

## Sección 3 — Migración (alto nivel)

El plan de implementación detalla los pasos. Aquí solo los hitos:

### Fase A — Refactor estructura (sin tocar GitHub)
1. Crear `src/shared/`, `src/zoning/`, `src/vial/` con `__init__.py`
2. Mover archivos con `git mv` (preserva history)
3. Actualizar imports en cada archivo
4. Actualizar `pyproject.toml` a `packages = [...]`
5. Reorganizar `tests/` en sub-carpetas
6. Correr tests — confirmar 72/72 pasando

### Fase B — Prebuilts fuera del repo
7. `git rm --cached visualizer/datos_*.js`
8. Añadir a `.gitignore`
9. Escribir `visualizer/README.md` con instrucciones de uso
10. Crear el GitHub Release `v3.1` (manual desde GitHub UI, o via `gh release create` script)

### Fase C — UI del visualizer
11. Implementar las module pills en `index.html`
12. Implementar master toggles en la leyenda
13. Implementar el control de fondo (Oculto / Atenuado / Completo)
14. Persistencia localStorage
15. Smoke test browser

### Fase D — Branding
16. Rewrite `README.md` y `README.es.md` con la narrativa "toolkit modular"
17. Actualizar METHODOLOGY.md cabecera
18. Actualizar los 6 Reddit drafts del escritorio con nuevo nombre y URL
19. Actualizar Obsidian + memoria persistente con nuevo path/nombre

### Fase E — GitHub
20. Rename repo en GitHub: Settings → Repository name → `cs2-osm-toolkit`
21. `git remote set-url origin https://github.com/Osyanne/cs2-osm-toolkit.git`
22. Push del refactor
23. Renombrar carpeta local: `C:\Users\osyanne\Documents\Claude\Projects\Proyecto mineapolis\cs2-osm-toolkit\`

GitHub mantiene redirect automático del nombre viejo, así que cualquier link externo `cs2-minneapolis-zoning` seguirá funcionando.

---

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Romper los 72 tests por imports cambiados | Refactor en commits atómicos, correr tests tras cada paso. TDD-style: si falla, revertir. |
| Romper el visualizer mientras se reorganiza | Mantener `datos_*.js` en disco durante la migración (solo se sacan del git tracking, no se borran físicamente). Smoke test browser después de cada cambio sustantivo. |
| Rename del repo confunde el setup de pyproject.toml | `pyproject.toml` no referencia el nombre del repo, solo el nombre del package `cs2-minneapolis-zoning`. Esto SÍ habría que actualizar al rename para consistencia, aunque funcionalmente no es bloqueante. |
| Los 6 Reddit drafts quedan con URL vieja | Actualizar los drafts en el desktop (no están publicados aún). |
| Performance del control "Fondo Atenuado" con 108k features | Implementar con `setStyle` batch sobre layer groups, no add/remove de layers individuales. |
| Pre-existing failing test (`test_mixed_apartments_uses_spatial_join`) puede confundir el "72 passing" | Considera arreglar este test pre-existing como parte del refactor de tests/. Solo es cambiar `around.comm:3` → `around.comm:5` en el assert. Out-of-scope estricto pero oportunista. |

---

## Out of scope (para futuras sesiones)

- Sesión 3 (Servicios) y Sesión 4 (Transporte) — el refactor sienta las bases pero no las implementa
- XSS escape en popups de zoning (heredado de Sesión 1 antes de Sesión 2)
- Capturar colores reales del HUD CS2 para refinar paleta pixel-perfect
- Clip al boundary real de Minneapolis (filtrar Edina/St. Louis Park del bbox)
- Etiquetas de barrios overlay

---

## Decisiones tomadas por el usuario (explícitas, no cuestionar)

1. ✅ Renombrar a `cs2-osm-toolkit`
2. ✅ Prebuilts a GitHub Releases (sacar del git tracking)
3. ✅ Sub-carpetas por módulo dentro de `src/`
4. ✅ Module pills multi-select arriba (no tabs radio)
5. ✅ Master toggle en cada section header de la leyenda
6. ✅ Control de fondo 3-way (Oculto / Atenuado / Completo) cuando ≥1 módulo está off
7. ✅ Layer Control de Leaflet existente se mantiene para fine-tune granular
8. ✅ Persistencia localStorage del estado de pills + fondo

---

## Aprobación

Diseño aprobado por el usuario en la conversación del 2026-05-15. Próximo paso: invocar `superpowers:writing-plans` para generar el plan de implementación detallado.
