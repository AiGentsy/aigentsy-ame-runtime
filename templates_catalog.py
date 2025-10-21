# templates_catalog.py
from typing import List, Dict

_TEMPLATES: List[Dict] = [
    {
        "id": "tmpl_local_service_leads",
        "name": "Local Service Lead Gen",
        "description": "Click-to-call lead capture for local services (plumber, HVAC, salon).",
        "tags": ["local", "leads", "service", "bookings", "quote", "appointment", "phone"],
        "franchise_pack": ["growth-retarget-r3-v1.json", "bundle-pricing-ab-v1.json"]
    },
    {
        "id": "tmpl_creator_merch_shop",
        "name": "Creator Merch Mini-Shop",
        "description": "One-page Shopify + AAM retargeting for creators and podcasters.",
        "tags": ["creator", "podcast", "merch", "shop", "shopify", "store", "tees"],
        "franchise_pack": ["shopify-inventory-aware-v1.json", "bundle-pricing-ab-v1.json"]
    },
    {
        "id": "tmpl_digital_course",
        "name": "Digital Course + Upsell",
        "description": "Landing + checkout with post-purchase upsell and pricing tests.",
        "tags": ["course", "coaching", "ebook", "webinar", "lesson", "tutorial"],
        "franchise_pack": ["bundle-pricing-ab-v1.json", "growth-retarget-r3-v1.json"]
    },
    {
        "id": "tmpl_affiliate_hub",
        "name": "Affiliate Offer Hub",
        "description": "MetaBridge deal-graph + intent exchange to route demand to partners.",
        "tags": ["affiliate", "offers", "deals", "partner", "collab"],
        "franchise_pack": ["metabridge-dealgraph-v1.json", "growth-retarget-r3-v1.json"]
    },
]

def list_templates() -> List[Dict]:
    return _TEMPLATES

def search_templates(q: str) -> List[Dict]:
    ql = (q or "").lower()
    out = []
    for t in _TEMPLATES:
        text = " ".join([t["id"], t["name"], t.get("description","")] + t.get("tags", []))
        if ql in text.lower():
            out.append(t)
    return out

def get_template(tid: str) -> Dict:
    for t in _TEMPLATES:
        if t["id"] == tid:
            return t
    return {}
