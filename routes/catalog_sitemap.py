"""
CATALOG SITEMAP ROUTES
======================

Machine-readable sitemap of active SKUs and PDLs.
Helps SEO and partner integrations.

Endpoints:
- GET /catalog/sitemap.json - Full sitemap in JSON
- GET /catalog/sitemap.xml - XML sitemap for search engines
- GET /catalog/skus - List active SKUs
- GET /catalog/sku/{sku_id} - Get specific SKU details

Usage:
    from routes.catalog_sitemap import router as sitemap_router
    app.include_router(sitemap_router)
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

try:
    from fastapi import APIRouter, HTTPException, Query
    from fastapi.responses import Response
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    class APIRouter:
        def get(self, *args, **kwargs):
            def decorator(f): return f
            return decorator
    class Response:
        def __init__(self, *args, **kwargs): pass


SKU_DIR = Path(__file__).parent.parent / "skus"
PDL_DIR = Path(__file__).parent.parent / "pdl_catalog"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"


def _load_skus() -> List[Dict[str, Any]]:
    """Load all active SKUs from configs"""
    skus = []

    # Load from skus directory
    if SKU_DIR.exists():
        for f in SKU_DIR.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                if isinstance(data, dict):
                    data["sku_id"] = data.get("id", f.stem)
                    data["source"] = "sku_config"
                    skus.append(data)
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            item["source"] = "sku_config"
                            skus.append(item)
            except Exception:
                pass

    # Load from PDL catalog
    if PDL_DIR.exists():
        for f in PDL_DIR.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                if isinstance(data, dict):
                    data["sku_id"] = data.get("pdl_id", f.stem)
                    data["source"] = "pdl_catalog"
                    skus.append(data)
            except Exception:
                pass

    return skus


router = APIRouter(tags=["catalog"])


@router.get("/catalog/sitemap.json")
async def get_sitemap_json() -> Dict[str, Any]:
    """
    Get full catalog sitemap in JSON format.
    """
    skus = _load_skus()

    items = []
    for sku in skus:
        items.append({
            "sku": sku.get("sku_id") or sku.get("id") or sku.get("pdl_id"),
            "title": sku.get("title") or sku.get("name"),
            "description": sku.get("description", "")[:200],
            "pdl": sku.get("pdl_name") or sku.get("pdl_id"),
            "sla_minutes": sku.get("sla_minutes") or sku.get("delivery_sla", {}).get("target_minutes"),
            "price_band": sku.get("price_band") or _get_price_band(sku),
            "capabilities": sku.get("capabilities", []),
            "category": sku.get("category") or sku.get("vertical"),
            "active": sku.get("active", True),
            "source": sku.get("source")
        })

    return {
        "ok": True,
        "items": items,
        "total": len(items),
        "generated_at": _now_iso(),
        "formats": {
            "json": "/catalog/sitemap.json",
            "xml": "/catalog/sitemap.xml"
        }
    }


@router.get("/catalog/sitemap.xml")
async def get_sitemap_xml() -> Response:
    """
    Get catalog sitemap in XML format for search engines.
    """
    skus = _load_skus()
    base_url = "https://aigentsy.com/catalog"

    xml_items = []
    for sku in skus:
        sku_id = sku.get("sku_id") or sku.get("id") or sku.get("pdl_id", "unknown")
        title = sku.get("title") or sku.get("name", "")

        xml_items.append(f"""  <url>
    <loc>{base_url}/{sku_id}</loc>
    <lastmod>{datetime.now(timezone.utc).strftime("%Y-%m-%d")}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>""")

    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(xml_items)}
</urlset>"""

    if FASTAPI_AVAILABLE:
        return Response(content=xml_content, media_type="application/xml")
    return {"xml": xml_content}


@router.get("/catalog/skus")
async def list_skus(
    category: str = Query(None),
    active_only: bool = Query(True),
    limit: int = Query(100, ge=1, le=1000)
) -> Dict[str, Any]:
    """
    List active SKUs with optional filtering.

    Args:
        category: Filter by category
        active_only: Only return active SKUs
        limit: Maximum results
    """
    skus = _load_skus()

    # Filter
    if active_only:
        skus = [s for s in skus if s.get("active", True)]

    if category:
        skus = [s for s in skus if s.get("category") == category or s.get("vertical") == category]

    skus = skus[:limit]

    return {
        "ok": True,
        "skus": [
            {
                "sku_id": s.get("sku_id") or s.get("id"),
                "title": s.get("title") or s.get("name"),
                "category": s.get("category") or s.get("vertical"),
                "price_band": _get_price_band(s),
                "sla_minutes": s.get("sla_minutes")
            }
            for s in skus
        ],
        "count": len(skus),
        "filters": {"category": category, "active_only": active_only}
    }


@router.get("/catalog/sku/{sku_id}")
async def get_sku(sku_id: str) -> Dict[str, Any]:
    """
    Get details for a specific SKU.

    Args:
        sku_id: SKU identifier
    """
    skus = _load_skus()

    for sku in skus:
        if sku.get("sku_id") == sku_id or sku.get("id") == sku_id or sku.get("pdl_id") == sku_id:
            return {
                "ok": True,
                "sku": {
                    "sku_id": sku.get("sku_id") or sku.get("id") or sku.get("pdl_id"),
                    "title": sku.get("title") or sku.get("name"),
                    "description": sku.get("description"),
                    "category": sku.get("category") or sku.get("vertical"),
                    "price_band": _get_price_band(sku),
                    "price_min": sku.get("price_min") or sku.get("min_price"),
                    "price_max": sku.get("price_max") or sku.get("max_price"),
                    "sla_minutes": sku.get("sla_minutes"),
                    "capabilities": sku.get("capabilities", []),
                    "connectors": sku.get("connectors", []),
                    "active": sku.get("active", True),
                    "proof_count": sku.get("proof_count", 0),
                    "avg_csat": sku.get("avg_csat"),
                    "completion_rate": sku.get("completion_rate")
                }
            }

    if FASTAPI_AVAILABLE:
        raise HTTPException(status_code=404, detail="SKU not found")
    return {"ok": False, "error": "sku_not_found"}


@router.get("/catalog/categories")
async def list_categories() -> Dict[str, Any]:
    """
    List all available categories.
    """
    skus = _load_skus()

    categories = {}
    for sku in skus:
        cat = sku.get("category") or sku.get("vertical") or "other"
        if cat not in categories:
            categories[cat] = {"count": 0, "sample_skus": []}
        categories[cat]["count"] += 1
        if len(categories[cat]["sample_skus"]) < 3:
            categories[cat]["sample_skus"].append(
                sku.get("sku_id") or sku.get("id")
            )

    return {
        "ok": True,
        "categories": categories,
        "total_categories": len(categories)
    }


def _get_price_band(sku: Dict[str, Any]) -> str:
    """Determine price band from SKU data"""
    if "price_band" in sku:
        return sku["price_band"]

    min_price = sku.get("price_min") or sku.get("min_price") or 0
    max_price = sku.get("price_max") or sku.get("max_price") or min_price

    if max_price == 0:
        return "custom"
    elif max_price <= 50:
        return "$0-$50"
    elif max_price <= 200:
        return "$50-$200"
    elif max_price <= 500:
        return "$200-$500"
    elif max_price <= 1000:
        return "$500-$1000"
    elif max_price <= 5000:
        return "$1000-$5000"
    else:
        return "$5000+"


# Non-FastAPI fallback functions
def get_sitemap_data() -> Dict[str, Any]:
    """Non-async version for non-FastAPI usage"""
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(get_sitemap_json())
    finally:
        loop.close()


def list_active_skus() -> List[Dict[str, Any]]:
    """List active SKUs (for use by other modules)"""
    skus = _load_skus()
    return [s for s in skus if s.get("active", True)]
