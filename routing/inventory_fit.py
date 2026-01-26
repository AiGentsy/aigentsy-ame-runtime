"""
INVENTORY FIT SCORER: Match Opportunities to Offer Packs

Features:
- Skill matching
- Category alignment
- Capacity checking
- Price range fit
"""

import logging
import re
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class OfferPack:
    """Definition of a service offering"""
    id: str
    name: str
    skills: Set[str] = field(default_factory=set)
    categories: Set[str] = field(default_factory=set)
    min_price: float = 0
    max_price: float = float('inf')
    capacity: int = 100  # Max concurrent
    current_load: int = 0
    enabled: bool = True

    def has_capacity(self) -> bool:
        return self.current_load < self.capacity

    def price_fits(self, price: Optional[float]) -> bool:
        if price is None:
            return True
        return self.min_price <= price <= self.max_price


# Default offer packs
DEFAULT_OFFER_PACKS = [
    OfferPack(
        id='web_dev',
        name='Web Development',
        skills={'javascript', 'react', 'vue', 'angular', 'nodejs', 'typescript',
                'html', 'css', 'frontend', 'backend', 'fullstack', 'web'},
        categories={'web', 'frontend', 'backend', 'fullstack'},
        min_price=500,
        max_price=50000,
    ),
    OfferPack(
        id='mobile_dev',
        name='Mobile Development',
        skills={'ios', 'android', 'swift', 'kotlin', 'react native', 'flutter',
                'mobile', 'app'},
        categories={'mobile', 'ios', 'android', 'app'},
        min_price=1000,
        max_price=100000,
    ),
    OfferPack(
        id='data_ml',
        name='Data & ML',
        skills={'python', 'machine learning', 'ml', 'ai', 'data science',
                'tensorflow', 'pytorch', 'pandas', 'data analysis', 'nlp'},
        categories={'data', 'ml', 'ai', 'analytics'},
        min_price=1000,
        max_price=100000,
    ),
    OfferPack(
        id='devops',
        name='DevOps & Cloud',
        skills={'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'devops',
                'ci/cd', 'terraform', 'cloud', 'infrastructure'},
        categories={'devops', 'cloud', 'infrastructure'},
        min_price=500,
        max_price=50000,
    ),
    OfferPack(
        id='design',
        name='Design & UX',
        skills={'ui', 'ux', 'design', 'figma', 'sketch', 'adobe', 'graphic',
                'user experience', 'user interface'},
        categories={'design', 'ui', 'ux', 'creative'},
        min_price=300,
        max_price=30000,
    ),
    OfferPack(
        id='writing',
        name='Writing & Content',
        skills={'writing', 'content', 'copywriting', 'blog', 'technical writing',
                'documentation', 'editor', 'seo'},
        categories={'writing', 'content', 'marketing'},
        min_price=100,
        max_price=10000,
    ),
    OfferPack(
        id='automation',
        name='Automation & Scripting',
        skills={'automation', 'scripting', 'python', 'selenium', 'rpa',
                'web scraping', 'bot', 'integration'},
        categories={'automation', 'integration', 'scripting'},
        min_price=200,
        max_price=20000,
    ),
]


class InventoryFitScorer:
    """
    Score opportunities by fit with available offer packs.

    Considers:
    - Skill match
    - Category alignment
    - Price range fit
    - Current capacity
    """

    def __init__(self, offer_packs: Optional[List[OfferPack]] = None):
        self.offer_packs = offer_packs or DEFAULT_OFFER_PACKS
        self.stats = {
            'scored': 0,
            'matches_found': 0,
            'no_matches': 0,
        }

    def score(self, opportunity: Dict) -> Dict[str, float]:
        """
        Score opportunity against all offer packs.

        Returns:
            Dict of pack_id -> fit_score (0-1)
        """
        self.stats['scored'] += 1

        # Extract skills and text from opportunity
        opp_skills = self._extract_skills(opportunity)
        opp_text = f"{opportunity.get('title', '')} {opportunity.get('body', '')}".lower()
        opp_price = opportunity.get('value') or opportunity.get('pricing', {}).get('estimated_value')

        scores = {}
        best_match = None
        best_score = 0.0

        for pack in self.offer_packs:
            if not pack.enabled:
                continue

            score = self._score_pack_fit(pack, opp_skills, opp_text, opp_price)
            scores[pack.id] = score

            if score > best_score:
                best_score = score
                best_match = pack.id

        if best_score > 0:
            self.stats['matches_found'] += 1
        else:
            self.stats['no_matches'] += 1

        return scores

    def get_best_match(self, opportunity: Dict) -> tuple:
        """
        Get best matching offer pack.

        Returns:
            Tuple of (pack_id, score)
        """
        scores = self.score(opportunity)

        if not scores:
            return None, 0.0

        best_id = max(scores, key=scores.get)
        return best_id, scores[best_id]

    def enrich(self, opportunity: Dict) -> Dict:
        """Enrich opportunity with inventory fit score"""
        scores = self.score(opportunity)
        best_id, best_score = self.get_best_match(opportunity)

        if 'enrichment' not in opportunity:
            opportunity['enrichment'] = {}

        opportunity['enrichment']['inventory_fit'] = best_score
        opportunity['enrichment']['inventory_scores'] = scores
        opportunity['enrichment']['best_offer_pack'] = best_id
        opportunity['inventory_fit'] = best_score  # Legacy field

        return opportunity

    def _extract_skills(self, opportunity: Dict) -> Set[str]:
        """Extract skills from opportunity"""
        skills = set()

        # From explicit skills field
        opp_skills = opportunity.get('skills', [])
        if isinstance(opp_skills, list):
            skills.update(s.lower() for s in opp_skills)

        # From enrichment
        enrichment = opportunity.get('enrichment', {})
        if enrichment.get('skills_extracted'):
            skills.update(s.lower() for s in enrichment['skills_extracted'])

        return skills

    def _score_pack_fit(
        self,
        pack: OfferPack,
        opp_skills: Set[str],
        opp_text: str,
        opp_price: Optional[float]
    ) -> float:
        """Score single pack fit"""
        score = 0.0

        # Skill match (0-0.5)
        if pack.skills and opp_skills:
            skill_overlap = len(pack.skills & opp_skills)
            skill_score = min(0.5, skill_overlap * 0.1)
            score += skill_score
        else:
            # Text-based skill detection
            skill_matches = sum(1 for skill in pack.skills if skill in opp_text)
            score += min(0.4, skill_matches * 0.08)

        # Category match (0-0.3)
        for category in pack.categories:
            if category in opp_text:
                score += 0.1
                break

        # Price fit (0-0.2)
        if pack.price_fits(opp_price):
            score += 0.2
        elif opp_price is not None:
            # Partial score if close to range
            if opp_price < pack.min_price:
                ratio = opp_price / pack.min_price
                score += 0.1 * ratio
            elif opp_price > pack.max_price:
                ratio = pack.max_price / opp_price
                score += 0.1 * ratio

        # Capacity penalty
        if not pack.has_capacity():
            score *= 0.5

        return min(1.0, score)

    def update_capacity(self, pack_id: str, delta: int):
        """Update pack capacity (e.g., when accepting job)"""
        for pack in self.offer_packs:
            if pack.id == pack_id:
                pack.current_load = max(0, pack.current_load + delta)
                break

    def get_available_packs(self) -> List[Dict]:
        """Get list of packs with capacity"""
        return [
            {
                'id': p.id,
                'name': p.name,
                'capacity_remaining': p.capacity - p.current_load,
            }
            for p in self.offer_packs
            if p.enabled and p.has_capacity()
        ]

    def get_stats(self) -> Dict:
        """Get scorer stats"""
        return {
            **self.stats,
            'offer_packs': len(self.offer_packs),
            'match_rate': self.stats['matches_found'] / max(1, self.stats['scored']),
        }


# Singleton
_inventory_scorer: Optional[InventoryFitScorer] = None


def get_inventory_scorer() -> InventoryFitScorer:
    """Get or create inventory scorer instance"""
    global _inventory_scorer
    if _inventory_scorer is None:
        _inventory_scorer = InventoryFitScorer()
    return _inventory_scorer
