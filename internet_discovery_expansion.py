"""
INTERNET DISCOVERY EXPANSION
============================
Expands alpha_discovery_engine from 27 platforms to ENTIRE INTERNET.

ADDS TO EXISTING:
- Search engine discovery (Google, Bing, DuckDuckGo)
- Contact info extraction (email, Twitter, LinkedIn, Reddit)
- News/RSS monitoring for opportunity signals
- Forum/community scanning beyond Reddit

PHILOSOPHY:
- SCAN everywhere (no platform limits)
- EXTRACT contact info for direct outreach
- NEVER post to restricted platforms (Fiverr, Upwork)
- Route to direct_outreach_engine for DM/email

INTEGRATES WITH:
- alpha_discovery_engine (extends dimensions)
- direct_outreach_engine (passes contacts)
- platform_apis (uses for outreach)
- quality_control (apex QC on all)
"""

import asyncio
import aiohttp
import os
import re
import json
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from urllib.parse import urlparse, quote_plus, urljoin
import xml.etree.ElementTree as ET


# =============================================================================
# CONFIGURATION
# =============================================================================

class InternetSource(Enum):
    """Extended discovery sources beyond the original 27"""
    # Search Engines
    GOOGLE_SEARCH = "google_search"
    BING_SEARCH = "bing_search"
    DUCKDUCKGO = "duckduckgo"
    
    # News & RSS
    GOOGLE_NEWS = "google_news"
    RSS_FEEDS = "rss_feeds"
    HACKER_NEWS_NEW = "hn_new"
    
    # Forums & Communities
    DISCOURSE_FORUMS = "discourse"
    STACK_OVERFLOW = "stackoverflow"
    QUORA = "quora"
    INDIE_HACKERS = "indie_hackers"
    
    # Social Deep Scan
    TWITTER_ADVANCED = "twitter_advanced"
    LINKEDIN_POSTS = "linkedin_posts"
    FACEBOOK_GROUPS = "facebook_groups"
    
    # Job Boards (scan only)
    INDEED_SCAN = "indeed_scan"
    GLASSDOOR_SCAN = "glassdoor_scan"
    ANGELLIST_SCAN = "angellist_scan"
    WELLFOUND_SCAN = "wellfound_scan"
    
    # Freelance Platforms (scan only - NO posting)
    UPWORK_SCAN = "upwork_scan"
    FIVERR_SCAN = "fiverr_scan"
    TOPTAL_SCAN = "toptal_scan"
    FREELANCER_SCAN = "freelancer_scan"


@dataclass
class ExtractedContact:
    """Contact info extracted from opportunity"""
    source_url: str
    name: Optional[str] = None
    email: Optional[str] = None
    twitter_handle: Optional[str] = None
    linkedin_url: Optional[str] = None
    reddit_username: Optional[str] = None
    github_username: Optional[str] = None
    website: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    extraction_confidence: float = 0.0
    preferred_outreach: Optional[str] = None  # email, twitter_dm, linkedin_message


@dataclass 
class InternetOpportunity:
    """Opportunity discovered from internet-wide scan"""
    opportunity_id: str
    source: InternetSource
    source_url: str
    title: str
    description: str
    pain_point: str
    keywords: List[str]
    estimated_value: float
    contact: Optional[ExtractedContact] = None
    urgency_score: float = 0.5
    actionability_score: float = 0.5
    quality_score: float = 0.5
    discovered_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    raw_data: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# SEARCH ENGINE DISCOVERY
# =============================================================================

class SearchEngineScanner:
    """
    Scans search engines for monetizable opportunities.
    Uses SerpAPI, Google Custom Search, or fallback scrapers.
    """
    
    def __init__(self):
        self.serpapi_key = os.getenv("SERPAPI_KEY")
        self.google_cse_key = os.getenv("GOOGLE_CSE_KEY")
        self.google_cse_cx = os.getenv("GOOGLE_CSE_CX")
        
        # High-value search queries
        self.opportunity_queries = [
            # Direct hiring intent
            '"looking for a developer" OR "need developer help"',
            '"hiring freelancer" OR "need freelancer"',
            '"budget for" AND "project"',
            '"paying" AND ("per hour" OR "fixed price")',
            
            # Pain points
            '"frustrated with" site:reddit.com',
            '"wish there was" site:twitter.com',
            '"anyone know how to" site:reddit.com',
            '"struggling with" AND "automation"',
            
            # Business opportunities
            '"need help automating"',
            '"looking for AI solution"',
            '"want to build" AND "app"',
            '"need a bot" OR "need automation"',
            
            # Startup/tech opportunities
            '"just raised" AND "hiring"',
            '"launching soon" AND "need"',
            '"MVP" AND "looking for"',
        ]
        
        # Industry-specific queries
        self.industry_queries = {
            'ecommerce': ['"shopify help" OR "woocommerce developer"', '"need inventory system"'],
            'saas': ['"saas automation" OR "saas integration"', '"api integration help"'],
            'marketing': ['"marketing automation" OR "need marketing tool"', '"social media manager needed"'],
            'finance': ['"fintech developer" OR "payment integration"', '"accounting automation"'],
            'healthcare': ['"healthtech" AND "developer needed"', '"medical app" AND "build"'],
        }
    
    async def scan_google(self, query: str, num_results: int = 10) -> List[Dict]:
        """Scan Google using Custom Search API or SerpAPI"""
        
        results = []
        
        # Try SerpAPI first
        if self.serpapi_key:
            results = await self._serpapi_search(query, num_results)
        
        # Fallback to Google CSE
        elif self.google_cse_key and self.google_cse_cx:
            results = await self._google_cse_search(query, num_results)
        
        return results
    
    async def _serpapi_search(self, query: str, num: int) -> List[Dict]:
        """Search via SerpAPI"""
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://serpapi.com/search"
                params = {
                    "q": query,
                    "api_key": self.serpapi_key,
                    "num": num,
                    "engine": "google"
                }
                
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("organic_results", [])
        except Exception as e:
            print(f"SerpAPI error: {e}")
        
        return []
    
    async def _google_cse_search(self, query: str, num: int) -> List[Dict]:
        """Search via Google Custom Search Engine"""
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://www.googleapis.com/customsearch/v1"
                params = {
                    "q": query,
                    "key": self.google_cse_key,
                    "cx": self.google_cse_cx,
                    "num": min(num, 10)
                }
                
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("items", [])
        except Exception as e:
            print(f"Google CSE error: {e}")
        
        return []
    
    async def scan_bing(self, query: str, num_results: int = 10) -> List[Dict]:
        """Scan Bing using Bing Web Search API"""
        bing_key = os.getenv("BING_SEARCH_KEY")
        if not bing_key:
            return []
        
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://api.bing.microsoft.com/v7.0/search"
                headers = {"Ocp-Apim-Subscription-Key": bing_key}
                params = {"q": query, "count": num_results}
                
                async with session.get(url, headers=headers, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("webPages", {}).get("value", [])
        except Exception as e:
            print(f"Bing search error: {e}")
        
        return []
    
    async def scan_all_engines(self, query: str) -> List[Dict]:
        """Scan all available search engines"""
        all_results = []
        
        # Google
        google_results = await self.scan_google(query)
        for r in google_results:
            r['_source'] = 'google'
        all_results.extend(google_results)
        
        # Bing
        bing_results = await self.scan_bing(query)
        for r in bing_results:
            r['_source'] = 'bing'
        all_results.extend(bing_results)
        
        # Dedupe by URL
        seen_urls = set()
        deduped = []
        for r in all_results:
            url = r.get('link') or r.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                deduped.append(r)
        
        return deduped


# =============================================================================
# CONTACT INFO EXTRACTOR
# =============================================================================

class ContactExtractor:
    """
    Extracts contact information from discovered opportunities.
    Enables direct outreach via DM/email instead of platform posting.
    """
    
    # Email patterns
    EMAIL_PATTERNS = [
        r'[\w\.-]+@[\w\.-]+\.\w+',
        r'[\w\.-]+\s*\[at\]\s*[\w\.-]+\s*\[dot\]\s*\w+',
        r'[\w\.-]+\s*at\s*[\w\.-]+\s*dot\s*\w+',
    ]
    
    # Social handle patterns
    TWITTER_PATTERNS = [
        r'@([A-Za-z0-9_]{1,15})',
        r'twitter\.com/([A-Za-z0-9_]{1,15})',
        r'x\.com/([A-Za-z0-9_]{1,15})',
    ]
    
    LINKEDIN_PATTERNS = [
        r'linkedin\.com/in/([\w-]+)',
        r'linkedin\.com/company/([\w-]+)',
    ]
    
    GITHUB_PATTERNS = [
        r'github\.com/([\w-]+)',
    ]
    
    REDDIT_PATTERNS = [
        r'reddit\.com/u(?:ser)?/([\w-]+)',
        r'/u/([\w-]+)',
        r'u/([\w-]+)',
    ]
    
    async def extract_from_url(self, url: str) -> ExtractedContact:
        """Extract contact info from a URL by fetching and parsing the page"""
        
        contact = ExtractedContact(source_url=url)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        contact = await self._parse_html_for_contacts(html, url)
        except Exception as e:
            print(f"Error extracting from {url}: {e}")
        
        return contact
    
    async def extract_from_text(self, text: str, source_url: str = "") -> ExtractedContact:
        """Extract contact info from raw text"""
        
        contact = ExtractedContact(source_url=source_url)
        
        # Extract emails
        for pattern in self.EMAIL_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Clean up email
                email = matches[0]
                email = email.replace('[at]', '@').replace('[dot]', '.')
                email = email.replace(' at ', '@').replace(' dot ', '.')
                contact.email = email
                break
        
        # Extract Twitter handles
        for pattern in self.TWITTER_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                contact.twitter_handle = matches[0]
                break
        
        # Extract LinkedIn
        for pattern in self.LINKEDIN_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                contact.linkedin_url = f"https://linkedin.com/in/{matches[0]}"
                break
        
        # Extract GitHub
        for pattern in self.GITHUB_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                contact.github_username = matches[0]
                break
        
        # Extract Reddit
        for pattern in self.REDDIT_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                contact.reddit_username = matches[0]
                break
        
        # Calculate confidence
        contact.extraction_confidence = self._calculate_confidence(contact)
        
        # Determine preferred outreach
        contact.preferred_outreach = self._determine_preferred_outreach(contact)
        
        return contact
    
    async def _parse_html_for_contacts(self, html: str, url: str) -> ExtractedContact:
        """Parse HTML for contact information"""
        
        # Start with text extraction
        contact = await self.extract_from_text(html, url)
        
        # Look for structured data (JSON-LD, microdata)
        try:
            # JSON-LD
            jsonld_match = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
            if jsonld_match:
                try:
                    data = json.loads(jsonld_match.group(1))
                    if isinstance(data, dict):
                        if 'email' in data and not contact.email:
                            contact.email = data['email']
                        if 'name' in data and not contact.name:
                            contact.name = data['name']
                        if 'author' in data and isinstance(data['author'], dict):
                            if not contact.name:
                                contact.name = data['author'].get('name')
                except:
                    pass
            
            # Meta tags
            og_title = re.search(r'<meta property="og:title" content="([^"]+)"', html)
            if og_title and not contact.name:
                contact.name = og_title.group(1)
            
            twitter_creator = re.search(r'<meta name="twitter:creator" content="@?([^"]+)"', html)
            if twitter_creator and not contact.twitter_handle:
                contact.twitter_handle = twitter_creator.group(1)
                
        except Exception as e:
            print(f"HTML parsing error: {e}")
        
        # Recalculate confidence
        contact.extraction_confidence = self._calculate_confidence(contact)
        contact.preferred_outreach = self._determine_preferred_outreach(contact)
        
        return contact
    
    def _calculate_confidence(self, contact: ExtractedContact) -> float:
        """Calculate extraction confidence score"""
        score = 0.0
        
        if contact.email:
            score += 0.4  # Email is highest value
        if contact.twitter_handle:
            score += 0.25
        if contact.linkedin_url:
            score += 0.2
        if contact.reddit_username:
            score += 0.15
        if contact.github_username:
            score += 0.1
        if contact.name:
            score += 0.1
        
        return min(score, 1.0)
    
    def _determine_preferred_outreach(self, contact: ExtractedContact) -> str:
        """Determine best outreach channel based on available contact info"""
        
        # Priority: Email > Twitter DM > LinkedIn > Reddit DM
        if contact.email:
            return "email"
        elif contact.twitter_handle:
            return "twitter_dm"
        elif contact.linkedin_url:
            return "linkedin_message"
        elif contact.reddit_username:
            return "reddit_dm"
        elif contact.github_username:
            return "github_discussion"
        else:
            return "none"


# =============================================================================
# RSS/NEWS SCANNER
# =============================================================================

class NewsScanner:
    """
    Scans news sources and RSS feeds for opportunity signals.
    Detects: funding rounds, product launches, hiring announcements.
    """
    
    def __init__(self):
        self.rss_feeds = [
            # Tech news
            "https://news.ycombinator.com/rss",
            "https://www.producthunt.com/feed",
            "https://techcrunch.com/feed/",
            "https://feeds.feedburner.com/venturebeat/SZYF",
            
            # Startup/funding
            "https://www.crunchbase.com/news/feed",
            
            # Reddit hiring subreddits
            "https://www.reddit.com/r/forhire/.rss",
            "https://www.reddit.com/r/freelance/.rss",
            "https://www.reddit.com/r/jobbit/.rss",
        ]
        
        # Signal keywords
        self.funding_signals = ['raised', 'funding', 'series a', 'series b', 'seed round', 'investment']
        self.hiring_signals = ['hiring', 'looking for', 'job opening', 'we\'re hiring', 'join our team']
        self.launch_signals = ['launching', 'just launched', 'announcing', 'introducing', 'new product']
    
    async def scan_rss(self, feed_url: str) -> List[Dict]:
        """Scan a single RSS feed"""
        items = []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(feed_url, timeout=15) as resp:
                    if resp.status == 200:
                        content = await resp.text()
                        items = self._parse_rss(content, feed_url)
        except Exception as e:
            print(f"RSS scan error for {feed_url}: {e}")
        
        return items
    
    def _parse_rss(self, xml_content: str, feed_url: str) -> List[Dict]:
        """Parse RSS XML content"""
        items = []
        
        try:
            root = ET.fromstring(xml_content)
            
            # Handle different RSS formats
            for item in root.findall('.//item') or root.findall('.//{http://www.w3.org/2005/Atom}entry'):
                title = item.findtext('title') or item.findtext('{http://www.w3.org/2005/Atom}title', '')
                link = item.findtext('link') or item.findtext('{http://www.w3.org/2005/Atom}link', '')
                desc = item.findtext('description') or item.findtext('{http://www.w3.org/2005/Atom}summary', '')
                
                # Handle Atom link format
                if not link:
                    link_elem = item.find('{http://www.w3.org/2005/Atom}link')
                    if link_elem is not None:
                        link = link_elem.get('href', '')
                
                if title:
                    # Detect signals
                    text_lower = (title + ' ' + desc).lower()
                    signals = []
                    
                    for kw in self.funding_signals:
                        if kw in text_lower:
                            signals.append('funding')
                            break
                    
                    for kw in self.hiring_signals:
                        if kw in text_lower:
                            signals.append('hiring')
                            break
                    
                    for kw in self.launch_signals:
                        if kw in text_lower:
                            signals.append('launch')
                            break
                    
                    items.append({
                        'title': title,
                        'url': link,
                        'description': desc[:500] if desc else '',
                        'signals': signals,
                        'feed_source': feed_url
                    })
        except Exception as e:
            print(f"RSS parse error: {e}")
        
        return items
    
    async def scan_all_feeds(self) -> List[Dict]:
        """Scan all configured RSS feeds"""
        all_items = []
        
        tasks = [self.scan_rss(feed) for feed in self.rss_feeds]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                all_items.extend(result)
        
        return all_items


# =============================================================================
# FREELANCE PLATFORM SCANNER (SCAN ONLY - NO POSTING)
# =============================================================================

class FreelancePlatformScanner:
    """
    Scans freelance platforms for opportunities.
    IMPORTANT: Only scans and extracts contact info.
    NEVER posts to these platforms (violates ToS).
    Contact via DM/email instead.
    """
    
    def __init__(self):
        # RSS feeds for public job listings
        self.feeds = {
            'upwork': None,  # No public RSS, needs scraping
            'fiverr': None,  # No public RSS
            'freelancer': "https://www.freelancer.com/rss.xml",
        }
    
    async def scan_upwork_public(self) -> List[Dict]:
        """
        Scan Upwork's public job listings.
        Note: We scan only. For execution, we contact the client directly
        via their provided contact info (email/website).
        """
        # This would use their public job search or RSS if available
        # For now, return empty - implement with actual scraping if needed
        return []
    
    async def scan_fiverr_requests(self) -> List[Dict]:
        """
        Scan Fiverr buyer requests (if accessible).
        We don't respond on Fiverr - we contact buyers directly.
        """
        return []
    
    async def extract_client_contact_from_listing(self, listing_url: str) -> ExtractedContact:
        """
        Extract client contact info from a freelance listing.
        Goal: Find their email, website, or social handles for direct contact.
        """
        extractor = ContactExtractor()
        return await extractor.extract_from_url(listing_url)


# =============================================================================
# MAIN INTERNET DISCOVERY EXPANSION ENGINE
# =============================================================================

class InternetDiscoveryExpansion:
    """
    Main engine that expands discovery beyond the 27 original platforms.
    Integrates with alpha_discovery_engine.
    
    Flow:
    1. Scan search engines with opportunity queries
    2. Scan RSS/news for signals (funding, hiring, launches)
    3. Extract contact info from all discoveries
    4. Score and filter opportunities
    5. Pass to direct_outreach_engine for DM/email contact
    """
    
    def __init__(self):
        self.search_scanner = SearchEngineScanner()
        self.contact_extractor = ContactExtractor()
        self.news_scanner = NewsScanner()
        self.freelance_scanner = FreelancePlatformScanner()
        
        # Quality filters
        self.min_value = 100  # Minimum $100 opportunity
        self.min_confidence = 0.3  # Minimum contact confidence
    
    async def run_full_scan(self) -> List[InternetOpportunity]:
        """Run complete internet-wide scan"""
        
        print("\n" + "=" * 60)
        print("🌐 INTERNET DISCOVERY EXPANSION - FULL SCAN")
        print("=" * 60)
        
        all_opportunities = []
        
        # 1. Search engine discovery
        print("\n🔍 Scanning search engines...")
        search_opps = await self._scan_search_engines()
        all_opportunities.extend(search_opps)
        print(f"   Found {len(search_opps)} from search engines")
        
        # 2. News/RSS discovery
        print("\n📰 Scanning news and RSS feeds...")
        news_opps = await self._scan_news_feeds()
        all_opportunities.extend(news_opps)
        print(f"   Found {len(news_opps)} from news/RSS")
        
        # 3. Extract contacts for all
        print("\n📇 Extracting contact information...")
        for opp in all_opportunities:
            if not opp.contact or opp.contact.extraction_confidence < 0.2:
                opp.contact = await self.contact_extractor.extract_from_url(opp.source_url)
        
        # 4. Filter by quality
        print("\n⚡ Filtering for actionable opportunities...")
        filtered = [
            opp for opp in all_opportunities
            if opp.contact and opp.contact.preferred_outreach != "none"
        ]
        
        print(f"\n✅ SCAN COMPLETE:")
        print(f"   Total discovered: {len(all_opportunities)}")
        print(f"   With contact info: {len(filtered)}")
        print(f"   Ready for outreach: {len([o for o in filtered if o.contact.extraction_confidence >= self.min_confidence])}")
        
        return filtered
    
    async def _scan_search_engines(self) -> List[InternetOpportunity]:
        """Scan search engines with opportunity queries"""
        
        opportunities = []
        
        # Use top 5 queries to avoid rate limits
        queries = self.search_scanner.opportunity_queries[:5]
        
        for query in queries:
            results = await self.search_scanner.scan_all_engines(query)
            
            for result in results[:5]:  # Limit per query
                url = result.get('link') or result.get('url', '')
                title = result.get('title', '')
                snippet = result.get('snippet') or result.get('description', '')
                
                if not url or not title:
                    continue
                
                # Create opportunity
                opp_id = hashlib.md5(url.encode()).hexdigest()[:12]
                
                opp = InternetOpportunity(
                    opportunity_id=f"inet_{opp_id}",
                    source=InternetSource.GOOGLE_SEARCH,
                    source_url=url,
                    title=title,
                    description=snippet,
                    pain_point=self._extract_pain_point(title, snippet),
                    keywords=query.split()[:5],
                    estimated_value=self._estimate_value(title, snippet),
                    raw_data=result
                )
                
                opportunities.append(opp)
            
            # Rate limit between queries
            await asyncio.sleep(1)
        
        return opportunities
    
    async def _scan_news_feeds(self) -> List[InternetOpportunity]:
        """Scan news and RSS feeds"""
        
        opportunities = []
        items = await self.news_scanner.scan_all_feeds()
        
        for item in items:
            # Only process items with relevant signals
            if not item.get('signals'):
                continue
            
            url = item.get('url', '')
            title = item.get('title', '')
            
            if not url or not title:
                continue
            
            opp_id = hashlib.md5(url.encode()).hexdigest()[:12]
            
            opp = InternetOpportunity(
                opportunity_id=f"news_{opp_id}",
                source=InternetSource.RSS_FEEDS,
                source_url=url,
                title=title,
                description=item.get('description', ''),
                pain_point=f"Signal: {', '.join(item['signals'])}",
                keywords=item['signals'],
                estimated_value=self._value_from_signal(item['signals']),
                urgency_score=0.7 if 'hiring' in item['signals'] else 0.5,
                raw_data=item
            )
            
            opportunities.append(opp)
        
        return opportunities
    
    def _extract_pain_point(self, title: str, description: str) -> str:
        """Extract the core pain point from title/description"""
        text = (title + ' ' + description).lower()
        
        pain_indicators = [
            ('looking for', 'Need help with'),
            ('need help', 'Seeking assistance with'),
            ('frustrated', 'Frustrated with'),
            ('struggling', 'Struggling with'),
            ('want to', 'Wants to'),
            ('how to', 'Needs to learn'),
        ]
        
        for indicator, prefix in pain_indicators:
            if indicator in text:
                # Extract context around indicator
                idx = text.find(indicator)
                context = text[idx:idx+100].split('.')[0]
                return f"{prefix}: {context}"
        
        return f"Opportunity: {title[:100]}"
    
    def _estimate_value(self, title: str, description: str) -> float:
        """Estimate opportunity value from content"""
        text = (title + ' ' + description).lower()
        
        # Look for budget mentions
        budget_patterns = [
            (r'\$(\d+)k', lambda m: int(m.group(1)) * 1000),
            (r'\$(\d+),(\d+)', lambda m: int(m.group(1) + m.group(2))),
            (r'\$(\d+)', lambda m: int(m.group(1))),
            (r'budget.*?(\d+)', lambda m: int(m.group(1))),
        ]
        
        for pattern, extractor in budget_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return float(extractor(match))
                except:
                    pass
        
        # Default estimates by keywords
        if 'enterprise' in text or 'startup' in text:
            return 5000.0
        elif 'small business' in text:
            return 2000.0
        elif 'mvp' in text or 'prototype' in text:
            return 3000.0
        else:
            return 1000.0
    
    def _value_from_signal(self, signals: List[str]) -> float:
        """Estimate value based on signal type"""
        value = 1000.0
        
        if 'funding' in signals:
            value += 5000.0  # Funded companies have budget
        if 'hiring' in signals:
            value += 2000.0  # Active hiring = active spending
        if 'launch' in signals:
            value += 1000.0  # New products need support
        
        return value


# =============================================================================
# INTEGRATION WITH ALPHA DISCOVERY
# =============================================================================

async def expand_discovery_dimensions(alpha_engine=None) -> List[InternetOpportunity]:
    """
    Integrates with alpha_discovery_engine to add internet-wide discovery.
    Call this in addition to alpha_discovery_engine.run_discovery()
    """
    
    expansion = InternetDiscoveryExpansion()
    
    # Run internet-wide scan
    internet_opportunities = await expansion.run_full_scan()
    
    # Convert to alpha_discovery format if needed
    if alpha_engine:
        # Would convert InternetOpportunity to alpha_discovery format
        pass
    
    return internet_opportunities


# =============================================================================
# STANDALONE TEST
# =============================================================================

async def test_internet_discovery():
    """Test the internet discovery expansion"""
    
    print("\n" + "=" * 70)
    print("🧪 TESTING INTERNET DISCOVERY EXPANSION")
    print("=" * 70)
    
    expansion = InternetDiscoveryExpansion()
    
    # Test contact extraction
    print("\n📇 Testing contact extraction...")
    extractor = ContactExtractor()
    
    test_text = """
    Hi, I'm looking for a developer to help with my project.
    You can reach me at john@example.com or @johndoe on Twitter.
    My LinkedIn is linkedin.com/in/john-doe
    """
    
    contact = await extractor.extract_from_text(test_text)
    print(f"   Email: {contact.email}")
    print(f"   Twitter: {contact.twitter_handle}")
    print(f"   LinkedIn: {contact.linkedin_url}")
    print(f"   Confidence: {contact.extraction_confidence}")
    print(f"   Preferred: {contact.preferred_outreach}")
    
    # Test search engine scanner (if API keys present)
    if os.getenv("SERPAPI_KEY") or os.getenv("GOOGLE_CSE_KEY"):
        print("\n🔍 Testing search engine scanner...")
        scanner = SearchEngineScanner()
        results = await scanner.scan_google('"looking for developer"', num_results=3)
        print(f"   Found {len(results)} results")
        for r in results[:2]:
            print(f"   - {r.get('title', '')[:50]}...")
    else:
        print("\n⚠️ No search API keys configured - skipping search test")
    
    # Test RSS scanner
    print("\n📰 Testing RSS/news scanner...")
    news = NewsScanner()
    items = await news.scan_rss("https://news.ycombinator.com/rss")
    print(f"   Found {len(items)} items from HN RSS")
    for item in items[:3]:
        signals = item.get('signals', [])
        print(f"   - {item['title'][:40]}... [{', '.join(signals) if signals else 'no signal'}]")
    
    print("\n✅ Internet discovery expansion test complete!")


if __name__ == "__main__":
    asyncio.run(test_internet_discovery())
