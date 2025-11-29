from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from jsonbin_client import JSONBinClient

router = APIRouter()

class PublishPack(BaseModel):
    author: str
    manifests: List[str]
    fee_pct: float

class ActivatePack(BaseModel):
    user: str
    pack_id: str

@router.post("/publish_pack")
def publish_pack(req: PublishPack):
    jb = JSONBinClient()
    data = jb.get_latest().get("record") or {}
    fps = data.setdefault("franchise_packs", [])
    pid = f"fp_{len(fps)+1}"
    fps.append({"id":pid,"author":req.author,"manifests":req.manifests,"fee_pct":req.fee_pct})
    jb.put_record(data)
    return {"ok": True, "pack_id": pid}

@router.post("/activate_pack")
def activate_pack(req: ActivatePack):
    return {"ok": True, "activated": req.pack_id, "user": req.user}
