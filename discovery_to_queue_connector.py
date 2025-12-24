from typing import Dict, Any, List
from datetime import datetime, timezone


async def process_and_queue(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point - discovers and queues in one call
    
    Handles all errors gracefully
    """
    
    try:
        # Get params
        username = request.get("username", "wade")
        platforms = request.get("platforms")
        
        # Step 1: Import modules (do this inside function to avoid circular imports)
        try:
            from ultimate_discovery_engine_FINAL import discover_all_opportunities
            from wade_integrated_workflow import integrated_workflow
        except ImportError as e:
            return {
                "ok": False,
                "error": f"Import failed: {str(e)}",
                "step": "imports"
            }
        
        # Step 2: Run discovery
        try:
            discovery_results = await discover_all_opportunities(username, platforms or {})
        except Exception as e:
            return {
                "ok": False,
                "error": f"Discovery failed: {str(e)}",
                "step": "discovery"
            }
        
        # Check discovery results
        if not discovery_results.get('status') == 'ok':
            return {
                "ok": False,
                "error": "Discovery returned non-ok status",
                "step": "discovery",
                "discovery_results": discovery_results
            }
        
        # Step 3: Get opportunities
        all_opportunities = discovery_results.get('opportunities', [])
        
        if not all_opportunities:
            return {
                "ok": True,
                "message": "No opportunities found",
                "total_discovered": 0,
                "wade_opportunities": 0,
                "processed": 0
            }
        
        # Step 4: Filter for Wade
        wade_opportunities = []
        for opp in all_opportunities:
            fulfillability = opp.get('fulfillability', {})
            
            if (fulfillability.get('routing') == 'wade' and 
                fulfillability.get('can_wade_fulfill', False)):
                wade_opportunities.append(opp)
        
        # Step 5: Process each Wade opportunity
        processed = []
        errors = []
        
        for opp in wade_opportunities:
            try:
                # Add to approval queue
                result = await integrated_workflow.process_discovered_opportunity(opp)
                
                if result:
                    processed.append({
                        'opportunity_id': opp['id'],
                        'title': opp['title'][:60] if 'title' in opp else 'Unknown',
                        'platform': opp.get('source', 'unknown'),
                        'value': opp.get('estimated_value', 0),
                        'workflow_id': result.get('workflow_id'),
                        'fulfillment_id': result.get('fulfillment_id')
                    })
                
            except Exception as e:
                errors.append({
                    'opportunity_id': opp.get('id', 'unknown'),
                    'title': opp.get('title', 'unknown')[:60],
                    'error': str(e)
                })
        
        # Return summary
        return {
            "ok": True,
            "total_discovered": len(all_opportunities),
            "wade_opportunities": len(wade_opportunities),
            "processed": len(processed),
            "errors": len(errors),
            "opportunities": processed[:10],  # First 10 for preview
            "error_details": errors[:5] if errors else [],  # First 5 errors
            "completed_at": datetime.now(timezone.utc).isoformat()
        }
    
    except Exception as e:
        # Catch-all for any unexpected errors
        return {
            "ok": False,
            "error": f"Unexpected error: {str(e)}",
            "error_type": type(e).__name__,
            "step": "general"
        }


# Standalone function for testing
async def test_process_and_queue():
    """Test function"""
    result = await process_and_queue({"username": "wade", "platforms": ["github"]})
    return result

# Add this at the end of the file for backward compatibility
async def auto_discover_and_queue(username: str = "wade", platforms: List[str] = None) -> Dict[str, Any]:
    """Backward compatible wrapper"""
    request = {
        "username": username,
        "platforms": platforms
    }
    return await process_and_queue(request)
