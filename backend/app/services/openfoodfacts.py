"""Client for the public OpenFoodFacts API.

Two endpoints are used:

* ``GET /api/v2/search``            — free-text product search
* ``GET /api/v2/product/{barcode}`` — single product lookup

If the v2 search endpoint is unavailable the legacy ``/cgi/search.pl``
endpoint is used as a fallback. Every response is normalised into
:class:`~app.schemas.FoodSearchResult` with macros expressed **per 100 g**,
which is the unit OpenFoodFacts stores them in.

Upstream payloads are treated as untrusted: any field may be missing, ``null``,
or a string where a number is expected, so every value goes through
:func:`_to_float`.
"""

from __future__ import annotations

import logging
import re
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.config import settings
from app.schemas import FoodSearchResult

logger = logging.getLogger(__name__)

# Fields requested from the API — keeps payloads small and predictable.
_FIELDS = ",".join(
    [
        "code",
        "product_name",
        "product_name_en",
        "generic_name",
        "brands",
        "image_front_small_url",
        "image_url",
        "serving_size",
        "serving_quantity",
        "nutriments",
    ]
)

KJ_PER_KCAL = 4.184
_NUMBER_RE = re.compile(r"[-+]?\d*\.?\d+")


def _to_float(value: Any, default: float = 0.0) -> float:
    """Coerce an arbitrary upstream value to a non-negative float."""
    if isinstance(value, bool) or value is None:
        return default
    if isinstance(value, (int, float)):
        result = float(value)
    elif isinstance(value, str):
        match = _NUMBER_RE.search(value)
        if not match:
            return default
        try:
            result = float(match.group())
        except ValueError:
            return default
    else:
        return default
    if result != result or result in (float("inf"), float("-inf")):  # NaN / inf
        return default
    return max(result, 0.0)


def _calories_per_100g(nutriments: dict[str, Any]) -> float:
    """kcal per 100 g, converting from kJ when kcal is not provided."""
    for key in ("energy-kcal_100g", "energy-kcal_value", "energy-kcal"):
        if key in nutriments:
            kcal = _to_float(nutriments[key])
            if kcal:
                return round(kcal, 2)
    for key in ("energy_100g", "energy-kj_100g", "energy"):
        if key in nutriments:
            kj = _to_float(nutriments[key])
            if kj:
                return round(kj / KJ_PER_KCAL, 2)
    return 0.0


def _serving_size_g(product: dict[str, Any]) -> float | None:
    """Serving size in grams, if OpenFoodFacts provides a usable one."""
    quantity = _to_float(product.get("serving_quantity"))
    if quantity > 0:
        return round(quantity, 2)
    raw = product.get("serving_size")
    if isinstance(raw, str):
        parsed = _to_float(raw)
        if parsed > 0:
            return round(parsed, 2)
    return None


def _display_name(product: dict[str, Any]) -> str:
    for key in ("product_name", "product_name_en", "generic_name"):
        value = product.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()[:255]
    return ""


def normalize_product(product: dict[str, Any]) -> FoodSearchResult | None:
    """Map one raw OpenFoodFacts product onto a ``FoodSearchResult``.

    Returns ``None`` for products that are unusable — no name, or no macro
    data at all — so they never reach the client.
    """
    if not isinstance(product, dict):
        return None

    name = _display_name(product)
    if not name:
        return None

    nutriments = product.get("nutriments")
    if not isinstance(nutriments, dict):
        nutriments = {}

    calories = _calories_per_100g(nutriments)
    protein = round(_to_float(nutriments.get("proteins_100g")), 2)
    carbs = round(_to_float(nutriments.get("carbohydrates_100g")), 2)
    fats = round(_to_float(nutriments.get("fat_100g")), 2)
    fiber = round(_to_float(nutriments.get("fiber_100g")), 2)

    if not any((calories, protein, carbs, fats, fiber)):
        return None

    brands = product.get("brands")
    barcode = product.get("code")

    return FoodSearchResult(
        barcode=str(barcode)[:64] if barcode else None,
        name=name,
        brand=brands.strip()[:255] if isinstance(brands, str) and brands.strip() else None,
        image_url=product.get("image_front_small_url") or product.get("image_url") or None,
        serving_size_g=_serving_size_g(product),
        calories_per_100g=calories,
        protein_per_100g=protein,
        carbs_per_100g=carbs,
        fats_per_100g=fats,
        fiber_per_100g=fiber,
    )


def _headers() -> dict[str, str]:
    # OpenFoodFacts asks every client to identify itself with a User-Agent.
    return {"User-Agent": settings.openfoodfacts_user_agent, "Accept": "application/json"}


async def _get_json(client: httpx.AsyncClient, url: str, params: dict[str, Any]) -> dict[str, Any]:
    response = await client.get(url, params=params, headers=_headers())
    response.raise_for_status()
    payload = response.json()
    return payload if isinstance(payload, dict) else {}


async def search_foods(query: str, page_size: int = 20) -> list[FoodSearchResult]:
    """Search OpenFoodFacts for ``query`` and return normalised results."""
    query = query.strip()
    if not query:
        return []

    base = settings.openfoodfacts_base_url.rstrip("/")
    timeout = httpx.Timeout(settings.openfoodfacts_timeout_seconds)

    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            try:
                payload = await _get_json(
                    client,
                    f"{base}/api/v2/search",
                    {"search_terms": query, "fields": _FIELDS, "page_size": page_size, "json": 1},
                )
            except httpx.HTTPStatusError:
                # Older/regional deployments only expose the legacy endpoint.
                payload = await _get_json(
                    client,
                    f"{base}/cgi/search.pl",
                    {
                        "search_terms": query,
                        "search_simple": 1,
                        "action": "process",
                        "json": 1,
                        "page_size": page_size,
                        "fields": _FIELDS,
                    },
                )
    except httpx.HTTPError as exc:
        logger.warning("OpenFoodFacts search failed for %r: %s", query, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The OpenFoodFacts service is currently unavailable. Please try again.",
        ) from exc
    except ValueError as exc:  # malformed JSON
        logger.warning("OpenFoodFacts returned invalid JSON for %r: %s", query, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Received an unreadable response from OpenFoodFacts.",
        ) from exc

    raw_products = payload.get("products")
    if not isinstance(raw_products, list):
        return []

    results: list[FoodSearchResult] = []
    for raw in raw_products[:page_size]:
        normalized = normalize_product(raw)
        if normalized is not None:
            results.append(normalized)
    return results


async def get_food_by_barcode(barcode: str) -> FoodSearchResult | None:
    """Look up a single product by barcode; ``None`` when not found."""
    barcode = barcode.strip()
    if not barcode.isdigit():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Barcode must be numeric.")

    base = settings.openfoodfacts_base_url.rstrip("/")
    timeout = httpx.Timeout(settings.openfoodfacts_timeout_seconds)

    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            payload = await _get_json(
                client, f"{base}/api/v2/product/{barcode}", {"fields": _FIELDS}
            )
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return None
        logger.warning("OpenFoodFacts barcode lookup failed for %s: %s", barcode, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The OpenFoodFacts service is currently unavailable. Please try again.",
        ) from exc
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("OpenFoodFacts barcode lookup failed for %s: %s", barcode, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The OpenFoodFacts service is currently unavailable. Please try again.",
        ) from exc

    product = payload.get("product")
    if not isinstance(product, dict):
        return None
    return normalize_product(product)
