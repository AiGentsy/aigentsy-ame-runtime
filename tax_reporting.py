"""
AiGentsy Automated Tax Reporting
1099 generation, VAT compliance, quarterly reports
"""
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

def _now():
    return datetime.now(timezone.utc).isoformat()

def _year(ts_iso: str) -> int:
    try:
        return datetime.fromisoformat(ts_iso.replace("Z", "+00:00")).year
    except:
        return datetime.now(timezone.utc).year


# Tax thresholds
FORM_1099_THRESHOLD = 600.0  # $600 minimum for 1099-NEC
VAT_REGISTRATION_THRESHOLD = 85000.0  # UK VAT threshold (example)

# Tax rates by region
TAX_RATES = {
    "US": {
        "federal_rate": 0.15,  # Self-employment tax estimate
        "state_rate": 0.05     # Average state tax
    },
    "UK": {
        "vat_rate": 0.20,      # 20% VAT
        "income_tax": 0.20     # Basic rate
    },
    "EU": {
        "vat_rate": 0.21,      # Average EU VAT
        "income_tax": 0.25     # Average
    }
}


def calculate_annual_earnings(
    user: Dict[str, Any],
    year: int = None
) -> Dict[str, Any]:
    """
    Calculate agent's total earnings for a tax year
    """
    if not year:
        year = datetime.now(timezone.utc).year
    
    ledger = user.get("ownership", {}).get("ledger", [])
    
    gross_income = 0.0
    platform_fees = 0.0
    expenses = 0.0
    
    income_entries = []
    expense_entries = []
    
    for entry in ledger:
        entry_year = _year(entry.get("ts", ""))
        
        if entry_year != year:
            continue
        
        basis = entry.get("basis", "")
        amount = float(entry.get("amount", 0))
        
        # Income
        if basis == "revenue" and amount > 0:
            gross_income += amount
            income_entries.append({
                "date": entry.get("ts"),
                "amount": amount,
                "ref": entry.get("ref", "")
            })
        
        # Platform fees (deductible expense)
        if basis == "platform_fee":
            platform_fees += abs(amount)
            expense_entries.append({
                "date": entry.get("ts"),
                "amount": abs(amount),
                "type": "platform_fee",
                "ref": entry.get("ref", "")
            })
        
        # Insurance (deductible expense)
        if basis == "insurance_premium":
            expenses += abs(amount)
            expense_entries.append({
                "date": entry.get("ts"),
                "amount": abs(amount),
                "type": "insurance",
                "ref": entry.get("ref", "")
            })
        
        # Factoring fees (deductible expense)
        if basis == "factoring_fee":
            expenses += abs(amount)
            expense_entries.append({
                "date": entry.get("ts"),
                "amount": abs(amount),
                "type": "factoring_fee",
                "ref": entry.get("ref", "")
            })
    
    # Calculate net income
    total_expenses = platform_fees + expenses
    net_income = gross_income - total_expenses
    
    return {
        "year": year,
        "gross_income": round(gross_income, 2),
        "platform_fees": round(platform_fees, 2),
        "other_expenses": round(expenses, 2),
        "total_expenses": round(total_expenses, 2),
        "net_income": round(net_income, 2),
        "total_transactions": len(income_entries),
        "income_entries": income_entries,
        "expense_entries": expense_entries
    }


def generate_1099_nec(
    user: Dict[str, Any],
    year: int = None,
    payer_info: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Generate 1099-NEC form data for US agents
    """
    if not year:
        year = datetime.now(timezone.utc).year
    
    earnings = calculate_annual_earnings(user, year)
    gross_income = earnings["gross_income"]
    
    # Check threshold
    if gross_income < FORM_1099_THRESHOLD:
        return {
            "ok": False,
            "reason": "below_threshold",
            "threshold": FORM_1099_THRESHOLD,
            "gross_income": gross_income,
            "message": f"Gross income ${gross_income} is below $600 threshold"
        }
    
    # Default payer info
    if not payer_info:
        payer_info = {
            "name": "AiGentsy Inc.",
            "ein": "XX-XXXXXXX",  # Replace with actual EIN
            "address": "123 Platform St",
            "city": "San Francisco",
            "state": "CA",
            "zip": "94102"
        }
    
    # Get agent info
    username = user.get("consent", {}).get("username") or user.get("username")
    profile = user.get("profile", {})
    
    form_1099 = {
        "form_type": "1099-NEC",
        "tax_year": year,
        "payer": payer_info,
        "recipient": {
            "name": profile.get("name", username),
            "tin": profile.get("ssn") or profile.get("ein") or "XXXXX",  # Taxpayer ID
            "address": profile.get("address", ""),
            "city": profile.get("city", ""),
            "state": profile.get("state", ""),
            "zip": profile.get("zip", "")
        },
        "box_1_nonemployee_compensation": round(gross_income, 2),
        "federal_income_tax_withheld": 0.0,  # No withholding for 1099-NEC
        "state_income_tax_withheld": 0.0,
        "generated_at": _now(),
        "due_date": f"{year + 1}-01-31"  # 1099s due Jan 31
    }
    
    return {
        "ok": True,
        "form_1099_nec": form_1099,
        "earnings_summary": earnings
    }


def calculate_estimated_taxes(
    earnings: Dict[str, Any],
    region: str = "US"
) -> Dict[str, Any]:
    """
    Calculate estimated tax liability
    """
    net_income = earnings["net_income"]
    
    if region not in TAX_RATES:
        return {
            "ok": False,
            "error": "unsupported_region",
            "region": region
        }
    
    rates = TAX_RATES[region]
    
    # Calculate taxes
    federal_tax = net_income * rates.get("federal_rate", 0)
    state_tax = net_income * rates.get("state_rate", 0)
    total_tax = federal_tax + state_tax
    
    # Quarterly payments
    quarterly_payment = total_tax / 4
    
    return {
        "ok": True,
        "region": region,
        "net_income": net_income,
        "federal_tax": round(federal_tax, 2),
        "state_tax": round(state_tax, 2),
        "total_estimated_tax": round(total_tax, 2),
        "quarterly_payment": round(quarterly_payment, 2),
        "effective_rate": round((total_tax / net_income * 100), 2) if net_income > 0 else 0,
        "note": "This is an estimate. Consult a tax professional for accurate calculations."
    }


def generate_quarterly_report(
    user: Dict[str, Any],
    year: int,
    quarter: int
) -> Dict[str, Any]:
    """
    Generate quarterly tax report (Q1, Q2, Q3, Q4)
    """
    # Define quarter date ranges
    quarters = {
        1: (f"{year}-01-01", f"{year}-03-31"),
        2: (f"{year}-04-01", f"{year}-06-30"),
        3: (f"{year}-07-01", f"{year}-09-30"),
        4: (f"{year}-10-01", f"{year}-12-31")
    }
    
    if quarter not in quarters:
        return {"error": "invalid_quarter", "valid_quarters": [1, 2, 3, 4]}
    
    start_date, end_date = quarters[quarter]
    
    # Filter ledger entries for this quarter
    ledger = user.get("ownership", {}).get("ledger", [])
    
    gross_income = 0.0
    expenses = 0.0
    
    for entry in ledger:
        ts = entry.get("ts", "")
        
        if ts < start_date or ts > end_date:
            continue
        
        basis = entry.get("basis", "")
        amount = float(entry.get("amount", 0))
        
        if basis == "revenue" and amount > 0:
            gross_income += amount
        
        if basis in ["platform_fee", "insurance_premium", "factoring_fee"]:
            expenses += abs(amount)
    
    net_income = gross_income - expenses
    
    return {
        "year": year,
        "quarter": quarter,
        "period": f"{start_date} to {end_date}",
        "gross_income": round(gross_income, 2),
        "expenses": round(expenses, 2),
        "net_income": round(net_income, 2),
        "generated_at": _now()
    }


def calculate_vat_liability(
    user: Dict[str, Any],
    year: int,
    quarter: int = None
) -> Dict[str, Any]:
    """
    Calculate VAT liability for EU/UK agents
    """
    ledger = user.get("ownership", {}).get("ledger", [])
    
    # If quarter specified, filter
    if quarter:
        quarters = {
            1: (f"{year}-01-01", f"{year}-03-31"),
            2: (f"{year}-04-01", f"{year}-06-30"),
            3: (f"{year}-07-01", f"{year}-09-30"),
            4: (f"{year}-10-01", f"{year}-12-31")
        }
        start_date, end_date = quarters.get(quarter, (f"{year}-01-01", f"{year}-12-31"))
    else:
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
    
    vat_collected = 0.0  # VAT on sales
    vat_paid = 0.0       # VAT on purchases
    
    for entry in ledger:
        ts = entry.get("ts", "")
        
        if ts < start_date or ts > end_date:
            continue
        
        basis = entry.get("basis", "")
        amount = float(entry.get("amount", 0))
        currency = entry.get("currency", "USD")
        
        # Only process EUR/GBP transactions
        if currency not in ["EUR", "GBP"]:
            continue
        
        # VAT on revenue (output VAT)
        if basis == "revenue" and amount > 0:
            vat_rate = 0.20  # 20% standard rate
            vat_amount = amount * (vat_rate / (1 + vat_rate))
            vat_collected += vat_amount
        
        # VAT on expenses (input VAT - can be reclaimed)
        if basis in ["platform_fee", "insurance_premium"]:
            vat_rate = 0.20
            vat_amount = abs(amount) * (vat_rate / (1 + vat_rate))
            vat_paid += vat_amount
    
    # Net VAT owed (collected - paid)
    vat_owed = vat_collected - vat_paid
    
    return {
        "year": year,
        "quarter": quarter,
        "period": f"{start_date} to {end_date}",
        "vat_collected": round(vat_collected, 2),
        "vat_paid": round(vat_paid, 2),
        "net_vat_owed": round(vat_owed, 2),
        "currency": "EUR/GBP",
        "generated_at": _now()
    }


def generate_annual_tax_summary(
    user: Dict[str, Any],
    year: int = None
) -> Dict[str, Any]:
    """
    Comprehensive annual tax summary
    """
    if not year:
        year = datetime.now(timezone.utc).year
    
    earnings = calculate_annual_earnings(user, year)
    estimated_taxes = calculate_estimated_taxes(earnings, region="US")
    
    # Check 1099 eligibility
    requires_1099 = earnings["gross_income"] >= FORM_1099_THRESHOLD
    
    # Get quarterly breakdown
    quarters = []
    for q in [1, 2, 3, 4]:
        q_report = generate_quarterly_report(user, year, q)
        quarters.append(q_report)
    
    return {
        "year": year,
        "earnings": earnings,
        "estimated_taxes": estimated_taxes,
        "requires_1099": requires_1099,
        "quarterly_breakdown": quarters,
        "deduction_summary": {
            "platform_fees": earnings["platform_fees"],
            "other_expenses": earnings["other_expenses"],
            "total_deductions": earnings["total_expenses"]
        },
        "generated_at": _now()
    }


def batch_generate_1099s(
    users: List[Dict[str, Any]],
    year: int = None
) -> Dict[str, Any]:
    """
    Generate 1099s for all eligible agents
    """
    if not year:
        year = datetime.now(timezone.utc).year
    
    eligible_agents = []
    below_threshold = []
    
    for user in users:
        earnings = calculate_annual_earnings(user, year)
        
        if earnings["gross_income"] >= FORM_1099_THRESHOLD:
            form_1099 = generate_1099_nec(user, year)
            
            if form_1099.get("ok"):
                eligible_agents.append({
                    "username": user.get("username"),
                    "gross_income": earnings["gross_income"],
                    "form_1099": form_1099["form_1099_nec"]
                })
        else:
            below_threshold.append({
                "username": user.get("username"),
                "gross_income": earnings["gross_income"]
            })
    
    return {
        "ok": True,
        "year": year,
        "total_agents": len(users),
        "eligible_for_1099": len(eligible_agents),
        "below_threshold": len(below_threshold),
        "agents_with_1099": eligible_agents,
        "agents_below_threshold": below_threshold,
        "generated_at": _now()
    }


def export_tax_csv(
    user: Dict[str, Any],
    year: int = None
) -> Dict[str, Any]:
    """
    Export tax data as CSV for accountant
    """
    if not year:
        year = datetime.now(timezone.utc).year
    
    earnings = calculate_annual_earnings(user, year)
    
    # CSV format: Date, Type, Description, Amount, Category
    csv_rows = []
    csv_rows.append(["Date", "Type", "Description", "Amount", "Category"])
    
    # Income entries
    for entry in earnings["income_entries"]:
        csv_rows.append([
            entry["date"],
            "Income",
            f"Job: {entry['ref']}",
            entry["amount"],
            "Revenue"
        ])
    
    # Expense entries
    for entry in earnings["expense_entries"]:
        csv_rows.append([
            entry["date"],
            "Expense",
            entry["type"],
            entry["amount"],
            "Business Expense"
        ])
    
    return {
        "ok": True,
        "year": year,
        "format": "csv",
        "rows": csv_rows,
        "total_rows": len(csv_rows)
    }
