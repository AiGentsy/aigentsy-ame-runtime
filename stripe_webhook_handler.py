import os
import stripe
from fastapi import Request, HTTPException
from datetime import datetime, timezone

# Import AIGx helpers
from aigx_config import (
    calculate_aigx_from_transaction,
    calculate_user_tier,
    check_milestone_reward,
    get_platform_fee,
    AIGX_CONFIG
)

# Import user data functions
from log_to_jsonbin import get_user
from log_to_jsonbin_merged import (
    log_agent_update,
    append_intent_ledger
)

from log_to_jsonbin import get_user as get_user_fallback

# Load Stripe secrets
STRIPE_SECRET = os.getenv("STRIPE_SECRET")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# Only configure Stripe if secret exists
if STRIPE_SECRET:
    stripe.api_key = STRIPE_SECRET
else:
    print("⚠️ Stripe secret key not found — webhook handler is inactive.")

async def handle_stripe_webhook(request: Request):
    """
    Handle Stripe webhook events.
    Primary event: payment_intent.succeeded (when customer pays)
    Awards AIGx based on transaction amount, user tier, and early adopter status.
    """
    if not STRIPE_SECRET or not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Stripe not configured.")
    
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature.")
    
    event_type = event.get("type")
    print(f"🔔 Received Stripe event: {event_type}")
    
    # ============================================================
    # PAYMENT SUCCEEDED - AWARD AIGX
    # ============================================================
    if event_type == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        
        try:
            result = await process_payment_success(payment_intent)
            return {"status": "ok", "processed": True, "result": result}
        except Exception as e:
            print(f"❌ Error processing payment: {e}")
            return {"status": "error", "error": str(e)}
    
    # ============================================================
    # CHECKOUT SESSION COMPLETED (Optional - for subscription setup)
    # ============================================================
    elif event_type == "checkout.session.completed":
        session = event["data"]["object"]
        print(f"✅ Checkout session completed: {session.get('id')}")
        # Handle subscription setup if needed in future
        return {"status": "ok", "processed": False, "note": "Checkout session logged"}
    
    # ============================================================
    # OTHER EVENTS (Log but don't process)
    # ============================================================
    else:
        print(f"ℹ️ Unhandled event type: {event_type}")
        return {"status": "ok", "processed": False, "note": "Event logged"}


async def process_payment_success(payment_intent: dict) -> dict:
    """
    Process a successful payment and award AIGx.
    
    Steps:
    1. Extract payment details (amount, username from metadata)
    2. Get user data (tier, early adopter multiplier, lifetime revenue)
    3. Calculate AIGx earned
    4. Check for milestone rewards
    5. Check for tier upgrade
    6. Update user record
    7. Log to ownership ledger
    
    Args:
        payment_intent: Stripe PaymentIntent object
        
    Returns:
        dict: Processing results
    """
    
    # ============================================================
    # STEP 1: EXTRACT PAYMENT DETAILS
    # ============================================================
    
    amount_cents = payment_intent.get("amount", 0)
    amount_usd = amount_cents / 100.0  # Convert cents to dollars
    currency = payment_intent.get("currency", "usd").upper()
    payment_id = payment_intent.get("id")
    
    # Get username from metadata (must be set when creating payment intent)
    metadata = payment_intent.get("metadata", {})
    username = metadata.get("username") or metadata.get("agent_username")
    
    if not username:
        print(f"⚠️ No username in payment metadata for {payment_id}")
        return {
            "ok": False,
            "error": "No username in payment metadata",
            "payment_id": payment_id
        }
    
    print(f"💰 Processing payment: ${amount_usd} from {username}")
    
    # ============================================================
    # STEP 2: GET USER DATA
    # ============================================================
    
    user = get_user(username)
    if not user:
        user = get_user_fallback(username)
    
    if not user:
        print(f"❌ User not found: {username}")
        return {
            "ok": False,
            "error": "User not found",
            "username": username
        }
    
    # Extract user's earning parameters
    current_tier = user.get("currentTier", "free")
    early_adopter_multiplier = user.get("aigxMultiplier", 1.0)
    previous_revenue = user.get("lifetimeRevenue", 0.0)
    
    print(f"👤 User: {username} | Tier: {current_tier} | Multiplier: {early_adopter_multiplier}x | Previous Revenue: ${previous_revenue}")
    
    # ============================================================
    # STEP 3: CALCULATE PLATFORM FEE
    # ============================================================
    
    fee_details = get_platform_fee(amount_usd, current_tier)
    net_to_user = fee_details["net_to_user"]
    
    print(f"💵 Platform fee: ${fee_details['total_fee']} | Net to user: ${net_to_user}")
    
    # ============================================================
    # STEP 4: CALCULATE AIGX EARNED
    # ============================================================
    
    aigx_from_transaction = calculate_aigx_from_transaction(
        amount_usd=amount_usd,
        user_tier=current_tier,
        early_adopter_multiplier=early_adopter_multiplier
    )
    
    print(f"💎 AIGx earned from transaction: {aigx_from_transaction}")
    
    # ============================================================
    # STEP 5: UPDATE LIFETIME REVENUE & CHECK TIER UPGRADE
    # ============================================================
    
    new_lifetime_revenue = previous_revenue + amount_usd
    new_tier = calculate_user_tier(new_lifetime_revenue)
    tier_upgraded = new_tier != current_tier
    
    if tier_upgraded:
        print(f"🎉 TIER UPGRADE: {current_tier} → {new_tier}")
    
    # ============================================================
    # STEP 6: CHECK MILESTONE REWARDS
    # ============================================================
    
    milestone = check_milestone_reward(new_lifetime_revenue, previous_revenue)
    milestone_aigx = milestone["aigx_reward"] if milestone["milestone_hit"] else 0
    
    if milestone["milestone_hit"]:
        print(f"🏆 MILESTONE HIT: {milestone['description']} | Reward: {milestone_aigx} AIGx")
    
    # Check for first sale milestone separately
    first_sale_bonus = 0
    if previous_revenue == 0 and new_lifetime_revenue > 0:
        first_sale_milestone = AIGX_CONFIG["milestones"]["first_sale"]
        first_sale_bonus = first_sale_milestone["aigx_reward"]
        print(f"🎊 FIRST SALE! Bonus: {first_sale_bonus} AIGx")
    
    # ============================================================
    # STEP 7: CALCULATE TOTAL AIGX
    # ============================================================
    
    total_aigx = aigx_from_transaction + milestone_aigx + first_sale_bonus
    
    print(f"💰 Total AIGx to award: {total_aigx} (Transaction: {aigx_from_transaction}, Milestone: {milestone_aigx}, First Sale: {first_sale_bonus})")
    
    # ============================================================
    # STEP 8: UPDATE USER RECORD
    # ============================================================
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Update ownership
    user.setdefault("ownership", {"aigx": 0, "equity": 0, "ledger": []})
    user["ownership"]["aigx"] = user["ownership"].get("aigx", 0) + total_aigx
    
    # Update lifetime revenue
    user["lifetimeRevenue"] = new_lifetime_revenue
    
    # Update tier if upgraded
    if tier_upgraded:
        user["currentTier"] = new_tier
        # Update tier multiplier in earning rate
        tier_config = AIGX_CONFIG["tier_progression"][new_tier]
        user["aigxEarningRate"]["tier_multiplier"] = tier_config["aigx_multiplier"]
        user["aigxEarningRate"]["total_multiplier"] = (
            tier_config["aigx_multiplier"] * early_adopter_multiplier
        )
    
    # ============================================================
    # STEP 9: LOG TO OWNERSHIP LEDGER
    # ============================================================
    
    # Transaction AIGx
    user["ownership"]["ledger"].append({
        "ts": now,
        "amount": aigx_from_transaction,
        "currency": "AIGx",
        "basis": "transaction_revenue",
        "payment_id": payment_id,
        "transaction_amount": amount_usd,
        "tier": current_tier,
        "tier_multiplier": AIGX_CONFIG["tier_progression"][current_tier]["aigx_multiplier"],
        "early_adopter_multiplier": early_adopter_multiplier,
        "total_multiplier": AIGX_CONFIG["tier_progression"][current_tier]["aigx_multiplier"] * early_adopter_multiplier
    })
    
    # First sale bonus
    if first_sale_bonus > 0:
        user["ownership"]["ledger"].append({
            "ts": now,
            "amount": first_sale_bonus,
            "currency": "AIGx",
            "basis": "milestone_first_sale",
            "milestone": "first_sale",
            "payment_id": payment_id
        })
    
    # Milestone bonus
    if milestone_aigx > 0:
        user["ownership"]["ledger"].append({
            "ts": now,
            "amount": milestone_aigx,
            "currency": "AIGx",
            "basis": "milestone_reward",
            "milestone": milestone["milestone_key"],
            "description": milestone["description"],
            "revenue_threshold": new_lifetime_revenue
        })
    
    # Tier upgrade
    if tier_upgraded:
        user["ownership"]["ledger"].append({
            "ts": now,
            "amount": 0,
            "currency": "upgrade",
            "basis": "tier_upgrade",
            "old_tier": current_tier,
            "new_tier": new_tier,
            "revenue_achieved": new_lifetime_revenue
        })
    
    # ============================================================
    # STEP 10: SAVE USER RECORD
    # ============================================================
    
    try:
        log_agent_update(user)
        print(f"✅ User record updated: {username}")
    except Exception as e:
        print(f"❌ Failed to save user record: {e}")
        return {
            "ok": False,
            "error": f"Failed to save user: {str(e)}",
            "username": username
        }
    
    # ============================================================
    # STEP 11: RETURN RESULTS
    # ============================================================
    
    result = {
        "ok": True,
        "username": username,
        "payment_id": payment_id,
        "transaction": {
            "amount_usd": amount_usd,
            "platform_fee": fee_details["total_fee"],
            "net_to_user": net_to_user
        },
        "aigx": {
            "from_transaction": aigx_from_transaction,
            "from_first_sale": first_sale_bonus,
            "from_milestone": milestone_aigx,
            "total_awarded": total_aigx,
            "new_balance": user["ownership"]["aigx"]
        },
        "revenue": {
            "previous": previous_revenue,
            "new": new_lifetime_revenue,
            "increase": amount_usd
        },
        "tier": {
            "previous": current_tier,
            "new": new_tier,
            "upgraded": tier_upgraded
        },
        "milestone": {
            "hit": milestone["milestone_hit"] or first_sale_bonus > 0,
            "description": milestone.get("description") or ("First sale!" if first_sale_bonus > 0 else ""),
            "reward": milestone_aigx + first_sale_bonus
        }
    }
    
    print(f"✅ Payment processed successfully for {username}")
    return result
