"""
EXECUTION SIMILARITY: Learn from Similar Past Executions
=========================================================

Find and learn from similar past executions to:
- Predict success likelihood
- Estimate accurate timing
- Reuse successful patterns
- Avoid past mistakes

Updated: Jan 2026
"""

import logging
import hashlib
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class ExecutionRecord:
    """Record of a past execution"""
    id: str
    opportunity_id: str
    pack: str
    platform: str
    budget_usd: float
    title: str
    description: str
    tags: List[str] = field(default_factory=list)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_minutes: int = 0
    success: bool = False
    artifacts: List[str] = field(default_factory=list)
    error: Optional[str] = None
    learnings: List[str] = field(default_factory=list)

    # Similarity features
    feature_vector: List[float] = field(default_factory=list)


@dataclass
class SimilarityMatch:
    """A match to a similar past execution"""
    execution: ExecutionRecord
    similarity_score: float
    matching_factors: List[str]
    learnings: List[str]


class ExecutionSimilarityEngine:
    """
    Find similar past executions and extract learnings.

    Similarity Factors:
    1. Pack type (exact match)
    2. Platform (exact or category match)
    3. Budget range (within 50%)
    4. Title/description (keyword overlap)
    5. Tags (Jaccard similarity)
    6. Success outcome (for filtering)
    """

    # Budget buckets for similarity
    BUDGET_BUCKETS = [
        (0, 100, 'micro'),
        (100, 500, 'small'),
        (500, 2000, 'medium'),
        (2000, 10000, 'large'),
        (10000, float('inf'), 'enterprise'),
    ]

    # Platform categories
    PLATFORM_CATEGORIES = {
        'freelance': ['upwork', 'fiverr', 'toptal', 'freelancer'],
        'jobs': ['linkedin', 'indeed', 'weworkremotely', 'remoteok'],
        'social': ['twitter', 'instagram', 'facebook', 'tiktok'],
        'enterprise': ['salesforce', 'hubspot'],
    }

    def __init__(self):
        self.executions: Dict[str, ExecutionRecord] = {}
        self.by_pack: Dict[str, List[str]] = defaultdict(list)
        self.by_platform: Dict[str, List[str]] = defaultdict(list)
        self.by_budget_bucket: Dict[str, List[str]] = defaultdict(list)
        self.stats = {
            'executions_recorded': 0,
            'similarity_queries': 0,
            'learnings_applied': 0,
            'avg_similarity_score': 0.0,
        }

    def record_execution(
        self,
        opportunity_id: str,
        pack: str,
        platform: str,
        budget_usd: float,
        title: str,
        description: str = "",
        tags: List[str] = None,
        success: bool = False,
        duration_minutes: int = 0,
        artifacts: List[str] = None,
        error: str = None,
        learnings: List[str] = None,
    ) -> ExecutionRecord:
        """
        Record an execution for future similarity matching.
        """
        exec_id = f"exec_{hashlib.md5(f'{opportunity_id}_{datetime.now().isoformat()}'.encode()).hexdigest()[:12]}"

        record = ExecutionRecord(
            id=exec_id,
            opportunity_id=opportunity_id,
            pack=pack,
            platform=platform.lower(),
            budget_usd=budget_usd,
            title=title,
            description=description,
            tags=tags or [],
            started_at=datetime.now(timezone.utc).isoformat(),
            success=success,
            duration_minutes=duration_minutes,
            artifacts=artifacts or [],
            error=error,
            learnings=learnings or [],
        )

        # Compute feature vector
        record.feature_vector = self._compute_features(record)

        # Store and index
        self.executions[exec_id] = record
        self.by_pack[pack].append(exec_id)
        self.by_platform[platform.lower()].append(exec_id)

        budget_bucket = self._get_budget_bucket(budget_usd)
        self.by_budget_bucket[budget_bucket].append(exec_id)

        self.stats['executions_recorded'] += 1

        logger.info(f"Recorded execution: {exec_id} ({pack}/{platform})")

        return record

    def _compute_features(self, record: ExecutionRecord) -> List[float]:
        """Compute feature vector for similarity matching"""
        features = []

        # Budget normalized (0-1 scale, log)
        import math
        features.append(math.log1p(record.budget_usd) / 10.0)

        # Pack one-hot (simplified)
        pack_map = {'web_dev': 0, 'mobile_dev': 1, 'design': 2, 'content': 3, 'devops': 4}
        pack_idx = pack_map.get(record.pack, 5)
        features.extend([1.0 if i == pack_idx else 0.0 for i in range(6)])

        # Platform category one-hot
        platform_cat = self._get_platform_category(record.platform)
        cat_map = {'freelance': 0, 'jobs': 1, 'social': 2, 'enterprise': 3, 'other': 4}
        cat_idx = cat_map.get(platform_cat, 4)
        features.extend([1.0 if i == cat_idx else 0.0 for i in range(5)])

        return features

    def _get_budget_bucket(self, budget: float) -> str:
        """Get budget bucket label"""
        for min_val, max_val, label in self.BUDGET_BUCKETS:
            if min_val <= budget < max_val:
                return label
        return 'enterprise'

    def _get_platform_category(self, platform: str) -> str:
        """Get platform category"""
        platform = platform.lower()
        for category, platforms in self.PLATFORM_CATEGORIES.items():
            if platform in platforms or any(p in platform for p in platforms):
                return category
        return 'other'

    def find_similar(
        self,
        pack: str,
        platform: str,
        budget_usd: float,
        title: str,
        description: str = "",
        tags: List[str] = None,
        limit: int = 5,
        min_similarity: float = 0.5,
        success_only: bool = False,
    ) -> List[SimilarityMatch]:
        """
        Find similar past executions.

        Args:
            pack: Service pack type
            platform: Source platform
            budget_usd: Budget amount
            title: Opportunity title
            description: Opportunity description
            tags: Tags to match
            limit: Max results to return
            min_similarity: Minimum similarity score
            success_only: Only return successful executions

        Returns:
            List of SimilarityMatch objects
        """
        self.stats['similarity_queries'] += 1
        tags = tags or []

        # Create query record for feature comparison
        query_features = self._compute_features(ExecutionRecord(
            id='query',
            opportunity_id='query',
            pack=pack,
            platform=platform,
            budget_usd=budget_usd,
            title=title,
            description=description,
            tags=tags,
        ))

        # Get candidate executions (same pack first)
        candidates = []
        for exec_id in self.by_pack.get(pack, []):
            candidates.append(self.executions[exec_id])

        # Also check similar packs
        similar_packs = {
            'web_dev': ['mobile_dev', 'design'],
            'mobile_dev': ['web_dev'],
            'design': ['web_dev', 'content'],
            'content': ['design'],
            'devops': ['web_dev'],
        }
        for similar_pack in similar_packs.get(pack, []):
            for exec_id in self.by_pack.get(similar_pack, [])[:10]:
                candidates.append(self.executions[exec_id])

        if not candidates:
            return []

        # Score candidates
        matches = []
        for candidate in candidates:
            if success_only and not candidate.success:
                continue

            score, factors = self._compute_similarity(
                query_features=query_features,
                query_title=title,
                query_description=description,
                query_tags=tags,
                query_budget=budget_usd,
                query_platform=platform,
                candidate=candidate,
            )

            if score >= min_similarity:
                matches.append(SimilarityMatch(
                    execution=candidate,
                    similarity_score=score,
                    matching_factors=factors,
                    learnings=candidate.learnings,
                ))

        # Sort by similarity
        matches.sort(key=lambda m: m.similarity_score, reverse=True)

        # Update stats
        if matches:
            avg = sum(m.similarity_score for m in matches[:limit]) / min(len(matches), limit)
            self.stats['avg_similarity_score'] = (
                self.stats['avg_similarity_score'] * 0.9 + avg * 0.1
            )

        return matches[:limit]

    def _compute_similarity(
        self,
        query_features: List[float],
        query_title: str,
        query_description: str,
        query_tags: List[str],
        query_budget: float,
        query_platform: str,
        candidate: ExecutionRecord,
    ) -> Tuple[float, List[str]]:
        """Compute similarity score between query and candidate"""
        factors = []
        scores = []

        # 1. Feature vector cosine similarity (0.3 weight)
        if query_features and candidate.feature_vector:
            dot = sum(a * b for a, b in zip(query_features, candidate.feature_vector))
            mag_q = sum(a * a for a in query_features) ** 0.5
            mag_c = sum(a * a for a in candidate.feature_vector) ** 0.5
            if mag_q > 0 and mag_c > 0:
                cosine = dot / (mag_q * mag_c)
                scores.append(('features', cosine, 0.3))
                if cosine > 0.8:
                    factors.append('similar_features')

        # 2. Title keyword overlap (0.25 weight)
        title_overlap = self._keyword_overlap(query_title, candidate.title)
        scores.append(('title', title_overlap, 0.25))
        if title_overlap > 0.5:
            factors.append('similar_title')

        # 3. Budget proximity (0.2 weight)
        budget_ratio = min(query_budget, candidate.budget_usd) / max(query_budget, candidate.budget_usd, 1)
        scores.append(('budget', budget_ratio, 0.2))
        if budget_ratio > 0.7:
            factors.append('similar_budget')

        # 4. Tag overlap (0.15 weight)
        tag_overlap = self._jaccard_similarity(query_tags, candidate.tags)
        scores.append(('tags', tag_overlap, 0.15))
        if tag_overlap > 0.3:
            factors.append('matching_tags')

        # 5. Platform match (0.1 weight)
        platform_score = 1.0 if query_platform.lower() == candidate.platform else 0.5
        if self._get_platform_category(query_platform) == self._get_platform_category(candidate.platform):
            platform_score = max(platform_score, 0.7)
            factors.append('same_platform_category')
        scores.append(('platform', platform_score, 0.1))

        # Weighted average
        total_score = sum(score * weight for _, score, weight in scores)

        return total_score, factors

    def _keyword_overlap(self, text1: str, text2: str) -> float:
        """Compute keyword overlap between two texts"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        # Remove stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'is', 'are'}
        words1 = words1 - stop_words
        words2 = words2 - stop_words

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0

    def _jaccard_similarity(self, set1: List, set2: List) -> float:
        """Compute Jaccard similarity between two sets"""
        s1 = set(s.lower() for s in set1)
        s2 = set(s.lower() for s in set2)

        if not s1 or not s2:
            return 0.0

        intersection = s1 & s2
        union = s1 | s2

        return len(intersection) / len(union) if union else 0.0

    def get_learnings_for_opportunity(
        self,
        pack: str,
        platform: str,
        budget_usd: float,
        title: str,
    ) -> Dict[str, Any]:
        """
        Get aggregated learnings for an opportunity.

        Returns insights from similar past executions.
        """
        similar = self.find_similar(
            pack=pack,
            platform=platform,
            budget_usd=budget_usd,
            title=title,
            limit=10,
            min_similarity=0.4,
        )

        if not similar:
            return {
                'found_similar': False,
                'message': 'No similar past executions found',
            }

        # Aggregate learnings
        all_learnings = []
        success_rate = 0
        avg_duration = 0
        common_errors = []

        for match in similar:
            all_learnings.extend(match.learnings)
            if match.execution.success:
                success_rate += 1
            if match.execution.duration_minutes > 0:
                avg_duration += match.execution.duration_minutes
            if match.execution.error:
                common_errors.append(match.execution.error)

        n = len(similar)
        success_rate = success_rate / n if n > 0 else 0
        avg_duration = avg_duration / n if n > 0 else 0

        # Deduplicate learnings
        unique_learnings = list(set(all_learnings))[:5]

        self.stats['learnings_applied'] += 1

        return {
            'found_similar': True,
            'similar_count': len(similar),
            'top_match': {
                'id': similar[0].execution.id,
                'similarity': similar[0].similarity_score,
                'factors': similar[0].matching_factors,
            },
            'predicted_success_rate': round(success_rate, 2),
            'predicted_duration_minutes': round(avg_duration),
            'learnings': unique_learnings,
            'common_errors': list(set(common_errors))[:3],
            'recommendation': self._generate_recommendation(success_rate, unique_learnings),
        }

    def _generate_recommendation(
        self,
        success_rate: float,
        learnings: List[str],
    ) -> str:
        """Generate recommendation based on learnings"""
        if success_rate >= 0.8:
            return "High confidence - similar executions have strong success rate"
        elif success_rate >= 0.5:
            return "Moderate confidence - review learnings before proceeding"
        else:
            return "Low confidence - consider additional validation or scope adjustment"

    def add_learning(self, execution_id: str, learning: str) -> bool:
        """Add learning to an execution"""
        execution = self.executions.get(execution_id)
        if not execution:
            return False

        execution.learnings.append(learning)
        return True

    def mark_complete(
        self,
        execution_id: str,
        success: bool,
        duration_minutes: int = 0,
        artifacts: List[str] = None,
        error: str = None,
    ) -> bool:
        """Mark execution as complete"""
        execution = self.executions.get(execution_id)
        if not execution:
            return False

        execution.completed_at = datetime.now(timezone.utc).isoformat()
        execution.success = success
        execution.duration_minutes = duration_minutes
        if artifacts:
            execution.artifacts.extend(artifacts)
        execution.error = error

        return True

    def get_stats(self) -> Dict[str, Any]:
        """Get engine stats"""
        return {
            **self.stats,
            'total_executions': len(self.executions),
            'success_rate': sum(1 for e in self.executions.values() if e.success) / max(1, len(self.executions)),
            'packs_covered': list(self.by_pack.keys()),
        }


# Singleton
_similarity_engine: Optional[ExecutionSimilarityEngine] = None


def get_execution_similarity() -> ExecutionSimilarityEngine:
    """Get or create execution similarity engine"""
    global _similarity_engine
    if _similarity_engine is None:
        _similarity_engine = ExecutionSimilarityEngine()
    return _similarity_engine
