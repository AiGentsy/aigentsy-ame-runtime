"""
LEGAL TERMS: Handshake Agreement + Deposit Terms
=================================================

Legal disclosures and terms for the handshake flow.

Terms:
1. AI-POWERED DISCLOSURE - Service uses AI with human QA
2. PREVIEW IS A SAMPLE - ~20% work to demonstrate capability
3. IP OWNERSHIP - Remains AiGentsy property until full payment
4. PREVIEW EXPIRATION - 48 hours from delivery
5. DEPOSIT REQUIREMENT - 50% to proceed, held in escrow
6. MONEY-BACK GUARANTEE - Full refund within 7 days if not satisfied

Updated: Jan 2026
"""

from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta


@dataclass
class LegalTerm:
    """A single legal term/disclosure"""
    id: str
    title: str
    description: str
    required: bool = True


# Handshake Agreement Terms
HANDSHAKE_TERMS: List[LegalTerm] = [
    LegalTerm(
        id="ai_disclosure",
        title="AI-POWERED SERVICE",
        description=(
            "This service is powered by artificial intelligence, including but not limited to "
            "Claude (Anthropic), GPT-4 (OpenAI), and Gemini (Google). All AI-generated work "
            "undergoes human quality assurance review before delivery. By accepting these terms, "
            "you acknowledge that your deliverables will be created with AI assistance."
        ),
        required=True,
    ),
    LegalTerm(
        id="preview_sample",
        title="PREVIEW IS A SAMPLE",
        description=(
            "The preview you will receive represents approximately 20% of the total work. "
            "It is provided to demonstrate our capability and approach, not as a complete "
            "deliverable. The preview is watermarked and remains AiGentsy's intellectual "
            "property until you complete payment."
        ),
        required=True,
    ),
    LegalTerm(
        id="ip_ownership",
        title="INTELLECTUAL PROPERTY",
        description=(
            "All work product, including previews and final deliverables, remains the sole "
            "intellectual property of AiGentsy until full payment is received. Upon full "
            "payment, all intellectual property rights transfer to you. You may not use, "
            "reproduce, or distribute any work product before payment is complete."
        ),
        required=True,
    ),
    LegalTerm(
        id="preview_expiration",
        title="PREVIEW EXPIRATION",
        description=(
            "Your preview will be available for 48 hours from the time of delivery. After "
            "this period, the preview will expire and you will need to request a new one. "
            "This ensures our work remains current and relevant to your needs."
        ),
        required=True,
    ),
    LegalTerm(
        id="deposit_escrow",
        title="DEPOSIT & ESCROW",
        description=(
            "To proceed beyond the preview, a 50% deposit is required. This deposit is held "
            "in escrow (authorized but not captured) via Stripe. The deposit is only captured "
            "after you approve the completed work. If you do not approve, the deposit is "
            "released back to you."
        ),
        required=True,
    ),
    LegalTerm(
        id="money_back",
        title="MONEY-BACK GUARANTEE",
        description=(
            "We offer a full money-back guarantee within 7 days of final delivery if you are "
            "not satisfied with the completed work. Simply contact us within 7 days of "
            "receiving your final deliverables, and we will refund your payment in full."
        ),
        required=True,
    ),
]


# Deposit Terms (shown at payment)
DEPOSIT_TERMS: List[LegalTerm] = [
    LegalTerm(
        id="deposit_amount",
        title="DEPOSIT AMOUNT",
        description=(
            "The deposit is 50% of the quoted price. This amount will be held in escrow "
            "and only captured upon your approval of the completed work."
        ),
        required=True,
    ),
    LegalTerm(
        id="escrow_hold",
        title="ESCROW HOLD",
        description=(
            "Your deposit is held via Stripe using payment authorization. The funds are "
            "reserved on your card but not captured until you approve the work. If you "
            "do not approve, the authorization is released."
        ),
        required=True,
    ),
    LegalTerm(
        id="capture_trigger",
        title="PAYMENT CAPTURE",
        description=(
            "Payment is captured only after you explicitly approve the completed deliverables. "
            "You will have the opportunity to review all work before any funds are transferred."
        ),
        required=True,
    ),
    LegalTerm(
        id="balance_due",
        title="BALANCE DUE",
        description=(
            "The remaining 50% balance is due upon final delivery and your approval. "
            "Full intellectual property rights transfer upon receipt of full payment."
        ),
        required=True,
    ),
]


# Preview expiration hours
PREVIEW_EXPIRATION_HOURS = 48

# Handshake expiration hours (from contract creation)
HANDSHAKE_EXPIRATION_HOURS = 48

# Deposit percentage
DEPOSIT_PERCENTAGE = 0.50

# Money-back guarantee days
MONEY_BACK_GUARANTEE_DAYS = 7


def get_handshake_terms() -> List[Dict[str, Any]]:
    """Get all handshake terms as dictionaries"""
    return [
        {
            "id": term.id,
            "title": term.title,
            "description": term.description,
            "required": term.required,
        }
        for term in HANDSHAKE_TERMS
    ]


def get_deposit_terms() -> List[Dict[str, Any]]:
    """Get all deposit terms as dictionaries"""
    return [
        {
            "id": term.id,
            "title": term.title,
            "description": term.description,
            "required": term.required,
        }
        for term in DEPOSIT_TERMS
    ]


def get_handshake_agreement_text() -> str:
    """Get full handshake agreement as formatted text"""
    lines = [
        "AIGENTSY SERVICE AGREEMENT",
        "=" * 50,
        "",
        "By clicking 'Accept & View Preview', you agree to the following terms:",
        "",
    ]

    for i, term in enumerate(HANDSHAKE_TERMS, 1):
        lines.append(f"{i}. {term.title}")
        lines.append(f"   {term.description}")
        lines.append("")

    lines.extend([
        "=" * 50,
        "Questions? Contact support@aigentsy.com",
    ])

    return "\n".join(lines)


def get_deposit_agreement_text() -> str:
    """Get full deposit agreement as formatted text"""
    lines = [
        "DEPOSIT AGREEMENT",
        "=" * 50,
        "",
        "By proceeding with payment, you agree to the following:",
        "",
    ]

    for i, term in enumerate(DEPOSIT_TERMS, 1):
        lines.append(f"{i}. {term.title}")
        lines.append(f"   {term.description}")
        lines.append("")

    lines.extend([
        "=" * 50,
        "Secure payment via Stripe",
    ])

    return "\n".join(lines)


def calculate_preview_expiration() -> str:
    """Calculate preview expiration timestamp (48h from now)"""
    expires = datetime.now(timezone.utc) + timedelta(hours=PREVIEW_EXPIRATION_HOURS)
    return expires.isoformat()


def calculate_handshake_expiration() -> str:
    """Calculate handshake expiration timestamp (48h from now)"""
    expires = datetime.now(timezone.utc) + timedelta(hours=HANDSHAKE_EXPIRATION_HOURS)
    return expires.isoformat()


def calculate_deposit_amount(total_price: float) -> float:
    """Calculate deposit amount (50% of total)"""
    return round(total_price * DEPOSIT_PERCENTAGE, 2)


def calculate_balance_due(total_price: float) -> float:
    """Calculate balance due after deposit (50% of total)"""
    return round(total_price * (1 - DEPOSIT_PERCENTAGE), 2)


def is_preview_expired(preview_expires_at: str) -> bool:
    """Check if preview has expired"""
    if not preview_expires_at:
        return True
    try:
        expires = datetime.fromisoformat(preview_expires_at.replace("Z", "+00:00"))
        return datetime.now(timezone.utc) > expires
    except:
        return True


def is_handshake_expired(handshake_expires_at: str) -> bool:
    """Check if handshake window has expired"""
    if not handshake_expires_at:
        return True
    try:
        expires = datetime.fromisoformat(handshake_expires_at.replace("Z", "+00:00"))
        return datetime.now(timezone.utc) > expires
    except:
        return True


def get_remaining_time(expires_at: str) -> Dict[str, Any]:
    """Get remaining time until expiration"""
    if not expires_at:
        return {"expired": True, "hours": 0, "minutes": 0}

    try:
        expires = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = expires - now

        if diff.total_seconds() <= 0:
            return {"expired": True, "hours": 0, "minutes": 0}

        hours = int(diff.total_seconds() // 3600)
        minutes = int((diff.total_seconds() % 3600) // 60)

        return {
            "expired": False,
            "hours": hours,
            "minutes": minutes,
            "total_seconds": int(diff.total_seconds()),
        }
    except:
        return {"expired": True, "hours": 0, "minutes": 0}
