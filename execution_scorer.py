"""
EXECUTION SCORER
Calculates win probability for each opportunity before engagement
Factors: urgency, competition, value, capability, source type
"""

from datetime import datetime
from typing import Dict, Any, Optional
import json

class ExecutionScorer:
    """
    Scores opportunities based on likelihood of successful execution
    Higher score = higher probability of winning and delivering
    """
    
    def __init__(self):
        # Competition levels by platform
        self.competition_multipliers = {
            'github': 0.4,              # High competition (public issues)
            'upwork': 0.5,              # High competition (many bidders)
            'reddit': 0.6,              # Medium competition
            'hackernews': 0.7,          # Medium-low competition
            'twitter': 0.8,             # Low competition
            'proactive_outreach': 1.8,  # Very low competition (we found them)
            'internal_network': 1.5,    # Low competition (referrals)
            'predictive': 1.6           # Low competition (ahead of market)
        }
        
        # Urgency impact on execution difficulty
        self.urgency_multipliers = {
            'low': 1.0,
            'medium': 0.85,
            'high': 0.7,
            'critical': 0.6
        }
        
        # Historical conversion rates by opportunity type
        self.conversion_baselines = {
            'software_development': 0.65,
            'web_development': 0.70,
            'mobile_development': 0.60,
            'content_creation': 0.75,
            'business_consulting': 0.55,
            'data_analysis': 0.68,
            'marketing': 0.72,
            'design': 0.62,
            'default': 0.60
        }
    
    def score_opportunity(
        self, 
        opportunity: Dict[str, Any], 
        capability: Dict[str, Any],
        user_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive execution score
        
        Returns:
            {
                'win_probability': float (0-1),
                'expected_value': float,
                'risk_level': str,
                'execution_difficulty': str,
                'time_to_close_days': int,
                'confidence_factors': dict,
                'recommendation': str
            }
        """
        
        # Start with base probability
        opp_type = opportunity.get('type', 'default')
        base_score = self.conversion_baselines.get(opp_type, 0.60)
        
        # Factor 1: Competition level
        platform = opportunity.get('platform', 'unknown')
        competition_mult = self.competition_multipliers.get(platform, 0.6)
        
        # Factor 2: Urgency impact
        urgency = opportunity.get('urgency', 'medium')
        urgency_mult = self.urgency_multipliers.get(urgency, 0.85)
        
        # Factor 3: Value-based difficulty (higher value = harder close)
        value = opportunity.get('value', 1000)
        if value > 10000:
            value_mult = 0.6
        elif value > 5000:
            value_mult = 0.75
        elif value > 2000:
            value_mult = 0.9
        else:
            value_mult = 1.0
        
        # Factor 4: Capability confidence
        cap_confidence = capability.get('confidence', 0.8)
        
        # Factor 5: Source type boost (proactive vs reactive)
        source = opportunity.get('source', 'unknown')
        if source in ['opportunity_creation', 'predictive_intelligence']:
            source_boost = 1.5  # Proactive = 50% better conversion
        elif source in ['network_amplification', 'flow_arbitrage']:
            source_boost = 1.3  # Strategic = 30% better
        else:
            source_boost = 1.0
        
        # Factor 6: Time advantage (are we first?)
        created_at = opportunity.get('created_at', datetime.utcnow().isoformat())
        time_advantage = self._calculate_time_advantage(created_at, platform)
        
        # Factor 7: User match quality (if routing to user)
        user_match_mult = 1.0
        if user_data:
            user_match_mult = self._calculate_user_match(opportunity, user_data)
        
        # CALCULATE FINAL WIN PROBABILITY
        win_probability = (
            base_score * 
            competition_mult * 
            urgency_mult * 
            value_mult * 
            cap_confidence * 
            source_boost * 
            time_advantage * 
            user_match_mult
        )
        
        # Cap at 0.95 (never 100% certain)
        win_probability = min(win_probability, 0.95)
        
        # Calculate expected value
        expected_value = value * win_probability
        
        # Determine risk level
        if win_probability > 0.7:
            risk_level = 'low'
            execution_difficulty = 'easy'
        elif win_probability > 0.5:
            risk_level = 'medium'
            execution_difficulty = 'moderate'
        elif win_probability > 0.3:
            risk_level = 'high'
            execution_difficulty = 'hard'
        else:
            risk_level = 'very_high'
            execution_difficulty = 'very_hard'
        
        # Estimate time to close
        time_to_close = self._estimate_time_to_close(
            urgency, 
            value, 
            platform,
            win_probability
        )
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            win_probability,
            expected_value,
            risk_level,
            opportunity
        )
        
        return {
            'win_probability': round(win_probability, 3),
            'expected_value': round(expected_value, 2),
            'risk_level': risk_level,
            'execution_difficulty': execution_difficulty,
            'time_to_close_days': time_to_close,
            'confidence_factors': {
                'base_conversion': base_score,
                'competition_impact': competition_mult,
                'urgency_impact': urgency_mult,
                'value_impact': value_mult,
                'capability_confidence': cap_confidence,
                'source_advantage': source_boost,
                'time_advantage': time_advantage,
                'user_match': user_match_mult
            },
            'recommendation': recommendation,
            'score_timestamp': datetime.utcnow().isoformat()
        }
    
    def _calculate_time_advantage(self, created_at: str, platform: str) -> float:
        """Calculate if we're early to the opportunity"""
        try:
            created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            now = datetime.utcnow()
            hours_old = (now - created.replace(tzinfo=None)).total_seconds() / 3600
            
            # Fresh opportunities (< 6 hours) = advantage
            if hours_old < 6:
                return 1.3
            elif hours_old < 24:
                return 1.1
            elif hours_old < 72:
                return 1.0
            else:
                return 0.8  # Stale opportunities harder to win
        except:
            return 1.0
    
    def _calculate_user_match(self, opportunity: Dict, user_data: Dict) -> float:
        """Calculate how well opportunity matches user capability"""
        opp_type = opportunity.get('type', '')
        user_type = user_data.get('companyType', '')
        
        # Perfect match
        type_matches = {
            'marketing': ['marketing', 'content_creation', 'seo'],
            'software_development': ['software_development', 'web_development', 'api'],
            'consulting': ['business_consulting', 'consulting'],
            'design': ['design', 'ui_ux', 'branding']
        }
        
        for user_category, opp_types in type_matches.items():
            if user_type == user_category and opp_type in opp_types:
                return 1.4  # 40% boost for perfect match
        
        return 1.0
    
    def _estimate_time_to_close(
        self, 
        urgency: str, 
        value: float, 
        platform: str,
        win_prob: float
    ) -> int:
        """Estimate days to close deal"""
        base_days = {
            'critical': 2,
            'high': 5,
            'medium': 10,
            'low': 20
        }.get(urgency, 10)
        
        # Higher value = longer sales cycle
        if value > 10000:
            base_days *= 2
        elif value > 5000:
            base_days *= 1.5
        
        # Lower win prob = longer to close
        if win_prob < 0.4:
            base_days *= 1.5
        
        return int(base_days)
    
    def _generate_recommendation(
        self,
        win_prob: float,
        expected_value: float,
        risk_level: str,
        opportunity: Dict
    ) -> str:
        """Generate actionable recommendation"""
        
        if win_prob > 0.8 and expected_value > 2000:
            return "EXECUTE IMMEDIATELY - High probability, high value opportunity"
        
        elif win_prob > 0.6 and expected_value > 1000:
            return "EXECUTE - Good opportunity with solid expected value"
        
        elif win_prob > 0.5:
            return "CONSIDER - Moderate probability, evaluate capacity"
        
        elif win_prob > 0.3:
            return "LOW PRIORITY - Only execute if capacity available"
        
        else:
            return "SKIP - Low win probability, not worth resources"
    
    def batch_score_opportunities(
        self, 
        opportunities: list,
        capabilities: Dict[str, Any]
    ) -> list:
        """Score multiple opportunities and rank by expected value"""
        
        scored = []
        for opp in opportunities:
            # Get capability for this opportunity type
            capability = capabilities.get(
                opp.get('type', 'default'),
                {'confidence': 0.8}
            )
            
            score = self.score_opportunity(opp, capability)
            
            scored.append({
                'opportunity': opp,
                'score': score
            })
        
        # Sort by expected value (descending)
        scored.sort(key=lambda x: x['score']['expected_value'], reverse=True)
        
        return scored
    
    def get_execution_stats(self, scored_opportunities: list) -> Dict[str, Any]:
        """Calculate aggregate statistics across scored opportunities"""
        
        if not scored_opportunities:
            return {}
        
        total_count = len(scored_opportunities)
        total_value = sum(s['opportunity']['value'] for s in scored_opportunities)
        total_expected_value = sum(s['score']['expected_value'] for s in scored_opportunities)
        
        avg_win_prob = sum(s['score']['win_probability'] for s in scored_opportunities) / total_count
        
        # Count by recommendation
        recommendations = {}
        for s in scored_opportunities:
            rec = s['score']['recommendation'].split('-')[0].strip()
            recommendations[rec] = recommendations.get(rec, 0) + 1
        
        # Count by risk level
        risk_levels = {}
        for s in scored_opportunities:
            risk = s['score']['risk_level']
            risk_levels[risk] = risk_levels.get(risk, 0) + 1
        
        return {
            'total_opportunities': total_count,
            'total_value': total_value,
            'total_expected_value': round(total_expected_value, 2),
            'expected_conversion_rate': round(avg_win_prob, 3),
            'recommendations': recommendations,
            'risk_distribution': risk_levels,
            'top_10_expected_value': round(
                sum(s['score']['expected_value'] for s in scored_opportunities[:10]), 
                2
            )
        }


# Example usage
if __name__ == "__main__":
    scorer = ExecutionScorer()
    
    # Test opportunity
    test_opp = {
        'id': 'github_123',
        'platform': 'github',
        'type': 'software_development',
        'value': 5000,
        'urgency': 'high',
        'source': 'explicit_marketplace',
        'created_at': datetime.utcnow().isoformat()
    }
    
    test_capability = {
        'confidence': 0.9,
        'method': 'aigentsy_direct'
    }
    
    score = scorer.score_opportunity(test_opp, test_capability)
    print(json.dumps(score, indent=2))
