#!/usr/bin/env python3
"""
INTEGRATION SMOKE TEST
======================
End-to-end test of the monetization + brain overlay wiring.

Tests the full flywheel:
Discovery → Bidding → Execution → Reputation → Payments

Usage:
    python integration_smoke_test.py
    # or with backend:
    BACKEND=https://aigentsy-ame-runtime.onrender.com python integration_smoke_test.py
"""

import os
import sys
import json
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any

# Add current directory to path
sys.path.insert(0, '.')


def _now():
    return datetime.now(timezone.utc).isoformat() + "Z"


class IntegrationSmokeTest:
    """End-to-end integration smoke test"""

    def __init__(self):
        self.backend = os.getenv("BACKEND", "local")
        self.auth_token = os.getenv("AUTH_TOKEN", "test_token")
        self.results = []
        self.actor_id = f"smoke_test_{int(datetime.now().timestamp())}"
        self.run_id = f"run_{int(datetime.now().timestamp())}"

    def log(self, test_name: str, success: bool, details: Dict = None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "success": success,
            "details": details or {},
            "timestamp": _now()
        }
        self.results.append(result)
        print(f"\n{status}: {test_name}")
        if details:
            for k, v in details.items():
                print(f"   {k}: {v}")

    async def test_1_discovery_hook(self) -> bool:
        """Test discovery event emission"""
        print("\n" + "="*60)
        print("TEST 1: Discovery Hook")
        print("="*60)

        try:
            from integration_hooks import IntegrationHooks
            hooks = IntegrationHooks("smoke_test")

            opportunity = {
                "id": f"opp_{self.run_id}",
                "source": "github",
                "entity_id": self.actor_id,
                "estimated_value": 500,
                "title": "Smoke Test Opportunity"
            }

            result = hooks.on_discovery(
                opportunity,
                source="github",
                confidence=0.85,
                estimated_value=500
            )

            success = result.get("hooked") and result.get("brain_event")
            self.log("Discovery Hook", success, {
                "hooked": result.get("hooked"),
                "brain_event": result.get("brain_event"),
                "suggested_price": result.get("suggested_price"),
                "provider_ocs": result.get("provider_ocs")
            })
            return success

        except Exception as e:
            self.log("Discovery Hook", False, {"error": str(e)})
            return False

    async def test_2_fabric_quote(self) -> bool:
        """Test monetization fabric quote"""
        print("\n" + "="*60)
        print("TEST 2: Monetization Fabric Quote")
        print("="*60)

        try:
            from monetization import MonetizationFabric
            fabric = MonetizationFabric()

            # Test price_outcome
            base_price = 100.0
            suggested = fabric.price_outcome(
                base_price=base_price,
                load_pct=0.5,
                wave_score=0.3,
                cogs=10.0,
                min_margin=0.25
            )

            # Test revenue split
            splits = fabric.split_revenue(suggested)

            success = suggested > base_price and splits.get("platform", 0) > 0
            self.log("Fabric Quote", success, {
                "base_price": base_price,
                "suggested_price": suggested,
                "platform_fee": splits.get("platform"),
                "user_share": splits.get("user"),
                "pool_share": splits.get("pool")
            })
            return success

        except Exception as e:
            self.log("Fabric Quote", False, {"error": str(e)})
            return False

    async def test_3_bid_hooks(self) -> bool:
        """Test bidding hooks"""
        print("\n" + "="*60)
        print("TEST 3: Bidding Hooks")
        print("="*60)

        try:
            from integration_hooks import IntegrationHooks
            hooks = IntegrationHooks("smoke_test")

            bid = {
                "id": f"bid_{self.run_id}",
                "entity_id": self.actor_id,
                "amount": 450
            }

            # Test bid placed
            placed_result = hooks.on_bid_placed(
                bid,
                opportunity_id=f"opp_{self.run_id}",
                bid_amount=450
            )

            # Test bid won
            won_result = hooks.on_bid_won(
                bid,
                opportunity_id=f"opp_{self.run_id}",
                winning_amount=450,
                runner_up_amount=400
            )

            success = (
                placed_result.get("hooked") and
                won_result.get("hooked") and
                won_result.get("revenue_split")
            )

            self.log("Bidding Hooks", success, {
                "bid_placed_hooked": placed_result.get("hooked"),
                "bid_won_hooked": won_result.get("hooked"),
                "fees_calculated": placed_result.get("fees") is not None,
                "revenue_split": won_result.get("revenue_split") is not None
            })
            return success

        except Exception as e:
            self.log("Bidding Hooks", False, {"error": str(e)})
            return False

    async def test_4_execution_hooks(self) -> bool:
        """Test execution start/complete hooks"""
        print("\n" + "="*60)
        print("TEST 4: Execution Hooks")
        print("="*60)

        try:
            from integration_hooks import IntegrationHooks
            hooks = IntegrationHooks("smoke_test")

            coi = {
                "coi_id": f"coi_{self.run_id}",
                "entity_id": self.actor_id,
                "opportunity": {"id": f"opp_{self.run_id}", "platform": "github"}
            }

            # Test execution start
            start_result = hooks.on_execution_start(
                coi,
                connector="github",
                pdl_id="code_fix"
            )

            # Test execution complete with proofs
            proofs = [
                {"type": "commit", "url": f"https://github.com/test/commit/{self.run_id}"},
                {"type": "screenshot", "data": "base64..."}
            ]

            complete_result = hooks.on_execution_complete(
                coi,
                success=True,
                proofs=proofs,
                revenue=450,
                connector="github"
            )

            success = (
                start_result.get("hooked") and
                complete_result.get("hooked") and
                complete_result.get("ledger_posted")
            )

            self.log("Execution Hooks", success, {
                "start_hooked": start_result.get("hooked"),
                "connector_rec": start_result.get("connector_recommendation") is not None,
                "complete_hooked": complete_result.get("hooked"),
                "ocs_updated": complete_result.get("ocs_updated"),
                "new_ocs": complete_result.get("new_ocs"),
                "ledger_posted": complete_result.get("ledger_posted")
            })
            return success

        except Exception as e:
            self.log("Execution Hooks", False, {"error": str(e)})
            return False

    async def test_5_payment_hook(self) -> bool:
        """Test payment received hook"""
        print("\n" + "="*60)
        print("TEST 5: Payment Hook")
        print("="*60)

        try:
            from integration_hooks import IntegrationHooks
            hooks = IntegrationHooks("smoke_test")

            result = hooks.on_payment_received(
                amount=450,
                currency="USD",
                payer_id="test_client",
                ref_type="coi",
                ref_id=f"coi_{self.run_id}"
            )

            success = (
                result.get("hooked") and
                result.get("ledger_posted") and
                result.get("revenue_split")
            )

            splits = result.get("revenue_split", {})
            self.log("Payment Hook", success, {
                "hooked": result.get("hooked"),
                "ledger_posted": result.get("ledger_posted"),
                "platform_revenue": splits.get("platform"),
                "user_revenue": splits.get("user")
            })
            return success

        except Exception as e:
            self.log("Payment Hook", False, {"error": str(e)})
            return False

    async def test_6_reputation_ocs(self) -> bool:
        """Test reputation → OCS sync"""
        print("\n" + "="*60)
        print("TEST 6: Reputation → OCS Sync")
        print("="*60)

        try:
            from integration_hooks import IntegrationHooks
            hooks = IntegrationHooks("smoke_test")

            # Apply positive reputation delta
            result = hooks.on_reputation_change(
                self.actor_id,
                delta=15,
                reason="excellent_delivery",
                source_system="smoke_test"
            )

            # Get updated OCS
            ocs_data = hooks.get_entity_ocs(self.actor_id)

            success = result.get("hooked") and result.get("brain_event")

            self.log("Reputation → OCS", success, {
                "hooked": result.get("hooked"),
                "brain_event": result.get("brain_event"),
                "ocs_updated": result.get("ocs_updated"),
                "current_ocs": ocs_data.get("ocs"),
                "tier": ocs_data.get("tier")
            })
            return success

        except Exception as e:
            self.log("Reputation → OCS", False, {"error": str(e)})
            return False

    async def test_7_brain_events(self) -> bool:
        """Test brain event bus"""
        print("\n" + "="*60)
        print("TEST 7: Brain Event Bus")
        print("="*60)

        try:
            from brain_overlay import Brain
            brain = Brain()

            # Emit test event
            brain.emit("smoke_test", {
                "run_id": self.run_id,
                "actor_id": self.actor_id,
                "test": True
            })

            # Check event stats
            stats = brain.events.get_stats()

            success = stats.get("total_events", 0) > 0

            self.log("Brain Event Bus", success, {
                "total_events": stats.get("total_events"),
                "by_type": stats.get("by_type")
            })
            return success

        except Exception as e:
            self.log("Brain Event Bus", False, {"error": str(e)})
            return False

    async def test_8_policy_engine(self) -> bool:
        """Test policy engine suggestions"""
        print("\n" + "="*60)
        print("TEST 8: Policy Engine")
        print("="*60)

        try:
            from brain_overlay import Brain
            brain = Brain()

            # Get policy objects and call suggest
            pricing_policy = brain.policy("pricing.oaa")
            pricing_rec = pricing_policy.suggest({"base_price": 100})

            connector_policy = brain.policy("connector.ucb")
            connector_rec = connector_policy.suggest({"connector_id": "api"})

            success = pricing_rec is not None and connector_rec is not None

            self.log("Policy Engine", success, {
                "pricing_action": pricing_rec.get("action") if pricing_rec else None,
                "pricing_params": list(pricing_rec.get("params", {}).keys()) if pricing_rec else [],
                "connector_action": connector_rec.get("action") if connector_rec else None
            })
            return success

        except Exception as e:
            self.log("Policy Engine", False, {"error": str(e)})
            return False

    async def test_9_ledger_integrity(self) -> bool:
        """Test ledger posting"""
        print("\n" + "="*60)
        print("TEST 9: Ledger Integrity")
        print("="*60)

        try:
            from monetization.ledger import post_entry, get_ledger_summary

            # Post test entry - returns row dict directly
            row = post_entry(
                entry_type="smoke_test",
                ref=f"test:{self.run_id}",
                debit=100.0,
                credit=0,
                meta={"test": True}
            )

            # Get summary
            summary = get_ledger_summary()

            # Check row has expected fields
            success = (
                row is not None and
                row.get("type") == "smoke_test" and
                summary.get("entry_count", 0) > 0
            )

            self.log("Ledger Integrity", success, {
                "entry_posted": row is not None,
                "entry_type": row.get("type") if row else None,
                "entry_ref": row.get("ref") if row else None,
                "total_entries": summary.get("entry_count"),
                "total_debit": summary.get("total_debit")
            })
            return success

        except Exception as e:
            self.log("Ledger Integrity", False, {"error": str(e)})
            return False

    async def test_10_fee_schedule(self) -> bool:
        """Test centralized fee schedule"""
        print("\n" + "="*60)
        print("TEST 10: Centralized Fee Schedule")
        print("="*60)

        try:
            from monetization.fee_schedule import get_fee, calculate_platform_fee, get_schedule

            # Get various fees
            platform_pct = get_fee("base_platform_pct")
            insurance_pct = get_fee("insurance_origination_pct")
            referral_pct = get_fee("referral_default_pct")

            # Calculate platform fee
            fee_calc = calculate_platform_fee(1000)

            # Get full schedule
            schedule = get_schedule()

            success = (
                platform_pct is not None and
                fee_calc.get("total", 0) > 0 and
                len(schedule) > 10
            )

            self.log("Fee Schedule", success, {
                "platform_fee_pct": platform_pct,
                "insurance_pct": insurance_pct,
                "referral_pct": referral_pct,
                "fee_on_$1000": fee_calc.get("total"),
                "effective_rate": fee_calc.get("effective_rate"),
                "total_fees_defined": len(schedule)
            })
            return success

        except Exception as e:
            self.log("Fee Schedule", False, {"error": str(e)})
            return False

    async def run_all(self):
        """Run all smoke tests"""
        print("\n" + "="*70)
        print("🔥 INTEGRATION SMOKE TEST")
        print(f"   Run ID: {self.run_id}")
        print(f"   Actor ID: {self.actor_id}")
        print(f"   Backend: {self.backend}")
        print("="*70)

        tests = [
            self.test_1_discovery_hook,
            self.test_2_fabric_quote,
            self.test_3_bid_hooks,
            self.test_4_execution_hooks,
            self.test_5_payment_hook,
            self.test_6_reputation_ocs,
            self.test_7_brain_events,
            self.test_8_policy_engine,
            self.test_9_ledger_integrity,
            self.test_10_fee_schedule,
        ]

        passed = 0
        failed = 0

        for test in tests:
            try:
                result = await test()
                if result:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"\n❌ EXCEPTION in {test.__name__}: {e}")
                failed += 1

        # Summary
        print("\n" + "="*70)
        print("📊 SMOKE TEST SUMMARY")
        print("="*70)
        print(f"   ✅ Passed: {passed}")
        print(f"   ❌ Failed: {failed}")
        print(f"   📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
        print("="*70)

        if failed == 0:
            print("\n🎉 ALL TESTS PASSED - Flywheel is wired correctly!")
        else:
            print(f"\n⚠️  {failed} test(s) need attention")

        return self.results


async def main():
    tester = IntegrationSmokeTest()
    results = await tester.run_all()

    # Write results to file
    with open("smoke_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults written to: smoke_test_results.json")


if __name__ == "__main__":
    asyncio.run(main())
