# Plan — Sesión 1.6: Realineamiento de Zonas a CS2 Oficial

**Fecha:** 2026-05-13
**Workspace:** `cs2-minneapolis-zoning/`
**Predecesor:** [Sesión 1.5 — Fixes y Precisión](./2026-05-13-zoning-visualizer-fixes.md)

---

## Objetivo

Realinear el modelo de zonas del visualizador y del pipeline Python al modelo oficial de **Cities: Skylines 2** para que las categorías mostradas en el plano correspondan 1:1 con las que el usuario zonifica dentro del juego.

## Motivación

El screenshot de la leyenda actual mostró 4 problemas concretos:

| Síntoma | Causa raíz |
|---|---|
| `com_high = 0` polígonos | Clasificador exige `>=4 niveles` pero la query es `landuse=commercial` (zonas, no edificios sin `building:levels`) |
| `mixed_res_com = 0` polígonos | Query requiere combo `residential=yes` + `landuse=commercial` — combo casi inexistente en OSM |
| `mixed = 2` polígonos | Tags `landuse=mixed` / `building=mixed_use` son raros en Minneapolis OSM |
| `res_low = 5,920` domina | Fallback por defecto se traga todo cuando faltan `building:levels` |

Además, el modelo actual tiene **10 zonas + 2 parking**, pero CS2 oficial tiene **10 zonas + 2 sub-tipos de oficinas + 1 industrial = 11 zonas urbanas**, con estructuras distintas:

- Residencial: **6 tipos** (vs 3 actuales)
- Comercial: **2 tipos** (vs 3 actuales — Retail Hub no existe en CS2)
- Oficinas: **2 tipos** (vs 1 actual — falta High Density Offices)
- Mixto: **1 tipo** (vs 2 actuales — son redundantes)

## Decisiones del usuario

1. ✅ Incluir `res_high` (High Density Housing — torres residenciales)
2. ✅ Fusionar `mixed` + `mixed_res_com` en `res_mixed` (Mixed Housing único de CS2)
3. ✅ Fusionar `retail` en `com_low` (Retail Hub no existe en CS2)
4. ✅ Paleta basada en familias CS2 (verde/azul/morado/amarillo) con juicio

---

## Modelo de zonas nuevo

### Residencial (6 — familia verde)

| Clave | CS2 oficial | Regla OSM | Fill | Neon |
|---|---|---|---|---|
| `res_low_house` | Low Density Housing | `building ∈ {house, detached, bungalow}` o landuse=residential fallback | `#A5D6A7` | `#C8E6C9` |
| `res_row` | Medium Density Row Housing | `building ∈ {terrace, townhouse, row_house, semi, semi_detached, semidetached_house, dormitory}` o `residential ∈ {townhouse, semi, dormitory}` | `#9CCC65` | `#C5E1A5` |
| `res_med` | Medium Density Housing | `building=apartments` con 2-4 niveles efectivos | `#66BB6A` | `#81C784` |
| `res_mixed` | Mixed Housing | `building=apartments` + `shop=*` o `amenity ∈ {restaurant, cafe, bar, pub, fast_food}` en la misma vía, o `landuse=mixed/mixed_use` o `building:use=mixed/residential;commercial` | `#26A69A` | `#4DB6AC` |
| `res_low_rent` | Low Rent Housing | `building ∈ {public_housing, council_house}` o `social_housing=yes` o apartments con 4-6 niveles **y** footprint grande | `#558B2F` | `#7CB342` |
| `res_high` | High Density Housing | `building ∈ {apartments, residential}` con 7+ niveles o `building ∈ {tower, residential_tower, skyscraper}` con uso residencial | `#1B5E20` | `#2E7D32` |

### Comercial (2 — familia azul)

| Clave | CS2 oficial | Regla OSM | Fill | Neon |
|---|---|---|---|---|
| `com_low` | Low Density Business | `landuse=commercial/retail`, `shop=*`, `amenity ∈ {restaurant, fuel, cafe, bar, fast_food, marketplace}`, `building ∈ {retail, supermarket}` con ≤3 niveles | `#039BE5` | `#4FC3F7` |
| `com_high` | High Density Business | `shop=mall`, `tourism=hotel` (grande), `amenity ∈ {cinema, theatre, casino, conference_centre}`, `building=commercial` con ≥4 niveles, polígonos grandes de `landuse=retail` | `#01579B` | `#0277BD` |

### Oficinas (2 — familia morada)

| Clave | CS2 oficial | Regla OSM | Fill | Neon |
|---|---|---|---|---|
| `office_low` | Low Density Offices | `building=office` o `office=*` con 1-3 niveles efectivos | `#9C27B0` | `#BA68C8` |
| `office_high` | High Density Offices | `building=office` con ≥4 niveles o `building=skyscraper` con uso office | `#4A148C` | `#6A1B9A` |

### Industrial (1 — familia amarilla)

| Clave | CS2 oficial | Regla OSM | Fill | Neon |
|---|---|---|---|---|
| `industrial` | Industrial Manufacturing | `landuse=industrial` o `building ∈ {industrial, warehouse, factory}` | `#F9A825` | `#FFCA28` |

### Parking (2 — gris, fuera de zonificación CS2)

| Clave | Concepto | Regla OSM | Fill | Neon |
|---|---|---|---|---|
| `prk_surface` | Estacionamiento superficie | `amenity=parking` superficial | `#B0BEC5` | `#CFD8DC` |
| `prk_ramp` | Parking estructura | `parking ∈ {multi-storey, structure, underground}` | `#37474F` | `#607D8B` |

**Total: 13 categorías** (11 zonas CS2 + 2 parking)

### Caveats

- **OSM no tagea "rent" ni "luxury"** → distinguir `res_low_rent` vs `res_high` se basa en niveles + footprint. Casos ambiguos se asume aceptables porque el visualizador es referencia.
- **Mixed Housing es la única zona "teal"** (#26A69A) — refleja visualmente la mezcla verde+azul. Defendible como diseño aunque CS2 use otro color exacto en el HUD.
- **Footprint area** (m²) se calcula con la fórmula del shoelace + corrección por latitud para "Low Rent" heurística.

---

## Tareas

### Tarea 1 — Plan en disco
- [x] Este archivo

### Tarea 2 — `src/cs2_zones.py`
Reescribir `CS2_LABELS` con 13 keys. Reescribir `build_queries()` con 6 queries paralelas:
- `apartments` (incluye shop/amenity para detectar `res_mixed`)
- `landuse_residential` (fallback para `res_low_house`)
- `residential_subtypes` (terrace, townhouse, etc → `res_row`)
- `commercial` (landuse + retail + shops + amenities)
- `office` (building=office + office=*)
- `industrial` (landuse + buildings)
- `parking` (amenity=parking)

Eliminar queries `mixed`, `mixed_res_com`, `retail` separadas.

### Tarea 3 — `src/classifiers.py`
- Eliminar `classify_residential` (la genérica) — sustituir por funciones más específicas
- Añadir `classify_apartment_v2(tags, area_m2)` que devuelve uno de {`res_med`, `res_mixed`, `res_low_rent`, `res_high`}
- Añadir `classify_residential_building(tags)` para edificios no-apartments (devuelve `res_low_house` / `res_row`)
- Reescribir `classify_commercial(tags, area_m2)` que devuelve `com_low` / `com_high`
- Añadir `classify_office(tags)` que devuelve `office_low` / `office_high`
- Mantener `classify_parking` igual
- Helper `polygon_area_m2(coords)` para heurística de "Low Rent"

### Tarea 4 — `src/extract_zoning.py`
- Actualizar lista de categorías a las 6 nuevas queries
- Loops de clasificación nuevos que llamen a las funciones nuevas
- Output JSON con keys nuevas

### Tarea 5 — `visualizer/index.html`
- Reescribir `ZONES` (objeto JSON con 13 keys + secciones nuevas: Residencial/Comercial/Oficinas/Industrial/Parking)
- Reescribir `QUERIES` (6 queries paralelas)
- Reescribir `CLASSIFIERS` (paridad JS con Python)
- Helper `polyAreaM2(ring)` en JS
- Actualizar `PREBUILT_ZONE_MAP` y `PREBUILT_DATASETS` para las nuevas keys
- Subir versión de cache: `CACHE_KEY = "cs2-mineapolis-zoning-v2"` (invalida cache vieja automáticamente)

### Tarea 6 — `tests/test_classifiers.py`
Añadir tests para las funciones nuevas:
- `test_residential_building_detached_is_low_house`
- `test_residential_building_terrace_is_row`
- `test_residential_building_townhouse_is_row`
- `test_apartment_2_levels_is_med`
- `test_apartment_4_levels_small_is_med`
- `test_apartment_5_levels_big_footprint_is_low_rent`
- `test_apartment_8_levels_is_high`
- `test_apartment_with_shop_is_mixed`
- `test_apartment_with_restaurant_amenity_is_mixed`
- `test_apartment_tower_tag_is_high`
- `test_apartment_public_housing_is_low_rent`
- `test_commercial_mall_is_high`
- `test_commercial_hotel_is_high`
- `test_commercial_shop_is_low`
- `test_office_low_2_floors`
- `test_office_high_5_floors`
- `test_office_skyscraper_is_high`

**Total previsto:** ~32 actuales + ~15 nuevos = **~47 tests**.

### Tarea 7 — pytest
Ejecutar `uv run --with pytest pytest ../tests/ -v` y verificar todos pasan.

### Tarea 8 — Obsidian
Actualizar 3 notas:
- `📋 Estado del Proyecto.md` — añadir Sesión 1.6 completada
- `🏙 CS2-Mineapolis (MOC).md` — link a Sesión 1.6
- `🎨 Colores CS2 Zonificación.md` — nueva paleta de 13 colores
- Crear `📦 Sesión 1.6 — Realineamiento CS2.md` con resumen completo

---

## Out of scope (Sesión 1.6)

- Generar `datos_zonificacion.js` (sigue en modo live)
- Commits + push al repo GitHub (acumulando 1, 1.5, 1.6 sin push)
- Clip al boundary real de Minneapolis
- Etiquetas de barrios
- Sesión 2 (Vial) — desbloqueada al cerrar 1.6

## Riesgos

- `res_low_rent` puede sobre-incluir polígonos por la heurística de footprint. **Mitigación:** umbrales conservadores (≥1500 m² y ≥4 niveles).
- Cambio de keys puede romper `datos_zonificacion.js` si el usuario lo genera con la versión vieja. **Mitigación:** `CACHE_KEY` bumped a v2 invalida cache automáticamente; el `datos_zonificacion.js` no existe localmente, así que no hay nada que romper.
- Queries más grandes pueden timeout. **Mitigación:** mantener concurrencia 2 + retry exponencial 2s/4s/8s heredados de Sesión 1.5.
