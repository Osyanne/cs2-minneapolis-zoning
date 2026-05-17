# CS2 Minneapolis OSM Toolkit — v3.2

> Datos GIS reales de OpenStreetMap → Cities: Skylines 2
> Toolkit modular · 100% open source · Sin API keys · Mapa interactivo dark

![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue)
![License MIT](https://img.shields.io/badge/License-MIT-green)
![OSM Data](https://img.shields.io/badge/Data-OpenStreetMap-orange)
![Tests](https://img.shields.io/badge/tests-127%20passing-success)

> 🇬🇧 English version: [README.md](README.md)

---

## Inicio rápido — Elige tu camino

### Opción A: Solo ver Mineapolis (5 minutos, sin Python)

Descarga los archivos de datos precompilados desde la [última release](https://github.com/Osyanne/cs2-minneapolis-osm-toolkit/releases):

1. Descarga `datos_zonificacion.js`, `datos_vial.js` y `datos_servicios.js`
2. Descarga o clona el repo para tener la carpeta `visualizer/`
3. Coloca los tres archivos `.js` en la carpeta `visualizer/`
4. Haz doble clic en `visualizer/index.html`

Listo. Sin terminal, sin Python, sin configuración.

### Opción B: Usarlo para tu ciudad (15–20 minutos, requiere Python)

Guía paso a paso completa (instalar Python, instalar uv, encontrar el bbox de tu ciudad, ejecutar los extractores): [docs/QUICKSTART.md](docs/QUICKSTART.md).

La versión corta:
1. Instala Python 3.11+ con la casilla "Add to PATH" marcada, luego instala uv
2. Abre una terminal en la carpeta `src/` y ejecuta `uv sync`
3. Ejecuta los tres extractores con el bounding box de tu ciudad:

        uv run extract-zoning --bbox "sur,oeste,norte,este"
        uv run extract-vial --bbox "sur,oeste,norte,este"
        uv run extract-services --bbox "sur,oeste,norte,este"

Ver también: [docs/adapting-to-other-cities.md](docs/adapting-to-other-cities.md) para guía de calibración específica por ciudad y ejemplos de bbox.

**¿Algo no funciona?** Ver [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

### Opción C: Desarrollar o contribuir

Clona el repo, ejecuta `uv sync` dentro de `src/`, corre los tests con `uv run pytest`. Todos los detalles técnicos abajo.

---

## ¿Qué hace este toolkit?

Un toolkit modular que extrae datos reales de infraestructura desde OpenStreetMap (vía Overpass API) y los renderiza en un mapa Leaflet dark-mode interactivo. Sirve como referencia visual para construir Mineapolis 1:1 en Cities: Skylines 2. Tres módulos, ~192k features en total.

### 🗺 Módulo Zonificación
Clasifica todos los polígonos de edificios en los **11 tipos de zona oficiales de Cities: Skylines 2** (Low/Medium/High Density Residential, Row Housing, Mixed Housing, Low Rent Housing, Low/High Density Business, Low/High Density Offices, Industrial Manufacturing). 81.732 polígonos en el bbox de Mineapolis.

Ejecutar: `cd src && uv run extract-zoning`
Salida: `visualizer/datos_zonificacion.js` (~28 MB)

### 🛣 Módulo Red Vial
Clasifica todas las vías OSM en las **6 categorías de carretera de CS2** (Highway, Major Road, Minor Road, Local Street, Pedestrian Path, Bike Lane). Se renderiza como capa de LineStrings. 108.825 features.

Ejecutar: `cd src && uv run extract-vial`
Salida: `visualizer/datos_vial.js` (~25 MB)

### 🏥 Módulo Servicios
5 capas alineadas a las solapas de servicios base de Cities: Skylines 2 con buena cobertura OpenStreetMap:

- **H** Atención sanitaria y funeraria — hospitales, clínicas, doctors, funeral directors, crematorios, cementerios
- **E** Educación e investigación — schools, universities, colleges, kindergartens, research institutes
- **B** Bomberos — fire stations
- **A** Policía y administración — police HQ, city hall, courthouses, prison + landmarks culturales (bibliotecas, museos, teatros, arts centres, cinemas) + oficinas de gobierno
- **P** Parques — parks, nature reserves, gardens, playgrounds, sports centres

Ejecutar: `cd src && uv run extract-services`
Salida: `visualizer/datos_servicios.js` (~1,3 MB)

**Notas:**
- Bibliotecas, museos, teatros, arts centres, cinemas comparten el bucket `admin` con policía y oficinas de gobierno. Se diferencian solo por nombre + subtype en el popup.
- Lugares de culto descartados conscientemente (no en estructura CS2 base).
- Electricidad, agua y saneamiento, gestión de residuos diferidos a Sesión 4 (requieren fuentes EIA + MN GIS Commons + opendata.minneapolismn.gov, no OSM).
- Bbox de Minneapolis típicamente devuelve ~2.300 features. Render async chunked para no bloquear el browser.

### Próximos
- 🚌 Módulo Transporte (Blue/Green Line, BRT, rutas de bus, ciclovías) — Sesión 4

---

## Features del visualizer

- **Module pills (arriba derecha)**: toggle módulos enteros en un click
- **Master toggles en leyenda**: mismo efecto, espejado en la barra lateral
- **Modo de fondo** (cuando hay módulos apagados): Oculto / Atenuado / Completo
- **Layer Control** (arriba derecha): toggle granular por zona / categoría vial
- **Canvas renderer**: pan/zoom fluido con 80k+ polígonos + 108k linestrings
- **Tier-based hiding**: casas individuales se ocultan en zoom <14, bloques siempre visibles
- **Paleta fiel a CS2**: 4 familias (verde/azul/morado/amarillo) alineadas al HUD del juego
- **Tema oscuro**: basemap CartoDB Dark Matter
- **Persistencia**: estado de la vista guardado en localStorage (`cs2-mineapolis-view-state-v1`)

---

## Setup técnico

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

Los archivos prebuilt `datos_*.js` (~53 MB en total) **no están** en este repo. Dos opciones:

**Opción A — Descargar desde GitHub Releases** (recomendado):
1. Ir a https://github.com/Osyanne/cs2-minneapolis-osm-toolkit/releases
2. Descargar `datos_zonificacion.js`, `datos_vial.js` y `datos_servicios.js` desde la última release
3. Colocarlos en `visualizer/`

**Opción B — Regenerar localmente**:
```bash
cd src
uv run extract-zoning    # ~3-5 min
uv run extract-vial      # ~30s
uv run extract-services  # ~30s
```

### Levantar el visualizer

```bash
cd visualizer
python -m http.server 8080
# Abrir http://localhost:8080/index.html
```

### Correr tests

```bash
cd src
uv run pytest
```

127 tests pasando en módulos de zoning, vial y services.

---

## Estructura del proyecto

```
src/
├── shared/
│   └── overpass_client.py    # Cliente Overpass con retry + rotación de endpoints
├── zoning/
│   ├── zones.py              # Modelo de zonas CS2 + queries Overpass
│   ├── classifiers.py        # Clasificador OSM tag → zona CS2
│   ├── extract.py            # Pipeline CLI (entry: extract-zoning)
│   ├── patch_colors.py       # Utility de paleta
│   └── extract_msbuildings.py  # Augmentación experimental con MS Buildings
├── vial/
│   ├── zones.py              # Modelo de vías CS2 + query Overpass
│   ├── classifiers.py        # Clasificador OSM highway tag → categoría vial
│   └── extract.py            # Pipeline CLI (entry: extract-vial)
└── services/
    ├── zones.py              # Modelo de servicios CS2 + queries Overpass (5 buckets)
    ├── classifiers.py        # Clasificador OSM tags → bucket H/E/B/A/P
    └── extract.py            # Pipeline CLI (entry: extract-services)

tests/
├── zoning/                   # 61 tests (50 classifiers + 11 query sanity)
├── vial/                     # 12 tests
└── services/                 # 54 tests

visualizer/
├── index.html                # Visualizer Leaflet single-file con module pills
└── README.md                 # Cómo obtener prebuilts

docs/
├── QUICKSTART.md             # Guía ELI5 para usuarios no técnicos
├── TROUBLESHOOTING.md        # Errores comunes y soluciones
├── adapting-to-other-cities.md
├── bbox-mcp-server.md
├── cs2-zone-reference.md
├── github-publishing.md
├── plans/                    # Planes de implementación por sesión
└── specs/                    # Specs de diseño
```

---

## Stats del proyecto

| | |
|---|---|
| **Módulos** | 3 (Zonificación, Red Vial, Servicios) — 1 pendiente (Transporte) |
| **Bounding box** | `44.86,-93.38,45.05,-93.17` (Mineapolis + bordes inmediatos) |
| **Features totales** | ~192.830 (81.732 zoning + 108.825 vial + 2.273 servicios) |
| **Tests** | 127 pasando |
| **Última extracción** | 2026-05-16 |

---

## Adaptarlo a otras ciudades

El bbox es paramétrico — apunta los extractores a un `--bbox` distinto y obtienes el mismo mapa para cualquier ciudad con cobertura OSM.

Ver [docs/adapting-to-other-cities.md](docs/adapting-to-other-cities.md) para guía específica por ciudad, ejemplos de bbox y calibración de umbrales de densidad.

---

## Licencia

MIT. Datos OSM via OpenStreetMap contributors bajo ODbL.
