# Visualizador de Zonificación — Plan de Fixes y Mejoras de Precisión

> **Para workers agénticos:** REQUIRED SUB-SKILL: Usar `superpowers:subagent-driven-development` (recomendado) o `superpowers:executing-plans` para implementar este plan tarea por tarea. Los pasos usan checkboxes (`- [ ]`) para tracking.

**Goal:** Resolver los 5 bugs activos en `visualizer/index.html` y mejorar la precisión del mapa de zonificación de Minneapolis usando datos pre-generados como fuente primaria, con cobertura más amplia de tipos OSM.

**Architecture:** Cargar `datos_zonificacion.js` (generado por pipeline Python) como fuente primaria → si no existe, fallback a Overpass live con retry exponencial → cache en `localStorage` con TTL 24h. Ampliar clasificadores para detectar tipos OSM adicionales (`building=detached/house/terrace`, `shop=*`, `building=retail/supermarket`) y resolver el solapamiento UI entre Layer Control y leyenda con CSS de scroll vertical.

**Tech Stack:** HTML5 / Vanilla JS / Leaflet 1.9.4 / Overpass API / localStorage / Python 3.11+ con uv y pytest para los tests del pipeline.

---

## Mapa de archivos

| Archivo | Rol | Cambios |
|---|---|---|
| `cs2-minneapolis-zoning/visualizer/index.html` | Visualizador único | Modificado en cada tarea (bug fixes + precisión) |
| `cs2-minneapolis-zoning/visualizer/datos_zonificacion.js` | Datos pre-generados | Generado por `extract_zoning.py` (ya existe el script) |
| `cs2-minneapolis-zoning/src/classifiers.py` | Clasificadores Python | Ampliar reglas para detectar más subtipos |
| `cs2-minneapolis-zoning/src/cs2_zones.py` | Queries Overpass | Ampliar queries (`shop=*`, `building=retail`) |
| `cs2-minneapolis-zoning/tests/test_classifiers.py` | Tests pytest | Añadir tests para nuevas reglas |
| `cs2-minneapolis-zoning/tests/test_queries.py` | Tests pytest | Añadir tests de sanidad para nuevos selectores |

---

## Decisiones clave

1. **Datos pre-generados primero, Overpass como fallback.** Resuelve Bug #1 + Bug #3 al mismo tiempo. Si `DATA_*` está definido en `window`, usarlo. Si no, hacer las 9 queries con retry.
2. **Retry con backoff exponencial (3 intentos: 2s, 4s, 8s).** Cada query individual gana resiliencia ante rate limiting.
3. **`localStorage` cache con TTL 24h.** Después de una carga exitosa de Overpass, guardar el resultado para evitar re-fetches en recargas rápidas.
4. **Layer Control con scroll + leyenda en `bottomleft`.** Resuelve Bug #2 sin reorganizar la UI.
5. **`out body geom` en queries que clasifican.** Resuelve Bug #5 garantizando tags presentes.
6. **Ampliar clasificación residencial:** detectar `building=detached/house/semi_detached/terrace` para aumentar precisión sin esperar al pipeline.
7. **Ampliar retail/comercial:** capturar `shop=*` y `building=retail/supermarket` que actualmente se pierden.

---

## Fase A — Fixes de bugs (P0)

### Task 1: Bug #4 — Retry con backoff exponencial en `fetchOP`

**Files:**
- Modify: `cs2-minneapolis-zoning/visualizer/index.html` (función `fetchOP`, ~líneas 268-301)

- [ ] **Step 1: Añadir helper `sleep` antes de `fetchOP`**

Buscar la línea `async function fetchOP(query) {` (~línea 268) y justo antes insertar:

```javascript
// Pausa async — usado por retry exponencial
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
```

- [ ] **Step 2: Envolver `fetchOP` en wrapper con retry**

Reemplazar la línea `async function fetchOP(query) {` por:

```javascript
async function fetchOPRaw(query) {
```

Y dejar el cuerpo igual hasta el cierre de la función (línea 301 aprox). Después de la `}` de cierre de `fetchOPRaw`, añadir:

```javascript
// Retry con backoff exponencial: 2s, 4s, 8s
async function fetchOP(query, label = "query") {
  const delays = [2000, 4000, 8000];
  let lastErr;
  for (let attempt = 0; attempt <= delays.length; attempt++) {
    try {
      return await fetchOPRaw(query);
    } catch (e) {
      lastErr = e;
      if (attempt < delays.length) {
        console.warn(`[${label}] intento ${attempt + 1} falló (${e.message}), reintentando en ${delays[attempt]}ms`);
        await sleep(delays[attempt]);
      }
    }
  }
  throw new Error(`Tras ${delays.length + 1} intentos: ${lastErr.message}`);
}
```

- [ ] **Step 3: Pasar `label` desde `loadAll`**

En la función `loadAll` buscar la línea:

```javascript
const data = await fetchOP(q);
```

Reemplazar por:

```javascript
const data = await fetchOP(q, key);
```

- [ ] **Step 4: Verificación manual en navegador**

Abrir `visualizer/index.html` con un servidor local: `cd cs2-minneapolis-zoning/visualizer && python -m http.server 8080`
Abrir `http://localhost:8080` y abrir la consola (F12).
Verificar: si una query falla por rate limit, en consola aparecen mensajes `[<key>] intento 1 falló (...), reintentando en 2000ms`. Después de la espera reintenta sin re-cargar la página.

- [ ] **Step 5: Commit**

```bash
cd C:/Users/osyanne/Documents/Claude/Projects/Proyecto\ mineapolis/cs2-minneapolis-zoning
git add visualizer/index.html
git commit -m "fix(visualizer): retry con backoff exponencial 2s/4s/8s en fetchOP (Bug #4)"
```

---

### Task 2: Bug #5 — Forzar `out body geom` en queries que clasifican

**Files:**
- Modify: `cs2-minneapolis-zoning/visualizer/index.html` (array `QUERIES`, ~líneas 169-215)

Las queries con clasificación dependen de tags (`building:levels`, `parking`, etc.). `out geom;` puede omitir tags en algunos endpoints. Cambiar a `out body geom;` solo donde se clasifica.

Queries con clasificación: `apartments`, `residential`, `commercial`, `parking`.
Queries sin clasificación (siempre devuelven el mismo tipo): `industrial`, `retail`, `office`, `mixed`, `mixed_res_com` — pueden quedarse, pero por consistencia las migramos todas.

- [ ] **Step 1: Reemplazar todas las ocurrencias de `out geom;` por `out body geom;` en el array QUERIES**

Usar `replace_all: true` con la cadena exacta `);out geom;` → `);out body geom;` en `visualizer/index.html` dentro del array QUERIES (líneas 169-215).

- [ ] **Step 2: Verificar manualmente**

Abrir el visualizador. En la consola del navegador:
```javascript
// Tras recargar, verificar que una query commercial trae tags:
fetch("https://overpass-api.de/api/interpreter?data=" + encodeURIComponent(QUERIES[2].q)).then(r=>r.json()).then(d => console.log(d.elements[0].tags))
```
Debe imprimir un objeto con tags (no `undefined`).

- [ ] **Step 3: Commit**

```bash
git add visualizer/index.html
git commit -m "fix(visualizer): cambiar out geom a out body geom en queries Overpass (Bug #5)"
```

---

### Task 3: Bug #2 — Resolver solapamiento Layer Control / Leyenda

**Files:**
- Modify: `cs2-minneapolis-zoning/visualizer/index.html` (CSS bloque `<style>` + posición de leyenda)

- [ ] **Step 1: Añadir CSS para limitar altura del Layer Control expandido**

Buscar el comentario `/* ══ LEAFLET DARK OVERRIDES ════` (~línea 74) y, dentro de ese bloque después de la regla `.leaflet-control-layers-separator`, añadir:

```css
    /* Bug #2 fix: limitar altura del control de capas expandido para no tapar leyenda */
    .leaflet-control-layers-expanded {
      max-height: 70vh !important;
      overflow-y: auto !important;
      scrollbar-width: thin;
      scrollbar-color: #2a2d3d transparent;
    }
    .leaflet-control-layers-expanded::-webkit-scrollbar { width: 5px; }
    .leaflet-control-layers-expanded::-webkit-scrollbar-thumb {
      background: #2a2d3d; border-radius: 4px;
    }
```

- [ ] **Step 2: Mover la leyenda a `bottomleft` para máxima separación**

Buscar la línea ~425:

```javascript
const legend = L.control({ position: "bottomright" });
```

Reemplazar por:

```javascript
const legend = L.control({ position: "bottomleft" });
```

- [ ] **Step 3: Verificación manual**

Recargar el visualizador. Hacer click en el icono del Layer Control (esquina superior derecha) para expandirlo. Verificar:
- El control aparece con scroll vertical si tiene más de 12 capas visibles
- La leyenda "CS2 Zonificación" ahora está en la esquina inferior izquierda
- Ningún elemento UI se solapa

- [ ] **Step 4: Commit**

```bash
git add visualizer/index.html
git commit -m "fix(visualizer): leyenda a bottomleft + scroll en Layer Control (Bug #2)"
```

---

### Task 4: Bug #3 + #1 — Integrar `datos_zonificacion.js` como fuente primaria

**Files:**
- Modify: `cs2-minneapolis-zoning/visualizer/index.html`

Esta es la corrección crítica. Cambia el flujo de:
```
[abrir HTML] → [9 queries Overpass en vivo] → [render]
```
a:
```
[abrir HTML] → [intentar cargar datos_zonificacion.js]
                ↓
        [si existe → render instantáneo]
        [si NO existe → 9 queries Overpass con retry]
```

- [ ] **Step 1: Añadir tag `<script>` para cargar datos pre-generados (con onerror tolerante)**

Buscar en `<head>` la línea:
```html
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
```

Justo después añadir:
```html
  <!-- Datos pre-generados por extract_zoning.py — opcional, si no existe se usa Overpass live -->
  <script src="datos_zonificacion.js" onerror="window.__noPrebuilt=true"></script>
```

- [ ] **Step 2: Añadir función que detecta y consume datos pre-generados**

Buscar la línea `// MAIN LOADER` (~línea 345). Justo antes de `async function loadAll() {` insertar:

```javascript
// ══════════════════════════════════════════════════════════════════════════════
// PREBUILT DATA LOADER (datos_zonificacion.js)
// ══════════════════════════════════════════════════════════════════════════════
function hasPrebuiltData() {
  // El pipeline genera variables DATA_APARTMENTS, DATA_RESIDENTIAL, etc.
  return typeof DATA_APARTMENTS !== "undefined"
      && typeof DATA_RESIDENTIAL !== "undefined";
}

// Mapeo de claves del pipeline a claves de zona CS2
const PREBUILT_ZONE_MAP = {
  apartments:    (item) => ({ high: "res_high", medium: "res_med", low: "res_low" })[item.zone],
  residential:   (item) => ({ high: "res_high", medium: "res_med", low: "res_low" })[item.zone],
  commercial:    (item) => ({ high: "com_high", low: "com_low" })[item.zone],
  industrial:    () => "industrial",
  retail:        () => "retail",
  parking:       (item) => ({ surface: "prk_surface", ramp: "prk_ramp" })[item.zone],
  office:        () => "office",
  mixed:         () => "mixed",
  mixed_res_com: () => "mixed_res_com",
};

const PREBUILT_DATASETS = {
  apartments:    () => DATA_APARTMENTS,
  residential:   () => DATA_RESIDENTIAL,
  commercial:    () => DATA_COMMERCIAL,
  industrial:    () => DATA_INDUSTRIAL,
  retail:        () => DATA_RETAIL,
  parking:       () => DATA_PARKING,
  office:        () => DATA_OFFICE,
  mixed:         () => DATA_MIXED,
  mixed_res_com: () => DATA_MIXED_RES_COM,
};

function renderPrebuilt(key, items) {
  let count = 0;
  const mapper = PREBUILT_ZONE_MAP[key];
  for (const item of items) {
    const zKey = mapper(item);
    const zone = ZONES[zKey];
    if (!zone || !item.coords || item.coords.length < 3) continue;

    const popup =
      `<div style="min-width:160px">` +
      `<b style="color:#ddd;font-size:13px">${item.name || "Sin nombre"}</b><br>` +
      `<span style="display:inline-block;width:10px;height:10px;background:${zone.neon};` +
      `border-radius:2px;margin-right:5px;vertical-align:middle"></span>` +
      `<span style="color:${zone.neon};font-size:11px">${zone.label}</span><br>` +
      `<span style="color:#555;font-size:10px">OSM id ${item.id}</span></div>`;

    L.polygon(item.coords, {
      color: zone.neon, fillColor: zone.color,
      weight: 0.7, opacity: 0.9, fillOpacity: 0.55,
    }).bindPopup(popup, { maxWidth: 260 }).addTo(groups[zKey]);
    count++;
  }
  return count;
}

async function loadFromPrebuilt() {
  console.log("[prebuilt] datos_zonificacion.js detectado — render instantáneo");
  for (const { key, label } of QUERIES) {
    setP(key, "loading", "⟳ Render…");
    try {
      const items = PREBUILT_DATASETS[key]();
      const count = renderPrebuilt(key, items);
      bump(count);
      setP(key, "done", `✓ ${count.toLocaleString()}`);
    } catch (e) {
      setP(key, "error", "✗ Error render");
      console.error(`[prebuilt:${key}]`, e.message);
    }
  }
}
```

- [ ] **Step 3: Modificar `loadAll` para usar datos pre-generados si existen**

Buscar la línea:
```javascript
async function loadAll() {
  let anyError = false;

  for (const { key, q, label } of QUERIES) {
```

Reemplazar `let anyError = false;` y la apertura del `for` por:

```javascript
async function loadAll() {
  let anyError = false;

  // Bug #3 fix: usar datos pre-generados si están disponibles
  if (hasPrebuiltData()) {
    await loadFromPrebuilt();
    finalizeLoad(false);
    return;
  }

  console.log("[live] sin datos_zonificacion.js — fetching Overpass live (con retry)");
  for (const { key, q, label } of QUERIES) {
```

- [ ] **Step 4: Extraer el cierre de loadAll en una función `finalizeLoad`**

Buscar al final de `loadAll`:
```javascript
  // Finish — hide overlay
  const overlay = document.getElementById("loading");
  if (anyError && total === 0) {
```

Reemplazar todo desde `// Finish — hide overlay` hasta el cierre `}` de `loadAll` (línea ~409) por:

```javascript
  finalizeLoad(anyError);
}

function finalizeLoad(anyError) {
  const overlay = document.getElementById("loading");
  if (anyError && total === 0) {
    document.getElementById("errmsg").style.display = "block";
    document.getElementById("errmsg").textContent =
      "No se pudieron cargar los datos. Abre este archivo desde un servidor web " +
      "(ej: python -m http.server 8080) o usa una extensión de servidor local en VS Code.";
    return;
  }
  overlay.style.transition = "opacity 0.5s";
  overlay.style.opacity    = "0";
  setTimeout(() => { overlay.style.display = "none"; }, 530);

  const sb = document.getElementById("statusbar");
  sb.innerHTML = `<b>${total.toLocaleString()}</b> polígonos · Minneapolis, MN · datos OSM`;
  sb.style.display = "block";
}
```

- [ ] **Step 5: Verificación manual sin datos pre-generados**

Confirmar que `visualizer/datos_zonificacion.js` NO existe en disco.
Abrir el visualizador con servidor local. En consola debe aparecer: `[live] sin datos_zonificacion.js — fetching Overpass live (con retry)`.
Las queries van vía Overpass como antes.

- [ ] **Step 6: Verificación manual con datos pre-generados**

Generar el archivo:
```bash
cd cs2-minneapolis-zoning/src
uv run extract_zoning.py
```
(esto tarda ~10-15 min — si no tienes tiempo, crear un stub de prueba con 1 polígono por categoría)

Recargar el visualizador. En consola debe aparecer: `[prebuilt] datos_zonificacion.js detectado — render instantáneo`.
La carga es instantánea. Las 9 categorías deben mostrar `✓ <N>` sin queries Overpass.

- [ ] **Step 7: Commit**

```bash
git add visualizer/index.html
git commit -m "fix(visualizer): integrar datos_zonificacion.js como fuente primaria con fallback Overpass (Bug #1, #3)"
```

---

### Task 5: localStorage cache con TTL 24h (refuerza Bug #1)

**Files:**
- Modify: `cs2-minneapolis-zoning/visualizer/index.html`

Después de una carga exitosa de Overpass, cachear el resultado por 24h. Si recargas la página dentro de ese plazo, render instantáneo desde cache (sin Overpass, sin pre-generated).

- [ ] **Step 1: Añadir helpers de cache antes de `loadAll`**

Buscar `// PREBUILT DATA LOADER` (sección recién creada en Task 4). Justo antes de ese comentario insertar:

```javascript
// ══════════════════════════════════════════════════════════════════════════════
// LOCALSTORAGE CACHE  (TTL 24h)
// ══════════════════════════════════════════════════════════════════════════════
const CACHE_KEY = "cs2-mineapolis-zoning-v1";
const CACHE_TTL_MS = 24 * 60 * 60 * 1000;

function readCache() {
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (Date.now() - parsed.timestamp > CACHE_TTL_MS) {
      localStorage.removeItem(CACHE_KEY);
      return null;
    }
    return parsed.data;
  } catch (e) {
    console.warn("[cache] no se pudo leer cache:", e.message);
    return null;
  }
}

function writeCache(data) {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify({
      timestamp: Date.now(),
      data,
    }));
  } catch (e) {
    console.warn("[cache] no se pudo escribir cache (¿quota?):", e.message);
  }
}
```

- [ ] **Step 2: Acumular datos crudos en loadAll y persistir tras éxito**

En `loadAll`, después de `console.log("[live] sin datos_zonificacion.js …")`, añadir:

```javascript
  const cached = readCache();
  if (cached) {
    console.log("[cache] usando cache localStorage (<24h)");
    for (const { key, label } of QUERIES) {
      setP(key, "loading", "⟳ Render…");
      try {
        const data = cached[key];
        if (!data) throw new Error("cache vacío para esta key");
        const count = renderRawElements(key, data.elements || []);
        bump(count);
        setP(key, "done", `✓ ${count.toLocaleString()}`);
      } catch (e) {
        anyError = true;
        setP(key, "error", "✗ Error cache");
      }
    }
    finalizeLoad(anyError);
    return;
  }

  const rawCache = {};
```

Después del `for (const { key, q, label } of QUERIES) {` y dentro del bloque `try` (donde antes se rendereaba en línea), justo después de `const data = await fetchOP(q, key);`, añadir:

```javascript
      rawCache[key] = data;
```

Y antes de `finalizeLoad(anyError);`, añadir:

```javascript
  if (!anyError && Object.keys(rawCache).length === QUERIES.length) {
    writeCache(rawCache);
    console.log("[cache] guardado en localStorage para próximas 24h");
  }
```

- [ ] **Step 3: Refactor — extraer renderizado a `renderRawElements(key, elements)`**

El render actual está inline dentro del `for` de `loadAll`. Para reusarlo desde el cache, extraerlo. Buscar el bloque que empieza con `for (const el of (data.elements || [])) {` y termina con la siguiente `}`. Reemplazar las líneas:

```javascript
      let count = 0;

      for (const el of (data.elements || [])) {
        const tags    = el.tags || {};
        const ring    = coords(el);
        if (!ring) continue;

        const zKey    = (CLASSIFIERS[key] || CLASSIFIERS.mixed)(tags);
        const zone    = ZONES[zKey];
        if (!zone) continue;

        const name    = tags.name || tags["addr:street"] || "";
        const popup   =
          `<div style="min-width:160px">` +
          `<b style="color:#ddd;font-size:13px">${name || "Sin nombre"}</b><br>` +
          `<span style="display:inline-block;width:10px;height:10px;background:${zone.neon};` +
          `border-radius:2px;margin-right:5px;vertical-align:middle"></span>` +
          `<span style="color:${zone.neon};font-size:11px">${zone.label}</span><br>` +
          `<span style="color:#555;font-size:10px">OSM ${el.type}/${el.id}</span></div>`;

        L.polygon(ring, {
          color:       zone.neon,
          fillColor:   zone.color,
          weight:      0.7,
          opacity:     0.9,
          fillOpacity: 0.55,
        }).bindPopup(popup, { maxWidth: 260 }).addTo(groups[zKey]);
        count++;
      }

      bump(count);
      setP(key, "done", `✓ ${count.toLocaleString()}`);
```

por:

```javascript
      const count = renderRawElements(key, data.elements || []);
      bump(count);
      setP(key, "done", `✓ ${count.toLocaleString()}`);
```

Después insertar la función `renderRawElements` antes de `// PREBUILT DATA LOADER`:

```javascript
// ══════════════════════════════════════════════════════════════════════════════
// RENDER — Overpass elements crudos → polígonos en el mapa
// ══════════════════════════════════════════════════════════════════════════════
function renderRawElements(key, elements) {
  let count = 0;
  for (const el of elements) {
    const tags = el.tags || {};
    const ring = coords(el);
    if (!ring) continue;

    const zKey = (CLASSIFIERS[key] || CLASSIFIERS.mixed)(tags);
    const zone = ZONES[zKey];
    if (!zone) continue;

    const name = tags.name || tags["addr:street"] || "";
    const popup =
      `<div style="min-width:160px">` +
      `<b style="color:#ddd;font-size:13px">${name || "Sin nombre"}</b><br>` +
      `<span style="display:inline-block;width:10px;height:10px;background:${zone.neon};` +
      `border-radius:2px;margin-right:5px;vertical-align:middle"></span>` +
      `<span style="color:${zone.neon};font-size:11px">${zone.label}</span><br>` +
      `<span style="color:#555;font-size:10px">OSM ${el.type}/${el.id}</span></div>`;

    L.polygon(ring, {
      color: zone.neon, fillColor: zone.color,
      weight: 0.7, opacity: 0.9, fillOpacity: 0.55,
    }).bindPopup(popup, { maxWidth: 260 }).addTo(groups[zKey]);
    count++;
  }
  return count;
}
```

- [ ] **Step 4: Verificación manual**

1. Abrir el visualizador y dejar que cargue completamente vía Overpass.
2. En consola: `localStorage.getItem("cs2-mineapolis-zoning-v1")` — debe imprimir un string JSON grande con timestamp.
3. Recargar la página. Debe aparecer en consola: `[cache] usando cache localStorage (<24h)`. La carga es instantánea.
4. Para forzar re-fetch: `localStorage.clear()` y recargar.

- [ ] **Step 5: Commit**

```bash
git add visualizer/index.html
git commit -m "feat(visualizer): localStorage cache 24h tras carga Overpass exitosa"
```

---

## Fase B — Mejoras de precisión (P1)

### Task 6: Ampliar clasificadores residenciales en JS

**Files:**
- Modify: `cs2-minneapolis-zoning/visualizer/index.html` (objeto `CLASSIFIERS`, ~líneas 222-246)

OSM tiene tags más específicos que `landuse=residential` que el visualizador actualmente ignora. Aprovecharlos eleva la precisión sin esperar al pipeline.

- [ ] **Step 1: Mejorar `CLASSIFIERS.residential` para detectar subtipos por tag `building`**

Reemplazar la función `residential` actual (líneas ~227-235):

```javascript
  residential(tags) {
    const l = lv(tags);
    const r = (tags["residential"] || "").toLowerCase();
    const b = (tags["building"] || "").toLowerCase();
    if (l >= 5 || ["apartments","condominium","condo"].includes(r)) return "res_high";
    if (l >= 3 || ["terrace","dormitory","townhouse"].includes(b)
               || ["townhouse","dormitory","semi"].includes(r))      return "res_med";
    return "res_low";
  },
```

por:

```javascript
  residential(tags) {
    const l = lv(tags);
    const h = parseFloat(tags["height"]) || 0;  // metros
    const r = (tags["residential"] || "").toLowerCase();
    const b = (tags["building"] || "").toLowerCase();

    // Estimar pisos desde altura cuando building:levels falta (3m por piso)
    const estimatedLevels = h > 0 ? Math.round(h / 3) : 0;
    const effectiveLevels = Math.max(l, estimatedLevels);

    // HIGH: 5+ pisos, apartamentos, condos, residencial mixto multi-nivel
    if (effectiveLevels >= 5
        || ["apartments","condominium","condo"].includes(r)
        || ["apartments","tower"].includes(b)) return "res_high";

    // MEDIUM: 3-4 pisos, townhouses, terraces, dorms, semis
    if (effectiveLevels >= 3
        || ["terrace","dormitory","townhouse","semi","semidetached_house","semi_detached"].includes(b)
        || ["townhouse","dormitory","semi"].includes(r)) return "res_med";

    // LOW: casas detached, single-family, residential genérico
    return "res_low";
  },
```

- [ ] **Step 2: Mejorar `CLASSIFIERS.commercial` con `shop`, `office`, y altura**

Reemplazar:

```javascript
  commercial(tags) { return lv(tags) >= 4 ? "com_high" : "com_low"; },
```

por:

```javascript
  commercial(tags) {
    const l = lv(tags);
    const h = parseFloat(tags["height"]) || 0;
    const estimatedLevels = h > 0 ? Math.round(h / 3) : 0;
    const effectiveLevels = Math.max(l, estimatedLevels);
    return effectiveLevels >= 4 ? "com_high" : "com_low";
  },
```

- [ ] **Step 3: Verificación manual**

Recargar visualizador. En consola: hacer click en un polígono residencial conocido — verificar que la zona asignada coincide con la altura real del edificio (ej. una torre del downtown debería ser `res_high`, una casa de Linden Hills `res_low`).

- [ ] **Step 4: Commit**

```bash
git add visualizer/index.html
git commit -m "feat(visualizer): ampliar clasificadores con altura y subtipos building (Bug #5 precisión)"
```

---

### Task 7: Ampliar query `retail` para capturar `shop=*` y building tags

**Files:**
- Modify: `cs2-minneapolis-zoning/visualizer/index.html` (array `QUERIES`)
- Modify: `cs2-minneapolis-zoning/src/cs2_zones.py` (query equivalente)
- Modify: `cs2-minneapolis-zoning/tests/test_queries.py` (test de sanidad)

`landuse=retail` es muy poco usado en Minneapolis. La cobertura real está en `shop=*` (supermercados, ropa, electrónica, etc.) y `building=retail/supermarket`.

- [ ] **Step 1: Añadir test de sanidad para nueva query retail**

Abrir `tests/test_queries.py` y añadir al final:

```python
def test_retail_query_includes_shop_and_building():
    """La query retail debe capturar shop=* y building=retail/supermarket además de landuse."""
    from cs2_zones import build_queries
    q = build_queries("44.86,-93.38,45.05,-93.17")["retail"]
    assert 'shop' in q, "query retail debe incluir selector shop=*"
    assert 'building"="retail"' in q or "building'='retail'" in q, "query retail debe incluir building=retail"
    assert 'building"="supermarket"' in q or "building'='supermarket'" in q, "query retail debe incluir building=supermarket"
```

- [ ] **Step 2: Correr el test, verificar que falla**

```bash
cd cs2-minneapolis-zoning/src
uv run pytest ../tests/test_queries.py::test_retail_query_includes_shop_and_building -v
```
Esperado: FAIL (la query actual no incluye shop ni building=retail).

- [ ] **Step 3: Actualizar query retail en `cs2_zones.py`**

Reemplazar en `cs2_zones.py` el bloque de la query `"retail"`:

```python
        "retail": f"""
[out:json][timeout:180];
(
  way["landuse"="retail"]({bbox});
  relation["landuse"="retail"]({bbox});
);
out geom;
""".strip(),
```

por:

```python
        "retail": f"""
[out:json][timeout:180];
(
  way["landuse"="retail"]({bbox});
  relation["landuse"="retail"]({bbox});
  way["shop"]({bbox});
  way["building"="retail"]({bbox});
  way["building"="supermarket"]({bbox});
);
out body geom;
""".strip(),
```

- [ ] **Step 4: Correr el test, verificar que pasa**

```bash
cd cs2-minneapolis-zoning/src
uv run pytest ../tests/test_queries.py::test_retail_query_includes_shop_and_building -v
```
Esperado: PASS.

- [ ] **Step 5: Replicar la query nueva en `visualizer/index.html`**

Buscar en el array `QUERIES` (línea ~190-194):

```javascript
  {
    key: "retail",
    label: "Retail / Comercio Local",
    q: `[out:json][timeout:90];(way["landuse"="retail"](${BBOX});relation["landuse"="retail"](${BBOX}););out geom;`,
  },
```

Reemplazar por:

```javascript
  {
    key: "retail",
    label: "Retail / Comercio Local",
    q: `[out:json][timeout:90];(way["landuse"="retail"](${BBOX});relation["landuse"="retail"](${BBOX});way["shop"](${BBOX});way["building"="retail"](${BBOX});way["building"="supermarket"](${BBOX}););out body geom;`,
  },
```

- [ ] **Step 6: Verificación manual en navegador**

Recargar visualizador (con cache cleared: `localStorage.clear()`). La capa "Retail / Comercio Local" debe mostrar significativamente más polígonos que antes (esperable: 200-500+ vs ~20-50 antes en Minneapolis).

- [ ] **Step 7: Commit**

```bash
git add visualizer/index.html src/cs2_zones.py tests/test_queries.py
git commit -m "feat(zoning): ampliar query retail con shop=* y building=retail/supermarket"
```

---

### Task 8: Ampliar clasificación residencial en Python con altura

**Files:**
- Modify: `cs2-minneapolis-zoning/src/classifiers.py`
- Modify: `cs2-minneapolis-zoning/tests/test_classifiers.py`

Espejar en Python la lógica de altura que añadimos en JS, para mantener paridad cuando se regenere `datos_zonificacion.js`.

- [ ] **Step 1: Añadir tests fallidos para nueva regla de altura**

Abrir `tests/test_classifiers.py` y añadir al final:

```python
def test_residential_uses_height_when_levels_missing():
    """Cuando building:levels falta pero height está, usar height/3 como pisos estimados."""
    from classifiers import classify_residential
    # Edificio de 18 metros sin levels → ~6 pisos → high
    assert classify_residential({"height": "18"}) == "high"
    # Edificio de 9 metros sin levels → ~3 pisos → medium
    assert classify_residential({"height": "9"}) == "medium"
    # Edificio sin nada → low
    assert classify_residential({}) == "low"


def test_residential_detects_more_building_subtypes():
    """Detectar building=apartments, tower, semidetached_house como medium/high."""
    from classifiers import classify_residential
    assert classify_residential({"building": "apartments"}) == "high"
    assert classify_residential({"building": "tower"}) == "high"
    assert classify_residential({"building": "semidetached_house"}) == "medium"
    assert classify_residential({"building": "semi_detached"}) == "medium"


def test_commercial_uses_height_when_levels_missing():
    """Comercial >= 12m (~4 pisos) → high."""
    from classifiers import classify_commercial
    assert classify_commercial({"height": "15"}) == "high"
    assert classify_commercial({"height": "6"}) == "low"
```

- [ ] **Step 2: Correr los tests, verificar que fallan**

```bash
cd cs2-minneapolis-zoning/src
uv run pytest ../tests/test_classifiers.py -v -k "height or subtypes"
```
Esperado: FAIL (3 tests fallan).

- [ ] **Step 3: Actualizar `classify_residential` para usar altura y más subtipos**

Reemplazar la función `classify_residential` en `classifiers.py`:

```python
def classify_residential(tags: dict) -> str:
    """
    Classify a landuse=residential polygon into CS2 density tiers.

    Uses building:levels primary, falls back to height/3 (3m por piso).
    Recognizes additional building subtypes: apartments, tower, semidetached_house.

    CS2 thresholds:
    - HIGH   (>=5 pisos OR apartments/condo/tower)
    - MEDIUM (>=3 pisos OR terrace/townhouse/semi)
    - LOW    (default)
    """
    tag_levels = int(tags.get("building:levels") or tags.get("levels") or 0)
    try:
        height_m = float(tags.get("height") or 0)
    except (ValueError, TypeError):
        height_m = 0
    estimated_levels = round(height_m / 3) if height_m > 0 else 0
    effective_levels = max(tag_levels, estimated_levels)

    residential_subtype = tags.get("residential", "").lower()
    building_type = tags.get("building", "").lower()

    if (effective_levels >= 5
            or residential_subtype in ("apartments", "condominium", "condo")
            or building_type in ("apartments", "tower")):
        return "high"

    if (effective_levels >= 3
            or building_type in ("terrace", "dormitory", "townhouse",
                                 "semi", "semidetached_house", "semi_detached")
            or residential_subtype in ("townhouse", "dormitory", "semi")):
        return "medium"

    return "low"
```

- [ ] **Step 4: Actualizar `classify_commercial` para usar altura**

Reemplazar la función `classify_commercial`:

```python
def classify_commercial(tags: dict) -> str:
    """
    Classify commercial zones into HIGH or LOW density.

    Usa building:levels o height/3 (3m por piso) como fallback.

    CS2 thresholds:
    - HIGH (>=4 pisos)
    - LOW  (default)
    """
    tag_levels = int(tags.get("building:levels") or tags.get("levels") or 0)
    try:
        height_m = float(tags.get("height") or 0)
    except (ValueError, TypeError):
        height_m = 0
    estimated_levels = round(height_m / 3) if height_m > 0 else 0
    effective_levels = max(tag_levels, estimated_levels)

    return "high" if effective_levels >= 4 else "low"
```

- [ ] **Step 5: Correr los tests, verificar que pasan**

```bash
cd cs2-minneapolis-zoning/src
uv run pytest ../tests/test_classifiers.py -v
```
Esperado: PASS (todos, los nuevos + los 22 originales).

- [ ] **Step 6: Commit**

```bash
git add src/classifiers.py tests/test_classifiers.py
git commit -m "feat(classifiers): usar altura como fallback de building:levels + más subtipos"
```

---

## Fase C — Verificación final y entrega

### Task 9: Smoke test completo y entrega del HTML

**Files:**
- Read: `cs2-minneapolis-zoning/visualizer/index.html`

- [ ] **Step 1: Servir el visualizador localmente**

```bash
cd cs2-minneapolis-zoning/visualizer
python -m http.server 8080
```

Abrir `http://localhost:8080` en el navegador.

- [ ] **Step 2: Checklist de verificación visual**

Verificar uno por uno:
- [ ] Bug #1: Recargar 3 veces — todas las 9 capas cargan en cada recarga (gracias a retry + cache)
- [ ] Bug #2: Expandir Layer Control en esquina superior derecha — tiene scroll, no tapa la leyenda
- [ ] Bug #3: Si `datos_zonificacion.js` existe, en consola se ve `[prebuilt] datos_zonificacion.js detectado`. Si no, se ve `[live] sin datos_zonificacion.js`
- [ ] Bug #4: Si una query falla, la consola muestra `intento N falló … reintentando en Xms`
- [ ] Bug #5: Click en un polígono comercial alto del downtown (ej. IDS Center) — debe clasificarse como Comercial Alta Densidad
- [ ] Precisión: Capa "Retail" muestra muchos más polígonos que antes (incluye supermercados, tiendas)
- [ ] Precisión: Edificios sin `building:levels` pero con `height` se clasifican correctamente por altura

- [ ] **Step 3: Copiar el HTML al outputs para que el usuario lo abra**

```bash
cp cs2-minneapolis-zoning/visualizer/index.html "/sessions/intelligent-nice-ramanujan/mnt/Proyecto mineapolis/visualizer-test/index.html"
```

- [ ] **Step 4: Push al repo (opcional, según prefiera el usuario)**

```bash
cd cs2-minneapolis-zoning
git push origin main
```

- [ ] **Step 5: Reportar al usuario con el archivo final**

Devolver el `visualizer/index.html` final + breve resumen de:
- Cambios aplicados (lista corta)
- Cómo verificarlos
- Próximas mejoras sugeridas (si las hay)

---

## Self-review

**Cobertura de bugs:**
- Bug #1 (carga inconsistente) → Task 4 (datos pre-generados) + Task 5 (cache) + Task 1 (retry)
- Bug #2 (layer control tapa leyenda) → Task 3
- Bug #3 (sin integración js) → Task 4
- Bug #4 (sin retry) → Task 1
- Bug #5 (queries sin tags) → Task 2

**Cobertura de precisión:**
- Más subtipos OSM detectados → Task 6 (JS) + Task 8 (Python con tests)
- Más cobertura retail/comercial → Task 7

**Tests añadidos:**
- 1 test de sanidad para nueva query retail (Task 7)
- 3 tests para clasificadores con altura/subtipos (Task 8)

**Riesgos identificados:**
- El cache localStorage puede saturarse si hay muchos polígonos (>5MB) → manejado con try/catch en `writeCache`
- `datos_zonificacion.js` sin `onerror` rompe la carga → usamos `onerror="window.__noPrebuilt=true"` y `typeof DATA_APARTMENTS !== "undefined"` para detección no fragil
- Las nuevas queries retail con `way["shop"]` pueden devolver puntos (nodes) en vez de ways en algunos casos → no afecta porque `coords()` filtra elementos sin geometría

**Commits previstos:** 8 commits atómicos, uno por task de fase A y B.
