"""
services/classifiers.py — Clasificación de tags OSM → categoría CS2 (Sesión 3)
==============================================================================
Mapeo tabla → categoría. Sin heurísticas. El tag amenity/leisure/landuse/
office/tourism es suficiente para decidir.

Reglas especiales:
- landuse=cemetery solo cuenta si element_type=='way'
- Subtypes culturales en admin (library, theatre, museum, cinema, arts_centre)
  requieren tag name=*
"""

# Single source of truth — mapeo (key, value) → categoría
TAG_TO_CATEGORY = {
    # health (sanitaria + funeraria)
    ("amenity", "hospital"):           "health",
    ("amenity", "clinic"):             "health",
    ("amenity", "doctors"):            "health",
    ("amenity", "funeral_directors"):  "health",
    ("amenity", "crematorium"):        "health",
    ("landuse", "cemetery"):           "health",   # solo ways
    # education + research
    ("amenity", "school"):             "education",
    ("amenity", "university"):         "education",
    ("amenity", "college"):            "education",
    ("amenity", "kindergarten"):       "education",
    ("amenity", "research_institute"): "education",
    ("office",  "research"):           "education",
    # fire
    ("amenity", "fire_station"):       "fire",
    # admin (incluye landmarks culturales)
    ("amenity", "police"):             "admin",
    ("amenity", "townhall"):           "admin",
    ("amenity", "courthouse"):         "admin",
    ("amenity", "prison"):             "admin",
    ("amenity", "library"):            "admin",
    ("amenity", "theatre"):            "admin",
    ("amenity", "arts_centre"):        "admin",
    ("amenity", "cinema"):             "admin",
    ("office",  "government"):         "admin",
    ("tourism", "museum"):             "admin",
    # parks
    ("leisure", "park"):               "parks",
    ("leisure", "nature_reserve"):     "parks",
    ("leisure", "garden"):             "parks",
    ("leisure", "playground"):         "parks",
    ("leisure", "sports_centre"):      "parks",
}

# Subtypes que requieren name=* (solo culturales en admin)
NAME_REQUIRED_SUBTYPES = {
    ("amenity", "library"),
    ("amenity", "theatre"),
    ("amenity", "arts_centre"),
    ("amenity", "cinema"),
    ("tourism", "museum"),
}


def classify_service(tags: dict, element_type: str) -> str | None:
    """
    Devuelve la categoría ('health'|'education'|'fire'|'admin'|'parks') o
    None si los tags no clasifican.

    Reglas:
    - Itera los tags y devuelve la PRIMERA categoría matched (determinístico
      por orden de iteración de dict en Python 3.7+).
    - landuse=cemetery solo cuenta si element_type=='way' (cementerios sin
      polígono no aportan).
    - Subtypes culturales (library, theatre, museum, cinema, arts_centre)
      requieren tag name=*.
    """
    for key, value in tags.items():
        cat = TAG_TO_CATEGORY.get((key, value))
        if cat is None:
            continue
        # cementerios solo ways
        if (key, value) == ("landuse", "cemetery") and element_type == "node":
            return None
        # culturales requieren name
        if (key, value) in NAME_REQUIRED_SUBTYPES and not tags.get("name"):
            return None
        return cat
    return None


def infer_geometry_kind(element: dict) -> str:
    """
    Devuelve 'polygon' si el way está cerrado (>=4 nodos, primer==último),
    sino 'point'. Nodes siempre son 'point'. Ways sin geometría también 'point'.
    """
    if element["type"] != "way":
        return "point"
    geom = element.get("geometry", [])
    if len(geom) < 4:
        return "point"
    first, last = geom[0], geom[-1]
    if first["lat"] == last["lat"] and first["lon"] == last["lon"]:
        return "polygon"
    return "point"
