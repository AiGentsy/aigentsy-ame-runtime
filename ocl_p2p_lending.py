"""
AiGentsy OCL P2P Lending Expansion
-----------------------------------
Peer-to-peer lending marketplace where users stake on other users.

Features:
- UoO-based credit scoring
- P2P loan marketplace
- Lender stakes on borrowers
- AiGentsy takes 2.5% facilitation fee
- Auto-repayment from earnings
- Risk management & defaults
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from uuid import uuid4

def now_iso():
    return datetime.now(timezone.utc).isoformat() + "Z"


# ============================================================
# CREDIT SCORING - UoO-BASED
# ============================================================

def calculate_credit_score(username: str) -> Dict[str, Any]:
    """
    Calculate credit score based on UoO history.
    
    Credit score = 300-850 (FICO-like scale)
    Based on:
    - Total UoO (40%)
    - Verification rate (30%)
    - Revenue history (20%)
    - Account age (10%)
    """
    from log_to_jsonbin import get_user
    from analytics_engine import get_uol_summary
    from outcome_oracle import get_agent_poo_stats
    
    user = get_user(username)
    if not user:
        return {"ok": False, "error": "user_not_found"}
    
    # Get UoO stats
    uol = get_uol_summary(username)
    total_uoo = uol.get("total_uoo", 0)
    
    # Get PoO stats
    poo_stats = get_agent_poo_stats(username)
    verification_rate = poo_stats.get("stats", {}).get("verification_rate", 0)
    
    # Get revenue
    revenue = user.get("revenue_tracking", {}).get("total_revenue_usd", 0)
    
    # Get account age (days)
    created_at = user.get("created", now_iso())
    try:
        created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        account_age_days = (datetime.now(timezone.utc) - created_dt).days
    except:
        account_age_days = 0
    
    # ============================================
    # SCORING ALGORITHM
    # ============================================
    
    # Component 1: UoO Score (40% weight) - 0 to 340 points
    # Scale: 0 UoO = 0, 100 UoO = 340
    uoo_score = min(340, (total_uoo / 100) * 340)
    
    # Component 2: Verification Rate (30% weight) - 0 to 255 points
    # Scale: 0% = 0, 100% = 255
    verification_score = (verification_rate / 100) * 255
    
    # Component 3: Revenue (20% weight) - 0 to 170 points
    # Scale: $0 = 0, $100k = 170
    revenue_score = min(170, (revenue / 100000) * 170)
    
    # Component 4: Account Age (10% weight) - 0 to 85 points
    # Scale: 0 days = 0, 365 days = 85
    age_score = min(85, (account_age_days / 365) * 85)
    
    # Total score (300-850 range)
    raw_score = uoo_score + verification_score + revenue_score + age_score
    credit_score = int(300 + raw_score)  # Minimum 300
    
    # Determine credit tier
    if credit_score >= 750:
        tier = "excellent"
        max_loan = 50000
    elif credit_score >= 700:
        tier = "good"
        max_loan = 25000
    elif credit_score >= 650:
        tier = "fair"
        max_loan = 10000
    elif credit_score >= 600:
        tier = "poor"
        max_loan = 5000
    else:
        tier = "very_poor"
        max_loan = 1000
    
    return {
        "ok": True,
        "username": username,
        "credit_score": credit_score,
        "tier": tier,
        "max_loan_amount": max_loan,
        "components": {
            "uoo": {"score": round(uoo_score, 1), "weight": "40%", "value": total_uoo},
            "verification_rate": {"score": round(verification_score, 1), "weight": "30%", "value": verification_rate},
            "revenue": {"score": round(revenue_score, 1), "weight": "20%", "value": revenue},
            "account_age": {"score": round(age_score, 1), "weight": "10%", "value": account_age_days}
        },
        "generated_at": now_iso()
    }


# ============================================================
# P2P LOAN MARKETPLACE
# ============================================================

# In-memory storage (replace with DB)
_LOAN_OFFERS: Dict[str, Dict[str, Any]] = {}
_LOAN_REQUESTS: Dict[str, Dict[str, Any]] = {}
_ACTIVE_LOANS: Dict[str, Dict[str, Any]] = {}

def create_loan_offer(
    lender_username: str,
    amount: float,
    interest_rate: float,
    duration_days: int,
    min_credit_score: int = 600
) -> Dict[str, Any]:
    """
    Lender creates offer to lend capital.
    
    Args:
        lender_username: Username of lender
        amount: Amount willing to lend
        interest_rate: Annual interest rate (e.g., 12.0 for 12%)
        duration_days: Loan duration in days
        min_credit_score: Minimum credit score required
    """
    from log_to_jsonbin import get_user
    
    lender = get_user(lender_username)
    if not lender:
        return {"ok": False, "error": "lender_not_found"}
    
    # Check lender has funds
    aigx_balance = lender.get("yield", {}).get("aigxEarned", 0)
    if aigx_balance < amount:
        return {
            "ok": False,
            "error": "insufficient_funds",
            "available": aigx_balance,
            "requested": amount
        }
    
    offer_id = f"offer_{uuid4().hex[:8]}"
    
    offer = {
        "id": offer_id,
        "lender": lender_username,
        "amount": amount,
        "interest_rate": interest_rate,
        "duration_days": duration_days,
        "min_credit_score": min_credit_score,
        "status": "open",
        "created_at": now_iso(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat() + "Z",
        "matched_to": None
    }
    
    _LOAN_OFFERS[offer_id] = offer
    
    return {
        "ok": True,
        "offer": offer,
        "message": "Loan offer created. Borrowers can now apply."
    }


def create_loan_request(
    borrower_username: str,
    amount: float,
    purpose: str,
    duration_days: int = 30
) -> Dict[str, Any]:
    """
    Borrower requests a loan.
    
    Args:
        borrower_username: Username of borrower
        amount: Amount requested
        purpose: Loan purpose
        duration_days: Desired loan duration
    """
    from log_to_jsonbin import get_user
    
    borrower = get_user(borrower_username)
    if not borrower:
        return {"ok": False, "error": "borrower_not_found"}
    
    # Calculate credit score
    credit_score_result = calculate_credit_score(borrower_username)
    if not credit_score_result.get("ok"):
        return credit_score_result
    
    credit_score = credit_score_result["credit_score"]
    max_loan = credit_score_result["max_loan_amount"]
    
    # Check if amount exceeds max
    if amount > max_loan:
        return {
            "ok": False,
            "error": "amount_exceeds_limit",
            "requested": amount,
            "max_allowed": max_loan,
            "credit_score": credit_score
        }
    
    request_id = f"req_{uuid4().hex[:8]}"
    
    request = {
        "id": request_id,
        "borrower": borrower_username,
        "amount": amount,
        "purpose": purpose,
        "duration_days": duration_days,
        "credit_score": credit_score,
        "credit_tier": credit_score_result["tier"],
        "status": "pending",
        "created_at": now_iso(),
        "matched_offers": []
    }
    
    _LOAN_REQUESTS[request_id] = request
    
    # Auto-match with available offers
    matched_offers = match_loan_offers(request_id)
    
    return {
        "ok": True,
        "request": request,
        "matched_offers": matched_offers,
        "message": f"Loan request created. {len(matched_offers)} potential lenders found."
    }


def match_loan_offers(request_id: str) -> List[Dict[str, Any]]:
    """
    Match loan request with available offers.
    """
    request = _LOAN_REQUESTS.get(request_id)
    if not request:
        return []
    
    borrower_credit = request["credit_score"]
    requested_amount = request["amount"]
    
    matched = []
    
    for offer_id, offer in _LOAN_OFFERS.items():
        if offer["status"] != "open":
            continue
        
        # Check credit score requirement
        if borrower_credit < offer["min_credit_score"]:
            continue
        
        # Check amount availability
        if offer["amount"] < requested_amount:
            continue
        
        matched.append({
            "offer_id": offer_id,
            "lender": offer["lender"],
            "amount": offer["amount"],
            "interest_rate": offer["interest_rate"],
            "duration_days": offer["duration_days"]
        })
    
    # Sort by best interest rate
    matched.sort(key=lambda x: x["interest_rate"])
    
    return matched


def accept_loan_offer(
    request_id: str,
    offer_id: str
) -> Dict[str, Any]:
    """
    Borrower accepts a loan offer.
    
    Creates active loan and transfers funds.
    """
    request = _LOAN_REQUESTS.get(request_id)
    offer = _LOAN_OFFERS.get(offer_id)
    
    if not request or not offer:
        return {"ok": False, "error": "request_or_offer_not_found"}
    
    if request["status"] != "pending":
        return {"ok": False, "error": "request_not_pending"}
    
    if offer["status"] != "open":
        return {"ok": False, "error": "offer_not_available"}
    
    # Create active loan
    loan_id = f"loan_{uuid4().hex[:8]}"
    
    # Calculate repayment amount (simple interest)
    principal = request["amount"]
    annual_rate = offer["interest_rate"] / 100
    days = offer["duration_days"]
    interest = principal * annual_rate * (days / 365)
    total_repayment = principal + interest
    
    # Calculate AiGentsy fee (2.5%)
    aigentsy_fee = principal * 0.025
    net_to_borrower = principal - aigentsy_fee
    
    loan = {
        "id": loan_id,
        "request_id": request_id,
        "offer_id": offer_id,
        "lender": offer["lender"],
        "borrower": request["borrower"],
        "principal": principal,
        "interest_rate": offer["interest_rate"],
        "interest_amount": round(interest, 2),
        "total_repayment": round(total_repayment, 2),
        "aigentsy_fee": round(aigentsy_fee, 2),
        "net_to_borrower": round(net_to_borrower, 2),
        "duration_days": offer["duration_days"],
        "status": "active",
        "disbursed_at": now_iso(),
        "due_at": (datetime.now(timezone.utc) + timedelta(days=offer["duration_days"])).isoformat() + "Z",
        "repaid_amount": 0.0,
        "remaining_balance": round(total_repayment, 2),
        "payment_history": []
    }
    
    _ACTIVE_LOANS[loan_id] = loan
    
    # Update request and offer status
    request["status"] = "funded"
    request["loan_id"] = loan_id
    offer["status"] = "matched"
    offer["matched_to"] = request_id
    offer["loan_id"] = loan_id
    
    # TODO: Transfer funds (deduct from lender, credit to borrower)
    
    return {
        "ok": True,
        "loan": loan,
        "message": f"Loan activated. ${net_to_borrower} disbursed to borrower."
    }


# ============================================================
# LOAN REPAYMENT
# ============================================================

def make_loan_payment(
    loan_id: str,
    payment_amount: float
) -> Dict[str, Any]:
    """
    Make payment toward loan.
    """
    loan = _ACTIVE_LOANS.get(loan_id)
    if not loan:
        return {"ok": False, "error": "loan_not_found"}
    
    if loan["status"] != "active":
        return {"ok": False, "error": "loan_not_active"}
    
    remaining = loan["remaining_balance"]
    
    if payment_amount > remaining:
        payment_amount = remaining
    
    # Record payment
    payment = {
        "amount": payment_amount,
        "paid_at": now_iso(),
        "remaining_after": round(remaining - payment_amount, 2)
    }
    
    loan["payment_history"].append(payment)
    loan["repaid_amount"] += payment_amount
    loan["remaining_balance"] = round(remaining - payment_amount, 2)
    
    # Check if fully repaid
    if loan["remaining_balance"] <= 0.01:  # Allow for rounding
        loan["status"] = "repaid"
        loan["repaid_at"] = now_iso()
    
    return {
        "ok": True,
        "payment": payment,
        "remaining_balance": loan["remaining_balance"],
        "status": loan["status"]
    }


def auto_repay_from_earnings(
    username: str,
    earnings_amount: float,
    repayment_percentage: float = 0.5
) -> Dict[str, Any]:
    """
    Auto-repay loans from earnings.
    
    Args:
        username: Borrower username
        earnings_amount: Amount earned
        repayment_percentage: Percentage to allocate (default 50%)
    """
    # Find active loans for user
    user_loans = [
        loan for loan in _ACTIVE_LOANS.values()
        if loan["borrower"] == username and loan["status"] == "active"
    ]
    
    if not user_loans:
        return {"ok": True, "message": "No active loans", "repaid": 0}
    
    # Calculate repayment amount
    repayment_amount = earnings_amount * repayment_percentage
    
    total_repaid = 0
    repayments = []
    
    # Repay oldest loan first
    user_loans.sort(key=lambda x: x["disbursed_at"])
    
    for loan in user_loans:
        if repayment_amount <= 0:
            break
        
        # Pay toward this loan
        payment = min(repayment_amount, loan["remaining_balance"])
        
        result = make_loan_payment(loan["id"], payment)
        
        if result.get("ok"):
            total_repaid += payment
            repayment_amount -= payment
            
            repayments.append({
                "loan_id": loan["id"],
                "amount": payment,
                "remaining": result["remaining_balance"]
            })
    
    return {
        "ok": True,
        "total_repaid": round(total_repaid, 2),
        "repayments": repayments,
        "earnings_allocated": round(total_repaid, 2)
    }


# ============================================================
# LOAN QUERIES
# ============================================================

def get_active_loans(username: str, role: str = "borrower") -> Dict[str, Any]:
    """
    Get active loans for a user.
    
    Args:
        username: User to query
        role: "borrower" or "lender"
    """
    if role == "borrower":
        loans = [l for l in _ACTIVE_LOANS.values() if l["borrower"] == username]
    else:
        loans = [l for l in _ACTIVE_LOANS.values() if l["lender"] == username]
    
    active = [l for l in loans if l["status"] == "active"]
    
    total_borrowed = sum(l["principal"] for l in active) if role == "borrower" else 0
    total_lent = sum(l["principal"] for l in active) if role == "lender" else 0
    total_owed = sum(l["remaining_balance"] for l in active) if role == "borrower" else 0
    total_owed_to_you = sum(l["remaining_balance"] for l in active) if role == "lender" else 0
    
    return {
        "ok": True,
        "username": username,
        "role": role,
        "active_loans": active,
        "count": len(active),
        "total_borrowed": round(total_borrowed, 2) if role == "borrower" else 0,
        "total_lent": round(total_lent, 2) if role == "lender" else 0,
        "total_owed": round(total_owed, 2) if role == "borrower" else 0,
        "total_owed_to_you": round(total_owed_to_you, 2) if role == "lender" else 0
    }


def get_loan_history(username: str) -> Dict[str, Any]:
    """Get complete loan history for user."""
    borrower_loans = [l for l in _ACTIVE_LOANS.values() if l["borrower"] == username]
    lender_loans = [l for l in _ACTIVE_LOANS.values() if l["lender"] == username]
    
    return {
        "ok": True,
        "username": username,
        "as_borrower": {
            "total_loans": len(borrower_loans),
            "total_borrowed": sum(l["principal"] for l in borrower_loans),
            "active": len([l for l in borrower_loans if l["status"] == "active"]),
            "repaid": len([l for l in borrower_loans if l["status"] == "repaid"]),
            "loans": borrower_loans
        },
        "as_lender": {
            "total_loans": len(lender_loans),
            "total_lent": sum(l["principal"] for l in lender_loans),
            "active": len([l for l in lender_loans if l["status"] == "active"]),
            "repaid": len([l for l in lender_loans if l["status"] == "repaid"]),
            "loans": lender_loans
        }
    }


def list_available_offers(min_amount: float = 0, max_interest: float = 100) -> Dict[str, Any]:
    """List all available loan offers."""
    offers = [
        o for o in _LOAN_OFFERS.values()
        if o["status"] == "open" and o["amount"] >= min_amount and o["interest_rate"] <= max_interest
    ]
    
    # Sort by best interest rate
    offers.sort(key=lambda x: x["interest_rate"])
    
    return {
        "ok": True,
        "offers": offers,
        "count": len(offers),
        "total_capital_available": sum(o["amount"] for o in offers)
    }
