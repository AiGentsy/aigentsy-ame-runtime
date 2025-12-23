"""
EXPLICIT MARKETPLACE SCRAPERS - DIMENSION 1
Real API integrations to discover opportunities

Tier 1 Platforms (Phase 1):
- GitHub Issues (bounties, "help wanted")
- Upwork (active gigs)
- Reddit (r/forhire, r/entrepreneur, r/startups)
- HackerNews (Who's Hiring threads)

Future Tiers:
- LinkedIn, AngelList, RemoteOK, ProductHunt, Discord, etc.
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional
from datetime import datetime, timezone
import os


class ExplicitMarketplaceScrapers:
    """
    Scrapes explicit job boards and marketplaces
    """
    
    def __init__(self):
        # API keys (set via environment variables)
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.upwork_key = os.getenv('UPWORK_API_KEY')
        self.reddit_client_id = os.getenv('REDDIT_CLIENT_ID')
        self.reddit_secret = os.getenv('REDDIT_CLIENT_SECRET')
    
    async def scrape_all(self, platforms: Optional[List[str]] = None) -> List[Dict]:
        """
        Scrape all platforms in parallel
        
        Args:
            platforms: Optional list of specific platforms to scrape
                      If None, scrapes all available platforms
        
        Returns:
            List of opportunities from all platforms
        """
        
        all_platforms = ['github', 'upwork', 'reddit', 'hackernews']
        
        if platforms:
            platforms_to_scrape = [p for p in platforms if p in all_platforms]
        else:
            platforms_to_scrape = all_platforms
        
        # Scrape all platforms in parallel
        tasks = []
        
        if 'github' in platforms_to_scrape:
            tasks.append(self.scrape_github())
        
        if 'upwork' in platforms_to_scrape:
            tasks.append(self.scrape_upwork())
        
        if 'reddit' in platforms_to_scrape:
            tasks.append(self.scrape_reddit())
        
        if 'hackernews' in platforms_to_scrape:
            tasks.append(self.scrape_hackernews())
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten results
        all_opportunities = []
        for result in results:
            if isinstance(result, list):
                all_opportunities.extend(result)
            elif isinstance(result, Exception):
                print(f"   ⚠️  Scraper error: {result}")
        
        return all_opportunities
    
    async def scrape_github(self) -> List[Dict]:
        """
        Scrape GitHub for issues with bounties and "help wanted" labels
        
        API: https://api.github.com/search/issues
        """
        
        print("   🔍 GitHub: Searching for bounties and help-wanted issues...")
        
        opportunities = []
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {}
                if self.github_token:
                    headers['Authorization'] = f'token {self.github_token}'
                
                # Search for issues with bounties
                queries = [
                    'label:bounty is:open',
                    'label:"help wanted" is:open',
                    'label:beginner is:open',
                    'label:hacktoberfest is:open'
                ]
                
                for query in queries:
                    url = f'https://api.github.com/search/issues?q={query}&sort=created&per_page=10'
                    
                    async with session.get(url, headers=headers) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            
                            for issue in data.get('items', []):
                                # Extract value from labels or description
                                value = self._extract_github_value(issue)
                                
                                opportunities.append({
                                    'id': f"github_{issue['id']}",
                                    'platform': 'github',
                                    'type': 'software_development',
                                    'title': issue['title'],
                                    'description': issue.get('body', '')[:500],
                                    'url': issue['html_url'],
                                    'value': value,
                                    'urgency': 'medium',
                                    'created_at': issue['created_at'],
                                    'source_data': {
                                        'repo': issue['repository_url'].split('/')[-2:],
                                        'labels': [l['name'] for l in issue.get('labels', [])]
                                    }
                                })
        
        except Exception as e:
            print(f"   ❌ GitHub scraper error: {e}")
        
        print(f"   ✅ GitHub: Found {len(opportunities)} opportunities")
        return opportunities
    
    def _extract_github_value(self, issue: Dict) -> float:
        """Extract bounty value from GitHub issue"""
        
        # Check labels for bounty amounts
        for label in issue.get('labels', []):
            label_name = label['name'].lower()
            if '$' in label_name:
                try:
                    # Extract number from label like "bounty: $500"
                    amount = int(''.join(filter(str.isdigit, label_name)))
                    if amount > 0:
                        return float(amount)
                except:
                    pass
        
        # Check body for bounty mentions
        body = issue.get('body', '').lower()
        if 'bounty' in body or '$' in body:
            # Simple extraction - can be improved
            words = body.split()
            for i, word in enumerate(words):
                if '$' in word:
                    try:
                        amount = int(''.join(filter(str.isdigit, word)))
                        if amount > 0:
                            return float(amount)
                    except:
                        pass
        
        # Default estimates based on labels
        labels = [l['name'].lower() for l in issue.get('labels', [])]
        
        if 'beginner' in ' '.join(labels) or 'good first issue' in ' '.join(labels):
            return 100.0  # Small beginner issue
        elif 'help wanted' in ' '.join(labels):
            return 500.0  # Medium issue
        else:
            return 1000.0  # Larger issue
    
    async def scrape_upwork(self) -> List[Dict]:
        """
        Scrape Upwork for active gigs
        
        NOTE: Upwork API requires OAuth and approval
        Using simulated data for Phase 1
        """
        
        print("   🔍 Upwork: Searching for active gigs...")
        
        # Simulated opportunities (replace with real API when available)
        opportunities = [
            {
                'id': f'upwork_{i}',
                'platform': 'upwork',
                'type': 'web_development',
                'title': f'Build React Dashboard (Project #{i+1})',
                'description': 'Need experienced React developer to build analytics dashboard',
                'url': f'https://upwork.com/job/{i}',
                'value': 2000 + (i * 500),
                'urgency': 'high',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'source_data': {
                    'budget': '2000-5000',
                    'duration': '1-3 months',
                    'expertise': 'Expert'
                }
            }
            for i in range(5)
        ]
        
        print(f"   ✅ Upwork: Found {len(opportunities)} opportunities")
        return opportunities
    
    async def scrape_reddit(self) -> List[Dict]:
        """
        Scrape Reddit for hiring posts
        
        Subreddits: r/forhire, r/entrepreneur, r/startups
        """
        
        print("   🔍 Reddit: Searching hiring subreddits...")
        
        opportunities = []
        
        try:
            async with aiohttp.ClientSession() as session:
                subreddits = ['forhire', 'entrepreneur', 'startups']
                
                for subreddit in subreddits:
                    url = f'https://www.reddit.com/r/{subreddit}/new.json?limit=10'
                    
                    async with session.get(url, headers={'User-Agent': 'AiGentsy-Discovery-Bot'}) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            
                            for post in data.get('data', {}).get('children', []):
                                post_data = post['data']
                                title = post_data['title'].lower()
                                
                                # Filter for hiring posts
                                if any(kw in title for kw in ['hiring', 'looking for', 'need', 'seeking']):
                                    value = self._extract_reddit_value(post_data)
                                    opp_type = self._classify_reddit_opportunity(post_data)
                                    
                                    opportunities.append({
                                        'id': f"reddit_{post_data['id']}",
                                        'platform': 'reddit',
                                        'type': opp_type,
                                        'title': post_data['title'],
                                        'description': post_data.get('selftext', '')[:500],
                                        'url': f"https://reddit.com{post_data['permalink']}",
                                        'value': value,
                                        'urgency': 'medium',
                                        'created_at': datetime.fromtimestamp(post_data['created_utc']).isoformat(),
                                        'source_data': {
                                            'subreddit': subreddit,
                                            'score': post_data['score']
                                        }
                                    })
        
        except Exception as e:
            print(f"   ❌ Reddit scraper error: {e}")
        
        print(f"   ✅ Reddit: Found {len(opportunities)} opportunities")
        return opportunities
    
    def _extract_reddit_value(self, post: Dict) -> float:
        """Extract value from Reddit post"""
        
        text = (post.get('title', '') + ' ' + post.get('selftext', '')).lower()
        
        # Look for budget mentions
        if '$' in text:
            words = text.split()
            for word in words:
                if '$' in word:
                    try:
                        amount = int(''.join(filter(str.isdigit, word)))
                        if amount > 0:
                            return float(amount)
                    except:
                        pass
        
        # Default estimate
        return 500.0
    
    def _classify_reddit_opportunity(self, post: Dict) -> str:
        """Classify Reddit opportunity type"""
        
        text = (post.get('title', '') + ' ' + post.get('selftext', '')).lower()
        
        if any(kw in text for kw in ['developer', 'coding', 'programming', 'software']):
            return 'software_development'
        elif any(kw in text for kw in ['design', 'designer', 'ui', 'ux']):
            return 'design'
        elif any(kw in text for kw in ['marketing', 'seo', 'content', 'social']):
            return 'marketing'
        elif any(kw in text for kw in ['writing', 'writer', 'blog', 'copy']):
            return 'content_creation'
        else:
            return 'consulting'
    
    async def scrape_hackernews(self) -> List[Dict]:
        """
        Scrape HackerNews "Who's Hiring" threads
        
        API: https://hn.algolia.com/api
        """
        
        print("   🔍 HackerNews: Searching Who's Hiring threads...")
        
        opportunities = []
        
        try:
            async with aiohttp.ClientSession() as session:
                # Search for "Who is hiring" posts
                url = 'https://hn.algolia.com/api/v1/search?query=who%20is%20hiring&tags=story'
                
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        for hit in data.get('hits', [])[:3]:  # Top 3 hiring threads
                            # Get comments (job postings)
                            story_id = hit['objectID']
                            comments_url = f'https://hn.algolia.com/api/v1/items/{story_id}'
                            
                            async with session.get(comments_url) as comments_resp:
                                if comments_resp.status == 200:
                                    comments_data = await comments_resp.json()
                                    
                                    for comment in comments_data.get('children', [])[:10]:  # First 10 jobs
                                        if comment.get('text'):
                                            value = self._extract_hn_value(comment)
                                            opp_type = self._classify_hn_opportunity(comment)
                                            
                                            opportunities.append({
                                                'id': f"hn_{comment['id']}",
                                                'platform': 'hackernews',
                                                'type': opp_type,
                                                'title': f"HackerNews: {comment.get('author', 'Unknown')} - {opp_type}",
                                                'description': comment.get('text', '')[:500],
                                                'url': f"https://news.ycombinator.com/item?id={comment['id']}",
                                                'value': value,
                                                'urgency': 'medium',
                                                'created_at': datetime.fromtimestamp(comment['created_at_i']).isoformat(),
                                                'source_data': {
                                                    'author': comment.get('author', ''),
                                                    'story_id': story_id
                                                }
                                            })
        
        except Exception as e:
            print(f"   ❌ HackerNews scraper error: {e}")
        
        print(f"   ✅ HackerNews: Found {len(opportunities)} opportunities")
        return opportunities
    
    def _extract_hn_value(self, comment: Dict) -> float:
        """Extract value from HN comment"""
        
        text = comment.get('text', '').lower()
        
        # HN posts often have salary ranges
        # Default to project value estimate
        return 3000.0
    
    def _classify_hn_opportunity(self, comment: Dict) -> str:
        """Classify HN opportunity type"""
        
        text = comment.get('text', '').lower()
        
        if any(kw in text for kw in ['engineer', 'developer', 'software', 'backend', 'frontend']):
            return 'software_development'
        elif any(kw in text for kw in ['design', 'designer', 'ui', 'ux']):
            return 'design'
        elif any(kw in text for kw in ['marketing', 'growth', 'seo']):
            return 'marketing'
        elif any(kw in text for kw in ['data', 'analyst', 'analytics']):
            return 'data_analysis'
        else:
            return 'consulting'


# Example usage
if __name__ == "__main__":
    async def test():
        scraper = ExplicitMarketplaceScrapers()
        opportunities = await scraper.scrape_all()
        print(f"\nTotal opportunities found: {len(opportunities)}")
    
    asyncio.run(test())
