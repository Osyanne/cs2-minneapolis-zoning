# Featured Cities Pack — Design Spec

**Fecha:** 2026-05-17
**Workspace actual:** `cs2-minneapolis-zoning/` (repo: `cs2-minneapolis-osm-toolkit`, rename deferido)
**Predecesor:** [Sesión 3 — Módulo Servicios](../plans/2026-05-16-modulo-servicios.md)
**Versión target:** v3.3

---

## Motivación

Tras Sesión 3, el toolkit es maduro técnicamente (127 tests, 3 módulos, render async chunked) pero sigue hardcoded a Minneapolis a nivel de visualizer. Las ideas validadas en mayo 2026 incluyen "OSM→CS2 SaaS" como roadmap futuro, pero antes de invertir en heightmap pipeline o infraestructura SaaS necesitamos **validar demanda real**.

Adicionalmente, el feedback reciente en r/openstreetmap (mayo 2026) mostró que la comunidad detecta y castiga packaging templatizado. Cualquier movimiento debe preservar la goodwill open-source y evitar acelerar más rápido que la validación de mercado lo justifique.

## Goal

Pivotar a **Phase 1 + Phase 2 combinadas** del roadmap de 3 fases:

1. **Phase 1 — Featured Cities Pack:** parametrizar el pipeline para soportar múltiples ciudades. Generar 4 ciudades nuevas curadas (Manhattan, Tokyo, Amsterdam, Madison) como prebuilts versionados — **inicialmente solo módulo de zonificación**. Minneapolis sigue siendo la ciudad hero con los 3 módulos completos (zoning + vial + services).
2. **Phase 2 — Hosted viewer:** servir el visualizer desde GitHub Pages con URLs amigables `?city=<slug>`, landing page con galería (5 ciudades total: Minneapolis full + 4 nuevas zoning-only), y onboarding para city requests vía GitHub Issues.

**Scope reducido intencional:** Limitar las 4 ciudades nuevas a zoning baja el trabajo de 12 extracts (4×3) a 4, reduce ~70% el storage del pack, y permite validar demanda del módulo más visualmente atractivo antes de comprometerse con vial+services per-city (que pasan a backlog Phase 2.5+ on-demand).

**Lo que NO se hace en este scope** (ver §10): heightmap, backend, SaaS, paywall, live Overpass desde browser, rename del repo, vial+services para las 4 ciudades nuevas.

Sin regresión: los 127 tests existentes deben seguir pasando. Minneapolis sigue funcionando idéntico (3 módulos accesibles vía `?city=minneapolis`).

---

## Sección 1 — Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│  GitHub Pages (estático, servido desde /visualizer)     │
│  ├─ index.html       → landing con galería de 5         │
│  ├─ map.html         → visualizer (lee ?city=)          │
│  ├─ cities.json      → registro: { slug → metadata }    │
│  ├─ cities/<slug>/                                      │
│  │   ├─ manifest.json    → qué módulos están + hashes   │
│  │   ├─ datos_zonificacion.js  (siempre)                │
│  │   ├─ datos_vial.js          (solo Minneapolis V1)    │
│  │   └─ datos_servicios.js     (solo Minneapolis V1)    │
│  └─ assets/thumbnails/<slug>.png  (~200KB c/u)          │
├─────────────────────────────────────────────────────────┤
│  Pipeline Python (offline, máquina del usuario)         │
│  ├─ uv run extract-zoning   --city <slug>   (siempre)   │
│  ├─ uv run extract-vial     --city <slug>   (opcional)  │
│  └─ uv run extract-services --city <slug>   (opcional)  │
│      → leen cities.json, output a cities/<slug>/        │
├─────────────────────────────────────────────────────────┤
│  Onboarding nuevas ciudades                             │
│  └─ Issue template "City Request"                       │
│      → owner abre PR: entry a cities.json               │
│        + corre extract-zoning + push prebuilt           │
│        (vial+services on-demand si hay pedidos)         │
└─────────────────────────────────────────────────────────┘
```

**Tres capas:** site estático (GH Pages), pipeline offline (Python local), workflow de onboarding (Issues → manual PR).

**Cambio fundamental vs estado actual:** el visualizer pasa de single-city hardcoded a multi-city data-driven y por-módulo. El pipeline Python apenas cambia (ya acepta `--bbox`; agrega `--city` como alias que consulta `cities.json`).

**Modularidad por ciudad:** cada ciudad tiene un `manifest.json` que declara qué módulos están disponibles. El visualizer lo lee al cargar e inyecta scripts solo para los módulos presentes. Minneapolis (V1) declara los 3; las 4 nuevas declaran solo `zoning`.

---

## Sección 2 — Componentes

### 2.1 `cities.json` (NUEVO — single source of truth)

Archivo en raíz del repo. Ejemplo ilustrativo del shape (bboxes/centers exactos se definen durante implementación, una vez verificados contra la cobertura OSM de cada ciudad):

```json
{
  "minneapolis": {
    "display_name": "Minneapolis, MN",
    "country": "USA",
    "bbox": [44.86, -93.38, 45.05, -93.17],
    "center": [44.97, -93.27],
    "zoom": 12,
    "tagline": "Ciudad original — fully featured",
    "locale": "es"
  },
  "manhattan": {
    "display_name": "Manhattan, NYC",
    "country": "USA",
    "bbox": [40.700, -74.020, 40.880, -73.910],
    "center": [40.790, -73.965],
    "zoom": 12,
    "tagline": "Grilla densa de rascacielos",
    "locale": "en"
  },
  "tokyo":     { /* mismo shape, bbox + center + zoom + tagline TBD */ },
  "amsterdam": { /* mismo shape */ },
  "madison":   { /* mismo shape */ }
}
```

Único lugar donde se define una ciudad. Consumido tanto por el pipeline Python (lookup de bbox) como por el visualizer JS (validación de slug, metadata para título/bounds/center). Cualquier ciudad nueva entra agregando una entry aquí.

**Importante:** `cities.json` NO declara qué módulos están disponibles por ciudad — eso vive en `cities/<slug>/manifest.json` (single source of truth para "qué hay en disco"). `cities.json` es solo "qué ciudades existen".

### 2.2 Pipeline Python (MODIFICACIÓN MÍNIMA)

Cada `src/{zoning,vial,services}/extract.py` gana:

- Nuevo flag `--city <slug>` que busca en `cities.json` y deriva `bbox` + `slug`.
- Output siempre a `visualizer/cities/<slug>/datos_*.js` (en lugar de `visualizer/datos_*.js`).
- Se elimina la constante `MINNEAPOLIS_BBOX` de cada `zones.py` (deprecada).
- Se quita el branding "Minneapolis" de los `print()` headers (mensajes neutros).
- Se mantiene `--bbox` como escape hatch combinado con `--slug` (uso: generar ciudades de prueba sin tocar `cities.json`).

**Cambio neto estimado:** ~30 líneas por script. Los 127 tests existentes deben seguir pasando con ajustes mínimos (probablemente cambios en path expectations).

### 2.3 `index.html` (REESCRITO — Landing)

Pantalla con galería de 5 cards. Cada card:
- Thumbnail PNG (~200KB)
- `display_name`
- `country`
- `tagline`
- Stats (features count, agregado de los módulos presentes)
- Badges de módulos disponibles (ej. Minneapolis: "Zoning · Vial · Servicios"; Manhattan: "Zoning")
- Link a `map.html?city=<slug>`

Layout: grid responsivo. 5 cards → puede ser 3+2, o 5-in-a-row en desktop wide. Minneapolis puede ir destacada (primera card, "Featured / Most complete") o tratada igual que las demás — se decide visualmente al implementar.

CSS vanilla, sin frameworks. Footer con CTA "¿Tu ciudad no está? Pedila acá" → link al Issue template.

**Generación:** build-time. Script Python lee `cities.json` + cada `manifest.json` (para counts y módulos) + thumbnails, y emite el HTML. Re-corre cada vez que cambia `cities.json` o algún manifest (manual o vía pre-commit hook a futuro). El HTML resultante no tiene JS dinámico.

### 2.4 `map.html` (NUEVO — el visualizer actual, refactorizado)

Es el `index.html` actual movido a `map.html` y modificado:

- Lee `?city=<slug>` del URL.
- Fetch `cities.json` (~2KB, cacheable).
- Valida slug; si inválido → redirect transparente a `/`.
- Fetch `cities/<slug>/manifest.json` (~200B) para saber qué módulos están y sus hashes.
- Inyecta dinámicamente `<script src="cities/<slug>/datos_<modulo>.js?v=<hash>">` **solo para los módulos presentes** en el manifest.
- Espera Promise.all sobre los `onload` (con timeout de seguridad).
- Setea title, footer subtitle, map bounds, map center desde `cities.json[slug]`.
- En el Layer Control y la leyenda: solo muestra controles para módulos cargados (oculta secciones vacías).
- **Elimina** todo el código de live-Overpass fallback (decisión consciente: sólo prebuilt, ver §4).

**Cambio neto estimado:** ~300 líneas modificadas/eliminadas en un archivo de ~1400. La limpieza de live-Overpass es ~200 líneas menos. La lógica condicional por módulo agrega ~50 líneas.

### 2.5 GitHub Issue template (NUEVO)

`.github/ISSUE_TEMPLATE/city-request.yml` con campos estructurados:

- City name (display)
- Slug propuesto (lowercase, sin espacios, sin acentos)
- País / región
- Bbox `south,west,north,east` (+ link a bboxfinder.com en placeholder)
- Por qué esta ciudad (urban form interesante, builder popular que la pidió, etc.)

Hace fácil el request al user y le da al owner toda la info necesaria para correr `extract-zoning --city <slug>` (default Phase 1, ver §6.2) y abrir el PR. Vial y services son ampliación on-demand si la ciudad acumula múltiples requests.

### 2.6 Repo identity — DEFERRED

**No se renombra en este scope.** El repo se queda como `cs2-minneapolis-osm-toolkit` para preservar el SEO/momentum de los posts Reddit v3.2 actuales. El rename a `cs2-osm-toolkit` se hace en una sesión futura cuando el tráfico de los posts actuales decaiga (estimado: 4-6 semanas post-publicación).

Implicación: el README/landing va a tener un mismatch leve entre nombre del repo ("Minneapolis") y contenido ("5 ciudades, Minneapolis hero + 4 nuevas en zoning"). Se mitiga con un párrafo en README explicando "el toolkit nació para Minneapolis, ahora soporta 5 ciudades — rename pendiente".

---

## Sección 3 — Data flow

### 3.1 Runtime flow (usuario visitando el site)

**Caso A — usuario llega a la raíz (`/`):**

```
Browser → GET index.html (estático, build-time)
       → Renderiza galería de 5 cards (Minneapolis full + 4 nuevas)
       → Usuario clickea card "Manhattan"
       → Navega a /map.html?city=manhattan
```

**Caso B — usuario llega con link directo (`/map.html?city=manhattan`):**

```
Browser → GET map.html
       → JS parsea ?city= de URL
       → fetch('cities.json')          (~2KB, cacheable)
       → Valida slug
              ✗ inválido → redirect a /
              ✓ válido   → continúa
       → fetch('cities/manhattan/manifest.json')  (~200B)
       → Lee modules + hashes
       → Inyecta <script> SOLO para módulos presentes:
            Manhattan (V1):    <script src="cities/manhattan/datos_zonificacion.js?v=hash">
            Minneapolis (V1):  <script src="cities/minneapolis/datos_zonificacion.js?v=hash">
                               <script src="cities/minneapolis/datos_vial.js?v=hash">
                               <script src="cities/minneapolis/datos_servicios.js?v=hash">
       → Espera Promise.all sobre onload
       → Setea title/bounds/center/footer desde cities.json[slug]
       → Layer Control + leyenda: solo secciones de módulos cargados
       → Renderiza mapa (mismo código que hoy, lee globals DATA_ZONING/DATA_VIAL/DATA_SERVICES)
```

### 3.2 Build flow (owner generando una ciudad)

**Path A — Nueva ciudad (zoning-only, default Phase 1):**

```
1. Agregar entry a cities.json:
   "tokyo": { display_name: "Tokyo", bbox: [...], center: [...], ... }

2. Correr SOLO extract-zoning:
   uv run extract-zoning --city tokyo

   - Lee cities.json → bbox de Tokyo
   - Query Overpass (paginado/retry como hoy, sub-paquete src/shared/overpass_client)
   - Clasifica features con classifiers compartidos
   - Output a visualizer/cities/tokyo/datos_zonificacion.js
   - Actualiza visualizer/cities/tokyo/manifest.json: { zoning: { hash, features }, generated_at }

3. Regenerar landing:
   uv run generate-landing  (script nuevo, lee cities.json + manifests, emite index.html)

4. Verificación local:
   - Abrir visualizer/map.html?city=tokyo en browser
   - Smoke test: zoning carga, leyenda OK (solo sección zoning), popups OK, console limpia

5. Commit cities.json + cities/tokyo/ + index.html → push → GH Pages se actualiza solo

Tiempo total: ~30-45 min (cuello: Overpass query).
```

**Path B — Re-generar Minneapolis (los 3 módulos, preserva V1):**

```
1. Correr los 3 extracts en orden:
   uv run extract-zoning   --city minneapolis
   uv run extract-vial     --city minneapolis
   uv run extract-services --city minneapolis

2. Cada uno actualiza su entry en manifest.json:
   { zoning: {...}, vial: {...}, services: {...}, generated_at }

3. Regenerar landing + commit + push (igual que Path A).

Tiempo total: ~1-1.5h. Se hace solo cuando hay re-generación intencional de Mpls.
```

**Path C — Agregar vial o services a una ciudad existente (escenario futuro, on-demand):**

```
1. Correr el extract específico:
   uv run extract-vial --city manhattan  (o --city tokyo, etc.)

2. extract actualiza manifest.json: agrega entry "vial"
3. Regenerar landing → la card de Manhattan ahora muestra badge "Zoning · Vial"
4. Commit + push

Habilita la modularidad por demanda sin cambios al pipeline.
```

### 3.3 Manejo de errores

| Caso | Comportamiento |
|------|---------------|
| `cities.json` 404 o malformado | Banner "Site error, please report" + link al Issue template |
| Slug inválido en URL | Redirect transparente a `/` (landing) |
| `manifest.json` 404 o malformado | Banner "City data corrupted" + link al Issue |
| Script `datos_*.js` 404 (módulo declarado en manifest pero archivo missing) | Mensaje "City data missing" + link al Issue + console.error |
| Módulo NO declarado en manifest | **No es error** — comportamiento esperado. Se oculta su toggle/leyenda sin warn. Caso normal para las 4 ciudades nuevas que solo declaran zoning. |
| Una capa carga pero otra falla (parcial inesperado) | Renderiza las disponibles, esconde toggle de la faltante, console.warn |
| Overpass timeout (build-time) | El extract script exit-fail con mensaje claro, owner re-intenta |

---

## Sección 4 — Decisiones de implementación

| Decisión | Elección | Razón |
|----------|----------|-------|
| Carga dinámica de prebuilts | `<script>` injection + `onload` Promise | Los `datos_*.js` actuales son IIFE que setean globals (`DATA_ZONING` etc.). Cambiar a `fetch + JSON.parse` sería re-trabajo grande. Script injection mantiene compat 100%. |
| Cache busting de prebuilts | Query string con hash: `datos_*.js?v=<hash>` | Cuando se regenera una ciudad, browsers cacheados toman versión vieja sin esto. El hash sale de `cities/<slug>/manifest.json` — archivo pequeño escrito por cada extract con `{ modules: { zoning: { hash, features }, vial: {...}, services: {...} }, generated_at: "..." }`. Solo aparecen las keys de los módulos generados (las 4 ciudades nuevas solo tienen `zoning`). El visualizer lo lee primero y arma los URLs con `?v=<hash>` solo por capas presentes. |
| Source of truth de módulos | `manifest.json` per-city (NO `cities.json`) | `cities.json` = "qué ciudades existen". `manifest.json` = "qué datos tiene esta ciudad ahora mismo". Evita drift entre registro y disco. Permite agregar/quitar módulos sin tocar `cities.json`. |
| Renderizado de landing | Build-time, Python genera `index.html` desde `cities.json` + manifests | Cero JS en landing, primera pintura instant. Re-genera con cada cambio de `cities.json` o cualquier manifest. |
| Thumbnails de cards | Screenshots manuales del visualizer en cada ciudad | Una vez por ciudad. ~200KB c/u, 5 cards = ~1MB total. Auto-generación con headless browser es overkill para 5. |
| `--bbox` standalone | Mantenido como escape hatch combinado con `--slug` | Para generar ciudades de prueba sin tocar `cities.json`. Útil para devs y para experimentación. |
| Default si no hay `?city=` en `map.html` | Redirect a `/` (landing) | Más simple que "default to Manhattan". Forza al user a elegir, evita confusión "¿por qué veo Manhattan?". |
| Code path live-Overpass en visualizer | **Eliminado** (no oculto) | ~200 líneas de fallback que sumaban complejidad. Sin ellas el visualizer es notablemente más simple y testeable. Decisión consciente: sólo prebuilt mode. |
| URL scheme | Sólo `?city=<slug>` (sin `?bbox=` arbitrario) | Decidido: registro fijo, no live fetch. Bbox arbitrario requeriría re-introducir Overpass live → contradice decisión anterior. |
| Storage de prebuilts | In-repo en `visualizer/cities/<slug>/` | Minneapolis full (~53MB) + 4 ciudades zoning-only (~15-50MB c/u, estimado ~120MB total) = ~175MB en repo. Manejable. Si crece a 10+ ciudades o si agregamos vial/services per-city después, migrar a GH Releases en Phase 3. |
| Scope per-city Phase 1 | Solo zoning para las 4 ciudades nuevas; Minneapolis preserva los 3 módulos | Reduce trabajo de generación 70%, valida demanda del módulo más visual antes de comprometerse con vial+services per-city. Modularidad por manifest hace que ampliar después sea trivial (Path C en §3.2). |
| Branch strategy | `feature/featured-cities-pack` → PR a main | Convención del repo (Sesiones 1.6, 2, 3 todas usaron feature branches). |

---

## Sección 5 — Testing

| Capa | Estrategia |
|------|-----------|
| Pipeline Python | Los 127 tests existentes deben seguir pasando. ~5 tests nuevos: parser `--city`, lookup en `cities.json`, output path con slug, escritura de `manifest.json`. |
| `cities.json` schema | Test nuevo en `tests/test_cities_registry.py`: valida estructura, 5 entries presentes (minneapolis + manhattan + tokyo + amsterdam + madison), bbox válidos (4 floats, south<north, west<east), slugs lowercase/no-espacios. |
| `manifest.json` schema | Test que valida shape `{ modules: {...}, generated_at }`, que las keys de `modules` están en `["zoning", "vial", "services"]`, y que cada entry tiene `hash` + `features`. |
| Visualizer JS | Sin tests automatizados (el proyecto no tiene framework JS de test). Smoke test manual de las 5 ciudades pre-deploy: cargar `map.html?city=<slug>` para cada una, verificar que: (a) las 4 ciudades nuevas muestran solo zoning + leyenda condensada, (b) Minneapolis muestra los 3 módulos como hoy, (c) popups OK, (d) console limpia. |
| `generate-landing` script | Test que valida que el HTML generado contiene 5 cards + links correctos + thumbnails + badges de módulos correctos (Mpls "Zoning · Vial · Servicios"; otras solo "Zoning"). |
| Integration (manual) | Después de deploy: abrir el URL público de GH Pages, verificar landing + las 5 ciudades responden con sus módulos respectivos. |

---

## Sección 6 — Deployment & onboarding

### 6.1 GitHub Pages setup

- **Source:** `main` branch, directorio `/visualizer`
- **URL final:** `https://osyanne.github.io/cs2-minneapolis-osm-toolkit/`
- **Custom domain:** no en este scope (eventualmente en Phase 3)
- **Branch de trabajo:** `feature/featured-cities-pack` → PR a main cuando esté smoke-tested
- **Versioning:** v3.3 (badge en READMEs + CHANGELOG)

### 6.2 Workflow nueva ciudad (post-launch)

**Default: solo zoning** (consistente con scope Phase 1 para ciudades no-Minneapolis):

```
Trigger:  Issue "City Request" abierto (template guía al user a llenar bbox)
   │
   ▼
Owner:  1. Revisa bbox (validar tamaño razonable, no >50km de lado)
        2. Edita cities.json: agrega entry
        3. Corre extract-zoning --city <nuevo>  (~20-30 min)
        4. Smoke test local: map.html?city=<nuevo>
        5. Si el módulo sube >100MB → ajustar precisión o splittear
        6. Corre generate-landing
        7. Commit + push a main
        8. Cierra el Issue con link al map
```

Tiempo realista: **30-60 min por ciudad nueva (zoning-only)**.

**Si la ciudad acumula 5+ requests por vial o services en el Issue tracker**, se promueve a "fully featured" corriendo los otros 2 extracts (Path C de §3.2). Esto es trabajo post-Phase 1, no parte del scope inicial.

---

## Sección 7 — Estrategia Reddit (post-deploy)

Aprovechando el contexto reciente (backlash anti-template en r/openstreetmap mayo 2026), el plan es **conservador**:

| Subreddit | Estrategia | Riesgo |
|-----------|-----------|--------|
| **r/CitiesSkylines2** | Post principal: "OSM toolkit ahora soporta 4 ciudades nuevas (zoning) + Minneapolis full — pediime las tuyas". Tono builder-focused, foco en visuales. Aclarar que las nuevas son zoning-only (vial/services on-demand). Cuidado con Rule 3 (no direct images): postear como link al map.html con preview, no como image post. | Bajo |
| **r/CitiesSkylines** | Cross-post. CS1 audience también construye 1:1. | Bajo |
| **r/openstreetmap** | **NO postear en Phase 1.** Esperar Phase 2 pulida + escribir desde cero, prosa plana, sin templates. La memoria es explícita: "audiencia anti-spam, detecta packaging". | Alto si no se respeta |
| **r/Minneapolis, r/Madison, r/manhattanNYC, r/japanlife, r/Amsterdam** | Posts dedicados por ciudad, hand-written, foco local. Espaciados 1-2 días, no batch. Para Minneapolis: enfatizar que es la ciudad full-featured. Para las otras 4: ser honesto que es zoning-only de momento. | Medio |
| **r/Python, r/MapPorn** | Skip para Phase 1. No hay novedad técnica grande. Phase 3 (heightmap) sí justifica. | N/A |

Templates Reddit (en Desktop, ya v3.2) se actualizan a v3.3 mencionando "5 ciudades: Mpls full + 4 nuevas zoning". Esos siguen siendo locales (memoria: "NO re-agregar `docs/reddit_posts.md` al repo").

---

## Sección 8 — Métricas de éxito (1 semana post-launch)

Para decidir si pasar a Phase 3 (heightmap + SaaS):

| Métrica | Threshold "vale Phase 3" | Threshold "pivotear a otra idea" |
|---------|--------------------------|----------------------------------|
| City requests vía Issue | >20 en 7 días | <5 |
| Stars en el repo | >50 en 7 días | <10 |
| Tráfico GH Pages (insights) | >500 visitantes únicos | <100 |
| Comentarios negativos r/CS2 | <5% del thread | >20% |

**Lógica:** si los 4 superan threshold "Phase 3" → empezar pipeline heightmap. Si 2-3 superan → seguir agregando ciudades on-demand, no invertir en heightmap. Si <2 → archivar como portfolio piece y mover a otra idea (#1, #3, #4 o #5 de la lista validada en mayo 2026).

---

## Sección 9 — Riesgos

1. **Tokyo OSM tag variations.** Convenciones JP usan `mansion` para apartments, `commercial` con sub-tags distintos. Los classifiers actuales son US-centric.
   *Mitigación:* smoke test temprano de Tokyo; si la clasificación se ve rota, ajustar classifiers compartidos (no per-city). Aplica solo a zoning (las otras módulos no aplican en Phase 1).

2. **Amsterdam cycleway explosion — NO APLICA Phase 1.** Risk diferido. Solo se materializa cuando se promueva Amsterdam a vial (Path C post-Phase-1).

3. **Manhattan zoning size.** Densidad ~5x Mpls, prebuilt zoning podría rozar 50-80MB. GH Pages límite es 100MB/file.
   *Mitigación:* si excede, splittear por sub-categoría o reducir precisión decimal de coords (gana ~30%). Más holgado ahora que solo es zoning (sin vial+services agregando).

4. **Repo size con 5 ciudades scope reducido.** ~175MB total estimado (Mpls full ~53MB + 4 ciudades zoning ~15-50MB c/u). Manejable, lejos del 1GB de GH Pages.
   *Mitigación:* si crece a 10+ ciudades o se promueven módulos, mover a GH Releases en Phase 3.

5. **Mismatch nombre de repo vs contenido.** Repo dice "Minneapolis", landing muestra 5 ciudades.
   *Mitigación:* párrafo en README explicando que el rename está pendiente.

6. **r/openstreetmap re-escalation.** Si alguien encuentra el repo y postea sobre Phase 1 en r/OSM sin avisar.
   *Mitigación:* monitorear menciones del repo en r/OSM la primera semana; si aparece thread negativo, responder en prosa plana sin templates.

7. **Overpass rate limiting al generar 4 ciudades back-to-back.** Con scope reducido son solo 4 extracts (1 por ciudad nueva), no 12. Riesgo mucho menor.
   *Mitigación:* espaciar runs por ciudad (no batch script). El `src/shared/overpass_client` ya hace retry y multi-endpoint.

8. **Expectativas de usuario al ver "zoning only" en cards nuevas.** Riesgo de feedback "¿por qué Manhattan no tiene calles?".
   *Mitigación:* badge claro en card + nota en README + en el visualizer mismo, leyenda menciona "Zoning-only · vial+services próximamente si hay demanda".

---

## Sección 10 — Out of scope (explícito)

Para evitar scope creep, lo siguiente queda **fuera** de Phase 1+2:

- ❌ Heightmap generation (Phase 3)
- ❌ Live Overpass desde browser
- ❌ Backend / API / DB
- ❌ Cuentas de usuario / auth
- ❌ Pago / Patreon / monetización
- ❌ **Vial + services para las 4 ciudades nuevas** (Manhattan, Tokyo, Amsterdam, Madison). Solo zoning en Phase 1. Promoción a "fully featured" es trabajo on-demand post-launch (Path C de §3.2), gateado por demanda real en Issues.
- ❌ Tag-overrides per-city (si Tokyo necesita re-clasificación, se hace en classifiers compartidos)
- ❌ i18n del visualizer (queda en español como hoy)
- ❌ Custom domain
- ❌ Asset Editor / CS2 mod integration
- ❌ Rename del repo (deferido a sesión futura, ver §2.6)
- ❌ Posts en r/openstreetmap (ver §7)

---

## Sección 11 — Open questions

Ninguna bloqueante. Los siguientes se resuelven durante implementación:

- **Layout exacto de las cards** (2×2 vs 4-in-a-row, breakpoints): se decide visualmente al implementar.
- **Estilo de los thumbnails** (raw screenshot vs con overlay del nombre): se decide al generar el primero.
- **Pre-commit hook para regenerar landing**: nice-to-have, no bloqueante. Si se omite, el owner corre `generate-landing` manualmente.

---

## Referencias

- [Sesión 2 — Módulo Vial (plan)](../plans/2026-05-15-modulo-vial.md)
- [Sesión 3 — Módulo Servicios (plan)](../plans/2026-05-16-modulo-servicios.md)
- [Toolkit Reorg (spec previa)](2026-05-15-toolkit-reorg-design.md)
- [Adapting to other cities (doc existente)](../adapting-to-other-cities.md) — referencia para usuarios que quieran adaptar el toolkit fuera del workflow oficial
