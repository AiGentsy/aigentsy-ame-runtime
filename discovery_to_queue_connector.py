"""
DISCOVERY TO QUEUE CONNECTOR
Processes discovered opportunities and routes them to Wade's approval queue

Usage:
    from discovery_to_queue_connector import process_discovery_results
    
    # After running discovery
    discovery_results = await discover_all_opportunities("wade", {})
    processed = await process_discovery_results(discovery_results)
"""

from typing import Dict, Any, List
import asyncio
from datetime import datetime, timezone


async def process_discovery_results(discovery_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Take discovery results and feed Wade opportunities into approval queue
    
    Args:
        discovery_results: Output from discover_all_opportunities()
    
    Returns:
        Summary of processing
    """
    
    from wade_integrated_workflow import integrated_workflow
    
    if not discovery_results.get('ok'):
        return {
            'ok': False,
            'error': 'Discovery results not ok',
            'results': discovery_results
        }
    
    # Get opportunities from discovery results
    # discover_all_opportunities returns: {ok, opportunities, by_platform, total_found}
    all_opportunities = discovery_results.get('opportunities', [])
    
    # Filter for Wade-fulfillable opportunities
    # For now, take all opportunities (can add filtering logic later)
    wade_opportunities = all_opportunities
    
    total_found = discovery_results.get('total_found', 0)
    
    print(f"📊 Processing {len(wade_opportunities)} opportunities out of {total_found} total discovered")
    
    processed = []
    errors = []
    
    for opp in wade_opportunities:
        try:
            # Add to Wade's approval queue via integrated workflow
            result = await integrated_workflow.process_discovered_opportunity(opp)
            
            processed.append({
                'opportunity_id': opp['id'],
                'title': opp['title'][:60],
                'platform': opp['source'],
                'value': opp.get('estimated_value', 0),
                'workflow_id': result.get('workflow_id'),
                'fulfillment_id': result.get('fulfillment_id'),
                'stage': result.get('stage')
            })
            
            print(f"  ✅ Added: {opp['title'][:50]} (${opp.get('estimated_value', 0)})")
            
        except Exception as e:
            errors.append({
                'opportunity_id': opp['id'],
                'title': opp['title'][:60],
                'error': str(e)
            })
            print(f"  ❌ Failed: {opp['title'][:50]} - {str(e)}")
    
    return {
        'ok': True,
        'total_discovered': discovery_results.get('total_found', 0),
        'wade_opportunities': len(wade_opportunities),
        'processed': len(processed),
        'errors': len(errors),
        'fulfillment_ids': [p['fulfillment_id'] for p in processed if p.get('fulfillment_id')],
        'opportunities': processed,
        'error_details': errors,
        'completed_at': datetime.now(timezone.utc).isoformat()
    }


async def auto_discover_and_queue(username: str = "wade", platforms: List[str] = None) -> Dict[str, Any]:
    """
    Complete flow: Discover → Filter → Queue
    
    One-step function to discover and queue opportunities
    """
    
    from ultimate_discovery_engine import discover_all_opportunities
    
    print(f"🔍 Starting auto-discovery for {username}...")
    print(f"   Platforms: {platforms or 'ALL (27 platforms)'}")
    
    # Build user profile (can be enhanced with actual user data)
    user_profile = {
        "username": username,
        "skills": [],
        "kits": [],
        "companyType": "general"
    }
    
    # Step 1: Discover
    discovery_results = await discover_all_opportunities(
        username=username,
        user_profile=user_profile,
        platforms=platforms
    )
    
    if not discovery_results.get('ok'):
        return {
            'ok': False,
            'error': 'Discovery failed',
            'details': discovery_results
        }
    
    total_found = discovery_results.get('total_found', 0)
    print(f"✅ Discovery complete: {total_found} opportunities found")
    
    # Step 2: Process and queue
    queue_results = await process_discovery_results(discovery_results)
    
    print(f"\n📋 SUMMARY:")
    print(f"   Total discovered: {queue_results['total_discovered']}")
    print(f"   Wade opportunities: {queue_results['wade_opportunities']}")
    print(f"   Added to queue: {queue_results['processed']}")
    print(f"   Errors: {queue_results['errors']}")
    
    return queue_results


# For FastAPI endpoint
async def endpoint_discover_and_queue(username: str, platforms: List[str] = None):
    """
    FastAPI endpoint handler
    
    POST /wade/discover-and-queue
    {
        "username": "wade",
        "platforms": ["github", "upwork"]  // optional
    }
    """
    return await auto_discover_and_queue(username, platforms)


if __name__ == "__main__":
    # Test
    results = asyncio.run(auto_discover_and_queue("wade"))
    print(f"\n✅ Complete! {results['processed']} opportunities added to Wade's queue")
