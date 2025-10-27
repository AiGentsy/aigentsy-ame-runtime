from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class NudgeReq(BaseModel):
    user_id: str
    proposal_id: str

class ConvertReq(BaseModel):
    user_id: str
    proposal_id: str

@router.post("/proposal/nudge")
def nudge(req: NudgeReq):
    return {"ok": True, "nudged": req.proposal_id}

@router.post("/proposal/convert")
def convert(req: ConvertReq):
    url = f"https://shop.quick/{req.proposal_id}"
    return {"ok": True, "converted": req.proposal_id, "url": url}
