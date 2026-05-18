# GitHub Publishing Instructions

Steps to publish `cs2-minneapolis-zoning` to GitHub as a public repo.

---

## Step 1 — Create the repository on GitHub

1. Go to **https://github.com/new**
2. Fill in:
   - **Repository name:** `cs2-minneapolis-zoning`
   - **Description:** `GIS pipeline to extract real-world zoning data from OpenStreetMap for Cities Skylines 2`
   - **Visibility:** ✅ Public
   - **Initialize repository:** Leave all checkboxes UNCHECKED (we'll push existing files)
3. Click **Create repository**

---

## Step 2 — Initialize git and push

Run these commands from the `cs2-minneapolis-zoning/` folder:

```bash
# Navigate to the repo folder
cd "C:\Users\osyanne\Documents\Claude\Projects\Urban Planning Minneapolis Realism\cs2-minneapolis-zoning"

# Initialize git
git init

# Stage all files
git add .

# Verify what's being committed (check .gitignore is excluding the right things)
git status

# Create the initial commit
git commit -m "feat: initial release v1.0 — Minneapolis zoning pipeline

- Python extraction script with multi-endpoint retry logic
- Interactive Leaflet.js visualizer (CartoDB Dark Matter)
- Full methodology documentation (METHODOLOGY.md)
- CS2 zone type reference guide (docs/cs2-zone-reference.md)
- Adapting to other cities guide (docs/adapting-to-other-cities.md)
- bbox-mcp-server optional dependency guide

Coverage: Full Minneapolis bbox (44.86,-93.38,45.05,-93.17)
Data source: OpenStreetMap via Overpass API"

# Point to GitHub remote
git branch -M main
git remote add origin https://github.com/Osyanne/cs2-osm-toolkit.git

# Push
git push -u origin main
```

---

## Step 3 — Configure the repository on GitHub

After pushing, go to your repo settings and configure:

**Topics/Tags** (Settings → Topics):
```
cities-skylines-2  gis  openstreetmap  overpass-api  leaflet
urban-planning  open-source  python  minneapolis
```

**About section** (click the gear icon on the repo homepage):
- Description: `GIS pipeline to extract real-world zoning data from OpenStreetMap for Cities Skylines 2`
- Website: *(leave blank for now, or add GitHub Pages URL if you set it up)*

---

## Step 4 — Verify before posting to Reddit

Check these items before posting:

- [ ] `README.md` renders correctly on GitHub (images show, tables format correctly)
- [ ] `src/` files are present and complete
- [ ] `visualizer/datos_zonificacion.js` is the PLACEHOLDER (empty arrays), NOT the 5.4 MB real file
- [ ] `data/sample_output.js` exists with real data subset (~42 KB)
- [ ] `docs/screenshots/` contains all 3 PNG files
- [ ] `LICENSE` shows "Copyright (c) 2026 Osyanne"
- [ ] `.gitignore` is present (check it excluded `.venv/`, `__pycache__/`, etc.)

---

## Optional: GitHub Pages for the visualizer

To host the visualizer as a live demo:

1. Go to repo **Settings → Pages**
2. Source: **Deploy from a branch**
3. Branch: `main`, Folder: `/visualizer`
4. Save

The live map will be at: `https://osyanne.github.io/cs2-osm-toolkit/`

Note: The live demo will show an empty map until visitors run `extract_zoning.py` themselves (the data file is excluded from git). You can add a note about this in the visualizer or show `sample_output.js` as the default.

---

## File size verification

Before pushing, verify no large files are included:

```bash
# Check file sizes in the repo (should all be small)
find . -not -path './.git/*' -type f | xargs ls -lh | sort -k5 -rh | head -20
```

The largest file should be `data/sample_output.js` at ~42 KB. If you see anything over 1 MB, double-check your `.gitignore`.
