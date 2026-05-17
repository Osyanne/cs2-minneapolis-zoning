# Quick Start — Using This Toolkit for Your City

By the end of this guide you'll have an interactive dark-mode map of your city showing zoning, roads, and points of interest — all sourced from real OpenStreetMap data, ready to use as a reference layer while building in Cities: Skylines 2. The whole process takes about 15–20 minutes.

If something breaks along the way, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

---

## Step 1: Install Python

Go to [python.org/downloads](https://www.python.org/downloads/) and download the latest Python 3.11 or newer installer for Windows.

Run the installer. **Before clicking Install Now, check the box that says "Add Python to PATH".** This is easy to miss and if you skip it, nothing else in this guide will work. You'd have to reinstall.

On **macOS**: Python 3.11+ usually comes via [Homebrew](https://brew.sh/) — `brew install python@3.11`. On **Linux**: use your distro's package manager (`apt install python3.11` or equivalent).

Once installed, open a new terminal and type `python --version`. You should see something like `Python 3.11.x`. If you get an error, the PATH wasn't set — go back and reinstall with the checkbox.

*Time: 3–5 min*

---

## Step 2: Install uv

uv is a fast Python package manager. You only install it once, globally.

Open PowerShell (search "PowerShell" in the Start menu) and paste:

    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

Close and reopen PowerShell after it finishes so the PATH changes take effect. Then verify: `uv --version`.

On **macOS/Linux**:

    curl -LsSf https://astral.sh/uv/install.sh | sh

*Time: 1 min*

---

## Step 3: Download the Repo

Go to [github.com/Osyanne/cs2-minneapolis-osm-toolkit](https://github.com/Osyanne/cs2-minneapolis-osm-toolkit), click the green **Code** button, then **Download ZIP**.

Unzip it somewhere easy to find — your Desktop or Documents folder works fine. You should end up with a folder called something like `cs2-minneapolis-osm-toolkit-main`.

*Time: 1 min*

---

## Step 4: Find Your City's Bounding Box

The extractors need four coordinates that draw a rectangle around your city: south, west, north, east (in that order).

The easiest way: go to [bboxfinder.com](http://bboxfinder.com/), zoom to your city, and draw a rectangle around the area you want. The coordinates appear at the bottom of the page. Copy them — you'll use them in Step 7.

For a more detailed explanation of all the ways to find a bbox (including an AI-assisted method), see [adapting-to-other-cities.md](adapting-to-other-cities.md).

*Time: 2–3 min*

---

## Step 5: Open a Terminal Inside the src/ Folder

Navigate to the folder you unzipped, then into the `src` subfolder.

Hold **Shift** and **right-click** on the `src` folder. Choose "Open in Terminal" or "Open PowerShell window here". (In Windows 11, you might need to click "Show more options" to see it.)

You should see the terminal path end in `...\src>`.

*Time: 1 min*

---

## Step 6: Install Dependencies

In that terminal, run:

    uv sync

This downloads and installs everything the toolkit needs. It only does the heavy work the first time — subsequent runs are instant. Wait until you see the terminal prompt return.

If it fails, make sure you're inside the `src` folder (not the root of the repo). See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) if you're stuck.

*Time: 1–2 min*

---

## Step 7: Generate Data for Your City

Now run these three commands, one at a time. Replace `south,west,north,east` with the coordinates you found in Step 4.

    uv run extract-zoning --bbox "south,west,north,east"

    uv run extract-vial --bbox "south,west,north,east"

    uv run extract-services --bbox "south,west,north,east"

For example, for Madison, WI:

    uv run extract-zoning --bbox "43.05,-89.50,43.15,-89.30"
    uv run extract-vial --bbox "43.05,-89.50,43.15,-89.30"
    uv run extract-services --bbox "43.05,-89.50,43.15,-89.30"

Each command contacts the OpenStreetMap Overpass API, downloads data, classifies it, and writes a `.js` file into the `visualizer/` folder. The zoning extractor takes the longest — 1–5 minutes depending on city size and Overpass server load. The other two are usually under a minute.

You'll see progress lines in the terminal. When a command finishes you get your prompt back.

Note: this toolkit uses OSM land use tags to approximate zoning, not actual municipal zoning data. OSM coverage varies — some cities have very detailed building data, others don't. If your output looks sparse, see the OSM coverage section in [adapting-to-other-cities.md](adapting-to-other-cities.md).

*Time: 3–8 min total*

---

## Step 8: Open the Visualizer

Go to the `visualizer/` folder in your file explorer and double-click `index.html`. It opens in your browser.

The map will center on your city's data automatically. Use the layer controls on the right to toggle zoning, roads, and services on and off. Click any polygon or marker for details.

That's it.

*Time: 30 seconds*

---

## If Something Breaks

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for fixes for the most common errors, including Python not found, uv not found, Overpass timeouts, and blank visualizer pages.

If your issue isn't listed there, open a GitHub Issue at [github.com/Osyanne/cs2-minneapolis-osm-toolkit/issues](https://github.com/Osyanne/cs2-minneapolis-osm-toolkit/issues) — include the error message and what step you were on.
