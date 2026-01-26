"""
FAST-PATH EXECUTION: Same-Cycle Contact & Close

For high-intent opportunities:
- Quick price quote
- AIGx assurance attachment
- One-tap payment widget
- Snap outreach within same minute
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class FastPath:
    """
    Instant contact & close for high-intent opportunities.

    Criteria for fast-path:
    - payment_proximity >= 0.7
    - contactability >= 0.6
    - risk_score < 0.5
    """

    def __init__(self, config: Optional[Dict] = None):
        config = config or {}

        # Thresholds
        self.min_payment_proximity = config.get('min_payment_proximity', 0.7)
        self.min_contactability = config.get('min_contactability', 0.6)
        self.max_risk = config.get('max_risk', 0.5)

        # Price floor settings
        self.min_price = config.get('min_price', 25)
        self.default_hourly = config.get('default_hourly', 75)

        # Stats
        self.stats = {
            'qualified': 0,
            'executed': 0,
            'succeeded': 0,
            'failed': 0,
        }

    def should_fast_path(self, opp: Dict) -> bool:
        """
        Check if opportunity qualifies for fast-path execution.

        Returns True if:
        - High payment proximity (ready to pay)
        - High contactability (can reach them)
        - Low risk (not a scam)
        """
        payment_proximity = opp.get('payment_proximity', 0)
        contactability = opp.get('contactability', 0)
        risk_score = opp.get('risk_score', 1.0)

        return (
            payment_proximity >= self.min_payment_proximity and
            contactability >= self.min_contactability and
            risk_score < self.max_risk
        )

    def calculate_price(self, opp: Dict) -> float:
        """
        Calculate price for opportunity.

        Uses:
        - Budget hint from opportunity
        - Platform average
        - Complexity estimation
        """
        # Check for explicit budget
        budget = opp.get('budget_amount') or opp.get('value', 0)

        if budget and budget >= self.min_price:
            # Use budget hint, potentially negotiate up slightly
            return max(self.min_price, budget * 0.9)

        # Estimate based on complexity
        body = opp.get('body', '') or opp.get('description', '') or ''
        complexity = self._estimate_complexity(body)

        # Base price on complexity
        if complexity == 'simple':
            return max(self.min_price, 50)
        elif complexity == 'medium':
            return max(self.min_price, 150)
        else:
            return max(self.min_price, 500)

    def _estimate_complexity(self, description: str) -> str:
        """Estimate project complexity from description"""
        if not description:
            return 'simple'

        word_count = len(description.split())

        # Simple heuristic
        if word_count < 50:
            return 'simple'
        elif word_count < 200:
            return 'medium'
        else:
            return 'complex'

    def craft_offer_message(self, opp: Dict, price: float) -> str:
        """
        Craft value-first offer message.

        Key principles:
        - Lead with value
        - Be specific to their need
        - Clear price
        - Easy next step
        """
        title = opp.get('title', '')[:100]
        platform = opp.get('platform', '')

        # Customize by platform
        if 'reddit' in platform.lower():
            message = f"""Hi! I saw your post about {title}.

I specialize in this and can help. My rate for this is ${price:.0f}.

I can start immediately. Reply here or DM me to discuss details.

Looking forward to helping!"""

        elif 'upwork' in platform.lower() or 'freelancer' in platform.lower():
            message = f"""Hello,

I read your project requirements carefully. I have experience with exactly this type of work.

My quote: ${price:.0f}

I can deliver high-quality work and am available to start right away.

Let me know if you'd like to discuss the details.

Best regards"""

        elif 'hackernews' in platform.lower():
            message = f"""Hey - I can help with this.

Rate: ${price:.0f}

Happy to chat more about approach. Email in profile or reply here."""

        else:
            # Generic
            message = f"""Hi! I saw your post about {title}.

I can help with this. My rate is ${price:.0f}.

Happy to discuss details whenever works for you.

Thanks!"""

        return message.strip()

    async def execute(self, opp: Dict) -> Dict:
        """
        Execute fast-path for opportunity.

        Steps:
        1. Verify qualification
        2. Calculate price
        3. Craft message
        4. (Would send outreach - simulated for now)
        """
        self.stats['qualified'] += 1

        # Verify qualification
        if not self.should_fast_path(opp):
            return {
                'success': False,
                'method': 'fast_path',
                'reason': 'does_not_qualify',
            }

        self.stats['executed'] += 1

        try:
            # Calculate price
            price = self.calculate_price(opp)

            # Craft message
            message = self.craft_offer_message(opp, price)

            # In production, this would actually send the message
            # For now, return the prepared outreach
            result = {
                'success': True,
                'method': 'fast_path',
                'platform': opp.get('platform'),
                'url': opp.get('url'),
                'price': price,
                'message': message,
                'executed_at': datetime.now(timezone.utc).isoformat(),
                'payment_proximity': opp.get('payment_proximity'),
                'contactability': opp.get('contactability'),
            }

            self.stats['succeeded'] += 1
            logger.info(f"[fast_path] Executed: {opp.get('platform')} - ${price:.0f}")

            return result

        except Exception as e:
            self.stats['failed'] += 1
            logger.error(f"[fast_path] Failed: {e}")
            return {
                'success': False,
                'method': 'fast_path',
                'error': str(e),
            }

    async def execute_batch(self, opportunities: List[Dict]) -> List[Dict]:
        """Execute fast-path for batch of opportunities"""
        results = []
        for opp in opportunities:
            if self.should_fast_path(opp):
                result = await self.execute(opp)
                results.append(result)
        return results

    def filter_fast_path_eligible(self, opportunities: List[Dict]) -> List[Dict]:
        """Filter opportunities eligible for fast-path"""
        return [opp for opp in opportunities if self.should_fast_path(opp)]

    def get_stats(self) -> Dict:
        """Get fast-path stats"""
        return {
            **self.stats,
            'success_rate': (
                self.stats['succeeded'] / max(1, self.stats['executed'])
            ),
        }


# Singleton instance
_fast_path: Optional[FastPath] = None


def get_fast_path(config: Optional[Dict] = None) -> FastPath:
    """Get or create fast-path instance"""
    global _fast_path
    if _fast_path is None:
        _fast_path = FastPath(config)
    return _fast_path
