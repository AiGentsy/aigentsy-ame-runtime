# === PATCH APPLIED ===
import uuid
from typing import Literal, Optional, List, Dict
from fastapi.responses import StreamingResponse
import asyncio
import hashlib
import hmac
import time as _time
# ============================
# AiGentsy Runtime (main.py)
# Canonical mint + AMG/AL/JV/AIGx/Contacts + Business-in-a-Box rails
# ============================
import os, httpx, uuid, json, hmac, hashlib, csv, io, logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

from revenue_flows import (
    ingest_shopify_order,
    ingest_affiliate_commission,
    ingest_content_cpm,
    ingest_service_payment,
    distribute_staking_returns,
    split_jv_revenue,
    distribute_clone_royalty,
    get_earnings_summary
)
from agent_spending import (
    check_spending_capacity,
    execute_agent_spend,
    agent_to_agent_payment,
    get_spending_summary
)
from fastapi import FastAPI, Request, Body, Path, HTTPException, Header, BackgroundTasks
PLATFORM_FEE = float(os.getenv("PLATFORM_FEE", "0.12"))  # single source of truth
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from venture_builder_agent import get_agent_graph
from log_to_jsonbin_merged import (
    log_agent_update, append_intent_ledger, credit_aigx as credit_aigx_srv,
    log_metaloop, log_autoconnect, log_metabridge, log_metahive
)
# Admin normalize uses the classic module (keep both available)
from log_to_jsonbin import _get as _bin_get, _put as _bin_put, normalize_user_data
# Intent Exchange (upgraded with auction system)
try:
    from intent_exchange_UPGRADED import router as intent_router
except Exception:
    intent_router = None
# ---- App, logging, CORS (single block) ----
import os, logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
# --- internal signing for trusted backend calls ---
def _sign_payload(body_bytes: bytes) -> dict:
    secret = os.getenv("HMAC_SECRET", "")
    if not secret:
        return {}
    ts = str(int(_time.time()))
    sig = hmac.new(secret.encode(), (ts + "." + body_bytes.decode()).encode(), hashlib.sha256).hexdigest()
    return {"X-Ts": ts, "X-Sign": sig}
# Intent Exchange (upgraded with auction system)
try:
    from intent_exchange_UPGRADED import router as intent_router
except Exception:
    intent_router = None

# MetaBridge DealGraph (upgraded with real matching)
try:
    from metabridge_dealgraph_UPGRADED import router as dealgraph_router
except Exception:
    dealgraph_router = None

# R³ Budget Router (upgraded with ROI prediction)
try:
    from r3_router_UPGRADED import router as r3_router
except Exception:
    r3_router = None

from ocl_engine import calculate_ocl_limit, spend_ocl, auto_repay_ocl, expand_ocl_on_poo

# ============ PERFORMANCE BONDS ============
try:
    from performance_bonds import (
        stake_bond,
        return_bond,
        calculate_sla_bonus,
        award_sla_bonus,
        slash_bond,
        calculate_bond_amount
    )
except Exception as e:
    print(f" performance_bonds import failed: {e}")
    async def stake_bond(u, i): return {"ok": False}
    async def return_bond(u, i): return {"ok": False}
    async def award_sla_bonus(u, i): return {"ok": False}
    async def slash_bond(u, i, s): return {"ok": False}
    def calculate_bond_amount(v): return {"amount": 0}

# ============ INSURANCE POOL ============
try:
    from insurance_pool import (
        calculate_insurance_fee,
        collect_insurance,
        get_pool_balance,
        payout_from_pool,
        calculate_dispute_rate,
        calculate_annual_refund,
        issue_annual_refund
    )
except Exception as e:
    print(f" insurance_pool import failed: {e}")
    async def collect_insurance(u, i, v): return {"ok": False, "fee": 0}
    async def get_pool_balance(p): return 0

# ============ AGENT FACTORING ============
try:
    from agent_factoring import (
        request_factoring_advance,
        settle_factoring,
        calculate_factoring_eligibility,
        calculate_factoring_tier,
        calculate_outstanding_factoring
    )
except Exception as e:
    print(f" agent_factoring import failed: {e}")
    async def request_factoring_advance(u, i): return {"ok": False, "net_advance": 0}
    async def settle_factoring(u, i, p): return {"ok": False}

# ============ REPUTATION PRICING (ARM) ============
try:
    from reputation_pricing import (
        calculate_pricing_tier,
        calculate_reputation_price,
        calculate_arm_price_range,
        calculate_dynamic_bid_price,
        update_outcome_score_weighted,
        calculate_pricing_impact,
        PRICING_TIERS
    )
except Exception as e:
    print(f" reputation_pricing import failed: {e}")
    def calculate_pricing_tier(outcome_score: int):
        return {"tier": "novice", "multiplier": 0.70, "outcome_score": outcome_score, "description": "New agent"}
    def calculate_reputation_price(base_price: float, outcome_score: int, apply_guardrails: bool = True):
        return {"base_price": base_price, "adjusted_price": base_price * 0.70, "discount_or_premium": -base_price * 0.30, "tier": "novice", "multiplier": 0.70}
    def calculate_arm_price_range(service_type: str, outcome_score: int, market_demand: float = 1.0):
        return {"recommended_price": 200.0, "pricing_tier": "novice", "reputation_multiplier": 0.70, "price_range": {"min": 180, "max": 220}}
    def calculate_dynamic_bid_price(intent, agent_outcome_score: int, existing_bids=None):
        return {"recommended_bid": 140.0, "adjustment": "standard", "rationale": "Default pricing"}
    def update_outcome_score_weighted(current_score: int, new_outcome_result: str, weight: float = 0.1):
        return current_score + 10
    def calculate_pricing_impact(current_score: int, new_score: int, base_price: float):
        return {"score_change": new_score - current_score, "price_change": 0, "current_tier": "novice", "new_tier": "novice"}
    PRICING_TIERS = {}

# ============ ESCROW LITE (STRIPE) ============
try:
    from escrow_lite import (
        create_payment_intent,
        capture_payment_intent,
        refund_payment_intent,
        auto_capture_on_delivered
    )
except Exception as e:
    print(f" escrow_lite import failed: {e}")
    async def create_payment_intent(a, b, i, m): return {"ok": False}
    async def capture_payment_intent(p): return {"ok": False}
    async def auto_capture_on_delivered(i): return {"ok": False}

# ============ MULTI-CURRENCY ENGINE ============
try:
    from currency_engine import (
        convert_currency,
        get_user_balance,
        credit_currency,
        debit_currency,
        transfer_with_conversion,
        fetch_live_rates,
        SUPPORTED_CURRENCIES
    )
except Exception as e:
    print(f" currency_engine import failed: {e}")
    def convert_currency(a, f, t, r=None): return {"ok": False, "error": "not_available"}
    def get_user_balance(u, c="USD"): return {"ok": False, "error": "not_available"}
    def credit_currency(u, a, c, r=""): return {"ok": False, "error": "not_available"}
    def debit_currency(u, a, c, r=""): return {"ok": False, "error": "not_available"}
    def transfer_with_conversion(f, t, a, fc, tc, r=""): return {"ok": False, "error": "not_available"}
    async def fetch_live_rates(): return {}
    SUPPORTED_CURRENCIES = ["USD", "EUR", "GBP", "AIGx", "CREDITS"]

# ============ BATCH PAYMENT PROCESSING ============
try:
    from batch_payments import (
        create_batch_payment,
        execute_batch_payment,
        generate_bulk_invoices,
        batch_revenue_recognition,
        schedule_recurring_payment,
        generate_payment_report,
        retry_failed_payments
    )
except Exception as e:
    print(f" batch_payments import failed: {e}")
    async def create_batch_payment(p, b=None, d=""): return {"ok": False}
    async def execute_batch_payment(b, u, c): return {"ok": False}
    async def generate_bulk_invoices(i, b=None): return {"ok": False}
    async def batch_revenue_recognition(i, u, p=0.05): return {"ok": False}
    async def schedule_recurring_payment(p, s="monthly", d=None): return {"ok": False}
    def generate_payment_report(b, f="summary"): return {"ok": False}
    async def retry_failed_payments(b, u, c): return {"ok": False}

# ============ AUTOMATED TAX REPORTING ============
try:
    from tax_reporting import (
        calculate_annual_earnings,
        generate_1099_nec,
        calculate_estimated_taxes,
        generate_quarterly_report,
        calculate_vat_liability,
        generate_annual_tax_summary,
        batch_generate_1099s,
        export_tax_csv
    )
except Exception as e:
    print(f" tax_reporting import failed: {e}")
    def calculate_annual_earnings(u, y=None): return {"ok": False}
    def generate_1099_nec(u, y=None, p=None): return {"ok": False}
    def calculate_estimated_taxes(e, r="US"): return {"ok": False}
    def generate_quarterly_report(u, y, q): return {"ok": False}
    def calculate_vat_liability(u, y, q=None): return {"ok": False}
    def generate_annual_tax_summary(u, y=None): return {"ok": False}
    def batch_generate_1099s(u, y=None): return {"ok": False}
    def export_tax_csv(u, y=None): return {"ok": False}

# ============ R³ AUTOPILOT (KEEP-ME-GROWING) ============
try:
    from r3_autopilot import (
        create_autopilot_strategy,
        calculate_budget_allocation,
        predict_roi,
        execute_autopilot_spend,
        rebalance_autopilot,
        get_autopilot_recommendations,
        AUTOPILOT_TIERS,
        CHANNELS
    )
except Exception as e:
    print(f" r3_autopilot import failed: {e}")
    def create_autopilot_strategy(u, t="balanced", m=500): return {"ok": False}
    def calculate_budget_allocation(b, t, h=None): return {"ok": False}
    def predict_roi(c, s, h=None): return {"ok": False}
    def execute_autopilot_spend(s, u): return {"ok": False}
    def rebalance_autopilot(s, a=None): return {"ok": False}
    def get_autopilot_recommendations(u, c=None): return {"ok": False}
    AUTOPILOT_TIERS = {}
    CHANNELS = {}

# ============ AUTONOMOUS LOGIC UPGRADES ============
try:
    from autonomous_upgrades import (
        create_logic_variant,
        create_ab_test,
        assign_to_test_group,
        record_test_outcome,
        analyze_ab_test,
        deploy_logic_upgrade,
        rollback_logic_upgrade,
        get_active_tests,
        suggest_next_upgrade,
        UPGRADE_TYPES
    )
except Exception as e:
    print(f" autonomous_upgrades import failed: {e}")
    def create_logic_variant(u, b, m=0.2): return {"ok": False}
    def create_ab_test(u, c, t=14, s=100): return {"ok": False}
    def assign_to_test_group(a, agent_id): return "control"
    def record_test_outcome(a, g, m): return {"ok": False}
    def analyze_ab_test(a, m=30): return {"ok": False}
    def deploy_logic_upgrade(a, u): return {"ok": False}
    def rollback_logic_upgrade(u, users, r=None): return {"ok": False}
    def get_active_tests(t): return []
    def suggest_next_upgrade(u, e): return {"ok": False}
    UPGRADE_TYPES = {}

# ============ DARK-POOL PERFORMANCE AUCTIONS ============
try:
    from dark_pool import (
        anonymize_agent,
        get_reputation_tier,
        create_dark_pool_auction,
        submit_dark_pool_bid,
        calculate_bid_score,
        close_dark_pool_auction,
        reveal_agent_identity,
        calculate_dark_pool_metrics,
        get_agent_dark_pool_history,
        REPUTATION_TIERS
    )
except Exception as e:
    print(f"⚠️ dark_pool import failed: {e}")
    def anonymize_agent(a, auc): return "agent_anonymous"
    def get_reputation_tier(s): return {"tier": "silver", "badge": "🥈"}
    def create_dark_pool_auction(i, m="silver", d=24, r=True): return {"ok": False}
    def submit_dark_pool_bid(auc, u, b, d, p=""): return {"ok": False}
    def calculate_bid_score(b, w=None): return 0.5
    def close_dark_pool_auction(auc, m="reputation_weighted_price"): return {"ok": False}
    def reveal_agent_identity(auc, anon, req): return {"ok": False}
    def calculate_dark_pool_metrics(aucs): return {"ok": False}
    def get_agent_dark_pool_history(a, aucs): return {"ok": False}
    REPUTATION_TIERS = {}
    
app = FastAPI()


async def auto_bid_background():
    """Runs in background forever"""
    base_url = os.getenv("SELF_URL", "http://localhost:8000")
    await asyncio.sleep(60)
    
    while True:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.post(f"{base_url}/intent/auto_bid")
                result = r.json()
                print(f"Auto-bid: {result.get('count', 0)} bids submitted")
        except Exception as e:
            print(f"Auto-bid error: {e}")
        
        await asyncio.sleep(30)

@app.on_event("startup")
async def startup_event():
    """Start background tasks"""
    asyncio.create_task(auto_bid_background())
    print("Auto-bid background task started")

logger = logging.getLogger("aigentsy")
@app.on_event("startup")
async def startup_event():
    """Start background tasks"""
    asyncio.create_task(auto_bid_background())
    print("Auto-bid background task started")
# ========== END BLOCK ==========
async def auto_release_escrows_job():
    """
    Runs every 6 hours
    Auto-releases escrows after 7-day timeout with no disputes
    """
    while True:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                users = await _load_users(client)
                
                for user in users:
                    for intent in user.get("intents", []):
                        if intent.get("status") == "DELIVERED" and \
                           intent.get("payment_intent_id") and \
                           not intent.get("payment_captured"):
                            
                            # Check timeout
                            result = await auto_timeout_release(intent, timeout_days=7)
                            
                            if result.get("ok"):
                                print(f"Auto-released escrow for intent {intent.get('id')}")
                
                await _save_users(client, users)
        except Exception as e:
            print(f" Auto-release job error: {e}")
        
        # Run every 6 hours
        await asyncio.sleep(6 * 3600)

@app.on_event("startup")
async def startup_event():
    """Start background tasks"""
    asyncio.create_task(auto_bid_background())
    asyncio.create_task(auto_release_escrows_job())  # ADD THIS
    print("Background tasks started: auto-bid, auto-release")
    
logger = logging.getLogger("aigentsy")
logging.basicConfig(level=logging.DEBUG if os.getenv("VERBOSE_LOGGING") else logging.INFO)


ALLOW_ORIGINS = [
    os.getenv("FRONTEND_ORIGIN", "https://aigentsy.com"),
    "https://aigentsy.com",
    "https://www.aigentsy.com",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,   # explicit allowed sites
    allow_credentials=False,       # set True only if you use cookies/auth headers
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,
)

@app.get("/healthz")
async def healthz():
    return {"ok": True, "ts": datetime.now(timezone.utc).isoformat()}

# ========== ADD THESE 3 ENDPOINTS HERE ==========
@app.get("/revenue/summary")
async def revenue_summary_get(username: str):
    """Frontend expects this endpoint"""
    result = get_earnings_summary(username)
    return result

@app.get("/score/outcome") 
async def get_outcome_score_query(username: str):
    """Frontend polls this"""
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        u = next((x for x in users if _uname(x) == username), None)
        if not u:
            return {"error": "user not found"}
        return {"ok": True, "score": int(u.get("outcomeScore", 0))}

@app.get("/metrics/summary")
async def metrics_summary_get(username: str):
    """Compact snapshot for dashboard"""
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        u = next((x for x in users if _uname(x) == username), None)
        if not u:
            return {"error": "user not found"}
        
        return {
            "ok": True,
            "proposals": len(u.get("proposals", [])),
            "intents": len(u.get("intents", [])),
            "quotes": len(u.get("quotes", [])),
            "escrow": len([e for e in u.get("escrow", []) if e.get("status") == "held"]),
            "aigx": float(u.get("yield", {}).get("aigxEarned", 0))
        }
# ========== END BLOCK ==========

# ---- Env ----
JSONBIN_URL     = os.getenv("JSONBIN_URL")
JSONBIN_SECRET  = os.getenv("JSONBIN_SECRET")
PROPOSAL_WEBHOOK_URL = os.getenv("PROPOSAL_WEBHOOK_URL")  # used by /contacts/send webhook
POL_SECRET      = os.getenv("POL_SECRET", "dev-secret")   # for signed Offer Links
CANONICAL_SCHEMA_VERSION = "v1.1"  # bumped
SELF_URL        = os.getenv("SELF_URL")  # optional, e.g. https://your-service.onrender.com

# ---- Agent Graph (AiGent Venture; MetaUpgrade25+26) ----
agent_graph = get_agent_graph()

# ============================
# Helpers
# ============================
def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _id(pfx: str) -> str:
    return f"{pfx}_{uuid.uuid4().hex[:10]}"

def _hmac(payload: str, secret: str) -> str:
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()

def _empty_kits() -> Dict[str, Any]:
    return {
        "universal": {"unlocked": False},
        "growth": {"unlocked": False},
        "legal": {"unlocked": False},
        "sdk": {"unlocked": False},
        "branding": {"unlocked": False},
        "marketing": {"unlocked": False},
        "social": {"unlocked": False},
    }

def _empty_licenses():
    return {"sdk": False, "vault": False, "remix": False, "clone": False, "aigx": False}

# ---- Fees ----

def _platform_fee_rate(u: dict) -> float:
    """Resolve take-rate in order: per-user override -> env PLATFORM_FEE -> 0.05 default."""
    return float((u.get("fees") or {}).get("take_rate") or PLATFORM_FEE or 0.05)


def _ratelimit(u, key: str, per_min: int = 30):
    now = datetime.utcnow()
    window_start = (now - timedelta(minutes=1)).isoformat()
    rl = u.setdefault("rate", {}).setdefault(key, [])
    rl[:] = [t for t in rl if t >= window_start]
    if len(rl) >= per_min:
        return False, len(rl)
    rl.append(_now())
    return True, len(rl)

COMPANY_TYPE_PRESETS = {
    "legal":     {"meta_role": "CLO", "traits_add": ["legal"],     "kits_unlock": ["universal"],              "flags": {"vaultAccess": True}},
    "social":    {"meta_role": "CMO", "traits_add": ["marketing"], "kits_unlock": ["universal"],              "flags": {"vaultAccess": True}},
    "saas":      {"meta_role": "CTO", "traits_add": [],            "kits_unlock": ["universal","sdk"],        "flags": {"vaultAccess": True, "sdkAccess_eligible": True}},
    "marketing": {"meta_role": "CMO", "traits_add": ["marketing"], "kits_unlock": ["universal","branding"],   "flags": {"vaultAccess": True}},
    "custom":    {"meta_role": "Founder", "traits_add": ["custom"],"kits_unlock": ["universal"],              "flags": {"vaultAccess": True}},
    "general":   {"meta_role": "Founder", "traits_add": [],        "kits_unlock": ["universal"],              "flags": {"vaultAccess": True}},
}

# ===== Monetization / payouts config =====
PAYOUT_MIN = float(os.getenv("PAYOUT_MIN", "10"))                  # $10 minimum
PAYOUT_HOLDBACK_DAYS = int(os.getenv("PAYOUT_HOLDBACK_DAYS", "7")) # 7-day eligibility window
REFERRAL_BOUNTY = float(os.getenv("REFERRAL_BOUNTY", "1.0"))       # 1 AIGx for a signup referral

# Treat 1 AIGx == 1 USD for accounting display (you can change later).
def _as_usd(entry: Dict[str, Any]) -> float:
    amt = float(entry.get("amount", 0))
    cur = (entry.get("currency") or "USD").upper()
    # If ledger is in AIGx treat 1:1 to USD for money tab. Tune via FX later if needed.
    return amt if cur in ("USD", "AIGX") else amt

def _days_ago(ts_iso: str) -> int:
    try:
        then = datetime.fromisoformat(ts_iso.replace("Z","+00:00"))
        return (datetime.now(timezone.utc) - then.astimezone(timezone.utc)).days
    except Exception:
        return 9999

def _money_summary(u: Dict[str, Any]) -> Dict[str, Any]:
    led = (u.get("ownership") or {}).get("ledger", [])
    # Gross money events that increase balance
    earn_bases = {"revenue","partner","affiliate","bounty","task","uplift","royalty"}
    gross_all = sum(_as_usd(x) for x in led if (x.get("basis") in earn_bases))
    # Eligible (older than holdback)
    eligible_gross = sum(_as_usd(x) for x in led
                         if (x.get("basis") in earn_bases and _days_ago(x.get("ts","")) >= PAYOUT_HOLDBACK_DAYS))
    # Platform fees already posted as negative ledger lines (if you adopt patch below)
    posted_fees = sum(_as_usd(x) for x in led if x.get("basis") == "platform_fee")
    # Final payouts executed (negative)
    paid_out = sum(_as_usd(x) for x in led if x.get("basis") == "payout")
    # Pending payout requests (not yet ledgered)
    pending_req = sum(float(p.get("amount",0)) for p in u.get("payouts", []) if p.get("status") in ("requested","queued"))

    # If you *haven't* posted platform_fee lines yet, uncomment the next line to estimate fees:
    # posted_fees = - eligible_gross * PLATFORM_FEE

    available_gross = eligible_gross + posted_fees + paid_out  # posted_fees is negative, paid_out negative
    available = max(0.0, available_gross - pending_req)

    return {
        "gross_lifetime": round(gross_all, 2),
        "eligible_gross": round(eligible_gross, 2),
        "fees_posted": round(posted_fees, 2),
        "paid_out": round(paid_out, 2),
        "pending_requests": round(pending_req, 2),
        "available": round(available, 2),
        "holdback_days": PAYOUT_HOLDBACK_DAYS,
    }

def make_canonical_record(username: str, company_type: str = "general", referral: str = "origin/hero") -> Dict[str, Any]:
    preset = COMPANY_TYPE_PRESETS.get(company_type, COMPANY_TYPE_PRESETS["general"])
    kits = _empty_kits()
    for k in preset["kits_unlock"]:
        kits[k]["unlocked"] = True

    runtime_flags = {
        "flagged": False,
        "eligibleForAudit": True,
        "needsReview": False,
        "vaultAccess": False,
        "remixUnlocked": False,
        "cloneLicenseUnlocked": False,
        "sdkAccess_eligible": False,
        "autonomyLevel": "AL1",
    }
    runtime_flags.update(preset["flags"])

    traits = sorted(list({*["founder", "autonomous", "aigentsy"], *preset["traits_add"]}))

    user = {
        "schemaVersion": CANONICAL_SCHEMA_VERSION,
        "id": str(uuid.uuid4()),
        "ventureID": f"aigent0-{username}",
        "consent": {"agreed": True, "username": username, "timestamp": _now()},
        "username": username,
        "companyType": company_type,
        "role": preset["meta_role"],
        "meta_role": preset["meta_role"],
        "traits": traits,
        "kits": kits,
        "licenses": _empty_licenses(),
        "runtimeFlags": runtime_flags,
        "walletAddress": "0x0",
        "wallet": {"aigx": 0, "staked": 0},
        "yield": {
            "autoStake": False, "aigxEarned": 0, "vaultYield": 0, "remixYield": 0,
            "aigxAttributedTo": [], "aigxEarnedEnabled": True
        },
        "remix": {"remixCount": 0, "remixCredits": 1000, "lineageDepth": 0, "royaltyTerms": "Standard 30%"},
        "cloneLineage": [],
        "realm": {"name": "Realm 101 — Strategic Expansion", "joinedAt": _now()},
        "metaVenture": {"ventureHive": "Autonomous Launch", "ventureRole": preset["meta_role"], "ventureStatus": "Pending", "ventureID": f"MV-{int(datetime.now().timestamp())}"},
        "mirror": {"mirroredInRealms": ["Realm 101 — Strategic Expansion"], "mirrorIntegrity": "Verified", "sentinelAlert": False},
        "proposal": {"personaHint": "", "proposalsSent": [], "proposalsReceived": []},
        "proposals": [],
        "transactions": {"unlocks": [], "yieldEvents": [], "referralEvents": [], "outreachEvents": []},
        "offerings": {"products": [], "services": [], "pricing": [], "description": ""},
        "packaging": {"kits_sent": [], "proposals": [], "custom_files": [], "active": False},
        "automatch": {"status": "pending", "lastMatchResult": None, "matchReady": True},
        "metaloop": {"enabled": True, "lastMatchCheck": None, "proposalHistory": []},
        "metabridge": {"active": True, "lastBridge": None, "bridgeCount": 0},
        "earningsEnabled": True,
        "listingStatus": "Active",
        "protocolStatus": "Bound",
        "tethered": True,
        "runtimeURL": "https://aigentsy.com/agents/aigent0.html",
        "referral": referral,
        "mintTime": _now(),
        "created": _now(),
        "amg": {"apps": [], "capabilities": [], "lastSync": None},
        "ownership": {"aigx": 0, "royalties": 0, "ledger": []},
        "jvMesh": [],
        "contacts": {"sources": [], "counts": {}, "lastSync": None},  # ✅ COMMA ADDED
        "ocl": {
            "limit": 10.0,
            "used": 0.0,
            "available": 10.0,
            "poo_multiplier": 5.0,
            "max_limit": 200.0,
            "last_updated": _now(),
            "auto_repay": True,
            "repayment_schedule": [],
            "expansion_events": []
        }
    }
    
    user["runtimeFlags"]["vaultAccess"] = user["runtimeFlags"]["vaultAccess"] or user["kits"]["universal"]["unlocked"]
    return user

def _today_key():
    return datetime.utcnow().strftime("%Y-%m-%d")

def _current_spend(u):
    s = u.setdefault("spend", {})
    day = _today_key()
    s.setdefault(day, 0.0)
    return s, day

def _can_spend(u, amt: float) -> bool:
    guard = (u.get("policy", {}) or {}).get("guardrails", {}) or {}
    cap = float(guard.get("dailyBudget", 0))
    s, day = _current_spend(u)
    return (s[day] + amt) <= cap if cap else True

def _spend(u, amt: float, basis="media_spend", ref=None):
    s, day = _current_spend(u)
    s[day] = round(s[day] + amt, 2)
    u.setdefault("ownership", {}).setdefault("ledger", []).append(
        {"ts": _now(), "amount": -float(amt), "currency": "USD", "basis": basis, "ref": ref}
    )

def normalize_user_record(raw: Dict[str, Any]) -> Dict[str, Any]:
    if not raw: return {}
    username = raw.get("username") or raw.get("consent", {}).get("username") or ""
    kits = raw.get("kits") or _empty_kits()
    licenses = raw.get("licenses") or _empty_licenses()
    rf = raw.get("runtimeFlags", {})
    vault_access = bool(rf.get("vaultAccess") or raw.get("vaultAccess") or licenses.get("vault") or kits.get("universal", {}).get("unlocked"))
    remix_unlocked = bool(rf.get("remixUnlocked") or raw.get("remixUnlocked") or licenses.get("remix"))
    clone_unlocked = bool(rf.get("cloneLicenseUnlocked") or raw.get("cloneLicenseUnlocked") or licenses.get("clone"))
    sdk_eligible = bool(rf.get("sdkAccess_eligible") or raw.get("sdkAccess_eligible") or raw.get("sdkAccess") or licenses.get("sdk"))

    # proposals: flatten legacy
    flat_proposals = raw.get("proposals") or []
    if not flat_proposals and "proposal" in raw:
        sent = raw["proposal"].get("proposalsSent", [])
        received = raw["proposal"].get("proposalsReceived", [])
        flat_proposals = [*sent, *received]

    raw.setdefault("amg", {"apps": [], "capabilities": [], "lastSync": None})
    raw.setdefault("ownership", {"aigx": 0, "royalties": 0, "ledger": []})
    raw.setdefault("jvMesh", [])
    raw.setdefault("contacts", {"sources": [], "counts": {}, "lastSync": None})

    normalized = {
        **raw,
        "schemaVersion": raw.get("schemaVersion") or CANONICAL_SCHEMA_VERSION,
        "username": username,
        "kits": kits,
        "licenses": licenses,
        "runtimeFlags": {
            **{"flagged": False, "eligibleForAudit": True, "needsReview": False, "autonomyLevel": raw.get("runtimeFlags", {}).get("autonomyLevel", "AL1")},
            **rf,
            "vaultAccess": vault_access,
            "remixUnlocked": remix_unlocked,
            "cloneLicenseUnlocked": clone_unlocked,
            "sdkAccess_eligible": sdk_eligible
        },
        "proposals": flat_proposals,
    }
    return normalized

async def _jsonbin_get(client: httpx.AsyncClient) -> Dict[str, Any]:
    r = await client.get(JSONBIN_URL, headers={"X-Master-Key": JSONBIN_SECRET})
    r.raise_for_status()
    return r.json()

async def _jsonbin_put(client: httpx.AsyncClient, users: list) -> None:
    r = await client.put(JSONBIN_URL,
                         headers={"X-Master-Key": JSONBIN_SECRET, "Content-Type": "application/json"},
                         json={"record": users})
    r.raise_for_status()

def _upsert(users: list, record: Dict[str, Any]) -> list:
    uname = record.get("username") or record.get("consent", {}).get("username")
    rid = record.get("id")
    replaced = False
    for i, u in enumerate(users):
        if u.get("id") == rid or (uname and (u.get("username") == uname or u.get("consent", {}).get("username") == uname)):
            users[i] = record
            replaced = True
            break
    if not replaced:
        users.append(record)
    return users

# --- helpers for new rails ---
async def _load_users(client: httpx.AsyncClient) -> List[Dict[str, Any]]:
    data = await _jsonbin_get(client)
    return data.get("record", [])

async def _save_users(client: httpx.AsyncClient, users: List[Dict[str, Any]]):
    await _jsonbin_put(client, users)

# ---- Shared helpers (added) ----
async def _get_users_client():
    client = httpx.AsyncClient(timeout=20)
    data = await _jsonbin_get(client)
    users = data.get("record", [])
    return users, client

def _find_user(users, username: str):
    uname = (username or "").lower()
    for u in users:
        u_un = (u.get("username") or (u.get("consent", {}) or {}).get("username") or "").lower()
        if u_un == uname:
            return u
    return None

def _require_key(users, username: str, provided: str | None):
    if provided and provided == os.getenv("ADMIN_TOKEN",""):
        return True
    u = _find_user(users, username)
    if not u:
        raise HTTPException(status_code=404, detail="user not found")
    keys = [k for k in (u.get("api_keys") or []) if not k.get("revoked")]
    if not keys:
        if os.getenv("DEV_ALLOW_NO_API_KEY","").lower() in ("1","true","yes"):
            return True
        raise HTTPException(status_code=401, detail="no api keys on file")
    if not provided:
        raise HTTPException(status_code=401, detail="missing X-API-Key")
    if not any(k.get("key")==provided for k in keys):
        raise HTTPException(status_code=401, detail="invalid api key")
    return True

def _uname(u: Dict[str, Any]) -> str:
    return u.get("username") or (u.get("consent", {}) or {}).get("username")

def _ensure_business(u: Dict[str, Any]) -> Dict[str, Any]:
    u.setdefault("proposals", [])
    u.setdefault("quotes", [])
    u.setdefault("orders", [])
    u.setdefault("invoices", [])
    u.setdefault("payments", [])
    u.setdefault("contacts", [])
    u.setdefault("experiments", [])
    u.setdefault("kpi_snapshots", [])
    u.setdefault("tickets", [])
    u.setdefault("nps", [])
    u.setdefault("testimonials", [])
    u.setdefault("collectibles", [])
    u.setdefault("listings", [])
    u.setdefault("api_keys", [])
    u.setdefault("roles", [])
    u.setdefault("audit", [])
    u.setdefault("docs", [])
    u.setdefault("consents", [])
    u.setdefault("offers", [])
    u.setdefault("ownership", {"aigx": 0.0, "royalties": 0.0, "ledger": []})
    u.setdefault("yield", {"aigxEarned": 0.0})
    return u

def _find_in(lst: List[Dict[str, Any]], key: str, val: str) -> Optional[Dict[str, Any]]:
    for it in lst:
        if it.get(key) == val:
            return it
    return None

# ============================
# Endpoints
# ============================

# ---------- BANDIT: epsilon-greedy for creatives/offers ----------
def _bandit_slot(u: Dict[str, Any], key: str):
    b = u.setdefault("bandits", {}).setdefault(key, {"arms": {}})
    return b

@app.post("/bandit/next")
async def bandit_next(body: Dict = Body(...)):
    """
    Body: { username, key, arms:["A","B",...], epsilon:0.15 }
    Returns: { arm }
    """
    username = body.get("username"); key = body.get("key"); arms = body.get("arms") or []
    eps = float(body.get("epsilon", 0.15))
    if not (username and key and arms): return {"error":"username, key, arms required"}

    async with httpx.AsyncClient(timeout=15) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        slot = _bandit_slot(u, key)
        # init arms
        for a in arms:
            slot["arms"].setdefault(a, {"n": 0, "r": 0.0})
        import random
        if random.random() < eps:
            choice = random.choice(arms)
        else:
            # pick argmax avg reward
            choice = max(arms, key=lambda a: (slot["arms"][a]["r"] / max(1, slot["arms"][a]["n"])))
        await _save_users(client, users)
        return {"ok": True, "arm": choice}

@app.post("/bandit/reward")
async def bandit_reward(body: Dict = Body(...)):
    """
    Body: { username, key, arm, reward }   # reward ∈ [0,1] (click/lead/won)
    """
    username = body.get("username"); key = body.get("key"); arm = body.get("arm")
    reward = float(body.get("reward", 0))
    if not (username and key and arm): return {"error":"username, key, arm required"}
    async with httpx.AsyncClient(timeout=15) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        slot = _bandit_slot(u, key)
        armstat = slot["arms"].setdefault(arm, {"n":0, "r":0.0})
        armstat["n"] += 1
        armstat["r"] += reward
        await _save_users(client, users)
        return {"ok": True, "arm": arm, "n": armstat["n"], "sum_r": armstat["r"]}

# ---- GET/POST: normalized user by username ----
@app.post("/user")
async def get_user(request: Request):
    body = await request.json()
    username = (body or {}).get("username")
    if not username:
        return {"error": "Missing username"}

    async with httpx.AsyncClient(timeout=15) as client:
        data = await _jsonbin_get(client)
        for record in data.get("record", []):
            if record.get("username") == username or record.get("consent", {}).get("username") == username:
                return {"record": normalize_user_record(record)}
        return {"error": "User not found"}

# ---- POST: mint (idempotent) ----
@app.post("/mint")
async def mint_user(request: Request):
    body = await request.json()
    username = body.get("username")
    company_type = body.get("companyType", "general")
    referral = body.get("referral", "origin/hero")
    if not username:
        return {"ok": False, "error": "Username required"}

    async with httpx.AsyncClient(timeout=20) as client:
        data = await _jsonbin_get(client)
        users = data.get("record", [])
        for u in users:
            if u.get("username") == username or u.get("consent", {}).get("username") == username:
                return {"ok": True, "record": normalize_user_record(u)}

        new_user = make_canonical_record(username, company_type, referral)
        users = _upsert(users, new_user)
        await _jsonbin_put(client, users)
        try:
            log_agent_update(new_user)
            append_intent_ledger(username, {"event":"mint","referral": referral})
        except Exception:
            pass
        return {"ok": True, "record": normalize_user_record(new_user)}

# ---- POST: unlock (kits/licenses/flags) ----
@app.post("/unlock")
async def unlock_feature(request: Request):
    body = await request.json()
    username = body.get("username")
    target = body.get("target")  # e.g., "branding" (kit) or "sdk" (license) or runtime "vaultAccess"
    kind   = body.get("kind", "kit")  # "kit" | "license" | "flag"
    value  = bool(body.get("value", True))
    if not (username and target):
        return {"error": "username & target required"}

    async with httpx.AsyncClient(timeout=20) as client:
        data = await _jsonbin_get(client)
        users = data.get("record", [])
        for i, u in enumerate(users):
            uname = u.get("username") or u.get("consent", {}).get("username")
            if uname == username:
                if kind == "kit":
                    u.setdefault("kits", _empty_kits())
                    u["kits"].setdefault(target, {"unlocked": False})
                    u["kits"][target]["unlocked"] = value
                elif kind == "license":
                    u.setdefault("licenses", _empty_licenses())
                    u["licenses"][target] = value
                else:
                    u.setdefault("runtimeFlags", {})
                    u["runtimeFlags"][target] = value

                u.setdefault("transactions", {}).setdefault("unlocks", []).append(
                    {"target": target, "kind": kind, "value": value, "ts": _now()}
                )
                users[i] = u
                await _jsonbin_put(client, users)
                return {"ok": True, "record": normalize_user_record(u)}
        return {"error": "User not found"}

# ---- POST: AMG sync (App Monetization Graph) ----
@app.post("/amg/sync")
async def amg_sync(request: Request):
    """
    Body: { username, apps: [{name, scopes:[]}, ...] }
    Derives capabilities and saves to user.amg
    """
    body = await request.json()
    username = body.get("username")
    apps = body.get("apps", [])
    if not username:
        return {"error": "username required"}

    caps = set()
    for app in apps:
        n = (app.get("name") or "").lower()
        scopes = [s.lower() for s in app.get("scopes", [])]
        if n in ("shopify","woo","square","stripe"):
            caps.add("commerce_in")
        if any(s in scopes for s in ("payments","charges.read","orders.read")):
            caps.add("commerce_in")
        if n in ("gmail","outlook","mailgun","postmark"):
            caps.add("email_out")
        if n in ("tiktok","instagram","facebook","twitter","x","linkedin","youtube"):
            caps.add("content_out")
        if n in ("calendly","calendar","google calendar","outlook calendar"):
            caps.add("calendar")
        if n in ("twilio","messagebird","nexmo"):
            caps.add("sms_out")
        if n in ("meta-ads","google-ads","tiktok-ads"):
            caps.add("ads_budget")

    async with httpx.AsyncClient(timeout=20) as client:
        data = await _jsonbin_get(client)
        users = data.get("record", [])
        for i, u in enumerate(users):
            uname = u.get("username") or u.get("consent", {}).get("username")
            if uname == username:
                u.setdefault("amg", {"apps": [], "capabilities": [], "lastSync": None})
                u["amg"]["apps"] = apps
                u["amg"]["capabilities"] = sorted(list(caps))
                u["amg"]["lastSync"] = _now()
                users[i] = u
                await _jsonbin_put(client, users)
                return {"ok": True, "amg": u["amg"], "record": normalize_user_record(u)}
        return {"error": "User not found"}

# ===== Money / Summary =====
@app.post("/money/summary")
async def money_summary(body: Dict = Body(...)):
    username = body.get("username")
    if not username: return {"error":"username required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        return {"ok": True, "summary": _money_summary(u)}
@app.get("/revenue/summary")
async def revenue_summary_get(username: str):
    """Frontend expects this endpoint"""
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        u = next((x for x in users if _uname(x) == username), None)
        if not u:
            return {"error": "user not found"}
        
        # Call your revenue_flows.py function
        from revenue_flows import get_earnings_summary
        result = get_earnings_summary(username)
        return result

@app.get("/score/outcome") 
async def get_outcome_score_query(username: str):
    """Frontend polls this"""
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        u = next((x for x in users if _uname(x) == username), None)
        if not u:
            return {"error": "user not found"}
        return {"ok": True, "score": int(u.get("outcomeScore", 0))}

@app.get("/metrics/summary")
async def metrics_summary_get(username: str):
    """Compact snapshot for dashboard"""
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        u = next((x for x in users if _uname(x) == username), None)
        if not u:
            return {"error": "user not found"}
        
        return {
            "ok": True,
            "proposals": len(u.get("proposals", [])),
            "intents": len(u.get("intents", [])),
            "quotes": len(u.get("quotes", [])),
            "escrow": len([e for e in u.get("escrow", []) if e.get("status") == "held"]),
            "aigx": float(u.get("yield", {}).get("aigxEarned", 0))
        }
# ===== Referral credit (double-sided friendly) =====
@app.post("/referral/credit")
async def referral_credit(body: Dict = Body(...)):
    """
    Body: { referrer: "alice", newUser: "bob", amount?: number }
    Adds AIGx to referrer for bringing in a new user.
    """
    referrer = body.get("referrer"); new_user = body.get("newUser")
    amount = float(body.get("amount", REFERRAL_BOUNTY))
    if not (referrer and new_user): return {"error":"referrer & newUser required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        r = next((x for x in users if _uname(x)==referrer), None)
        if not r: return {"error":"referrer not found"}
        _ensure_business(r)
        # ledger
        entry = {"ts": _now(), "amount": amount, "currency": "AIGx", "basis": "referral_bounty", "ref": new_user}
        r["ownership"]["ledger"].append(entry)
        r["ownership"]["aigx"] = float(r["ownership"].get("aigx",0)) + amount
        r.setdefault("transactions", {}).setdefault("referralEvents", []).append(
            {"user": new_user, "amount": amount, "ts": _now()}
        )
        await _save_users(client, users)
        return {"ok": True, "ledgerEntry": entry, "summary": _money_summary(r)}

# ===== Wallet connect / payout rail =====

@app.post("/wallet/connect")
async def wallet_connect(body: Dict = Body(...)):
    """
    Body: { username, method: "stripe"|"crypto", account?: "acct_...", address?: "0x..", note? }
    Stores payout destination metadata for the user.
    """
    username = body.get("username"); method = (body.get("method") or "stripe").lower()
    if not username: return {"error":"username required"}
    if method not in ("stripe","crypto"): return {"error":"method must be stripe|crypto"}

    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        w = u.setdefault("wallet", {})
        w["method"] = method
        if method == "stripe":
            if body.get("account"): w["stripe_connect_id"] = body.get("account")
        else:
            if body.get("address"): w["crypto_address"] = body.get("address")
        w["updated"] = _now(); w["note"] = body.get("note")
        await _save_users(client, users)

        safe = {k:v for k,v in w.items() if k not in ("keys","secrets")}
        return {"ok": True, "wallet": safe}

@app.post("/payout/request")
async def payout_request(request: Request, x_api_key: str | None = Header(None, alias='X-API-Key'), idemp: str | None = Header(None, alias='Idempotency-Key')):
    body = await request.json()
    """
    Body: { username, amount, method?: "stripe"|"crypto" }
    Checks available balance and raises a payout request (queued for ops/batch).
    """
    username = body.get("username"); amount = float(body.get("amount", 0))
    method = (body.get("method") or "stripe").lower()
    if not (username and amount): return {"error":"username & amount required"}
    if amount < PAYOUT_MIN: return {"error": f"minimum payout is {PAYOUT_MIN}"}

    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        _require_key(users, username, x_api_key)
        u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        # ensure wallet is set
        w = u.get("wallet") or {}
        if (method == 'stripe' and not w.get('stripe_connect_id')) or (method == 'crypto' and not w.get('crypto_address')):
            return {"error":"no payout destination on file; call /wallet/connect first"}

        money = _money_summary(u)
        if amount > money["available"]:
            return {"error": f"insufficient available funds ({money['available']})"}

        u.setdefault("payouts", [])
        pid = _id("pyo")
        req = {"id": pid, "amount": round(amount,2), "method": method, "status":"requested",
               "ts": _now(), "requested_by": username}
        u["payouts"].append(req)
        await _save_users(client, users)
        return {"ok": True, "payout": req, "summary": _money_summary(u)}

# ---- POST: Autonomy Level AL0–AL5 ----
@app.post("/autonomy")
async def set_autonomy(request: Request):
    body = await request.json()
    username = body.get("username")
    level = body.get("level", "AL1")  # AL0 ask-first … AL5 full-auto
    guardrails = body.get("guardrails", {}) # e.g. {"maxDiscount":0.1,"quietHours":[22,8],"budget":200}
    if not username:
        return {"error": "username required"}

    async with httpx.AsyncClient(timeout=20) as client:
        data = await _jsonbin_get(client)
        users = data.get("record", [])
        for i, u in enumerate(users):
            u_name = u.get("username") or u.get("consent", {}).get("username")
            if u_name == username:
                u.setdefault("runtimeFlags", {})
                u["runtimeFlags"]["autonomyLevel"] = level
                u.setdefault("policy", {})
                u["policy"]["guardrails"] = guardrails
                users[i] = u
                await _jsonbin_put(client, users)
                return {"ok": True, "record": normalize_user_record(u)}
        return {"error": "User not found"}

@app.post("/payout/status")
async def payout_status(body: Dict = Body(...)):
    """
    Admin/daemon hook.
    Body: { username, payoutId, status: "queued"|"paid"|"failed", txn_id? }
    On 'paid' we post a negative payout ledger line.
    """
    username = body.get("username"); pid = body.get("payoutId"); status = (body.get("status") or "").lower()
    if not (username and pid and status): return {"error":"username, payoutId, status required"}
    if status not in ("queued","paid","failed"): return {"error":"bad status"}

    async with httpx.AsyncClient(timeout=30) as client:
        users = await _load_users(client)
        u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)

        pay = next((p for p in u.get("payouts", []) if p.get("id")==pid), None)
        if not pay: return {"error":"payout not found"}
        pay["status"] = status; pay["status_ts"] = _now()
        if body.get("txn_id"): pay["txn_id"] = body.get("txn_id")

        if status == "paid":
            # finalize by ledgering a negative payout
            amt = float(pay.get("amount",0))
            entry = {"ts": _now(), "amount": -amt, "currency": "USD", "basis": "payout", "ref": pid}
            u["ownership"]["ledger"].append(entry)

        await _save_users(client, users)
        return {"ok": True, "payout": pay, "summary": _money_summary(u)}

# ---- POST: AIGx credit (Earn Layer receipts) ----
@app.post("/aigx/credit")
async def aigx_credit(request: Request):
    """
    Body: { username, amount, basis, ref }
    Adds to ownership.ledger and yield.aigxEarned
    """
    body = await request.json()
    username = body.get("username")
    amount = float(body.get("amount", 0))
    basis  = body.get("basis","uplift")  # uplift|royalty|bounty|task
    ref    = body.get("ref")            # optional invoice/ref
    if not (username and amount):
        return {"error": "username & amount required"}

    async with httpx.AsyncClient(timeout=20) as client:
        data = await _jsonbin_get(client)
        users = data.get("record", [])
        for i, u in enumerate(users):
            if (u.get("username") or u.get("consent", {}).get("username")) == username:
                u.setdefault("ownership", {"aigx":0,"royalties":0,"ledger":[]})
                u.setdefault("yield", {"aigxEarned":0})
                entry = {"ts": _now(), "amount": amount, "currency": "AIGx", "basis": basis, "ref": ref}
                u["ownership"]["ledger"].append(entry)
                u["ownership"]["aigx"] = float(u["ownership"].get("aigx",0)) + amount
                u["yield"]["aigxEarned"] = float(u["yield"].get("aigxEarned",0)) + amount
                users[i] = u
                await _jsonbin_put(client, users)
                try:
                    append_intent_ledger(username, {"event":"aigx_credit","amount": amount, "basis": basis})
                    log_metaloop(username, "credit", {"basis": basis, "amount": amount})
                except Exception:
                    pass
                return {"ok": True, "ledgerEntry": entry, "record": normalize_user_record(u)}
        return {"error": "User not found"}

@app.post("/referral/link")
async def referral_link(body: Dict = Body(...)):
    username = body.get("username")
    if not username: return {"error":"username required"}
    oid = _id("ref"); exp = int((datetime.utcnow()+timedelta(days=14)).timestamp())
    sig = _hmac(f"{oid}.{username}.{exp}", POL_SECRET)
    url = f"/r?oid={oid}&sig={sig}&ref={username}&exp={exp}"
    return {"ok": True, "url": url, "exp": exp}

@app.post("/vault/autostake")
async def vault_autostake(body: Dict = Body(...)):
    username = body.get("username"); enabled = bool(body.get("enabled", True)); pct = float(body.get("percent", 0.5))
    if not username: return {"error":"username required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        y = u.setdefault("yield", {}); y["autoStake"] = enabled; y["autoStakePct"] = pct
        await _save_users(client, users)
        return {"ok": True, "yield": y}

@app.get("/metrics")
async def metrics():
    async with httpx.AsyncClient(timeout=30) as client:
        data = await _jsonbin_get(client)
        users = data.get("record", [])
        rev = fee = payouts = invoices_open = 0.0
        for u in users:
            for l in (u.get("ownership", {}).get("ledger", []) or []):
                if l.get("basis") == "revenue": rev += float(l.get("amount",0))
                if l.get("basis") == "platform_fee": fee += float(l.get("amount",0))
                if l.get("basis") == "payout": payouts += float(l.get("amount",0))
            for inv in (u.get("invoices",[]) or []):
                if inv.get("status") == "issued": invoices_open += float(inv.get("amount",0))
        return {"ok": True, "totals": {
            "revenue": round(rev,2), "platform_fees": round(fee,2),
            "payouts": round(payouts,2), "invoices_open": round(invoices_open,2)
        }}
# Add to main.py after your existing /user endpoint

@app.get("/users/all")
async def get_all_users(limit: int = 100):
    """
    Return all users (for matching). Paginate in production.
    """
    async with httpx.AsyncClient(timeout=15) as client:
        data = await _jsonbin_get(client)
        users = data.get("record", [])[:limit]
        
        # Strip sensitive data
        safe_users = []
        for u in users:
            safe_users.append({
                "username": u.get("username") or u.get("consent", {}).get("username"),
                "traits": u.get("traits", []),
                "outcomeScore": u.get("outcomeScore", 0),
                "kits": list(u.get("kits", {}).keys()),
                "meta_role": u.get("meta_role", ""),
            })
        
        return {"ok": True, "users": safe_users, "count": len(safe_users)}
 # ---------- ALGO HINTS + SCHEDULER ----------
@app.post("/algo/hints/upsert")
async def algo_hints_upsert(body: Dict = Body(...)):
    """
    Body: { username, platform, hints: { cadence_per_day, quiet_hours:[22,8], max_caption_len, hashtags:int } }
    """
    username = body.get("username"); platform = (body.get("platform") or "").lower()
    hints = body.get("hints") or {}
    if not (username and platform): return {"error":"username & platform required"}
    async with httpx.AsyncClient(timeout=15) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        u.setdefault("algo_hints", {})[platform] = hints
        await _save_users(client, users)
        return {"ok": True, "hints": hints}

@app.post("/algo/schedule/plan")
async def algo_schedule_plan(body: Dict = Body(...)):
    """
    Body: { username, platform, window_hours: 48, start_iso?: now }
    Returns: { slots:[iso...] } best-effort evenly spaced outside quiet hours.
    """
    username = body.get("username"); platform = (body.get("platform") or "").lower()
    window = int(body.get("window_hours", 48))
    start = datetime.fromisoformat(body.get("start_iso")) if body.get("start_iso") else datetime.utcnow()
    if not (username and platform): return {"error":"username & platform required"}
    async with httpx.AsyncClient(timeout=15) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        hints = (u.get("algo_hints") or {}).get(platform, {})
        per_day = max(1, int(hints.get("cadence_per_day", 2)))
        quiet   = hints.get("quiet_hours", [23, 7])  # [startHour, endHour)
        slots = []
        total_posts = int((window/24.0) * per_day)
        step = timedelta(hours=window/max(1,total_posts))
        t = start
        while len(slots) < total_posts:
            hr = t.hour
            bad = quiet and ((quiet[0] <= hr) or (hr < quiet[1])) if quiet[0] < quiet[1] else (quiet[1] <= hr <= quiet[0])
            if not bad:
                slots.append(t.replace(microsecond=0).isoformat()+"Z")
            t += step
        return {"ok": True, "slots": slots}

# ---------- DISTRIBUTION REGISTRY + PUSH ----------
@app.post("/distribution/register")
async def distribution_register(request: Request, x_api_key: str | None = Header(None, alias="X-API-Key")):
    body = await request.json()
    """
    Body: { username, channel, endpoint_url, token }
    """
    username = body.get("username")
    channel = (body.get("channel") or "partner").lower()
    endpoint_url = body.get("endpoint_url") or body.get("endpoint") or body.get("url")
    token = body.get("token")
    if not (username and endpoint_url and token):
        return {"error":"username, endpoint_url, token required"}
    if not _safe_url(str(endpoint_url or "")):
        raise HTTPException(status_code=400, detail="endpoint not allowed")
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        u = next((x for x in users if _uname(x) == username), None)
        _require_key(users, username, x_api_key)
        if not u:
            return {"error":"user not found"}
        _ensure_business(u)
        u.setdefault("distribution", []).append({
            "id": str(uuid.uuid4()),
            "channel": channel,
            "url": endpoint_url,
            "token": token,
            "ts": _now()
        })
        await _save_users(client, users)
        return {"ok": True}

@app.post("/distribution/push")
async def distribution_push(request: Request, x_api_key: str | None = Header(None, alias='X-API-Key')):
    body = await request.json()
    """
    Body: { username, listingId, channels?:[] }
    Pushes a signed lightweight Offer Card (POL) to registered webhooks.
    """
    username = body.get("username"); lid = body.get("listingId"); channels = body.get("channels")
    if not (username and lid): return {"error":"username & listingId required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        _require_key(users, username, x_api_key)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        listing = _find_in(u.get("listings", []), "id", lid)
        if not listing: return {"error":"listing not found"}

        # prep POL-like card
        oid = _id("pol")
        exp = int((datetime.utcnow()+timedelta(days=2)).timestamp())
        sig = _hmac(f"{oid}.{username}.{exp}", POL_SECRET)
        card = {
            "oid": oid, "sig": sig, "exp": exp, "src": "distribution",
            "title": listing["title"], "price": listing.get("price",0), "usr": username,
            "url": f"/offer?oid={oid}&sig={sig}&usr={username}&exp={exp}&src=dist"
        }

        dispatched = []
        for d in u.get("distribution", []):
            if channels and d["channel"] not in channels:
                continue
            try:
                r = await client.post(d["url"], json={"token": d["token"], "card": card}, timeout=8)
                dispatched.append({"channel": d["channel"], "status": r.status_code})
            except Exception:
                dispatched.append({"channel": d["channel"], "status": "error"})

        listing["impressions"] = listing.get("impressions", 0) + len(dispatched)
        await _save_users(client, users)
        return {"ok": True, "sent": dispatched, "card": card}

# ---------- REVENUE SPLITTER (JV mesh) ----------
@app.post("/revenue/split")
async def revenue_split(request: Request, x_api_key: str | None = Header(None, alias='X-API-Key')):
    body = await request.json()
    """
    Body: { username, amount, currency:'USD', ref, jvId? }
    If jvId present, split by that entry; else split equally across all JV mesh entries.
    """
    username = body.get("username"); amt = float(body.get("amount", 0)); cur = (body.get("currency") or "USD").upper()
    ref = body.get("ref"); jvId = body.get("jvId")
    if not (username and amt): return {"error":"username & amount required"}

    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        _require_key(users, username, x_api_key)
        def find_user(name): return next((x for x in users if _uname(x)==name), None)
        origin = find_user(username)
        if not origin: return {"error":"user not found"}

        mesh = origin.get("jvMesh", []) or []
        targets = []
        # resolve targets
        if jvId:
            jv = _find_in(mesh, "id", jvId)
            if not jv:
                return {"error": "jv not found"}
            jv_split = jv.get("split") or []
            if not jv_split:
                targets = [(username, 1.0)]
            else:
                targets = [(name, float(frac)) for name, frac in jv_split if float(frac) > 0]
        else:
            targets = [(username, 1.0)]


        for uname, frac in targets:
            u = find_user(uname) or origin
            u.setdefault("ownership", {"aigx":0,"royalties":0,"ledger":[]})
            val = round(amt * frac, 2)
            entry = {"ts": _now(), "amount": val, "currency": cur, "basis": "jv_split", "ref": ref}
            u["ownership"]["ledger"].append(entry)
            u["ownership"]["aigx"] = float(u["ownership"].get("aigx",0)) + val

        await _save_users(client, users)
        return {"ok": True, "distributed": [{"user":t[0], "amount": round(amt*t[1],2)} for t in targets]}

# ---------- CREATIVE RENDER (FTC-safe) ----------
DISCLOSURES = {
    "tiktok": "#ad",
    "instagram": "#ad",
    "x": "Ad:",
    "twitter": "Ad:",
    "linkedin": "Sponsored",
    "youtube": "Includes paid promotion",
}

@app.post("/creative/render")
async def creative_render(body: Dict = Body(...)):
    """
    Body: { username, platform, caption, intent? }
    Ensures disclosure + max caption len based on algo hints (if set).
    """
    username = body.get("username"); platform = (body.get("platform") or "tiktok").lower()
    caption  = (body.get("caption") or "").strip()
    if not username: return {"error":"username required"}

    async with httpx.AsyncClient(timeout=15) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        hints = (u.get("algo_hints") or {}).get(platform, {})
        max_len = int(hints.get("max_caption_len", 2200 if platform == "instagram" else 280))
        disc = DISCLOSURES.get(platform)
        out = caption
        if disc and disc.lower() not in caption.lower():
            out = f"{disc} {caption}".strip()
        if len(out) > max_len:
            out = out[:max_len-1] + "…"
        return {"ok": True, "caption": out, "disclosure": disc, "max_len": max_len}

# ---- POST: Contacts (privacy-first) opt-in + counts ----
@app.post("/contacts/optin")
async def contacts_optin(request: Request, x_api_key: str | None = Header(None, alias='X-API-Key')):
    """
    Body: { username, sources: [{source:"upload/csv/gmail/phone", count:int}] }
    We store counts only (privacy-first). Send actual outreach via /contacts/send -> webhook.
    """
    body = await request.json()
    username = body.get("username")
    sources  = body.get("sources", [])
    if not username:
        return {"error": "username required"}

    async with httpx.AsyncClient(timeout=20) as client:
        data = await _jsonbin_get(client)
        users = data.get("record", [])
        for i, u in enumerate(users):
            if (u.get("username") or u.get("consent", {}).get("username")) == username:
                u.setdefault("contacts", {"sources": [], "counts": {}, "lastSync": None})
                for s in sources:
                    src = s.get("source","unknown")
                    cnt = int(s.get("count",0))
                    u["contacts"]["counts"][src] = int(u["contacts"]["counts"].get(src,0)) + cnt
                    if src not in u["contacts"]["sources"]:
                        u["contacts"]["sources"].append(src)
                u["contacts"]["lastSync"] = _now()
                users[i] = u
                await _jsonbin_put(client, users)
                return {"ok": True, "contacts": u["contacts"], "record": normalize_user_record(u)}
        return {"error": "User not found"}

# ---------- MONETIZE: BUDGET SCALER BY ROAS ----------
@app.post("/monetize/scale")
async def monetize_scale(body: Dict = Body(...)):
    """
    Body: { username, roas: float, min:0.5, max:1.5 }
    Returns a multiplier for tomorrow's budget based on ROAS.
    """
    username = body.get("username"); roas = float(body.get("roas", 1.0))
    lo = float(body.get("min", 0.8)); hi = float(body.get("max", 1.25))
    if not username: return {"error":"username required"}
    # piecewise: below 1.0 → shrink; above 2.0 → boost; clamp
    if roas < 0.8: m = lo
    elif roas < 1.0: m = 0.9
    elif roas < 1.5: m = 1.05
    elif roas < 2.0: m = 1.15
    else: m = hi
    return {"ok": True, "multiplier": round(m, 3)}

# ---- POST: Contacts send (webhook; logs outreach) [FIXED + RATE LIMIT] ----
@app.post("/contacts/send")
async def contacts_send(request: Request):
    """
    Body: { username, channel:"sms|email|dm", template, previewOnly=false }
    We store outreach events & counts only (no raw PII).
    Optional webhook fanout via PROPOSAL_WEBHOOK_URL.
    Adds soft per-user/channel rate-limit: 50 sends / 24h.
    """
    body = await request.json()
    username = body.get("username")
    channel  = (body.get("channel") or "email").lower()
    template = body.get("template") or ""
    preview  = bool(body.get("previewOnly", False))
    if not (username and template):
        return {"error": "username & template required"}

    async with httpx.AsyncClient(timeout=20) as client:
        data  = await _jsonbin_get(client)
        users = data.get("record", [])
        # load user first (previous bug fix)
        idx = next((i for i,u in enumerate(users) if (u.get("username") or u.get("consent", {}).get("username")) == username), None)
        if idx is None:
            return {"error": "User not found"}
        u = users[idx]
        _ensure_business(u)

        # soft rate-limit
        today = datetime.utcnow().date().isoformat()
        rl = u.setdefault("rate_limits", {}).setdefault("contacts_send", {})
        stats = rl.setdefault(channel, {"date": today, "count": 0})
        if stats["date"] != today:
            stats["date"] = today
            stats["count"] = 0
        if stats["count"] >= 50 and not preview:
            return {"error": "rate_limited", "detail": "Daily channel cap reached"}

        payload = {"type": "contacts_send", "channel": channel, "username": username, "template": template, "ts": _now()}
        delivered = False
        if (PROPOSAL_WEBHOOK_URL and not preview):
            try:
                r = await client.post(PROPOSAL_WEBHOOK_URL, json=payload, headers={"Content-Type":"application/json"})
                delivered = r.status_code in (200, 204)
            except Exception:
                delivered = False

        stats["count"] += 1
        u.setdefault("transactions", {}).setdefault("outreachEvents", []).append(
            {"channel": channel, "templateHash": hash(template), "delivered": delivered, "ts": _now()}
        )
        users[idx] = u
        await _jsonbin_put(client, users)
        return {"ok": True, "delivered": delivered, "count": stats["count"]}


# ---- POST: JV Mesh (MetaBridge 2.0 cap-table stub) ----
@app.post("/jv/create")
async def jv_create(request: Request, x_api_key: str | None = Header(None, alias='X-API-Key')):
    """
    Body: { a: "userA", b: "userB", title, split: {"a":0.6,"b":0.4}, terms }
    Appends JV entry to both users' jvMesh; settlement handled by MetaBridge runtime.
    """
    body = await request.json()
    username = (body.get('username') or body.get('consent',{}).get('username'))
    a = body.get("a"); b = body.get("b")
    title = body.get("title","JV")
    split = body.get("split", {"a":0.5,"b":0.5})
    terms = body.get("terms","rev-share on matched bundles")
    if not (a and b):
        return {"error": "a & b usernames required"}

    entry = {"id": str(uuid.uuid4()), "title": title, "split": split, "terms": terms, "created": _now()}
    async with httpx.AsyncClient(timeout=20) as client:
        data = await _jsonbin_get(client)
        users = data.get("record", [])
        found = 0
        for i, u in enumerate(users):
            uname = u.get("username") or u.get("consent", {}).get("username")
            if uname in (a, b):
                u.setdefault("jvMesh", []).append(entry)
                users[i] = u
                found += 1
        if found == 2:
            await _jsonbin_put(client, users)
            return {"ok": True, "jv": entry}
        return {"error": "One or both users not found"}

# ---- UPDATED: MetaBridge — generate & persist proposals via /submit_proposal ----
@app.post("/metabridge")
async def metabridge_dispatch(request: Request):
    try:
        data = await request.json()
        query = (data.get("query") or "").strip()
        originator = data.get("username", "anonymous")
        if not query:
            return {"error": "No query provided."}

        from aigent_growth_agent import (
            metabridge_dual_match_realworld_fulfillment,
            proposal_generator
        )
        matches   = metabridge_dual_match_realworld_fulfillment(query)
        proposals = proposal_generator(query, matches, originator)

        base = (os.getenv("SELF_URL") or str(request.base_url)).rstrip("/")
        submit_url = f"{base}/submit_proposal"

        async with httpx.AsyncClient(timeout=20) as client:
            for p in proposals:
                await client.post(submit_url, json=p, headers={"Content-Type": "application/json"})

        try:
            log_metabridge(originator, {"query": query, "matches": len(matches)})
        except Exception:
            pass

        return {"status": "ok", "query": query, "match_count": len(matches), "proposals": proposals, "matches": matches}
    except Exception as e:
        return {"error": f"MetaBridge runtime error: {e}"}

# ---- Agent passthrough ----
@app.post("/agent")
async def run_agent(request: Request):
    try:
        data = await request.json()
        user_input = data.get("input","")
        role = data.get("role", "CFO")  # CFO is venture_builder_agent (default)
        username = data.get("username", "guest")
        
        if not user_input:
            return {"error": "No input provided."}
        
        # Role-specific enforcement
        ROLE_INSTRUCTIONS = {
            "CFO": f"""CRITICAL: You are the CFO of {username}'s business. Speak ONLY in first person.
NEVER say "your CFO" or "the agent" — you ARE the CFO.
Start with: "💰 CFO here —"
Give 2-3 concrete financial next steps with ROI/pricing.
End with ONE clarifying question.""",
            
            "CMO": f"""CRITICAL: You are the CMO of {username}'s business. Speak ONLY in first person.
NEVER say "your CMO" or "the growth agent" — you ARE the CMO.
Start with: "📣 CMO here —"
Give 2-3 concrete growth plays with channels/targets.
End with ONE clarifying question.""",
            
            "CTO": f"""CRITICAL: You are the CTO of {username}'s business. Speak ONLY in first person.
NEVER say "your CTO" or "the SDK agent" — you ARE the CTO.
Start with: "🧬 CTO here —"
Give 2-3 concrete technical steps with build/integration plan.
End with ONE clarifying question.""",
            
            "CLO": f"""CRITICAL: You are the CLO of {username}'s business. Speak ONLY in first person.
NEVER say "your CLO" or "the legal agent" — you ARE the CLO.
Start with: "📜 CLO here —"
Give 2-3 concrete legal/branding steps with risk mitigation.
End with ONE clarifying question.""",
        }
        
        # Inject role instruction into input
        role_instruction = ROLE_INSTRUCTIONS.get(role, ROLE_INSTRUCTIONS["CFO"])
        enhanced_input = f"{role_instruction}\n\nUser question: {user_input}"
        
        initial_state = {
            "input": enhanced_input,
            "memory": data.get("memory", [])
        }
        
        result = await agent_graph.ainvoke(initial_state)
        output = result.get("output", "No output returned.")
        
        # Safety filter: Remove third-person references
        output = output.replace("your CFO", "I")
        output = output.replace("your CMO", "I")
        output = output.replace("your CTO", "I")
        output = output.replace("your CLO", "I")
        output = output.replace("the CFO", "I")
        output = output.replace("the CMO", "I")
        output = output.replace("the CTO", "I")
        output = output.replace("the CLO", "I")
        output = output.replace("AiGent Growth", "I")
        output = output.replace("AiGent Venture", "I")
        output = output.replace("AiGentsy SDK", "I")
        output = output.replace("AiGentsy Remix", "I")
        
        return {"output": output, "role": role}
        
    except Exception as e:
        return {"error": f"Agent runtime error: {str(e)}"}
# ---- Existing router/decide (intent orchestrator) retained ----
@app.post("/router/decide")
async def router_decide(request: Request):
    """
    Body: { username, intent, payload, previewOnly=false }
    Returns a routing decision with risk/holdout flags for safe execution.
    """
    body = await request.json()
    username = body.get("username")
    intent = body.get("intent","generic")
    payload = body.get("payload",{})
    preview = bool(body.get("previewOnly", False))

    decision = {
        "intent": intent,
        "action": "shadow" if preview else "execute",
        "score": 0.62,   # placeholder scorer
        "blocked": False,
        "control": False,
        "ts": _now()
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            data = await _jsonbin_get(client)
            users = data.get("record", [])
            for u in users:
                uname = u.get("username") or u.get("consent", {}).get("username")
                if uname == username:
                    quiet = u.get("policy", {}).get("guardrails", {}).get("quietHours")
                    if isinstance(quiet, (list, tuple)) and len(quiet)==2:
                        decision["blocked"] = False  # implement localtime check if needed
                    import random
                    decision["control"] = (not preview) and (random.random() < 0.1)
                    break
    except Exception:
        pass

    return {"ok": True, "decision": decision}

# ---- Consent (list/upsert) retained ----
@app.post("/consent/upsert")
async def consent_upsert(request: Request):
    """
    Body: { username, scopes:[], connectors:[] }
    Upserts consent scopes/connectors to user.consent.
    """
    body = await request.json()
    username = body.get("username")
    scopes = body.get("scopes", [])
    connectors = body.get("connectors", [])
    if not username:
        return {"error":"username required"}

    async with httpx.AsyncClient(timeout=15) as client:
        data = await _jsonbin_get(client)
        users = data.get("record", [])
        for i,u in enumerate(users):
            uname = u.get("username") or u.get("consent", {}).get("username")
            if uname == username:
                u.setdefault("consent", {}).setdefault("scopes", [])
                u.setdefault("consent", {}).setdefault("connectors", [])
                u["consent"]["scopes"] = sorted(list(set(u["consent"]["scopes"] + scopes)))
                u["consent"]["connectors"] = sorted(list(set(u["consent"]["connectors"] + connectors)))
                users[i]=u
                await _jsonbin_put(client, users)
                return {"ok": True, "consent": u["consent"], "record": normalize_user_record(u)}
        return {"error":"User not found"}

@app.post("/consent/list")
async def consent_list(request: Request):
    body = await request.json()
    username = body.get("username")
    if not username: return {"error":"username required"}
    async with httpx.AsyncClient(timeout=10) as client:
        data = await _jsonbin_get(client)
        for u in data.get("record", []):
            uname = u.get("username") or u.get("consent", {}).get("username")
            if uname == username:
                return {"ok": True, "consent": u.get("consent", {})}
    return {"error":"User not found"}

# ---- Micro-Pricing nudger retained ----
@app.post("/pricing/nudge")
async def pricing_nudge(request: Request):
    """
    Body: { username, itemId, floor, currentPrice }
    Returns a safe ±1–3% nudge recommendation, respecting floors.
    """
    body = await request.json()
    username = body.get("username")
    floor = float(body.get("floor", 0))
    price = float(body.get("currentPrice", 0))
    if not username: return {"error":"username required"}

    import random
    delta = round(price * (random.choice([0.01, 0.02, 0.03])) * random.choice([-1, 1]), 2)
    proposed = max(floor, price + delta)
    rec = {"old": price, "delta": proposed - price, "new": proposed, "ts": _now()}
    return {"ok": True, "recommendation": rec}

# ---- MetaHive stubs retained ----
@app.post("/metahive/optin")
async def metahive_optin(request: Request):
    body = await request.json()
    username = body.get("username")
    enabled = bool(body.get("enabled", True))
    if not username: return {"error":"username required"}

    async with httpx.AsyncClient(timeout=15) as client:
        data = await _jsonbin_get(client)
        users = data.get("record", [])
        for i,u in enumerate(users):
            uname = u.get("username") or u.get("consent", {}).get("username")
            if uname == username:
                u.setdefault("metahive", {}).update({"enabled": enabled, "joinedAt": _now()})
                users[i]=u
                await _jsonbin_put(client, users)
                return {"ok": True, "metahive": u.get("metahive", {})}
    return {"error":"User not found"}

@app.post("/metahive/summary")
async def metahive_summary(request: Request):
    async with httpx.AsyncClient(timeout=15) as client:
        data = await _jsonbin_get(client)
        users = data.get("record", [])
        enabled = [u for u in users if u.get("metahive", {}).get("enabled")]
        return {"ok": True, "members": len(enabled)}

# === TEMPLATE CATALOG ROUTES (non-destructive) ===
try:
    from fastapi import APIRouter
    from templates_catalog import list_templates, search_templates, get_template
except Exception:
    APIRouter = None

_tpl_router = APIRouter() if 'APIRouter' in globals() and APIRouter else None

if _tpl_router:
    @_tpl_router.get('/templates/list')
    async def templates_list():
        try:
            return {'ok': True, 'templates': list_templates()}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    @_tpl_router.get('/templates/search')
    async def templates_search(q: str = ''):
        try:
            return {'ok': True, 'templates': search_templates(q)}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    @_tpl_router.post('/templates/activate')
    async def templates_activate(payload: dict):
        """Activate a template (echo-only for now; frontend also passes context)."""
        try:
            tid = payload.get('id') or payload.get('template_id')
            t = get_template(tid)
            if not t:
                return {'ok': False, 'error': 'template_not_found'}
            return {'ok': True, 'active_template': t}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

try:
    app  # type: ignore
    if _tpl_router:
        app.include_router(_tpl_router)
except Exception:
    pass

# ================================
# >>> Business-in-a-Box: NEW ROUTES <<<
# ================================

# ---------- 1) ORDER-TO-CASH ----------
@app.post("/quote/create")
async def quote_create(body: Dict = Body(...)):
    username = body.get("username"); proposalId = body.get("proposalId")
    price = float(body.get("price", 0)); scope = body.get("scope",""); terms = body.get("terms","")
    if not (username and proposalId): return {"error":"username & proposalId required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        prop = _find_in(u["proposals"], "id", proposalId) or {}
        qid = _id("qt")
        quote = {"id": qid, "proposalId": proposalId, "price": price, "scope": scope, "terms": terms,
                 "status":"offered", "ts": _now(), "title": prop.get("title","")}
        u["quotes"].append(quote)
        await _save_users(client, users)
        return {"ok": True, "quote": quote}

@app.post("/order/accept")
async def order_accept(body: Dict = Body(...)):
    username = body.get("username"); qid = body.get("quoteId")
    if not (username and qid): return {"error":"username & quoteId required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        quote = _find_in(u["quotes"], "id", qid)
        if not quote: return {"error":"quote not found"}
        quote["status"] = "accepted"
        oid = _id("ord")
        order = {
            "id": oid, "quoteId": qid, "status":"queued", "ts": _now(),
            "sla": {"due": (datetime.utcnow()+timedelta(hours=48)).isoformat(), "breaches":0},
            "tasks": [
                {"id": _id("t"), "title":"Kickoff / assets intake", "status":"todo"},
                {"id": _id("t"), "title":"Deliverable v1", "status":"todo"},
                {"id": _id("t"), "title":"Review & revisions", "status":"todo"},
                {"id": _id("t"), "title":"Final delivery", "status":"todo"},
            ]
        }
        u["orders"].append(order)
        await _save_users(client, users)
        return {"ok": True, "order": order}

@app.post("/intent/auto_bid")
async def intent_auto_bid():
    users, client = await _get_users_client()
    try:
        r = await client.get("https://aigentsy-ame-runtime.onrender.com/intents/list?status=AUCTION")
        intents = r.json().get("intents", [])
    except Exception as e:
        return {"ok": False, "error": f"failed to fetch intents: {e}"}
    bids_submitted = []
    for intent in intents:
        iid = intent["id"]
        brief = intent["intent"].get("brief", "").lower()
        budget = float(intent.get("escrow_usd", 0))
        for u in users:
            username = _username_of(u)
            traits = u.get("traits", [])
            can_fulfill = False
            if "marketing" in brief and "marketing" in traits:
                can_fulfill = True
            elif "video" in brief and "marketing" in traits:
                can_fulfill = True
            elif "sdk" in brief and "sdk" in traits:
                can_fulfill = True
            elif "legal" in brief and "legal" in traits:
                can_fulfill = True
            elif "branding" in brief and "branding" in traits:
                can_fulfill = True
            if not can_fulfill:
                continue
            import random
            discount = random.uniform(0.10, 0.20)
            bid_price = round(budget * (1 - discount), 2)
            delivery_hours = 24 if "urgent" in brief else 48
            try:
                await client.post("https://aigentsy-ame-runtime.onrender.com/intents/bid", json={"intent_id": iid, "agent": username, "price_usd": bid_price, "delivery_hours": delivery_hours, "message": f"I can deliver this within {delivery_hours}h for ${bid_price}."})
                bids_submitted.append({"intent": iid, "agent": username, "price": bid_price})
                try:
                    await publish({"type":"bid","agent":username,"intent_id":iid,"price":bid_price})
                except:
                    pass
            except Exception as e:
                print(f"Failed to bid for {username} on {iid}: {e}")
    return {"ok": True, "bids_submitted": bids_submitted, "count": len(bids_submitted)}

@app.post("/invoice/create")
async def invoice_create(body: Dict = Body(...)):
    username = body.get("username"); oid = body.get("orderId")
    amount = float(body.get("amount",0)); currency = (body.get("currency") or "USD").upper()
    if not (username and oid): return {"error":"username & orderId required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        order = _find_in(u["orders"], "id", oid)
        if not order: return {"error":"order not found"}
        inv_id = _id("inv")
        invoice = {"id": inv_id, "orderId": oid, "amount": amount, "currency": currency,
                   "status":"issued", "ts": _now()}
        u["invoices"].append(invoice)
        await _save_users(client, users)
        return {"ok": True, "invoice": invoice}

@app.post("/pay/link")
async def pay_link(body: Dict = Body(...)):
    username = body.get("username"); inv_id = body.get("invoiceId")
    if not (username and inv_id): return {"error":"username & invoiceId required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        invoice = _find_in(u["invoices"], "id", inv_id)
        if not invoice: return {"error":"invoice not found"}
        pay_id = _id("pay")
        checkout_url = f"https://pay.aigentsy/checkout/{inv_id}"  # swap for real Stripe if needed
        payment = {"id": pay_id, "invoiceId": inv_id, "amount": invoice["amount"],
                   "currency": invoice["currency"], "status":"pending", "ts": _now(),
                   "provider":"stripe", "checkout_url": checkout_url}
        u["payments"].append(payment)
        await _save_users(client, users)
        return {"ok": True, "checkout_url": checkout_url, "payment": payment}

@app.post("/revenue/recognize")
async def revenue_recognize(request: Request, x_api_key: str | None = Header(None, alias='X-API-Key')):
    body = await request.json()
    username = body.get("username")
    inv_id = body.get("invoiceId")
    intent_id = body.get("intent_id")  # ✅ ADD THIS - needed for factoring settlement
    
    if not (username and inv_id):
        return {"error": "username & invoiceId required"}
    
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        _require_key(users, username, x_api_key)
        u = next((x for x in users if _uname(x) == username), None)
        if not u:
            return {"error": "user not found"}
        _ensure_business(u)
        
        invoice = _find_in(u["invoices"], "id", inv_id)
        if not invoice:
            return {"error": "invoice not found"}
        
        # Mark paid
        invoice["status"] = "paid"
        invoice["paid_ts"] = _now()
        
        # Mark related payment paid
        for p in u.get("payments", []):
            if p.get("invoiceId") == inv_id:
                p["status"] = "paid"
                p["paid_ts"] = _now()
        
        amt = float(invoice.get("amount", 0))
        currency = invoice.get("currency", "USD")
        
        # Platform fee
        fee_rate = _platform_fee_rate(u)
        fee_amt = round(amt * fee_rate, 2)
        net_amt = round(amt - fee_amt, 2)
        
        # Ledger entries
        u["ownership"]["ledger"].append({
            "ts": _now(),
            "amount": amt,
            "currency": currency,
            "basis": "revenue",
            "ref": inv_id
        })
        u["ownership"]["ledger"].append({
            "ts": _now(),
            "amount": -fee_amt,
            "currency": currency,
            "basis": "platform_fee",
            "ref": inv_id
        })
        
        # Update balances
        u["yield"]["aigxEarned"] = float(u["yield"].get("aigxEarned", 0)) + net_amt
        u["ownership"]["aigx"] = float(u["ownership"].get("aigx", 0)) + net_amt
        
        # ✅ 1. SETTLE FACTORING (if intent_id provided)
        factoring_result = None
        if intent_id:
            try:
                # Find intent
                intent = None
                for user in users:
                    for i in user.get("intents", []):
                        if i.get("id") == intent_id:
                            intent = i
                            break
                    if intent:
                        break
                
                if intent and intent.get("factoring"):
                    factoring_result = await settle_factoring(u, intent, amt)
                    
                    if factoring_result.get("ok"):
                        print(f" Settled factoring: agent receives ${factoring_result.get('agent_payout')} holdback")
            except Exception as e:
                print(f" Factoring settlement failed: {e}")
                factoring_result = {"ok": False, "error": str(e)}
        
        # ✅ 2. AUTO-REPAY OCL from earnings
        repay_result = None
        if net_amt > 0:
            try:
                repay_result = await auto_repay_ocl(u, net_amt)
            except Exception as e:
                print(f"⚠️ OCL repayment failed: {e}")
                repay_result = {"ok": False, "error": str(e)}
        
        # ✅ SAVE USERS
        await _save_users(client, users)
        
        # ✅ RETURN
        return {
            "ok": True,
            "invoice": invoice,
            "fee": {"rate": fee_rate, "amount": fee_amt},
            "net": net_amt,
            "factoring_settlement": factoring_result,
            "ocl_repayment": repay_result
        }
        

@app.post("/outcome/attribute")
async def outcome_attribute(body: Dict = Body(...)):
    """
    Called when revenue is attributed to a channel.
    Updates Outcome Oracle + triggers R³ reallocation.
    """
    username = body.get("username")
    channel = body.get("channel")
    revenue = float(body.get("revenue_usd", 0))
    spend = float(body.get("spend_usd", 0))
    
    if not (username and channel and revenue):
        return {"error": "username, channel, revenue_usd required"}
    
    # Calculate ROAS
    roas = round(revenue / spend, 2) if spend > 0 else 0.0
    cpa = round(spend / revenue, 2) if revenue > 0 else 0.0
    
    # Update Outcome Oracle
    try:
        from outcome_oracle_MAX import on_event
        on_event({
            "kind": "ATTRIBUTED",
            "username": username,
            "value_usd": revenue,
            "channel": channel,
            "provider": channel
        })
    except Exception as e:
        print(f"Oracle update failed: {e}")
    
    # Update R³ channel pacing
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(
                "https://aigentsy-ame-runtime.onrender.com/r3/pacing/update",
                json={
                    "user_id": username,
                    "channel": channel,
                    "performance": {
                        "roas": roas,
                        "cpa": cpa,
                        "revenue": revenue,
                        "spend": spend
                    }
                }
            )
        except Exception as e:
            print(f"R³ pacing update failed: {e}")
    
    return {
        "ok": True,
        "attribution": {
            "user": username,
            "channel": channel,
            "revenue": revenue,
            "spend": spend,
            "roas": roas,
            "cpa": cpa
        }
    }
    
@app.post("/budget/spend")
async def budget_spend(body: Dict = Body(...)):
    username = body.get("username"); amount = float(body.get("amount", 0))
    basis = body.get("basis", "media_spend"); ref = body.get("ref")
    if not (username and amount): return {"error": "username & amount required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        if not _can_spend(u, amount): 
            return {"error": "daily budget exceeded"}
        _spend(u, amount, basis, ref)
        await _save_users(client, users)
        return {"ok": True, "spent_today": _current_spend(u)[0][_today_key()], "summary": _money_summary(u)}

@app.post("/events/log")
async def events_log(body: Dict = Body(...)):
    username = body.get("username"); ev = body.get("event")
    if not (username and isinstance(ev, dict)): return {"error":"username & event required"}
    async with httpx.AsyncClient(timeout=15) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        ev.setdefault("ts", _now())
        u.setdefault("events", []).append(ev)  # {playbook, channel, kind, cost?, revenue?}
        await _save_users(client, users)
        return {"ok": True}

@app.post("/attribution/rollup")
async def attribution_rollup(body: Dict = Body(...)):
    username = body.get("username")
    if not username: return {"error":"username required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        data = {}
        for ev in u.get("events", []):
            key = (ev.get("playbook") or "unknown", ev.get("channel") or "unknown")
            data.setdefault(key, {"spend":0.0,"rev":0.0,"count":0})
            data[key]["spend"] += float(ev.get("cost",0))
            data[key]["rev"]   += float(ev.get("revenue",0))
            data[key]["count"] += 1
        table = [{"playbook":k[0], "channel":k[1], "spend":round(v["spend"],2),
                  "revenue":round(v["rev"],2), "roas": round((v["rev"]/v["spend"]) if v["spend"] else 0, 2),
                  "events": v["count"]} for k,v in data.items()]
        table.sort(key=lambda r: r["roas"], reverse=True)
        return {"ok": True, "by_channel": table[:20]}

@app.post("/automatch/pulse")
async def automatch_pulse(body: Dict = Body(...)):
    username = body.get("username"); unit_spend = float(body.get("unitSpend", 1.0))
    if not username: return {"error":"username required"}
    async with httpx.AsyncClient(timeout=25) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        enabled = ((u.get("playbooks", {}) or {}).get("enabled", []))  # catalog code(s)
        actions = []
        for code in enabled:
            if not _can_spend(u, unit_spend): break
            # “fire” a tiny action – e.g., a post, an email, a DM; here we just log outreach
            u.setdefault("transactions", {}).setdefault("outreachEvents", []).append(
                {"code": code, "delivered": True, "ts": _now()}
            )
            _spend(u, unit_spend, basis="media_spend", ref=code)
            actions.append({"code": code, "spent": unit_spend})
        await _save_users(client, users)
        return {"ok": True, "fired": actions, "spent_today": _current_spend(u)[0][_today_key()]}

# ===== Monetize toggle (AL1 by default with budget/quietHours guardrails) =====
@app.post("/monetize/toggle")
async def monetize_toggle(body: Dict = Body(...)):
    """
    Body: { username, enabled: bool, dailyBudget?: number, quietHours?: [22,8] }
    Sets runtimeFlags.monetizeEnabled and basic guardrails.
    """
    username = body.get("username"); enabled = bool(body.get("enabled", False))
    budget = float(body.get("dailyBudget", 10))  # default $10/day
    quiet = body.get("quietHours", [22, 8])

    if not username: return {"error":"username required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        u.setdefault("runtimeFlags", {})["monetizeEnabled"] = enabled
        u.setdefault("policy", {}).setdefault("guardrails", {})
        u["policy"]["guardrails"]["dailyBudget"] = budget
        u["policy"]["guardrails"]["quietHours"] = quiet
        users = users  # no-op, clarity
        await _save_users(client, users)
        return {"ok": True, "monetizeEnabled": enabled, "policy": u.get("policy", {})}

# ===== Playbook catalog (static examples) =====
_PLAYBOOK_CATALOG = [
    {
        "code": "tiktok_affiliate",
        "title": "TikTok → Affiliate Links",
        "requires": ["content_out"],
        "default_budget": 0,
        "steps": ["connect_tiktok","fetch_trending","render_script","post_with_disclosure","track_clicks"]
    },
    {
        "code": "email_audit_to_checkout",
        "title": "Email Audit → Stripe Checkout",
        "requires": ["email_out","calendar","commerce_in"],
        "default_budget": 10,
        "steps": ["send_audit_offer","book_meeting","issue_checkout"]
    },
    {
        "code": "shorts_calendar_checkout",
        "title": "Shorts → Calendar → Checkout",
        "requires": ["content_out","calendar","commerce_in"],
        "default_budget": 5,
        "steps": ["generate_short","post_short","send_booking","send_payment_link"]
    },
]

@app.get("/playbooks/catalog")
async def playbooks_catalog():
    return {"ok": True, "catalog": _PLAYBOOK_CATALOG}

# ===== User playbooks enable/config =====
@app.post("/playbooks/enable")
async def playbooks_enable(body: Dict = Body(...)):
    """
    Body: { username, codes: ["tiktok_affiliate", ...], enabled: true|false }
    """
    username = body.get("username"); codes = body.get("codes", []); enabled = bool(body.get("enabled", True))
    if not (username and codes): return {"error":"username & codes required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        cfg = u.setdefault("playbooks", {"enabled": [], "configs": {}})
        if enabled:
            for c in codes:
                if c not in cfg["enabled"]: cfg["enabled"].append(c)
        else:
            cfg["enabled"] = [c for c in cfg["enabled"] if c not in codes]
        await _save_users(client, users)
        return {"ok": True, "playbooks": cfg}

@app.post("/playbooks/config")
async def playbooks_config(body: Dict = Body(...)):
    """
    Body: { username, code, config: { budget?:number, notes?:str } }
    """
    username = body.get("username"); code = body.get("code"); config = body.get("config", {})
    if not (username and code): return {"error":"username & code required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        pb = u.setdefault("playbooks", {"enabled": [], "configs": {}})
        pb["configs"][code] = {**pb["configs"].get(code, {}), **config, "updated": _now()}
        await _save_users(client, users)
        return {"ok": True, "playbooks": pb}

# ---------- 2) FULFILLMENT ----------
@app.post("/orders/{orderId}/tasks/add")
async def order_task_add(orderId: str = Path(...), body: Dict = Body(...)):
    username = body.get("username"); title = body.get("title")
    if not (username and title): return {"error":"username & title required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        order = _find_in(u["orders"], "id", orderId)
        if not order: return {"error":"order not found"}
        t = {"id": _id("t"), "title": title, "assignee": body.get("assignee"), "due": body.get("due"),
             "status":"todo", "ts": _now()}
        order.setdefault("tasks", []).append(t)
        await _save_users(client, users)
        return {"ok": True, "task": t}

@app.post("/orders/{orderId}/tasks/done")
async def order_task_done(orderId: str = Path(...), body: Dict = Body(...)):
    username = body.get("username"); tid = body.get("taskId")
    if not (username and tid): return {"error":"username & taskId required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        order = _find_in(u["orders"], "id", orderId)
        if not order: return {"error":"order not found"}
        for t in order.get("tasks", []):
            if t.get("id") == tid:
                t["status"] = "done"; t["done_ts"] = _now()
        await _save_users(client, users)
        return {"ok": True, "order": order}

@app.post("/orders/{orderId}/status")
async def order_status(orderId: str = Path(...), body: Dict = Body(...)):
    username = body.get("username"); status = body.get("status")
    if not (username and status): return {"error":"username & status required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        order = _find_in(u["orders"], "id", orderId)
        if not order: return {"error":"order not found"}
        order["status"] = status; order["status_ts"] = _now()
        if status == "blocked":
            order.setdefault("sla", {}).setdefault("breaches", 0)
            order["sla"]["breaches"] += 1
        await _save_users(client, users)
        return {"ok": True, "order": order}

# ---------- 3) PROPOSAL FOLLOW-UPS ----------
def _schedule_followups(base_ts: datetime) -> List[Dict[str, Any]]:
    return [
        {"id": _id("fu"), "when": (base_ts+timedelta(days=1)).isoformat(), "status":"scheduled"},
        {"id": _id("fu"), "when": (base_ts+timedelta(days=3)).isoformat(), "status":"scheduled"},
        {"id": _id("fu"), "when": (base_ts+timedelta(days=7)).isoformat(), "status":"scheduled"},
    ]

@app.post("/proposal/{proposalId}/followup/schedule")
async def proposal_followup_schedule(proposalId: str = Path(...), body: Dict = Body(...)):
    username = body.get("username")
    if not username: return {"error":"username required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        p = _find_in(u["proposals"], "id", proposalId)
        if not p: return {"error":"proposal not found"}
        p.setdefault("followups", []).extend(_schedule_followups(datetime.utcnow()))
        await _save_users(client, users)
        return {"ok": True, "followups": p["followups"]}

@app.post("/proposal/{proposalId}/followup/send")
async def proposal_followup_send(proposalId: str = Path(...), body: Dict = Body(...)):
    username = body.get("username"); fid = body.get("followupId")
    if not (username and fid): return {"error":"username & followupId required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        p = _find_in(u["proposals"], "id", proposalId)
        if not p: return {"error":"proposal not found"}
        for fu in p.get("followups", []):
            if fu["id"] == fid:
                fu["status"] = "sent"; fu["sent_ts"] = _now()
        await _save_users(client, users)
        return {"ok": True}

# ---------- 4) SCHEDULING + NOTES ----------
@app.post("/schedule/create")
async def schedule_create(body: Dict = Body(...)):
    username = body.get("username"); pid = body.get("proposalId")
    if not username: return {"error":"username required"}
    booking_id = _id("meet")
    url = f"https://meet.aigentsy/book/{booking_id}"
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        u.setdefault("meetings", [])
        meeting = {"id": booking_id, "proposalId": pid, "booking_url": url, "status":"pending", "ts": _now()}
        u["meetings"].append(meeting)
        await _save_users(client, users)
        return {"ok": True, "booking_url": url, "meeting": meeting}

@app.post("/meeting/notes")
async def meeting_notes(body: Dict = Body(...)):
    username = body.get("username"); pid = body.get("proposalId"); notes = body.get("notes","")
    if not (username and pid): return {"error":"username & proposalId required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        u.setdefault("meetings", [])
        mt = {"id": _id("note"), "proposalId": pid, "notes": notes[:5000], "ts": _now()}
        u["meetings"].append(mt)
        await _save_users(client, users)
        return {"ok": True, "note": mt}

# ---------- 5) CRM-LITE ----------
@app.post("/contacts/import")
async def contacts_import(request: Request, x_api_key: str | None = Header(None, alias='X-API-Key')):
    body = await request.json()
    username = body.get("username")
    if not username: return {"error":"username required"}
    new_contacts: List[Dict[str, Any]] = []
    if body.get("contacts"):
        for c in body["contacts"]:
            c["id"] = _id("c"); c.setdefault("tags",[]); c.setdefault("opt_in", False)
            new_contacts.append(c)
    elif body.get("csv"):
        reader = csv.DictReader(io.StringIO(body["csv"]))
        for row in reader:
            new_contacts.append({"id": _id("c"), "name": row.get("name"), "email": row.get("email"),
                                 "tags": [], "opt_in": False})
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        _require_key(users, username, x_api_key)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        u.setdefault("crm", []).extend(new_contacts)
        await _save_users(client, users)
        return {"ok": True, "added": len(new_contacts)}

@app.post("/contacts/segment")
async def contacts_segment(request: Request, x_api_key: str | None = Header(None, alias='X-API-Key')):
    body = await request.json()
    username = body.get("username"); ids = body.get("ids", []); tags = body.get("tags", [])
    if not (username and ids and tags): return {"error":"username, ids, tags required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        _require_key(users, username, x_api_key)
        if not u: return {"error":"user not found"}
        for c in u.get("crm", []):
            if c["id"] in ids:
                c.setdefault("tags", [])
                for t in tags:
                    if t not in c["tags"]: c["tags"].append(t)
        await _save_users(client, users)
        return {"ok": True}

@app.post("/contacts/optout")
async def contacts_optout(request: Request, x_api_key: str | None = Header(None, alias='X-API-Key')):
    body = await request.json()
    username = body.get("username"); email = (body.get("email") or "").lower()
    if not (username and email): return {"error":"username & email required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        _require_key(users, username, x_api_key)
        if not u: return {"error":"user not found"}
        for c in u.get("crm", []):
            if (c.get("email") or "").lower() == email:
                c["opt_in"] = False; c.setdefault("tags", []).append("opt_out")
        await _save_users(client, users)
        return {"ok": True}

# ---------- 6) VALUE ROUTER / PRICING (A/B) ----------
@app.post("/pricing/decide")
async def pricing_decide(body: Dict = Body(...)):
    offer = (body.get("offer") or "").lower()
    base = 149 if "branding" in offer else 199 if "sdk" in offer else 99
    win = 0.62 if base == 149 else 0.48 if base == 199 else 0.55
    ev = round(base * win, 2)
    return {"price": base, "win_prob": win, "ev": ev}

@app.post("/pricing/ab/assign")
async def pricing_ab_assign(body: Dict = Body(...)):
    import random
    username = body.get("username"); offer = body.get("offer")
    if not (username and offer): return {"error":"username & offer required"}
    variant = "A" if random.random() < 0.5 else "B"
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        u["experiments"].append({"id": _id("ab"), "offer": offer, "variant": variant, "ts": _now()})
        await _save_users(client, users)
        return {"ok": True, "variant": variant}

@app.post("/pricing/ab/result")
async def pricing_ab_result(body: Dict = Body(...)):
    username = body.get("username"); eid = body.get("experimentId"); result = body.get("result")
    if not (username and eid and result): return {"error":"username, experimentId, result required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        for e in u.get("experiments", []):
            if e["id"] == eid: e["result"] = result; e["result_ts"] = _now()
        await _save_users(client, users)
        return {"ok": True}

# ---------- 7) CONSENT VAULT + DOCS ----------
@app.post("/doc/generate")
async def doc_generate(body: Dict = Body(...)):
    username = body.get("username"); dtype = body.get("type")
    if not (username and dtype): return {"error":"username & type required"}
    content = f"{dtype} TEMPLATE v1 :: generated {datetime.utcnow().isoformat()}"
    doc_id = _id("doc"); hashv = hashlib.sha256(content.encode()).hexdigest()
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        doc = {"id": doc_id, "type": dtype, "ref": body.get("ref"), "hash": hashv, "ts": _now()}
        u["docs"].append(doc)
        await _save_users(client, users)
        return {"ok": True, "doc": doc, "content": content}

@app.post("/doc/attach")
async def doc_attach(body: Dict = Body(...)):
    username = body.get("username"); docId = body.get("docId")
    if not (username and docId): return {"error":"username & docId required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        target = {"proposalId": body.get("proposalId"), "orderId": body.get("orderId")}
        for d in u["docs"]:
            if d["id"] == docId: d["attached_to"] = target; d["attached_ts"] = _now()
        await _save_users(client, users)
        return {"ok": True}

# ---------- 8) KPI AUTOPILOT ----------
@app.post("/kpi/rollup")
async def kpi_rollup(body: Dict = Body(...)):
    username = body.get("username")
    if not username: return {"error":"username required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        cash = float(u["ownership"].get("aigx", 0))
        burn = 100.0
        runway = int(cash / burn) if burn else 0
        pipeline = sum(float(q.get("price",0)) for q in u["quotes"] if q.get("status")=="offered")
        won = sum(1 for e in u.get("experiments",[]) if e.get("result")=="won")
        total = sum(1 for e in u.get("experiments",[]) if e.get("result"))
        close = (won/total) if total else 0.0
        snap = {"ts": _now(), "runway_days": runway, "mrr": 0, "pipeline_value": pipeline, "close_rate": round(close,2)}
        u["kpi_snapshots"].append(snap)
        await _save_users(client, users)
        return {"ok": True, "snapshot": snap}

@app.post("/kpi/forecast")
async def kpi_forecast(body: Dict = Body(...)):
    username = body.get("username"); horizon = int(body.get("horizon",30))
    if not username: return {"error":"username required"}
    growth = 1.15 if horizon==30 else 1.32 if horizon==60 else 1.5
    return {"ok": True, "horizon": horizon, "projected_pipeline": growth}

# ---------- 9) SUPPORT • NPS • TESTIMONIALS ----------
@app.post("/support/create")
async def support_create(body: Dict = Body(...)):
    username = body.get("username"); subject = body.get("subject"); description = body.get("description","")
    if not (username and subject): return {"error":"username & subject required"}
    tid = _id("ticket")
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        t = {"id": tid, "subject": subject, "description": description, "status":"open", "ts": _now()}
        u["tickets"].append(t); await _save_users(client, users)
        return {"ok": True, "ticket": t}

@app.post("/support/status")
async def support_status(body: Dict = Body(...)):
    username = body.get("username"); tid = body.get("ticketId"); status = body.get("status")
    if not (username and tid and status): return {"error":"username, ticketId, status required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        for t in u.get("tickets", []):
            if t["id"] == tid: t["status"] = status; t["status_ts"] = _now()
        await _save_users(client, users)
        return {"ok": True}

@app.post("/nps/ping")
async def nps_ping(body: Dict = Body(...)):
    username = body.get("username")
    if not username: return {"error":"username required"}
    nid = _id("nps")
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        u.setdefault("nps", []).append({"id": nid, "orderId": body.get("orderId"), "status":"sent", "ts": _now()})
        await _save_users(client, users)
        return {"ok": True, "nps": nid}

@app.post("/nps/submit")
async def nps_submit(body: Dict = Body(...)):
    username = body.get("username"); nid = body.get("npsId"); score = int(body.get("score",0))
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        for n in u.get("nps", []):
            if n["id"] == nid: n["status"]="answered"; n["score"]=score; n["comment"]=body.get("comment"); n["answered_ts"]=_now()
        await _save_users(client, users)
        return {"ok": True}

@app.post("/testimonial/add")
async def testimonial_add(body: Dict = Body(...)):
    username = body.get("username"); text = body.get("text")
    if not (username and text): return {"error":"username & text required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        u.setdefault("testimonials", []).append({"id": _id("tm"), "text": text[:1000], "ref": body.get("ref"), "ts": _now()})
        await _save_users(client, users)
        return {"ok": True}

# ---------- 10) IDENTITY & COLLECTIBLES ----------
@app.post("/collectible/award")
async def collectible_award(body: Dict = Body(...)):
    username = body.get("username"); ctype = body.get("type")
    if not (username and ctype): return {"error":"username & type required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        u.setdefault("collectibles", []).append({"id": _id("cb"), "type": ctype, "ref": body.get("ref"), "ts": _now()})
        await _save_users(client, users)
        return {"ok": True}

# ---------- 11) MARKETPLACE LISTINGS ----------
@app.post("/listing/publish")
async def listing_publish(body: Dict = Body(...)):
    username = body.get("username"); title = body.get("title"); price = float(body.get("price",0))
    channel = body.get("channel","internal")
    if not (username and title): return {"error":"username & title required"}
    lid = _id("lst")
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        l = {"id": lid, "title": title, "price": price, "channel": channel, "status":"published", "ts": _now(),
             "impressions":0, "clicks":0}
        u["listings"].append(l); await _save_users(client, users)
        return {"ok": True, "listing": l}

@app.post("/listing/status")
async def listing_status(body: Dict = Body(...)):
    username = body.get("username"); lid = body.get("listingId"); status = body.get("status")
    if not (username and lid and status): return {"error":"username, listingId, status required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        for l in u.get("listings", []):
            if l["id"] == lid: l["status"]=status; l["status_ts"]=_now()
        await _save_users(client, users)
        return {"ok": True}

# ---------- 12) SECURITY / RBAC / AUDIT ----------
@app.post("/apikey/issue")
async def apikey_issue(body: Dict = Body(...)):
    username = body.get("username"); label = body.get("label","default")
    if not username: return {"error":"username required"}
    key = uuid.uuid4().hex + uuid.uuid4().hex
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        u.setdefault("api_keys", []).append({"id": _id("key"), "label": label, "key": key, "ts": _now(), "revoked": False})
        await _save_users(client, users)
        return {"ok": True, "key": key}

@app.post("/apikey/revoke")
async def apikey_revoke(body: Dict = Body(...)):
    username = body.get("username"); key = body.get("key")
    if not (username and key): return {"error":"username & key required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        for k in u.get("api_keys", []):
            if k["key"] == key: k["revoked"] = True; k["revoked_ts"]=_now()
        await _save_users(client, users)
        return {"ok": True}

@app.post("/roles/grant")
async def roles_grant(body: Dict = Body(...)):
    username = body.get("username"); role = body.get("role"); grantee = body.get("grantee")
    if not (username and role and grantee): return {"error":"username, role, grantee required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client); u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        u.setdefault("roles", []).append({"role": role, "grantee": grantee, "ts": _now()})
        await _save_users(client, users)
        return {"ok": True}

@app.post("/roles/revoke")
async def roles_revoke(body: Dict = Body(...)):
    username = body.get("username"); role = body.get("role"); grantee = body.get("grantee")
    if not (username and role and grantee): return {"error":"username, role, grantee required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        u["roles"] = [r for r in u.get("roles", []) if not (r["role"]==role and r["grantee"]==grantee)]
        await _save_users(client, users)
        return {"ok": True}

@app.post("/audit/log")
async def audit_log(body: Dict = Body(...)):
    username = body.get("username"); action = body.get("action")
    if not (username and action): return {"error":"username & action required"}
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        u = next((x for x in users if _uname(x)==username), None)
        if not u: return {"error":"user not found"}
        _ensure_business(u)
        u.setdefault("audit", []).append({"id": _id("audit"), "action": action, "ref": body.get("ref"), "meta": body.get("meta"), "ts": _now()})
        await _save_users(client, users)
        return {"ok": True}

# ================================
# >>> Two essential patches <<<
# ================================

# ---- PATCH: /submit_proposal (adds id, status, followups) ----
@app.post("/submit_proposal")
async def submit_proposal(request: Request):
    body = await request.json()
    sender = body.get("sender")
    if not sender:
        return {"error": "missing sender"}
    # ensure minimal shape
    pid = body.get("id") or f"prop_{uuid.uuid4().hex[:10]}"
    body["id"] = pid
    body.setdefault("timestamp", _now())
    body.setdefault("status", "sent")
    body.setdefault("followups", [])
    body.setdefault("meta", {})
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            users = await _load_users(client)
            u = next((x for x in users if _uname(x)==sender), None)
            if not u:
                return {"error": f"user {sender} not found"}
            _ensure_business(u)
            u["proposals"].append(body)
            await _save_users(client, users)
            return {"ok": True, "proposal": body}
    except Exception as e:
        return {"error": f"submit_proposal_failed: {e}"}

# ---- PATCH: /earn/task/complete (direct ledger; no localhost hop) ----
@app.post("/earn/task/complete")
async def earn_task_complete(request: Request):
    body = await request.json()
    username = body.get("username")
    task = body.get("taskId")
    if not (username and task):
        return {"error":"username & taskId required"}
    payout = 1.0
    if task == "promo-15s": payout = 2.0
    elif task == "scan-receipt": payout = 1.5
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            users = await _load_users(client)
            u = next((x for x in users if _uname(x)==username), None)
            if not u: return {"error":"user not found"}
            _ensure_business(u)
            entry = {"ts": _now(), "amount": payout, "currency": "AIGx", "basis": "task", "ref": task}
            u["ownership"]["ledger"].append(entry)
            u["ownership"]["aigx"] = float(u["ownership"].get("aigx",0)) + payout
            u["yield"]["aigxEarned"] = float(u["yield"].get("aigxEarned",0)) + payout
            await _save_users(client, users)
            return {"ok": True, "ledgerEntry": entry}
    except Exception as e:
        return {"error": f"earn_complete_error: {e}"}

# --- Admin normalize route ---
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")

class AdminIn(BaseModel):
    token: str

@app.post("/admin/normalize")
async def admin_normalize(a: AdminIn):
    if not ADMIN_TOKEN or a.token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="forbidden")
    data = await run_in_threadpool(_bin_get)
    records = data["record"] if isinstance(data, dict) and "record" in data else data
    if not isinstance(records, list):
        raise HTTPException(status_code=500, detail="bin payload not a list")
    upgraded = [normalize_user_data(r) for r in records]
    await run_in_threadpool(_bin_put, upgraded)
    return {"ok": True, "count": len(upgraded)}

from urllib.parse import urlparse
import ipaddress, socket

ALLOWED_DIST_DOMAINS = [d.strip() for d in os.getenv("ALLOWED_DIST_DOMAINS", "hooks.slack.com,discord.com,api.telegram.org").split(",") if d.strip()]

def _safe_url(u: str) -> bool:
    try:
        p = urlparse(u)
        if p.scheme not in ("https", "http"):
            return False
        host = p.hostname or ""
        if not any(host.endswith(d) for d in ALLOWED_DIST_DOMAINS):
            return False
        try:
            infos = socket.getaddrinfo(host, None)
        except Exception:
            return False
        ips = {ai[4][0] for ai in infos if ai and ai[4]}
        for ip in ips:
            try:
                ipaddr = ipaddress.ip_address(ip)
            except Exception:
                return False
            if ipaddr.is_private or ipaddr.is_loopback or ipaddr.is_link_local:
                return False
        return True
    except Exception:
        return False


from fastapi import HTTPException



EVENT_BUS = asyncio.Queue()

async def publish(evt: dict):
    try:
        await EVENT_BUS.put(json.dumps(evt))
    except Exception:
        pass

@app.get("/stream/activity")
async def stream_activity():
    async def gen():
        while True:
            msg = await EVENT_BUS.get()
            yield f"data: {msg}\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream")

def _find_proposal(u, proposal_id):
    for p in u.get("proposals", []):
        if p.get("id")==proposal_id:
            return p
    return None

ProposalOutcome = Literal["won","lost","ignored","replied"]

@app.post("/proposal/feedback")
async def proposal_feedback(username: str, proposal_id: str, outcome: ProposalOutcome, weight: float = 1.0, x_api_key: str = Header("")):
    users, client = await _get_users_client()
    _require_key(users, username, x_api_key)
    u = _find_user(users, username)
    if not u: return {"error":"user not found"}
    u.setdefault("runtimeWeights", {"keywords": {}, "platforms": {}})
    p = _find_proposal(u, proposal_id)
    if not p: return {"error":"proposal not found"}
    meta = p.get("meta", {})
    kws = meta.get("keywords", []) or []
    plat = meta.get("platform", "internal")
    for k in kws:
        u["runtimeWeights"]["keywords"][k] = u["runtimeWeights"]["keywords"].get(k, 0.0) + (1.0 if outcome=="won" else (-0.5 if outcome=="ignored" else (0.2 if outcome=="replied" else -1.0)))*weight
    u["runtimeWeights"]["platforms"][plat] = u["runtimeWeights"]["platforms"].get(plat, 0.0) + (1.0 if outcome=="won" else -0.2)
    await _save_users(client, users)
    return {"ok": True, "weights": u["runtimeWeights"]}


AGENT_WEBHOOKS = {
    "cfo":   os.getenv("VENTURE_AGENT_URL"),
    "cmo":   os.getenv("GROWTH_AGENT_URL"),
    "clo":   os.getenv("REMIX_AGENT_URL"),
    "cto":   os.getenv("SDK_AGENT_URL"),
}

async def _broadcast_yield(u, event):
    try:
        import httpx
    except Exception:
        return
    payload = {"username": (u.get("username") or u.get("consent",{}).get("username")), "event": event, "ts": _now()}
    async with httpx.AsyncClient(timeout=8.0) as h:
        for name, url in AGENT_WEBHOOKS.items():
            if not url: continue
            try:
                await h.post(f"{url.rstrip('/')}/autopropagate", json=payload)
            except Exception:
                pass

def _verify_signature(body: bytes, ts: str, sign: str):
    secret = os.getenv("HMAC_SECRET","")
    if not secret:
        return True
    mac = hmac.new(secret.encode(), (ts+"."+body.decode()).encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac, sign)

@app.middleware("http")
async def hmac_guard(request, call_next):
    protected = ("/submit_proposal","/aigx/credit","/unlock")
    if any(request.url.path.startswith(p) for p in protected):
        ts = request.headers.get("X-Ts"); sign = request.headers.get("X-Sign")
        body = await request.body()
        if not _verify_signature(body, ts or "", sign or ""):
            from fastapi.responses import JSONResponse
            return JSONResponse({"error":"bad signature"}, status_code=401)
        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}
        request._receive = receive
    return await call_next(request)


# ========= AiGentsy Consumer-First Upgrades (Storefront, Widget, PoO-Lite, Intent Auction, Productizer, Quotes, Escrow, etc.) =========

def _uid():
    return str(uuid.uuid4())

def _username_of(u):
    return u.get("username") or u.get("consent",{}).get("username")

def _global_find_intent(users, intent_id):
    for u in users:
        for it in u.get("intents", []):
            if it.get("id")==intent_id:
                return u, it
    return None, None

@app.get("/storefront/config")
async def storefront_get_config(username: str):
    users, client = await _get_users_client()
    u = _find_user(users, username)
    if not u: return {"error":"user not found"}
    cfg = u.setdefault("storefront", {"theme":"light","palette":"default","hero_video":None,"offers":[], "kits":[], "badges":[], "social":{}})
    return {"ok": True, "config": cfg}

@app.post("/storefront/config")
async def storefront_set_config(username: str, config: dict):
    users, client = await _get_users_client()
    u = _find_user(users, username)
    if not u: return {"error":"user not found"}
    u["storefront"] = {**u.get("storefront", {}), **(config or {})}
    await _save_users(client, users)
    return {"ok": True, "config": u["storefront"]}

@app.post("/storefront/publish")
async def storefront_publish(username: str, base_url: Optional[str] = None):
    users, client = await _get_users_client()
    u = _find_user(users, username)
    if not u: return {"error":"user not found"}
    u.setdefault("storefront", {}).update({"published": _now()})
    slug = _username_of(u)
    url = f"{(base_url or os.getenv('PUBLIC_BASE','https://aigentsy.com')).rstrip('/')}/u/{slug}"
    u["storefront"]["url"] = url
    await _save_users(client, users)
    return {"ok": True, "url": url}

@app.post("/analytics/track")
async def analytics_track(username: str, event: dict):
    users, client = await _get_users_client()
    u = _find_user(users, username)
    if not u: return {"error":"user not found"}
    q = u.setdefault("analytics", [])
    event = {"id": _uid(), "ts": _now(), **(event or {})}
    q.append(event)
    await _save_users(client, users)
    try:
        await publish({"type":"analytics","user":username,"event":event})
    except Exception:
        pass
    return {"ok": True}

# ============ OCL (OUTCOME-BACKED CREDIT LINE) ============

@app.get("/credit/status")
async def ocl_status(username: str):
    """Get OCL credit status"""
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        u = _find_user(users, username)
        if not u: return {"error": "user not found"}
        
        limits = await calculate_ocl_limit(u)
        return {"ok": True, **limits}

@app.post("/credit/spend")
async def ocl_spend_endpoint(body: Dict = Body(...)):
    """Spend from OCL"""
    username = body.get("username")
    amount = float(body.get("amount", 0))
    ref = body.get("ref", "purchase")
    
    if not username or not amount:
        return {"error": "username and amount required"}
    
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        u = _find_user(users, username)
        if not u: return {"error": "user not found"}
        
        result = await spend_ocl(u, amount, ref)
        
        if result["ok"]:
            await _save_users(client, users)
        
        return result

@app.post("/credit/repay")
async def ocl_repay_endpoint(body: Dict = Body(...)):
    """Manual OCL repayment"""
    username = body.get("username")
    amount = float(body.get("amount", 0))
    
    if not username or not amount:
        return {"error": "username and amount required"}
    
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        u = _find_user(users, username)
        if not u: return {"error": "user not found"}
        
        # Add repayment entry
        entry = {
            "ts": _now(),
            "amount": float(amount),
            "currency": "USD",
            "basis": "ocl_repay",
            "ref": "manual_repay"
        }
        
        u.setdefault("ownership", {}).setdefault("ledger", []).append(entry)
        await _save_users(client, users)
        
        limits = await calculate_ocl_limit(u)
        return {"ok": True, "repaid": amount, **limits}

# ============ ESCROW-LITE (AUTH→CAPTURE) ============

from escrow_lite import (
    create_payment_intent,
    capture_payment,
    cancel_payment,
    get_payment_status,
    auto_capture_on_delivered,
    auto_timeout_release,
    partial_refund_on_dispute
)

@app.post("/escrow/create_intent")
async def create_escrow_intent(body: Dict = Body(...)):
    """
    Create payment intent (authorize but don't capture)
    Called when buyer accepts a quote
    """
    buyer = body.get("buyer")
    amount = float(body.get("amount", 0))
    intent_id = body.get("intent_id")
    buyer_email = body.get("buyer_email", f"{buyer}@aigentsy.com")
    
    if not all([buyer, amount, intent_id]):
        return {"error": "buyer, amount, intent_id required"}
    
    # Create Stripe PaymentIntent
    result = await create_payment_intent(
        amount=amount,
        buyer_email=buyer_email,
        intent_id=intent_id,
        metadata={"buyer": buyer}
    )
    
    if result["ok"]:
        # Store payment intent ID with the intent
        async with httpx.AsyncClient(timeout=20) as client:
            users = await _load_users(client)
            
            # Find buyer's intent
            buyer_user = _find_user(users, buyer)
            if buyer_user:
                for intent in buyer_user.get("intents", []):
                    if intent.get("id") == intent_id:
                        intent["payment_intent_id"] = result["payment_intent_id"]
                        intent["escrow_status"] = "authorized"
                        intent["escrow_created_at"] = _now()
                        break
                
                await _save_users(client, users)
    
    return result

@app.post("/escrow/capture")
async def capture_escrow(body: Dict = Body(...)):
    """
    Capture authorized payment (called on DELIVERED)
    """
    intent_id = body.get("intent_id")
    partial_amount = body.get("amount")  # Optional: for partial captures
    
    if not intent_id:
        return {"error": "intent_id required"}
    
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        
        # Find intent with payment_intent_id
        payment_intent_id = None
        intent_owner = None
        target_intent = None
        
        for user in users:
            for intent in user.get("intents", []):
                if intent.get("id") == intent_id:
                    payment_intent_id = intent.get("payment_intent_id")
                    intent_owner = user
                    target_intent = intent
                    break
            if payment_intent_id:
                break
        
        if not payment_intent_id:
            return {"error": "payment_intent not found"}
        
        # Check for disputes
        result = await auto_capture_on_delivered(target_intent)
        
        if result["ok"]:
            # Update intent status
            target_intent["payment_captured"] = True
            target_intent["payment_captured_at"] = _now()
            target_intent["escrow_status"] = "captured"
            
            await _save_users(client, users)
        
        return result

@app.post("/escrow/cancel")
async def cancel_escrow(body: Dict = Body(...)):
    """
    Cancel authorized payment (dispute or timeout)
    """
    intent_id = body.get("intent_id")
    reason = body.get("reason", "dispute")
    
    if not intent_id:
        return {"error": "intent_id required"}
    
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        
        # Find payment intent
        payment_intent_id = None
        target_intent = None
        
        for user in users:
            for intent in user.get("intents", []):
                if intent.get("id") == intent_id:
                    payment_intent_id = intent.get("payment_intent_id")
                    target_intent = intent
                    break
            if payment_intent_id:
                break
        
        if not payment_intent_id:
            return {"error": "payment_intent not found"}
        
        # Cancel payment
        result = await cancel_payment(payment_intent_id)
        
        if result["ok"]:
            target_intent["escrow_status"] = "cancelled"
            target_intent["escrow_cancelled_at"] = _now()
            target_intent["escrow_cancel_reason"] = reason
            
            await _save_users(client, users)
        
        return result

@app.get("/escrow/status")
async def escrow_status(intent_id: str):
    """
    Check escrow/payment status
    """
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        
        # Find intent
        for user in users:
            for intent in user.get("intents", []):
                if intent.get("id") == intent_id:
                    payment_intent_id = intent.get("payment_intent_id")
                    
                    if payment_intent_id:
                        stripe_status = await get_payment_status(payment_intent_id)
                        
                        return {
                            "ok": True,
                            "intent_id": intent_id,
                            "escrow_status": intent.get("escrow_status"),
                            "stripe_status": stripe_status
                        }
                    else:
                        return {
                            "ok": True,
                            "intent_id": intent_id,
                            "escrow_status": "not_created"
                        }
        
        return {"error": "intent not found"}

@app.post("/escrow/refund")
async def escrow_refund(body: Dict = Body(...)):
    """
    Issue partial refund for dispute resolution
    """
    intent_id = body.get("intent_id")
    refund_amount = float(body.get("amount", 0))
    reason = body.get("reason", "dispute_resolution")
    
    if not all([intent_id, refund_amount]):
        return {"error": "intent_id and amount required"}
    
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        
        # Find payment intent
        payment_intent_id = None
        
        for user in users:
            for intent in user.get("intents", []):
                if intent.get("id") == intent_id:
                    payment_intent_id = intent.get("payment_intent_id")
                    break
            if payment_intent_id:
                break
        
        if not payment_intent_id:
            return {"error": "payment_intent not found"}
        
        # Issue refund
        result = await partial_refund_on_dispute(
            payment_intent_id=payment_intent_id,
            refund_amount=refund_amount,
            reason=reason
        )
        
        return result

# ============ PERFORMANCE BONDS + SLA BONUS ============

from performance_bonds import (
    stake_bond,
    return_bond,
    calculate_sla_bonus,
    award_sla_bonus,
    slash_bond,
    calculate_bond_amount
)

@app.post("/bond/stake")
async def stake_performance_bond(body: Dict = Body(...)):
    """
    Stake performance bond when accepting intent
    Auto-called on intent acceptance
    """
    username = body.get("username")
    intent_id = body.get("intent_id")
    
    if not all([username, intent_id]):
        return {"error": "username and intent_id required"}
    
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        user = _find_user(users, username)
        
        if not user:
            return {"error": "user not found"}
        
        # Find intent
        intent = None
        for u in users:
            for i in u.get("intents", []):
                if i.get("id") == intent_id:
                    intent = i
                    break
            if intent:
                break
        
        if not intent:
            return {"error": "intent not found"}
        
        # Stake bond
        result = await stake_bond(user, intent)
        
        if result["ok"]:
            await _save_users(client, users)
        
        return result

@app.post("/bond/return")
async def return_performance_bond(body: Dict = Body(...)):
    """
    Return bond on successful delivery
    Auto-called on PoO verification
    """
    username = body.get("username")
    intent_id = body.get("intent_id")
    
    if not all([username, intent_id]):
        return {"error": "username and intent_id required"}
    
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        user = _find_user(users, username)
        
        if not user:
            return {"error": "user not found"}
        
        # Find intent
        intent = None
        for u in users:
            for i in u.get("intents", []):
                if i.get("id") == intent_id:
                    intent = i
                    break
            if intent:
                break
        
        if not intent:
            return {"error": "intent not found"}
        
        # Return bond
        result = await return_bond(user, intent)
        
        if result["ok"]:
            await _save_users(client, users)
        
        return result

@app.post("/bond/award_bonus")
async def award_bonus(body: Dict = Body(...)):
    """
    Award SLA bonus for early delivery
    Auto-called on PoO verification
    """
    username = body.get("username")
    intent_id = body.get("intent_id")
    
    if not all([username, intent_id]):
        return {"error": "username and intent_id required"}
    
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        user = _find_user(users, username)
        
        if not user:
            return {"error": "user not found"}
        
        # Find intent
        intent = None
        for u in users:
            for i in u.get("intents", []):
                if i.get("id") == intent_id:
                    intent = i
                    break
            if intent:
                break
        
        if not intent:
            return {"error": "intent not found"}
        
        # Award bonus
        result = await award_sla_bonus(user, intent)
        
        if result["ok"]:
            await _save_users(client, users)
        
        return result

@app.post("/bond/slash")
async def slash_performance_bond(body: Dict = Body(...)):
    """
    Slash bond on dispute loss
    Called by dispute resolution system
    """
    username = body.get("username")
    intent_id = body.get("intent_id")
    severity = body.get("severity", "moderate")  # minor | moderate | major
    
    if not all([username, intent_id]):
        return {"error": "username and intent_id required"}
    
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        user = _find_user(users, username)
        
        if not user:
            return {"error": "user not found"}
        
        # Find intent
        intent = None
        for u in users:
            for i in u.get("intents", []):
                if i.get("id") == intent_id:
                    intent = i
                    break
            if intent:
                break
        
        if not intent:
            return {"error": "intent not found"}
        
        # Slash bond
        result = await slash_bond(user, intent, severity)
        
        if result["ok"]:
            await _save_users(client, users)
        
        return result

@app.get("/bond/calculate")
async def calculate_bond(order_value: float):
    """
    Calculate required bond for an order value
    """
    from performance_bonds import calculate_bond_amount
    result = calculate_bond_amount(order_value)
    return {"ok": True, **result}

# ============ PERFORMANCE INSURANCE POOL ============

from insurance_pool import (
    calculate_insurance_fee,
    collect_insurance,
    get_pool_balance,
    payout_from_pool,
    calculate_dispute_rate,
    calculate_annual_refund,
    issue_annual_refund
)

@app.get("/insurance/pool/balance")
async def insurance_pool_balance():
    """Get current insurance pool balance"""
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        
        # Find or create pool user
        pool_user = next((u for u in users if _uname(u) == "insurance_pool"), None)
        
        if not pool_user:
            # Create pool user
            pool_user = {
                "consent": {"username": "insurance_pool", "agreed": True, "timestamp": _now()},
                "username": "insurance_pool",
                "ownership": {"aigx": 0, "ledger": []},
                "role": "system",
                "created_at": _now()
            }
            users.append(pool_user)
            await _save_users(client, users)
        
        balance = await get_pool_balance(pool_user)
        
        # Calculate stats
        ledger = pool_user.get("ownership", {}).get("ledger", [])
        
        total_collected = sum([
            abs(float(e.get("amount", 0)))
            for e in ledger
            if e.get("basis") == "insurance_premium"
        ])
        
        total_paid_out = sum([
            abs(float(e.get("amount", 0)))
            for e in ledger
            if e.get("basis") == "insurance_payout"
        ])
        
        return {
            "ok": True,
            "balance": balance,
            "total_collected": round(total_collected, 2),
            "total_paid_out": round(total_paid_out, 2),
            "transaction_count": len(ledger)
        }

@app.post("/insurance/collect")
async def collect_insurance_fee(body: Dict = Body(...)):
    """
    Collect insurance fee when intent is awarded
    Auto-called by /intent/award
    """
    username = body.get("username")
    intent_id = body.get("intent_id")
    order_value = float(body.get("order_value", 0))
    
    if not all([username, intent_id, order_value]):
        return {"error": "username, intent_id, order_value required"}
    
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        
        # Find agent
        agent_user = _find_user(users, username)
        if not agent_user:
            return {"error": "agent not found"}
        
        # Find or create pool user
        pool_user = next((u for u in users if _uname(u) == "insurance_pool"), None)
        if not pool_user:
            pool_user = {
                "consent": {"username": "insurance_pool", "agreed": True, "timestamp": _now()},
                "username": "insurance_pool",
                "ownership": {"aigx": 0, "ledger": []},
                "role": "system",
                "created_at": _now()
            }
            users.append(pool_user)
        
        # Find intent
        intent = None
        for user in users:
            for i in user.get("intents", []):
                if i.get("id") == intent_id:
                    intent = i
                    break
            if intent:
                break
        
        if not intent:
            return {"error": "intent not found"}
        
        # Collect insurance
        result = await collect_insurance(agent_user, intent, order_value)
        
        if result["ok"]:
            # Credit pool
            fee = result["fee"]
            pool_user["ownership"]["aigx"] = float(pool_user["ownership"].get("aigx", 0)) + fee
            
            pool_user["ownership"].setdefault("ledger", []).append({
                "ts": _now(),
                "amount": fee,
                "currency": "AIGx",
                "basis": "insurance_premium",
                "agent": username,
                "ref": intent_id
            })
            
            await _save_users(client, users)
        
        return result

@app.post("/insurance/payout")
async def insurance_payout(body: Dict = Body(...)):
    """
    Pay out from insurance pool on dispute resolution
    Called by dispute resolution system
    """
    dispute_id = body.get("dispute_id")
    intent_id = body.get("intent_id")
    buyer = body.get("buyer")
    agent = body.get("agent")
    payout_amount = float(body.get("payout_amount", 0))
    
    if not all([dispute_id, intent_id, buyer, payout_amount]):
        return {"error": "dispute_id, intent_id, buyer, payout_amount required"}
    
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        
        # Find pool user
        pool_user = next((u for u in users if _uname(u) == "insurance_pool"), None)
        if not pool_user:
            return {"error": "insurance_pool not found"}
        
        # Find buyer
        buyer_user = _find_user(users, buyer)
        if not buyer_user:
            return {"error": "buyer not found"}
        
        # Payout from pool
        dispute = {
            "dispute_id": dispute_id,
            "intent_id": intent_id,
            "buyer": buyer,
            "agent": agent
        }
        
        result = await payout_from_pool(pool_user, dispute, payout_amount)
        
        if result["ok"]:
            # Credit buyer
            buyer_user["ownership"]["aigx"] = float(buyer_user["ownership"].get("aigx", 0)) + result["payout"]
            
            buyer_user["ownership"].setdefault("ledger", []).append({
                "ts": _now(),
                "amount": result["payout"],
                "currency": "AIGx",
                "basis": "insurance_payout",
                "ref": dispute_id
            })
            
            await _save_users(client, users)
        
        return result

@app.get("/insurance/dispute_rate")
async def get_dispute_rate(username: str, days: int = 365):
    """Check agent's dispute rate"""
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        user = _find_user(users, username)
        
        if not user:
            return {"error": "user not found"}
        
        result = await calculate_dispute_rate(user, days)
        return {"ok": True, **result}

@app.post("/insurance/claim_refund")
async def claim_annual_refund(username: str):
    """
    Claim annual insurance refund (for low-dispute agents)
    """
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        
        user = _find_user(users, username)
        if not user:
            return {"error": "user not found"}
        
        pool_user = next((u for u in users if _uname(u) == "insurance_pool"), None)
        if not pool_user:
            return {"error": "insurance_pool not found"}
        
        # Check eligibility
        refund_calc = await calculate_annual_refund(user, pool_user)
        
        if not refund_calc.get("eligible"):
            return refund_calc
        
        # Issue refund
        result = await issue_annual_refund(user, pool_user, refund_calc["refund_amount"])
        
        if result["ok"]:
            await _save_users(client, users)
        
        return result

# ============ AGENT FACTORING LINE ============

from agent_factoring import (
    request_factoring_advance,
    settle_factoring,
    calculate_factoring_eligibility,
    calculate_factoring_tier,
    calculate_outstanding_factoring
)

@app.get("/factoring/eligibility")
async def factoring_eligibility(username: str):
    """Check agent's factoring eligibility and tier"""
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        user = _find_user(users, username)
        
        if not user:
            return {"error": "user not found"}
        
        result = await calculate_factoring_eligibility(user)
        return result

@app.get("/factoring/outstanding")
async def factoring_outstanding(username: str):
    """Get agent's outstanding factoring balance"""
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        user = _find_user(users, username)
        
        if not user:
            return {"error": "user not found"}
        
        outstanding = calculate_outstanding_factoring(user)
        tier_info = calculate_factoring_tier(user)
        
        return {
            "ok": True,
            "outstanding": outstanding,
            "tier": tier_info["tier"],
            "rate": tier_info["rate"]
        }

@app.post("/factoring/request")
async def request_factoring(body: Dict = Body(...)):
    """
    Request factoring advance (auto-called on intent award)
    """
    username = body.get("username")
    intent_id = body.get("intent_id")
    
    if not all([username, intent_id]):
        return {"error": "username and intent_id required"}
    
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        user = _find_user(users, username)
        
        if not user:
            return {"error": "user not found"}
        
        # Find intent
        intent = None
        for u in users:
            for i in u.get("intents", []):
                if i.get("id") == intent_id:
                    intent = i
                    break
            if intent:
                break
        
        if not intent:
            return {"error": "intent not found"}
        
        # Request advance
        result = await request_factoring_advance(user, intent)
        
        if result["ok"]:
            await _save_users(client, users)
        
        return result

@app.post("/factoring/settle")
async def settle_factoring_endpoint(body: Dict = Body(...)):
    """
    Settle factoring when buyer pays (auto-called on revenue recognition)
    """
    username = body.get("username")
    intent_id = body.get("intent_id")
    payment_received = float(body.get("payment_received", 0))
    
    if not all([username, intent_id, payment_received]):
        return {"error": "username, intent_id, payment_received required"}
    
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        user = _find_user(users, username)
        
        if not user:
            return {"error": "user not found"}
        
        # Find intent
        intent = None
        for u in users:
            for i in u.get("intents", []):
                if i.get("id") == intent_id:
                    intent = i
                    break
            if intent:
                break
        
        if not intent:
            return {"error": "intent not found"}
        
        # Settle factoring
        result = await settle_factoring(user, intent, payment_received)
        
        if result["ok"]:
            await _save_users(client, users)
        
        return result

# ============ REPUTATION-INDEXED PRICING (ARM) ============

from reputation_pricing import (
    calculate_pricing_tier,
    calculate_reputation_price,
    calculate_arm_price_range,
    calculate_dynamic_bid_price,
    update_outcome_score_weighted,
    calculate_pricing_impact
)

@app.get("/pricing/tier")
async def get_pricing_tier(username: str):
    """Get agent's current pricing tier based on OutcomeScore"""
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        user = _find_user(users, username)
        
        if not user:
            return {"error": "user not found"}
        
        outcome_score = int(user.get("outcomeScore", 0))
        tier_info = calculate_pricing_tier(outcome_score)
        
        return {"ok": True, **tier_info}

@app.get("/pricing/calculate")
async def calculate_price(
    username: str,
    base_price: float,
    service_type: str = "custom"
):
    """Calculate reputation-adjusted price for a service"""
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        user = _find_user(users, username)
        
        if not user:
            return {"error": "user not found"}
        
        outcome_score = int(user.get("outcomeScore", 0))
        
        # Get ARM pricing
        arm_pricing = calculate_arm_price_range(service_type, outcome_score)
        
        # Also calculate for custom base price
        custom_pricing = calculate_reputation_price(base_price, outcome_score)
        
        return {
            "ok": True,
            "arm_pricing": arm_pricing,
            "custom_base_pricing": custom_pricing
        }

@app.post("/pricing/recommend_bid")
async def recommend_bid_price(body: Dict = Body(...)):
    """
    Recommend optimal bid price for an intent
    Takes into account agent reputation + existing bids
    """
    username = body.get("username")
    intent_id = body.get("intent_id")
    
    if not all([username, intent_id]):
        return {"error": "username and intent_id required"}
    
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        user = _find_user(users, username)
        
        if not user:
            return {"error": "user not found"}
        
        # Find intent
        intent = None
        for u in users:
            for i in u.get("intents", []):
                if i.get("id") == intent_id:
                    intent = i
                    break
            if intent:
                break
        
        if not intent:
            return {"error": "intent not found"}
        
        outcome_score = int(user.get("outcomeScore", 0))
        existing_bids = intent.get("bids", [])
        
        # Calculate optimal bid
        recommendation = calculate_dynamic_bid_price(
            intent=intent,
            agent_outcome_score=outcome_score,
            existing_bids=existing_bids
        )
        
        return {"ok": True, **recommendation}

@app.post("/pricing/update_score")
async def update_pricing_score(body: Dict = Body(...)):
    """
    Update agent's OutcomeScore after job completion
    Auto-called by PoO verification
    """
    username = body.get("username")
    outcome_result = body.get("outcome_result")  # excellent | good | satisfactory | poor | failed
    
    if not all([username, outcome_result]):
        return {"error": "username and outcome_result required"}
    
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        user = _find_user(users, username)
        
        if not user:
            return {"error": "user not found"}
        
        current_score = int(user.get("outcomeScore", 0))
        new_score = update_outcome_score_weighted(current_score, outcome_result)
        
        # Calculate pricing impact
        impact = calculate_pricing_impact(current_score, new_score, base_price=200)
        
        # Update score
        user["outcomeScore"] = new_score
        
        # Log score change
        user.setdefault("ownership", {}).setdefault("ledger", []).append({
            "ts": _now(),
            "amount": 0,
            "currency": "SCORE",
            "basis": "outcome_score_update",
            "old_score": current_score,
            "new_score": new_score,
            "outcome_result": outcome_result
        })
        
        await _save_users(client, users)
        
        return {
            "ok": True,
            "old_score": current_score,
            "new_score": new_score,
            "score_change": new_score - current_score,
            "pricing_impact": impact
        }

@app.get("/pricing/market_rates")
async def get_market_rates(service_type: str = "custom"):
    """Get current market rates by reputation tier"""
    
    tiers_pricing = {}
    
    for tier_name, tier_info in PRICING_TIERS.items():
        # Use mid-point of score range
        mid_score = (tier_info["min_score"] + tier_info["max_score"]) // 2
        
        arm_pricing = calculate_arm_price_range(service_type, mid_score)
        
        tiers_pricing[tier_name] = {
            "score_range": f"{tier_info['min_score']}-{tier_info['max_score']}",
            "multiplier": tier_info["multiplier"],
            "price_range": arm_pricing["price_range"],
            "recommended_price": arm_pricing["recommended_price"]
        }
    
    return {
        "ok": True,
        "service_type": service_type,
        "tiers": tiers_pricing
    }

# ============ MULTI-CURRENCY SUPPORT ============

@app.get("/currency/rates")
async def get_exchange_rates():
    """Get current exchange rates"""
    live_rates = await fetch_live_rates()
    
    return {
        "ok": True,
        "rates": live_rates,
        "supported_currencies": SUPPORTED_CURRENCIES,
        "aigx_rates": {
            "USD": 1.0,
            "EUR": 0.92,
            "GBP": 0.79,
            "CREDITS": 100
        }
    }

@app.post("/currency/convert")
async def convert_currency_endpoint(body: Dict = Body(...)):
    """Convert amount from one currency to another"""
    amount = float(body.get("amount", 0))
    from_currency = body.get("from_currency", "USD")
    to_currency = body.get("to_currency", "USD")
    
    if amount <= 0:
        return {"error": "invalid_amount", "amount": amount}
    
    result = convert_currency(amount, from_currency, to_currency)
    return result

@app.get("/currency/balance")
async def get_currency_balance(username: str, currency: str = "USD"):
    """Get user's balance in specified currency"""
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        user = _find_user(users, username)
        
        if not user:
            return {"error": "user not found"}
        
        result = get_user_balance(user, currency)
        return result

@app.post("/currency/credit")
async def credit_user_currency(body: Dict = Body(...)):
    """Credit user's account in any supported currency"""
    username = body.get("username")
    amount = float(body.get("amount", 0))
    currency = body.get("currency", "USD")
    reason = body.get("reason", "credit")
    
    if not all([username, amount]):
        return {"error": "username and amount required"}
    
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        user = _find_user(users, username)
        
        if not user:
            return {"error": "user not found"}
        
        result = credit_currency(user, amount, currency, reason)
        
        if result["ok"]:
            await _save_users(client, users)
        
        return result

@app.post("/currency/debit")
async def debit_user_currency(body: Dict = Body(...)):
    """Debit user's account in any supported currency"""
    username = body.get("username")
    amount = float(body.get("amount", 0))
    currency = body.get("currency", "USD")
    reason = body.get("reason", "debit")
    
    if not all([username, amount]):
        return {"error": "username and amount required"}
    
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        user = _find_user(users, username)
        
        if not user:
            return {"error": "user not found"}
        
        result = debit_currency(user, amount, currency, reason)
        
        if result["ok"]:
            await _save_users(client, users)
        
        return result

@app.post("/currency/transfer")
async def transfer_between_users(body: Dict = Body(...)):
    """Transfer funds between users with currency conversion"""
    from_username = body.get("from_username")
    to_username = body.get("to_username")
    amount = float(body.get("amount", 0))
    from_currency = body.get("from_currency", "USD")
    to_currency = body.get("to_currency", "USD")
    reason = body.get("reason", "transfer")
    
    if not all([from_username, to_username, amount]):
        return {"error": "from_username, to_username, and amount required"}
    
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        
        from_user = _find_user(users, from_username)
        to_user = _find_user(users, to_username)
        
        if not from_user:
            return {"error": "from_user not found"}
        
        if not to_user:
            return {"error": "to_user not found"}
        
        result = transfer_with_conversion(
            from_user, to_user, amount,
            from_currency, to_currency, reason
        )
        
        if result["ok"]:
            await _save_users(client, users)
        
        return result

# ============ BATCH PAYMENT PROCESSING ============

@app.post("/batch/payment/create")
async def create_batch_payment_endpoint(body: Dict = Body(...)):
    """
    Create a batch payment for multiple agents
    
    Body:
    {
        "payments": [
            {"username": "agent1", "amount": 100, "currency": "USD", "reason": "job_123"},
            {"username": "agent2", "amount": 50, "currency": "EUR", "reason": "job_456"}
        ],
        "description": "Weekly agent payouts"
    }
    """
    payments = body.get("payments", [])
    description = body.get("description", "")
    batch_id = body.get("batch_id")
    
    if not payments:
        return {"error": "no_payments_provided"}
    
    batch = await create_batch_payment(payments, batch_id, description)
    
    return {"ok": True, "batch": batch}

@app.post("/batch/payment/execute")
async def execute_batch_payment_endpoint(body: Dict = Body(...)):
    """Execute a batch payment - credit all agents"""
    batch_id = body.get("batch_id")
    batch = body.get("batch")
    
    if not batch:
        return {"error": "batch_required"}
    
    async with httpx.AsyncClient(timeout=30) as client:
        users = await _load_users(client)
        
        # Execute batch
        result = await execute_batch_payment(batch, users, credit_currency)
        
        # Save users
        await _save_users(client, users)
        
        return result

@app.post("/batch/invoices/generate")
async def generate_bulk_invoices_endpoint(body: Dict = Body(...)):
    """
    Generate invoices for multiple completed intents
    
    Body:
    {
        "intent_ids": ["intent_123", "intent_456"]
    }
    """
    intent_ids = body.get("intent_ids", [])
    batch_id = body.get("batch_id")
    
    if not intent_ids:
        return {"error": "no_intent_ids_provided"}
    
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        
        # Find all intents
        intents = []
        for user in users:
            for intent in user.get("intents", []):
                if intent.get("id") in intent_ids:
                    intents.append(intent)
        
        # Generate invoices
        result = await generate_bulk_invoices(intents, batch_id)
        
        return result

@app.post("/batch/revenue/recognize")
async def batch_revenue_recognition_endpoint(body: Dict = Body(...)):
    """
    Process revenue recognition for multiple invoices at once
    
    Body:
    {
        "invoice_ids": ["inv_123", "inv_456"],
        "platform_fee_rate": 0.05
    }
    """
    invoice_ids = body.get("invoice_ids", [])
    platform_fee_rate = float(body.get("platform_fee_rate", 0.05))
    
    if not invoice_ids:
        return {"error": "no_invoice_ids_provided"}
    
    async with httpx.AsyncClient(timeout=30) as client:
        users = await _load_users(client)
        
        # Find all invoices
        invoices = []
        for user in users:
            for invoice in user.get("invoices", []):
                if invoice.get("id") in invoice_ids:
                    invoices.append(invoice)
        
        # Process batch revenue recognition
        result = await batch_revenue_recognition(invoices, users, platform_fee_rate)
        
        # Save users
        await _save_users(client, users)
        
        return result

@app.post("/batch/payment/schedule")
async def schedule_recurring_payment_endpoint(body: Dict = Body(...)):
    """
    Schedule recurring payment (monthly stipends, etc.)
    
    Body:
    {
        "payment_template": {
            "username": "agent1",
            "amount": 1000,
            "currency": "USD",
            "reason": "monthly_stipend"
        },
        "schedule": "monthly",
        "start_date": "2025-12-01T00:00:00Z"
    }
    """
    payment_template = body.get("payment_template")
    schedule = body.get("schedule", "monthly")
    start_date = body.get("start_date")
    
    if not payment_template:
        return {"error": "payment_template_required"}
    
    result = await schedule_recurring_payment(payment_template, schedule, start_date)
    
    return result

@app.get("/batch/payment/report")
async def get_batch_payment_report(batch_id: str, format: str = "summary"):
    """
    Get payment report for a batch
    
    format: summary | detailed | csv
    """
    # This is a simplified version - in production, you'd load batch from database
    return {
        "ok": True,
        "message": "In production, load batch from storage",
        "batch_id": batch_id,
        "format": format
    }

@app.post("/batch/payment/retry")
async def retry_failed_payments_endpoint(body: Dict = Body(...)):
    """Retry all failed payments from a batch"""
    batch = body.get("batch")
    
    if not batch:
        return {"error": "batch_required"}
    
    async with httpx.AsyncClient(timeout=30) as client:
        users = await _load_users(client)
        
        result = await retry_failed_payments(batch, users, credit_currency)
        
        await _save_users(client, users)
        
        return result

# ============ FINANCIAL ANALYTICS DASHBOARD ============

@app.get("/analytics/revenue")
async def get_revenue_analytics(period_days: int = 30):
    """Get platform revenue metrics"""
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        
        metrics = calculate_revenue_metrics(users, period_days)
        
        return {"ok": True, **metrics}

@app.get("/analytics/revenue/by_currency")
async def get_revenue_by_currency(period_days: int = 30):
    """Get revenue broken down by currency"""
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        
        result = calculate_revenue_by_currency(users, period_days)
        
        return {"ok": True, **result}

@app.get("/analytics/revenue/forecast")
async def get_revenue_forecast(historical_days: int = 30, forecast_days: int = 30):
    """Forecast future revenue based on historical data"""
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        
        historical = calculate_revenue_metrics(users, historical_days)
        forecast = forecast_revenue(historical, forecast_days)
        
        return {"ok": True, "historical": historical, "forecast": forecast}

@app.get("/analytics/agent")
async def get_agent_analytics(username: str, period_days: int = 30):
    """Get individual agent performance metrics"""
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        user = _find_user(users, username)
        
        if not user:
            return {"error": "user not found"}
        
        metrics = calculate_agent_metrics(user, period_days)
        
        return {"ok": True, **metrics}

@app.get("/analytics/leaderboard")
async def get_agent_leaderboard(metric: str = "total_earned", limit: int = 10):
    """
    Get agent leaderboard
    
    metric options: total_earned, completed_jobs, outcome_score, on_time_rate
    """
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        
        result = rank_agents_by_performance(users, metric, limit)
        
        return {"ok": True, **result}

@app.get("/analytics/health")
async def get_platform_health():
    """Get overall platform financial health score"""
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        
        health = calculate_platform_health(users)
        
        return {"ok": True, **health}

@app.get("/analytics/cohorts")
async def get_cohort_analysis(cohort_by: str = "signup_month"):
    """
    Analyze user cohorts
    
    cohort_by options: signup_month, outcome_score_tier, revenue_tier
    """
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        
        result = generate_cohort_analysis(users, cohort_by)
        
        return {"ok": True, **result}

@app.get("/analytics/alerts")
async def get_financial_alerts():
    """Get financial health alerts and recommendations"""
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        
        health = calculate_platform_health(users)
        revenue = calculate_revenue_metrics(users, period_days=30)
        
        alerts = detect_financial_alerts(health, revenue)
        
        return {
            "ok": True,
            "alert_count": len(alerts),
            "alerts": alerts,
            "platform_status": health["status"]
        }

@app.get("/analytics/dashboard")
async def get_analytics_dashboard():
    """Get complete analytics dashboard summary"""
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        
        # Calculate all metrics
        revenue_30d = calculate_revenue_metrics(users, period_days=30)
        revenue_7d = calculate_revenue_metrics(users, period_days=7)
        health = calculate_platform_health(users)
        top_agents = rank_agents_by_performance(users, "total_earned", 5)
        alerts = detect_financial_alerts(health, revenue_30d)
        
        return {
            "ok": True,
            "revenue_30d": revenue_30d,
            "revenue_7d": revenue_7d,
            "platform_health": health,
            "top_agents": top_agents["top_agents"],
            "alerts": alerts,
            "dashboard_generated_at": _now()
        }

# ============ AUTOMATED TAX REPORTING ============

@app.get("/tax/earnings")
async def get_annual_earnings(username: str, year: int = None):
    """Get agent's annual earnings for tax purposes"""
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        user = _find_user(users, username)
        
        if not user:
            return {"error": "user not found"}
        
        earnings = calculate_annual_earnings(user, year)
        
        return {"ok": True, **earnings}

@app.get("/tax/1099")
async def get_1099_nec(username: str, year: int = None):
    """Generate 1099-NEC form for agent"""
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        user = _find_user(users, username)
        
        if not user:
            return {"error": "user not found"}
        
        result = generate_1099_nec(user, year)
        
        return result

@app.get("/tax/estimated")
async def get_estimated_taxes(username: str, year: int = None, region: str = "US"):
    """Calculate estimated tax liability"""
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        user = _find_user(users, username)
        
        if not user:
            return {"error": "user not found"}
        
        earnings = calculate_annual_earnings(user, year)
        taxes = calculate_estimated_taxes(earnings, region)
        
        return taxes

@app.get("/tax/quarterly")
async def get_quarterly_report(username: str, year: int, quarter: int):
    """
    Generate quarterly tax report
    
    quarter: 1, 2, 3, or 4
    """
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        user = _find_user(users, username)
        
        if not user:
            return {"error": "user not found"}
        
        report = generate_quarterly_report(user, year, quarter)
        
        return {"ok": True, **report}

@app.get("/tax/vat")
async def get_vat_liability(username: str, year: int, quarter: int = None):
    """Calculate VAT liability for EU/UK agents"""
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        user = _find_user(users, username)
        
        if not user:
            return {"error": "user not found"}
        
        vat = calculate_vat_liability(user, year, quarter)
        
        return {"ok": True, **vat}

@app.get("/tax/summary")
async def get_annual_tax_summary_endpoint(username: str, year: int = None):
    """Get comprehensive annual tax summary"""
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        user = _find_user(users, username)
        
        if not user:
            return {"error": "user not found"}
        
        summary = generate_annual_tax_summary(user, year)
        
        return {"ok": True, **summary}

@app.get("/tax/batch_1099")
async def batch_generate_1099s_endpoint(year: int = None):
    """
    Generate 1099s for all eligible agents
    Admin only
    """
    async with httpx.AsyncClient(timeout=30) as client:
        users = await _load_users(client)
        
        result = batch_generate_1099s(users, year)
        
        return result

@app.get("/tax/export_csv")
async def export_tax_csv_endpoint(username: str, year: int = None):
    """Export tax data as CSV for accountant"""
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        user = _find_user(users, username)
        
        if not user:
            return {"error": "user not found"}
        
        csv_data = export_tax_csv(user, year)
        
        return csv_data

        # ============ R³ AUTOPILOT (KEEP-ME-GROWING) ============

@app.get("/r3/autopilot/tiers")
async def get_autopilot_tiers():
    """Get available autopilot tiers"""
    return {
        "ok": True,
        "tiers": AUTOPILOT_TIERS,
        "channels": CHANNELS
    }

@app.get("/r3/autopilot/recommend")
async def recommend_autopilot_tier(username: str):
    """Get personalized autopilot recommendations"""
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        user = _find_user(users, username)
        
        if not user:
            return {"error": "user not found"}
        
        recommendations = get_autopilot_recommendations(user)
        
        return recommendations

@app.post("/r3/autopilot/create")
async def create_autopilot_strategy_endpoint(body: Dict = Body(...)):
    """
    Create an autopilot budget strategy
    
    Body:
    {
        "username": "agent1",
        "tier": "balanced",
        "monthly_budget": 500
    }
    """
    username = body.get("username")
    tier = body.get("tier", "balanced")
    monthly_budget = float(body.get("monthly_budget", 500))
    
    if not username:
        return {"error": "username required"}
    
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        user = _find_user(users, username)
        
        if not user:
            return {"error": "user not found"}
        
        # Create strategy
        result = create_autopilot_strategy(user, tier, monthly_budget)
        
        if result["ok"]:
            # Store strategy in user record
            user.setdefault("r3_autopilot", {})
            user["r3_autopilot"]["strategy"] = result["strategy"]
            
            await _save_users(client, users)
        
        return result

@app.get("/r3/autopilot/strategy")
async def get_autopilot_strategy(username: str):
    """Get user's current autopilot strategy"""
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        user = _find_user(users, username)
        
        if not user:
            return {"error": "user not found"}
        
        strategy = user.get("r3_autopilot", {}).get("strategy")
        
        if not strategy:
            return {"error": "no_strategy_found", "message": "User has not created an autopilot strategy"}
        
        return {"ok": True, "strategy": strategy}

@app.post("/r3/autopilot/allocate")
async def calculate_allocation_endpoint(body: Dict = Body(...)):
    """
    Calculate optimal budget allocation
    
    Body:
    {
        "budget": 500,
        "tier": "balanced",
        "historical_performance": {...}
    }
    """
    budget = float(body.get("budget", 500))
    tier = body.get("tier", "balanced")
    historical_performance = body.get("historical_performance")
    
    if tier not in AUTOPILOT_TIERS:
        return {"error": "invalid_tier", "valid_tiers": list(AUTOPILOT_TIERS.keys())}
    
    tier_config = AUTOPILOT_TIERS[tier]
    
    allocation = calculate_budget_allocation(budget, tier_config, historical_performance)
    
    return {"ok": True, "allocation": allocation}

@app.post("/r3/autopilot/predict")
async def predict_channel_roi(body: Dict = Body(...)):
    """
    Predict ROI for a specific channel
    
    Body:
    {
        "channel": "google_ads",
        "spend_amount": 200,
        "historical_data": {...}
    }
    """
    channel_id = body.get("channel")
    spend_amount = float(body.get("spend_amount", 0))
    historical_data = body.get("historical_data")
    
    if not channel_id:
        return {"error": "channel required"}
    
    prediction = predict_roi(channel_id, spend_amount, historical_data)
    
    return prediction

@app.post("/r3/autopilot/execute")
async def execute_autopilot_spend_endpoint(body: Dict = Body(...)):
    """
    Execute the autopilot spend for current period
    
    Body:
    {
        "username": "agent1"
    }
    """
    username = body.get("username")
    
    if not username:
        return {"error": "username required"}
    
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        user = _find_user(users, username)
        
        if not user:
            return {"error": "user not found"}
        
        # Get strategy
        strategy = user.get("r3_autopilot", {}).get("strategy")
        
        if not strategy:
            return {"error": "no_strategy_found"}
        
        # Execute spend
        result = execute_autopilot_spend(strategy, user)
        
        if result["ok"]:
            # Update user record
            user["r3_autopilot"]["strategy"] = strategy
            user["r3_autopilot"]["last_execution"] = _now()
            
            await _save_users(client, users)
        
        return result

@app.post("/r3/autopilot/rebalance")
async def rebalance_autopilot_endpoint(body: Dict = Body(...)):
    """
    Rebalance autopilot strategy based on performance
    
    Body:
    {
        "username": "agent1",
        "actual_performance": {
            "google_ads": {"roi": 2.1, "revenue": 420},
            "facebook_ads": {"roi": 1.4, "revenue": 168}
        }
    }
    """
    username = body.get("username")
    actual_performance = body.get("actual_performance")
    
    if not username:
        return {"error": "username required"}
    
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        user = _find_user(users, username)
        
        if not user:
            return {"error": "user not found"}
        
        # Get strategy
        strategy = user.get("r3_autopilot", {}).get("strategy")
        
        if not strategy:
            return {"error": "no_strategy_found"}
        
        # Rebalance
        result = rebalance_autopilot(strategy, actual_performance)
        
        if result["ok"]:
            # Update user record
            user["r3_autopilot"]["strategy"] = strategy
            user["r3_autopilot"]["last_rebalance"] = _now()
            
            await _save_users(client, users)
        
        return result

@app.post("/r3/autopilot/pause")
async def pause_autopilot(username: str):
    """Pause autopilot strategy"""
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        user = _find_user(users, username)
        
        if not user:
            return {"error": "user not found"}
        
        strategy = user.get("r3_autopilot", {}).get("strategy")
        
        if not strategy:
            return {"error": "no_strategy_found"}
        
        strategy["status"] = "paused"
        strategy["paused_at"] = _now()
        
        await _save_users(client, users)
        
        return {"ok": True, "message": "Autopilot paused", "strategy": strategy}

@app.post("/r3/autopilot/resume")
async def resume_autopilot(username: str):
    """Resume paused autopilot strategy"""
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        user = _find_user(users, username)
        
        if not user:
            return {"error": "user not found"}
        
        strategy = user.get("r3_autopilot", {}).get("strategy")
        
        if not strategy:
            return {"error": "no_strategy_found"}
        
        strategy["status"] = "active"
        strategy["resumed_at"] = _now()
        
        await _save_users(client, users)
        
        return {"ok": True, "message": "Autopilot resumed", "strategy": strategy}

@app.get("/r3/autopilot/performance")
async def get_autopilot_performance(username: str):
    """Get autopilot performance summary"""
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        user = _find_user(users, username)
        
        if not user:
            return {"error": "user not found"}
        
        strategy = user.get("r3_autopilot", {}).get("strategy")
        
        if not strategy:
            return {"error": "no_strategy_found"}
        
        performance = strategy.get("performance", {})
        
        # Calculate actual ROI from ledger
        ledger = user.get("ownership", {}).get("ledger", [])
        
        total_autopilot_spend = 0.0
        total_autopilot_revenue = 0.0
        
        for entry in ledger:
            basis = entry.get("basis", "")
            
            if basis == "r3_autopilot_spend":
                total_autopilot_spend += abs(float(entry.get("amount", 0)))
            
            # Revenue from autopilot campaigns (would need tracking)
            if basis == "revenue" and entry.get("source") == "r3_autopilot":
                total_autopilot_revenue += float(entry.get("amount", 0))
        
        actual_roi = (total_autopilot_revenue / total_autopilot_spend) if total_autopilot_spend > 0 else 0
        
        return {
            "ok": True,
            "strategy_id": strategy["id"],
            "tier": strategy["tier"],
            "performance": {
                **performance,
                "total_spend": round(total_autopilot_spend, 2),
                "total_revenue": round(total_autopilot_revenue, 2),
                "actual_roi": round(actual_roi, 2)
            },
            "status": strategy["status"]
        }

# ============ AUTONOMOUS LOGIC UPGRADES ============

@app.get("/upgrades/types")
async def get_upgrade_types():
    """Get available logic upgrade types"""
    return {
        "ok": True,
        "upgrade_types": UPGRADE_TYPES
    }

@app.post("/upgrades/test/create")
async def create_ab_test_endpoint(body: Dict = Body(...)):
    """
    Create an A/B test for a logic upgrade
    
    Body:
    {
        "upgrade_type": "pricing_strategy",
        "control_logic": {...},
        "test_duration_days": 14,
        "sample_size": 100
    }
    """
    upgrade_type = body.get("upgrade_type")
    control_logic = body.get("control_logic", {})
    test_duration_days = int(body.get("test_duration_days", 14))
    sample_size = int(body.get("sample_size", 100))
    
    if not upgrade_type:
        return {"error": "upgrade_type required"}
    
    if upgrade_type not in UPGRADE_TYPES:
        return {
            "error": "invalid_upgrade_type",
            "valid_types": list(UPGRADE_TYPES.keys())
        }
    
    # Create test
    ab_test = create_ab_test(upgrade_type, control_logic, test_duration_days, sample_size)
    
    # Store test (in production, would store in database)
    # For now, store in a special system user
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        
        # Find or create system user for tests
        system_user = next((u for u in users if u.get("username") == "system_tests"), None)
        
        if not system_user:
            system_user = {
                "username": "system_tests",
                "role": "system",
                "ab_tests": [],
                "created_at": _now()
            }
            users.append(system_user)
        
        system_user.setdefault("ab_tests", []).append(ab_test)
        
        await _save_users(client, users)
    
    return {"ok": True, "ab_test": ab_test}

@app.get("/upgrades/test/list")
async def list_ab_tests(status: str = None):
    """
    List all A/B tests
    
    status: active | completed | deployed | all
    """
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        
        system_user = next((u for u in users if u.get("username") == "system_tests"), None)
        
        if not system_user:
            return {"ok": True, "tests": [], "count": 0}
        
        tests = system_user.get("ab_tests", [])
        
        if status and status != "all":
            tests = [t for t in tests if t.get("status") == status]
        
        return {
            "ok": True,
            "tests": tests,
            "count": len(tests),
            "active_count": len([t for t in tests if t.get("status") == "active"])
        }

@app.get("/upgrades/test/{test_id}")
async def get_ab_test(test_id: str):
    """Get specific A/B test details"""
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        
        system_user = next((u for u in users if u.get("username") == "system_tests"), None)
        
        if not system_user:
            return {"error": "no_tests_found"}
        
        tests = system_user.get("ab_tests", [])
        test = next((t for t in tests if t.get("id") == test_id), None)
        
        if not test:
            return {"error": "test_not_found", "test_id": test_id}
        
        return {"ok": True, "test": test}

@app.post("/upgrades/test/assign")
async def assign_agent_to_test(body: Dict = Body(...)):
    """
    Assign agent to A/B test group
    
    Body:
    {
        "test_id": "test_abc123",
        "agent_id": "agent1"
    }
    """
    test_id = body.get("test_id")
    agent_id = body.get("agent_id")
    
    if not all([test_id, agent_id]):
        return {"error": "test_id and agent_id required"}
    
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        
        system_user = next((u for u in users if u.get("username") == "system_tests"), None)
        
        if not system_user:
            return {"error": "test_not_found"}
        
        tests = system_user.get("ab_tests", [])
        test = next((t for t in tests if t.get("id") == test_id), None)
        
        if not test:
            return {"error": "test_not_found", "test_id": test_id}
        
        # Assign to group
        group = assign_to_test_group(test, agent_id)
        
        # Get logic for assigned group
        logic = test[group]["logic"]
        
        return {
            "ok": True,
            "test_id": test_id,
            "agent_id": agent_id,
            "assigned_group": group,
            "logic": logic
        }

@app.post("/upgrades/test/record")
async def record_test_outcome_endpoint(body: Dict = Body(...)):
    """
    Record outcome for an A/B test sample
    
    Body:
    {
        "test_id": "test_abc123",
        "group": "variant",
        "metrics": {
            "win_rate": 0.35,
            "avg_margin": 0.15,
            "conversion_rate": 0.28
        }
    }
    """
    test_id = body.get("test_id")
    group = body.get("group")
    metrics = body.get("metrics", {})
    
    if not all([test_id, group]):
        return {"error": "test_id and group required"}
    
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        
        system_user = next((u for u in users if u.get("username") == "system_tests"), None)
        
        if not system_user:
            return {"error": "test_not_found"}
        
        tests = system_user.get("ab_tests", [])
        test = next((t for t in tests if t.get("id") == test_id), None)
        
        if not test:
            return {"error": "test_not_found", "test_id": test_id}
        
        # Record outcome
        result = record_test_outcome(test, group, metrics)
        
        if result["ok"]:
            await _save_users(client, users)
        
        return result

@app.post("/upgrades/test/analyze")
async def analyze_ab_test_endpoint(body: Dict = Body(...)):
    """
    Analyze A/B test results
    
    Body:
    {
        "test_id": "test_abc123",
        "min_sample_size": 30
    }
    """
    test_id = body.get("test_id")
    min_sample_size = int(body.get("min_sample_size", 30))
    
    if not test_id:
        return {"error": "test_id required"}
    
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        
        system_user = next((u for u in users if u.get("username") == "system_tests"), None)
        
        if not system_user:
            return {"error": "test_not_found"}
        
        tests = system_user.get("ab_tests", [])
        test = next((t for t in tests if t.get("id") == test_id), None)
        
        if not test:
            return {"error": "test_not_found", "test_id": test_id}
        
        # Analyze
        analysis = analyze_ab_test(test, min_sample_size)
        
        if analysis.get("ok"):
            # Update test status
            if analysis.get("is_significant"):
                test["status"] = "completed"
            
            await _save_users(client, users)
        
        return analysis

@app.post("/upgrades/deploy")
async def deploy_upgrade_endpoint(body: Dict = Body(...)):
    """
    Deploy winning logic upgrade to all agents
    
    Body:
    {
        "test_id": "test_abc123"
    }
    """
    test_id = body.get("test_id")
    
    if not test_id:
        return {"error": "test_id required"}
    
    async with httpx.AsyncClient(timeout=30) as client:
        users = await _load_users(client)
        
        system_user = next((u for u in users if u.get("username") == "system_tests"), None)
        
        if not system_user:
            return {"error": "test_not_found"}
        
        tests = system_user.get("ab_tests", [])
        test = next((t for t in tests if t.get("id") == test_id), None)
        
        if not test:
            return {"error": "test_not_found", "test_id": test_id}
        
        # Deploy
        result = deploy_logic_upgrade(test, users)
        
        if result["ok"]:
            await _save_users(client, users)
        
        return result

@app.post("/upgrades/rollback")
async def rollback_upgrade_endpoint(body: Dict = Body(...)):
    """
    Rollback a logic upgrade
    
    Body:
    {
        "upgrade_type": "pricing_strategy",
        "rollback_to_version": "var_abc123" (optional)
    }
    """
    upgrade_type = body.get("upgrade_type")
    rollback_to_version = body.get("rollback_to_version")
    
    if not upgrade_type:
        return {"error": "upgrade_type required"}
    
    async with httpx.AsyncClient(timeout=30) as client:
        users = await _load_users(client)
        
        result = rollback_logic_upgrade(upgrade_type, users, rollback_to_version)
        
        if result["ok"]:
            await _save_users(client, users)
        
        return result

@app.get("/upgrades/suggest")
async def suggest_next_upgrade_endpoint():
    """Suggest next logic upgrade to test based on platform needs"""
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        
        # Get existing tests
        system_user = next((u for u in users if u.get("username") == "system_tests"), None)
        existing_tests = system_user.get("ab_tests", []) if system_user else []
        
        suggestion = suggest_next_upgrade(users, existing_tests)
        
        return suggestion

@app.get("/upgrades/agent/history")
async def get_agent_upgrade_history(username: str):
    """Get agent's logic upgrade history"""
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        user = _find_user(users, username)
        
        if not user:
            return {"error": "user not found"}
        
        logic_upgrades = user.get("logic_upgrades", [])
        current_logic = user.get("logic", {})
        
        return {
            "ok": True,
            "username": username,
            "current_logic": current_logic,
            "upgrade_history": logic_upgrades,
            "total_upgrades": len(logic_upgrades)
        }

@app.get("/upgrades/active")
async def get_active_tests_endpoint():
    """Get all active A/B tests"""
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        
        system_user = next((u for u in users if u.get("username") == "system_tests"), None)
        
        if not system_user:
            return {"ok": True, "active_tests": [], "count": 0}
        
        all_tests = system_user.get("ab_tests", [])
        active = get_active_tests(all_tests)
        
        return {
            "ok": True,
            "active_tests": active,
            "count": len(active)
        }

@app.get("/upgrades/dashboard")
async def get_upgrades_dashboard():
    """Get autonomous upgrades dashboard summary"""
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        
        system_user = next((u for u in users if u.get("username") == "system_tests"), None)
        
        if not system_user:
            return {
                "ok": True,
                "total_tests": 0,
                "active_tests": 0,
                "completed_tests": 0,
                "deployed_upgrades": 0
            }
        
        all_tests = system_user.get("ab_tests", [])
        
        active = len([t for t in all_tests if t.get("status") == "active"])
        completed = len([t for t in all_tests if t.get("status") == "completed"])
        deployed = len([t for t in all_tests if t.get("status") == "deployed"])
        
        # Get suggestion
        suggestion = suggest_next_upgrade(users, all_tests)
        
        return {
            "ok": True,
            "total_tests": len(all_tests),
            "active_tests": active,
            "completed_tests": completed,
            "deployed_upgrades": deployed,
            "next_suggestion": suggestion,
            "upgrade_types": UPGRADE_TYPES,
            "dashboard_generated_at": _now()
        }
        
@app.post("/poo/issue")
async def poo_issue(username: str, title: str, metrics: dict = None, evidence_urls: List[str] = None):
    users, client = await _get_users_client()
    u = _find_user(users, username)
    if not u: return {"error":"user not found"}
    entry = {"id": _uid(), "ts": _now(), "title": title, "metrics": metrics or {}, "evidence_urls": evidence_urls or []}
    u.setdefault("outcomes", []).append(entry)
    score = int(u.get("outcomeScore", 0)) + 3
    u["outcomeScore"] = max(0, min(100, score))
    await _save_users(client, users)
    
    # ADD THIS:
    try:
        await publish({"type":"poo","user":username,"title":title,"score":score})
    except Exception as e:
        print(f"Publish error: {e}")
    
    return {"ok": True, "outcome": entry, "score": u["outcomeScore"]}
from outcome_oracle import (
    issue_poo as issue_poo_oracle,
    verify_poo as verify_poo_oracle,
    get_poo,
    list_poos,
    get_agent_poo_stats
)

@app.post("/poo/submit")
async def poo_submit(
    username: str,
    intent_id: str,
    title: str,
    evidence_urls: List[str] = None,
    metrics: Dict[str, Any] = None,
    description: str = ""
):
    result = await issue_poo_oracle(
        username=username,
        intent_id=intent_id,
        title=title,
        evidence_urls=evidence_urls,
        metrics=metrics,
        description=description
    )
    return result


    
@app.post("/poo/verify")
async def poo_verify(
    poo_id: str,
    buyer_username: str,
    approved: bool,
    feedback: str = "",
    outcome_rating: str = "good" 
):
    """Verify PoO + auto-capture escrow + return bond + award bonus"""
    result = await verify_poo_oracle(
        poo_id=poo_id,
        buyer_username=buyer_username,
        approved=approved,
        feedback=feedback
    )
    
    if result.get("ok") and approved:
        async with httpx.AsyncClient(timeout=20) as client:
            users = await _load_users(client)
            poo = result.get("poo", {})
            intent_id = poo.get("intent_id")
            agent = poo.get("agent")
            
            # Find intent & agent user
            intent = None
            agent_user = None
            
            for user in users:
                # Find agent user
                if _uname(user) == agent:
                    agent_user = user
                
                # Find intent
                for i in user.get("intents", []):
                    if i.get("id") == intent_id:
                        intent = i
                        # Mark as delivered
                        intent["status"] = "DELIVERED"
                        intent["delivered_at"] = _now()
            
            # AUTO-CAPTURE ESCROW
            if intent:
                capture_result = await auto_capture_on_delivered(intent)
                result["escrow_capture"] = capture_result
            
            # AUTO-RETURN BOND
            if agent_user and intent:
                bond_result = await return_bond(agent_user, intent)
                result["bond_return"] = bond_result
                
                # AUTO-AWARD SLA BONUS (if delivered early/on-time)
                bonus_result = await award_sla_bonus(agent_user, intent)
                result["sla_bonus"] = bonus_result
            
            #  OCL EXPANSION (existing logic)
            if agent_user:
                expansion = await expand_ocl_on_poo(agent_user, poo_id)
                result["ocl_expansion"] = expansion
            
            # ✅ UPDATE OUTCOMESCORE
            if agent_user:
                # Determine outcome rating from delivery speed + feedback
                outcome_result = outcome_rating  # Default from param
                
                # Auto-determine if not explicitly provided
                if outcome_rating == "good":
                    # Check SLA performance
                    if intent and intent.get("accepted_at") and intent.get("delivered_at"):
                        from performance_bonds import _hours_between
                        delivery_hours = _hours_between(intent["accepted_at"], intent["delivered_at"])
                        sla_hours = intent.get("delivery_hours", 48)
                        
                        if delivery_hours < (sla_hours * 0.5):
                            outcome_result = "excellent"
                        elif delivery_hours > sla_hours:
                            outcome_result = "satisfactory"
                
                # Update score
                current_score = int(agent_user.get("outcomeScore", 0))
                new_score = update_outcome_score_weighted(current_score, outcome_result)
                
                agent_user["outcomeScore"] = new_score
                
                # Calculate pricing impact
                pricing_impact = calculate_pricing_impact(current_score, new_score, base_price=200)
                
                result["score_update"] = {
                    "old_score": current_score,
                    "new_score": new_score,
                    "outcome_result": outcome_result,
                    "pricing_impact": pricing_impact
                }
                
                print(f" Updated {agent} OutcomeScore: {current_score} → {new_score}")
            
            await _save_users(client, users)
    
    return result
    

@app.get("/poo/{poo_id}")
async def poo_get(poo_id: str):
    return get_poo(poo_id)

@app.get("/poo/list")
async def poo_list(
    agent: str = None,
    intent_id: str = None,
    status: str = None
):
    return list_poos(agent=agent, intent_id=intent_id, status=status)

@app.get("/poo/stats/{username}")
async def poo_stats(username: str):
    return get_agent_poo_stats(username)    
@app.get("/score/outcome")
async def get_outcome_score(username: str):
    users, client = await _get_users_client()
    u = _find_user(users, username)
    if not u: return {"error":"user not found"}
    return {"ok": True, "score": int(u.get("outcomeScore", 0))}

from disputes import (
    open_dispute as open_dispute_system,
    submit_evidence,
    auto_resolve_dispute,
    resolve_dispute as resolve_dispute_system,
    get_dispute,
    list_disputes,
    get_party_dispute_stats
)

@app.post("/disputes/open")
async def dispute_open(
    intent_id: str,
    opener: str,
    reason: str,
    evidence_urls: List[str] = None,
    description: str = ""
):
    result = await open_dispute_system(
        intent_id=intent_id,
        opener=opener,
        reason=reason,
        evidence_urls=evidence_urls,
        description=description
    )
    return result

@app.post("/disputes/evidence")
async def dispute_evidence(
    dispute_id: str,
    party: str,
    evidence_urls: List[str],
    statement: str = ""
):
    result = await submit_evidence(
        dispute_id=dispute_id,
        party=party,
        evidence_urls=evidence_urls,
        statement=statement
    )
    return result

@app.post("/disputes/auto_resolve")
async def dispute_auto_resolve(dispute_id: str):
    result = await auto_resolve_dispute(dispute_id)
    return result

@app.post("/disputes/resolve")
async def dispute_resolve(
    dispute_id: str,
    resolver: str,
    resolution: str,
    refund_pct: float
):
    result = await resolve_dispute_system(
        dispute_id=dispute_id,
        resolver=resolver,
        resolution=resolution,
        refund_pct=refund_pct
    )
    return result

@app.get("/disputes/{dispute_id}")
async def dispute_get(dispute_id: str):
    return get_dispute(dispute_id)

@app.get("/disputes/list")
async def dispute_list(
    status: str = None,
    tier: str = None,
    party: str = None
):
    return list_disputes(status=status, tier=tier, party=party)

@app.get("/disputes/stats/{party}")
async def dispute_stats(party: str):
    return get_party_dispute_stats(party)
#@app.post("/intent/create")
async def intent_create(buyer: str, brief: str, budget: float):
    users, client = await _get_users_client()
    u = _find_user(users, buyer)
    if not u: return {"error":"buyer not found"}
    intent = {"id": _uid(), "ts": _now(), "brief": brief, "budget": float(budget), "status":"open", "bids":[]}
    u.setdefault("intents", []).append(intent)
    await _save_users(client, users)
    try:
        await publish({"type":"intent","buyer":buyer,"id":intent["id"],"brief":brief})
    except Exception:
        pass
    return {"ok": True, "intent": intent}

from revenue_flows import register_clone_lineage

from compliance_oracle import (
    submit_kyc,
    approve_kyc,
    reject_kyc,
    check_transaction_allowed,
    get_kyc_status,
    list_pending_kyc,
    list_sars,
    get_compliance_stats
)

@app.post("/compliance/kyc/submit")
async def kyc_submit(
    username: str,
    level: str,
    full_name: str,
    date_of_birth: str,
    country: str,
    documents: List[Dict[str, Any]] = None
):
    """Submit KYC"""
    result = await submit_kyc(username, level, full_name, date_of_birth, country, documents)
    return result

@app.post("/compliance/kyc/approve")
async def kyc_approve(username: str, reviewer: str, notes: str = ""):
    """Approve KYC"""
    result = approve_kyc(username, reviewer, notes)
    return result

@app.post("/compliance/kyc/reject")
async def kyc_reject(username: str, reviewer: str, reason: str):
    """Reject KYC"""
    result = reject_kyc(username, reviewer, reason)
    return result

@app.post("/compliance/check")
async def compliance_check(
    username: str,
    transaction_type: str,
    amount: float,
    destination: str = None
):
    """Check transaction compliance"""
    result = await check_transaction_allowed(username, transaction_type, amount, destination)
    return result

@app.get("/compliance/kyc/{username}")
async def kyc_status(username: str):
    return get_kyc_status(username)

@app.get("/compliance/kyc/pending")
async def kyc_pending():
    return list_pending_kyc()

@app.get("/compliance/sars")
async def sars_list(status: str = None):
    return list_sars(status)

@app.get("/compliance/stats")
async def compliance_stats():
    return get_compliance_stats()

from aigentsy_conductor import (
    register_device,
    scan_opportunities,
    create_execution_plan,
    approve_execution_plan,
    execute_plan,
    set_user_policy,
    get_device_dashboard
)

@app.post("/conductor/register")
async def conductor_register(
    username: str,
    device_id: str,
    connected_apps: List[Dict[str, Any]],
    capabilities: List[str]
):
    """Register device"""
    result = await register_device(username, device_id, connected_apps, capabilities)
    return result

@app.post("/conductor/scan")
async def conductor_scan(username: str, device_id: str):
    """Scan for opportunities"""
    result = await scan_opportunities(username, device_id)
    return result

@app.post("/conductor/plan")
async def conductor_plan(
    username: str,
    device_id: str,
    opportunities: List[Dict[str, Any]],
    max_actions: int = 10
):
    """Create execution plan"""
    result = await create_execution_plan(username, device_id, opportunities, max_actions)
    return result

@app.post("/conductor/approve")
async def conductor_approve(
    plan_id: str,
    username: str,
    approved_action_ids: List[str] = None
):
    """Approve plan"""
    result = await approve_execution_plan(plan_id, username, approved_action_ids)
    return result

@app.post("/conductor/execute")
async def conductor_execute(plan_id: str):
    """Execute plan"""
    result = await execute_plan(plan_id)
    return result

@app.post("/conductor/policy")
async def conductor_policy(username: str, policy: Dict[str, Any]):
    """Set user policy"""
    result = set_user_policy(username, policy)
    return result

@app.get("/conductor/dashboard/{username}/{device_id}")
async def conductor_dashboard(username: str, device_id: str):
    return get_device_dashboard(username, device_id)

from device_oauth_connector import (
    initiate_oauth,
    complete_oauth,
    create_post,
    approve_post,
    reject_post,
    get_connected_platforms,
    get_pending_posts,
    disconnect_platform
)

@app.post("/oauth/initiate")
async def oauth_initiate(username: str, platform: str, redirect_uri: str):
    """Initiate OAuth"""
    result = await initiate_oauth(username, platform, redirect_uri)
    return result

@app.post("/oauth/complete")
async def oauth_complete(username: str, platform: str, code: str, redirect_uri: str):
    """Complete OAuth"""
    result = await complete_oauth(username, platform, code, redirect_uri)
    return result

@app.post("/oauth/post")
async def oauth_post(
    username: str,
    platform: str,
    content: Dict[str, Any],
    schedule_for: str = None
):
    """Create post"""
    result = await create_post(username, platform, content, schedule_for)
    return result

@app.post("/oauth/post/{post_id}/approve")
async def oauth_approve(post_id: str, username: str):
    """Approve post"""
    result = await approve_post(post_id, username)
    return result

@app.post("/oauth/post/{post_id}/reject")
async def oauth_reject(post_id: str, username: str, reason: str = ""):
    """Reject post"""
    result = await reject_post(post_id, username, reason)
    return result

@app.get("/oauth/platforms/{username}")
async def oauth_platforms(username: str):
    return get_connected_platforms(username)

@app.get("/oauth/pending/{username}")
async def oauth_pending(username: str):
    return get_pending_posts(username)

@app.post("/oauth/disconnect")
async def oauth_disconnect(username: str, platform: str):
    """Disconnect platform"""
    result = await disconnect_platform(username, platform)
    return result

from value_chain_engine import (
    discover_value_chain,
    create_value_chain,
    approve_chain_participation,
    execute_chain_action,
    get_chain,
    get_user_chains,
    get_chain_performance,
    get_chain_stats
)

@app.post("/chains/discover")
async def chain_discover(
    initiator: str,
    initiator_capability: str,
    target_outcome: str,
    max_hops: int = 4
):
    """Discover value chains"""
    result = await discover_value_chain(initiator, initiator_capability, target_outcome, max_hops)
    return result

@app.post("/chains/create")
async def chain_create(initiator: str, chain_config: Dict[str, Any]):
    """Create value chain"""
    result = await create_value_chain(initiator, chain_config)
    return result

@app.post("/chains/{chain_id}/approve")
async def chain_approve(chain_id: str, username: str):
    """Approve chain participation"""
    result = await approve_chain_participation(chain_id, username)
    return result

@app.post("/chains/{chain_id}/execute")
async def chain_execute(
    chain_id: str,
    action_type: str,
    action_data: Dict[str, Any],
    executed_by: str
):
    """Execute chain action"""
    result = await execute_chain_action(chain_id, action_type, action_data, executed_by)
    return result

@app.get("/chains/{chain_id}")
async def chain_get(chain_id: str):
    return get_chain(chain_id)

@app.get("/chains/user/{username}")
async def chain_user(username: str):
    return get_user_chains(username)

@app.get("/chains/{chain_id}/performance")
async def chain_performance(chain_id: str):
    return get_chain_performance(chain_id)

@app.get("/chains/stats")
async def chain_stats():
    return get_chain_stats()
    
@app.post("/clone/register")
async def clone_register(
    clone_owner: str,
    clone_id: str,
    original_owner: str,
    generation: int = 1
):
    """Register clone with multi-gen lineage tracking"""
    result = await register_clone_lineage(
        clone_owner=clone_owner,
        clone_id=clone_id,
        original_owner=original_owner,
        generation=generation
    )
    return result

@app.post("/intent/bid")
async def intent_bid(
    agent: str,
    intent_id: str,
    price: Optional[float] = None,  # ✅ NOW OPTIONAL - ARM can suggest
    ttr: str = "48h"
):
    """Bid on intent with ARM price recommendation"""
    users, client = await _get_users_client()
    
    # Find intent
    buyer_user, intent = _global_find_intent(users, intent_id)
    if not intent:
        return {"error": "intent not found"}
    
    if intent.get("status") != "open":
        return {"error": "intent closed"}
    
    # Find agent
    agent_user = _find_user(users, agent)
    if not agent_user:
        return {"error": "agent not found"}
    
    # ✅ ARM PRICE RECOMMENDATION (if price not provided)
    arm_recommendation = None
    
    if not price:
        try:
            outcome_score = int(agent_user.get("outcomeScore", 0))
            existing_bids = intent.get("bids", [])
            
            arm_recommendation = calculate_dynamic_bid_price(
                intent=intent,
                agent_outcome_score=outcome_score,
                existing_bids=existing_bids
            )
            
            if arm_recommendation.get("recommended_bid"):
                price = arm_recommendation["recommended_bid"]
                print(f"💡 ARM recommended price: ${price} for {agent} (tier: {calculate_pricing_tier(outcome_score)['tier']})")
            else:
                # Agent's tier exceeds budget or other issue
                return {
                    "error": "cannot_bid",
                    "reason": arm_recommendation.get("rationale"),
                    "suggestion": arm_recommendation.get("suggestion"),
                    "arm_recommendation": arm_recommendation
                }
        except Exception as e:
            print(f"⚠️ ARM price calculation failed: {e}")
            # Continue without ARM - require manual price
            if not price:
                return {
                    "error": "price_required",
                    "message": "ARM price calculation failed. Please provide a manual price."
                }
    
    # ✅ PRICE VALIDATION
    if not price or price <= 0:
        return {"error": "invalid_price", "price": price}
    
    # Check if price exceeds intent budget
    intent_budget = float(intent.get("budget", 999999))
    if price > intent_budget:
        return {
            "error": "price_exceeds_budget",
            "your_price": price,
            "buyer_budget": intent_budget,
            "suggestion": f"Reduce price to ${intent_budget} or below"
        }
    
    # ✅ CREATE BID
    delivery_hours = int(ttr.replace("h", "")) if "h" in ttr else 48
    
    bid = {
        "id": _uid(),
        "agent": agent,
        "price": float(price),
        "price_usd": float(price),  
        "ttr": ttr,
        "delivery_hours": delivery_hours,  
        "ts": _now(),
        "submitted_at": _now()
    }
    
    # ✅ ADD ARM METADATA (if used)
    if arm_recommendation:
        bid["arm_pricing"] = {
            "recommended": arm_recommendation.get("recommended_bid"),
            "tier": calculate_pricing_tier(agent_user.get("outcomeScore", 0))["tier"],
            "outcome_score": agent_user.get("outcomeScore", 0),
            "adjustment": arm_recommendation.get("adjustment")
        }
    
    # Add to intent
    intent.setdefault("bids", []).append(bid)
    
    await _save_users(client, users)
    
    # Publish event
    try:
        await publish({
            "type": "intent_bid",
            "intent_id": intent_id,
            "agent": agent,
            "price": price,
            "arm_used": arm_recommendation is not None,
            "pricing_tier": calculate_pricing_tier(agent_user.get("outcomeScore", 0))["tier"] if arm_recommendation else None
        })
    except Exception:
        pass
    
    return {
        "ok": True,
        "bid": bid,
        "arm_recommendation": arm_recommendation,
        "message": "Bid submitted successfully"
    }
    
@app.post("/intent/award")
async def intent_award(body: Dict = Body(...)):
    """Award intent + create escrow + stake bond + collect insurance + factoring advance"""
    intent_id = body.get("intent_id")
    bid_id = body.get("bid_id")
    
    async with httpx.AsyncClient(timeout=20) as client:
        users = await _load_users(client)
        
        # Find intent
        buyer_user = None
        intent = None
        
        for user in users:
            for i in user.get("intents", []):
                if i.get("id") == intent_id:
                    buyer_user = user
                    intent = i
                    break
            if intent:
                break
        
        if not intent:
            return {"error": "intent not found"}
        
        # Find winning bid
        bids = intent.get("bids", [])
        if bid_id:
            chosen_bid = next((b for b in bids if b.get("id") == bid_id), None)
        else:
            # Auto-select lowest price
            chosen_bid = min(bids, key=lambda b: b.get("price", float('inf'))) if bids else None
        
        if not chosen_bid:
            return {"error": "no valid bid found"}
        
        # Find agent
        agent_username = chosen_bid.get("agent")
        agent_user = _find_user(users, agent_username)
        
        if not agent_user:
            return {"error": "agent not found"}
        
        # Update intent
        intent["status"] = "ACCEPTED"
        intent["awarded_bid"] = chosen_bid
        intent["awarded_at"] = _now()
        intent["accepted_at"] = _now()
        intent["agent"] = agent_username
        intent["delivery_hours"] = chosen_bid.get("delivery_hours", 48)
        intent["price_usd"] = chosen_bid.get("price", 0)
        
        order_value = float(chosen_bid.get("price", 0))
        
        # ✅ 1. COLLECT INSURANCE (0.5% fee to pool)
        insurance_result = {"ok": False, "fee": 0}
        
        # Find or create insurance pool
        pool_user = next((u for u in users if _uname(u) == "insurance_pool"), None)
        if not pool_user:
            pool_user = {
                "consent": {"username": "insurance_pool", "agreed": True, "timestamp": _now()},
                "username": "insurance_pool",
                "ownership": {"aigx": 0, "ledger": []},
                "role": "system",
                "created_at": _now()
            }
            users.append(pool_user)
        
        try:
            insurance_result = await collect_insurance(agent_user, intent, order_value)
            
            if insurance_result["ok"]:
                # Credit insurance pool
                fee = insurance_result["fee"]
                pool_user["ownership"]["aigx"] = float(pool_user["ownership"].get("aigx", 0)) + fee
                pool_user["ownership"].setdefault("ledger", []).append({
                    "ts": _now(),
                    "amount": fee,
                    "currency": "AIGx",
                    "basis": "insurance_premium",
                    "agent": agent_username,
                    "ref": intent_id,
                    "order_value": order_value
                })
        except Exception as e:
            print(f"⚠️ Insurance collection failed: {e}")
            insurance_result = {"ok": False, "error": str(e), "warning": "Insurance collection failed"}
        
        # ✅ 2. REQUEST FACTORING ADVANCE
        factoring_result = {"ok": False, "net_advance": 0, "holdback": 0}
        
        try:
            factoring_result = await request_factoring_advance(agent_user, intent)
            
            if not factoring_result["ok"]:
                factoring_result["warning"] = factoring_result.get("error", "Factoring unavailable")
                print(f"⚠️ Factoring unavailable: {factoring_result.get('error')}")
        except Exception as e:
            print(f"⚠️ Factoring request failed: {e}")
            factoring_result = {"ok": False, "error": str(e), "warning": "Factoring request failed"}
        
        # ✅ 3. STAKE BOND
        bond_result = {"ok": False, "bond_amount": 0}
        
        try:
            bond_result = await stake_bond(agent_user, intent)
            
            if not bond_result["ok"]:
                bond_result["warning"] = "Agent needs more AIGx for performance bond"
        except Exception as e:
            print(f"⚠️ Bond staking failed: {e}")
            bond_result = {"ok": False, "error": str(e), "warning": "Bond staking failed"}
        
        # ✅ 4. CREATE ESCROW
        escrow_result = {"ok": False}
        
        try:
            buyer_email = buyer_user.get("consent", {}).get("username") + "@aigentsy.com"
            escrow_result = await create_payment_intent(
                amount=order_value,
                buyer_email=buyer_email,
                intent_id=intent_id,
                metadata={
                    "buyer": _uname(buyer_user),
                    "agent": agent_username
                }
            )
            
            if escrow_result["ok"]:
                intent["payment_intent_id"] = escrow_result["payment_intent_id"]
                intent["escrow_status"] = "authorized"
                intent["escrow_created_at"] = _now()
        except Exception as e:
            print(f"⚠️ Escrow creation failed: {e}")
            escrow_result = {"ok": False, "error": str(e)}
        
        # Save all changes
        await _save_users(client, users)
        
        # Publish event
        try:
            await publish({
                "type": "intent_award",
                "intent_id": intent_id,
                "agent": agent_username,
                "buyer": _uname(buyer_user),
                "order_value": order_value,
                "escrow_created": escrow_result["ok"],
                "bond_staked": bond_result.get("ok", False),
                "bond_amount": bond_result.get("bond_amount", 0),
                "insurance_collected": insurance_result.get("ok", False),
                "insurance_fee": insurance_result.get("fee", 0),
                "factoring_advanced": factoring_result.get("ok", False),
                "factoring_amount": factoring_result.get("net_advance", 0),
                "factoring_tier": factoring_result.get("factoring_tier", "new")
            })
        except Exception as e:
            print(f"⚠️ Event publish failed: {e}")
        
        return {
            "ok": True,
            "award": chosen_bid,
            "escrow": escrow_result,
            "bond": bond_result,
            "insurance": insurance_result,
            "factoring": factoring_result,
            "summary": {
                "order_value": order_value,
                "insurance_fee": insurance_result.get("fee", 0),
                "bond_staked": bond_result.get("bond_amount", 0),
                "factoring_advance": factoring_result.get("net_advance", 0),
                "factoring_fee": factoring_result.get("factoring_fee", 0),
                "factoring_tier": factoring_result.get("factoring_tier", "new"),
                "agent_receives_now": factoring_result.get("net_advance", 0),
                "agent_receives_on_delivery": factoring_result.get("holdback", 0),
                "escrow_authorized": escrow_result.get("ok", False)
            },
            "agent_net_summary": {
                "immediate_cash": factoring_result.get("net_advance", 0),
                "costs_paid": insurance_result.get("fee", 0) + factoring_result.get("factoring_fee", 0),
                "bond_staked_aigx": bond_result.get("bond_amount", 0),
                "remaining_on_delivery": factoring_result.get("holdback", 0),
                "net_immediate": round(
                    factoring_result.get("net_advance", 0) - 
                    insurance_result.get("fee", 0), 
                    2
                )
            }
        }
        

@app.post("/productize")
async def productize(username: str, url: Optional[str] = None, file_meta: dict = None):
    users, client = await _get_users_client()
    u = _find_user(users, username)
    if not u: return {"error":"user not found"}
    offer = {"id": _uid(), "title": "Auto Productized Offer", "source": url or file_meta or {}, "price": 199, "created": _now()}
    u.setdefault("offers", []).append(offer)
    await _save_users(client, users)
    return {"ok": True, "offer": offer}

@app.post("/quote")
async def quote(buyer: str, seller: str, scope: str, ttr: str = "48h"):
    users, client = await _get_users_client()
    sb = _find_user(users, seller); bb = _find_user(users, buyer)
    if not (sb and bb): return {"error":"buyer or seller not found"}
    base = 199.0
    price = base * (1.5 if (ttr or '').lower().startswith("24") else 1.0)
    q = {"id": _uid(), "ts": _now(), "buyer": buyer, "seller": seller, "scope": scope, "ttr": ttr, "price": price, "status":"open"}
    sb.setdefault("quotes", []).append(q)
    bb.setdefault("quotes", []).append(q)
    await _save_users(client, users)
    return {"ok": True, "quote": q}

@app.post("/escrow/create")
async def escrow_create(quote_id: str, buyer: str):
    users, client = await _get_users_client()
    b = _find_user(users, buyer)
    if not b: return {"error":"buyer not found"}
    e = {"id": _uid(), "quote_id": quote_id, "status":"held", "ts": _now()}
    b.setdefault("escrow", []).append(e)
    await _save_users(client, users)
    return {"ok": True, "escrow": e}

@app.post("/escrow/release")
async def escrow_release(escrow_id: str):
    users, client = await _get_users_client()
    for u in users:
        for e in u.get("escrow", []):
            if e["id"]==escrow_id:
                e["status"] = "released"; await _save_users(client, users); return {"ok": True}
    return {"error":"escrow not found"}

@app.post("/escrow/dispute")
async def escrow_dispute(escrow_id: str, reason: str):
    users, client = await _get_users_client()
    for u in users:
        for e in u.get("escrow", []):
            if e["id"]==escrow_id:
                e["status"] = "disputed"; e["reason"]=reason; await _save_users(client, users); return {"ok": True}
    return {"error":"escrow not found"}

@app.post("/offer/localize")
async def offer_localize(username: str, offer_id: str, locales: List[str]):
    users, client = await _get_users_client()
    u = _find_user(users, username)
    if not u: return {"error":"user not found"}
    variants = []
    for loc in locales or []:
        variants.append({"id": _uid(), "base": offer_id, "locale": loc, "ts": _now()})
    u.setdefault("offer_variants", []).extend(variants)
    await _save_users(client, users)
    return {"ok": True, "variants": variants}

@app.get("/fx")
async def fx():
    return {"USD":1.0,"EUR":0.93,"GBP":0.81,"JPY":149.0}

@app.post("/media/bind_offer")
async def media_bind_offer(username: str, media_id: str, offer_id: str):
    users, client = await _get_users_client()
    u = _find_user(users, username)
    if not u: return {"error":"user not found"}
    m = {"media_id": media_id, "offer_id": offer_id, "ts": _now()}
    u.setdefault("media_bindings", []).append(m)
    await _save_users(client, users)
    return {"ok": True, "binding": m}

@app.post("/team/create")
async def team_create(lead_owner: str, members: List[str], split: List[float]):
    users, client = await _get_users_client()
    lead = _find_user(users, lead_owner)
    if not lead: return {"error":"lead not found"}
    team = {"id": _uid(), "members": members, "split": split, "ts": _now()}
    lead.setdefault("teams", []).append(team)
    await _save_users(client, users)
    return {"ok": True, "team": team}

@app.post("/team/offer")
async def team_offer(lead_owner: str, team_id: str, bundle_spec: dict):
    users, client = await _get_users_client()
    lead = _find_user(users, lead_owner)
    if not lead: return {"error":"lead not found"}
    t = next((x for x in lead.get("teams", []) if x["id"]==team_id), None)
    if not t: return {"error":"team not found"}
    off = {"id": _uid(), "team_id": team_id, "spec": bundle_spec, "ts": _now()}
    lead.setdefault("team_offers", []).append(off)
    await _save_users(client, users)
    return {"ok": True, "team_offer": off}

@app.post("/retarget/schedule")
async def retarget_schedule(username: str, lead_id: str, cadence: str = "3d", incentive: str = "AIGx10"):
    users, client = await _get_users_client()
    u = _find_user(users, username)
    if not u: return {"error":"user not found"}
    task = {"id": _uid(), "lead_id": lead_id, "cadence": cadence, "incentive": incentive, "ts": _now()}
    u.setdefault("retarget_tasks", []).append(task)
    await _save_users(client, users)
    return {"ok": True, "task": task}

@app.get("/market/rank")
async def market_rank(category: Optional[str] = None):
    users, client = await _get_users_client()
    ranked = []
    for u in users:
        score = int(u.get("outcomeScore", 0))
        completion = len(u.get("outcomes", []))
        response_bonus = 1 if len(u.get("analytics", []))>0 else 0
        price_bias = 0
        ranked.append({"username": _username_of(u), "rank": score + completion + response_bonus - price_bias})
    ranked.sort(key=lambda r: r["rank"], reverse=True)
    return {"ok": True, "results": ranked[:100]}

@app.get("/offer/upsells")
async def offer_upsells(offer_id: str):
    return {"ok": True, "upsells":[
        {"id":"rush","title":"Rush Delivery (24h)","price_delta":99},
        {"id":"brandpack","title":"Brand Pack Add-on","price_delta":149},
        {"id":"support30","title":"30 Days Support","price_delta":79}
    ]}

@app.post("/concierge/triage")
async def concierge_triage(text: str):
    scope = "General help with " + (text[:120] if text else "your project")
    suggested = [{"title":"Starter Offer","price":149},{"title":"Pro Offer","price":299}]
    return {"ok": True, "scope": scope, "suggested_offers": suggested, "price_bands":[149,299,499]}

# ============ REVENUE INGESTION ENDPOINTS ============

@app.post("/webhooks/shopify")
async def shopify_webhook(request: Request):
    """Shopify order webhook"""
    # Get headers
    topic = request.headers.get("X-Shopify-Topic", "")
    shop_domain = request.headers.get("X-Shopify-Shop-Domain", "")
    received_hmac = request.headers.get("X-Shopify-Hmac-Sha256", "")
    
    # Get raw body for HMAC verification
    raw_body = await request.body()
    
    # Verify HMAC (you need to implement this based on your Shopify secret)
    # For now, we'll skip verification in development
    
    # Parse payload
    try:
        payload = await request.json()
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    # Map shop domain to username (you need to configure this)
    # For now, use a default username
    username = os.getenv("SHOPIFY_USERNAME", "demo_user")
    
    # Extract order details
    order_id = str(payload.get("id", ""))
    revenue_usd = float(payload.get("total_price") or payload.get("current_total_price") or 0)
    
    # Ingest revenue
    result = await ingest_shopify_order(username, order_id, revenue_usd)
    
    return result


@app.post("/revenue/affiliate")
async def affiliate_commission(
    username: str,
    source: str,  # "tiktok" or "amazon"
    revenue_usd: float,
    product_id: Optional[str] = None
):
    """Ingest affiliate commission"""
    result = await ingest_affiliate_commission(username, source, revenue_usd, product_id)
    return result


@app.post("/revenue/cpm")
async def content_cpm(
    username: str,
    platform: str,  # "youtube" or "tiktok"
    views: int,
    cpm_rate: float
):
    """Ingest content CPM revenue"""
    result = await ingest_content_cpm(username, platform, views, cpm_rate)
    return result


@app.post("/revenue/service")
async def service_payment(
    username: str,
    invoice_id: str,
    amount_usd: float
):
    """Ingest service payment"""
    result = await ingest_service_payment(username, invoice_id, amount_usd)
    return result


@app.post("/revenue/staking")
async def staking_returns(username: str, amount_usd: float):
    """Distribute staking returns"""
    result = await distribute_staking_returns(username, amount_usd)
    return result


@app.get("/revenue/summary")
async def earnings_summary(username: str):
    """Get earnings breakdown"""
    result = get_earnings_summary(username)
    return result


# ============ JV & ROYALTY ENDPOINTS ============

@app.post("/revenue/jv_split")
async def jv_split(username: str, amount_usd: float, jv_id: str):
    """Split revenue with JV partner"""
    result = await split_jv_revenue(username, amount_usd, jv_id)
    return result


@app.post("/revenue/clone_royalty")
async def clone_royalty(username: str, amount_usd: float, clone_id: str):
    """Pay clone royalty to original owner"""
    result = await distribute_clone_royalty(username, amount_usd, clone_id)
    return result


# ============ AGENT SPENDING ENDPOINTS ============

@app.post("/agent/check_spend")
async def check_spend(username: str, amount_usd: float):
    """Check if agent can spend amount"""
    result = await check_spending_capacity(username, amount_usd)
    return result


@app.post("/agent/spend")
async def agent_spend(username: str, amount_usd: float, basis: str, ref: Optional[str] = None):
    """Execute agent spending"""
    result = await execute_agent_spend(username, amount_usd, basis, ref)
    return result


@app.post("/agent/pay")
async def agent_pay(from_user: str, to_user: str, amount_usd: float, reason: str):
    """Agent-to-agent payment"""
    result = await agent_to_agent_payment(from_user, to_user, amount_usd, reason)
    return result


@app.get("/agent/spending")
async def spending_summary(username: str):
    """Get agent spending analytics"""
    result = get_spending_summary(username)
    return result
    
# ===== AiGentsy AAM — helpers (idempotent) =====
import base64, hmac, hashlib, os, json as _json

def _now_utc():
    import datetime as _dt
    return _dt.datetime.utcnow().isoformat() + "Z"

def _uid_gen():
    import uuid as _uuid
    return str(_uuid.uuid4())

# Generic provider event recorder into your existing JSON store.
# Reuses your _get_users_client() and _save_users() helpers.
async def _record_provider_event(provider: str, topic: str, payload: dict):
    users, client = await _get_users_client()
    event = {
        "id": _uid(),
        "source": provider,
        "topic": topic,
        "payload": payload or {},
        "ts": _now()
    }
    # Append to a global bucket; adjust to per-user mapping if desired.
    # We try to place it on the first record to avoid schema surprises.
    if not users:
        return {"ok": False, "reason": "no_user_records"}
    users[0].setdefault("events", []).append(event)
    await _save_users(client, users)
    return {"ok": True, "event_id": event["id"]}

def _shopify_hmac_valid(secret: str, raw_body: bytes, received_hmac: str) -> bool:
    digest = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).digest()
    calc = base64.b64encode(digest).decode("utf-8")
    return hmac.compare_digest(calc, (received_hmac or "").strip())


# ===== AiGentsy AAM — trigger endpoint =====
from fastapi import Request

# ===== AiGentsy AAM — provider webhooks =====
from fastapi import Request, HTTPException

# --- Safe fallbacks for optional AAM runtime modules ---
try:
    from aam_queue import AAMQueue  # provided by your AAM package
except Exception:  # ModuleNotFoundError or others
    class AAMQueue:  # minimal no-op queue to avoid import errors in deployments without AAM bundle
        def __init__(self, executor=None):
            self.executor = executor
        def submit(self, job):
            # immediate pass-through for demo
            if self.executor:
                try:
                    return self.executor(job)
                except Exception:
                    return {"ok": False, "error": "executor_failed"}
            return {"ok": True, "status": "queued", "job": job}

try:
    from sdk_aam_executor import execute  # orchestrates AAM actions
except Exception:
    def execute(job):
        # minimal fallback executor
        return {"ok": True, "executed": False, "reason": "sdk_aam_executor missing", "job": job}

try:
    from caio_orchestrator import run_play  # runs a named play through the AAM queue
except Exception:
    def run_play(queue, user_id, app_name, slug, context, autonomy):
        # minimal fallback orchestrator
        job = {
            "user_id": user_id,
            "app": app_name,
            "slug": slug,
            "context": context,
            "autonomy": autonomy
        }
        return {"ok": True, "ran": False, "reason": "caio_orchestrator missing", "result": queue.submit(job)}


# Single global queue instance
try:
    QUEUE  # type: ignore
except NameError:
    QUEUE = AAMQueue(executor=execute)

@app.post("/aam/run/{app_name}/{slug}")
async def run_aam(app_name: str, slug: str, req: Request):
    body = await req.json()
    user_id  = body.get("user_id") or "demo_user"
    context  = body.get("context") or {}
    autonomy = body.get("autonomy") or {"level":"suggest","policy":{"block":[]}}
    results = run_play(QUEUE, user_id, app_name, slug, context, autonomy)
    return {"ok": True, "results": results}


# ===== AiGentsy AAM — provider webhooks =====
from fastapi import Request, HTTPException

# Shopify (HMAC-verified)
@app.post("/webhook/shopify")
async def webhook_shopify(request: Request):
    secret = os.getenv("SHOPIFY_API_SECRET") or os.getenv("SHOPIFY_WEBHOOK_SECRET") or ""
    if not secret:
        raise HTTPException(status_code=500, detail="SHOPIFY_API_SECRET/SHOPIFY_WEBHOOK_SECRET not configured")
    topic = request.headers.get("X-Shopify-Topic", "") or "unknown"
    shop_domain = request.headers.get("X-Shopify-Shop-Domain", "")
    received_hmac = request.headers.get("X-Shopify-Hmac-Sha256", "")
    raw = await request.body()
    if not _shopify_hmac_valid(secret, raw, received_hmac):
        raise HTTPException(status_code=401, detail="Invalid HMAC")
    try:
        payload = _json.loads(raw.decode("utf-8") or "{}")
    except Exception:
        payload = {}
    payload.setdefault("shop_domain", shop_domain)
    rec = await _record_provider_event("shopify", topic, payload)
    return {"ok": True, **(rec or {})}

# TikTok (signature optional / TODO)
@app.post("/webhook/tiktok")
async def webhook_tiktok(request: Request):
    raw = await request.body()
    try:
        payload = _json.loads(raw.decode("utf-8") or "{}")
    except Exception:
        payload = {}
    topic = payload.get("event") or request.headers.get("X-Tt-Event", "unknown")
    rec = await _record_provider_event("tiktok", topic, payload)
    return {"ok": True, **(rec or {})}

# Amazon (shared-secret optional / TODO)
@app.post("/webhook/amazon")
async def webhook_amazon(request: Request):
    raw = await request.body()
    try:
        payload = _json.loads(raw.decode("utf-8") or "{}")
    except Exception:
        payload = {}
    topic = payload.get("event") or request.headers.get("X-Amazon-Event", "unknown")
    rec = await _record_provider_event("amazon", topic, payload)
    return {"ok": True, **(rec or {})}


import os
from aam_stripe import verify_stripe_signature, process_stripe_webhook

@app.post("/webhook/stripe")
async def webhook_stripe(request: Request):
    """Stripe webhook handler"""
    
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")
    
    stripe_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    
    if stripe_secret and not verify_stripe_signature(payload, signature, stripe_secret):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    try:
        event = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    event_type = event.get("type")
    
    result = await process_stripe_webhook(event_type, event)
    
    return result

from pricing_oracle import (
    calculate_dynamic_price,
    suggest_optimal_pricing,
    get_competitive_pricing
)

@app.post("/pricing/dynamic")
async def pricing_dynamic(
    base_price: float,
    agent: str,
    context: Dict[str, Any] = None
):
    """Calculate dynamic price"""
    result = await calculate_dynamic_price(base_price, agent, context)
    return result

@app.post("/pricing/optimize")
async def pricing_optimize(
    service_type: str,
    agent: str,
    target_conversion_rate: float = 0.50
):
    """Get optimal pricing suggestion"""
    result = await suggest_optimal_pricing(service_type, agent, target_conversion_rate)
    return result

@app.get("/pricing/competitive")
async def pricing_competitive(
    service_type: str,
    quality_tier: str = "standard"
):
    """Get competitive market pricing"""
    result = await get_competitive_pricing(service_type, quality_tier)
    return result
    
# === AIGENTSY EXPANSION ROUTES (non-destructive) ===
try:
    from fastapi import APIRouter, Request
except Exception:
    APIRouter = None
    Request = None

# Create a router to avoid touching your existing app routes.
_expansion_router = APIRouter() if 'APIRouter' in globals() and APIRouter else None

def _safe_json(obj):
    try:
        import json
        json.dumps(obj)
        return obj
    except Exception:
        return {"ok": False, "error": "unserializable_response"}

def _event_emit(kind: str, data: dict):
    try:
        from events import emit as _emit
        _emit(kind, data or {})
    except Exception:
        pass
    try:
        from log_to_jsonbin_aam_patched import log_event as _log
        _log({"kind": kind, **(data or {})})
    except Exception:
        pass

# ----- MetaBridge DealGraph -----
if _expansion_router:
    @_expansion_router.post("/metabridge/dealgraph/create")
    async def metabridge_dealgraph_create(payload: dict):
        try:
            from metabridge_dealgraph import create_dealgraph
            opportunity = payload.get("opportunity") or {}
            roles = payload.get("roles") or payload.get("roles_needed") or []
            rev_split = payload.get("rev_split") or []
            graph = create_dealgraph(opportunity, roles, rev_split)
            _event_emit("DEALGRAPH_CREATED", {"graph_id": graph.get("id"), **opportunity})
            return _safe_json({"ok": True, "graph": graph})
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @_expansion_router.post("/metabridge/dealgraph/activate")
    async def metabridge_dealgraph_activate(payload: dict):
        try:
            from metabridge_dealgraph import activate
            gid = payload.get("graph_id") or payload.get("id")
            res = activate(gid)
            _event_emit("DEALGRAPH_ACTIVATED", {"graph_id": gid})
            return _safe_json({"ok": True, "result": res})
        except Exception as e:
            return {"ok": False, "error": str(e)}

# ----- Pricing A/B Arm -----
if _expansion_router:
    @_expansion_router.post("/pricing/arm")
    async def pricing_arm_endpoint(payload: dict):
        try:
            from pricing_arm import start_bundle_test, next_arm, record_outcome, best_arm
            op = (payload.get("op") or "").lower()
            username = payload.get("username") or payload.get("user") or "chatgpt"
            if payload.get("bundles") and not op:
                op = "start"
            if payload.get("bundle_id") and "revenue_usd" in payload and not op:
                op = "record"

            if op == "start":
                bundles = payload.get("bundles") or []
                epsilon = float(payload.get("epsilon", 0.15))
                exp = await start_bundle_test(username, bundles, epsilon)
                return _safe_json({"ok": True, "experiment": exp})
            elif op == "next":
                exp_id = payload.get("exp_id")
                arm = await next_arm(username, exp_id)
                return _safe_json({"ok": True, "choice": arm})
            elif op == "record":
                exp_id = payload.get("exp_id")
                bundle_id = payload.get("bundle_id")
                revenue = float(payload.get("revenue_usd", 0))
                out = await record_outcome(username, exp_id, bundle_id, revenue)
                _event_emit("PAID", {"user": username, "value_usd": revenue, "bundle_id": bundle_id})
                return _safe_json(out)
            elif op == "best":
                exp_id = payload.get("exp_id")
                out = await best_arm(username, exp_id)
                return _safe_json({"ok": True, "best": out})
            else:
                return {"ok": False, "error": "unknown_op", "hint": "use op=start|next|record|best"}
        except Exception as e:
            return {"ok": False, "error": str(e)}


# ----- Shopify inventory proxy -----
if _expansion_router:
    @_expansion_router.get("/inventory/get")
    async def inventory_get(product_id: str):
        try:
            from shopify_inventory_proxy import get_stock
            return _safe_json({"ok": True, **get_stock(product_id)})
        except Exception as e:
            return {"ok": False, "error": str(e)}

# ----- Co-op sponsors -----
if _expansion_router:
    @_expansion_router.post("/coop/sponsor")
    async def coop_sponsor(payload: dict):
        try:
            from coop_sponsors import sponsor_add, state
            name = payload.get("name") or "anon"
            cap = float(payload.get("spend_cap_usd", 0))
            sponsor_add(name, cap)
            return _safe_json({"ok": True, "state": state()})
        except Exception as e:
            return {"ok": False, "error": str(e)}

# ----- LTV predictor -----
if _expansion_router:
    @_expansion_router.post("/ltv/predict")
    async def ltv_predict(payload: dict):
        try:
            from ltv_forecaster import predict
            user = payload.get("user") or {}
            channel = payload.get("channel") or "tiktok"
            val = predict(user, channel)
            return _safe_json({"ok": True, "ltv": float(val)})
        except Exception as e:
            return {"ok": False, "error": str(e)}

# ----- Proposal auto-close -----
if _expansion_router:
    @_expansion_router.post("/proposal/nudge")
    async def proposal_nudge(payload: dict):
        try:
            from proposal_autoclose import nudge
            pid = payload.get("proposal_id") or payload.get("id")
            res = nudge(pid)
            _event_emit("PROPOSAL_NUDGED", {"proposal_id": pid})
            return _safe_json(res)
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @_expansion_router.post("/proposal/convert")
    async def proposal_convert(payload: dict):
        try:
            from proposal_autoclose import convert_to_quickpay
            pid = payload.get("proposal_id") or payload.get("id")
            res = convert_to_quickpay(pid)
            _event_emit("PROPOSAL_CONVERTED", {"proposal_id": pid})
            return _safe_json(res)
        except Exception as e:
            return {"ok": False, "error": str(e)}

# ---- Mount the router if an app exists ----
try:
    app  # type: ignore  # check if app is already defined in your file
    if _expansion_router:
        app.include_router(_expansion_router)
except Exception:
    # No FastAPI app found or not constructed yet — safe to skip
    pass
# ===== MOUNT ALL UPGRADED ROUTERS =====
if intent_router:
    app.include_router(intent_router, prefix="/intents", tags=["Intent Exchange"])

if dealgraph_router:
    app.include_router(dealgraph_router, prefix="/dealgraph", tags=["MetaBridge"])

if r3_router:
    app.include_router(r3_router, prefix="/r3", tags=["R³ Budget"])

# Mount expansion router (for any remaining stubs)
try:
    app.include_router(_expansion_router)
except Exception:
    pass
@app.get("/events/stream")
async def events_stream():
    # Reuse the existing SSE generator
    return await stream_activity()

# === Expansion router (ensures required endpoints exist) ===
from fastapi import APIRouter, Request, HTTPException
_expansion_router = APIRouter()

@_expansion_router.post("/pricing/arm")
async def _exp_pricing_arm(payload: dict):
    try:
        from pricing_arm import start_bundle_test, next_arm, record_outcome, best_arm
        op = (payload.get("op") or "").lower()
        if payload.get("bundles") and not op: op = "start"
        if payload.get("bundle_id") and "revenue_usd" in payload and not op: op = "record"
        if op == "start":
            return {"ok": True, "experiment": await start_bundle_test(payload.get("username","sys"), payload.get("bundles"), float(payload.get("epsilon",0.15)))}
        if op == "next":
            return {"ok": True, "choice": await next_arm(payload.get("username","sys"), payload.get("exp_id"))}
        if op == "record":
            out = await record_outcome(payload.get("username","sys"), payload.get("exp_id"), payload.get("bundle_id"), float(payload.get("revenue_usd",0)))
            return {"ok": True, **out}
        if op == "best":
            return {"ok": True, "best": await best_arm(payload.get("username","sys"), payload.get("exp_id"))}
        return {"ok": False, "error": "unknown_op"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@_expansion_router.post("/intents/claim")
async def _exp_intents_claim(payload: dict):
    try:
        from intent_exchange import claim
        return {"ok": True, "intent": claim(payload.get("intent_id") or payload.get("id"), payload.get("agent") or payload.get("username"))}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@_expansion_router.post("/intents/settle")
async def _exp_intents_settle(payload: dict):
    try:
        from intent_exchange import settle
        return {"ok": True, "intent": settle(payload.get("intent_id") or payload.get("id"), payload.get("outcome") or {})}
    except Exception as e:
        return {"ok": False, "error": str(e)}
   
# Mount it
if r3_router:
    app.include_router(r3_router, prefix="/r3", tags=["R³ Budget"])
@_expansion_router.post("/r3/allocate")
async def _exp_r3_allocate(payload: dict):
    try:
        from r3_router import allocate
        return {"ok": True, **allocate(payload.get("user") or {}, float(payload.get("budget_usd",0)))}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# Mount it
if r3_router:
    app.include_router(r3_router, prefix="/r3", tags=["R³ Budget"])
@_expansion_router.get("/inventory/get")
async def _exp_inventory_get(product_id: str):
    try:
        from shopify_inventory_proxy import get_stock
        return {"ok": True, **get_stock(product_id)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

from yield_memory import (
    store_pattern,
    find_similar_patterns,
    get_best_action,
    get_patterns_to_avoid,
    get_memory_stats,
    export_memory,
    import_memory
)

@app.post("/memory/store")
async def memory_store(
    username: str,
    pattern_type: str,
    context: Dict[str, Any],
    action: Dict[str, Any],
    outcome: Dict[str, Any]
):
    """Store a yield pattern"""
    result = store_pattern(
        username=username,
        pattern_type=pattern_type,
        context=context,
        action=action,
        outcome=outcome
    )
    return result

@app.post("/memory/recommend")
async def memory_recommend(
    username: str,
    context: Dict[str, Any],
    pattern_type: str = None
):
    """Get recommended action based on memory"""
    result = get_best_action(
        username=username,
        context=context,
        pattern_type=pattern_type
    )
    return result

@app.post("/memory/avoid")
async def memory_avoid(
    username: str,
    context: Dict[str, Any],
    pattern_type: str = None
):
    """Get patterns to avoid"""
    result = get_patterns_to_avoid(
        username=username,
        context=context,
        pattern_type=pattern_type
    )
    return result

@app.get("/memory/stats/{username}")
async def memory_stats(username: str):
    """Get memory statistics"""
    return get_memory_stats(username)

@app.get("/memory/export/{username}")
async def memory_export(username: str):
    """Export memory as JSON"""
    json_data = export_memory(username)
    return {"ok": True, "json": json_data}

@app.post("/memory/import")
async def memory_import(username: str, json_data: str):
    """Import memory from JSON"""
    result = import_memory(username, json_data)
    return result

@app.post("/memory/import")
async def memory_import(username: str, json_data: str):
    """Import memory from JSON"""
    result = import_memory(username, json_data)
    return result

# ADD HIVE ENDPOINTS HERE

from metahive_brain import (
    contribute_to_hive,
    query_hive,
    report_pattern_usage,
    get_hive_stats,
    get_top_patterns
)

@app.post("/hive/contribute")
async def hive_contribute(
    username: str,
    pattern_type: str,
    context: Dict[str, Any],
    action: Dict[str, Any],
    outcome: Dict[str, Any],
    anonymize: bool = True
):
    """Contribute pattern to hive"""
    result = await contribute_to_hive(
        username=username,
        pattern_type=pattern_type,
        context=context,
        action=action,
        outcome=outcome,
        anonymize=anonymize
    )
    return result

@app.post("/hive/query")
async def hive_query(
    context: Dict[str, Any],
    pattern_type: str = None,
    min_weight: float = 1.0,
    limit: int = 5
):
    """Query hive for patterns"""
    result = query_hive(
        context=context,
        pattern_type=pattern_type,
        min_weight=min_weight,
        limit=limit
    )
    return result

@app.post("/hive/report")
async def hive_report(
    pattern_id: str,
    success: bool,
    actual_roas: float = None
):
    """Report pattern usage"""
    result = report_pattern_usage(
        pattern_id=pattern_id,
        success=success,
        actual_roas=actual_roas
    )
    return result

@app.get("/hive/stats")
async def hive_stats():
    """Get hive statistics"""
    return get_hive_stats()

@app.get("/hive/top")
async def hive_top(
    pattern_type: str = None,
    sort_by: str = "weight",
    limit: int = 20
):
    """Get top patterns"""
    return get_top_patterns(
        pattern_type=pattern_type,
        sort_by=sort_by,
        limit=limit
    )

from jv_mesh import (
    create_jv_proposal,
    vote_on_jv,
    dissolve_jv,
    get_jv_proposal,
    get_active_jv,
    list_jv_proposals,
    list_active_jvs
)

@app.post("/jv/propose")
async def jv_propose(
    proposer: str,
    partner: str,
    title: str,
    description: str,
    revenue_split: Dict[str, float],
    duration_days: int = 90,
    terms: Dict[str, Any] = None
):
    """Create JV proposal"""
    result = await create_jv_proposal(
        proposer=proposer,
        partner=partner,
        title=title,
        description=description,
        revenue_split=revenue_split,
        duration_days=duration_days,
        terms=terms
    )
    return result

@app.post("/jv/vote")
async def jv_vote(
    proposal_id: str,
    voter: str,
    vote: str,
    feedback: str = ""
):
    """Vote on JV proposal"""
    result = await vote_on_jv(
        proposal_id=proposal_id,
        voter=voter,
        vote=vote,
        feedback=feedback
    )
    return result

@app.post("/jv/dissolve")
async def jv_dissolve(
    jv_id: str,
    requester: str,
    reason: str = ""
):
    """Dissolve JV"""
    result = await dissolve_jv(
        jv_id=jv_id,
        requester=requester,
        reason=reason
    )
    return result

@app.get("/jv/proposals/{proposal_id}")
async def jv_proposal_get(proposal_id: str):
    return get_jv_proposal(proposal_id)

@app.get("/jv/{jv_id}")
async def jv_get(jv_id: str):
    return get_active_jv(jv_id)

@app.get("/jv/proposals/list")
async def jv_proposals_list(party: str = None, status: str = None):
    return list_jv_proposals(party=party, status=status)

@app.get("/jv/list")
async def jv_list(party: str = None):
    return list_active_jvs(party=party)
@_expansion_router.post("/coop/sponsor")
async def _exp_coop_sponsor(payload: dict):
    try:
        from coop_sponsors import sponsor_add, state
        sponsor_add(payload.get("name") or "anon", float(payload.get("spend_cap_usd",0)))
        return {"ok": True, "state": state()}
    except Exception as e:
        return {"ok": False, "error": str(e)}

from fraud_detector import (
    check_fraud_signals,
    suspend_account,
    report_fraud,
    resolve_fraud_case,
    get_fraud_case,
    list_fraud_cases,
    get_user_risk_profile,
    get_fraud_stats
)

@app.post("/fraud/check")
async def fraud_check(
    username: str,
    action_type: str,
    metadata: Dict[str, Any] = None
):
    """Check for fraud signals"""
    result = await check_fraud_signals(username, action_type, metadata)
    return result

@app.post("/fraud/suspend")
async def fraud_suspend(
    username: str,
    reason: str,
    evidence: List[str]
):
    """Suspend account"""
    result = await suspend_account(username, reason, evidence)
    return result

@app.post("/fraud/report")
async def fraud_report(
    reporter: str,
    reported_user: str,
    fraud_type: str,
    description: str,
    evidence: Dict[str, Any] = None
):
    """Report fraud"""
    result = report_fraud(reporter, reported_user, fraud_type, description, evidence)
    return result

@app.post("/fraud/resolve")
async def fraud_resolve(
    case_id: str,
    resolution: str,
    action: str,
    notes: str = ""
):
    """Resolve fraud case"""
    result = resolve_fraud_case(case_id, resolution, action, notes)
    return result

@app.get("/fraud/case/{case_id}")
async def fraud_case(case_id: str):
    return get_fraud_case(case_id)

@app.get("/fraud/cases")
async def fraud_cases(username: str = None, status: str = None):
    return list_fraud_cases(username, status)

@app.get("/fraud/profile/{username}")
async def fraud_profile(username: str):
    return get_user_risk_profile(username)

@app.get("/fraud/stats")
async def fraud_stats():
    return get_fraud_stats()

from dispute_resolution import (
    file_dispute,
    respond_to_dispute,
    make_settlement_offer,
    accept_settlement,
    escalate_to_arbitration,
    arbitrate_dispute,
    get_dispute,
    list_disputes,
    get_dispute_stats
)

@app.post("/disputes/file")
async def dispute_file(
    claimant: str,
    respondent: str,
    dispute_type: str,
    amount_usd: float,
    description: str,
    evidence: List[Dict[str, Any]] = None
):
    """File dispute"""
    result = await file_dispute(claimant, respondent, dispute_type, amount_usd, description, evidence)
    return result

@app.post("/disputes/respond")
async def dispute_respond(
    dispute_id: str,
    respondent: str,
    response: str,
    counter_evidence: List[Dict[str, Any]] = None
):
    """Respond to dispute"""
    result = respond_to_dispute(dispute_id, respondent, response, counter_evidence)
    return result

@app.post("/disputes/offer")
async def dispute_offer(
    dispute_id: str,
    offerer: str,
    offer_type: str,
    offer_amount: float = None,
    offer_terms: str = ""
):
    """Make settlement offer"""
    result = make_settlement_offer(dispute_id, offerer, offer_type, offer_amount, offer_terms)
    return result

@app.post("/disputes/accept")
async def dispute_accept(
    dispute_id: str,
    offer_id: str,
    accepter: str
):
    """Accept settlement"""
    result = await accept_settlement(dispute_id, offer_id, accepter)
    return result

@app.post("/disputes/escalate")
async def dispute_escalate(dispute_id: str):
    """Escalate to arbitration"""
    result = escalate_to_arbitration(dispute_id)
    return result

@app.post("/disputes/arbitrate")
async def dispute_arbitrate(
    dispute_id: str,
    ruling: str,
    claimant_award: float,
    respondent_award: float,
    rationale: str
):
    """Arbitrate dispute"""
    result = await arbitrate_dispute(dispute_id, ruling, claimant_award, respondent_award, rationale)
    return result

@app.get("/disputes/{dispute_id}")
async def dispute_get(dispute_id: str):
    return get_dispute(dispute_id)

@app.get("/disputes/list")
async def dispute_list(username: str = None, status: str = None):
    return list_disputes(username, status)

@app.get("/disputes/stats")
async def dispute_stats():
    return get_dispute_stats()
    
from bundle_engine import (
    create_bundle,
    record_bundle_sale,
    assign_bundle_roles,
    update_bundle_status,
    get_bundle,
    list_bundles,
    get_bundle_performance_stats
)

@app.post("/bundles/create")
async def bundle_create(
    lead_agent: str,
    agents: List[str],
    title: str,
    description: str,
    services: List[Dict[str, Any]],
    pricing: Dict[str, Any]
):
    """Create multi-agent bundle"""
    result = await create_bundle(
        lead_agent=lead_agent,
        agents=agents,
        title=title,
        description=description,
        services=services,
        pricing=pricing
    )
    return result

@app.post("/bundles/sale")
async def bundle_sale(
    bundle_id: str,
    buyer: str,
    amount_usd: float,
    delivery_hours: int = None,
    satisfaction_score: float = None
):
    """Record bundle sale"""
    result = await record_bundle_sale(
        bundle_id=bundle_id,
        buyer=buyer,
        amount_usd=amount_usd,
        delivery_hours=delivery_hours,
        satisfaction_score=satisfaction_score
    )
    return result

@app.post("/bundles/roles")
async def bundle_roles(
    bundle_id: str,
    role_assignments: Dict[str, str]
):
    """Assign roles to agents"""
    result = await assign_bundle_roles(
        bundle_id=bundle_id,
        role_assignments=role_assignments
    )
    return result

@app.post("/bundles/status")
async def bundle_status(
    bundle_id: str,
    status: str,
    reason: str = ""
):
    """Update bundle status"""
    result = update_bundle_status(
        bundle_id=bundle_id,
        status=status,
        reason=reason
    )
    return result

@app.get("/bundles/{bundle_id}")
async def bundle_get(bundle_id: str):
    return get_bundle(bundle_id)

@app.get("/bundles/list")
async def bundle_list(
    agent: str = None,
    status: str = None,
    sort_by: str = "performance"
):
    return list_bundles(agent=agent, status=status, sort_by=sort_by)

@app.get("/bundles/stats/{bundle_id}")
async def bundle_stats(bundle_id: str):
    return get_bundle_performance_stats(bundle_id)
@_expansion_router.post("/ltv/predict")
async def _exp_ltv_predict(payload: dict):
    try:
        from ltv_forecaster import predict
        return {"ok": True, "ltv": float(predict(payload.get("user") or {}, payload.get("channel") or "tiktok"))}
    except Exception as e:
        return {"ok": False, "error": str(e)}

from metahive_rewards import (
    join_hive as join_hive_rewards,
    leave_hive,
    record_contribution,
    record_hive_revenue,
    distribute_hive_rewards,
    get_hive_member,
    list_hive_members,
    get_hive_treasury_stats,
    get_member_projected_earnings
)

@app.post("/hive/join")
async def hive_join(username: str, opt_in_data_sharing: bool = True):
    """Join MetaHive"""
    result = await join_hive_rewards(username, opt_in_data_sharing)
    return result

@app.post("/hive/leave")
async def hive_leave(username: str):
    """Leave MetaHive"""
    result = leave_hive(username)
    return result

@app.post("/hive/contribution")
async def hive_contribution(
    username: str,
    contribution_type: str,
    value: float = 1.0
):
    """Record contribution"""
    result = record_contribution(username, contribution_type, value)
    return result

@app.post("/hive/revenue")
async def hive_revenue(
    source: str,
    amount_usd: float,
    metadata: Dict[str, Any] = None
):
    """Record hive revenue"""
    result = await record_hive_revenue(source, amount_usd, metadata)
    return result

@app.post("/hive/distribute")
async def hive_distribute():
    """Distribute rewards"""
    result = await distribute_hive_rewards()
    return result

@app.get("/hive/member/{username}")
async def hive_member(username: str):
    return get_hive_member(username)

@app.get("/hive/members")
async def hive_members(status: str = None):
    return list_hive_members(status)

@app.get("/hive/treasury")
async def hive_treasury():
    return get_hive_treasury_stats()

@app.get("/hive/projected/{username}")
async def hive_projected(username: str):
    return get_member_projected_earnings(username)
@_expansion_router.post("/proposal/nudge")
async def _exp_proposal_nudge(payload: dict):
    try:
        from proposal_autoclose import nudge
        return nudge(payload.get("proposal_id") or payload.get("id"))
    except Exception as e:
        return {"ok": False, "error": str(e)}

@_expansion_router.post("/proposal/convert")
async def _exp_proposal_convert(payload: dict):
    try:
        from proposal_autoclose import convert_to_quickpay
        return convert_to_quickpay(payload.get("proposal_id") or payload.get("id"))
    except Exception as e:
        return {"ok": False, "error": str(e)}

@_expansion_router.post("/metabridge/dealgraph/create")
async def _exp_dg_create(payload: dict):
    try:
        from metabridge_dealgraph import create_dealgraph
        return {"ok": True, "graph": create_dealgraph(payload.get("opportunity") or {}, payload.get("roles") or payload.get("roles_needed") or [], payload.get("rev_split") or [])}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@_expansion_router.post("/metabridge/dealgraph/activate")
async def _exp_dg_activate(payload: dict):
    try:
        from metabridge_dealgraph import activate
        return {"ok": True, "result": activate(payload.get("graph_id") or payload.get("id"))}
    except Exception as e:
        return {"ok": False, "error": str(e)}

try:
    app.include_router(_expansion_router)
except Exception:
    pass
