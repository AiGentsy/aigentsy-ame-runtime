# internet_domination_engine_REAL.py
"""
🌐 INTERNET DOMINATION ENGINE - PRODUCTION VERSION
==================================================

PHASE 1: Free Sources (GitHub, Reddit, HackerNews) - WORKS NOW
PHASE 2: Paid APIs (SerpAPI, Google, Bing) - WORKS WHEN API KEYS SET

This version has REAL scrapers that actually return opportunities!
No more empty [] arrays!
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from enum import Enum
import asyncio
import aiohttp
import os
import re
import hashlib

router = APIRouter(tags=["Internet Domination"])


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

class PlatformTier(Enum):
    """Platform access tiers"""
    FREE = "free"  # No API key needed
    PAID = "paid"  # Requires API key
    OAUTH = "oauth"  # Requires OAuth flow


PLATFORMS = {
    # Tier 1: FREE - Works immediately
    "free": {
        "github": {"tier": PlatformTier.FREE, "value": "high"},
        "reddit": {"tier": PlatformTier.FREE, "value": "high"},
        "hackernews": {"tier": PlatformTier.FREE, "value": "high"},
        "stackoverflow": {"tier": PlatformTier.FREE, "value": "medium"},
    },
    
    # Tier 2: PAID - Requires API keys
    "paid": {
        "google_search": {"tier": PlatformTier.PAID, "cost": "$50-200/mo", "key": "SERPAPI_KEY"},
        "bing_search": {"tier": PlatformTier.PAID, "cost": "$7/1000 queries", "key": "BING_SEARCH_KEY"},
        "linkedin_jobs": {"tier": PlatformTier.PAID, "cost": "Varies", "key": "LINKEDIN_API_KEY"},
    },
    
    # Tier 3: OAUTH - Requires OAuth flow (future)
    "oauth": {
        "upwork": {"tier": PlatformTier.OAUTH, "status": "future"},
        "fiverr": {"tier": PlatformTier.OAUTH, "status": "future"},
        "freelancer": {"tier": PlatformTier.OAUTH, "status": "future"},
    }
}


# ═══════════════════════════════════════════════════════════════════════════════
# REAL SCRAPERS - TIER 1 (FREE)
# ═══════════════════════════════════════════════════════════════════════════════

class RealScrapers:
    """
    Production scrapers that actually return real data
    No more empty [] arrays!
    """
    
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.serpapi_key = os.getenv('SERPAPI_KEY')
        self.bing_key = os.getenv('BING_SEARCH_KEY')
    
    # -------------------------------------------------------------------------
    # GITHUB SCRAPER - FREE, WORKS NOW
    # -------------------------------------------------------------------------
    
    async def scrape_github_advanced(self) -> List[Dict]:
        """
        Advanced GitHub scraping - gets MORE than basic explicit_marketplace_scrapers
        
        Searches:
        1. Bounty issues (money involved)
        2. Help wanted (beginner friendly)
        3. Good first issue (easy money)
        4. Funded projects (startups hiring)
        5. Recently created repos (new projects need help)
        """
        
        print("   🔍 GitHub Advanced: Deep scan for opportunities...")
        
        opportunities = []
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {}
                if self.github_token:
                    headers['Authorization'] = f'token {self.github_token}'
                
                # EXPANDED SEARCHES - More than basic scraper
                searches = [
                    # Money-related
                    ('label:bounty is:open', 'bounty'),
                    ('label:sponsored is:open', 'sponsored'),
                    ('label:funded is:open', 'funded'),
                    ('in:title bounty is:open', 'bounty_title'),
                    ('in:body "$" is:open label:"help wanted"', 'paid_help'),
                    
                    # Easy opportunities
                    ('label:"good first issue" is:open', 'beginner'),
                    ('label:"help wanted" is:open', 'help_wanted'),
                    ('label:beginner is:open', 'beginner'),
                    
                    # High-value repos
                    ('stars:>1000 is:open label:"help wanted"', 'popular'),
                    ('created:>2024-01-01 is:open label:bounty', 'recent'),
                ]
                
                for query, category in searches:
                    url = f'https://api.github.com/search/issues?q={query}&sort=created&per_page=20'
                    
                    async with session.get(url, headers=headers) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            
                            for issue in data.get('items', []):
                                value = self._extract_github_value_advanced(issue)
                                
                                opportunities.append({
                                    'id': f"github_adv_{issue['id']}",
                                    'platform': 'github',
                                    'category': category,
                                    'type': 'software_development',
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
                                        'comments': issue.get('comments', 0),
                                        'state': issue.get('state', 'open')
                                    },
                                    'contact_info': {
                                        'github_user': issue.get('user', {}).get('login'),
                                        'github_url': issue.get('user', {}).get('html_url')
                                    }
                                })
                        
                        # Rate limiting
                        await asyncio.sleep(0.5)
        
        except Exception as e:
            print(f"   ❌ GitHub advanced scraper error: {e}")
        
        # Dedupe by issue ID
        seen = set()
        unique = []
        for opp in opportunities:
            if opp['id'] not in seen:
                seen.add(opp['id'])
                unique.append(opp)
        
        print(f"   ✅ GitHub Advanced: Found {len(unique)} unique opportunities")
        return unique
    
    def _extract_github_value_advanced(self, issue: Dict) -> float:
        """Enhanced value extraction"""
        
        # Check labels for bounty amounts
        for label in issue.get('labels', []):
            label_name = label['name'].lower()
            
            # Look for $ amounts
            if '$' in label_name:
                try:
                    amount = int(''.join(filter(str.isdigit, label_name)))
                    if amount > 0:
                        return float(amount)
                except:
                    pass
            
            # Look for keywords
            if 'bounty' in label_name:
                # Check for amount in label
                numbers = re.findall(r'\d+', label_name)
                if numbers:
                    return float(numbers[0])
        
        # Check body for bounty mentions
        body = issue.get('body', '').lower()
        
        # Look for explicit $ mentions
        money_patterns = [
            r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # $1,000 or $1000.00
            r'(\d+)\s*(?:dollars|USD|usd)',  # 1000 dollars
            r'bounty[:\s]+\$?(\d+)',  # bounty: $500
        ]
        
        for pattern in money_patterns:
            matches = re.findall(pattern, body)
            if matches:
                try:
                    amount = float(str(matches[0]).replace(',', ''))
                    if amount > 0:
                        return amount
                except:
                    pass
        
        # Estimate based on labels and repo popularity
        labels = ' '.join([l['name'].lower() for l in issue.get('labels', [])])
        
        if 'bounty' in labels or 'sponsored' in labels or 'funded' in labels:
            return 1000.0  # Assume $1k for bounty issues
        elif 'help wanted' in labels:
            # Check repo stars for value estimation
            return 500.0  # Medium value
        elif 'good first issue' in labels or 'beginner' in labels:
            return 100.0  # Beginner issue
        else:
            return 300.0  # Default
    
    # -------------------------------------------------------------------------
    # REDDIT SCRAPER - FREE, WORKS NOW
    # -------------------------------------------------------------------------
    
    async def scrape_reddit_advanced(self) -> List[Dict]:
        """
        Advanced Reddit scraping - MORE subreddits than basic scraper
        
        Subreddits:
        1. r/forhire - Direct hiring
        2. r/entrepreneur - Business opportunities
        3. r/startups - Startup hiring
        4. r/programming - Tech jobs
        5. r/freelance - Freelance gigs
        6. r/slavelabour - Micro tasks
        7. r/jobs4bitcoins - Crypto payments
        8. r/hiring - General hiring
        """
        
        print("   🔍 Reddit Advanced: Scanning 8+ subreddits...")
        
        opportunities = []
        
        try:
            async with aiohttp.ClientSession() as session:
                subreddits = [
                    'forhire', 'entrepreneur', 'startups', 'programming',
                    'freelance', 'slavelabour', 'jobs4bitcoins', 'hiring',
                    'remotejs', 'webdev', 'designjobs'
                ]
                
                for subreddit in subreddits:
                    url = f'https://www.reddit.com/r/{subreddit}/new.json?limit=25'
                    
                    async with session.get(url, headers={'User-Agent': 'AiGentsy-Advanced-Bot/2.0'}) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            
                            for post in data.get('data', {}).get('children', []):
                                post_data = post['data']
                                title = post_data['title'].lower()
                                
                                # EXPANDED filtering - catch more opportunities
                                keywords = [
                                    'hiring', 'looking for', 'need', 'seeking',
                                    'wanted', 'opportunity', 'gig', 'job',
                                    'project', 'work', 'freelance', 'contract',
                                    'paid', '$', 'budget', 'hire'
                                ]
                                
                                if any(kw in title for kw in keywords):
                                    value = self._extract_reddit_value_advanced(post_data)
                                    opp_type = self._classify_reddit_opportunity(post_data)
                                    
                                    # Extract contact info
                                    contact = self._extract_reddit_contact(post_data)
                                    
                                    opportunities.append({
                                        'id': f"reddit_adv_{post_data['id']}",
                                        'platform': 'reddit',
                                        'type': opp_type,
                                        'title': post_data['title'],
                                        'description': post_data.get('selftext', '')[:500],
                                        'url': f"https://reddit.com{post_data['permalink']}",
                                        'value': value,
                                        'estimated_value': value,
                                        'urgency': 'medium',
                                        'created_at': datetime.fromtimestamp(post_data['created_utc']).isoformat(),
                                        'source_data': {
                                            'subreddit': subreddit,
                                            'score': post_data['score'],
                                            'num_comments': post_data.get('num_comments', 0)
                                        },
                                        'contact_info': contact
                                    })
                    
                    await asyncio.sleep(1)  # Reddit rate limiting
        
        except Exception as e:
            print(f"   ❌ Reddit advanced scraper error: {e}")
        
        print(f"   ✅ Reddit Advanced: Found {len(opportunities)} opportunities")
        return opportunities
    
    def _extract_reddit_value_advanced(self, post: Dict) -> float:
        """Enhanced Reddit value extraction"""
        
        text = (post.get('title', '') + ' ' + post.get('selftext', '')).lower()
        
        # Look for explicit budget mentions
        money_patterns = [
            r'\$(\d{1,3}(?:,\d{3})*)',  # $1,000 or $1000
            r'(\d+)\s*(?:dollars|bucks|USD)',  # 1000 dollars
            r'budget[:\s]+\$?(\d+)',  # budget: $500
            r'pay(?:ing)?\s+\$?(\d+)',  # paying $500
        ]
        
        for pattern in money_patterns:
            matches = re.findall(pattern, text)
            if matches:
                try:
                    amount = float(str(matches[0]).replace(',', ''))
                    if 50 <= amount <= 50000:  # Sanity check
                        return amount
                except:
                    pass
        
        # Estimate based on keywords
        if any(word in text for word in ['enterprise', 'corporate', 'business']):
            return 2000.0
        elif any(word in text for word in ['startup', 'app', 'website']):
            return 1500.0
        elif any(word in text for word in ['freelance', 'contract', 'project']):
            return 800.0
        elif any(word in text for word in ['task', 'quick', 'small']):
            return 150.0
        else:
            return 500.0
    
    def _classify_reddit_opportunity(self, post: Dict) -> str:
        """Classify opportunity type from Reddit post"""
        
        text = (post.get('title', '') + ' ' + post.get('selftext', '')).lower()
        
        if any(kw in text for kw in ['code', 'developer', 'programming', 'software']):
            return 'software_development'
        elif any(kw in text for kw in ['design', 'logo', 'graphic', 'ui', 'ux']):
            return 'graphic_design'
        elif any(kw in text for kw in ['content', 'writing', 'article', 'blog']):
            return 'content_creation'
        elif any(kw in text for kw in ['marketing', 'seo', 'social']):
            return 'marketing'
        elif any(kw in text for kw in ['video', 'editing', 'youtube']):
            return 'video_editing'
        else:
            return 'general'
    
    def _extract_reddit_contact(self, post: Dict) -> Dict:
        """Extract contact info from Reddit post"""
        
        text = post.get('selftext', '')
        
        contact = {
            'reddit_username': post.get('author'),
            'reddit_url': f"https://reddit.com/user/{post.get('author')}"
        }
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            contact['email'] = emails[0]
        
        # Extract Twitter
        twitter_pattern = r'@([A-Za-z0-9_]{1,15})'
        twitter = re.findall(twitter_pattern, text)
        if twitter:
            contact['twitter'] = twitter[0]
        
        return contact
    
    # -------------------------------------------------------------------------
    # HACKERNEWS SCRAPER - FREE, WORKS NOW
    # -------------------------------------------------------------------------
    
    async def scrape_hackernews_advanced(self) -> List[Dict]:
        """
        Advanced HackerNews scraping - Gets MORE than just Who's Hiring
        
        Searches:
        1. Who's Hiring threads (jobs)
        2. Freelancer/seeking posts
        3. Show HN with commercial potential
        4. Ask HN about hiring
        """
        
        print("   🔍 HackerNews Advanced: Deep scan...")
        
        opportunities = []
        
        try:
            async with aiohttp.ClientSession() as session:
                # 1. Who's Hiring threads
                url = 'https://hn.algolia.com/api/v1/search?query=who%20is%20hiring&tags=story'
                
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        for hit in data.get('hits', [])[:5]:  # Top 5 hiring threads
                            story_id = hit['objectID']
                            comments_url = f'https://hn.algolia.com/api/v1/items/{story_id}'
                            
                            async with session.get(comments_url) as comments_resp:
                                if comments_resp.status == 200:
                                    comments_data = await comments_resp.json()
                                    
                                    for comment in comments_data.get('children', [])[:20]:  # 20 jobs per thread
                                        if comment.get('text'):
                                            value = self._extract_hn_value_advanced(comment)
                                            opp_type = self._classify_hn_opportunity(comment)
                                            contact = self._extract_hn_contact(comment)
                                            
                                            opportunities.append({
                                                'id': f"hn_adv_{comment['id']}",
                                                'platform': 'hackernews',
                                                'type': opp_type,
                                                'title': f"HN: {comment.get('author', 'Unknown')} - {opp_type}",
                                                'description': comment.get('text', '')[:500],
                                                'url': f"https://news.ycombinator.com/item?id={comment['id']}",
                                                'value': value,
                                                'estimated_value': value,
                                                'urgency': 'medium',
                                                'created_at': datetime.fromtimestamp(comment['created_at_i']).isoformat(),
                                                'source_data': {
                                                    'author': comment.get('author', ''),
                                                    'story_id': story_id,
                                                    'points': comment.get('points', 0)
                                                },
                                                'contact_info': contact
                                            })
                
                # 2. Freelancer/seeking posts
                freelance_url = 'https://hn.algolia.com/api/v1/search?query=freelancer%20OR%20seeking%20OR%20looking%20for&tags=story'
                
                async with session.get(freelance_url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        for hit in data.get('hits', [])[:10]:
                            if hit.get('title'):
                                opportunities.append({
                                    'id': f"hn_freelance_{hit['objectID']}",
                                    'platform': 'hackernews',
                                    'type': 'freelance',
                                    'title': hit['title'],
                                    'description': hit.get('story_text', '')[:500],
                                    'url': hit.get('url', f"https://news.ycombinator.com/item?id={hit['objectID']}"),
                                    'value': 3000.0,
                                    'estimated_value': 3000.0,
                                    'urgency': 'medium',
                                    'created_at': datetime.fromtimestamp(hit['created_at_i']).isoformat(),
                                    'source_data': {
                                        'author': hit.get('author', ''),
                                        'points': hit.get('points', 0)
                                    }
                                })
        
        except Exception as e:
            print(f"   ❌ HackerNews advanced scraper error: {e}")
        
        print(f"   ✅ HackerNews Advanced: Found {len(opportunities)} opportunities")
        return opportunities
    
    def _extract_hn_value_advanced(self, comment: Dict) -> float:
        """Enhanced HN value extraction"""
        
        text = comment.get('text', '').lower()
        
        # Look for salary/rate mentions
        money_patterns = [
            r'\$(\d{1,3}(?:,\d{3})*)',
            r'(\d+)k\s*(?:per|/)\s*year',
            r'(\d+)\s*(?:/hr|per hour)',
        ]
        
        for pattern in money_patterns:
            matches = re.findall(pattern, text)
            if matches:
                try:
                    amount = float(str(matches[0]).replace(',', '').replace('k', '000'))
                    # Convert hourly/yearly to project value
                    if '/hr' in text or 'per hour' in text:
                        amount = amount * 40  # 40 hour project
                    elif 'year' in text:
                        amount = amount / 12  # Monthly project value
                    
                    if 100 <= amount <= 50000:
                        return amount
                except:
                    pass
        
        # Estimate based on keywords
        if any(word in text for word in ['senior', 'lead', 'architect']):
            return 5000.0
        elif any(word in text for word in ['engineer', 'developer', 'full-time']):
            return 3500.0
        elif any(word in text for word in ['contract', 'freelance', 'project']):
            return 2500.0
        else:
            return 3000.0
    
    def _classify_hn_opportunity(self, comment: Dict) -> str:
        """Classify HN opportunity"""
        
        text = comment.get('text', '').lower()
        
        if any(kw in text for kw in ['engineer', 'developer', 'software', 'backend', 'frontend', 'full stack']):
            return 'software_development'
        elif any(kw in text for kw in ['design', 'designer', 'ui', 'ux']):
            return 'design'
        elif any(kw in text for kw in ['marketing', 'growth', 'seo']):
            return 'marketing'
        elif any(kw in text for kw in ['data', 'analyst', 'analytics', 'ml', 'ai']):
            return 'data_science'
        else:
            return 'engineering'
    
    def _extract_hn_contact(self, comment: Dict) -> Dict:
        """Extract contact from HN comment"""
        
        text = comment.get('text', '')
        
        contact = {
            'hn_username': comment.get('author'),
            'hn_url': f"https://news.ycombinator.com/user?id={comment.get('author')}"
        }
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            contact['email'] = emails[0]
        
        return contact
    
    # -------------------------------------------------------------------------
    # SERPAPI SCRAPERS - PAID, WORKS WHEN API KEY SET
    # -------------------------------------------------------------------------
    
    async def scrape_with_serpapi(self, queries: List[str]) -> List[Dict]:
        """
        Use SerpAPI to search for opportunities across the entire internet
        
        REQUIRES: SERPAPI_KEY environment variable
        COST: $50-200/month depending on volume
        """
        
        if not self.serpapi_key:
            print("   ⚠️  SerpAPI: No API key set, skipping...")
            return []
        
        print(f"   🔍 SerpAPI: Searching {len(queries)} queries...")
        
        opportunities = []
        
        try:
            async with aiohttp.ClientSession() as session:
                for query in queries:
                    url = "https://serpapi.com/search"
                    params = {
                        "q": query,
                        "api_key": self.serpapi_key,
                        "num": 10,
                        "engine": "google"
                    }
                    
                    async with session.get(url, params=params) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            
                            for result in data.get("organic_results", []):
                                # Parse search result into opportunity
                                value = self._estimate_value_from_serpapi(result, query)
                                
                                opportunities.append({
                                    'id': f"serpapi_{hashlib.md5(result['link'].encode()).hexdigest()[:12]}",
                                    'platform': 'google_search',
                                    'type': self._classify_from_query(query),
                                    'title': result.get('title', ''),
                                    'description': result.get('snippet', '')[:500],
                                    'url': result.get('link', ''),
                                    'value': value,
                                    'estimated_value': value,
                                    'urgency': 'medium',
                                    'created_at': datetime.now(timezone.utc).isoformat(),
                                    'source_data': {
                                        'position': result.get('position', 0),
                                        'domain': urlparse(result['link']).netloc if result.get('link') else '',
                                        'search_query': query
                                    }
                                })
                    
                    await asyncio.sleep(1)  # Rate limiting
        
        except Exception as e:
            print(f"   ❌ SerpAPI error: {e}")
        
        print(f"   ✅ SerpAPI: Found {len(opportunities)} opportunities")
        return opportunities
    
    def _estimate_value_from_serpapi(self, result: Dict, query: str) -> float:
        """Estimate opportunity value from SerpAPI result"""
        
        snippet = result.get('snippet', '').lower()
        title = result.get('title', '').lower()
        combined = f"{title} {snippet}"
        
        # Look for explicit amounts
        money_pattern = r'\$(\d{1,3}(?:,\d{3})*)'
        matches = re.findall(money_pattern, combined)
        if matches:
            try:
                return float(matches[0].replace(',', ''))
            except:
                pass
        
        # Estimate based on query type
        if 'freelance' in query or 'gig' in query:
            return 800.0
        elif 'job' in query or 'hiring' in query:
            return 3000.0
        elif 'project' in query:
            return 1500.0
        else:
            return 1000.0
    
    def _classify_from_query(self, query: str) -> str:
        """Classify opportunity from search query"""
        
        query = query.lower()
        
        if any(kw in query for kw in ['developer', 'programming', 'software']):
            return 'software_development'
        elif any(kw in query for kw in ['design', 'graphic', 'logo']):
            return 'graphic_design'
        elif any(kw in query for kw in ['writing', 'content', 'article']):
            return 'content_creation'
        elif any(kw in query for kw in ['marketing', 'seo', 'social']):
            return 'marketing'
        else:
            return 'general'


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════════════

class DominationConfig(BaseModel):
    """Configuration for internet domination scan"""
    use_free: bool = True  # GitHub, Reddit, HN
    use_paid: bool = True  # SerpAPI if key available
    search_queries: Optional[List[str]] = None
    max_opportunities: int = 500


_scrapers = RealScrapers()
_opportunity_cache: List[Dict] = []


@router.post("/domination/scan-all")
async def domination_scan_all(config: DominationConfig = DominationConfig()):
    """
    REAL Internet Domination Scan
    
    Phase 1: Free sources (GitHub, Reddit, HN) - WORKS NOW
    Phase 2: Paid sources (SerpAPI) - WORKS WHEN API KEY SET
    
    Returns REAL opportunities, not empty arrays!
    """
    
    global _opportunity_cache
    
    print("\n" + "="*70)
    print("🌐 INTERNET DOMINATION ENGINE - REAL SCAN")
    print("="*70)
    
    all_opportunities = []
    sources_used = []
    
    # PHASE 1: FREE SOURCES (Always works)
    if config.use_free:
        print("\n📡 PHASE 1: FREE SOURCES")
        
        # GitHub
        github_opps = await _scrapers.scrape_github_advanced()
        all_opportunities.extend(github_opps)
        sources_used.append(f"GitHub ({len(github_opps)})")
        
        # Reddit
        reddit_opps = await _scrapers.scrape_reddit_advanced()
        all_opportunities.extend(reddit_opps)
        sources_used.append(f"Reddit ({len(reddit_opps)})")
        
        # HackerNews
        hn_opps = await _scrapers.scrape_hackernews_advanced()
        all_opportunities.extend(hn_opps)
        sources_used.append(f"HackerNews ({len(hn_opps)})")
    
    # PHASE 2: PAID SOURCES (Only if API keys available)
    if config.use_paid and _scrapers.serpapi_key:
        print("\n💰 PHASE 2: PAID SOURCES")
        
        # Default search queries if none provided
        if not config.search_queries:
            config.search_queries = [
                "freelance developer jobs",
                "remote programming gigs",
                "startup hiring developers",
                "need web developer",
                "looking for graphic designer",
                "content writer needed"
            ]
        
        serpapi_opps = await _scrapers.scrape_with_serpapi(config.search_queries)
        all_opportunities.extend(serpapi_opps)
        sources_used.append(f"SerpAPI ({len(serpapi_opps)})")
    
    # Dedupe and score
    unique_opps = _dedupe_opportunities(all_opportunities)
    scored_opps = sorted(unique_opps, key=lambda x: x.get('value', 0), reverse=True)
    
    # Limit results
    final_opps = scored_opps[:config.max_opportunities]
    
    # Update cache
    _opportunity_cache = final_opps
    
    total_value = sum(opp.get('value', 0) for opp in final_opps)
    
    print(f"\n✅ SCAN COMPLETE")
    print(f"   Total found: {len(final_opps)} opportunities")
    print(f"   Total value: ${total_value:,.0f}")
    print(f"   Sources: {', '.join(sources_used)}")
    print("="*70 + "\n")
    
    return {
        "ok": True,
        "total_opportunities": len(final_opps),
        "total_value": total_value,
        "sources_used": sources_used,
        "opportunities": final_opps[:20],  # Return top 20
        "api_keys_configured": {
            "serpapi": bool(_scrapers.serpapi_key),
            "bing": bool(_scrapers.bing_key),
            "github_token": bool(_scrapers.github_token)
        }
    }


@router.get("/domination/opportunities")
async def get_domination_opportunities(limit: int = 100):
    """Get cached opportunities from last scan"""
    
    return {
        "ok": True,
        "total": len(_opportunity_cache),
        "opportunities": _opportunity_cache[:limit]
    }


def _dedupe_opportunities(opportunities: List[Dict]) -> List[Dict]:
    """Remove duplicates based on URL or ID"""
    
    seen = set()
    unique = []
    
    for opp in opportunities:
        # Create unique key from URL or ID
        key = opp.get('url') or opp.get('id')
        if key and key not in seen:
            seen.add(key)
            unique.append(opp)
    
    return unique


# Helper to parse URLs
from urllib.parse import urlparse


# Example usage
if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI
    
    app = FastAPI()
    app.include_router(router)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
