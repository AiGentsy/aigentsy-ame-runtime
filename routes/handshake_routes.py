"""
HANDSHAKE ROUTES: API Endpoints for Handshake/Preview Flow
============================================================

Endpoints:
- GET /handshake/{contract_id}/terms - Get legal terms
- POST /handshake/{contract_id}/accept - Accept handshake, trigger preview
- GET /handshake/{contract_id}/preview - Get preview status/artifacts
- POST /handshake/{contract_id}/preview/approve - Approve preview, create deposit
- GET /handshake/{contract_id}/status - Get full handshake/preview status

Updated: Jan 2026
"""

import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Try FastAPI
try:
    from fastapi import APIRouter, HTTPException, Query, Request
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    logger.warning("FastAPI not available - Handshake routes disabled")


if FASTAPI_AVAILABLE:
    router = APIRouter(prefix="/handshake", tags=["Handshake"])

    class AcceptHandshakeRequest(BaseModel):
        """Request to accept handshake terms"""
        accepted: bool = True

    class ApprovePreviewRequest(BaseModel):
        """Request to approve preview and create deposit"""
        approved: bool = True

    def _get_escrow():
        try:
            from contracts.milestone_escrow import get_milestone_escrow
            return get_milestone_escrow()
        except Exception as e:
            logger.warning(f"Failed to get escrow: {e}")
            return None

    def _get_legal_terms():
        try:
            from contracts.legal_terms import (
                get_handshake_terms,
                get_deposit_terms,
                get_handshake_agreement_text,
                calculate_preview_expiration,
                calculate_handshake_expiration,
                calculate_deposit_amount,
                is_preview_expired,
                is_handshake_expired,
                get_remaining_time,
            )
            return {
                "get_handshake_terms": get_handshake_terms,
                "get_deposit_terms": get_deposit_terms,
                "get_handshake_agreement_text": get_handshake_agreement_text,
                "calculate_preview_expiration": calculate_preview_expiration,
                "calculate_handshake_expiration": calculate_handshake_expiration,
                "calculate_deposit_amount": calculate_deposit_amount,
                "is_preview_expired": is_preview_expired,
                "is_handshake_expired": is_handshake_expired,
                "get_remaining_time": get_remaining_time,
            }
        except Exception as e:
            logger.warning(f"Failed to get legal terms: {e}")
            return None

    def _get_preview_definitions():
        try:
            from contracts.preview_definitions import (
                get_preview_spec,
                get_preview_artifacts,
                preview_to_dict,
            )
            return {
                "get_preview_spec": get_preview_spec,
                "get_preview_artifacts": get_preview_artifacts,
                "preview_to_dict": preview_to_dict,
            }
        except Exception as e:
            logger.warning(f"Failed to get preview definitions: {e}")
            return None

    @router.get("/{contract_id}/terms")
    async def get_handshake_terms(contract_id: str):
        """
        Get legal terms for handshake agreement.

        Returns:
        - Handshake terms (AI disclosure, preview terms, etc.)
        - Deposit terms
        - Full agreement text
        """
        escrow = _get_escrow()
        if not escrow:
            raise HTTPException(503, "Escrow service not available")

        contract = escrow.get_contract(contract_id)
        if not contract:
            raise HTTPException(404, f"Contract {contract_id} not found")

        legal = _get_legal_terms()
        if not legal:
            raise HTTPException(503, "Legal terms service not available")

        # Get current handshake status
        handshake_status = getattr(contract, 'handshake_status', 'pending')
        handshake_expires_at = getattr(contract, 'handshake_expires_at', None)

        # Check if already accepted
        already_accepted = handshake_status == 'accepted'

        # Check expiration
        expired = False
        if handshake_expires_at:
            expired = legal["is_handshake_expired"](handshake_expires_at)

        return {
            "ok": True,
            "contract_id": contract_id,
            "handshake_status": handshake_status,
            "already_accepted": already_accepted,
            "expired": expired,
            "expires_at": handshake_expires_at,
            "remaining_time": legal["get_remaining_time"](handshake_expires_at) if handshake_expires_at else None,
            "terms": {
                "handshake": legal["get_handshake_terms"](),
                "deposit": legal["get_deposit_terms"](),
            },
            "agreement_text": legal["get_handshake_agreement_text"](),
        }

    @router.post("/{contract_id}/accept")
    async def accept_handshake(
        contract_id: str,
        request: Request,
        body: AcceptHandshakeRequest,
    ):
        """
        Accept handshake terms and trigger preview generation.

        - Logs acceptance with IP/timestamp
        - Triggers preview generation
        - Returns preview spec
        """
        escrow = _get_escrow()
        if not escrow:
            raise HTTPException(503, "Escrow service not available")

        contract = escrow.get_contract(contract_id)
        if not contract:
            raise HTTPException(404, f"Contract {contract_id} not found")

        legal = _get_legal_terms()
        if not legal:
            raise HTTPException(503, "Legal terms service not available")

        preview_defs = _get_preview_definitions()
        if not preview_defs:
            raise HTTPException(503, "Preview definitions not available")

        if not body.accepted:
            raise HTTPException(400, "Terms must be accepted")

        # Check if already accepted
        handshake_status = getattr(contract, 'handshake_status', 'pending')
        if handshake_status == 'accepted':
            return {
                "ok": True,
                "already_accepted": True,
                "message": "Handshake already accepted",
            }

        # Check expiration
        handshake_expires_at = getattr(contract, 'handshake_expires_at', None)
        if handshake_expires_at and legal["is_handshake_expired"](handshake_expires_at):
            raise HTTPException(410, "Handshake window has expired")

        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Accept handshake using escrow method
        result = escrow.accept_handshake(contract_id, client_ip)
        if not result:
            raise HTTPException(500, "Failed to accept handshake")

        # Get preview spec for this fulfillment type
        # Try to determine fulfillment type from contract/opportunity
        fulfillment_type = getattr(contract, 'preview_type', None) or "development"
        preview_spec = preview_defs["preview_to_dict"](
            preview_defs["get_preview_spec"](fulfillment_type)
        )

        return {
            "ok": True,
            "accepted": True,
            "accepted_at": datetime.now(timezone.utc).isoformat(),
            "client_ip": client_ip,
            "preview_spec": preview_spec,
            "preview_expires_at": legal["calculate_preview_expiration"](),
            "message": "Terms accepted. Preview will be generated.",
            "next_step": "Check /handshake/{contract_id}/preview for preview status",
        }

    @router.get("/{contract_id}/preview")
    async def get_preview_status(contract_id: str):
        """
        Get preview status and artifacts.

        Returns:
        - Preview status (not_started, in_progress, delivered, approved, expired)
        - Preview artifacts (if delivered)
        - Expiration countdown
        """
        escrow = _get_escrow()
        if not escrow:
            raise HTTPException(503, "Escrow service not available")

        contract = escrow.get_contract(contract_id)
        if not contract:
            raise HTTPException(404, f"Contract {contract_id} not found")

        legal = _get_legal_terms()
        if not legal:
            raise HTTPException(503, "Legal terms service not available")

        preview_defs = _get_preview_definitions()
        if not preview_defs:
            raise HTTPException(503, "Preview definitions not available")

        # Get preview status from contract
        preview_status = getattr(contract, 'preview_status', 'not_started')
        preview_artifacts = getattr(contract, 'preview_artifacts', [])
        preview_delivered_at = getattr(contract, 'preview_delivered_at', None)
        preview_expires_at = getattr(contract, 'preview_expires_at', None)
        preview_type = getattr(contract, 'preview_type', 'development')

        # Check if handshake accepted
        handshake_status = getattr(contract, 'handshake_status', 'pending')
        if handshake_status != 'accepted':
            return {
                "ok": True,
                "preview_status": "not_started",
                "message": "Please accept handshake terms first",
                "handshake_required": True,
            }

        # Check expiration
        expired = False
        remaining_time = None
        if preview_expires_at:
            expired = legal["is_preview_expired"](preview_expires_at)
            remaining_time = legal["get_remaining_time"](preview_expires_at)

        # Get preview spec
        preview_spec = preview_defs["preview_to_dict"](
            preview_defs["get_preview_spec"](preview_type)
        )

        return {
            "ok": True,
            "preview_status": preview_status,
            "preview_type": preview_type,
            "preview_spec": preview_spec,
            "artifacts": preview_artifacts,
            "delivered_at": preview_delivered_at,
            "expires_at": preview_expires_at,
            "expired": expired,
            "remaining_time": remaining_time,
            "can_approve": preview_status == "delivered" and not expired,
        }

    @router.post("/{contract_id}/preview/approve")
    async def approve_preview(
        contract_id: str,
        body: ApprovePreviewRequest,
    ):
        """
        Approve preview and create deposit payment intent.

        - Verifies preview is delivered and not expired
        - Creates Stripe payment intent (auth, not capture)
        - Returns payment link
        """
        escrow = _get_escrow()
        if not escrow:
            raise HTTPException(503, "Escrow service not available")

        contract = escrow.get_contract(contract_id)
        if not contract:
            raise HTTPException(404, f"Contract {contract_id} not found")

        legal = _get_legal_terms()
        if not legal:
            raise HTTPException(503, "Legal terms service not available")

        if not body.approved:
            raise HTTPException(400, "Preview must be approved")

        # Check preview status
        preview_status = getattr(contract, 'preview_status', 'not_started')
        if preview_status not in ['delivered']:
            raise HTTPException(400, f"Preview must be delivered first. Current status: {preview_status}")

        # Check expiration
        preview_expires_at = getattr(contract, 'preview_expires_at', None)
        if preview_expires_at and legal["is_preview_expired"](preview_expires_at):
            raise HTTPException(410, "Preview has expired. Please request a new one.")

        # Calculate deposit amount
        total_amount = contract.total_amount_usd
        deposit_amount = legal["calculate_deposit_amount"](total_amount)

        # Approve preview using escrow method
        result = escrow.approve_preview(contract_id)
        if not result:
            raise HTTPException(500, "Failed to approve preview")

        # Create Stripe payment intent (auth only, not capture)
        payment_intent = None
        stripe_secret = os.getenv("STRIPE_SECRET_KEY")
        if stripe_secret:
            try:
                import stripe
                stripe.api_key = stripe_secret

                payment_intent = stripe.PaymentIntent.create(
                    amount=int(deposit_amount * 100),  # cents
                    currency="usd",
                    capture_method="manual",  # Auth only, capture later
                    metadata={
                        "contract_id": contract_id,
                        "type": "deposit",
                        "deposit_percentage": "50",
                    },
                    description=f"AiGentsy Deposit - Contract {contract_id}",
                )
            except Exception as e:
                logger.error(f"Stripe payment intent failed: {e}")
                # Continue without Stripe - will use fallback

        return {
            "ok": True,
            "approved": True,
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "deposit_amount": deposit_amount,
            "total_amount": total_amount,
            "balance_due": total_amount - deposit_amount,
            "payment_intent_id": payment_intent.id if payment_intent else None,
            "client_secret": payment_intent.client_secret if payment_intent else None,
            "message": "Preview approved. Complete deposit to proceed.",
            "next_step": "Complete payment to start full delivery",
        }

    @router.get("/{contract_id}/status")
    async def get_handshake_status(contract_id: str):
        """
        Get full handshake/preview status.

        Returns:
        - Handshake status
        - Preview status
        - Contract status
        - Timeline
        """
        escrow = _get_escrow()
        if not escrow:
            raise HTTPException(503, "Escrow service not available")

        contract = escrow.get_contract(contract_id)
        if not contract:
            raise HTTPException(404, f"Contract {contract_id} not found")

        legal = _get_legal_terms()
        if not legal:
            raise HTTPException(503, "Legal terms service not available")

        # Get all statuses
        handshake_status = getattr(contract, 'handshake_status', 'pending')
        handshake_accepted_at = getattr(contract, 'handshake_accepted_at', None)
        handshake_expires_at = getattr(contract, 'handshake_expires_at', None)
        handshake_ip = getattr(contract, 'handshake_ip', None)

        preview_status = getattr(contract, 'preview_status', 'not_started')
        preview_type = getattr(contract, 'preview_type', None)
        preview_artifacts = getattr(contract, 'preview_artifacts', [])
        preview_delivered_at = getattr(contract, 'preview_delivered_at', None)
        preview_expires_at = getattr(contract, 'preview_expires_at', None)

        referral_code = getattr(contract, 'referral_code', None)

        # Check expirations
        handshake_expired = False
        if handshake_expires_at:
            handshake_expired = legal["is_handshake_expired"](handshake_expires_at)

        preview_expired = False
        if preview_expires_at:
            preview_expired = legal["is_preview_expired"](preview_expires_at)

        # Determine current step
        current_step = "handshake_pending"
        if handshake_status == "accepted":
            current_step = "preview_pending"
            if preview_status == "delivered":
                current_step = "preview_delivered"
                if preview_status == "approved":
                    current_step = "deposit_pending"
                    if contract.status == "funded":
                        current_step = "in_progress"
                        if contract.status == "completed":
                            current_step = "completed"

        return {
            "ok": True,
            "contract_id": contract_id,
            "current_step": current_step,
            "handshake": {
                "status": handshake_status,
                "accepted_at": handshake_accepted_at,
                "expires_at": handshake_expires_at,
                "expired": handshake_expired,
                "ip": handshake_ip,
            },
            "preview": {
                "status": preview_status,
                "type": preview_type,
                "artifacts": preview_artifacts,
                "delivered_at": preview_delivered_at,
                "expires_at": preview_expires_at,
                "expired": preview_expired,
                "remaining_time": legal["get_remaining_time"](preview_expires_at) if preview_expires_at else None,
            },
            "contract": {
                "status": contract.status,
                "total_amount_usd": contract.total_amount_usd,
                "funded_amount_usd": contract.funded_amount_usd,
                "released_amount_usd": contract.released_amount_usd,
            },
            "referral_code": referral_code,
        }


def get_handshake_router():
    """Get Handshake router for app registration"""
    if FASTAPI_AVAILABLE:
        return router
    return None
