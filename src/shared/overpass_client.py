"""
overpass_client.py
==================
Cliente HTTP para la Overpass API con retry exponencial y rotación de endpoints.

Uso:
    from overpass_client import query_with_retry
    data = query_with_retry(overpass_ql_string, label="residential")
    # data es un dict JSON con la clave 'elements'

Diseño:
- 3 endpoints públicos (overpass-api.de, kumi.systems, mail.ru)
- Cada query: prueba endpoints en orden hasta que uno responda
- Retry con backoff exponencial (5s, 15s, 30s) si TODOS los endpoints fallan
- Timeout de request HTTP a 240s (las queries pesadas tardan 90-180s)
"""

from __future__ import annotations

import time
from typing import Any

import requests


ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

# Backoff entre rounds completos (cuando los 3 endpoints fallaron)
RETRY_DELAYS_S = [5, 15, 30]
HTTP_TIMEOUT_S = 240


class OverpassError(RuntimeError):
    """Una query Overpass falló tras agotar reintentos."""


def _try_endpoint(endpoint: str, query: str, label: str) -> dict[str, Any]:
    """Intenta una sola query contra un endpoint. Lanza excepción si falla."""
    response = requests.post(
        endpoint,
        data={"data": query},
        timeout=HTTP_TIMEOUT_S,
        headers={"User-Agent": "cs2-minneapolis-zoning/2.0 (educational use)"},
    )
    response.raise_for_status()
    payload = response.json()
    if "elements" not in payload:
        raise ValueError(f"respuesta sin 'elements' (¿error de query?): {payload!r}")
    return payload


def query_with_retry(query: str, label: str = "query") -> dict[str, Any]:
    """
    Ejecuta una query Overpass QL con retry y rotación de endpoints.

    Args:
        query: Cadena Overpass QL (incluye [out:json][timeout:N]; ... ;out geom;).
        label: Etiqueta legible para logs (ej. 'residential').

    Returns:
        El JSON parseado de la respuesta (dict con clave 'elements').

    Raises:
        OverpassError: si todos los endpoints fallaron en todos los reintentos.
    """
    last_errors: list[str] = []

    for round_idx in range(len(RETRY_DELAYS_S) + 1):
        for endpoint in ENDPOINTS:
            short_name = endpoint.replace("https://", "").split("/")[0]
            try:
                print(f"        [{label}] -> {short_name} (round {round_idx + 1})", flush=True)
                start = time.monotonic()
                data = _try_endpoint(endpoint, query, label)
                elapsed = time.monotonic() - start
                count = len(data.get("elements", []))
                print(f"        [{label}] OK {short_name} ({count} elementos en {elapsed:.1f}s)",
                      flush=True)
                return data
            except (requests.RequestException, ValueError) as e:
                msg = f"{short_name}: {type(e).__name__}: {e}"
                last_errors.append(msg)
                print(f"        [{label}] FAIL {msg}", flush=True)

        # Todos los endpoints fallaron en esta ronda. Backoff antes de reintentar.
        if round_idx < len(RETRY_DELAYS_S):
            delay = RETRY_DELAYS_S[round_idx]
            print(f"        [{label}] todos los endpoints fallaron — esperando {delay}s antes de reintentar",
                  flush=True)
            time.sleep(delay)

    raise OverpassError(
        f"[{label}] tras {len(RETRY_DELAYS_S) + 1} rondas, todos los endpoints fallaron:\n  "
        + "\n  ".join(last_errors[-6:])  # últimos 6 errores para no saturar
    )
