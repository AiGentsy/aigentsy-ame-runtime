"""
AiGentsy Multi-Currency Engine
Support for AIGx, USD, EUR, GBP + conversion
"""
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import httpx

def _now():
    return datetime.now(timezone.utc).isoformat()


# Supported currencies
SUPPORTED_CURRENCIES = ["USD", "EUR", "GBP", "AIGx", "CREDITS"]

# AIGx exchange rates (1 AIGx = X currency)
AIGX_RATES = {
    "USD": 1.0,      # 1 AIGx = $1 USD
    "EUR": 0.92,     # 1 AIGx = €0.92
    "GBP": 0.79,     # 1 AIGx = £0.79
    "AIGx": 1.0,     # 1 AIGx = 1 AIGx
    "CREDITS": 100   # 1 AIGx = 100 credits
}

# Fiat exchange rates (updated periodically)
FIAT_RATES = {
    "USD": {"EUR": 0.92, "GBP": 0.79},
    "EUR": {"USD": 1.09, "GBP": 0.86},
    "GBP": {"USD": 1.27, "EUR": 1.16}
}


async def fetch_live_rates() -> Dict[str, Dict[str, float]]:
    """
    Fetch live exchange rates from external API
    Falls back to static rates if API fails
    """
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            # Using exchangerate-api.com (free tier)
            response = await client.get(
                "https://api.exchangerate-api.com/v4/latest/USD"
            )
            
            if response.status_code == 200:
                data = response.json()
                rates = data.get("rates", {})
                
                return {
                    "USD": {
                        "EUR": rates.get("EUR", 0.92),
                        "GBP": rates.get("GBP", 0.79)
                    },
                    "timestamp": data.get("date", _now())
                }
    
    except Exception as e:
        print(f"⚠️ Live rates fetch failed: {e}")
    
    # Fallback to static rates
    return FIAT_RATES


def convert_currency(
    amount: float,
    from_currency: str,
    to_currency: str,
    rates: Dict[str, Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Convert amount from one currency to another
    """
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()
    
    # Same currency - no conversion
    if from_currency == to_currency:
        return {
            "ok": True,
            "from_amount": amount,
            "from_currency": from_currency,
            "to_amount": amount,
            "to_currency": to_currency,
            "rate": 1.0
        }
    
    # Validate currencies
    if from_currency not in SUPPORTED_CURRENCIES:
        return {
            "ok": False,
            "error": "unsupported_from_currency",
            "supported": SUPPORTED_CURRENCIES
        }
    
    if to_currency not in SUPPORTED_CURRENCIES:
        return {
            "ok": False,
            "error": "unsupported_to_currency",
            "supported": SUPPORTED_CURRENCIES
        }
    
    # Use provided rates or fallback to static
    if not rates:
        rates = FIAT_RATES
    
    # AIGx conversions
    if from_currency == "AIGx":
        rate = AIGX_RATES.get(to_currency, 1.0)
        to_amount = round(amount * rate, 2)
        
        return {
            "ok": True,
            "from_amount": amount,
            "from_currency": from_currency,
            "to_amount": to_amount,
            "to_currency": to_currency,
            "rate": rate
        }
    
    if to_currency == "AIGx":
        rate = 1.0 / AIGX_RATES.get(from_currency, 1.0)
        to_amount = round(amount * rate, 2)
        
        return {
            "ok": True,
            "from_amount": amount,
            "from_currency": from_currency,
            "to_amount": to_amount,
            "to_currency": to_currency,
            "rate": rate
        }
    
    # Fiat to fiat conversions
    if from_currency in rates and to_currency in rates[from_currency]:
        rate = rates[from_currency][to_currency]
        to_amount = round(amount * rate, 2)
        
        return {
            "ok": True,
            "from_amount": amount,
            "from_currency": from_currency,
            "to_amount": to_amount,
            "to_currency": to_currency,
            "rate": rate
        }
    
    # Inverse conversion
    if to_currency in rates and from_currency in rates[to_currency]:
        rate = 1.0 / rates[to_currency][from_currency]
        to_amount = round(amount * rate, 2)
        
        return {
            "ok": True,
            "from_amount": amount,
            "from_currency": from_currency,
            "to_amount": to_amount,
            "to_currency": to_currency,
            "rate": rate
        }
    
    return {
        "ok": False,
        "error": "conversion_not_available",
        "from_currency": from_currency,
        "to_currency": to_currency
    }


def get_user_balance(
    user: Dict[str, Any],
    currency: str = "USD"
) -> Dict[str, Any]:
    """
    Get user's balance in specified currency
    """
    ownership = user.get("ownership", {})
    
    # Get all currency balances
    balances = {
        "AIGx": float(ownership.get("aigx", 0)),
        "USD": float(ownership.get("usd", 0)),
        "EUR": float(ownership.get("eur", 0)),
        "GBP": float(ownership.get("gbp", 0)),
        "CREDITS": float(ownership.get("credits", 0))
    }
    
    # Convert to requested currency
    total_in_currency = 0.0
    conversions = []
    
    for curr, balance in balances.items():
        if balance > 0:
            conversion = convert_currency(balance, curr, currency)
            
            if conversion["ok"]:
                total_in_currency += conversion["to_amount"]
                conversions.append({
                    "from": f"{balance} {curr}",
                    "to": f"{conversion['to_amount']} {currency}",
                    "rate": conversion["rate"]
                })
    
    return {
        "ok": True,
        "currency": currency,
        "total": round(total_in_currency, 2),
        "balances": balances,
        "conversions": conversions
    }


def credit_currency(
    user: Dict[str, Any],
    amount: float,
    currency: str,
    reason: str = "payment"
) -> Dict[str, Any]:
    """
    Credit user's account in specified currency
    """
    currency = currency.upper()
    
    if currency not in SUPPORTED_CURRENCIES:
        return {
            "ok": False,
            "error": "unsupported_currency",
            "currency": currency
        }
    
    # Ensure ownership structure exists
    user.setdefault("ownership", {})
    
    # Get current balance
    currency_key = currency.lower() if currency != "AIGx" else "aigx"
    current = float(user["ownership"].get(currency_key, 0))
    
    # Credit account
    new_balance = current + amount
    user["ownership"][currency_key] = new_balance
    
    # Add ledger entry
    user["ownership"].setdefault("ledger", []).append({
        "ts": _now(),
        "amount": amount,
        "currency": currency,
        "basis": reason,
        "balance_after": new_balance
    })
    
    return {
        "ok": True,
        "amount": amount,
        "currency": currency,
        "previous_balance": current,
        "new_balance": new_balance
    }


def debit_currency(
    user: Dict[str, Any],
    amount: float,
    currency: str,
    reason: str = "payment"
) -> Dict[str, Any]:
    """
    Debit user's account in specified currency
    """
    currency = currency.upper()
    
    if currency not in SUPPORTED_CURRENCIES:
        return {
            "ok": False,
            "error": "unsupported_currency",
            "currency": currency
        }
    
    # Get current balance
    currency_key = currency.lower() if currency != "AIGx" else "aigx"
    current = float(user.get("ownership", {}).get(currency_key, 0))
    
    # Check sufficient funds
    if current < amount:
        return {
            "ok": False,
            "error": "insufficient_funds",
            "currency": currency,
            "available": current,
            "required": amount
        }
    
    # Debit account
    new_balance = current - amount
    user["ownership"][currency_key] = new_balance
    
    # Add ledger entry
    user["ownership"].setdefault("ledger", []).append({
        "ts": _now(),
        "amount": -amount,
        "currency": currency,
        "basis": reason,
        "balance_after": new_balance
    })
    
    return {
        "ok": True,
        "amount": amount,
        "currency": currency,
        "previous_balance": current,
        "new_balance": new_balance
    }


def transfer_with_conversion(
    from_user: Dict[str, Any],
    to_user: Dict[str, Any],
    amount: float,
    from_currency: str,
    to_currency: str,
    reason: str = "transfer"
) -> Dict[str, Any]:
    """
    Transfer funds between users with currency conversion
    """
    # Debit from sender
    debit_result = debit_currency(from_user, amount, from_currency, reason)
    
    if not debit_result["ok"]:
        return debit_result
    
    # Convert currency
    conversion = convert_currency(amount, from_currency, to_currency)
    
    if not conversion["ok"]:
        # Rollback debit
        credit_currency(from_user, amount, from_currency, "rollback")
        return conversion
    
    # Credit receiver
    credit_result = credit_currency(to_user, conversion["to_amount"], to_currency, reason)
    
    return {
        "ok": True,
        "from_user": from_user.get("username"),
        "to_user": to_user.get("username"),
        "from_amount": amount,
        "from_currency": from_currency,
        "to_amount": conversion["to_amount"],
        "to_currency": to_currency,
        "exchange_rate": conversion["rate"]
    }
