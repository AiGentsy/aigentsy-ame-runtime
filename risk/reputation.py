"""
REPUTATION SCORER: Poster Reputation Assessment

Features:
- Platform-specific reputation signals
- Account age/activity scoring
- Historical data tracking
- Reputation decay
"""

import logging
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class ReputationProfile:
    """Cached reputation profile for a poster"""
    poster_id: str
    platform: str
    reputation_score: float = 0.5
    opportunities_posted: int = 0
    opportunities_closed: int = 0
    avg_response_time: float = 0.0
    complaints: int = 0
    last_active: Optional[datetime] = None
    first_seen: Optional[datetime] = None

    def get_close_rate(self) -> float:
        if self.opportunities_posted == 0:
            return 0.5
        return self.opportunities_closed / self.opportunities_posted


class ReputationScorer:
    """
    Score poster/company reputation.

    Factors:
    - Platform-specific signals (karma, reviews, etc.)
    - Account age
    - Activity level
    - Historical close rate
    - Complaint rate
    """

    def __init__(self, config: Optional[Dict] = None):
        config = config or {}

        # Cached profiles
        self.profiles: Dict[str, ReputationProfile] = {}

        # Stats
        self.stats = {
            'scored': 0,
            'profiles_cached': 0,
        }

    def score(self, opportunity: Dict) -> float:
        """
        Score poster reputation.

        Returns:
            Reputation score 0-1
        """
        self.stats['scored'] += 1

        platform = opportunity.get('platform', '').lower()
        source_data = opportunity.get('source_data', {})

        # Start with platform baseline
        score = self._get_platform_baseline(platform)

        # Apply platform-specific signals
        if platform == 'upwork':
            score = self._score_upwork(source_data, score)
        elif platform in ['reddit', 'reddit_forhire']:
            score = self._score_reddit(source_data, score)
        elif platform in ['hackernews']:
            score = self._score_hackernews(source_data, score)
        elif platform == 'github':
            score = self._score_github(source_data, score)
        elif platform == 'linkedin':
            score = self._score_linkedin(source_data, score)
        else:
            score = self._score_generic(opportunity, score)

        # Check cached profile
        poster_id = self._get_poster_id(opportunity)
        if poster_id:
            profile = self.profiles.get(poster_id)
            if profile:
                # Blend with historical data
                score = 0.7 * score + 0.3 * profile.reputation_score

        return max(0.0, min(1.0, score))

    def _get_platform_baseline(self, platform: str) -> float:
        """Get baseline reputation score for platform"""
        baselines = {
            'upwork': 0.6,
            'toptal': 0.7,
            'freelancer': 0.5,
            'fiverr': 0.5,
            'linkedin': 0.6,
            'indeed': 0.5,
            'github': 0.6,
            'hackernews': 0.5,
            'reddit': 0.4,
            'twitter': 0.4,
            'craigslist': 0.3,
        }
        return baselines.get(platform, 0.5)

    def _score_upwork(self, source_data: Dict, base: float) -> float:
        """Score Upwork client reputation"""
        score = base

        # Client rating
        rating = source_data.get('client_rating', 0)
        if rating >= 4.5:
            score += 0.2
        elif rating >= 4.0:
            score += 0.1
        elif rating < 3.0 and rating > 0:
            score -= 0.2

        # Jobs posted
        jobs_posted = source_data.get('jobs_posted', 0)
        if jobs_posted >= 10:
            score += 0.1
        elif jobs_posted >= 5:
            score += 0.05

        # Hire rate
        hire_rate = source_data.get('hire_rate', 0)
        if hire_rate >= 0.5:
            score += 0.1
        elif hire_rate < 0.2 and hire_rate > 0:
            score -= 0.1

        # Payment verified
        if source_data.get('payment_verified'):
            score += 0.1

        return score

    def _score_reddit(self, source_data: Dict, base: float) -> float:
        """Score Reddit poster reputation"""
        score = base

        # Karma
        karma = source_data.get('score', 0)
        if karma >= 100:
            score += 0.15
        elif karma >= 10:
            score += 0.05
        elif karma < 0:
            score -= 0.1

        # Account age (from created_utc)
        created_utc = source_data.get('created_utc')
        if created_utc:
            age_days = (time.time() - created_utc) / 86400
            if age_days >= 365:
                score += 0.1
            elif age_days >= 90:
                score += 0.05
            elif age_days < 7:
                score -= 0.1

        # Comments
        comments = source_data.get('num_comments', 0)
        if comments >= 10:
            score += 0.05

        return score

    def _score_hackernews(self, source_data: Dict, base: float) -> float:
        """Score HN poster reputation"""
        score = base

        # Points
        points = source_data.get('score', 0)
        if points >= 100:
            score += 0.15
        elif points >= 10:
            score += 0.05

        # Comments
        comments = source_data.get('descendants', 0)
        if comments >= 20:
            score += 0.05

        return score

    def _score_github(self, source_data: Dict, base: float) -> float:
        """Score GitHub poster reputation"""
        score = base

        # Repo stars (if available)
        stars = source_data.get('stargazers_count', 0)
        if stars >= 100:
            score += 0.15
        elif stars >= 10:
            score += 0.05

        # Issue comments
        comments = source_data.get('comments', 0)
        if comments >= 5:
            score += 0.05

        return score

    def _score_linkedin(self, source_data: Dict, base: float) -> float:
        """Score LinkedIn poster reputation"""
        score = base

        # Connections (if available)
        connections = source_data.get('connections', 0)
        if connections >= 500:
            score += 0.1
        elif connections >= 100:
            score += 0.05

        # Company verified
        if source_data.get('company_verified'):
            score += 0.15

        return score

    def _score_generic(self, opportunity: Dict, base: float) -> float:
        """Generic reputation scoring"""
        score = base

        # Check for verification signals in text
        text = f"{opportunity.get('title', '')} {opportunity.get('body', '')}".lower()

        if 'verified' in text:
            score += 0.1
        if 'established' in text or 'years' in text:
            score += 0.05

        # Company name present
        if opportunity.get('company'):
            score += 0.05

        return score

    def _get_poster_id(self, opportunity: Dict) -> Optional[str]:
        """Get unique poster ID"""
        platform = opportunity.get('platform', '')
        source_data = opportunity.get('source_data', {})

        author = (
            source_data.get('author') or
            source_data.get('by') or
            source_data.get('user') or
            opportunity.get('company')
        )

        if author:
            return f"{platform}:{author}".lower()

        return None

    def enrich(self, opportunity: Dict) -> Dict:
        """Enrich opportunity with reputation score"""
        score = self.score(opportunity)

        if 'enrichment' not in opportunity:
            opportunity['enrichment'] = {}

        opportunity['enrichment']['poster_reputation'] = score
        opportunity['win_probability'] = score  # Legacy field

        return opportunity

    def update_profile(self, poster_id: str, outcome: str):
        """Update profile based on outcome"""
        if poster_id not in self.profiles:
            return

        profile = self.profiles[poster_id]
        profile.last_active = datetime.now(timezone.utc)

        if outcome == 'closed':
            profile.opportunities_closed += 1
            # Boost reputation
            profile.reputation_score = min(1.0, profile.reputation_score + 0.05)
        elif outcome == 'complaint':
            profile.complaints += 1
            # Reduce reputation
            profile.reputation_score = max(0.0, profile.reputation_score - 0.1)

    def get_profile(self, opportunity: Dict) -> Optional[ReputationProfile]:
        """Get reputation profile for poster"""
        poster_id = self._get_poster_id(opportunity)
        return self.profiles.get(poster_id) if poster_id else None

    def get_stats(self) -> Dict:
        """Get scorer stats"""
        return {
            **self.stats,
            'profiles_cached': len(self.profiles),
        }


# Singleton
_reputation_scorer: Optional[ReputationScorer] = None


def get_reputation_scorer() -> ReputationScorer:
    """Get or create reputation scorer instance"""
    global _reputation_scorer
    if _reputation_scorer is None:
        _reputation_scorer = ReputationScorer()
    return _reputation_scorer
