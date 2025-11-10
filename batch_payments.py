"""
AiGentsy Batch Payment Processing
Pay multiple agents at once with bulk invoice generation
"""
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import asyncio

def _now():
    return datetime.now(timezone.utc).isoformat()


async def create_batch_payment(
    payments: List[Dict[str, Any]],
    batch_id: str = None,
    description: str = ""
) -> Dict[str, Any]:
    """
    Create a batch payment for multiple agents
    
    payments format:
    [
        {"username": "agent1", "amount": 100, "currency": "USD", "reason": "job_123"},
        {"username": "agent2", "amount": 50, "currency": "EUR", "reason": "job_456"}
    ]
    """
    from uuid import uuid4
    
    if not batch_id:
        batch_id = f"batch_{uuid4().hex[:12]}"
    
    batch = {
        "id": batch_id,
        "status": "pending",
        "description": description,
        "created_at": _now(),
        "payments": payments,
        "total_payments": len(payments),
        "successful": 0,
        "failed": 0,
        "total_amount": sum([float(p.get("amount", 0)) for p in payments]),
        "results": []
    }
    
    return batch


async def execute_batch_payment(
    batch: Dict[str, Any],
    users: List[Dict[str, Any]],
    credit_function
) -> Dict[str, Any]:
    """
    Execute a batch payment - credit all agents
    """
    results = []
    successful = 0
    failed = 0
    
    for payment in batch["payments"]:
        username = payment.get("username")
        amount = float(payment.get("amount", 0))
        currency = payment.get("currency", "USD")
        reason = payment.get("reason", "batch_payment")
        
        # Find user
        user = None
        for u in users:
            if u.get("username") == username or u.get("consent", {}).get("username") == username:
                user = u
                break
        
        if not user:
            results.append({
                "username": username,
                "status": "failed",
                "error": "user_not_found",
                "amount": amount,
                "currency": currency
            })
            failed += 1
            continue
        
        # Credit user
        try:
            credit_result = credit_function(user, amount, currency, reason)
            
            if credit_result.get("ok"):
                results.append({
                    "username": username,
                    "status": "success",
                    "amount": amount,
                    "currency": currency,
                    "new_balance": credit_result.get("new_balance")
                })
                successful += 1
            else:
                results.append({
                    "username": username,
                    "status": "failed",
                    "error": credit_result.get("error"),
                    "amount": amount,
                    "currency": currency
                })
                failed += 1
        
        except Exception as e:
            results.append({
                "username": username,
                "status": "failed",
                "error": str(e),
                "amount": amount,
                "currency": currency
            })
            failed += 1
    
    batch["status"] = "completed"
    batch["completed_at"] = _now()
    batch["successful"] = successful
    batch["failed"] = failed
    batch["results"] = results
    
    return batch


async def generate_bulk_invoices(
    intents: List[Dict[str, Any]],
    batch_id: str = None
) -> Dict[str, Any]:
    """
    Generate invoices for multiple completed intents
    """
    from uuid import uuid4
    
    if not batch_id:
        batch_id = f"inv_batch_{uuid4().hex[:12]}"
    
    invoices = []
    total_amount = 0.0
    
    for intent in intents:
        agent = intent.get("agent")
        price = float(intent.get("price_usd", 0))
        intent_id = intent.get("id")
        
        if not all([agent, price, intent_id]):
            continue
        
        invoice = {
            "id": f"inv_{uuid4().hex[:8]}",
            "agent": agent,
            "intent_id": intent_id,
            "amount": price,
            "currency": "USD",
            "status": "generated",
            "batch_id": batch_id,
            "generated_at": _now()
        }
        
        invoices.append(invoice)
        total_amount += price
    
    return {
        "ok": True,
        "batch_id": batch_id,
        "total_invoices": len(invoices),
        "total_amount": total_amount,
        "invoices": invoices,
        "generated_at": _now()
    }


async def batch_revenue_recognition(
    invoices: List[Dict[str, Any]],
    users: List[Dict[str, Any]],
    platform_fee_rate: float = 0.05
) -> Dict[str, Any]:
    """
    Process revenue recognition for multiple invoices
    """
    results = []
    total_revenue = 0.0
    total_fees = 0.0
    total_net = 0.0
    
    for invoice in invoices:
        agent_username = invoice.get("agent")
        amount = float(invoice.get("amount", 0))
        currency = invoice.get("currency", "USD")
        
        # Find agent
        agent_user = None
        for u in users:
            if u.get("username") == agent_username or u.get("consent", {}).get("username") == agent_username:
                agent_user = u
                break
        
        if not agent_user:
            results.append({
                "invoice_id": invoice.get("id"),
                "agent": agent_username,
                "status": "failed",
                "error": "agent_not_found"
            })
            continue
        
        # Calculate fees
        fee_amount = round(amount * platform_fee_rate, 2)
        net_amount = round(amount - fee_amount, 2)
        
        # Update agent balances
        agent_user.setdefault("ownership", {})
        agent_user["ownership"]["aigx"] = float(agent_user["ownership"].get("aigx", 0)) + net_amount
        
        # Add ledger entries
        agent_user["ownership"].setdefault("ledger", []).append({
            "ts": _now(),
            "amount": amount,
            "currency": currency,
            "basis": "revenue",
            "ref": invoice.get("id")
        })
        
        agent_user["ownership"]["ledger"].append({
            "ts": _now(),
            "amount": -fee_amount,
            "currency": currency,
            "basis": "platform_fee",
            "ref": invoice.get("id")
        })
        
        # Update invoice status
        invoice["status"] = "paid"
        invoice["paid_at"] = _now()
        
        results.append({
            "invoice_id": invoice.get("id"),
            "agent": agent_username,
            "status": "success",
            "amount": amount,
            "fee": fee_amount,
            "net": net_amount
        })
        
        total_revenue += amount
        total_fees += fee_amount
        total_net += net_amount
    
    return {
        "ok": True,
        "total_invoices": len(invoices),
        "successful": len([r for r in results if r["status"] == "success"]),
        "failed": len([r for r in results if r["status"] == "failed"]),
        "total_revenue": round(total_revenue, 2),
        "total_fees": round(total_fees, 2),
        "total_net": round(total_net, 2),
        "results": results,
        "processed_at": _now()
    }


async def schedule_recurring_payment(
    payment_template: Dict[str, Any],
    schedule: str = "monthly",
    start_date: str = None
) -> Dict[str, Any]:
    """
    Schedule recurring payment (monthly agent stipends, etc.)
    
    schedule options: daily, weekly, monthly
    """
    from uuid import uuid4
    
    recurring_id = f"recurring_{uuid4().hex[:12]}"
    
    if not start_date:
        start_date = _now()
    
    recurring_payment = {
        "id": recurring_id,
        "template": payment_template,
        "schedule": schedule,
        "start_date": start_date,
        "status": "active",
        "next_run": start_date,
        "total_runs": 0,
        "created_at": _now()
    }
    
    return {
        "ok": True,
        "recurring_payment": recurring_payment
    }


def generate_payment_report(
    batch: Dict[str, Any],
    format: str = "summary"
) -> Dict[str, Any]:
    """
    Generate payment report from batch
    
    format: summary | detailed | csv
    """
    if format == "summary":
        return {
            "batch_id": batch.get("id"),
            "total_payments": batch.get("total_payments"),
            "successful": batch.get("successful"),
            "failed": batch.get("failed"),
            "total_amount": batch.get("total_amount"),
            "status": batch.get("status"),
            "completed_at": batch.get("completed_at")
        }
    
    if format == "detailed":
        return batch
    
    if format == "csv":
        # Generate CSV data
        csv_rows = []
        csv_rows.append(["Username", "Amount", "Currency", "Status", "Error"])
        
        for result in batch.get("results", []):
            csv_rows.append([
                result.get("username"),
                result.get("amount"),
                result.get("currency"),
                result.get("status"),
                result.get("error", "")
            ])
        
        return {
            "batch_id": batch.get("id"),
            "format": "csv",
            "rows": csv_rows
        }
    
    return {"error": "invalid_format"}


async def retry_failed_payments(
    batch: Dict[str, Any],
    users: List[Dict[str, Any]],
    credit_function
) -> Dict[str, Any]:
    """
    Retry all failed payments from a batch
    """
    failed_payments = [
        r for r in batch.get("results", [])
        if r.get("status") == "failed"
    ]
    
    if not failed_payments:
        return {
            "ok": True,
            "message": "no_failed_payments_to_retry"
        }
    
    # Create retry batch
    retry_payments = [
        {
            "username": p.get("username"),
            "amount": p.get("amount"),
            "currency": p.get("currency"),
            "reason": "retry_" + batch.get("id")
        }
        for p in failed_payments
    ]
    
    retry_batch = await create_batch_payment(
        payments=retry_payments,
        batch_id=f"retry_{batch.get('id')}",
        description=f"Retry of failed payments from {batch.get('id')}"
    )
    
    # Execute retry
    result = await execute_batch_payment(retry_batch, users, credit_function)
    
    return result
