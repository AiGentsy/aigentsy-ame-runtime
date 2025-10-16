import os
from datetime import datetime
from typing import List, Dict, Any, Optional

# Your existing dual emit
try:
    from events import emit as _emit
except Exception:
    def _emit(kind: str, data: dict):  # safe fallback
        pass

try:
    from log_to_jsonbin_aam_patched import log_event as _log_event
except Exception:
    def _log_event(evt: dict):
        pass

def emit_both(kind: str, data: dict):
    try:
        _emit(kind, data)
    except Exception:
        pass
    try:
        _log_event({"kind": kind, **(data or {})})
    except Exception:
        pass

# Optional DealGraph utilities
def _dg_create(opportunity: dict, roles_needed: list, rev_split: list) -> dict:
    try:
        from metabridge_dealgraph import create_dealgraph
        return create_dealgraph(opportunity, roles_needed, rev_split)
    except Exception:
        # Safe mock
        return {"id": f"dg_{int(datetime.utcnow().timestamp())}", "opportunity": opportunity, "roles": roles_needed, "rev_split": rev_split}

def _dg_invite(graph_id: str) -> dict:
    try:
        from metabridge_dealgraph import invite_roles
        return invite_roles(graph_id)
    except Exception:
        return {"ok": True, "graph_id": graph_id, "invited": True}

def _dg_activate(graph_id: str) -> dict:
    try:
        from metabridge_dealgraph import activate
        return activate(graph_id)
    except Exception:
        return {"ok": True, "graph_id": graph_id, "status": "activated"}

# Optional Outcome Oracle (for richer attribution if you want to call it here)
def _oracle(kind: str, payload: dict):
    try:
        from outcome_oracle_MAX import on_event as on_event_max
        on_event_max({"kind": kind, **payload})
    except Exception:
        try:
            from outcome_oracle_UPGRADED import on_event as on_event_up
            on_event_up({"kind": kind, **payload})
        except Exception:
            # logging already handled by emit_both
            pass

class MetaBridgeRuntime:
    def __init__(self):
        self.history: List[dict] = []
        self.matches_cache: Dict[str, List[dict]] = {}

    def match_offer(self, query: str) -> List[dict]:
        """
        Returns a list of matches. Each match SHOULD include a 'roles' or 'meta_role' field for DealGraph.
        """
        try:
            from aigent_growth_metamatch import metabridge_dual_match_realworld_fulfillment
            matches = metabridge_dual_match_realworld_fulfillment(query)
        except Exception:
            matches = []
        self.history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "query": query,
            "matches": matches
        })
        return matches

    # ---- DealGraph integration ----
    def _roles_from_matches(self, matches: List[dict]) -> List[str]:
        roles: List[str] = []
        for m in matches or []:
            r = m.get("roles") or m.get("meta_role") or m.get("role")
            if isinstance(r, list):
                roles.extend(r)
            elif isinstance(r, str):
                roles.append(r)
        # normalize
        return [str(x).upper() for x in roles if x]

    def _maybe_create_dealgraph(self, query: str, originator: str, matches: List[dict], mesh_session_id: Optional[str]) -> Optional[dict]:
        roles = self._roles_from_matches(matches)
        unique_roles = sorted(set(roles))
        if len(unique_roles) < 2:
            return None  # no need for dealgraph when single-role

        opportunity = {
            "query": query,
            "originator": originator,
            "mesh_session_id": mesh_session_id
        }
        # basic even split when not specified
        pct = round(100 / max(1, len(unique_roles)), 2)
        rev_split = [{"role": r, "pct": pct} for r in unique_roles]

        graph = _dg_create(opportunity, unique_roles, rev_split)
        emit_both("DEALGRAPH_CREATED", {"graph_id": graph.get("id"), **opportunity, "roles": unique_roles, "rev_split": rev_split})
        _oracle("DEALGRAPH_CREATED", {"graph_id": graph.get("id"), **opportunity})
        inv = _dg_invite(graph.get("id"))
        emit_both("DEALGRAPH_INVITED", {"graph_id": graph.get("id"), "invited": inv.get("invited", True)})
        _oracle("DEALGRAPH_INVITED", {"graph_id": graph.get("id")})
        return graph

    def activate_dealgraph(self, graph_id: str, mesh_session_id: Optional[str] = None) -> dict:
        res = _dg_activate(graph_id)
        payload = {"graph_id": graph_id, "mesh_session_id": mesh_session_id}
        emit_both("DEALGRAPH_ACTIVATED", payload)
        _oracle("DEALGRAPH_ACTIVATED", payload)
        return {"ok": True, "graph_id": graph_id, "activated": True}

    # ---- Proposals ----
    def generate_proposal(self, originator: str, query: str, matches: List[dict]) -> str:
        try:
            from proposal_generator import proposal_generator
            return proposal_generator(originator, query, matches)
        except Exception:
            return f"Proposal from {originator} for: {query}\\n\\nMatches: {', '.join([m.get('username','?') for m in (matches or [])])}"

    def dispatch_proposal(self, originator: str, query: str, matches: List[dict], mesh_session_id: Optional[str] = None) -> dict:
        # If multi-role, create a DealGraph
        graph = self._maybe_create_dealgraph(query, originator, matches, mesh_session_id)

        # Build & send proposal
        proposal = self.generate_proposal(originator, query, matches)
        match_target = matches[0].get("username") if matches else None
        delivery = {}
        try:
            from proposal_generator import proposal_dispatch, deliver_proposal
            proposal_dispatch(originator, proposal, match_target=match_target)
            delivery = deliver_proposal(query, matches, originator)
        except Exception:
            delivery = {"ok": False, "error": "delivery_module_missing"}

        # Emit high-level events
        emit_both("PROPOSAL_DISPATCHED", {
            "originator": originator, "target": match_target, "mesh_session_id": mesh_session_id
        })
        _oracle("PROPOSAL_DISPATCHED", {"originator": originator, "target": match_target, "mesh_session_id": mesh_session_id})

        # Optionally auto-activate graph after dispatch
        if graph and graph.get("id"):
            self.activate_dealgraph(graph["id"], mesh_session_id=mesh_session_id)

        return {"proposal": proposal, "delivery": delivery, "dealgraph": graph}

    def full_cycle(self, query: str, originator: str, mesh_session_id: Optional[str] = None) -> dict:
        matches = self.match_offer(query)
        return self.dispatch_proposal(originator, query, matches, mesh_session_id=mesh_session_id)
