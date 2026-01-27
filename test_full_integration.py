#!/usr/bin/env python3
"""
TEST FULL INTEGRATION: End-to-End Pipeline Test
═══════════════════════════════════════════════════════════════════════════════

Tests the complete Discovery→Contract→Fulfill→Proof→Learn flow.

Run: python test_full_integration.py
"""

import asyncio
import logging
import sys
from datetime import datetime, timezone

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_system_loader():
    """Test system loader"""
    print("\n" + "=" * 60)
    print("TEST 1: System Loader")
    print("=" * 60)

    try:
        from integration.system_loader import get_system_loader
        loader = get_system_loader()
        stats = loader.get_stats()

        print(f"  Total loaded: {stats.get('total_loaded', 0)}")
        print(f"  Total failed: {stats.get('total_failed', 0)}")
        print(f"  Managers: {stats.get('managers_loaded', 0)}")
        print(f"  Engines: {stats.get('engines_loaded', 0)}")
        print(f"  Oracles: {stats.get('oracles_loaded', 0)}")
        print(f"  Brain: {stats.get('brain_loaded', 0)}")
        print(f"  Agents: {stats.get('agents_loaded', 0)}")

        health = loader.health_check()
        print(f"  Health: {health.get('healthy')} ({health.get('coverage_pct')}%)")

        return True
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


async def test_fulfillment_orchestrator():
    """Test fulfillment orchestrator"""
    print("\n" + "=" * 60)
    print("TEST 2: Fulfillment Orchestrator")
    print("=" * 60)

    try:
        from fulfillment.orchestrator import get_fulfillment_orchestrator

        orchestrator = get_fulfillment_orchestrator()

        # Create test opportunity
        opportunity = {
            'id': 'test_opp_001',
            'title': 'Build a landing page',
            'body': 'Need a responsive landing page for product launch',
            'platform': 'test',
            'url': 'https://example.com/test',
            'enrichment': {
                'inventory_scores': {'web_dev': 0.9, 'design': 0.3},
                'payment_proximity': 0.7,
                'contact_score': 0.8,
            }
        }

        # Generate plan
        plan = orchestrator.plan_from_offerpack(opportunity)
        plan_dict = orchestrator.to_dict(plan)

        print(f"  Plan ID: {plan.opportunity_id}")
        print(f"  Offer Pack: {plan.offer_pack}")
        print(f"  Steps: {len(plan.steps)}")
        print(f"  Total SLA: {plan.total_sla_minutes} minutes")
        print(f"  Estimated Cost: ${plan.estimated_cost_usd}")

        for step in plan.steps[:3]:
            print(f"    - {step.name} ({step.sla_minutes}min)")

        return True, opportunity, plan_dict
    except Exception as e:
        print(f"  ERROR: {e}")
        return False, None, None


async def test_sow_generator(opportunity, plan_dict):
    """Test SOW generator"""
    print("\n" + "=" * 60)
    print("TEST 3: SOW Generator")
    print("=" * 60)

    try:
        from contracts.sow_generator import get_sow_generator

        generator = get_sow_generator()
        sow = generator.sow_from_plan(opportunity, plan_dict)
        sow_dict = generator.to_dict(sow)

        print(f"  SOW ID: {sow.id}")
        print(f"  Title: {sow.title}")
        print(f"  Total Amount: ${sow.total_amount_usd}")
        print(f"  Milestones: {len(sow.milestones)}")

        for m in sow.milestones:
            print(f"    - {m.name}: ${m.amount_usd} ({m.percentage}%)")

        print(f"  Deliverables: {len(sow.deliverables)}")

        return True, sow_dict
    except Exception as e:
        print(f"  ERROR: {e}")
        return False, None


async def test_milestone_escrow(opportunity, sow_dict):
    """Test milestone escrow"""
    print("\n" + "=" * 60)
    print("TEST 4: Milestone Escrow")
    print("=" * 60)

    try:
        from contracts.milestone_escrow import get_milestone_escrow

        escrow = get_milestone_escrow()
        contract = await escrow.create_milestones(opportunity, sow_dict)
        contract_dict = escrow.to_dict(contract)

        print(f"  Contract ID: {contract.id}")
        print(f"  Total Amount: ${contract.total_amount_usd}")
        print(f"  Status: {contract.status}")
        print(f"  Client Room: {contract.client_room_url[:50]}...")
        print(f"  Milestones: {len(contract.milestones)}")

        for m in contract.milestones:
            print(f"    - {m.milestone_id}: ${m.amount_usd} (AIGx: ${m.aigx_assurance_amount})")

        return True, contract_dict
    except Exception as e:
        print(f"  ERROR: {e}")
        return False, None


async def test_qa_checklists():
    """Test QA checklists"""
    print("\n" + "=" * 60)
    print("TEST 5: QA Checklists")
    print("=" * 60)

    try:
        from qa.checklists import get_qa_checklists

        qa = get_qa_checklists()

        # Create a gate
        gate = qa.create_gate('test_step_001', 'code_review')
        print(f"  Gate ID: {gate.id}")
        print(f"  Checks: {len(gate.checks)}")

        for check in gate.checks:
            print(f"    - {check.name} ({check.check_type})")

        # Run automated checks
        gate = qa.run_automated_checks(gate.id)
        print(f"  Gate Passed: {gate.passed}")

        stats = qa.get_stats()
        print(f"  Gates Created: {stats['gates_created']}")
        print(f"  Checks Run: {stats['checks_run']}")

        return True
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


async def test_workforce_dispatcher(plan_dict):
    """Test workforce dispatcher"""
    print("\n" + "=" * 60)
    print("TEST 6: Workforce Dispatcher")
    print("=" * 60)

    try:
        from workforce.dispatcher import get_workforce_dispatcher

        dispatcher = get_workforce_dispatcher()

        # Dispatch first step
        if plan_dict and plan_dict.get('steps'):
            step = plan_dict['steps'][0]
            task = await dispatcher.dispatch_step(step, plan_dict['opportunity_id'])

            print(f"  Task ID: {task.id}")
            print(f"  Tier: {task.tier.value}")
            print(f"  Priority: {task.priority.value}")
            print(f"  Status: {task.status}")
            print(f"  Assigned To: {task.assigned_to}")

        # Check capacity
        capacity = dispatcher.get_capacity()
        print(f"  Capacity:")
        for tier, data in capacity.items():
            print(f"    - {tier}: {data['available']}/{data['capacity']} available")

        stats = dispatcher.get_stats()
        print(f"  Tasks Dispatched: {stats['tasks_dispatched']}")

        return True
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


async def test_proof_ledger(opportunity):
    """Test proof of outcome ledger"""
    print("\n" + "=" * 60)
    print("TEST 7: Proof of Outcome Ledger")
    print("=" * 60)

    try:
        from monetization.proof_ledger import get_proof_ledger

        ledger = get_proof_ledger()

        # Create proof
        proof = ledger.create_proof(
            opportunity_id=opportunity['id'],
            title="Landing Page Delivered",
            description="Responsive landing page with all requested features",
            artifacts=[
                "https://github.com/example/pr/123",
                "https://staging.example.com",
            ],
            proof_type="deliverable",
        )

        print(f"  Proof ID: {proof.id}")
        print(f"  Hash: {proof.hash[:32]}...")
        print(f"  Public URL: {proof.public_url}")
        print(f"  Artifacts: {len(proof.artifacts)}")

        # Verify proof
        ledger.verify_proof(proof.id, "client", 1000)
        print(f"  Verified: {proof.verified}")

        stats = ledger.get_stats()
        print(f"  Proofs Created: {stats['proofs_created']}")
        print(f"  Proofs Verified: {stats['proofs_verified']}")

        return True
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


async def test_growth_loops(opportunity, contract_dict):
    """Test growth loops"""
    print("\n" + "=" * 60)
    print("TEST 8: Growth Loops")
    print("=" * 60)

    try:
        from growth.growth_loops import get_growth_loops

        growth = get_growth_loops()

        # Simulate milestone completion
        milestone = {
            'id': 'm1',
            'name': 'Final Delivery',
        }

        opportunities = growth.on_milestone_complete(opportunity, contract_dict, milestone)
        print(f"  Growth Opportunities Identified: {len(opportunities)}")

        for opp in opportunities:
            print(f"    - {opp.title}: ${opp.estimated_value_usd} ({opp.type})")

        # Test referral on high satisfaction
        referral = growth.on_high_satisfaction(opportunity, contract_dict, 0.9)
        if referral:
            print(f"  Referral Created: {referral.id} (${referral.incentive_usd} incentive)")

        stats = growth.get_stats()
        print(f"  Total Identified: {stats['opportunities_identified']}")
        print(f"  Pipeline Value: ${stats['pipeline']['pipeline_value_usd']}")

        return True
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


async def test_event_bus():
    """Test event bus"""
    print("\n" + "=" * 60)
    print("TEST 9: Event Bus")
    print("=" * 60)

    try:
        from integration.event_bus import get_event_bus, EventType

        bus = get_event_bus()

        # Track received events
        received_events = []

        async def handler(event):
            received_events.append(event)

        # Subscribe
        bus.subscribe(
            'test_subscriber',
            [EventType.OPPORTUNITY_DISCOVERED, EventType.STEP_COMPLETED],
            handler
        )

        # Start bus
        await bus.start()

        # Publish events
        await bus.publish(EventType.OPPORTUNITY_DISCOVERED, {'id': 'test_001'})
        await bus.publish(EventType.STEP_COMPLETED, {'step_id': 'analyze'})

        # Wait for processing
        await asyncio.sleep(0.1)

        # Stop bus
        await bus.stop()

        print(f"  Events Published: {bus.stats['events_published']}")
        print(f"  Events Processed: {bus.stats['events_processed']}")
        print(f"  Events Received by Subscriber: {len(received_events)}")
        print(f"  Backpressure Status: {bus.get_backpressure_status()['backpressure_active']}")

        return True
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


async def main():
    """Run all integration tests"""
    print("\n" + "=" * 60)
    print("AIGENTSY FULL INTEGRATION TEST")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    results = {}

    # Test 1: System Loader
    results['system_loader'] = await test_system_loader()

    # Test 2: Fulfillment Orchestrator
    success, opportunity, plan_dict = await test_fulfillment_orchestrator()
    results['orchestrator'] = success

    if not opportunity:
        opportunity = {'id': 'fallback_opp', 'title': 'Test', 'body': '', 'platform': 'test'}

    # Test 3: SOW Generator
    if plan_dict:
        success, sow_dict = await test_sow_generator(opportunity, plan_dict)
        results['sow_generator'] = success
    else:
        results['sow_generator'] = False
        sow_dict = None

    # Test 4: Milestone Escrow
    if sow_dict:
        success, contract_dict = await test_milestone_escrow(opportunity, sow_dict)
        results['escrow'] = success
    else:
        results['escrow'] = False
        contract_dict = None

    # Test 5: QA Checklists
    results['qa_checklists'] = await test_qa_checklists()

    # Test 6: Workforce Dispatcher
    results['workforce'] = await test_workforce_dispatcher(plan_dict)

    # Test 7: Proof Ledger
    results['proof_ledger'] = await test_proof_ledger(opportunity)

    # Test 8: Growth Loops
    if contract_dict:
        results['growth_loops'] = await test_growth_loops(opportunity, contract_dict)
    else:
        results['growth_loops'] = False

    # Test 9: Event Bus
    results['event_bus'] = await test_event_bus()

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for r in results.values() if r)
    total = len(results)

    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")

    print(f"\n  Total: {passed}/{total} passed")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
