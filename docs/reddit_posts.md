# Reddit Post Drafts — CS2 Minneapolis OSM Toolkit

> Author: u/Kingleyend (Reddit) / Osyanne (GitHub)
> Source of truth. Desktop .md files are derived from this document.
> Post these AFTER creating the GitHub repo and uploading screenshots.

---

## v3.2 — CURRENT POSTS (Sesión 3 — Módulo Servicios, 2026-05-17)

3 modules active: Zoning (81k) + Road Network (108k) + Services (2.3k) = ~192k total features.
127 pytest tests passing (37 zoning + 36 vial + 54 services).

---

### Post 1 — r/CitiesSkylines2 [PRIMARY TARGET]

**Title:**
```
[OC] My Minneapolis 1:1 tool now maps real hospitals, schools, fire stations and parks — Services module added (v3.2, free + open source)
```

**Body:**

---

Hey r/CitiesSkylines2!

I've been building a 1:1 Minneapolis in CS2 and sharing the open-source toolkit I made along the way. Quick update: **v3.2 just dropped with a Services module** — and it's the one I was most excited to build.

**What's new in v3.2 — Services module:**

The visualizer now has 5 new toggleable layers that map directly to CS2's service tabs:

🏥 **Healthcare & Deathcare** — real Hennepin Healthcare campuses, clinics, doctor offices, funeral homes, cemeteries
🎓 **Education & Research** — U of M campus, Minneapolis Public Schools, kindergartens, community colleges
🚒 **Fire** — all Minneapolis fire stations, mapped from OSM
🏛️ **Police & Administration** — police HQ, city hall, Hennepin County courthouse, public libraries, Walker Art Center, Orpheum Theatre
🌳 **Parks** — Minnehaha Regional Park, Bde Maka Ska, Theodore Wirth, playgrounds, sports centres, nature reserves

That's **2,273 real features** (1,991 polygons + 282 point markers). When you're placing your CS2 hospitals, you can now see exactly where the real ones are. Same for schools, fire stations, parks — everything lines up with the actual city.

**Things I learned the hard way (v3.2 edition):**

1. **Tier-hiding by zoom was non-negotiable.** With 2,273 service markers on screen at once, low zoom became unreadable. I added zoom ≥ 12 visibility for point markers — polygons are always visible, markers only appear when you're zoomed in enough to actually place buildings. Big improvement.

2. **CS2 doesn't have a "Place of Worship" zone** — and I almost added churches/mosques because OSM has tons of them. But since there's no matching CS2 service slot in the base game, I excluded them. Kept it aligned to what you can actually build in-game.

3. **Libraries, museums, and theatres** go in the Police & Administration bucket (the "A" layer). CS2 doesn't have a dedicated culture tab, so that's the closest match — same as city hall and government offices. The Walker Art Center lives next to the police HQ in the visualizer. Accurate to how CS2 thinks about it.

**Current state of the tool:**

| Module | Features | Status |
|---|---|---|
| Zoning | 81,732 polygons | ✅ Active |
| Road Network | 108,825 roads | ✅ Active |
| Services | 2,273 features | ✅ New in v3.2 |
| **Total visualized** | **~192,000** | 🗺️ |

**Test coverage:** 127 pytest tests passing (37 zoning + 36 vial + 54 services)

**What's next (Sesión 4):**

Infrastructure module — Electricity, Water & Sanitation, Waste Management. OSM is patchy for this stuff so I'm pulling from EIA data + Minnesota GIS Commons + opendata.minneapolismn.gov. Coming soon.

**Repo:** https://github.com/Osyanne/cs2-minneapolis-osm-toolkit

Release v3.1 (with prebuilt datos_servicios.js coming shortly): https://github.com/Osyanne/cs2-minneapolis-osm-toolkit/releases/tag/v3.1

Clone, run `uv run extract_services.py`, open the visualizer. Works for any city — change the bbox.

Happy to answer questions. The services layer is honestly the most fun to use while building — highly recommend toggling parks + zoning simultaneously to see where the real green space is.

---

### Post 2 — r/CitiesSkylines [BROADER AUDIENCE]

**Title:**
```
[OC] Open-source OSM toolkit for 1:1 city builds — now with Services layer (hospitals, schools, parks, fire stations) — works for any city
```

**Body:**

---

Hi r/CitiesSkylines!

I've been building a 1:1 Minneapolis in CS2 and sharing the open-source toolkit I use as a reference. **v3.2 just added a Services module** — now the visualizer maps real-world hospitals, schools, fire stations, parks, and civic buildings alongside zoning and roads.

**What the tool gives you:**

An interactive dark-mode map with 3 toggleable modules:

- **Zoning** — 81,732 polygons classified into the 11 CS2 zone types (works conceptually for CS1 too — just mentally map "High Density Housing" to your preferred CS1 equivalent)
- **Road Network** — 108,825 OSM roads by category (Highway / Major / Minor / Local / Pedestrian / Bike)
- **Services (new in v3.2)** — 2,273 features covering healthcare, education, fire, police/admin, and parks

**Services breakdown (CS2-aligned):**

| CS2 Tab | What's mapped | Real examples |
|---|---|---|
| Healthcare & Deathcare | Hospitals, clinics, doctors, funeral directors, cemeteries | Hennepin Healthcare, HCMC |
| Education & Research | Schools, universities, colleges, kindergartens | U of M, Mpls Public Schools |
| Fire | Fire stations | All MPD fire stations |
| Police & Administration | Police HQ, city hall, courthouse, libraries, museums, theatres | Walker Art Center, Hennepin County Courthouse |
| Parks | Parks, gardens, playgrounds, sports centres, nature reserves | Minnehaha Park, Bde Maka Ska |

**Total features now rendered: ~192,000** (81k zoning + 108k roads + 2.3k services)

**Adapt to your city:**

```bash
uv run extract_zoning.py --bbox "south,west,north,east"
uv run extract_services.py --bbox "south,west,north,east"
```

Tested with Minneapolis but the logic is generic. If you're doing a 1:1 of any city with decent OSM coverage, this should work. CS1 players: the zoning layer is especially useful for getting density gradients right — the classification logic doesn't care which game you're zoning for.

**Repo:** https://github.com/Osyanne/cs2-minneapolis-osm-toolkit

**Release:** https://github.com/Osyanne/cs2-minneapolis-osm-toolkit/releases/tag/v3.1 (datos_servicios.js prebuilt coming shortly)

MIT licensed, no API keys needed. 127 pytest tests passing.

**What's next:** Infrastructure module (Electricity / Water / Waste) via EIA + MN GIS Commons — deferred because OSM doesn't have good coverage for utility infrastructure.

---

### Post 3 — r/openstreetmap [TECHNICAL OSM/GIS AUDIENCE]

**Title:**
```
[OC] Added 5 new Overpass layer types to my OSM urban classifier — healthcare, education, fire, admin/culture, parks (2,273 features, Minneapolis bbox)
```

**Body:**

---

Following up on my earlier post about classifying OSM polygons into urban zoning categories. **v3.2 adds a Services module** — 5 new layer types extracted entirely via Overpass, aligned to Cities Skylines 2's service tabs (but the extractor is generic).

**New in v3.2 — Services module:**

5 Overpass query groups, each producing a JS layer file:

- **H** — Healthcare & Deathcare: `amenity~"^(hospital|clinic|doctors|dentist)"`, `shop=funeral_directors`, `amenity=crematorium`, `landuse=cemetery`
- **E** — Education & Research: `amenity~"^(school|university|college|kindergarten)"`, `office=research`
- **B** — Fire: `amenity=fire_station`
- **A** — Police & Administration: `amenity~"^(police|townhall|courthouse|prison|library|museum|theatre|arts_centre|cinema)"`, `office=government`
- **P** — Parks: `leisure~"^(park|garden|playground|sports_centre|nature_reserve)"`

**Total extracted from Minneapolis bbox:** 2,273 features (1,991 polygons + 282 point markers), 1.3 MB prebuilt JS.

**Technical notes that might be useful:**

### 1. name=* filter for cultural subtypes

The `amenity=theatre` tag in OSM is broad — it catches everything from actual theatres to school auditoriums to church halls. Using `["name"]` as a required filter keeps only named institutions and eliminates ~60% of noise in Minneapolis. Worth noting for anyone building similar pipelines.

### 2. Libraries, museums, theatres bucketed into "admin" (A layer)

CS2's base game doesn't have a dedicated culture/arts service tab. The closest match for civic/cultural amenities is the Police & Administration tab. So `amenity=library`, `amenity=museum`, `amenity=theatre`, `amenity=arts_centre`, `amenity=cinema` all land in bucket A alongside city hall and the courthouse. Mention this because it means the A layer query is the most heterogeneous — if you're reusing the pipeline for something other than CS2, you'd split these.

### 3. Places of worship deliberately excluded

`amenity=place_of_worship` has excellent OSM coverage in Minneapolis (hundreds of features). I excluded them entirely because there's no matching service slot in CS2's base building types. If you're using the pipeline for non-game urban analysis, that query group is easy to add back.

### 4. Async chunked render was necessary at this scale

The previous modules (zoning, roads) had a sync → async migration already done. With 2,273 service features, the browser was blocking on first render (sync was fine at 200 features, not at 2,273). Fixed by reusing the same chunked async pattern from the road module: 500 features/batch, `setTimeout` yield between chunks.

### 5. OSM coverage is patchy for infrastructure

I originally planned to include Electricity, Water/Sanitation, and Waste Management in this session. OSM coverage for utility infrastructure in Minneapolis is insufficient — power substations show up but distribution lines and water treatment facilities are sparse. Deferred to Sesión 4, which will pull from EIA, Minnesota GIS Commons, and opendata.minneapolismn.gov instead.

**Known weakness (same as before):** Overpass returning HTTP 200 with `{"elements": []}` on silent overload. Multi-endpoint retry doesn't trigger on empty responses. Still haven't found a clean fix for this — semantic validation of expected min counts is the direction I'm considering.

**Repo:** https://github.com/Osyanne/cs2-minneapolis-osm-toolkit

**Release (prebuilt files):** https://github.com/Osyanne/cs2-minneapolis-osm-toolkit/releases/tag/v3.1 (datos_servicios.js coming shortly)

127 pytest tests passing (37 zoning + 36 vial + 54 services). Methodology doc updated.

---

### Post 4 — r/Python [DEVELOPER AUDIENCE]

**Title:**
```
Showcase: OpenStreetMap → urban services classifier — new sub-package with TDD, async chunked render fix, 127 pytest tests, uv-managed
```

**Body:**

---

**What My Project Does**

Pulls real-world urban data from OpenStreetMap via the Overpass API and classifies it into typed categories for city analysis. Originally built as a reference layer for a Cities: Skylines 2 build of Minneapolis, but the extractors are generic — any city with decent OSM coverage works.

**v3.2 adds a Services sub-package** with 5 new extractors (healthcare, education, fire, police/admin, parks) and brings the test suite from 72 → **127 pytest tests** (37 zoning + 36 vial + 54 services).

**Target Audience**

- Developers interested in HTTP retry/cache patterns for unreliable public APIs
- Anyone doing urban analysis with OSM data
- Folks learning async patterns in browser-side JS triggered from a Python pipeline
- TDD practitioners (test suite grew 76% this session)

**Architecture — 3 active sub-packages:**

```
src/
├── zoning/               # 81,732 polygons → 11 CS2 zone types
│   ├── cs2_zones.py      # Pure data: zone definitions + Overpass templates
│   ├── classifiers.py    # Pure logic: tag → CS2 zone (37 unit tests)
│   └── overpass_client.py
├── vial/                 # 108,825 roads → 6 road categories
│   ├── road_classifier.py
│   └── extract_vial.py
└── services/             # 2,273 features → 5 CS2 service categories (new v3.2)
    ├── service_classifier.py  # 54 unit tests
    └── extract_services.py
```

Total features rendered: ~192,000. All sub-packages share the same Overpass client and retry logic.

**Python-specific highlights in v3.2:**

**1. Async chunked render was the critical bug fix**

With 2,273 service features, the synchronous JS render was blocking the browser's main thread. The bug was subtle: 200 features rendered fine, 2,273 froze the tab. Traced to the render loop being synchronous — same problem that existed in the road module before v3.1.

Fix: chunked async with `setTimeout` yield between batches:

```javascript
async function renderServicesChunked(features, chunkSize = 500) {
    for (let i = 0; i < features.length; i += chunkSize) {
        const chunk = features.slice(i, i + chunkSize);
        chunk.forEach(f => renderFeature(f));
        await new Promise(resolve => setTimeout(resolve, 0)); // yield to UI
    }
}
```

The `await new Promise(resolve => setTimeout(resolve, 0))` pattern is easy to underestimate. At 2,273 features it's the difference between "works" and "tab crashes."

**2. TDD drove the classifier design**

54 unit tests were written before the service_classifier.py implementation. Pattern: write test for "hospital amenity → H bucket", "library amenity → A bucket", "park leisure → P bucket", run red, implement minimum logic to pass. Clean result: the classifier has zero conditional logic not covered by a test.

```python
# Test-first example
def test_library_goes_to_admin_bucket():
    feature = {"type": "node", "tags": {"amenity": "library", "name": "Central Library"}}
    assert classify_service(feature) == "admin"  # A layer

def test_unnamed_amenity_excluded():
    feature = {"type": "node", "tags": {"amenity": "theatre"}}
    assert classify_service(feature) is None  # name=* required
```

**3. name=* filter prevents OSM noise**

`amenity=theatre` without a name filter returns school auditoriums, church halls, and community rooms. Requiring `name` as a tag reduces noise by ~60% with one line of logic. Worth knowing for any OSM pipeline.

**4. uv + hatchling — still the right choice**

Zero friction for new sub-packages: add `[tool.hatch.build.targets.wheel] packages = ["src/services"]` to pyproject.toml, done. No setup.py, no MANIFEST.in drama. `uv run extract_services.py` just works.

**Comparison to alternatives**

Same as before: no PostGIS, no QGIS, no GeoPandas. Just `requests` + `tqdm` for the extractors. `shapely` only for the optional augmentation script.

**Repo:** https://github.com/Osyanne/cs2-minneapolis-osm-toolkit

**Release:** https://github.com/Osyanne/cs2-minneapolis-osm-toolkit/releases/tag/v3.1

Open to feedback — especially on the "empty 200 OK from Overpass" problem (retry doesn't trigger on empty responses, so occasionally you get a partial result that looks successful).

---

### Post 5 — r/Minneapolis [LOCAL PRIDE AUDIENCE]

**Title:**
```
[OC] Updated my interactive Minneapolis map — now shows real hospitals, schools, parks, and civic buildings (all from OpenStreetMap data)
```

**Body:**

---

Hey Mineapolis 👋

A few months ago I shared an interactive zoning map of Minneapolis built from OpenStreetMap data. I've been adding modules to it ever since. **v3.2 adds a Services layer** — now you can see where the real hospitals, schools, fire stations, parks, and civic buildings actually are.

Every feature is a real location, pulled from OSM:

🏥 **Healthcare** — Hennepin Healthcare main campus, HCMC, clinics scattered through the city, plus cemeteries and funeral homes
🎓 **Education** — University of Minnesota (it's huge when you see it on the map), all Minneapolis Public Schools buildings, community colleges, kindergartens
🚒 **Fire** — Every MPD fire station in the city
🏛️ **Civic & Culture** — Minneapolis City Hall, Hennepin County Government Center, the downtown library, **Walker Art Center**, Orpheum Theatre, First Avenue (yes it shows up as an arts centre)
🌳 **Parks** — Minnehaha Regional Park, Bde Maka Ska, Theodore Wirth Park, every neighborhood playground, all the sports centres

Fun things to look at:

- **U of M is enormous.** The campus polygon on the map is genuinely surprising if you haven't walked it. It stretches way further east than you'd expect.
- **The park system is incredible.** Toggle parks + zoning together and you can see why Minneapolis consistently ranks high for green space — there's a park within a few blocks of basically every residential neighborhood.
- **Walker Art Center shows up next to a police station** in the layer visualization. That's because CS2 (the game I'm building this for) doesn't have a separate arts/culture tab, so libraries, museums, and theatres all get grouped with government buildings. Accurate to the game, weird IRL.
- **I could have added churches** — OSM has hundreds of them tagged in Minneapolis — but I kept the tool aligned with what the game actually lets you build, so no places of worship. The Basilica is conspicuously absent. Sorry.

**Zoning and roads are still there too** — this is now a 3-layer map: zones (81k polygons), roads (108k features), and services (2.3k features). Toggle each layer on/off with the pill buttons.

As always, **it's only as accurate as OpenStreetMap**. If you notice your neighborhood park isn't on there or a hospital is misplaced, that's an OSM gap — anyone can fix it at openstreetmap.org and it'll show up in the next extraction.

Repo (free, open source): https://github.com/Osyanne/cs2-minneapolis-osm-toolkit

Curious what you notice. I'm always surprised by how the Northeast / South divide shows up so clearly in the data.

---

### Post 6 — r/MapPorn [VISUAL CARTOGRAPHY AUDIENCE]

**Title:**
```
Minneapolis zoning, roads, and services — ~192,000 real features from OpenStreetMap rendered as a layered dark-mode map [OC]
```

**Body:**

---

Made this using OpenStreetMap data via the Overpass API. Three toggleable layers, all rendered on CartoDB's Dark Matter basemap:

**Layer 1 — Zoning (81,732 polygons):**
Every building and land parcel classified into 13 zone types. Six shades of green for residential density, blues for commercial, purples for office, yellow for industrial. The residential gradient is the most visually striking part — you can see exactly where South Minneapolis shifts from single-family to mid-rise apartments along Hennepin and Nicollet.

**Layer 2 — Road Network (108,825 LineStrings):**
Roads classified by hierarchy: white for highways, grey → pale for local streets, teal for bike infrastructure, dotted for pedestrian-only. The Minneapolis grid snaps into focus immediately. The river crossings stand out clearly.

**Layer 3 — Services (2,273 features, new in v3.2):**
Letter-in-circle markers for point features, colored polygons for campuses and parks:
- 🔴 H — Hospitals, clinics, cemeteries
- 🔵 E — Schools, university campuses (U of M is a big one)
- 🟠 B — Fire stations (small circles scattered evenly across the city)
- 🟣 A — City hall, courthouse, libraries, Walker Art Center, theatres
- 🟢 P — Parks, playgrounds, nature reserves (Minnehaha Regional Park, Bde Maka Ska, Theodore Wirth)

**Total rendered: ~192,000 features** across all three layers.

**Visible patterns:**
- The Minneapolis grid (perfectly orthogonal SW of the river)
- Mississippi River cutting diagonally NW→SE
- Downtown's tight cluster of purple skyscrapers surrounded by civic markers
- U of M campus — larger than it looks on Google Maps
- Chain of parks along the lakes (Bde Maka Ska, Cedar, Harriet) interrupting the residential grid beautifully
- Industrial spine following the Hiawatha railway corridor south
- Fire station coverage is remarkably uniform — you can see the city planned these carefully
- Suburbia bleeding north (St. Anthony, Columbia Heights) with noticeably less mapping detail

**Technical notes for the cartography-interested:**
The markers for services use a zoom ≥ 12 visibility threshold — at city-wide view only polygons (parks, campuses) are visible; individual markers appear when you zoom into neighborhoods. Prevents the map from becoming unreadable at low zoom with 2,273 markers competing for space.

Pipeline is open source if you want to do the same for your city:
https://github.com/Osyanne/cs2-minneapolis-osm-toolkit

Originally built for a Cities: Skylines 2 recreation of Minneapolis — that's why the color palette mirrors the CS2 zone painter. Turned out to be a useful standalone visualization.

---

## v3.0 — PREVIOUS POSTS (Sesión 2 — Módulo Vial, 2026-05-15)

Kept for history. See individual Desktop .md files or git history for full content.

Summary of what changed v3.0 → v3.2:
- Added Services module (5 layer types, 2,273 features)
- Tests: 72 → 127
- Total features: ~190k → ~192k
- Bug fix: sync render → async chunked for services layer
- Tier-hiding by zoom for service markers

---

## v1.0 — ORIGINAL POSTS (history)

Kept for history — see git log for full content.

---

## Posting checklist (v3.2)

- [ ] datos_servicios.js uploaded to v3.1 release
- [ ] Screenshots include services layer visible
- [ ] Post to r/CitiesSkylines2 first (Día 1)
- [ ] r/Python with "Showcase" flair (Día 2)
- [ ] r/openstreetmap (Día 3)
- [ ] r/MapPorn with [OC] tag (Día 5)
- [ ] r/Minneapolis (Día 6)
- [ ] r/CitiesSkylines last, 24h+ after CS2 (Día 8)
- [ ] Reply to comments within first hour for visibility boost
