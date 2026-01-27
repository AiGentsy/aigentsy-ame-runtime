"""
CLIENT ROOM ROUTES: Real-Time Project Dashboard for Clients
═══════════════════════════════════════════════════════════════════════════════

Client-facing room with:
- Green Light Timeline (Today/This Week/Month 1)
- Milestone status and payment links
- Live artifact previews
- Proof-of-outcome cards

Updated: Jan 2026
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

# Try FastAPI
try:
    from fastapi import APIRouter, HTTPException, Query
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    logger.warning("FastAPI not available - Client Room routes disabled")


if FASTAPI_AVAILABLE:
    router = APIRouter(prefix="/client-room", tags=["Client Room"])

    class TimelineBlock:
        """A timeline block for the Green Light sequence"""
        def __init__(self, title: str, timeframe: str, items: List[Dict], status: str = "pending"):
            self.title = title
            self.timeframe = timeframe
            self.items = items
            self.status = status

    def _get_escrow():
        try:
            from contracts.milestone_escrow import get_milestone_escrow
            return get_milestone_escrow()
        except:
            return None

    def _get_orchestrator():
        try:
            from fulfillment.orchestrator import get_fulfillment_orchestrator
            return get_fulfillment_orchestrator()
        except:
            return None

    def _get_proof_ledger():
        try:
            from monetization.proof_ledger import get_proof_ledger
            return get_proof_ledger()
        except:
            return None

    def _get_growth_loops():
        try:
            from growth.growth_loops import get_growth_loops
            return get_growth_loops()
        except:
            return None

    @router.get("/{contract_id}")
    async def get_client_room(contract_id: str, token: str = Query(None)):
        """
        Get full client room data.

        Returns:
        - Contract status
        - Green Light timeline
        - Milestone cards with payment rails
        - Artifact previews
        - Proof cards
        """
        escrow = _get_escrow()
        if not escrow:
            raise HTTPException(503, "Escrow service not available")

        contract = escrow.get_contract(contract_id)
        if not contract:
            raise HTTPException(404, f"Contract {contract_id} not found")

        contract_dict = escrow.to_dict(contract)

        # Build timeline
        timeline = _build_timeline(contract_dict)

        # Get artifacts/previews
        previews = _get_artifact_previews(contract_id)

        # Get proofs
        proofs = _get_proofs(contract.opportunity_id)

        # Get NBA suggestion if applicable
        nba = _get_nba_suggestion(contract_dict)

        return {
            'ok': True,
            'contract': contract_dict,
            'timeline': timeline,
            'previews': previews,
            'proofs': proofs,
            'nba': nba,
        }

    @router.get("/{contract_id}/timeline")
    async def get_timeline(contract_id: str):
        """
        Get Green Light timeline.

        3-card sequence:
        1. Today: First artifact + SOW acceptance
        2. This Week: 2-3 milestones
        3. Month 1: Final results
        """
        escrow = _get_escrow()
        if not escrow:
            raise HTTPException(503, "Escrow service not available")

        contract = escrow.get_contract(contract_id)
        if not contract:
            raise HTTPException(404, f"Contract {contract_id} not found")

        contract_dict = escrow.to_dict(contract)
        timeline = _build_timeline(contract_dict)

        return {
            'ok': True,
            'timeline': timeline,
        }

    @router.get("/{contract_id}/milestones")
    async def get_milestones(contract_id: str):
        """Get milestone cards with payment rails"""
        escrow = _get_escrow()
        if not escrow:
            raise HTTPException(503, "Escrow service not available")

        contract = escrow.get_contract(contract_id)
        if not contract:
            raise HTTPException(404, f"Contract {contract_id} not found")

        milestones = []
        for m in contract.milestones:
            milestone_card = {
                'id': m.id,
                'milestone_id': m.milestone_id,
                'amount_usd': m.amount_usd,
                'status': m.status,
                'funded_at': m.funded_at,
                'released_at': m.released_at,
                'rails': [
                    {
                        'type': r.type,
                        'paylink_url': r.paylink_url,
                        'amount_usd': r.amount_usd,
                        'assurance': r.assurance,
                    }
                    for r in (m.rails or [])
                ] if hasattr(m, 'rails') and m.rails else [
                    {'type': 'cash', 'paylink_url': m.paylink_url, 'amount_usd': m.amount_usd}
                ],
                'selected_rail': getattr(m, 'selected_rail', None),
                'aigx_badge': {
                    'id': m.aigx_badge_id,
                    'assurance_amount': m.aigx_assurance_amount,
                } if m.aigx_badge_id else None,
            }
            milestones.append(milestone_card)

        return {
            'ok': True,
            'milestones': milestones,
            'total_amount_usd': contract.total_amount_usd,
            'funded_amount_usd': contract.funded_amount_usd,
            'released_amount_usd': contract.released_amount_usd,
        }

    @router.get("/{contract_id}/previews")
    async def get_previews(contract_id: str):
        """Get live artifact previews"""
        previews = _get_artifact_previews(contract_id)
        return {
            'ok': True,
            'previews': previews,
        }

    @router.get("/{contract_id}/proofs")
    async def get_proofs_for_contract(contract_id: str):
        """Get proof-of-outcome cards"""
        escrow = _get_escrow()
        if not escrow:
            raise HTTPException(503, "Escrow service not available")

        contract = escrow.get_contract(contract_id)
        if not contract:
            raise HTTPException(404, f"Contract {contract_id} not found")

        proofs = _get_proofs(contract.opportunity_id)
        return {
            'ok': True,
            'proofs': proofs,
        }

    @router.post("/{contract_id}/select-rail")
    async def select_payment_rail(
        contract_id: str,
        milestone_id: str = Query(...),
        rail_type: str = Query(...),
    ):
        """Select payment rail for a milestone"""
        escrow = _get_escrow()
        if not escrow:
            raise HTTPException(503, "Escrow service not available")

        contract = escrow.get_contract(contract_id)
        if not contract:
            raise HTTPException(404, f"Contract {contract_id} not found")

        for m in contract.milestones:
            if m.milestone_id == milestone_id:
                m.selected_rail = rail_type
                return {
                    'ok': True,
                    'milestone_id': milestone_id,
                    'selected_rail': rail_type,
                }

        raise HTTPException(404, f"Milestone {milestone_id} not found")

    def _build_timeline(contract_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build Green Light timeline blocks"""
        now = datetime.now(timezone.utc)
        milestones = contract_dict.get('milestones', [])

        # Block 1: Today (first artifact + SOW)
        today_items = [
            {
                'type': 'first_artifact',
                'title': 'First Artifact Preview',
                'description': 'Wireframe/PoC/outline delivered',
                'status': 'pending',
            },
            {
                'type': 'sow_acceptance',
                'title': 'SOW Acceptance',
                'description': 'Review and accept statement of work',
                'status': 'pending',
            },
        ]

        # Check if first milestone is funded
        if milestones and milestones[0].get('funded_at'):
            today_items[1]['status'] = 'completed'

        today_block = {
            'title': 'Today',
            'timeframe': now.strftime('%B %d'),
            'items': today_items,
            'status': 'in_progress',
        }

        # Block 2: This Week (milestones)
        week_items = []
        for i, m in enumerate(milestones[:3]):
            week_items.append({
                'type': 'milestone',
                'title': f"Milestone {i+1}",
                'description': f"${m.get('amount_usd', 0):.2f}",
                'status': m.get('status', 'pending'),
                'due_date': m.get('due_date'),
            })

        week_end = now + timedelta(days=7)
        week_block = {
            'title': 'This Week',
            'timeframe': f"{now.strftime('%b %d')} - {week_end.strftime('%b %d')}",
            'items': week_items,
            'status': 'pending',
        }

        # Block 3: Month 1 (results)
        month_items = [
            {
                'type': 'final_delivery',
                'title': 'Final Delivery',
                'description': 'All deliverables completed',
                'status': 'pending',
            },
            {
                'type': 'proof_of_outcome',
                'title': 'Proof of Outcome',
                'description': 'Verified results and artifacts',
                'status': 'pending',
            },
        ]

        month_end = now + timedelta(days=30)
        month_block = {
            'title': 'Month 1',
            'timeframe': f"By {month_end.strftime('%B %d')}",
            'items': month_items,
            'status': 'pending',
        }

        # Check if contract is completed
        if contract_dict.get('status') == 'completed':
            month_block['status'] = 'completed'
            month_items[0]['status'] = 'completed'
            month_items[1]['status'] = 'completed'

        return [today_block, week_block, month_block]

    def _get_artifact_previews(contract_id: str) -> List[Dict[str, Any]]:
        """Get artifact preview URLs"""
        previews = []

        # Check for FA30 contract
        try:
            from fulfillment.fa30_contracts import get_fa30_engine
            fa30 = get_fa30_engine()
            # Look for related FA30 contract
            for cid, contract in fa30.contracts.items():
                if contract_id in cid or cid in contract_id:
                    if contract.artifact_url:
                        previews.append({
                            'type': contract.artifact_type,
                            'url': contract.artifact_url,
                            'status': contract.status.value,
                            'delivered_at': contract.delivered_at,
                        })
        except:
            pass

        # Check proof ledger for artifact URLs
        ledger = _get_proof_ledger()
        if ledger:
            for proof in ledger.proofs.values():
                if proof.contract_id == contract_id:
                    for artifact in proof.artifacts:
                        if artifact.startswith('http'):
                            previews.append({
                                'type': 'artifact',
                                'url': artifact,
                                'status': 'delivered',
                                'proof_id': proof.id,
                            })

        return previews

    def _get_proofs(opportunity_id: str) -> List[Dict[str, Any]]:
        """Get proof cards for opportunity"""
        ledger = _get_proof_ledger()
        if not ledger:
            return []

        proofs = ledger.get_proofs_for_opportunity(opportunity_id)
        return [
            {
                'id': p.id,
                'title': p.title,
                'description': p.description,
                'verified': p.verified,
                'public_url': p.public_url,
                'created_at': p.created_at,
                'artifacts': p.artifacts,
            }
            for p in proofs
        ]

    def _get_nba_suggestion(contract_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get NBA suggestion if contract is near completion"""
        growth = _get_growth_loops()
        if not growth:
            return None

        # Only suggest NBA if mostly funded/released
        total = contract_dict.get('total_amount_usd', 0)
        released = contract_dict.get('released_amount_usd', 0)

        if total > 0 and released >= total * 0.5:
            # Contract is 50%+ complete - suggest NBA
            # This would normally come from growth_loops.nba_from_artifacts
            return {
                'available': True,
                'message': 'Ready for follow-up services',
            }

        return None


def get_client_room_router():
    """Get Client Room router for app registration"""
    if FASTAPI_AVAILABLE:
        return router
    return None
