
# shopify_inventory_proxy.py
import os
from typing import Dict, Any
def get_stock(product_id: str) -> Dict[str, Any]:
    token = os.getenv("SHOPIFY_ADMIN_TOKEN")
    if not token: return {"product_id": product_id, "stock": 42, "source":"mock"}
    return {"product_id": product_id, "stock": 0, "source":"not-implemented"}
