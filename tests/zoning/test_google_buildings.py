"""
Tests para extract_google_buildings.py — Google Open Buildings augmentation.

Solo testea las funciones puras (sin red, sin filesystem heavy). El pipeline
end-to-end requiere download de 200+ MB, así que ese path se valida manualmente.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import pytest
from shapely.geometry import Polygon
from shapely.strtree import STRtree

from zoning.extract_google_buildings import (
    s2_cells_for_bbox,
    classify_building,
)


# ══════════════════════════════════════════════════════════════════════════════
# s2_cells_for_bbox — lookup de S2 L6 token por bbox
# ══════════════════════════════════════════════════════════════════════════════

def test_s2_cells_for_mafra_returns_94dd():
    """Mafra, SC (bbox típico de 8.7×8.5 km) cae dentro de un solo S2 L6 cell."""
    bbox = [-26.1658, -49.8643, -26.0879, -49.77]
    cells = s2_cells_for_bbox(bbox)
    assert "94dd" in cells, f"Esperaba '94dd' para Mafra, got {cells}"
    # bbox pequeño debería caer en 1 cell (todos los corners + centroide en el mismo)
    assert len(cells) == 1, f"Esperaba 1 cell para bbox pequeño, got {len(cells)}"


def test_s2_cells_returns_sorted_list():
    """Output siempre ordenado para reproducibilidad."""
    bbox = [-26.1658, -49.8643, -26.0879, -49.77]
    cells = s2_cells_for_bbox(bbox)
    assert cells == sorted(cells)


def test_s2_cells_for_trondheim():
    """Trondheim (Noruega, lat 63) usa cells diferentes — sanity check."""
    bbox = [63.333645, 10.206814, 63.466541, 10.578632]
    cells = s2_cells_for_bbox(bbox)
    assert len(cells) >= 1
    # Trondheim NO debería estar en el mismo cell que Mafra
    assert "94dd" not in cells


# ══════════════════════════════════════════════════════════════════════════════
# classify_building — algoritmo idéntico a v3.3.4 (spatial join + área)
# ══════════════════════════════════════════════════════════════════════════════

def _square_polygon(center_lon, center_lat, side_m=20):
    """Helper: construye un polígono cuadrado (lon, lat) de side_m metros."""
    # 1 grado lat ≈ 111 km; 1 grado lon ≈ 111 km * cos(lat)
    import math
    delta_lat = side_m / 111_320.0
    delta_lon = side_m / (111_320.0 * math.cos(math.radians(center_lat)))
    return Polygon([
        (center_lon - delta_lon/2, center_lat - delta_lat/2),
        (center_lon + delta_lon/2, center_lat - delta_lat/2),
        (center_lon + delta_lon/2, center_lat + delta_lat/2),
        (center_lon - delta_lon/2, center_lat + delta_lat/2),
    ])


def test_classify_falls_back_to_area_without_tree():
    """Sin landuse tree, classify usa heurística de área."""
    poly = _square_polygon(-49.81, -26.13, side_m=10)  # ~100 m² → low_house
    key, method = classify_building(poly, area_m2=100, tree=None,
                                     landuse_geoms=[], landuse_keys=[])
    assert key == "res_low_house"
    assert method == "area"


def test_classify_industrial_via_area():
    """Buildings grandes (≥1500 m²) sin landuse → industrial."""
    poly = _square_polygon(-49.81, -26.13, side_m=50)
    key, method = classify_building(poly, area_m2=2500, tree=None,
                                     landuse_geoms=[], landuse_keys=[])
    assert key == "industrial"
    assert method == "area"


def test_classify_uses_landuse_when_centroid_inside():
    """Si el centroide cae dentro de un landuse polygon, gana ese (no el área)."""
    # Landuse=industrial cubriendo (-26.13, -49.81)
    industrial_zone = Polygon([
        (-49.82, -26.14), (-49.80, -26.14),
        (-49.80, -26.12), (-49.82, -26.12),
    ])
    landuse_geoms = [industrial_zone]
    landuse_keys = ["industrial"]
    tree = STRtree(landuse_geoms)

    # Building pequeño (≈100 m²) que por heurística sería res_low_house,
    # pero está DENTRO de un landuse=industrial → debe ser industrial.
    poly = _square_polygon(-49.81, -26.13, side_m=10)
    key, method = classify_building(poly, area_m2=100, tree=tree,
                                     landuse_geoms=landuse_geoms,
                                     landuse_keys=landuse_keys)
    assert key == "industrial"
    assert method == "landuse"


def test_classify_falls_back_when_centroid_outside_landuse():
    """Si el centroide cae fuera del landuse, usa heurística de área."""
    # Landuse=residential lejos del building
    far_zone = Polygon([
        (-49.95, -26.05), (-49.90, -26.05),
        (-49.90, -26.00), (-49.95, -26.00),
    ])
    landuse_geoms = [far_zone]
    landuse_keys = ["res_low_house"]
    tree = STRtree(landuse_geoms)

    poly = _square_polygon(-49.81, -26.13, side_m=10)
    key, method = classify_building(poly, area_m2=100, tree=tree,
                                     landuse_geoms=landuse_geoms,
                                     landuse_keys=landuse_keys)
    # Heurística por área → res_low_house (porque área < 300 m²)
    assert key == "res_low_house"
    assert method == "area"
