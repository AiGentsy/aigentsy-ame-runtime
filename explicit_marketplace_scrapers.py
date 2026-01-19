"""
STEP 1: SCALE THE 3 FREE SOURCES
=================================

Enhance explicit_marketplace_scrapers.py to get MORE opportunities from:
- GitHub (currently gets ~10, can get 100+)
- Reddit (currently gets ~10, can get 50+)
- HackerNews (currently gets ~30, can get 100+)

CHANGES FROM ORIGINAL:
1. GitHub: Query more labels, search issues + discussions
2. Reddit: Scan more subreddits, go deeper in threads
3. HackerNews: Parse ALL hiring threads, not just top 3
4. Better value extraction
5. Deduplication
"""

import asyncio
import aiohttp
from typing import Dict, List
from datetime import datetime, timezone
import os


class ExplicitMarketplaceScrapers:
    """
    SCALED version - gets 10x more opportunities from free sources
    """
    
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        # No API keys needed for Reddit/HN!
    
    async def scrape_all(self, platforms: List[str] = None) -> List[Dict]:
        """Scrape all platforms - SCALED UP"""
        
        if platforms is None:
            platforms = ['github', 'reddit', 'hackernews']
        
        tasks = []
        if 'github' in platforms:
            tasks.append(self.scrape_github_scaled())
        if 'reddit' in platforms:
            tasks.append(self.scrape_reddit_scaled())
        if 'hackernews' in platforms:
            tasks.append(self.scrape_hackernews_scaled())
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_opportunities = []
        for result in results:
            if isinstance(result, list):
                all_opportunities.extend(result)
            elif isinstance(result, Exception):
                print(f"   ⚠️  Scraper error: {result}")
        
        # Deduplicate
        seen = set()
        unique_opps = []
        for opp in all_opportunities:
            key = opp.get('url', opp.get('id'))
            if key not in seen:
                seen.add(key)
                unique_opps.append(opp)
        
        return unique_opps
    
    # =========================================================================
    # GITHUB - SCALED (10 → 100+ opportunities)
    # =========================================================================
    
    async def scrape_github_scaled(self) -> List[Dict]:
        """
        SCALED GitHub scraper
        
        ORIGINAL: 4 queries × 10 results = ~40 issues
        SCALED: 15+ queries × 30 results = ~300+ issues
        """
        
        print("   🔍 GitHub (SCALED): Searching bounties, help-wanted, good-first-issue...")
        
        opportunities = []
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {}
                if self.github_token:
                    headers['Authorization'] = f'token {self.github_token}'
                
                # EXPANDED query list
                queries = [
                    # Bounties
                    'label:bounty is:open',
                    'label:"💰bounty" is:open',
                    'label:reward is:open',
                    '"bounty $" in:body is:open',
                    
                    # Help wanted
                    'label:"help wanted" is:open',
                    'label:"help-wanted" is:open',
                    'label:hacktoberfest is:open',
                    
                    # Good first issues (easier to fulfill)
                    'label:"good first issue" is:open',
                    'label:beginner is:open',
                    'label:easy is:open',
                    
                    # Freelance/consulting
                    '"freelance" in:title is:open',
                    '"consulting" in:title is:open',
                    '"contractor" in:title is:open',
                    
                    # By topic (high-value)
                    'label:documentation is:open stars:>100',
                    'label:enhancement is:open stars:>100',
                    'topic:ai is:issue is:open stars:>50',
                ]
                
                for query in queries:
                    # Get 30 per query instead of 10
                    url = f'https://api.github.com/search/issues?q={query}&sort=created&per_page=30'
                    
                    async with session.get(url, headers=headers) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            
                            for issue in data.get('items', []):
                                value = self._extract_github_value(issue)
                                
                                # Only include if has meaningful value
                                if value >= 50:  # Minimum $50
                                    opportunities.append({
                                        'id': f"github_{issue['id']}",
                                        'platform': 'github',
                                        'type': self._classify_github_issue(issue),
                                        'title': issue['title'],
                                        'description': issue.get('body', '')[:500],
                                        'url': issue['html_url'],
                                        'value': value,
                                        'estimated_value': value,
                                        'urgency': 'medium',
                                        'created_at': issue['created_at'],
                                        'source_data': {
                                            'repo': issue['repository_url'].split('/')[-2:],
                                            'labels': [l['name'] for l in issue.get('labels', [])],
                                            'stars': issue.get('stargazers_count', 0),
                                            'comments': issue.get('comments', 0)
                                        }
                                    })
                        
                        # Respect rate limits
                        await asyncio.sleep(0.5)
        
        except Exception as e:
            print(f"   ❌ GitHub error: {e}")
        
        print(f"   ✅ GitHub: Found {len(opportunities)} opportunities")
        return opportunities
    
    def _extract_github_value(self, issue: Dict) -> float:
        """Extract $ value from GitHub issue - IMPROVED"""
        
        # Check labels for explicit amounts
        for label in issue.get('labels', []):
            label_name = label['name'].lower()
            if '$' in label_name or 'bounty' in label_name:
                # Try to extract number
                import re
                numbers = re.findall(r'\d+', label_name)
                if numbers:
                    try:
                        return float(numbers[0])
                    except:
                        pass
        
        # Check body for $ mentions
        body = issue.get('body', '').lower()
        if '$' in body or 'bounty' in body:
            import re
            # Find patterns like "$500", "$1,000", "$1k"
            patterns = [
                r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # $500, $1,000.00
                r'\$\s*(\d+)k',  # $5k
                r'bounty[:\s]+\$?\s*(\d+)',  # bounty: $500
            ]
            for pattern in patterns:
                matches = re.findall(pattern, body)
                if matches:
                    try:
                        amount = matches[0].replace(',', '')
                        if 'k' in body:
                            return float(amount) * 1000
                        return float(amount)
                    except:
                        pass
        
        # Estimate based on repo popularity and labels
        labels_str = ' '.join([l['name'].lower() for l in issue.get('labels', [])])
        
        # Check repo stars
        stars = issue.get('repository', {}).get('stargazers_count', 0)
        
        if 'beginner' in labels_str or 'good first issue' in labels_str:
            return 100.0 + (stars / 100)  # $100-200
        elif 'documentation' in labels_str:
            return 200.0 + (stars / 50)   # $200-400
        elif 'enhancement' in labels_str or 'feature' in labels_str:
            return 500.0 + (stars / 20)   # $500-1000
        elif 'bug' in labels_str and stars > 1000:
            return 300.0 + (stars / 30)   # $300-600
        else:
            return 150.0 + (stars / 100)  # $150-300
    
    def _classify_github_issue(self, issue: Dict) -> str:
        """Classify GitHub issue type"""
        labels = ' '.join([l['name'].lower() for l in issue.get('labels', [])])
        title = issue.get('title', '').lower()
        
        if 'documentation' in labels or 'docs' in title:
            return 'documentation'
        elif 'bug' in labels:
            return 'bug_fix'
        elif 'feature' in labels or 'enhancement' in labels:
            return 'feature_development'
        elif 'frontend' in labels or 'ui' in labels:
            return 'frontend_development'
        elif 'backend' in labels or 'api' in labels:
            return 'backend_development'
        else:
            return 'software_development'
    
    # =========================================================================
    # REDDIT - SCALED (10 → 50+ opportunities)
    # =========================================================================
    
    async def scrape_reddit_scaled(self) -> List[Dict]:
        """
        SCALED Reddit scraper
        
        ORIGINAL: 3 subreddits × 10 posts = ~30 posts
        SCALED: 10+ subreddits × 25 posts = ~250+ posts
        """
        
        print("   🔍 Reddit (SCALED): Scanning hiring subreddits...")
        
        opportunities = []
        
        try:
            async with aiohttp.ClientSession() as session:
                # EXPANDED subreddit list
                subreddits = [
                    'forhire',
                    'entrepreneur',
                    'startups',
                    'hiring',
                    'slavelabour',  # Microtasks ($5-50)
                    'freelance_forhire',
                    'freelanceWriters',
                    'designjobs',
                    'webdev',
                    'programming',
                    'SaaS',
                    'indiebiz',
                ]
                
                for subreddit in subreddits:
                    # Get 25 instead of 10
                    url = f'https://www.reddit.com/r/{subreddit}/new.json?limit=25'
                    
                    async with session.get(url, headers={'User-Agent': 'AiGentsy-Discovery-Bot/2.0'}) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            
                            for post in data.get('data', {}).get('children', []):
                                post_data = post['data']
                                title = post_data['title'].lower()
                                
                                # EXPANDED keyword matching
                                hiring_keywords = [
                                    'hiring', 'looking for', 'need', 'seeking',
                                    'wanted', 'freelancer', 'contractor',
                                    'project', 'gig', 'task', 'job'
                                ]
                                
                                if any(kw in title for kw in hiring_keywords):
                                    value = self._extract_reddit_value(post_data)
                                    
                                    # Only include if reasonable value
                                    if value >= 25:  # Minimum $25
                                        opportunities.append({
                                            'id': f"reddit_{post_data['id']}",
                                            'platform': 'reddit',
                                            'type': self._classify_reddit_post(post_data),
                                            'title': post_data['title'],
                                            'description': post_data.get('selftext', '')[:500],
                                            'url': f"https://reddit.com{post_data['permalink']}",
                                            'value': value,
                                            'estimated_value': value,
                                            'urgency': 'medium',
                                            'created_at': datetime.fromtimestamp(post_data['created_utc'], tz=timezone.utc).isoformat(),
                                            'source_data': {
                                                'subreddit': subreddit,
                                                'score': post_data['score'],
                                                'author': post_data.get('author', '[deleted]')
                                            }
                                        })
                    
                    # Rate limiting
                    await asyncio.sleep(1)
        
        except Exception as e:
            print(f"   ❌ Reddit error: {e}")
        
        print(f"   ✅ Reddit: Found {len(opportunities)} opportunities")
        return opportunities
    
    def _extract_reddit_value(self, post: Dict) -> float:
        """Extract $ value from Reddit post - IMPROVED"""
        import re
        
        text = (post.get('title', '') + ' ' + post.get('selftext', '')).lower()
        
        # Look for explicit $ amounts
        patterns = [
            r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # $500, $1,000
            r'\$\s*(\d+)k',  # $5k
            r'(\d+)\s*(?:dollars?|usd)',  # 500 dollars
            r'budget[:\s]+\$?\s*(\d+)',  # budget: $500
            r'pay(?:ing)?[:\s]+\$?\s*(\d+)',  # paying: $500
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                try:
                    amount = matches[0].replace(',', '')
                    if 'k' in text:
                        return float(amount) * 1000
                    return float(amount)
                except:
                    pass
        
        # Estimate based on subreddit and keywords
        subreddit = post.get('subreddit', '').lower()
        
        if 'slavelabour' in subreddit:
            return 25.0  # Microtasks
        elif any(kw in text for kw in ['enterprise', 'saas', 'business']):
            return 2000.0  # High-value projects
        elif any(kw in text for kw in ['startup', 'app', 'website']):
            return 1500.0  # Medium projects
        elif any(kw in text for kw in ['logo', 'design', 'content']):
            return 500.0  # Creative work
        else:
            return 750.0  # Default estimate
    
    def _classify_reddit_post(self, post: Dict) -> str:
        """Classify Reddit post type"""
        text = (post.get('title', '') + ' ' + post.get('selftext', '')).lower()
        
        if any(kw in text for kw in ['website', 'web dev', 'frontend', 'react']):
            return 'web_development'
        elif any(kw in text for kw in ['logo', 'design', 'graphic', 'branding']):
            return 'graphic_design'
        elif any(kw in text for kw in ['content', 'writing', 'blog', 'article']):
            return 'content_creation'
        elif any(kw in text for kw in ['app', 'mobile', 'ios', 'android']):
            return 'mobile_development'
        elif any(kw in text for kw in ['marketing', 'seo', 'social media']):
            return 'marketing'
        elif any(kw in text for kw in ['data', 'analysis', 'analytics']):
            return 'data_analysis'
        else:
            return 'consulting'
    
    # =========================================================================
    # HACKERNEWS - SCALED (30 → 100+ opportunities)
    # =========================================================================
    
    async def scrape_hackernews_scaled(self) -> List[Dict]:
        """
        SCALED HackerNews scraper
        
        ORIGINAL: 3 threads × 10 jobs = ~30 jobs
        SCALED: ALL recent threads × 50 jobs = ~200+ jobs
        """
        
        print("   🔍 HackerNews (SCALED): Parsing ALL Who's Hiring threads...")
        
        opportunities = []
        
        try:
            async with aiohttp.ClientSession() as session:
                # Find ALL recent "Who is hiring" posts
                url = 'https://hn.algolia.com/api/v1/search?query=who%20is%20hiring&tags=story&hitsPerPage=10'
                
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        for hit in data.get('hits', []):
                            story_id = hit['objectID']
                            
                            # Get ALL comments (jobs) from this thread
                            comments_url = f'https://hn.algolia.com/api/v1/items/{story_id}'
                            
                            async with session.get(comments_url) as comments_resp:
                                if comments_resp.status == 200:
                                    comments_data = await comments_resp.json()
                                    
                                    # Get up to 50 jobs per thread (vs 10 original)
                                    for comment in comments_data.get('children', [])[:50]:
                                        if comment.get('text'):
                                            value = self._extract_hn_value(comment)
                                            opp_type = self._classify_hn_job(comment)
                                            
                                            # Extract company/contact from text
                                            contact_info = self._extract_hn_contact(comment)
                                            
                                            opportunities.append({
                                                'id': f"hn_{comment['id']}",
                                                'platform': 'hackernews',
                                                'type': opp_type,
                                                'title': f"{contact_info.get('company', 'HN Job')}: {opp_type.replace('_', ' ').title()}",
                                                'description': comment.get('text', '')[:500],
                                                'url': f"https://news.ycombinator.com/item?id={comment['id']}",
                                                'value': value,
                                                'estimated_value': value,
                                                'urgency': 'medium',
                                                'created_at': datetime.fromtimestamp(comment['created_at_i'], tz=timezone.utc).isoformat(),
                                                'source_data': {
                                                    'author': comment.get('author', ''),
                                                    'story_id': story_id,
                                                    **contact_info
                                                }
                                            })
                            
                            # Rate limiting
                            await asyncio.sleep(1)
        
        except Exception as e:
            print(f"   ❌ HackerNews error: {e}")
        
        print(f"   ✅ HackerNews: Found {len(opportunities)} opportunities")
        return opportunities
    
    def _extract_hn_value(self, comment: Dict) -> float:
        """Extract value from HN job posting - IMPROVED"""
        import re
        
        text = comment.get('text', '').lower()
        
        # Look for salary/rate mentions
        patterns = [
            r'\$\s*(\d{1,3}(?:,\d{3})*)\s*[-–]\s*\$\s*(\d{1,3}(?:,\d{3})*)',  # $100,000 - $150,000
            r'\$\s*(\d{1,3})k\s*[-–]\s*\$\s*(\d{1,3})k',  # $100k - $150k
            r'\$\s*(\d+)\/hour',  # $50/hour
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                try:
                    if len(matches[0]) == 2:  # Range
                        low, high = matches[0]
                        avg = (float(low.replace(',', '')) + float(high.replace(',', ''))) / 2
                        if 'k' in text:
                            return avg * 1000 / 12  # Monthly from annual
                        return avg / 12 if avg > 50000 else avg  # Assume annual if >50k
                    else:
                        return float(matches[0]) * 160  # Hourly to monthly (160 hrs)
                except:
                    pass
        
        # Estimate based on role keywords
        if 'senior' in text or 'lead' in text or 'principal' in text:
            return 12000.0  # ~$144k annual
        elif 'engineer' in text or 'developer' in text:
            return 10000.0  # ~$120k annual
        elif 'designer' in text:
            return 8000.0   # ~$96k annual
        elif 'marketing' in text or 'growth' in text:
            return 7000.0   # ~$84k annual
        else:
            return 6000.0   # Default ~$72k annual
    
    def _classify_hn_job(self, comment: Dict) -> str:
        """Classify HN job type"""
        text = comment.get('text', '').lower()
        
        if any(kw in text for kw in ['frontend', 'react', 'vue', 'angular']):
            return 'frontend_development'
        elif any(kw in text for kw in ['backend', 'api', 'python', 'golang', 'node']):
            return 'backend_development'
        elif any(kw in text for kw in ['full stack', 'fullstack']):
            return 'fullstack_development'
        elif any(kw in text for kw in ['mobile', 'ios', 'android', 'react native']):
            return 'mobile_development'
        elif any(kw in text for kw in ['devops', 'sre', 'infrastructure', 'kubernetes']):
            return 'devops'
        elif any(kw in text for kw in ['designer', 'ui', 'ux', 'design']):
            return 'design'
        elif any(kw in text for kw in ['product manager', 'pm']):
            return 'product_management'
        elif any(kw in text for kw in ['data', 'ml', 'machine learning', 'ai']):
            return 'data_science'
        elif any(kw in text for kw in ['marketing', 'growth', 'seo']):
            return 'marketing'
        else:
            return 'software_development'
    
    def _extract_hn_contact(self, comment: Dict) -> Dict:
        """Extract company/contact info from HN post"""
        import re
        
        text = comment.get('text', '')
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        
        # Extract company name (usually first line or after "at")
        lines = text.split('\n')
        company = None
        if lines:
            # Try first non-empty line
            for line in lines[:3]:
                clean_line = re.sub(r'<[^>]+>', '', line).strip()
                if clean_line and len(clean_line) < 100:
                    company = clean_line
                    break
        
        return {
            'company': company,
            'email': emails[0] if emails else None,
            'author': comment.get('author')
        }


# =============================================================================
# USAGE EXAMPLE
# =============================================================================

if __name__ == "__main__":
    async def test_scaled_scrapers():
        scraper = ScaledMarketplaceScrapers()
        opportunities = await scraper.scrape_all()
        
        print(f"\n{'='*70}")
        print(f"TOTAL OPPORTUNITIES FOUND: {len(opportunities)}")
        print(f"{'='*70}\n")
        
        # Breakdown by platform
        platforms = {}
        for opp in opportunities:
            platform = opp['platform']
            platforms[platform] = platforms.get(platform, 0) + 1
        
        for platform, count in platforms.items():
            print(f"  {platform.upper()}: {count} opportunities")
        
        # Show top 10 by value
        print(f"\nTOP 10 BY VALUE:")
        print(f"{'-'*70}")
        sorted_opps = sorted(opportunities, key=lambda x: x['value'], reverse=True)
        for i, opp in enumerate(sorted_opps[:10], 1):
            print(f"{i}. ${opp['value']:,.0f} - {opp['title'][:50]}... ({opp['platform']})")
    
    asyncio.run(test_scaled_scrapers())
