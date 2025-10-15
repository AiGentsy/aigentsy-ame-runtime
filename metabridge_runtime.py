
import os
from events import emit
from log_to_jsonbin_aam_patched import log_event

def emit_both(kind: str, data: dict):
    try:
        emit(kind, data)
    except Exception:
        pass
    try:
        log_event({"kind": kind, **(data or {})})
    except Exception:
        pass
import requests
from datetime import datetime
from typing import List

class MetaBridgeRuntime:
    def __init__(self):
        self.history = []  # Persistent in-memory session
        self.matches_cache = {}  # Optional cache for reuse

    def match_offer(self, query: str) -> List[dict]:
        from aigent_growth_metamatch import metabridge_dual_match_realworld_fulfillment
        matches = metabridge_dual_match_realworld_fulfillment(query)
        self.history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "query": query,
            "matches": matches
        })
        return matches

    def generate_proposal(self, originator: str, query: str, matches: List[dict]) -> str:
        from proposal_generator import proposal_generator
        return proposal_generator(originator, query, matches)

    def dispatch_proposal(self, originator: str, query: str, matches: List[dict]) -> dict:
        from proposal_generator import proposal_dispatch, deliver_proposal
        proposal = self.generate_proposal(originator, query, matches)
        match_target = matches[0].get("username") if matches else None
        proposal_dispatch(originator, proposal, match_target=match_target)
        delivery_status = deliver_proposal(query, matches, originator)
        return {
            "proposal": proposal,
            "delivery": delivery_status
        }

    def full_cycle(self, query: str, originator: str) -> dict:
        matches = self.match_offer(query)
        return self.dispatch_proposal(originator, query, matches)
