"""
TRANSPARENT SAVINGS COUNTER - AiGentsy v115
============================================

"$X saved / Y SLAs hit / Z disputes avoided" - from proofs
Conversion lift with enterprises.

METRICS TRACKED:
- Total money saved (vs traditional methods)
- SLAs hit (delivery guarantees met)
- Disputes avoided (successful resolutions)
- Time saved (hours of automation)
- Quality scores maintained

All metrics are verifiable via public proofs (Merkle roots).

Powered by AiGentsy
"""

import os
import hashlib
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


AIGENTSY_URL = os.getenv("AIGENTSY_URL", "https://aigentsy.com")


def _now():
    return datetime.now(timezone.utc).isoformat() + "Z"


@dataclass
class SavingsMetrics:
    """Aggregate savings metrics"""
    total_money_saved: float = 0.0
    total_slas_hit: int = 0
    total_slas_missed: int = 0
    total_disputes_avoided: int = 0
    total_disputes_occurred: int = 0
    total_hours_saved: float = 0.0
    total_transactions: int = 0
    total_outcomes_delivered: int = 0
    avg_quality_score: float = 0.0
    quality_scores_sum: float = 0.0
    last_updated: str = ""


@dataclass
class UserSavings:
    """Per-user savings tracking"""
    user_id: str
    money_saved: float = 0.0
    slas_hit: int = 0
    slas_missed: int = 0
    disputes_avoided: int = 0
    hours_saved: float = 0.0
    transactions: int = 0
    outcomes: int = 0
    avg_quality: float = 0.0
    quality_sum: float = 0.0
    first_transaction: str = ""
    last_transaction: str = ""


# Global metrics
GLOBAL_METRICS = SavingsMetrics()

# Per-user metrics
USER_METRICS: Dict[str, UserSavings] = {}

# Transaction log for proof generation
TRANSACTION_LOG: List[Dict[str, Any]] = []


def record_savings(
    user_id: str,
    transaction_id: str,
    traditional_cost: float,
    aigentsy_cost: float,
    sla_met: bool,
    dispute_avoided: bool,
    hours_saved: float,
    quality_score: float,  # 0-5
    outcome_type: str = "service"
) -> Dict[str, Any]:
    """
    Record a savings event.

    Args:
        user_id: User who benefited
        transaction_id: Unique transaction ID
        traditional_cost: What it would cost traditionally
        aigentsy_cost: What it cost with AiGentsy
        sla_met: Was the SLA met?
        dispute_avoided: Was a potential dispute avoided?
        hours_saved: Hours of manual work saved
        quality_score: Quality rating 0-5

    Returns:
        Savings record with proof hash
    """

    money_saved = max(0, traditional_cost - aigentsy_cost)

    # Create savings record
    record = {
        "transaction_id": transaction_id,
        "user_id": user_id,
        "timestamp": _now(),
        "traditional_cost": traditional_cost,
        "aigentsy_cost": aigentsy_cost,
        "money_saved": money_saved,
        "sla_met": sla_met,
        "dispute_avoided": dispute_avoided,
        "hours_saved": hours_saved,
        "quality_score": quality_score,
        "outcome_type": outcome_type
    }

    # Generate proof hash
    record_json = json.dumps(record, sort_keys=True)
    proof_hash = hashlib.sha256(record_json.encode()).hexdigest()
    record["proof_hash"] = proof_hash

    # Add to transaction log
    TRANSACTION_LOG.append(record)

    # Update global metrics
    GLOBAL_METRICS.total_money_saved += money_saved
    GLOBAL_METRICS.total_transactions += 1
    GLOBAL_METRICS.total_outcomes_delivered += 1
    GLOBAL_METRICS.total_hours_saved += hours_saved
    GLOBAL_METRICS.quality_scores_sum += quality_score

    if sla_met:
        GLOBAL_METRICS.total_slas_hit += 1
    else:
        GLOBAL_METRICS.total_slas_missed += 1

    if dispute_avoided:
        GLOBAL_METRICS.total_disputes_avoided += 1
    else:
        GLOBAL_METRICS.total_disputes_occurred += 1

    # Update average quality
    GLOBAL_METRICS.avg_quality_score = (
        GLOBAL_METRICS.quality_scores_sum / GLOBAL_METRICS.total_transactions
    )
    GLOBAL_METRICS.last_updated = _now()

    # Update user metrics
    if user_id not in USER_METRICS:
        USER_METRICS[user_id] = UserSavings(user_id=user_id, first_transaction=_now())

    user = USER_METRICS[user_id]
    user.money_saved += money_saved
    user.transactions += 1
    user.outcomes += 1
    user.hours_saved += hours_saved
    user.quality_sum += quality_score
    user.avg_quality = user.quality_sum / user.transactions
    user.last_transaction = _now()

    if sla_met:
        user.slas_hit += 1
    else:
        user.slas_missed += 1

    if dispute_avoided:
        user.disputes_avoided += 1

    return {
        "ok": True,
        "transaction_id": transaction_id,
        "money_saved": money_saved,
        "proof_hash": proof_hash,
        "global_total_saved": GLOBAL_METRICS.total_money_saved,
        "powered_by": "AiGentsy"
    }


def get_global_savings() -> Dict[str, Any]:
    """Get global savings counter - the main display metric"""

    sla_rate = (
        GLOBAL_METRICS.total_slas_hit /
        (GLOBAL_METRICS.total_slas_hit + GLOBAL_METRICS.total_slas_missed)
        if (GLOBAL_METRICS.total_slas_hit + GLOBAL_METRICS.total_slas_missed) > 0
        else 0
    )

    dispute_avoidance_rate = (
        GLOBAL_METRICS.total_disputes_avoided /
        (GLOBAL_METRICS.total_disputes_avoided + GLOBAL_METRICS.total_disputes_occurred)
        if (GLOBAL_METRICS.total_disputes_avoided + GLOBAL_METRICS.total_disputes_occurred) > 0
        else 0
    )

    return {
        "ok": True,
        "savings_counter": {
            "money_saved": f"${GLOBAL_METRICS.total_money_saved:,.2f}",
            "money_saved_raw": round(GLOBAL_METRICS.total_money_saved, 2),
            "slas_hit": GLOBAL_METRICS.total_slas_hit,
            "sla_rate": f"{sla_rate * 100:.1f}%",
            "disputes_avoided": GLOBAL_METRICS.total_disputes_avoided,
            "dispute_avoidance_rate": f"{dispute_avoidance_rate * 100:.1f}%",
            "hours_saved": f"{GLOBAL_METRICS.total_hours_saved:,.0f}",
            "avg_quality": f"{GLOBAL_METRICS.avg_quality_score:.1f}/5",
            "total_outcomes": GLOBAL_METRICS.total_outcomes_delivered,
            "total_transactions": GLOBAL_METRICS.total_transactions
        },
        "display_string": f"${GLOBAL_METRICS.total_money_saved:,.0f} saved | {GLOBAL_METRICS.total_slas_hit} SLAs hit | {GLOBAL_METRICS.total_disputes_avoided} disputes avoided",
        "badge_html": f'<div class="aigentsy-savings-badge"><span class="money">${GLOBAL_METRICS.total_money_saved:,.0f} saved</span> | <span class="sla">{GLOBAL_METRICS.total_slas_hit} SLAs hit</span> | <span class="disputes">{GLOBAL_METRICS.total_disputes_avoided} disputes avoided</span> | <span class="powered">Powered by AiGentsy</span></div>',
        "last_updated": GLOBAL_METRICS.last_updated,
        "powered_by": "AiGentsy"
    }


def get_user_savings(user_id: str) -> Dict[str, Any]:
    """Get savings for a specific user"""

    if user_id not in USER_METRICS:
        return {
            "ok": False,
            "error": "User not found",
            "powered_by": "AiGentsy"
        }

    user = USER_METRICS[user_id]

    sla_rate = (
        user.slas_hit / (user.slas_hit + user.slas_missed)
        if (user.slas_hit + user.slas_missed) > 0
        else 0
    )

    return {
        "ok": True,
        "user_id": user_id,
        "savings": {
            "money_saved": f"${user.money_saved:,.2f}",
            "money_saved_raw": round(user.money_saved, 2),
            "slas_hit": user.slas_hit,
            "sla_rate": f"{sla_rate * 100:.1f}%",
            "disputes_avoided": user.disputes_avoided,
            "hours_saved": f"{user.hours_saved:,.0f}",
            "avg_quality": f"{user.avg_quality:.1f}/5",
            "total_outcomes": user.outcomes,
            "total_transactions": user.transactions
        },
        "display_string": f"${user.money_saved:,.0f} saved with AiGentsy",
        "first_transaction": user.first_transaction,
        "last_transaction": user.last_transaction,
        "powered_by": "AiGentsy"
    }


def generate_merkle_root() -> Dict[str, Any]:
    """
    Generate Merkle root from transaction log for verifiable proofs.

    Enterprises can verify savings claims against this root.
    """

    if not TRANSACTION_LOG:
        return {
            "ok": True,
            "merkle_root": None,
            "transaction_count": 0,
            "powered_by": "AiGentsy"
        }

    # Get all proof hashes
    leaves = [t["proof_hash"] for t in TRANSACTION_LOG]

    # Build Merkle tree
    while len(leaves) > 1:
        if len(leaves) % 2 == 1:
            leaves.append(leaves[-1])  # Duplicate last if odd

        next_level = []
        for i in range(0, len(leaves), 2):
            combined = leaves[i] + leaves[i + 1]
            parent = hashlib.sha256(combined.encode()).hexdigest()
            next_level.append(parent)

        leaves = next_level

    merkle_root = leaves[0] if leaves else None

    return {
        "ok": True,
        "merkle_root": merkle_root,
        "transaction_count": len(TRANSACTION_LOG),
        "verification_url": f"{AIGENTSY_URL}/proofs/verify/{merkle_root}",
        "generated_at": _now(),
        "powered_by": "AiGentsy"
    }


def verify_transaction_proof(transaction_id: str) -> Dict[str, Any]:
    """Verify a specific transaction is in the proof set"""

    # Find transaction
    transaction = next((t for t in TRANSACTION_LOG if t["transaction_id"] == transaction_id), None)

    if not transaction:
        return {
            "ok": False,
            "verified": False,
            "error": "Transaction not found",
            "powered_by": "AiGentsy"
        }

    # Verify hash
    record_copy = {k: v for k, v in transaction.items() if k != "proof_hash"}
    record_json = json.dumps(record_copy, sort_keys=True)
    computed_hash = hashlib.sha256(record_json.encode()).hexdigest()

    verified = computed_hash == transaction["proof_hash"]

    return {
        "ok": True,
        "verified": verified,
        "transaction_id": transaction_id,
        "proof_hash": transaction["proof_hash"],
        "savings_claimed": transaction["money_saved"],
        "timestamp": transaction["timestamp"],
        "powered_by": "AiGentsy"
    }


def get_savings_leaderboard(limit: int = 10) -> Dict[str, Any]:
    """Get top savers leaderboard"""

    sorted_users = sorted(
        USER_METRICS.values(),
        key=lambda u: u.money_saved,
        reverse=True
    )[:limit]

    leaderboard = []
    for i, user in enumerate(sorted_users):
        leaderboard.append({
            "rank": i + 1,
            "user_id": user.user_id[:8] + "...",  # Anonymize
            "money_saved": f"${user.money_saved:,.2f}",
            "outcomes": user.outcomes,
            "sla_rate": f"{(user.slas_hit / max(1, user.slas_hit + user.slas_missed)) * 100:.0f}%"
        })

    return {
        "ok": True,
        "leaderboard": leaderboard,
        "total_users": len(USER_METRICS),
        "powered_by": "AiGentsy"
    }


def get_savings_counter_status() -> Dict[str, Any]:
    """Get savings counter system status"""

    return {
        "ok": True,
        "global_savings": get_global_savings()["savings_counter"],
        "merkle_proof": generate_merkle_root(),
        "total_users_tracked": len(USER_METRICS),
        "total_transactions_logged": len(TRANSACTION_LOG),
        "verification_enabled": True,
        "powered_by": "AiGentsy"
    }


# ═══════════════════════════════════════════════════════════════════════════════
# EMBEDDABLE WIDGET
# ═══════════════════════════════════════════════════════════════════════════════

def get_savings_widget_html(style: str = "badge") -> str:
    """Get embeddable HTML widget for savings counter"""

    savings = get_global_savings()["savings_counter"]

    if style == "badge":
        return f'''
<div class="aigentsy-savings-widget" style="font-family: system-ui; padding: 12px 20px; background: linear-gradient(135deg, #6366f1, #8b5cf6); border-radius: 8px; color: white; display: inline-flex; gap: 16px; align-items: center; font-size: 14px;">
    <span style="font-weight: 600;">${GLOBAL_METRICS.total_money_saved:,.0f} saved</span>
    <span style="opacity: 0.7;">|</span>
    <span>{GLOBAL_METRICS.total_slas_hit} SLAs hit</span>
    <span style="opacity: 0.7;">|</span>
    <span>{GLOBAL_METRICS.total_disputes_avoided} disputes avoided</span>
    <span style="opacity: 0.7;">|</span>
    <a href="{AIGENTSY_URL}" style="color: white; text-decoration: none; font-weight: 500;">Powered by AiGentsy</a>
</div>
'''

    elif style == "card":
        return f'''
<div class="aigentsy-savings-card" style="font-family: system-ui; padding: 24px; background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); max-width: 320px;">
    <div style="font-size: 32px; font-weight: 700; color: #6366f1;">${GLOBAL_METRICS.total_money_saved:,.0f}</div>
    <div style="color: #666; margin-bottom: 16px;">Total Saved with AiGentsy</div>
    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; text-align: center;">
        <div>
            <div style="font-size: 20px; font-weight: 600; color: #10b981;">{GLOBAL_METRICS.total_slas_hit}</div>
            <div style="font-size: 12px; color: #666;">SLAs Hit</div>
        </div>
        <div>
            <div style="font-size: 20px; font-weight: 600; color: #f59e0b;">{GLOBAL_METRICS.total_disputes_avoided}</div>
            <div style="font-size: 12px; color: #666;">Disputes Avoided</div>
        </div>
        <div>
            <div style="font-size: 20px; font-weight: 600; color: #3b82f6;">{GLOBAL_METRICS.total_hours_saved:,.0f}h</div>
            <div style="font-size: 12px; color: #666;">Hours Saved</div>
        </div>
    </div>
    <div style="margin-top: 16px; padding-top: 12px; border-top: 1px solid #eee; text-align: center;">
        <a href="{AIGENTSY_URL}" style="color: #6366f1; text-decoration: none; font-size: 12px; font-weight: 500;">Powered by AiGentsy</a>
    </div>
</div>
'''

    return savings["display_string"]


# ═══════════════════════════════════════════════════════════════════════════════
# FASTAPI INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

def include_savings_counter(app):
    """Add savings counter endpoints to FastAPI app"""

    from fastapi import Body
    from fastapi.responses import HTMLResponse

    @app.get("/savings/status")
    async def savings_status():
        """Get savings counter status"""
        return get_savings_counter_status()

    @app.get("/savings/global")
    async def global_savings():
        """Get global savings counter"""
        return get_global_savings()

    @app.get("/savings/user/{user_id}")
    async def user_savings(user_id: str):
        """Get user savings"""
        return get_user_savings(user_id)

    @app.post("/savings/record")
    async def record(body: Dict = Body(...)):
        """Record a savings event"""
        return record_savings(
            user_id=body.get("user_id", "anonymous"),
            transaction_id=body.get("transaction_id"),
            traditional_cost=body.get("traditional_cost", 0),
            aigentsy_cost=body.get("aigentsy_cost", 0),
            sla_met=body.get("sla_met", True),
            dispute_avoided=body.get("dispute_avoided", True),
            hours_saved=body.get("hours_saved", 0),
            quality_score=body.get("quality_score", 5),
            outcome_type=body.get("outcome_type", "service")
        )

    @app.get("/savings/merkle-root")
    async def merkle_root():
        """Get Merkle root for proof verification"""
        return generate_merkle_root()

    @app.get("/savings/verify/{transaction_id}")
    async def verify(transaction_id: str):
        """Verify a transaction proof"""
        return verify_transaction_proof(transaction_id)

    @app.get("/savings/leaderboard")
    async def leaderboard(limit: int = 10):
        """Get savings leaderboard"""
        return get_savings_leaderboard(limit)

    @app.get("/savings/widget", response_class=HTMLResponse)
    async def widget(style: str = "badge"):
        """Get embeddable savings widget"""
        return get_savings_widget_html(style)

    print("=" * 80)
    print("💰 SAVINGS COUNTER LOADED - Powered by AiGentsy")
    print("=" * 80)
    print("Endpoints:")
    print("  GET  /savings/status")
    print("  GET  /savings/global")
    print("  GET  /savings/user/{user_id}")
    print("  POST /savings/record")
    print("  GET  /savings/merkle-root")
    print("  GET  /savings/verify/{transaction_id}")
    print("  GET  /savings/leaderboard")
    print("  GET  /savings/widget?style=badge|card")
    print("=" * 80)


if __name__ == "__main__":
    import secrets

    print("=" * 60)
    print("SAVINGS COUNTER TEST - Powered by AiGentsy")
    print("=" * 60)

    # Record some test savings
    for i in range(5):
        result = record_savings(
            user_id=f"user_{i % 3}",
            transaction_id=f"txn_{secrets.token_hex(4)}",
            traditional_cost=500 + (i * 100),
            aigentsy_cost=300 + (i * 50),
            sla_met=True,
            dispute_avoided=i % 2 == 0,
            hours_saved=2 + i,
            quality_score=4.5 + (i * 0.1)
        )
        print(f"Recorded: ${result['money_saved']:.2f} saved")

    print("\n" + "=" * 60)
    print("GLOBAL SAVINGS COUNTER")
    print("=" * 60)
    global_stats = get_global_savings()
    print(global_stats["display_string"])

    print("\n" + "=" * 60)
    print("MERKLE ROOT (for verification)")
    print("=" * 60)
    merkle = generate_merkle_root()
    print(f"Root: {merkle['merkle_root'][:40]}...")
    print(f"Transactions: {merkle['transaction_count']}")
