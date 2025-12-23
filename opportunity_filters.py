"""
OPPORTUNITY FILTERS - Sanity Guardrails for Discovery Engine
Implements outlier detection, skip logic, and staleness checks
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
import numpy as np


def calculate_p95_cap(opportunities: List[Dict[str, Any]]) -> float:
    """
    Calculate 95th percentile cap for opportunity values
    Used to filter outliers (likely parsing errors)
    """
    values = [opp.get("value", 0) for opp in opportunities]
    if not values:
        return 100000  # Default cap
    
    return float(np.percentile(values, 95))


def is_outlier(opp: Dict[str, Any], p95_cap: float) -> bool:
    """
    Check if opportunity value is an outlier (likely parsing error)
    
    Args:
        opp: Opportunity dict
        p95_cap: 95th percentile cap from calculate_p95_cap()
    
    Returns:
        True if value exceeds P95 cap (likely parsing bug)
    """
    return opp.get("value", 0) > p95_cap


def should_skip(score: Dict[str, Any]) -> bool:
    """
    Determine if opportunity should be auto-skipped based on execution score
    
    Skip if:
    - Win probability < 0.5 (low chance of success)
    - Recommendation starts with "SKIP" or "LOW PRIORITY"
    
    Args:
        score: Execution score dict from execution_scoring
    
    Returns:
        True if opportunity should be skipped
    """
    if not score:
        return True
    
    # Low win probability
    if score.get("win_probability", 0) < 0.5:
        return True
    
    # Explicit skip recommendation
    recommendation = score.get("recommendation", "")
    if recommendation.startswith("SKIP") or recommendation.startswith("LOW PRIORITY"):
        return True
    
    return False


def is_stale(opportunity: Dict[str, Any], max_age_days: int = 30) -> bool:
    """
    Check if opportunity is stale (too old to be actionable)
    
    Only applies to HackerNews and GitHub opportunities, which often
    pull old job posts or issues that are no longer relevant.
    
    Args:
        opportunity: Opportunity dict
        max_age_days: Maximum age before considering stale (default: 30 days)
    
    Returns:
        True if opportunity is stale
    """
    platform = opportunity.get("platform", "")
    
    # Only check staleness for HN and GitHub
    if platform not in ["hackernews", "github"]:
        return False
    
    created_at = opportunity.get("created_at")
    if not created_at:
        return False
    
    try:
        # Parse ISO datetime
        if isinstance(created_at, str):
            created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        else:
            return False
        
        now = datetime.now(timezone.utc)
        age_days = (now - created).days
        
        return age_days > max_age_days
    except Exception as e:
        print(f"Error parsing created_at: {e}")
        return False


def filter_opportunities(
    opportunities: List[Dict[str, Any]],
    routing_results: Dict[str, Any],
    enable_outlier_filter: bool = True,
    enable_skip_filter: bool = True,
    enable_stale_filter: bool = True,
    max_age_days: int = 30
) -> Dict[str, Any]:
    """
    Apply all sanity filters to discovered opportunities
    
    Args:
        opportunities: List of raw opportunities
        routing_results: Full routing results from discovery engine
        enable_outlier_filter: Remove outlier values (default: True)
        enable_skip_filter: Remove low-probability opportunities (default: True)
        enable_stale_filter: Remove stale HN/GitHub posts (default: True)
        max_age_days: Maximum age for stale filter (default: 30)
    
    Returns:
        Filtered routing results with stats
    """
    
    # Calculate P95 cap for outlier detection
    p95_cap = calculate_p95_cap(opportunities) if enable_outlier_filter else float('inf')
    
    # Track filter statistics
    stats = {
        "total_opportunities": len(opportunities),
        "outliers_removed": 0,
        "skipped_removed": 0,
        "stale_removed": 0,
        "remaining_opportunities": 0,
        "total_value_before": sum(opp.get("value", 0) for opp in opportunities),
        "total_value_after": 0,
        "p95_cap": p95_cap
    }
    
    # Filter each routing category
    filtered_user_routed = []
    filtered_aigentsy_routed = []
    filtered_held = []
    
    # Filter user-routed opportunities
    if routing_results.get("user_routed", {}).get("opportunities"):
        for opp_wrapper in routing_results["user_routed"]["opportunities"]:
            opp = opp_wrapper.get("opportunity", {})
            routing = opp_wrapper.get("routing", {})
            score = routing.get("execution_score", {})
            
            # Apply filters
            if enable_outlier_filter and is_outlier(opp, p95_cap):
                stats["outliers_removed"] += 1
                continue
            
            if enable_skip_filter and should_skip(score):
                stats["skipped_removed"] += 1
                continue
            
            if enable_stale_filter and is_stale(opp, max_age_days):
                stats["stale_removed"] += 1
                continue
            
            filtered_user_routed.append(opp_wrapper)
    
    # Filter aigentsy-routed opportunities
    if routing_results.get("aigentsy_routed", {}).get("opportunities"):
        for opp_wrapper in routing_results["aigentsy_routed"]["opportunities"]:
            opp = opp_wrapper.get("opportunity", {})
            routing = opp_wrapper.get("routing", {})
            score = routing.get("execution_score", {})
            
            # Apply filters
            if enable_outlier_filter and is_outlier(opp, p95_cap):
                stats["outliers_removed"] += 1
                continue
            
            if enable_skip_filter and should_skip(score):
                stats["skipped_removed"] += 1
                continue
            
            if enable_stale_filter and is_stale(opp, max_age_days):
                stats["stale_removed"] += 1
                continue
            
            filtered_aigentsy_routed.append(opp_wrapper)
    
    # Filter held opportunities
    if routing_results.get("held", {}).get("opportunities"):
        for opp_wrapper in routing_results["held"]["opportunities"]:
            opp = opp_wrapper.get("opportunity", {})
            
            # Apply filters (no scoring for held opportunities)
            if enable_outlier_filter and is_outlier(opp, p95_cap):
                stats["outliers_removed"] += 1
                continue
            
            if enable_stale_filter and is_stale(opp, max_age_days):
                stats["stale_removed"] += 1
                continue
            
            filtered_held.append(opp_wrapper)
    
    # Recalculate totals
    user_count = len(filtered_user_routed)
    user_value = sum(o["opportunity"].get("value", 0) for o in filtered_user_routed)
    user_fee = sum(o["routing"].get("economics", {}).get("aigentsy_fee", 0) for o in filtered_user_routed)
    
    aigentsy_count = len(filtered_aigentsy_routed)
    aigentsy_value = sum(o["opportunity"].get("value", 0) for o in filtered_aigentsy_routed)
    aigentsy_profit = sum(o["routing"].get("economics", {}).get("estimated_profit", 0) for o in filtered_aigentsy_routed)
    
    held_count = len(filtered_held)
    held_value = sum(o["opportunity"].get("value", 0) for o in filtered_held)
    
    stats["remaining_opportunities"] = user_count + aigentsy_count + held_count
    stats["total_value_after"] = user_value + aigentsy_value + held_value
    
    # Build filtered results
    filtered_results = {
        "user_routed": {
            "count": user_count,
            "value": user_value,
            "aigentsy_revenue": user_fee,
            "opportunities": filtered_user_routed
        },
        "aigentsy_routed": {
            "count": aigentsy_count,
            "value": aigentsy_value,
            "estimated_profit": aigentsy_profit,
            "opportunities": filtered_aigentsy_routed,
            "requires_approval": True
        },
        "held": {
            "count": held_count,
            "value": held_value,
            "opportunities": filtered_held
        }
    }
    
    return {
        "filtered_routing": filtered_results,
        "filter_stats": stats
    }


def get_execute_now_opportunities(
    routing_results: Dict[str, Any],
    min_win_probability: float = 0.7,
    min_expected_value: float = 1000
) -> List[Dict[str, Any]]:
    """
    Get high-priority opportunities that should be executed immediately
    
    Criteria:
    - Recommendation is "EXECUTE" or "EXECUTE IMMEDIATELY"
    - Win probability >= 0.7 OR Expected value >= $1000
    
    Args:
        routing_results: Routing results (user_routed + aigentsy_routed)
        min_win_probability: Minimum win probability threshold
        min_expected_value: Minimum expected value threshold
    
    Returns:
        List of opportunities ready for immediate execution
    """
    execute_now = []
    
    # Check user-routed opportunities
    for opp_wrapper in routing_results.get("user_routed", {}).get("opportunities", []):
        score = opp_wrapper.get("routing", {}).get("execution_score", {})
        rec = score.get("recommendation", "")
        wp = score.get("win_probability", 0)
        ev = score.get("expected_value", 0)
        
        if ("EXECUTE" in rec) and (wp >= min_win_probability or ev >= min_expected_value):
            execute_now.append({
                "opportunity": opp_wrapper["opportunity"],
                "routing": opp_wrapper["routing"],
                "priority": "EXECUTE_NOW",
                "reason": f"WP: {wp:.1%}, EV: ${ev:,.0f}"
            })
    
    # Check aigentsy-routed opportunities
    for opp_wrapper in routing_results.get("aigentsy_routed", {}).get("opportunities", []):
        score = opp_wrapper.get("routing", {}).get("execution_score", {})
        rec = score.get("recommendation", "")
        wp = score.get("win_probability", 0)
        ev = score.get("expected_value", 0)
        
        if ("EXECUTE" in rec) and (wp >= min_win_probability or ev >= min_expected_value):
            execute_now.append({
                "opportunity": opp_wrapper["opportunity"],
                "routing": opp_wrapper["routing"],
                "priority": "EXECUTE_NOW",
                "reason": f"WP: {wp:.1%}, EV: ${ev:,.0f}"
            })
    
    # Sort by expected value (highest first)
    execute_now.sort(key=lambda x: x["routing"]["execution_score"]["expected_value"], reverse=True)
    
    return execute_now


# Example usage
if __name__ == "__main__":
    # Test data
    test_opportunities = [
        {"id": "1", "value": 1000, "platform": "github", "created_at": "2020-01-01T00:00:00Z"},
        {"id": "2", "value": 2000, "platform": "upwork", "created_at": "2025-12-01T00:00:00Z"},
        {"id": "3", "value": 50000000, "platform": "reddit", "created_at": "2025-12-23T00:00:00Z"},  # Outlier
        {"id": "4", "value": 3000, "platform": "hackernews", "created_at": "2024-01-01T00:00:00Z"}  # Stale
    ]
    
    test_routing = {
        "user_routed": {
            "opportunities": [
                {
                    "opportunity": test_opportunities[1],
                    "routing": {
                        "execution_score": {
                            "win_probability": 0.8,
                            "expected_value": 1500,
                            "recommendation": "EXECUTE"
                        },
                        "economics": {"aigentsy_fee": 56}
                    }
                }
            ]
        },
        "aigentsy_routed": {
            "opportunities": [
                {
                    "opportunity": test_opportunities[0],
                    "routing": {
                        "execution_score": {
                            "win_probability": 0.2,
                            "expected_value": 200,
                            "recommendation": "SKIP - Low win probability"
                        },
                        "economics": {"estimated_profit": 300}
                    }
                },
                {
                    "opportunity": test_opportunities[2],
                    "routing": {
                        "execution_score": {
                            "win_probability": 0.5,
                            "expected_value": 25000000,
                            "recommendation": "CONSIDER"
                        },
                        "economics": {"estimated_profit": 35000000}
                    }
                },
                {
                    "opportunity": test_opportunities[3],
                    "routing": {
                        "execution_score": {
                            "win_probability": 0.7,
                            "expected_value": 2100,
                            "recommendation": "EXECUTE"
                        },
                        "economics": {"estimated_profit": 900}
                    }
                }
            ]
        },
        "held": {
            "opportunities": []
        }
    }
    
    # Test filters
    print("=" * 80)
    print("TESTING OPPORTUNITY FILTERS")
    print("=" * 80)
    
    result = filter_opportunities(test_opportunities, test_routing)
    
    print("\nFILTER STATS:")
    print(f"  Total opportunities: {result['filter_stats']['total_opportunities']}")
    print(f"  Outliers removed: {result['filter_stats']['outliers_removed']}")
    print(f"  Skipped removed: {result['filter_stats']['skipped_removed']}")
    print(f"  Stale removed: {result['filter_stats']['stale_removed']}")
    print(f"  Remaining: {result['filter_stats']['remaining_opportunities']}")
    print(f"  P95 cap: ${result['filter_stats']['p95_cap']:,.0f}")
    print(f"  Total value before: ${result['filter_stats']['total_value_before']:,.0f}")
    print(f"  Total value after: ${result['filter_stats']['total_value_after']:,.0f}")
    
    print("\nFILTERED RESULTS:")
    print(f"  User-routed: {result['filtered_routing']['user_routed']['count']} opportunities")
    print(f"  AiGentsy-routed: {result['filtered_routing']['aigentsy_routed']['count']} opportunities")
    print(f"  Held: {result['filtered_routing']['held']['count']} opportunities")
    
    # Test execute now
    execute_now = get_execute_now_opportunities(result['filtered_routing'])
    print(f"\nEXECUTE NOW: {len(execute_now)} opportunities")
    for opp in execute_now:
        print(f"  - {opp['opportunity']['id']}: {opp['reason']}")
