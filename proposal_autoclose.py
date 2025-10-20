
# proposal_autoclose.py
def nudge(proposal_id: str) -> dict: return {"ok": True, "proposal_id": proposal_id, "event": "PROPOSAL_NUDGED"}
def convert_to_quickpay(proposal_id: str) -> dict: return {"ok": True, "proposal_id": proposal_id, "event": "PROPOSAL_CONVERTED"}
