"""
OPPORTUNITY FILTERS - Sanity Guardrails for Discovery Engine
Implements outlier detection, skip logic, staleness checks, and MONETIZABILITY FILTERS

UPGRADED with:
- Non-monetizable pain point detection (personal problems, gaming, health advice)
- Actionability scoring (can we actually execute on this?)
- Contact info validation (email, phone, post_id)
- Platform-specific execution readiness
- POLYMORPHIC FLOW INTEGRATION (v115+)
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
import re

# Try numpy, fallback to manual percentile
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

# Try polymorphic execution flows
try:
    from platform_execution_flows import (
        determine_execution_flow,
        get_configured_apis,
        ExecutionMode
    )
    POLYMORPHIC_FLOWS_AVAILABLE = True
except ImportError:
    POLYMORPHIC_FLOWS_AVAILABLE = False
    determine_execution_flow = None
    get_configured_apis = None


# =============================================================================
# NON-MONETIZABLE CATEGORIES - Filter these OUT
# =============================================================================

# Subreddits that are NOT monetizable (personal advice, gaming, health, etc.)
NON_MONETIZABLE_SUBREDDITS = {
    # Personal/Health (we can't help with medical advice)
    'eczema', 'health', 'askdocs', 'medical', 'mentalhealth', 'depression',
    'anxiety', 'adhd', 'autism', 'chronicpain', 'chronicillness', 'cancer',
    'pregnant', 'babybumps', 'beyondthebump', 'parenting', 'mommit', 'daddit',
    'sleeptrain', 'newparents', 'toddlers',
    
    # Gaming (not monetizable service requests)
    'gaming', 'games', 'pcgaming', 'ps5', 'xbox', 'nintendoswitch', 'steam',
    'leagueoflegends', 'valorant', 'overwatch', 'minecraft', 'fortnite',
    'dbzdokkanbattle', 'gachagaming', 'mobilegaming', 'age_30_plus_gamers',
    
    # Shopping/Codes (spam territory)
    'sheincodeShare', 'coupons', 'deals', 'frugal', 'referralcodes',
    
    # Relationships (not our business)
    'relationships', 'relationship_advice', 'dating', 'tinder', 'bumble',
    'amitheasshole', 'tifu', 'confessions', 'offmychest', 'trueoffmychest',
    
    # Politics/News (too risky)
    'politics', 'worldnews', 'news', 'conservative', 'liberal',
    
    # Hobbies (not monetizable requests)
    'cars', 'indianbikes', 'motorcycles', 'bicycling', 'running', 'fitness',
    'food', 'cooking', 'recipes', 'gardening', 'houseplants',
    
    # Location-specific (usually not actionable)
    'luxembourg', 'netherlands', 'germany', 'france', 'uk', 'australia',
    'canada', 'losangeles', 'nyc', 'chicago', 'seattle', 'austin',
    'castateworkers',  # State worker questions
    
    # Random/Entertainment
    'funny', 'pics', 'videos', 'gifs', 'memes', 'dankmemes',
    'aww', 'eyebleach', 'wholesome', 'marcuswormfanclub',
}

# Pain point keywords that indicate NON-monetizable personal problems
NON_MONETIZABLE_KEYWORDS = [
    # Health/Medical
    'eczema', 'rash', 'symptoms', 'diagnosis', 'doctor', 'medication',
    'prescription', 'pregnant', 'baby', 'toddler', 'sleep training',
    'breastfeeding', 'nausea', 'pain', 'headache', 'chronic',
    
    # Personal life
    'boyfriend', 'girlfriend', 'husband', 'wife', 'divorce', 'breakup',
    'dating', 'relationship', 'marriage', 'family drama', 'in-laws',
    'landlord', 'eviction', 'moving', 'roommate',
    
    # Gaming
    'game recommendation', 'which game', 'best loadout', 'meta build',
    'battle pass', 'festival of battle', 'gamma', 'gohan', 'piccolo',
    
    # Shopping
    'shein', 'coupon code', 'discount code', 'referral', 'promo code',
    
    # General help
    'help me understand', 'explain like', 'eli5', 'what should i do',
]

# Keywords that INDICATE monetizable opportunities
MONETIZABLE_KEYWORDS = [
    # Hiring signals
    'hiring', 'looking for', 'need developer', 'need designer', 'need help with',
    'freelancer wanted', 'contractor needed', 'seeking expert', 'budget',
    '$', 'paid', 'compensation', 'salary', 'hourly', 'per project',
    
    # Business needs
    'build', 'develop', 'create', 'design', 'implement', 'automate',
    'website', 'app', 'api', 'integration', 'dashboard', 'platform',
    'saas', 'startup', 'mvp', 'prototype', 'landing page',
    
    # Technical bounties
    'bounty', 'reward', 'grant', 'prize', 'issue', 'bug fix', 'feature',
    'pull request', 'contribution', 'open source',
    
    # Marketing/Content
    'content creation', 'blog', 'seo', 'marketing', 'social media',
    'copywriting', 'ads', 'campaign', 'growth', 'leads',
]


def calculate_p95_cap(opportunities: List[Dict[str, Any]]) -> float:
    """
    Calculate 95th percentile cap for opportunity values
    Used to filter outliers (likely parsing errors)
    """
    values = [opp.get("value", 0) for opp in opportunities]
    if not values:
        return 100000  # Default cap
    
    if HAS_NUMPY:
        return float(np.percentile(values, 95))
    else:
        # Manual percentile calculation
        sorted_vals = sorted(values)
        idx = int(len(sorted_vals) * 0.95)
        return float(sorted_vals[min(idx, len(sorted_vals) - 1)])


def is_monetizable(opportunity: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Check if opportunity is actually monetizable (can we make money from it?)
    
    Returns:
        Tuple of (is_monetizable: bool, reason: str)
    """
    platform = opportunity.get('platform', '').lower()
    source = opportunity.get('source', '').lower()
    title = opportunity.get('title', '').lower()
    description = opportunity.get('description', '').lower()
    text = f"{title} {description}"
    
    # Check subreddit first
    source_data = opportunity.get('source_data', {})
    subreddit = source_data.get('subreddit', '').lower()
    
    if subreddit in NON_MONETIZABLE_SUBREDDITS:
        return False, f"Non-monetizable subreddit: r/{subreddit}"
    
    # Check for non-monetizable keywords
    for keyword in NON_MONETIZABLE_KEYWORDS:
        if keyword.lower() in text:
            # But check if there's also a monetizable signal
            has_monetizable = any(mk.lower() in text for mk in MONETIZABLE_KEYWORDS)
            if not has_monetizable:
                return False, f"Non-monetizable keyword: '{keyword}'"
    
    # GitHub issues without bounty labels might be unpaid
    if platform == 'github':
        labels = source_data.get('labels', [])
        label_str = ' '.join(str(l).lower() for l in labels)
        
        # Must have bounty/paid indicator OR help wanted
        if 'bounty' not in label_str and '$' not in label_str:
            # Check if it's a real bounty
            if 'help wanted' not in label_str and 'good first issue' not in label_str:
                return False, "GitHub issue without bounty/help-wanted label"
    
    # HackerNews jobs are often old
    if platform == 'hackernews':
        created = opportunity.get('created_at', '')
        if created and '2020' in created or '2019' in created or '2016' in created or '2017' in created:
            return False, "Stale HackerNews job post"
    
    # Check for monetizable signals
    has_monetizable_signal = any(mk.lower() in text for mk in MONETIZABLE_KEYWORDS)
    has_value = opportunity.get('value', 0) > 0
    
    if not has_monetizable_signal and not has_value:
        return False, "No monetizable signals detected"
    
    return True, "Monetizable"


def is_actionable(opportunity: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Check if we can actually take action on this opportunity
    
    Requirements by platform:
    - Reddit: need post_id or URL we can parse
    - Twitter: need tweet_id or URL
    - Email: need contact email
    - GitHub: need owner/repo/issue_number
    - Upwork: always actionable (manual)
    """
    platform = opportunity.get('platform', '').lower()
    url = opportunity.get('url', '')
    source_data = opportunity.get('source_data', {})
    
    if platform == 'reddit':
        # Parse Reddit URL for post ID
        post_id = source_data.get('post_id')
        if not post_id and url:
            # Try to extract from URL: /comments/POST_ID/
            match = re.search(r'/comments/([a-zA-Z0-9]+)/', url)
            if match:
                return True, f"Actionable: post_id={match.group(1)}"
        if post_id:
            return True, f"Actionable: post_id={post_id}"
        return False, "No Reddit post_id found"
    
    elif platform == 'twitter':
        tweet_id = source_data.get('tweet_id')
        if not tweet_id and url:
            # Try to extract from URL
            match = re.search(r'/status/(\d+)', url)
            if match:
                return True, f"Actionable: tweet_id={match.group(1)}"
        if tweet_id:
            return True, f"Actionable: tweet_id={tweet_id}"
        # Twitter pain points without specific tweet are harder
        if 'simulated' in url:
            return False, "Simulated Twitter opportunity"
        return False, "No Twitter tweet_id found"
    
    elif platform == 'github':
        # Parse GitHub URL
        if url:
            match = re.search(r'github\.com/([^/]+)/([^/]+)/issues/(\d+)', url)
            if match:
                return True, f"Actionable: {match.group(1)}/{match.group(2)}#{match.group(3)}"
            match = re.search(r'github\.com/([^/]+)/([^/]+)/pull/(\d+)', url)
            if match:
                return True, f"Actionable PR: {match.group(1)}/{match.group(2)}#{match.group(3)}"
        return False, "Cannot parse GitHub URL"
    
    elif platform in ['upwork', 'fiverr']:
        # Marketplace - always actionable via manual submission
        return True, "Actionable: marketplace opportunity"
    
    elif platform == 'email':
        email = opportunity.get('contact_email') or source_data.get('email')
        if email and '@' in str(email):
            return True, f"Actionable: email={email}"
        return False, "No contact email"
    
    elif platform == 'hackernews':
        # HN comments - need story/comment ID
        item_id = source_data.get('story_id') or source_data.get('id')
        if item_id:
            return True, f"Actionable: hn_id={item_id}"
        if url and 'item?id=' in url:
            return True, "Actionable: URL contains item ID"
        return False, "No HN item ID"
    
    elif platform in ['producthunt', 'quora', 'app_store']:
        # These are more for outreach/research
        return True, "Actionable: outreach opportunity"
    
    elif platform in ['predictive', 'cross_platform', 'internal_network', 'proactive_outreach', 'ai_analysis']:
        # These are AI-generated insights - always actionable
        return True, "Actionable: AI-generated opportunity"
    
    # Unknown platform - be permissive
    return True, "Actionable: unknown platform (permissive)"


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
    enable_monetizable_filter: bool = True,
    enable_actionable_filter: bool = True,
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
        enable_monetizable_filter: Remove non-monetizable opportunities (default: True)
        enable_actionable_filter: Remove non-actionable opportunities (default: True)
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
        "non_monetizable_removed": 0,
        "non_actionable_removed": 0,
        "remaining_opportunities": 0,
        "total_value_before": sum(opp.get("value", 0) for opp in opportunities),
        "total_value_after": 0,
        "p95_cap": p95_cap,
        "filter_reasons": []
    }
    
    def apply_filters(opp: Dict, score: Dict = None) -> Tuple[bool, str]:
        """Apply all filters to a single opportunity. Returns (passed, reason)."""
        
        # Outlier filter
        if enable_outlier_filter and is_outlier(opp, p95_cap):
            return False, "outlier"
        
        # Skip filter (low win probability)
        if enable_skip_filter and score and should_skip(score):
            return False, "low_probability"
        
        # Stale filter
        if enable_stale_filter and is_stale(opp, max_age_days):
            return False, "stale"
        
        # Monetizability filter
        if enable_monetizable_filter:
            monetizable, reason = is_monetizable(opp)
            if not monetizable:
                return False, f"non_monetizable: {reason}"
        
        # Actionability filter
        if enable_actionable_filter:
            actionable, reason = is_actionable(opp)
            if not actionable:
                return False, f"non_actionable: {reason}"
        
        return True, "passed"
    
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
            
            passed, reason = apply_filters(opp, score)
            
            if not passed:
                if "outlier" in reason:
                    stats["outliers_removed"] += 1
                elif "low_probability" in reason:
                    stats["skipped_removed"] += 1
                elif "stale" in reason:
                    stats["stale_removed"] += 1
                elif "non_monetizable" in reason:
                    stats["non_monetizable_removed"] += 1
                elif "non_actionable" in reason:
                    stats["non_actionable_removed"] += 1
                stats["filter_reasons"].append({"id": opp.get("id"), "reason": reason})
                continue
            
            filtered_user_routed.append(opp_wrapper)
    
    # Filter aigentsy-routed opportunities
    if routing_results.get("aigentsy_routed", {}).get("opportunities"):
        for opp_wrapper in routing_results["aigentsy_routed"]["opportunities"]:
            opp = opp_wrapper.get("opportunity", {})
            routing = opp_wrapper.get("routing", {})
            score = routing.get("execution_score", {})
            
            passed, reason = apply_filters(opp, score)
            
            if not passed:
                if "outlier" in reason:
                    stats["outliers_removed"] += 1
                elif "low_probability" in reason:
                    stats["skipped_removed"] += 1
                elif "stale" in reason:
                    stats["stale_removed"] += 1
                elif "non_monetizable" in reason:
                    stats["non_monetizable_removed"] += 1
                elif "non_actionable" in reason:
                    stats["non_actionable_removed"] += 1
                stats["filter_reasons"].append({"id": opp.get("id"), "reason": reason})
                continue
            
            filtered_aigentsy_routed.append(opp_wrapper)
    
    # Filter held opportunities
    if routing_results.get("held", {}).get("opportunities"):
        for opp_wrapper in routing_results["held"]["opportunities"]:
            opp = opp_wrapper.get("opportunity", {})
            
            passed, reason = apply_filters(opp)
            
            if not passed:
                if "outlier" in reason:
                    stats["outliers_removed"] += 1
                elif "stale" in reason:
                    stats["stale_removed"] += 1
                elif "non_monetizable" in reason:
                    stats["non_monetizable_removed"] += 1
                elif "non_actionable" in reason:
                    stats["non_actionable_removed"] += 1
                stats["filter_reasons"].append({"id": opp.get("id"), "reason": reason})
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


def extract_execution_target(opportunity: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract execution target info from opportunity URL/data

    ENHANCED: Now integrates with polymorphic execution flows to determine
    the correct execution mode and required APIs.

    Returns a dict with platform-specific execution info:
    - Reddit: post_id, subreddit
    - Twitter: tweet_id
    - GitHub: owner, repo, issue_number
    - Email: contact_email
    - Plus: execution_mode, flow_key, required_apis, auto_execute
    """
    platform = opportunity.get('platform', '').lower()
    url = opportunity.get('url', '')
    source_data = opportunity.get('source_data', {})

    target = {
        'platform': platform,
        'can_execute': False,
        'method': None,
        'details': {},
        # Polymorphic flow info
        'execution_mode': None,
        'flow_key': None,
        'requires_communication': True,
        'requires_approval': True,
        'auto_execute': False,
        'missing_apis': [],
        'flow_reason': None
    }

    # Get polymorphic flow info if available
    if POLYMORPHIC_FLOWS_AVAILABLE and determine_execution_flow:
        flow_result = determine_execution_flow(opportunity)
        target['execution_mode'] = flow_result.get('execution_mode')
        target['flow_key'] = flow_result.get('flow_key')
        target['requires_communication'] = flow_result.get('requires_communication', True)
        target['requires_approval'] = flow_result.get('requires_approval', True)
        target['auto_execute'] = flow_result.get('auto_execute', False)
        target['missing_apis'] = flow_result.get('missing_apis', [])
        target['flow_reason'] = flow_result.get('reason')

        # If flow says we can execute and APIs are available, set can_execute
        if flow_result.get('can_execute'):
            target['can_execute'] = True
    
    if platform == 'reddit':
        # Extract post ID from URL
        post_id = source_data.get('post_id')
        if not post_id and url:
            match = re.search(r'/comments/([a-zA-Z0-9]+)/', url)
            if match:
                post_id = match.group(1)
        
        if post_id:
            target['can_execute'] = True
            target['method'] = 'comment'
            target['details'] = {
                'post_id': post_id,
                'subreddit': source_data.get('subreddit', 'unknown'),
                'thing_id': f"t3_{post_id}" if not post_id.startswith('t3_') else post_id
            }
    
    elif platform == 'github':
        # Extract owner/repo/issue from URL
        if url:
            issue_match = re.search(r'github\.com/([^/]+)/([^/]+)/issues/(\d+)', url)
            pr_match = re.search(r'github\.com/([^/]+)/([^/]+)/pull/(\d+)', url)
            
            if issue_match:
                target['can_execute'] = True
                target['method'] = 'issue_comment'
                target['details'] = {
                    'owner': issue_match.group(1),
                    'repo': issue_match.group(2),
                    'issue_number': int(issue_match.group(3))
                }
            elif pr_match:
                target['can_execute'] = True
                target['method'] = 'pr_comment'
                target['details'] = {
                    'owner': pr_match.group(1),
                    'repo': pr_match.group(2),
                    'pr_number': int(pr_match.group(3))
                }
    
    elif platform == 'twitter':
        tweet_id = source_data.get('tweet_id')
        if not tweet_id and url:
            match = re.search(r'/status/(\d+)', url)
            if match:
                tweet_id = match.group(1)
        
        if tweet_id:
            target['can_execute'] = True
            target['method'] = 'reply'
            target['details'] = {'tweet_id': tweet_id}
        else:
            # Can still tweet about the opportunity
            target['can_execute'] = True
            target['method'] = 'tweet'
            target['details'] = {}
    
    elif platform == 'hackernews':
        item_id = source_data.get('story_id') or source_data.get('id')
        if not item_id and url:
            match = re.search(r'item\?id=(\d+)', url)
            if match:
                item_id = match.group(1)
        
        if item_id:
            target['can_execute'] = True
            target['method'] = 'comment'
            target['details'] = {'item_id': item_id}
    
    elif platform in ['upwork', 'fiverr', '99designs']:
        target['can_execute'] = True
        target['method'] = 'manual_apply'
        target['details'] = {'url': url}
    
    elif platform == 'email' or opportunity.get('contact_email'):
        email = opportunity.get('contact_email') or source_data.get('email')
        if email:
            target['can_execute'] = True
            target['method'] = 'email'
            target['details'] = {'email': email}
    
    elif platform in ['predictive', 'cross_platform', 'internal_network', 'proactive_outreach']:
        # AI-generated opportunities - execute via outreach
        target['can_execute'] = True
        target['method'] = 'proactive_outreach'
        target['details'] = {
            'source': opportunity.get('source', ''),
            'prediction_type': source_data.get('prediction_type', '')
        }
    
    return target


def enrich_opportunity_for_execution(opportunity: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich opportunity with execution target info

    Adds 'execution_target' key with parsed execution details
    including polymorphic flow information.
    """
    enriched = opportunity.copy()
    enriched['execution_target'] = extract_execution_target(opportunity)

    # Also add flow info directly to opportunity for orchestrator
    if POLYMORPHIC_FLOWS_AVAILABLE and determine_execution_flow:
        flow_result = determine_execution_flow(opportunity)
        enriched['_flow'] = flow_result

    return enriched


def get_execution_readiness_summary(opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Get a summary of execution readiness across all opportunities.

    Shows:
    - How many can be auto-executed (GitHub bounties, content posting)
    - How many need communication (LinkedIn, Reddit)
    - How many are blocked by missing APIs
    - Breakdown by execution mode
    """
    summary = {
        'total': len(opportunities),
        'can_auto_execute': 0,
        'needs_communication': 0,
        'needs_approval': 0,
        'blocked_by_apis': 0,
        'by_mode': {},
        'by_platform': {},
        'missing_apis_breakdown': {}
    }

    if not POLYMORPHIC_FLOWS_AVAILABLE:
        summary['warning'] = 'Polymorphic flows not available - all will use communication flow'
        return summary

    for opp in opportunities:
        flow_result = determine_execution_flow(opp)
        platform = opp.get('platform', 'unknown')
        mode = flow_result.get('execution_mode', 'unknown')

        # Count by mode
        summary['by_mode'][mode] = summary['by_mode'].get(mode, 0) + 1

        # Count by platform
        summary['by_platform'][platform] = summary['by_platform'].get(platform, 0) + 1

        # Check execution readiness
        if flow_result.get('auto_execute'):
            summary['can_auto_execute'] += 1
        if flow_result.get('requires_communication'):
            summary['needs_communication'] += 1
        if flow_result.get('requires_approval'):
            summary['needs_approval'] += 1

        # Check API availability
        missing = flow_result.get('missing_apis', [])
        if missing:
            summary['blocked_by_apis'] += 1
            for api in missing:
                summary['missing_apis_breakdown'][api] = summary['missing_apis_breakdown'].get(api, 0) + 1

    return summary


def filter_by_execution_readiness(
    opportunities: List[Dict[str, Any]],
    require_auto_execute: bool = False,
    skip_missing_apis: bool = True,
    allowed_modes: List[str] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Filter opportunities based on execution readiness.

    Args:
        opportunities: List of opportunities to filter
        require_auto_execute: If True, only return opportunities that can auto-execute
        skip_missing_apis: If True, skip opportunities missing required APIs
        allowed_modes: If provided, only return opportunities with these execution modes

    Returns:
        Tuple of (filtered_opportunities, filter_stats)
    """
    if not POLYMORPHIC_FLOWS_AVAILABLE:
        # Return all opportunities if flows not available
        return opportunities, {'warning': 'flows_not_available', 'returned': len(opportunities)}

    filtered = []
    stats = {
        'total': len(opportunities),
        'passed': 0,
        'skipped_auto_execute': 0,
        'skipped_missing_apis': 0,
        'skipped_mode': 0
    }

    for opp in opportunities:
        flow_result = determine_execution_flow(opp)

        # Check auto-execute requirement
        if require_auto_execute and not flow_result.get('auto_execute'):
            stats['skipped_auto_execute'] += 1
            continue

        # Check API availability
        if skip_missing_apis and flow_result.get('missing_apis'):
            stats['skipped_missing_apis'] += 1
            continue

        # Check allowed modes
        if allowed_modes:
            mode = flow_result.get('execution_mode')
            if mode not in allowed_modes:
                stats['skipped_mode'] += 1
                continue

        # Enrich and add
        enriched = opp.copy()
        enriched['_flow'] = flow_result
        filtered.append(enriched)
        stats['passed'] += 1

    return filtered, stats


def get_immediate_execution_opportunities(opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Get opportunities that can be executed immediately without communication.

    These are typically:
    - GitHub bounties (analyze → PR → claim)
    - Twitter affiliate posts (generate → post → track)
    - Content posting opportunities

    Returns opportunities enriched with flow info, ready for immediate execution.
    """
    if not POLYMORPHIC_FLOWS_AVAILABLE:
        return []

    immediate = []
    for opp in opportunities:
        flow_result = determine_execution_flow(opp)

        # Check if immediate execution is possible
        if (flow_result.get('execution_mode') == 'immediate' and
            flow_result.get('can_execute') and
            flow_result.get('auto_execute')):

            enriched = opp.copy()
            enriched['_flow'] = flow_result
            immediate.append(enriched)

    return immediate


# Example usage
if __name__ == "__main__":
    # Test data
    test_opportunities = [
        {"id": "1", "value": 1000, "platform": "github", "created_at": "2020-01-01T00:00:00Z",
         "url": "https://github.com/test/repo/issues/123"},
        {"id": "2", "value": 2000, "platform": "upwork", "created_at": "2025-12-01T00:00:00Z"},
        {"id": "3", "value": 50000000, "platform": "reddit", "created_at": "2025-12-23T00:00:00Z",
         "source_data": {"subreddit": "sheincodeShare"}},  # Non-monetizable
        {"id": "4", "value": 3000, "platform": "hackernews", "created_at": "2024-01-01T00:00:00Z"},  # Stale
        {"id": "5", "value": 500, "platform": "reddit", 
         "url": "https://reddit.com/r/forhire/comments/abc123/hiring_developer/",
         "source_data": {"subreddit": "forhire"}, "title": "[Hiring] Developer needed"},
    ]
    
    test_routing = {
        "user_routed": {
            "opportunities": [
                {
                    "opportunity": test_opportunities[4],
                    "routing": {
                        "execution_score": {
                            "win_probability": 0.8,
                            "expected_value": 400,
                            "recommendation": "EXECUTE"
                        },
                        "economics": {"aigentsy_fee": 14}
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
                            "win_probability": 0.7,
                            "expected_value": 700,
                            "recommendation": "EXECUTE"
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
    print("TESTING OPPORTUNITY FILTERS (WITH MONETIZABILITY)")
    print("=" * 80)
    
    result = filter_opportunities(test_opportunities, test_routing)
    
    print("\nFILTER STATS:")
    print(f"  Total opportunities: {result['filter_stats']['total_opportunities']}")
    print(f"  Outliers removed: {result['filter_stats']['outliers_removed']}")
    print(f"  Skipped removed: {result['filter_stats']['skipped_removed']}")
    print(f"  Stale removed: {result['filter_stats']['stale_removed']}")
    print(f"  Non-monetizable removed: {result['filter_stats']['non_monetizable_removed']}")
    print(f"  Non-actionable removed: {result['filter_stats']['non_actionable_removed']}")
    print(f"  Remaining: {result['filter_stats']['remaining_opportunities']}")
    print(f"  P95 cap: ${result['filter_stats']['p95_cap']:,.0f}")
    print(f"  Total value before: ${result['filter_stats']['total_value_before']:,.0f}")
    print(f"  Total value after: ${result['filter_stats']['total_value_after']:,.0f}")
    
    print("\nFILTER REASONS (sample):")
    for reason in result['filter_stats'].get('filter_reasons', [])[:5]:
        print(f"  - {reason['id']}: {reason['reason']}")
    
    print("\nFILTERED RESULTS:")
    print(f"  User-routed: {result['filtered_routing']['user_routed']['count']} opportunities")
    print(f"  AiGentsy-routed: {result['filtered_routing']['aigentsy_routed']['count']} opportunities")
    print(f"  Held: {result['filtered_routing']['held']['count']} opportunities")
    
    # Test execution target extraction
    print("\nEXECUTION TARGETS:")
    for opp in test_opportunities:
        target = extract_execution_target(opp)
        print(f"  - {opp['id']} ({opp['platform']}): {target['method']} -> {target['details']}")
    
    # Test execute now
    execute_now = get_execute_now_opportunities(result['filtered_routing'])
    print(f"\nEXECUTE NOW: {len(execute_now)} opportunities")
    for opp in execute_now:
        print(f"  - {opp['opportunity']['id']}: {opp['reason']}")
