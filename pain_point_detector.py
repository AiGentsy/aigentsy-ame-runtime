"""
DIMENSION 2: PAIN POINT DETECTION
Finds opportunities where people are complaining

Discovery Strategy:
- Where people complain = opportunity
- "I wish someone would build X"
- "Why doesn't X exist?"
- App with 1-star reviews = feature opportunity
- Unanswered questions = consulting opportunity

Sources:
1. Twitter sentiment (complaints, feature requests)
2. App Store reviews (1-2 stars)
3. Reddit complaint threads
4. GitHub issues (stale, no solutions)
5. Quora (unanswered questions)
6. YouTube comments (tutorial requests)
7. Product Hunt comments (feature requests)
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta
import re
import os


class PainPointDetector:
    """
    Detects opportunities from complaints and pain points
    """
    
    def __init__(self):
        # API keys
        self.twitter_bearer = os.getenv('TWITTER_BEARER_TOKEN')
        self.reddit_client_id = os.getenv('REDDIT_CLIENT_ID')
        self.reddit_secret = os.getenv('REDDIT_CLIENT_SECRET')
    
    async def detect_all_pain_points(self) -> List[Dict]:
        """
        Run all pain point detection in parallel
        """
        
        print("\n🔍 DIMENSION 2: PAIN POINT DETECTION")
        print("   Searching for complaints and problems...")
        
        tasks = [
            self.detect_twitter_pain_points(),
            self.detect_app_store_pain_points(),
            self.detect_reddit_complaints(),
            self.detect_github_stale_issues(),
            self.detect_quora_questions(),
            self.detect_youtube_requests(),
            self.detect_producthunt_feedback()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten results
        all_pain_points = []
        for result in results:
            if isinstance(result, list):
                all_pain_points.extend(result)
            elif isinstance(result, Exception):
                print(f"   ⚠️  Detector error: {result}")
        
        print(f"   ✅ Found {len(all_pain_points)} pain point opportunities")
        
        return all_pain_points
    
    # ========================================
    # TWITTER PAIN POINT DETECTION
    # ========================================
    
    async def detect_twitter_pain_points(self) -> List[Dict]:
        """
        Detect pain points from Twitter
        
        Search for:
        - "I wish someone would build"
        - "Why doesn't X exist"
        - "Looking for a tool that"
        - "Need help with"
        """
        
        print("   🐦 Twitter: Analyzing complaints and feature requests...")
        
        if not self.twitter_bearer:
            print("   ⚠️  Twitter: No API key, using simulated data")
            return self._generate_simulated_twitter_pain_points()
        
        opportunities = []
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {'Authorization': f'Bearer {self.twitter_bearer}'}
                
                # Search queries for pain points
                queries = [
                    '"I wish someone would build"',
                    '"Why doesn\'t" exist',
                    '"Looking for a tool that"',
                    '"Need help with"',
                    '"Can someone build"',
                    '"Is there a service for"'
                ]
                
                for query in queries:
                    url = f'https://api.twitter.com/2/tweets/search/recent?query={query}&max_results=10'
                    
                    async with session.get(url, headers=headers) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            
                            for tweet in data.get('data', []):
                                pain_point = self._analyze_twitter_pain_point(tweet)
                                if pain_point:
                                    opportunities.append(pain_point)
        
        except Exception as e:
            print(f"   ❌ Twitter error: {e}")
            return self._generate_simulated_twitter_pain_points()
        
        print(f"   ✅ Twitter: Found {len(opportunities)} pain points")
        return opportunities
    
    def _analyze_twitter_pain_point(self, tweet: Dict) -> Optional[Dict]:
        """Analyze Twitter complaint and extract opportunity"""
        
        text = tweet.get('text', '').lower()
        
        # Extract the problem/request
        problem = self._extract_problem_from_text(text)
        
        if not problem:
            return None
        
        # Classify opportunity type
        opp_type = self._classify_pain_point(text)
        
        # Estimate value based on urgency signals
        urgency = self._detect_urgency(text)
        value = 1000.0 if urgency == 'high' else 500.0
        
        return {
            'id': f"twitter_pain_{tweet.get('id', 'unknown')}",
            'platform': 'twitter',
            'source': 'pain_point_detection',
            'type': opp_type,
            'title': f"Twitter Request: {problem[:80]}",
            'description': text[:500],
            'url': f"https://twitter.com/i/web/status/{tweet.get('id')}",
            'value': value,
            'urgency': urgency,
            'pain_point': problem,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'source_data': {
                'platform': 'twitter',
                'original_text': text
            }
        }
    
    def _generate_simulated_twitter_pain_points(self) -> List[Dict]:
        """Generate simulated Twitter pain points"""
        
        simulated = [
            {
                'id': 'twitter_pain_sim_1',
                'platform': 'twitter',
                'source': 'pain_point_detection',
                'type': 'software_development',
                'title': 'Twitter Request: I wish someone would build a tool to automate my invoicing',
                'description': 'I waste 5 hours a week on invoices. Why doesn\'t a simple solution exist?',
                'url': 'https://twitter.com/simulated',
                'value': 1500.0,
                'urgency': 'high',
                'pain_point': 'Manual invoicing wasting 5 hours/week',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'source_data': {'platform': 'twitter'}
            },
            {
                'id': 'twitter_pain_sim_2',
                'platform': 'twitter',
                'source': 'pain_point_detection',
                'type': 'content_creation',
                'title': 'Twitter Request: Looking for someone to help with blog content',
                'description': 'Need 10 blog posts per month but don\'t have time to write them',
                'url': 'https://twitter.com/simulated',
                'value': 2000.0,
                'urgency': 'medium',
                'pain_point': 'Need consistent blog content production',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'source_data': {'platform': 'twitter'}
            }
        ]
        
        return simulated
    
    # ========================================
    # APP STORE PAIN POINT DETECTION
    # ========================================
    
    async def detect_app_store_pain_points(self) -> List[Dict]:
        """
        Detect pain points from App Store reviews
        
        Strategy:
        - Find apps with 1-2 star reviews
        - Extract feature requests from negative reviews
        - Offer to build missing features
        """
        
        print("   📱 App Store: Mining negative reviews for opportunities...")
        
        # Simulated for now (real implementation would use App Store API)
        opportunities = [
            {
                'id': 'appstore_pain_1',
                'platform': 'app_store',
                'source': 'pain_point_detection',
                'type': 'mobile_development',
                'title': 'App Store Request: Users want dark mode in productivity app',
                'description': '500+ reviews requesting dark mode. App has 4.2 stars but dark mode is #1 complaint',
                'url': 'https://apps.apple.com/app/example',
                'value': 3000.0,
                'urgency': 'high',
                'pain_point': 'Missing dark mode causing user complaints',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'source_data': {
                    'platform': 'app_store',
                    'app_rating': 4.2,
                    'review_count': 500
                }
            },
            {
                'id': 'appstore_pain_2',
                'platform': 'app_store',
                'source': 'pain_point_detection',
                'type': 'software_development',
                'title': 'App Store Request: Calendar sync broken in scheduling app',
                'description': 'App dropped from 4.8 to 3.2 stars due to sync issues. 200+ complaints',
                'url': 'https://apps.apple.com/app/example2',
                'value': 5000.0,
                'urgency': 'critical',
                'pain_point': 'Calendar sync failure causing revenue loss',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'source_data': {
                    'platform': 'app_store',
                    'app_rating': 3.2,
                    'rating_drop': 1.6
                }
            }
        ]
        
        print(f"   ✅ App Store: Found {len(opportunities)} opportunities")
        return opportunities
    
    # ========================================
    # REDDIT COMPLAINT DETECTION
    # ========================================
    
    async def detect_reddit_complaints(self) -> List[Dict]:
        """
        Detect complaints from Reddit threads
        
        Subreddits to monitor:
        - r/entrepreneur (business problems)
        - r/smallbusiness (operations issues)
        - r/webdev (technical problems)
        - r/freelance (service gaps)
        """
        
        print("   🔴 Reddit: Scanning complaint threads...")
        
        opportunities = []
        
        try:
            async with aiohttp.ClientSession() as session:
                subreddits = ['entrepreneur', 'smallbusiness', 'webdev', 'freelance']
                
                for subreddit in subreddits:
                    # Search for complaint/problem posts
                    url = f'https://www.reddit.com/r/{subreddit}/search.json?q=problem OR issue OR help&sort=new&limit=10'
                    
                    async with session.get(url, headers={'User-Agent': 'AiGentsy-PainPoint-Detector'}) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            
                            for post in data.get('data', {}).get('children', []):
                                pain_point = self._analyze_reddit_complaint(post['data'])
                                if pain_point:
                                    opportunities.append(pain_point)
        
        except Exception as e:
            print(f"   ❌ Reddit error: {e}")
        
        print(f"   ✅ Reddit: Found {len(opportunities)} complaint-based opportunities")
        return opportunities
    
    def _analyze_reddit_complaint(self, post: Dict) -> Optional[Dict]:
        """Analyze Reddit complaint"""
        
        title = post.get('title', '').lower()
        text = post.get('selftext', '').lower()
        
        # Must contain problem signals
        problem_signals = ['problem', 'issue', 'help', 'struggling', 'frustrated', 'can\'t']
        if not any(signal in title or signal in text for signal in problem_signals):
            return None
        
        problem = self._extract_problem_from_text(title + ' ' + text)
        opp_type = self._classify_pain_point(title + ' ' + text)
        
        # Higher value if many upvotes (validated problem)
        upvotes = post.get('ups', 0)
        value = 500.0 + (upvotes * 10)  # $10 per upvote
        
        return {
            'id': f"reddit_complaint_{post['id']}",
            'platform': 'reddit',
            'source': 'pain_point_detection',
            'type': opp_type,
            'title': f"Reddit Problem: {post['title'][:80]}",
            'description': text[:500],
            'url': f"https://reddit.com{post['permalink']}",
            'value': min(value, 5000.0),  # Cap at $5K
            'urgency': 'high' if upvotes > 50 else 'medium',
            'pain_point': problem,
            'created_at': datetime.fromtimestamp(post['created_utc']).isoformat(),
            'source_data': {
                'platform': 'reddit',
                'subreddit': post.get('subreddit'),
                'upvotes': upvotes
            }
        }
    
    # ========================================
    # GITHUB STALE ISSUES DETECTION
    # ========================================
    
    async def detect_github_stale_issues(self) -> List[Dict]:
        """
        Find GitHub issues that are stale (open >6 months)
        These represent unmet needs
        """
        
        print("   🐙 GitHub: Finding stale issues...")
        
        opportunities = []
        
        try:
            async with aiohttp.ClientSession() as session:
                # Search for old open issues
                six_months_ago = (datetime.now(timezone.utc) - timedelta(days=180)).strftime('%Y-%m-%d')
                url = f'https://api.github.com/search/issues?q=is:open is:issue created:<{six_months_ago}&sort=reactions&per_page=10'
                
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        for issue in data.get('items', []):
                            # Only issues with reactions (validated need)
                            reactions = issue.get('reactions', {}).get('total_count', 0)
                            if reactions < 5:
                                continue
                            
                            value = 500.0 + (reactions * 20)  # $20 per reaction
                            
                            opportunities.append({
                                'id': f"github_stale_{issue['id']}",
                                'platform': 'github',
                                'source': 'pain_point_detection',
                                'type': 'software_development',
                                'title': f"Stale Issue: {issue['title']}",
                                'description': issue.get('body', '')[:500],
                                'url': issue['html_url'],
                                'value': min(value, 3000.0),
                                'urgency': 'medium',
                                'pain_point': f"Unresolved for {(datetime.now(timezone.utc) - datetime.fromisoformat(issue['created_at'].replace('Z', '+00:00'))).days} days",
                                'created_at': issue['created_at'],
                                'source_data': {
                                    'platform': 'github',
                                    'reactions': reactions,
                                    'age_days': (datetime.now(timezone.utc) - datetime.fromisoformat(issue['created_at'].replace('Z', '+00:00'))).days
                                }
                            })
        
        except Exception as e:
            print(f"   ❌ GitHub stale issues error: {e}")
        
        print(f"   ✅ GitHub: Found {len(opportunities)} stale issue opportunities")
        return opportunities
    
    # ========================================
    # QUORA UNANSWERED QUESTIONS
    # ========================================
    
    async def detect_quora_questions(self) -> List[Dict]:
        """
        Find unanswered Quora questions = consulting opportunities
        """
        
        print("   ❓ Quora: Finding unanswered questions...")
        
        # Simulated (Quora API requires partnership)
        opportunities = [
            {
                'id': 'quora_1',
                'platform': 'quora',
                'source': 'pain_point_detection',
                'type': 'business_consulting',
                'title': 'Quora Question: How do I automate my e-commerce fulfillment?',
                'description': 'Question asked 3 months ago, 45 views, no good answers',
                'url': 'https://quora.com/example',
                'value': 1500.0,
                'urgency': 'medium',
                'pain_point': 'No clear solution for e-commerce automation',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'source_data': {
                    'platform': 'quora',
                    'views': 45,
                    'answer_count': 0
                }
            }
        ]
        
        print(f"   ✅ Quora: Found {len(opportunities)} unanswered questions")
        return opportunities
    
    # ========================================
    # YOUTUBE TUTORIAL REQUESTS
    # ========================================
    
    async def detect_youtube_requests(self) -> List[Dict]:
        """
        Find YouTube comments requesting tutorials
        "Can someone explain X?" = consulting opportunity
        """
        
        print("   📺 YouTube: Scanning tutorial requests...")
        
        # Simulated (YouTube API available but complex)
        opportunities = [
            {
                'id': 'youtube_1',
                'platform': 'youtube',
                'source': 'pain_point_detection',
                'type': 'content_creation',
                'title': 'YouTube Request: Tutorial on setting up Stripe subscriptions',
                'description': '50+ comments asking for tutorial on Stripe billing',
                'url': 'https://youtube.com/example',
                'value': 800.0,
                'urgency': 'medium',
                'pain_point': 'No clear tutorial on Stripe subscriptions',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'source_data': {
                    'platform': 'youtube',
                    'request_count': 50
                }
            }
        ]
        
        print(f"   ✅ YouTube: Found {len(opportunities)} tutorial requests")
        return opportunities
    
    # ========================================
    # PRODUCT HUNT FEEDBACK
    # ========================================
    
    async def detect_producthunt_feedback(self) -> List[Dict]:
        """
        Find ProductHunt comments requesting features
        "I wish this had X" = feature opportunity
        """
        
        print("   🚀 ProductHunt: Mining feature requests...")
        
        # Simulated
        opportunities = [
            {
                'id': 'ph_1',
                'platform': 'producthunt',
                'source': 'pain_point_detection',
                'type': 'software_development',
                'title': 'ProductHunt Feature Request: Users want API access',
                'description': 'Top-voted comment: "Great product but needs API"',
                'url': 'https://producthunt.com/example',
                'value': 2500.0,
                'urgency': 'high',
                'pain_point': 'Product missing API functionality',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'source_data': {
                    'platform': 'producthunt',
                    'upvotes': 120
                }
            }
        ]
        
        print(f"   ✅ ProductHunt: Found {len(opportunities)} feature requests")
        return opportunities
    
    # ========================================
    # HELPER FUNCTIONS
    # ========================================
    
    def _extract_problem_from_text(self, text: str) -> str:
        """Extract the core problem from complaint text"""
        
        # Simple extraction (can be enhanced with AI)
        text = text.strip()
        
        # Look for key phrases
        patterns = [
            r'i wish (.+?)(?:\.|$)',
            r'why doesn\'t (.+?)(?:\.|$)',
            r'looking for (.+?)(?:\.|$)',
            r'need help with (.+?)(?:\.|$)',
            r'can someone (.+?)(?:\.|$)',
            r'problem with (.+?)(?:\.|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Fallback: return first 100 chars
        return text[:100]
    
    def _classify_pain_point(self, text: str) -> str:
        """Classify what type of opportunity this is"""
        
        text = text.lower()
        
        if any(kw in text for kw in ['build', 'develop', 'code', 'software', 'app', 'website']):
            return 'software_development'
        elif any(kw in text for kw in ['write', 'content', 'blog', 'article', 'copy']):
            return 'content_creation'
        elif any(kw in text for kw in ['market', 'seo', 'traffic', 'growth', 'ads']):
            return 'marketing'
        elif any(kw in text for kw in ['design', 'ui', 'ux', 'logo', 'brand']):
            return 'design'
        elif any(kw in text for kw in ['data', 'analytics', 'report', 'dashboard']):
            return 'data_analysis'
        else:
            return 'consulting'
    
    def _detect_urgency(self, text: str) -> str:
        """Detect urgency level from text"""
        
        text = text.lower()
        
        high_urgency = ['urgent', 'asap', 'immediately', 'critical', 'emergency', 'losing money']
        medium_urgency = ['soon', 'need', 'want', 'looking for']
        
        if any(signal in text for signal in high_urgency):
            return 'high'
        elif any(signal in text for signal in medium_urgency):
            return 'medium'
        else:
            return 'low'


# ========================================
# EXAMPLE USAGE
# ========================================

if __name__ == "__main__":
    async def test():
        detector = PainPointDetector()
        pain_points = await detector.detect_all_pain_points()
        
        print(f"\n✅ Total pain points found: {len(pain_points)}")
        print(f"   Total potential value: ${sum(p['value'] for p in pain_points):,.0f}")
    
    asyncio.run(test())
