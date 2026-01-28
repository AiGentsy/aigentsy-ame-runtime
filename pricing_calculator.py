"""
AIGENTSY PRICING CALCULATOR
============================
Calculates market rates and AiGentsy pricing for opportunities.

Features:
- Market rate estimation by category/platform
- 30-40% discount calculation for AiGentsy pricing
- 50% deposit calculation
- Fulfillment type detection for messaging
"""

import random
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict


# =============================================================================
# CONSTANTS
# =============================================================================

# Market rate base prices by category (hourly rates in USD)
BASE_MARKET_RATES = {
    'development': {'base': 2500, 'hourly': 150},
    'backend': {'base': 2500, 'hourly': 150},
    'frontend': {'base': 2000, 'hourly': 125},
    'fullstack': {'base': 3500, 'hourly': 175},
    'api_integration': {'base': 1800, 'hourly': 120},
    'automation': {'base': 1500, 'hourly': 100},
    'design': {'base': 1200, 'hourly': 100},
    'landing_page': {'base': 1200, 'hourly': 100},
    'content': {'base': 800, 'hourly': 60},
    'data': {'base': 1500, 'hourly': 100},
    'marketing': {'base': 1200, 'hourly': 80},
    'mobile_app': {'base': 4000, 'hourly': 200},
    'default': {'base': 2000, 'hourly': 125}
}

# Platform multipliers (some platforms have higher rates)
PLATFORM_MULTIPLIERS = {
    'upwork': 1.0,
    'fiverr': 0.8,
    'github': 1.2,  # Bounties often pay more
    'twitter': 1.0,
    'reddit': 0.9,
    'linkedin': 1.3,  # Professional network premium
    'hackernews': 1.2,
    'default': 1.0
}

# AiGentsy discount range
AIGENTSY_DISCOUNT_MIN = 0.30  # 30% minimum discount
AIGENTSY_DISCOUNT_MAX = 0.40  # 40% maximum discount
DEPOSIT_PERCENTAGE = 0.50     # 50% deposit

# Fulfillment type names for messaging
FULFILLMENT_TYPE_NAMES = {
    'development': 'development',
    'backend': 'development',
    'frontend': 'development',
    'fullstack': 'development',
    'api_integration': 'integration',
    'automation': 'automation',
    'design': 'design',
    'landing_page': 'design',
    'content': 'content creation',
    'data': 'data analysis',
    'marketing': 'marketing',
    'mobile_app': 'development',
    'default': 'fulfillment'
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class PricingResult:
    """Complete pricing calculation result"""
    market_rate: float
    our_price: float
    discount_pct: int
    deposit_amount: float
    balance_amount: float
    savings: float
    fulfillment_type: str
    category: str
    estimated_hours: float
    delivery_time: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =============================================================================
# OPPORTUNITY TYPE DETECTION
# =============================================================================

def detect_opportunity_type(opportunity: Dict[str, Any]) -> str:
    """
    Detect the type of work from opportunity text.

    Args:
        opportunity: Opportunity dict with title, description, body, etc.

    Returns:
        Category string: 'development', 'automation', 'design', etc.
    """
    title = opportunity.get('title', '').lower()
    description = opportunity.get('description', '').lower()
    body = opportunity.get('body', '').lower()
    pain_point = opportunity.get('pain_point', '').lower()

    text = f"{title} {description} {body} {pain_point}"

    # Backend/API indicators
    if any(word in text for word in ['backend', 'api', 'database', 'server', 'node', 'python', 'django', 'flask', 'fastapi', 'express']):
        return 'backend'

    # Frontend indicators
    if any(word in text for word in ['frontend', 'react', 'vue', 'angular', 'ui', 'css', 'tailwind', 'component']):
        return 'frontend'

    # Fullstack indicators
    if any(word in text for word in ['fullstack', 'full stack', 'full-stack']):
        return 'fullstack'

    # Mobile app indicators
    if any(word in text for word in ['mobile', 'ios', 'android', 'react native', 'flutter', 'swift', 'kotlin']):
        return 'mobile_app'

    # Landing page indicators
    if any(word in text for word in ['landing', 'website', 'web page', 'homepage', 'wordpress', 'webflow']):
        return 'landing_page'

    # API integration indicators
    if any(word in text for word in ['integration', 'connect', 'webhook', 'zapier', 'third-party']):
        return 'api_integration'

    # Automation indicators
    if any(word in text for word in ['automat', 'script', 'bot', 'scraping', 'workflow', 'cron']):
        return 'automation'

    # Design indicators
    if any(word in text for word in ['design', 'figma', 'ui/ux', 'ux', 'logo', 'branding', 'graphic']):
        return 'design'

    # Content indicators
    if any(word in text for word in ['content', 'write', 'blog', 'copy', 'article', 'seo']):
        return 'content'

    # Data indicators
    if any(word in text for word in ['data', 'analyt', 'dashboard', 'report', 'visualization', 'bi', 'tableau']):
        return 'data'

    # Marketing indicators
    if any(word in text for word in ['marketing', 'campaign', 'ads', 'ppc', 'social media', 'growth']):
        return 'marketing'

    # General development fallback
    if any(word in text for word in ['develop', 'code', 'build', 'app', 'software', 'program']):
        return 'development'

    return 'default'


def get_fulfillment_type_name(category: str) -> str:
    """
    Get human-readable fulfillment type for messaging.

    Args:
        category: Category string from detect_opportunity_type()

    Returns:
        Friendly name like 'development', 'automation', 'design', etc.
    """
    return FULFILLMENT_TYPE_NAMES.get(category, 'fulfillment')


# =============================================================================
# COMPLEXITY ESTIMATION
# =============================================================================

def estimate_complexity(opportunity: Dict[str, Any]) -> Tuple[float, str]:
    """
    Estimate hours needed and complexity level.

    Args:
        opportunity: Opportunity dict

    Returns:
        Tuple of (estimated_hours, complexity_level)
    """
    title = opportunity.get('title', '').lower()
    description = opportunity.get('description', '').lower()
    body = opportunity.get('body', '').lower()

    text = f"{title} {description} {body}"

    # Simple indicators (1 hour)
    if any(word in text for word in ['simple', 'basic', 'quick', 'small', 'minor', 'tweak', 'fix bug']):
        return 1.0, 'simple'

    # Complex indicators (3 hours)
    if any(word in text for word in ['complex', 'advanced', 'multiple', 'integration', 'system', 'architecture', 'scalable', 'enterprise']):
        return 3.0, 'complex'

    # Default medium complexity (2 hours)
    return 2.0, 'medium'


# =============================================================================
# MARKET RATE CALCULATION
# =============================================================================

def calculate_market_rate(
    opportunity: Dict[str, Any],
    estimated_hours: Optional[float] = None
) -> float:
    """
    Calculate market rate for an opportunity.

    Uses:
    1. Base market rates by category
    2. Platform multiplier
    3. Complexity signals

    Args:
        opportunity: Opportunity dict
        estimated_hours: Override for hours (auto-detected if not provided)

    Returns:
        Market rate in USD
    """
    # Detect category
    category = detect_opportunity_type(opportunity)

    # Get base rate config
    rate_config = BASE_MARKET_RATES.get(category, BASE_MARKET_RATES['default'])

    # Estimate hours if not provided
    if estimated_hours is None:
        estimated_hours, _ = estimate_complexity(opportunity)

    # Get platform multiplier
    platform = opportunity.get('platform', '').lower()
    source = opportunity.get('source', '').lower()
    platform_key = platform or source or 'default'
    platform_mult = PLATFORM_MULTIPLIERS.get(platform_key, PLATFORM_MULTIPLIERS['default'])

    # Calculate market rate
    # Market rate = base + (hourly * hours * 2) - freelancers typically pad hours
    market_rate = rate_config['base'] + (rate_config['hourly'] * estimated_hours * 2)

    # Apply platform multiplier
    market_rate = market_rate * platform_mult

    return round(market_rate, 0)


# =============================================================================
# AIGENTSY PRICE CALCULATION
# =============================================================================

def calculate_aigentsy_price(
    market_rate: float,
    reputation_score: float = 0.5
) -> Tuple[float, int]:
    """
    Calculate AiGentsy price (30-40% below market).

    Higher reputation = smaller discount (closer to 30%)
    Lower reputation = larger discount (closer to 40%)

    Args:
        market_rate: Market rate in USD
        reputation_score: 0-1 score (higher = better reputation)

    Returns:
        Tuple of (our_price, discount_percentage)
    """
    # Scale discount based on reputation (inverted - higher rep = smaller discount)
    discount = AIGENTSY_DISCOUNT_MAX - (reputation_score * (AIGENTSY_DISCOUNT_MAX - AIGENTSY_DISCOUNT_MIN))

    # Calculate our price
    our_price = market_rate * (1 - discount)
    discount_pct = int(discount * 100)

    return round(our_price, 0), discount_pct


# =============================================================================
# FULL PRICING CALCULATION
# =============================================================================

def calculate_full_pricing(
    opportunity: Dict[str, Any],
    estimated_hours: Optional[float] = None,
    reputation_score: float = 0.5
) -> PricingResult:
    """
    Calculate complete pricing for an opportunity.

    Args:
        opportunity: Opportunity dict with title, description, etc.
        estimated_hours: Override for hours (auto-detected if not provided)
        reputation_score: 0-1 reputation score for discount calculation

    Returns:
        PricingResult with all pricing details
    """
    # Detect category
    category = detect_opportunity_type(opportunity)
    fulfillment_type = get_fulfillment_type_name(category)

    # Estimate complexity
    if estimated_hours is None:
        estimated_hours, _ = estimate_complexity(opportunity)

    # Calculate market rate
    market_rate = calculate_market_rate(opportunity, estimated_hours)

    # Calculate our price
    our_price, discount_pct = calculate_aigentsy_price(market_rate, reputation_score)

    # Calculate deposit and balance
    deposit = round(our_price * DEPOSIT_PERCENTAGE, 0)
    balance = our_price - deposit
    savings = market_rate - our_price

    # Build delivery time string
    delivery_time = f"{int(estimated_hours)}-{int(estimated_hours) + 1} hours"

    return PricingResult(
        market_rate=market_rate,
        our_price=our_price,
        discount_pct=discount_pct,
        deposit_amount=deposit,
        balance_amount=balance,
        savings=savings,
        fulfillment_type=fulfillment_type,
        category=category,
        estimated_hours=estimated_hours,
        delivery_time=delivery_time
    )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def format_pricing_for_message(pricing: PricingResult) -> Dict[str, str]:
    """
    Format pricing for use in message templates.

    Returns dict with formatted strings ready for interpolation.
    """
    return {
        'market_rate': f"${int(pricing.market_rate):,}",
        'our_price': f"${int(pricing.our_price):,}",
        'discount_pct': f"{pricing.discount_pct}%",
        'deposit_amount': f"${int(pricing.deposit_amount):,}",
        'savings': f"${int(pricing.savings):,}",
        'delivery_time': pricing.delivery_time,
        'fulfillment_type': pricing.fulfillment_type,
        'price_comparison': f"Market ${int(pricing.market_rate):,} → Your AiGentsy ${int(pricing.our_price):,} ({pricing.discount_pct}% less)"
    }


def get_pricing_from_value(
    estimated_value: float,
    category: str = 'default'
) -> PricingResult:
    """
    Calculate pricing from a pre-estimated value.

    Useful when the opportunity already has an estimated value
    and we just need to calculate market rate and discount.

    Args:
        estimated_value: Pre-estimated value in USD
        category: Category string

    Returns:
        PricingResult
    """
    # Use the estimated value as our price, back-calculate market rate
    our_price = estimated_value

    # Assume 35% discount (middle of range) to calculate market rate
    market_rate = our_price / (1 - 0.35)
    discount_pct = 35

    # Calculate deposit and balance
    deposit = round(our_price * DEPOSIT_PERCENTAGE, 0)
    balance = our_price - deposit
    savings = market_rate - our_price

    fulfillment_type = get_fulfillment_type_name(category)

    return PricingResult(
        market_rate=round(market_rate, 0),
        our_price=round(our_price, 0),
        discount_pct=discount_pct,
        deposit_amount=deposit,
        balance_amount=balance,
        savings=round(savings, 0),
        fulfillment_type=fulfillment_type,
        category=category,
        estimated_hours=2.0,
        delivery_time="1-2 hours"
    )


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("AIGENTSY PRICING CALCULATOR - TEST")
    print("=" * 70)

    # Test opportunities
    test_opportunities = [
        {
            'title': 'Need backend API development',
            'description': 'Build a REST API with authentication',
            'platform': 'upwork'
        },
        {
            'title': 'Simple landing page needed',
            'description': 'Quick WordPress landing page',
            'platform': 'fiverr'
        },
        {
            'title': 'Complex data pipeline automation',
            'description': 'Build scalable ETL system with multiple integrations',
            'platform': 'linkedin'
        },
        {
            'title': 'React component development',
            'description': 'Build reusable UI components',
            'platform': 'github'
        }
    ]

    for opp in test_opportunities:
        print(f"\n{'─' * 60}")
        print(f"Title: {opp['title']}")
        print(f"Platform: {opp['platform']}")

        pricing = calculate_full_pricing(opp)
        formatted = format_pricing_for_message(pricing)

        print(f"\nCategory: {pricing.category}")
        print(f"Fulfillment Type: {pricing.fulfillment_type}")
        print(f"Estimated Hours: {pricing.estimated_hours}")
        print(f"\n{formatted['price_comparison']}")
        print(f"Deposit: {formatted['deposit_amount']}")
        print(f"Savings: {formatted['savings']}")
        print(f"Delivery: {formatted['delivery_time']}")

    print(f"\n{'=' * 70}")
    print("Tests complete!")
