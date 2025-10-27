from fastapi import APIRouter
router = APIRouter()

@router.get("/get")
def get_stock(product_id: str):
    # TODO: call Shopify Admin API with SHOPIFY_ADMIN_TOKEN
    return {"product_id": product_id, "stock": 120}
