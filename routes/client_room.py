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
    from fastapi import APIRouter, HTTPException, Query, Request
    from fastapi.responses import HTMLResponse
    from fastapi.templating import Jinja2Templates
    from pydantic import BaseModel
    from pathlib import Path
    FASTAPI_AVAILABLE = True

    # Setup Jinja2 templates
    templates_dir = Path(__file__).parent.parent / "templates"
    templates = Jinja2Templates(directory=str(templates_dir))
except ImportError:
    FASTAPI_AVAILABLE = False
    logger.warning("FastAPI not available - Client Room routes disabled")
    templates = None


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

    def _render_error_page(title: str, message: str, contract_id: str) -> str:
        """Render a friendly error page with AiGentsy branding"""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - AiGentsy</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
            color: #fff;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .container {{
            text-align: center;
            padding: 40px;
            max-width: 500px;
        }}
        .logo {{
            font-size: 3rem;
            margin-bottom: 20px;
        }}
        .brand {{
            font-size: 1.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 30px;
        }}
        h1 {{
            font-size: 1.8rem;
            margin-bottom: 15px;
            color: #f1f1f1;
        }}
        p {{
            color: #a0a0a0;
            line-height: 1.6;
            margin-bottom: 30px;
        }}
        .cta {{
            display: inline-block;
            padding: 12px 24px;
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .cta:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(99, 102, 241, 0.3);
        }}
        .id {{
            font-size: 0.75rem;
            color: #555;
            margin-top: 40px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🤖</div>
        <div class="brand">AiGentsy</div>
        <h1>{title}</h1>
        <p>{message}</p>
        <a href="https://twitter.com/messages" class="cta">Open Twitter DMs</a>
        <p class="id">Ref: {contract_id}</p>
    </div>
</body>
</html>"""

    @router.get("/debug/contracts")
    async def debug_list_contracts():
        """
        DEBUG: List all contracts currently in the system.
        Shows contract IDs, status, and handshake state.
        """
        escrow = _get_escrow()
        if not escrow:
            return {"error": "Escrow service not available", "contracts": []}

        contracts = []
        for contract_id, contract in escrow.contracts.items():
            contract_dict = escrow.to_dict(contract)
            contracts.append({
                'id': contract_id,
                'title': contract_dict.get('title', 'Unknown')[:50],
                'status': contract_dict.get('status'),
                'handshake_status': contract_dict.get('handshake_status'),
                'preview_status': contract_dict.get('preview_status'),
                'total_amount': contract_dict.get('total_amount_usd'),
                'created_at': contract_dict.get('created_at'),
                'client_room_url': f"/client-room/{contract_id}"
            })

        # Sort by created_at descending
        contracts.sort(key=lambda x: x.get('created_at', ''), reverse=True)

        return {
            'total_contracts': len(contracts),
            'contracts': contracts
        }

    @router.get("/debug/outreach")
    async def debug_outreach_history():
        """
        DEBUG: Show outreach tracking history (spam prevention).
        """
        try:
            from outreach import get_outreach_tracker
            tracker = get_outreach_tracker()
            return {
                'stats': tracker.get_stats(),
                'history': tracker.history
            }
        except Exception as e:
            return {"error": str(e)}

    @router.get("/debug/conversations")
    async def debug_conversations():
        """
        DEBUG: Show active conversations being monitored.
        """
        try:
            from conversation import get_conversation_manager
            manager = get_conversation_manager()
            return {
                'stats': manager.get_stats(),
                'conversations': {
                    cid: {
                        'username': c.username,
                        'platform': c.platform,
                        'state': c.state,
                        'message_count': len(c.messages),
                        'last_activity': c.last_activity,
                        'contract_id': c.contract_id
                    }
                    for cid, c in manager.conversations.items()
                }
            }
        except Exception as e:
            return {"error": str(e)}

    @router.get("/{contract_id}/json")
    async def get_client_room_json(contract_id: str, token: str = Query(None)):
        """
        Get full client room data as JSON.

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

    @router.get("/{contract_id}", response_class=HTMLResponse)
    async def view_client_room(request: Request, contract_id: str, token: str = Query(None)):
        """
        Render full client room HTML page with AiGentsy branding.

        Returns a complete HTML page with:
        - Pricing comparison (market rate vs AiGentsy)
        - Green Light timeline
        - Milestone cards with payment links
        - Deposit CTA
        """
        escrow = _get_escrow()
        if not escrow:
            # Return friendly error page
            return HTMLResponse(content=_render_error_page(
                "Service Temporarily Unavailable",
                "We're experiencing a brief hiccup. Please try again in a moment.",
                contract_id
            ), status_code=503)

        contract = escrow.get_contract(contract_id)
        if not contract:
            # Return friendly "expired" page instead of JSON error
            return HTMLResponse(content=_render_error_page(
                "Proposal Expired",
                "This proposal link has expired or was created before our latest update. Don't worry - just reply to our DM and we'll send you a fresh link!",
                contract_id
            ), status_code=404)

        contract_dict = escrow.to_dict(contract)

        # Build timeline
        timeline = _build_timeline(contract_dict)

        # Get artifacts/previews
        previews = _get_artifact_previews(contract_id)

        # Get proofs
        proofs = _get_proofs(contract.opportunity_id)

        # Calculate pricing using pricing_calculator
        try:
            from pricing_calculator import calculate_full_pricing
            # Create opportunity-like dict for pricing
            opp_for_pricing = {
                'title': contract_dict.get('title', 'Project'),
                'value': contract_dict.get('total_amount_usd', 0),
                'platform': 'direct'
            }
            pricing_result = calculate_full_pricing(opp_for_pricing)
            pricing = {
                'market_rate': pricing_result.market_rate,
                'our_price': pricing_result.our_price,
                'discount_pct': pricing_result.discount_pct,
                'deposit_amount': pricing_result.deposit_amount,
                'savings': pricing_result.savings,
                'fulfillment_type': pricing_result.fulfillment_type,
                'delivery_time': pricing_result.delivery_time
            }
        except ImportError:
            # Fallback pricing
            total = contract_dict.get('total_amount_usd', 0)
            market_rate = total * 1.5
            pricing = {
                'market_rate': market_rate,
                'our_price': total,
                'discount_pct': 35,
                'deposit_amount': total * 0.5,
                'savings': market_rate - total,
                'fulfillment_type': 'fulfillment',
                'delivery_time': '1-2 hours'
            }

        # Render HTML template
        return templates.TemplateResponse("client_room.html", {
            "request": request,
            "contract": contract_dict,
            "timeline": timeline,
            "previews": previews,
            "proofs": proofs,
            "pricing": pricing,
            "client_room_url": f"/client-room/{contract_id}",
        })

    # Legacy route - redirect to main view
    @router.get("/{contract_id}/view", response_class=HTMLResponse)
    async def view_client_room_legacy(request: Request, contract_id: str, token: str = Query(None)):
        """Legacy route - redirects to main client room view"""
        return await view_client_room(request, contract_id, token)

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
