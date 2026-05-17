"""Tests del módulo services.classifiers (Sesión 3)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))


# ── classify_service ────────────────────────────────────────────────────────

def test_hospital_classifies_to_health():
    from services.classifiers import classify_service
    assert classify_service({"amenity": "hospital"}, "way") == "health"


def test_clinic_classifies_to_health():
    from services.classifiers import classify_service
    assert classify_service({"amenity": "clinic"}, "node") == "health"


def test_funeral_directors_classifies_to_health():
    from services.classifiers import classify_service
    assert classify_service({"amenity": "funeral_directors"}, "way") == "health"


def test_cemetery_way_is_health():
    from services.classifiers import classify_service
    assert classify_service({"landuse": "cemetery"}, "way") == "health"


def test_cemetery_node_is_rejected():
    from services.classifiers import classify_service
    assert classify_service({"landuse": "cemetery"}, "node") is None


def test_school_classifies_to_education():
    from services.classifiers import classify_service
    assert classify_service({"amenity": "school"}, "way") == "education"


def test_university_classifies_to_education():
    from services.classifiers import classify_service
    assert classify_service({"amenity": "university"}, "way") == "education"


def test_kindergarten_classifies_to_education():
    from services.classifiers import classify_service
    assert classify_service({"amenity": "kindergarten"}, "node") == "education"


def test_office_research_is_education():
    from services.classifiers import classify_service
    assert classify_service({"office": "research"}, "way") == "education"


def test_school_without_name_still_classified():
    """name=* NO requerido para schools (solo para culturales en admin)."""
    from services.classifiers import classify_service
    assert classify_service({"amenity": "school"}, "way") == "education"


def test_fire_station_classifies_to_fire():
    from services.classifiers import classify_service
    assert classify_service({"amenity": "fire_station"}, "way") == "fire"


def test_police_classifies_to_admin():
    from services.classifiers import classify_service
    assert classify_service({"amenity": "police"}, "way") == "admin"


def test_townhall_classifies_to_admin():
    from services.classifiers import classify_service
    assert classify_service({"amenity": "townhall"}, "way") == "admin"


def test_prison_classifies_to_admin():
    from services.classifiers import classify_service
    assert classify_service({"amenity": "prison"}, "way") == "admin"


def test_office_government_is_admin():
    from services.classifiers import classify_service
    assert classify_service({"office": "government"}, "way") == "admin"


def test_library_with_name_is_admin():
    from services.classifiers import classify_service
    assert classify_service({"amenity": "library", "name": "Hennepin Library"}, "way") == "admin"


def test_library_without_name_rejected():
    from services.classifiers import classify_service
    assert classify_service({"amenity": "library"}, "way") is None


def test_museum_with_name_is_admin():
    from services.classifiers import classify_service
    assert classify_service({"tourism": "museum", "name": "Walker Art Center"}, "way") == "admin"


def test_museum_without_name_rejected():
    from services.classifiers import classify_service
    assert classify_service({"tourism": "museum"}, "way") is None


def test_theatre_with_name_is_admin():
    from services.classifiers import classify_service
    assert classify_service({"amenity": "theatre", "name": "Guthrie"}, "way") == "admin"


def test_theatre_without_name_rejected():
    from services.classifiers import classify_service
    assert classify_service({"amenity": "theatre"}, "way") is None


def test_arts_centre_without_name_rejected():
    from services.classifiers import classify_service
    assert classify_service({"amenity": "arts_centre"}, "way") is None


def test_cinema_with_name_is_admin():
    from services.classifiers import classify_service
    assert classify_service({"amenity": "cinema", "name": "Uptown Theatre"}, "way") == "admin"


def test_park_classifies_to_parks():
    from services.classifiers import classify_service
    assert classify_service({"leisure": "park"}, "way") == "parks"


def test_playground_classifies_to_parks():
    from services.classifiers import classify_service
    assert classify_service({"leisure": "playground"}, "node") == "parks"


def test_sports_centre_classifies_to_parks():
    from services.classifiers import classify_service
    assert classify_service({"leisure": "sports_centre"}, "way") == "parks"


def test_garden_classifies_to_parks():
    from services.classifiers import classify_service
    assert classify_service({"leisure": "garden"}, "way") == "parks"


def test_nature_reserve_classifies_to_parks():
    from services.classifiers import classify_service
    assert classify_service({"leisure": "nature_reserve"}, "way") == "parks"


def test_irrelevant_amenity_is_none():
    from services.classifiers import classify_service
    assert classify_service({"amenity": "restaurant"}, "way") is None


def test_no_relevant_tag_is_none():
    from services.classifiers import classify_service
    assert classify_service({"building": "yes"}, "way") is None


def test_empty_tags_is_none():
    from services.classifiers import classify_service
    assert classify_service({}, "node") is None


# ── infer_geometry_kind ─────────────────────────────────────────────────────

def test_node_is_point():
    from services.classifiers import infer_geometry_kind
    assert infer_geometry_kind({"type": "node"}) == "point"


def test_closed_way_is_polygon():
    from services.classifiers import infer_geometry_kind
    el = {"type": "way", "geometry": [
        {"lat": 1.0, "lon": 1.0},
        {"lat": 1.0, "lon": 2.0},
        {"lat": 2.0, "lon": 2.0},
        {"lat": 1.0, "lon": 1.0},
    ]}
    assert infer_geometry_kind(el) == "polygon"


def test_open_way_is_point():
    from services.classifiers import infer_geometry_kind
    el = {"type": "way", "geometry": [
        {"lat": 1.0, "lon": 1.0},
        {"lat": 1.0, "lon": 2.0},
        {"lat": 2.0, "lon": 2.0},
    ]}
    assert infer_geometry_kind(el) == "point"


def test_short_way_is_point():
    from services.classifiers import infer_geometry_kind
    el = {"type": "way", "geometry": [
        {"lat": 1.0, "lon": 1.0},
        {"lat": 1.0, "lon": 2.0},
    ]}
    assert infer_geometry_kind(el) == "point"


def test_way_without_geometry_is_point():
    from services.classifiers import infer_geometry_kind
    el = {"type": "way"}
    assert infer_geometry_kind(el) == "point"
