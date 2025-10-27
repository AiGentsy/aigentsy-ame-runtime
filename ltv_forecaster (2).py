from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class PredictReq(BaseModel):
    user_id: str
    channel: str

@router.post("/predict")
def predict(req: PredictReq):
    base = {"tiktok":1.1,"amazon":1.05,"shopify":1.0}.get(req.channel,1.0)
    return {"ok": True, "ltv_multiplier": base}
