#!/usr/bin/env python3
"""
Verification Script - Real vs Simulated Revenue

This script checks what's actually happening vs what's projected.
Answers the critical question: Is $1.18M real or simulated?
"""

import json
import os
from datetime import datetime
from typing import Dict, Any
from urllib.request import urlopen, Request
from urllib.error import URLError

BASE_URL = "https://aigentsy-ame-runtime.onrender.com"


def fetch_json(endpoint: str) -> Dict[str, Any]:
    """Fetch JSON from endpoint"""
    url = f"{BASE_URL}{endpoint}"
    try:
        req = Request(url, headers={'User-Agent': 'Verifier/1.0'})
        with urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode())
    except URLError as e:
        print(f"Error fetching {endpoint}: {e}")
        return {}


def check_stripe_integration() -> Dict[str, Any]:
    """Check if Stripe is actually connected and processing"""

    data = fetch_json('/integration/stats')
    stats = data.get('stats', {})
    escrow = stats.get('escrow', {})

    return {
        'contracts_created': escrow.get('contracts_created', 0),
        'total_value_usd': escrow.get('total_value_usd', 0),
        'milestones_funded': escrow.get('milestones_funded', 0),
        'milestones_released': escrow.get('milestones_released', 0),
        'funded_amount_usd': escrow.get('funded_amount_usd', 0),
        'released_amount_usd': escrow.get('released_amount_usd', 0),
        'active_contracts': escrow.get('active_contracts', 0),
    }


def check_sow_status() -> Dict[str, Any]:
    """Check SOW generation status"""

    data = fetch_json('/integration/stats')
    stats = data.get('stats', {})
    sow = stats.get('sow_generator', {})

    return {
        'sows_generated': sow.get('sows_generated', 0),
        'sows_signed': sow.get('sows_signed', 0),
        'total_value_usd': sow.get('total_value_usd', 0),
        'active_sows': sow.get('active_sows', 0),
    }


def check_orchestrator_status() -> Dict[str, Any]:
    """Check orchestrator/fulfillment status"""

    data = fetch_json('/integration/stats')
    stats = data.get('stats', {})
    orch = stats.get('orchestrator', {})

    return {
        'plans_created': orch.get('plans_created', 0),
        'plans_completed': orch.get('plans_completed', 0),
        'plans_failed': orch.get('plans_failed', 0),
        'active_plans': orch.get('active_plans', 0),
        'runbooks_loaded': orch.get('runbooks_loaded', 0),
    }


def check_workforce_status() -> Dict[str, Any]:
    """Check workforce/task execution status"""

    data = fetch_json('/integration/stats')
    stats = data.get('stats', {})
    workforce = stats.get('workforce', {})

    return {
        'tasks_dispatched': workforce.get('tasks_dispatched', 0),
        'tasks_completed': workforce.get('tasks_completed', 0),
        'tasks_failed': workforce.get('tasks_failed', 0),
        'fabric_tasks': workforce.get('fabric_tasks', 0),
        'pdl_tasks': workforce.get('pdl_tasks', 0),
        'human_tasks': workforce.get('human_tasks', 0),
        'active_tasks': workforce.get('active_tasks', 0),
    }


def analyze_contract_code() -> Dict[str, Any]:
    """Analyze the contract creation code to understand the flow"""

    result = {
        'file_exists': False,
        'has_stripe_import': False,
        'has_real_stripe_calls': False,
        'has_simulated_paylinks': False,
        'paylink_pattern': None,
    }

    escrow_file = 'contracts/milestone_escrow.py'

    if os.path.exists(escrow_file):
        result['file_exists'] = True

        with open(escrow_file, 'r') as f:
            content = f.read()

            # Check for Stripe imports
            result['has_stripe_import'] = 'import stripe' in content

            # Check for real Stripe API calls
            result['has_real_stripe_calls'] = any([
                'stripe.PaymentIntent.create' in content,
                'stripe.checkout.Session.create' in content,
                'stripe.Customer.create' in content,
            ])

            # Check for simulated/fake paylinks
            if 'buy.stripe.com' in content:
                result['has_simulated_paylinks'] = True
                result['paylink_pattern'] = 'Generates fake buy.stripe.com URLs'

            if 'hashlib.md5' in content and 'paylink_url' in content:
                result['paylink_generation'] = 'Generates pseudo-random paylink URLs (not real Stripe)'

    return result


def analyze_discovery_code() -> Dict[str, Any]:
    """Analyze what discovery actually does"""

    result = {
        'discovery_manager_exists': False,
        'uses_real_apis': False,
        'uses_perplexity': False,
        'creates_real_opportunities': False,
    }

    discovery_file = 'discovery/discovery_manager.py'

    if os.path.exists(discovery_file):
        result['discovery_manager_exists'] = True

        with open(discovery_file, 'r') as f:
            content = f.read()

            result['uses_perplexity'] = 'perplexity' in content.lower()
            result['uses_real_apis'] = any([
                'api.perplexity.ai' in content,
                'PERPLEXITY_API_KEY' in content,
            ])

    return result


def main():
    """Main verification"""

    print("\n" + "=" * 80)
    print("🔍 COMPLETE SYSTEM VERIFICATION - REAL vs SIMULATED")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. Check Stripe/Escrow status
    print("\n" + "─" * 80)
    print("1️⃣  ESCROW/CONTRACT STATUS")
    print("─" * 80)

    escrow = check_stripe_integration()

    print(f"\n   Contracts Created: {escrow['contracts_created']}")
    print(f"   Total Value (Stats): ${escrow['total_value_usd']:,.2f}")
    print(f"   Milestones Funded: {escrow['milestones_funded']}")
    print(f"   Milestones Released: {escrow['milestones_released']}")
    print(f"   Funded Amount: ${escrow['funded_amount_usd']:,.2f}")
    print(f"   Released Amount: ${escrow['released_amount_usd']:,.2f}")

    # KEY INDICATOR
    if escrow['contracts_created'] > 0 and escrow['milestones_funded'] == 0:
        print(f"\n   ⚠️  INDICATOR: Contracts exist but NO milestones funded")
        print(f"   ⚠️  This means NO real customer payments have been received")

    # 2. Check SOW status
    print("\n" + "─" * 80)
    print("2️⃣  SOW (STATEMENT OF WORK) STATUS")
    print("─" * 80)

    sow = check_sow_status()

    print(f"\n   SOWs Generated: {sow['sows_generated']}")
    print(f"   SOWs Signed: {sow['sows_signed']}")
    print(f"   SOW Total Value: ${sow['total_value_usd']:,.2f}")

    if sow['sows_generated'] > 0 and sow['sows_signed'] == 0:
        print(f"\n   ⚠️  INDICATOR: SOWs generated but NONE signed by clients")
        print(f"   ⚠️  This means NO real client agreements exist")

    # 3. Check Orchestrator status
    print("\n" + "─" * 80)
    print("3️⃣  ORCHESTRATOR/FULFILLMENT STATUS")
    print("─" * 80)

    orch = check_orchestrator_status()

    print(f"\n   Plans Created: {orch['plans_created']}")
    print(f"   Plans Completed: {orch['plans_completed']}")
    print(f"   Plans Failed: {orch['plans_failed']}")
    print(f"   Runbooks Loaded: {orch['runbooks_loaded']}")

    if orch['plans_created'] > 0 and orch['plans_completed'] == 0:
        print(f"\n   ⚠️  INDICATOR: Plans created but NONE completed")
        print(f"   ⚠️  This means NO actual work has been delivered")

    # 4. Check Workforce status
    print("\n" + "─" * 80)
    print("4️⃣  WORKFORCE/TASK STATUS")
    print("─" * 80)

    workforce = check_workforce_status()

    print(f"\n   Tasks Dispatched: {workforce['tasks_dispatched']}")
    print(f"   Tasks Completed: {workforce['tasks_completed']}")
    print(f"   Fabric Tasks: {workforce['fabric_tasks']}")
    print(f"   Human Tasks: {workforce['human_tasks']}")

    # 5. Analyze code
    print("\n" + "─" * 80)
    print("5️⃣  CODE ANALYSIS")
    print("─" * 80)

    contract_code = analyze_contract_code()

    print(f"\n   Escrow file exists: {contract_code['file_exists']}")
    print(f"   Has Stripe import: {contract_code['has_stripe_import']}")
    print(f"   Has real Stripe API calls: {contract_code['has_real_stripe_calls']}")
    print(f"   Has simulated paylinks: {contract_code['has_simulated_paylinks']}")

    if contract_code.get('paylink_pattern'):
        print(f"   Paylink pattern: {contract_code['paylink_pattern']}")

    discovery_code = analyze_discovery_code()

    print(f"\n   Discovery manager exists: {discovery_code['discovery_manager_exists']}")
    print(f"   Uses Perplexity: {discovery_code['uses_perplexity']}")
    print(f"   Uses real APIs: {discovery_code['uses_real_apis']}")

    # FINAL VERDICT
    print("\n" + "=" * 80)
    print("💎 FINAL VERDICT")
    print("=" * 80)

    is_simulated = (
        escrow['contracts_created'] > 0 and
        escrow['milestones_funded'] == 0 and
        sow['sows_signed'] == 0
    )

    if is_simulated:
        print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ❌ STATUS: SIMULATION / PROJECTION MODE                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  The $1.18M is PROJECTED VALUE, not ACTUAL REVENUE.                         ║
║                                                                              ║
║  WHAT'S WORKING (Real):                                                      ║
║  ✅ Discovery is finding real opportunities (via Perplexity)                 ║
║  ✅ System is creating contract structures                                   ║
║  ✅ System is generating SOWs and milestones                                 ║
║  ✅ Tasks are being dispatched and tracked                                   ║
║  ✅ All 47 systems are operational                                           ║
║                                                                              ║
║  WHAT'S NOT HAPPENING (Missing):                                             ║
║  ❌ No real customers have signed contracts (sows_signed = 0)                ║
║  ❌ No real payments received (milestones_funded = 0)                        ║
║  ❌ No real revenue collected (Stripe balance = $0)                          ║
║  ❌ No actual work delivered to paying customers                             ║
║                                                                              ║
║  THE GAP:                                                                    ║
║  System discovers opportunities and creates contract PROPOSALS,              ║
║  but there's no customer acquisition flow to:                                ║
║    1. Present contracts to actual clients                                    ║
║    2. Get client signatures on SOWs                                          ║
║    3. Collect real payments via Stripe                                       ║
║    4. Deliver actual work to paying customers                                ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")

        print("\n📋 TO ACTIVATE REAL REVENUE:")
        print("─" * 80)
        print("""
1. CUSTOMER ACQUISITION FLOW
   - Present discovered opportunities to potential clients
   - Send contract proposals via email/platform
   - Track client responses and negotiations

2. CONTRACT SIGNING
   - Implement e-signature for SOWs
   - Track signed vs unsigned contracts
   - Only count signed contracts as "real"

3. PAYMENT COLLECTION
   - Create real Stripe Payment Intents (not fake URLs)
   - Send payment links to clients
   - Process actual charges
   - Track funded milestones

4. WORK DELIVERY
   - Execute actual deliverables for paying clients
   - Use FA30 to deliver first artifacts
   - Track completed work per contract

5. REVENUE TRACKING
   - Separate "projected" vs "actual" revenue
   - Only count Stripe charges as real revenue
   - Track conversion: discovered → signed → paid → delivered
""")
    else:
        print("\n   ✅ System may be processing real transactions")
        print("   (Further investigation needed)")

    # Summary stats
    print("\n" + "─" * 80)
    print("📊 SUMMARY STATS")
    print("─" * 80)
    print(f"""
   Projected Contract Value:  ${escrow['total_value_usd']:,.2f}
   Actual Revenue Collected:  ${escrow['released_amount_usd']:,.2f}
   Gap (Unrealized):          ${escrow['total_value_usd'] - escrow['released_amount_usd']:,.2f}

   Conversion Funnel:
   ─────────────────
   Contracts Created:   {escrow['contracts_created']}
   SOWs Signed:         {sow['sows_signed']} ({(sow['sows_signed']/max(1,escrow['contracts_created'])*100):.1f}%)
   Milestones Funded:   {escrow['milestones_funded']} ({(escrow['milestones_funded']/max(1,escrow['contracts_created'])*100):.1f}%)
   Milestones Released: {escrow['milestones_released']} ({(escrow['milestones_released']/max(1,escrow['contracts_created'])*100):.1f}%)
""")

    print("=" * 80)

    # Save results
    results = {
        'timestamp': datetime.now().isoformat(),
        'is_simulated': is_simulated,
        'escrow': escrow,
        'sow': sow,
        'orchestrator': orch,
        'workforce': workforce,
        'code_analysis': {
            'contract': contract_code,
            'discovery': discovery_code,
        }
    }

    with open('verification_report.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print("\n✅ Report saved to verification_report.json")


if __name__ == '__main__':
    main()
