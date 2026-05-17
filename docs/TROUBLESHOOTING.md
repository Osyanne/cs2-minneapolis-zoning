# Troubleshooting

Quick fixes for the most common issues. If yours isn't here, open a GitHub Issue — see the bottom of this page.

---

## "Python is not recognized" or "python: command not found"

You didn't check "Add Python to PATH" during installation (easy to miss — it's unchecked by default).

Fix: Reinstall Python from [python.org/downloads](https://www.python.org/downloads/). On the first screen of the installer, check the box that says **"Add Python to PATH"** before clicking Install Now. Then open a new terminal and try again.

If you'd rather not reinstall, you can add Python to PATH manually — search "Edit the system environment variables" in Windows, go to Environment Variables, find PATH under System variables, and add the folder where Python is installed (usually `C:\Users\<you>\AppData\Local\Programs\Python\Python311\` and the `Scripts\` subfolder inside it). Restart your terminal after.

---

## "uv: command not found" or "uv is not recognized"

Either uv didn't install or your terminal still has the old PATH.

First try: close all terminal windows and open a fresh one. Then run `uv --version`.

If that still fails, reinstall uv:

    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

On macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`

After installing, close and reopen the terminal. Run `Get-Command uv` (Windows) or `which uv` (Mac/Linux) to confirm it's found.

---

## `uv sync` fails

Three most common causes:

**Wrong directory.** You must be inside the `src/` folder when you run `uv sync`, not the root of the repo. Check that your terminal prompt ends with `\src>`. If it doesn't, navigate there first.

**No internet connection.** uv downloads packages from the internet. Check your connection and try again.

**Python version too old.** This toolkit requires Python 3.11 or newer. Run `python --version` and check the number. If it's 3.10 or earlier, install a newer version from [python.org](https://www.python.org/downloads/).

---

## Overpass timeout / "Gateway Timeout" / "504"

The Overpass API is a public service and sometimes struggles with large requests.

**Bbox too large.** Try a smaller bounding box — just the core urban area rather than the whole metro region. A smaller bbox means fewer features to download and is less likely to time out. You can always run a second extract for surrounding areas.

**All endpoints are down.** Rare but happens. The toolkit rotates between three public Overpass endpoints automatically. If they're all struggling, wait 5 minutes and try again. You can check server status at [status.openstreetmap.org](https://status.openstreetmap.org/).

---

## Empty output or very few features

The extraction ran without errors but your visualizer looks mostly empty.

This usually means your city has sparse OSM data. OSM is a volunteer-built map — coverage varies a lot by region. Some cities have extremely detailed building and land use data; others have barely the roads.

Check your city's OSM coverage at [osmstats.neis-one.org](https://osmstats.neis-one.org/). If the contributor and edit counts are low, that's why.

The best long-term fix is to contribute to OSM for your area — add building footprints, building levels, land use polygons. The OSM wiki has guides for getting started. After contributing, re-run the extractor.

Also check: is your bbox correct? Confirm at [bboxfinder.com](http://bboxfinder.com/) that it actually covers your city. A common mistake is swapping north/south or east/west.

---

## Visualizer shows a blank black page

Open browser developer tools (press **F12**), click the **Console** tab, and look for red error messages.

**Most common cause: .js files are in the wrong place.** The three data files (`datos_zonificacion.js`, `datos_vial.js`, `datos_servicios.js`) must be in the `visualizer/` folder, same folder as `index.html`. If they're in `src/` or anywhere else, the visualizer can't find them.

**Browser cache showing old version.** Press **Ctrl+Shift+R** (Windows) or **Cmd+Shift+R** (Mac) to force a full reload.

**File wasn't generated.** Check that the extraction commands completed without errors. If a command failed partway through, the .js file might not exist or might be empty.

---

## "Module not found: services" or similar import errors

You ran an extract command without running `uv sync` first, or you ran it from the wrong directory.

Make sure you're inside `src/` and run `uv sync` before any extract commands. After that, the module imports will work.

---

## Markers don't appear at low zoom levels

That's intentional. Services markers (the H/E/B/A/P circles) are hidden at zoom level 11 and below for performance — 2000+ markers at city scale would be visually noisy and slow. Zoom in past level 12 and they'll appear.

Polygon features (hospital campuses, parks, university grounds) are always visible regardless of zoom.

---

## Colors are hard to tell apart

Known limitation. The color palette is designed to match the in-game CS2 zone HUD, which uses several similar shades of green for residential subtypes (Low Density, Medium Density, Mixed Housing, Row Housing). They're distinct in the legend but can look similar on the map at medium zoom.

Zooming in helps. The legend on the left side shows the exact color for each zone type — use it as reference.

This is on the list for future improvement.

---

## Still stuck?

Open an issue at [github.com/Osyanne/cs2-minneapolis-osm-toolkit/issues](https://github.com/Osyanne/cs2-minneapolis-osm-toolkit/issues).

Include: what step you were on, the exact error message (copy-paste it, don't screenshot if you can help it), your OS and Python version, and your bbox if relevant. The more detail, the faster it gets resolved.
