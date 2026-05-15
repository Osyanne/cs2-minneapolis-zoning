"""
take_screenshots.py — Generate fresh screenshots of the visualizer for the README.

Uses Playwright (headless Chromium) to load the visualizer and capture the map
at multiple zoom levels. Assumes the python http.server is running on :8080.

Usage:
    # In one terminal:
    cd ../visualizer && python -m http.server 8080

    # In another:
    cd src && uv run --with playwright take_screenshots.py
    # First time: also run `uv run --with playwright playwright install chromium`
"""

import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT_DIR = Path(__file__).parent.parent / "docs" / "screenshots"
URL = "http://localhost:8080"
VIEWPORT = {"width": 1600, "height": 900}


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport=VIEWPORT)
        page = ctx.new_page()

        print(f"Loading {URL} ...")
        page.goto(URL, wait_until="domcontentloaded", timeout=30_000)
        # Wait for prebuilt data + initial render
        page.wait_for_function(
            "() => typeof DATA_RES_LOW_HOUSE !== 'undefined' && document.getElementById('loading').style.display === 'none'",
            timeout=60_000
        )
        print("  OKVisualizer loaded")

        shots = [
            # (name, [lat, lon], zoom, settle_ms)
            ("preview_full",     [44.97, -93.27], 12, 4000),
            ("preview_downtown", [44.978, -93.265], 15, 4000),
            ("preview_uptown",   [44.948, -93.295], 15, 4000),
        ]

        for name, center, zoom, settle in shots:
            print(f"Capturing {name} (center={center}, zoom={zoom}) ...")
            page.evaluate(f"map.setView({center}, {zoom})")
            page.wait_for_timeout(settle)
            # Mover el cursor fuera del mapa para que no aparezca en la captura
            page.mouse.move(1, 1)
            out_path = OUT_DIR / f"{name}.png"
            page.screenshot(path=str(out_path), type="png", full_page=False)
            size_kb = out_path.stat().st_size // 1024
            print(f"  OKSaved {out_path.name} ({size_kb} KB)")

        browser.close()

    print(f"\nDone. {len(shots)} screenshots in {OUT_DIR}")


if __name__ == "__main__":
    sys.exit(main() or 0)
