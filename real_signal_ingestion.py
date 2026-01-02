"""
REAL SIGNAL INGESTION ENGINE
=============================

Transforms Intent Prediction from simulated → REAL signals

THE ALPHA:
- Detect opportunities BEFORE they're posted
- First mover advantage on every deal
- You're not competing - you're the only one there

SIGNAL SOURCES:
1. Funding Signals → Company just raised → Will hire in 2-4 weeks
2. Hiring Signals → Job posted → Adjacent needs exist
3. Tech Stack Signals → New tool adopted → Integration work needed
4. Pain Signals → Complaints detected → Solution opportunity
5. Launch Signals → Product launched → Marketing/support needed
6. Growth Signals → Traffic spike → Scaling needs

INTEGRATES WITH:
- alpha_discovery_engine.py (Dimension 4: Predictive Intelligence)
- advanced_discovery_dimensions.py (PredictiveIntelligenceEngine)
"""

import asyncio
import hashlib
import os
import re
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
from uuid import uuid4
import httpx
from bs4 import BeautifulSoup
import feedparser


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _generate_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


# ============================================================
# SIGNAL TYPES & CONFIGURATION
# ============================================================

class SignalType(str, Enum):
    """Types of predictive signals"""
    FUNDING = "funding"  # Company raised money
    HIRING = "hiring"  # Company posting jobs
    TECH_STACK = "tech_stack"  # New technology adopted
    PAIN_POINT = "pain_point"  # Complaints/frustrations
    LAUNCH = "launch"  # Product/feature launched
    GROWTH = "growth"  # Traffic/revenue spike
    PARTNERSHIP = "partnership"  # New partnership announced
    EXPANSION = "expansion"  # Geographic/market expansion
    PIVOT = "pivot"  # Strategy change
    ACQUISITION = "acquisition"  # M&A activity


class SignalStrength(str, Enum):
    """How strong is the predictive signal"""
    WEAK = "weak"  # 20-40% confidence
    MODERATE = "moderate"  # 40-60% confidence
    STRONG = "strong"  # 60-80% confidence
    VERY_STRONG = "very_strong"  # 80%+ confidence


# What each signal predicts
SIGNAL_PREDICTIONS = {
    SignalType.FUNDING: {
        "predictions": [
            {"need": "hiring_support", "confidence": 0.85, "timing_days": 14},
            {"need": "marketing", "confidence": 0.75, "timing_days": 30},
            {"need": "product_development", "confidence": 0.70, "timing_days": 21},
            {"need": "legal_compliance", "confidence": 0.60, "timing_days": 7},
        ],
        "decay_days": 90
    },
    SignalType.HIRING: {
        "predictions": [
            {"need": "adjacent_role_support", "confidence": 0.70, "timing_days": 7},
            {"need": "onboarding_content", "confidence": 0.65, "timing_days": 14},
            {"need": "training_materials", "confidence": 0.60, "timing_days": 21},
        ],
        "decay_days": 30
    },
    SignalType.TECH_STACK: {
        "predictions": [
            {"need": "integration_work", "confidence": 0.80, "timing_days": 7},
            {"need": "migration_support", "confidence": 0.75, "timing_days": 14},
            {"need": "documentation", "confidence": 0.65, "timing_days": 21},
        ],
        "decay_days": 60
    },
    SignalType.PAIN_POINT: {
        "predictions": [
            {"need": "solution_provider", "confidence": 0.75, "timing_days": 3},
            {"need": "consulting", "confidence": 0.70, "timing_days": 7},
        ],
        "decay_days": 14
    },
    SignalType.LAUNCH: {
        "predictions": [
            {"need": "marketing", "confidence": 0.85, "timing_days": 7},
            {"need": "customer_support", "confidence": 0.80, "timing_days": 14},
            {"need": "content_creation", "confidence": 0.75, "timing_days": 7},
            {"need": "pr_outreach", "confidence": 0.70, "timing_days": 3},
        ],
        "decay_days": 30
    },
    SignalType.GROWTH: {
        "predictions": [
            {"need": "scaling_infrastructure", "confidence": 0.80, "timing_days": 7},
            {"need": "hiring_support", "confidence": 0.75, "timing_days": 14},
            {"need": "process_automation", "confidence": 0.70, "timing_days": 21},
        ],
        "decay_days": 45
    }
}


@dataclass
class Signal:
    """A detected predictive signal"""
    signal_id: str
    signal_type: SignalType
    source: str
    source_url: str
    company_name: str
    headline: str
    
    # Optional fields with defaults
    company_domain: Optional[str] = None
    company_industry: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    raw_data: Dict[str, Any] = field(default_factory=dict)
    strength: SignalStrength = SignalStrength.MODERATE
    confidence: float = 0.5
    detected_at: str = field(default_factory=_now)
    signal_date: Optional[str] = None
    predictions: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result["signal_type"] = self.signal_type.value
        result["strength"] = self.strength.value
        return result


@dataclass 
class PredictedOpportunity:
    """An opportunity predicted from signals"""
    opportunity_id: str
    signal_id: str
    signal_type: SignalType
    
    # Target
    company_name: str
    company_domain: Optional[str]
    
    # Prediction
    predicted_need: str
    confidence: float
    optimal_timing_days: int
    optimal_outreach_date: str
    
    # Opportunity details
    estimated_value: float
    suggested_pitch: str
    urgency: str
    
    # Status
    status: str = "pending"  # pending, contacted, converted, expired
    created_at: str = field(default_factory=_now)
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result["signal_type"] = self.signal_type.value
        return result


# ============================================================
# SIGNAL SCRAPERS - Real Data Sources
# ============================================================

class FundingSignalScraper:
    """
    Scrape funding announcements from:
    - TechCrunch RSS
    - Crunchbase (if API key available)
    - Twitter/X funding announcements
    - Press releases
    """
    
    TECHCRUNCH_FUNDING_RSS = "https://techcrunch.com/category/venture/feed/"
    
    async def scrape_techcrunch(self) -> List[Signal]:
        """Scrape TechCrunch funding news"""
        signals = []
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(self.TECHCRUNCH_FUNDING_RSS)
                
                if response.status_code == 200:
                    feed = feedparser.parse(response.text)
                    
                    for entry in feed.entries[:20]:
                        title = entry.get("title", "")
                        summary = entry.get("summary", "")
                        link = entry.get("link", "")
                        
                        # Look for funding keywords
                        funding_keywords = ["raises", "raised", "funding", "series", "seed", "million", "venture"]
                        if any(kw in title.lower() for kw in funding_keywords):
                            # Extract company name (usually first word or before "raises")
                            company = self._extract_company_name(title)
                            amount = self._extract_funding_amount(title + " " + summary)
                            
                            signal = Signal(
                                signal_id=_generate_id("sig_fund"),
                                signal_type=SignalType.FUNDING,
                                source="techcrunch",
                                source_url=link,
                                company_name=company,
                                headline=title,
                                details={
                                    "funding_amount": amount,
                                    "summary": summary[:500]
                                },
                                strength=self._calculate_strength(amount),
                                confidence=0.85
                            )
                            
                            # Generate predictions
                            signal.predictions = self._generate_predictions(signal)
                            signals.append(signal)
                            
        except Exception as e:
            print(f"TechCrunch scrape error: {e}")
        
        return signals
    
    async def scrape_crunchbase(self, api_key: str = None) -> List[Signal]:
        """Scrape Crunchbase funding rounds (requires API key)"""
        if not api_key:
            api_key = os.getenv("CRUNCHBASE_API_KEY")
        
        if not api_key:
            return []
        
        signals = []
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Crunchbase API endpoint for recent funding rounds
                url = "https://api.crunchbase.com/api/v4/searches/funding_rounds"
                headers = {"X-cb-user-key": api_key}
                
                payload = {
                    "field_ids": ["identifier", "funded_organization_identifier", "money_raised", "announced_on"],
                    "order": [{"field_id": "announced_on", "sort": "desc"}],
                    "limit": 50
                }
                
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for item in data.get("entities", []):
                        props = item.get("properties", {})
                        org = props.get("funded_organization_identifier", {})
                        
                        signal = Signal(
                            signal_id=_generate_id("sig_fund"),
                            signal_type=SignalType.FUNDING,
                            source="crunchbase",
                            source_url=f"https://crunchbase.com/funding_round/{item.get('uuid')}",
                            company_name=org.get("value", "Unknown"),
                            headline=f"{org.get('value')} raised ${props.get('money_raised', {}).get('value_usd', 0):,.0f}",
                            details={
                                "funding_amount": props.get("money_raised", {}).get("value_usd", 0),
                                "announced_on": props.get("announced_on")
                            },
                            strength=SignalStrength.VERY_STRONG,
                            confidence=0.95
                        )
                        
                        signal.predictions = self._generate_predictions(signal)
                        signals.append(signal)
                        
        except Exception as e:
            print(f"Crunchbase scrape error: {e}")
        
        return signals
    
    def _extract_company_name(self, title: str) -> str:
        """Extract company name from funding headline"""
        # Common patterns: "CompanyName raises $X" or "CompanyName secures $X"
        patterns = [
            r"^([A-Z][a-zA-Z0-9]+)\s+(?:raises|secures|closes|gets|lands)",
            r"^([A-Z][a-zA-Z0-9\s]+?)\s+raises",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title)
            if match:
                return match.group(1).strip()
        
        # Fallback: first capitalized word
        words = title.split()
        if words:
            return words[0]
        
        return "Unknown"
    
    def _extract_funding_amount(self, text: str) -> float:
        """Extract funding amount from text"""
        patterns = [
            r"\$(\d+(?:\.\d+)?)\s*(?:million|m\b)",
            r"\$(\d+(?:\.\d+)?)\s*(?:billion|b\b)",
            r"(\d+(?:\.\d+)?)\s*(?:million|m)\s*(?:dollars|\$)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                amount = float(match.group(1))
                if "billion" in text.lower() or "b" in match.group(0).lower():
                    amount *= 1000
                return amount * 1_000_000
        
        return 0
    
    def _calculate_strength(self, amount: float) -> SignalStrength:
        """Calculate signal strength based on funding amount"""
        if amount >= 50_000_000:
            return SignalStrength.VERY_STRONG
        elif amount >= 10_000_000:
            return SignalStrength.STRONG
        elif amount >= 1_000_000:
            return SignalStrength.MODERATE
        else:
            return SignalStrength.WEAK
    
    def _generate_predictions(self, signal: Signal) -> List[Dict]:
        """Generate predicted opportunities from signal"""
        predictions = []
        signal_config = SIGNAL_PREDICTIONS.get(signal.signal_type, {})
        
        for pred in signal_config.get("predictions", []):
            optimal_date = datetime.now(timezone.utc) + timedelta(days=pred["timing_days"])
            
            predictions.append({
                "need": pred["need"],
                "confidence": pred["confidence"] * signal.confidence,
                "timing_days": pred["timing_days"],
                "optimal_outreach_date": optimal_date.isoformat(),
                "estimated_value": self._estimate_value(signal, pred["need"])
            })
        
        return predictions
    
    def _estimate_value(self, signal: Signal, need: str) -> float:
        """Estimate opportunity value based on signal and need"""
        funding = signal.details.get("funding_amount", 0)
        
        # Typical spend ratios post-funding
        ratios = {
            "hiring_support": 0.001,  # 0.1% of funding
            "marketing": 0.005,  # 0.5% of funding
            "product_development": 0.003,
            "legal_compliance": 0.0005,
        }
        
        ratio = ratios.get(need, 0.001)
        estimated = funding * ratio
        
        # Cap at reasonable ranges
        return min(max(estimated, 500), 50000)


class HiringSignalScraper:
    """
    Scrape hiring signals from:
    - LinkedIn Jobs RSS
    - Indeed RSS
    - Company career pages
    - Greenhouse/Lever APIs
    """
    
    async def scrape_linkedin_jobs(self, keywords: List[str] = None) -> List[Signal]:
        """Scrape LinkedIn job postings for signals"""
        if not keywords:
            keywords = ["startup", "series a", "growing team", "founding"]
        
        signals = []
        
        # LinkedIn RSS feeds (public job searches)
        for keyword in keywords[:3]:  # Limit to avoid rate limits
            try:
                url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPostings/jobs?keywords={keyword}&start=0"
                
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.get(url, headers={
                        "User-Agent": "Mozilla/5.0 (compatible; AiGentsy/1.0)"
                    })
                    
                    if response.status_code == 200:
                        # Parse job listings
                        soup = BeautifulSoup(response.text, "html.parser")
                        
                        for job_card in soup.select(".job-search-card")[:10]:
                            company = job_card.select_one(".job-search-card__company-name")
                            title = job_card.select_one(".job-search-card__title")
                            link = job_card.select_one("a")
                            
                            if company and title:
                                signal = Signal(
                                    signal_id=_generate_id("sig_hire"),
                                    signal_type=SignalType.HIRING,
                                    source="linkedin",
                                    source_url=link.get("href", "") if link else "",
                                    company_name=company.get_text(strip=True),
                                    headline=f"{company.get_text(strip=True)} hiring: {title.get_text(strip=True)}",
                                    details={
                                        "job_title": title.get_text(strip=True),
                                        "keyword": keyword
                                    },
                                    strength=SignalStrength.MODERATE,
                                    confidence=0.70
                                )
                                
                                signal.predictions = self._generate_predictions(signal)
                                signals.append(signal)
                                
            except Exception as e:
                print(f"LinkedIn scrape error for {keyword}: {e}")
        
        return signals
    
    async def scrape_greenhouse_jobs(self, company_slugs: List[str] = None) -> List[Signal]:
        """Scrape Greenhouse job boards (many startups use this)"""
        if not company_slugs:
            # Popular startup greenhouse boards
            company_slugs = ["anthropic", "openai", "stripe", "notion", "figma"]
        
        signals = []
        
        for slug in company_slugs:
            try:
                url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
                
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.get(url)
                    
                    if response.status_code == 200:
                        data = response.json()
                        jobs = data.get("jobs", [])
                        
                        if len(jobs) >= 5:  # Company is actively hiring
                            signal = Signal(
                                signal_id=_generate_id("sig_hire"),
                                signal_type=SignalType.HIRING,
                                source="greenhouse",
                                source_url=f"https://boards.greenhouse.io/{slug}",
                                company_name=slug.replace("-", " ").title(),
                                headline=f"{slug.title()} has {len(jobs)} open positions",
                                details={
                                    "open_positions": len(jobs),
                                    "job_titles": [j.get("title") for j in jobs[:5]],
                                    "departments": list(set(j.get("departments", [{}])[0].get("name", "General") for j in jobs[:10]))
                                },
                                strength=SignalStrength.STRONG if len(jobs) >= 10 else SignalStrength.MODERATE,
                                confidence=0.80
                            )
                            
                            signal.predictions = self._generate_predictions(signal)
                            signals.append(signal)
                            
            except Exception as e:
                print(f"Greenhouse scrape error for {slug}: {e}")
        
        return signals
    
    def _generate_predictions(self, signal: Signal) -> List[Dict]:
        """Generate predicted opportunities from hiring signal"""
        predictions = []
        signal_config = SIGNAL_PREDICTIONS.get(signal.signal_type, {})
        
        for pred in signal_config.get("predictions", []):
            optimal_date = datetime.now(timezone.utc) + timedelta(days=pred["timing_days"])
            
            predictions.append({
                "need": pred["need"],
                "confidence": pred["confidence"] * signal.confidence,
                "timing_days": pred["timing_days"],
                "optimal_outreach_date": optimal_date.isoformat(),
                "estimated_value": self._estimate_value(signal, pred["need"])
            })
        
        return predictions
    
    def _estimate_value(self, signal: Signal, need: str) -> float:
        """Estimate value based on hiring volume"""
        open_positions = signal.details.get("open_positions", 1)
        
        # More hiring = bigger budget
        base_values = {
            "adjacent_role_support": 2000,
            "onboarding_content": 3000,
            "training_materials": 5000,
        }
        
        base = base_values.get(need, 2000)
        multiplier = min(open_positions / 5, 3)  # Cap at 3x
        
        return base * multiplier


class LaunchSignalScraper:
    """
    Scrape product launch signals from:
    - Product Hunt
    - Hacker News (Show HN)
    - Twitter announcements
    - Press releases
    """
    
    PRODUCTHUNT_RSS = "https://www.producthunt.com/feed"
    HN_SHOW_URL = "https://hacker-news.firebaseio.com/v0/showstories.json"
    
    async def scrape_producthunt(self) -> List[Signal]:
        """Scrape Product Hunt launches"""
        signals = []
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(self.PRODUCTHUNT_RSS)
                
                if response.status_code == 200:
                    feed = feedparser.parse(response.text)
                    
                    for entry in feed.entries[:15]:
                        title = entry.get("title", "")
                        link = entry.get("link", "")
                        summary = entry.get("summary", "")
                        
                        # Extract company/product name
                        company = title.split(" - ")[0] if " - " in title else title.split()[0]
                        
                        signal = Signal(
                            signal_id=_generate_id("sig_launch"),
                            signal_type=SignalType.LAUNCH,
                            source="producthunt",
                            source_url=link,
                            company_name=company,
                            headline=title,
                            details={
                                "tagline": summary[:200],
                                "platform": "producthunt"
                            },
                            strength=SignalStrength.STRONG,
                            confidence=0.85
                        )
                        
                        signal.predictions = self._generate_predictions(signal)
                        signals.append(signal)
                        
        except Exception as e:
            print(f"Product Hunt scrape error: {e}")
        
        return signals
    
    async def scrape_hackernews_show(self) -> List[Signal]:
        """Scrape Show HN launches"""
        signals = []
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Get Show HN story IDs
                response = await client.get(self.HN_SHOW_URL)
                
                if response.status_code == 200:
                    story_ids = response.json()[:15]
                    
                    for story_id in story_ids:
                        # Get story details
                        story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                        story_response = await client.get(story_url)
                        
                        if story_response.status_code == 200:
                            story = story_response.json()
                            title = story.get("title", "")
                            url = story.get("url", f"https://news.ycombinator.com/item?id={story_id}")
                            score = story.get("score", 0)
                            
                            if score >= 10:  # Only high-engagement launches
                                # Extract company name from Show HN title
                                company = title.replace("Show HN:", "").strip().split()[0]
                                
                                signal = Signal(
                                    signal_id=_generate_id("sig_launch"),
                                    signal_type=SignalType.LAUNCH,
                                    source="hackernews",
                                    source_url=url,
                                    company_name=company,
                                    headline=title,
                                    details={
                                        "hn_score": score,
                                        "hn_id": story_id,
                                        "platform": "hackernews"
                                    },
                                    strength=self._score_to_strength(score),
                                    confidence=0.80
                                )
                                
                                signal.predictions = self._generate_predictions(signal)
                                signals.append(signal)
                                
        except Exception as e:
            print(f"HN Show scrape error: {e}")
        
        return signals
    
    def _score_to_strength(self, score: int) -> SignalStrength:
        """Convert HN score to signal strength"""
        if score >= 100:
            return SignalStrength.VERY_STRONG
        elif score >= 50:
            return SignalStrength.STRONG
        elif score >= 20:
            return SignalStrength.MODERATE
        else:
            return SignalStrength.WEAK
    
    def _generate_predictions(self, signal: Signal) -> List[Dict]:
        """Generate predicted opportunities from launch signal"""
        predictions = []
        signal_config = SIGNAL_PREDICTIONS.get(signal.signal_type, {})
        
        for pred in signal_config.get("predictions", []):
            optimal_date = datetime.now(timezone.utc) + timedelta(days=pred["timing_days"])
            
            predictions.append({
                "need": pred["need"],
                "confidence": pred["confidence"] * signal.confidence,
                "timing_days": pred["timing_days"],
                "optimal_outreach_date": optimal_date.isoformat(),
                "estimated_value": self._estimate_value(signal, pred["need"])
            })
        
        return predictions
    
    def _estimate_value(self, signal: Signal, need: str) -> float:
        """Estimate value based on launch traction"""
        score = signal.details.get("hn_score", 10)
        
        base_values = {
            "marketing": 5000,
            "customer_support": 3000,
            "content_creation": 2000,
            "pr_outreach": 4000,
        }
        
        base = base_values.get(need, 2000)
        multiplier = min(score / 50, 3)  # Cap at 3x
        
        return base * max(multiplier, 1)


class PainPointSignalScraper:
    """
    Scrape pain point signals from:
    - Twitter complaints
    - G2/Capterra reviews
    - Reddit complaints
    - App Store reviews
    """
    
    async def scrape_twitter_pain(self, keywords: List[str] = None) -> List[Signal]:
        """Scrape Twitter for pain point signals"""
        # Note: Requires Twitter API access
        # This is a placeholder for when API is available
        return []
    
    async def scrape_reddit_pain(self, subreddits: List[str] = None) -> List[Signal]:
        """Scrape Reddit for pain point signals"""
        if not subreddits:
            subreddits = ["startups", "entrepreneur", "smallbusiness", "SaaS"]
        
        signals = []
        pain_keywords = ["struggling", "frustrated", "hate", "broken", "help", "issue", "problem", "anyone know"]
        
        for subreddit in subreddits:
            try:
                url = f"https://www.reddit.com/r/{subreddit}/new.json?limit=25"
                
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.get(url, headers={
                        "User-Agent": "AiGentsy/1.0 (Signal Detection)"
                    })
                    
                    if response.status_code == 200:
                        data = response.json()
                        posts = data.get("data", {}).get("children", [])
                        
                        for post in posts:
                            post_data = post.get("data", {})
                            title = post_data.get("title", "").lower()
                            selftext = post_data.get("selftext", "").lower()
                            combined = f"{title} {selftext}"
                            
                            # Check for pain keywords
                            if any(kw in combined for kw in pain_keywords):
                                signal = Signal(
                                    signal_id=_generate_id("sig_pain"),
                                    signal_type=SignalType.PAIN_POINT,
                                    source=f"reddit/{subreddit}",
                                    source_url=f"https://reddit.com{post_data.get('permalink', '')}",
                                    company_name=post_data.get("author", "Unknown"),
                                    headline=post_data.get("title", "")[:100],
                                    details={
                                        "subreddit": subreddit,
                                        "score": post_data.get("score", 0),
                                        "num_comments": post_data.get("num_comments", 0),
                                        "pain_keywords_found": [kw for kw in pain_keywords if kw in combined]
                                    },
                                    strength=SignalStrength.MODERATE,
                                    confidence=0.65
                                )
                                
                                signal.predictions = self._generate_predictions(signal)
                                signals.append(signal)
                                
            except Exception as e:
                print(f"Reddit pain scrape error for r/{subreddit}: {e}")
        
        return signals
    
    def _generate_predictions(self, signal: Signal) -> List[Dict]:
        """Generate predicted opportunities from pain signal"""
        predictions = []
        signal_config = SIGNAL_PREDICTIONS.get(signal.signal_type, {})
        
        for pred in signal_config.get("predictions", []):
            optimal_date = datetime.now(timezone.utc) + timedelta(days=pred["timing_days"])
            
            predictions.append({
                "need": pred["need"],
                "confidence": pred["confidence"] * signal.confidence,
                "timing_days": pred["timing_days"],
                "optimal_outreach_date": optimal_date.isoformat(),
                "estimated_value": 2000  # Pain points typically smaller value
            })
        
        return predictions


# ============================================================
# MAIN SIGNAL INGESTION ENGINE
# ============================================================

class RealSignalIngestionEngine:
    """
    Master engine that coordinates all signal scrapers
    and generates predicted opportunities
    """
    
    def __init__(self):
        self.funding_scraper = FundingSignalScraper()
        self.hiring_scraper = HiringSignalScraper()
        self.launch_scraper = LaunchSignalScraper()
        self.pain_scraper = PainPointSignalScraper()
        
        # Signal storage
        self._signals: Dict[str, Signal] = {}
        self._predicted_opportunities: Dict[str, PredictedOpportunity] = {}
        
        # Cache to avoid duplicate signals
        self._signal_hashes: set = set()
    
    async def ingest_all_signals(self) -> Dict[str, Any]:
        """
        Run all signal scrapers and generate predictions
        """
        print("\n" + "="*70)
        print("🔮 REAL SIGNAL INGESTION ENGINE")
        print("="*70)
        
        all_signals = []
        
        # FUNDING SIGNALS
        print("\n💰 Scraping funding signals...")
        funding_signals = await self.funding_scraper.scrape_techcrunch()
        all_signals.extend(funding_signals)
        print(f"   → Found {len(funding_signals)} funding signals")
        
        # HIRING SIGNALS
        print("\n👥 Scraping hiring signals...")
        hiring_signals = await self.hiring_scraper.scrape_greenhouse_jobs()
        all_signals.extend(hiring_signals)
        print(f"   → Found {len(hiring_signals)} hiring signals")
        
        # LAUNCH SIGNALS
        print("\n🚀 Scraping launch signals...")
        ph_signals = await self.launch_scraper.scrape_producthunt()
        hn_signals = await self.launch_scraper.scrape_hackernews_show()
        all_signals.extend(ph_signals)
        all_signals.extend(hn_signals)
        print(f"   → Found {len(ph_signals) + len(hn_signals)} launch signals")
        
        # PAIN SIGNALS
        print("\n😤 Scraping pain point signals...")
        pain_signals = await self.pain_scraper.scrape_reddit_pain()
        all_signals.extend(pain_signals)
        print(f"   → Found {len(pain_signals)} pain signals")
        
        # Store signals
        for signal in all_signals:
            self._signals[signal.signal_id] = signal
        
        # Generate predicted opportunities
        predicted = self._generate_all_predictions(all_signals)
        
        print(f"\n✅ TOTAL: {len(all_signals)} signals → {len(predicted)} predicted opportunities")
        print("="*70)
        
        return {
            "ok": True,
            "signals": {
                "total": len(all_signals),
                "by_type": self._count_by_type(all_signals),
                "signals": [s.to_dict() for s in all_signals]
            },
            "predictions": {
                "total": len(predicted),
                "opportunities": [p.to_dict() for p in predicted]
            },
            "timestamp": _now()
        }
    
    def _generate_all_predictions(self, signals: List[Signal]) -> List[PredictedOpportunity]:
        """Convert signals into actionable predicted opportunities"""
        opportunities = []
        
        for signal in signals:
            for pred in signal.predictions:
                opp = PredictedOpportunity(
                    opportunity_id=_generate_id("pred_opp"),
                    signal_id=signal.signal_id,
                    signal_type=signal.signal_type,
                    company_name=signal.company_name,
                    company_domain=signal.company_domain,
                    predicted_need=pred["need"],
                    confidence=pred["confidence"],
                    optimal_timing_days=pred["timing_days"],
                    optimal_outreach_date=pred["optimal_outreach_date"],
                    estimated_value=pred["estimated_value"],
                    suggested_pitch=self._generate_pitch(signal, pred),
                    urgency=self._calculate_urgency(pred)
                )
                
                opportunities.append(opp)
                self._predicted_opportunities[opp.opportunity_id] = opp
        
        # Sort by confidence and value
        opportunities.sort(key=lambda o: (o.confidence * o.estimated_value), reverse=True)
        
        return opportunities
    
    def _generate_pitch(self, signal: Signal, prediction: Dict) -> str:
        """Generate suggested pitch based on signal"""
        pitches = {
            "hiring_support": f"I noticed {signal.company_name} is growing quickly. I help companies streamline their hiring process with AI-powered candidate screening.",
            "marketing": f"Congrats on the recent momentum at {signal.company_name}! I help growing companies amplify their reach with targeted content and distribution.",
            "product_development": f"Saw {signal.company_name}'s recent growth. I specialize in helping teams ship faster with AI-assisted development.",
            "integration_work": f"I noticed {signal.company_name} is scaling up. I help companies integrate their tools and automate workflows.",
            "content_creation": f"Congrats on the launch, {signal.company_name}! I help startups create compelling content that converts.",
            "solution_provider": f"I saw your post about the challenge you're facing. I've solved similar problems for other companies.",
        }
        
        return pitches.get(prediction["need"], f"I noticed {signal.company_name} and thought I could help.")
    
    def _calculate_urgency(self, prediction: Dict) -> str:
        """Calculate urgency based on timing"""
        days = prediction["timing_days"]
        
        if days <= 3:
            return "critical"
        elif days <= 7:
            return "high"
        elif days <= 14:
            return "medium"
        else:
            return "low"
    
    def _count_by_type(self, signals: List[Signal]) -> Dict[str, int]:
        """Count signals by type"""
        counts = {}
        for signal in signals:
            signal_type = signal.signal_type.value
            counts[signal_type] = counts.get(signal_type, 0) + 1
        return counts
    
    def get_actionable_now(self) -> List[PredictedOpportunity]:
        """Get opportunities that should be acted on today"""
        today = datetime.now(timezone.utc)
        
        actionable = []
        for opp in self._predicted_opportunities.values():
            optimal_date = datetime.fromisoformat(opp.optimal_outreach_date.replace("Z", "+00:00"))
            days_until = (optimal_date - today).days
            
            if days_until <= 1 and opp.status == "pending":
                actionable.append(opp)
        
        return sorted(actionable, key=lambda o: o.confidence * o.estimated_value, reverse=True)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics"""
        return {
            "total_signals": len(self._signals),
            "total_predictions": len(self._predicted_opportunities),
            "signals_by_type": self._count_by_type(list(self._signals.values())),
            "actionable_today": len(self.get_actionable_now()),
            "total_predicted_value": sum(o.estimated_value for o in self._predicted_opportunities.values())
        }


# ============================================================
# SINGLETON
# ============================================================

_engine: Optional[RealSignalIngestionEngine] = None


def get_signal_engine() -> RealSignalIngestionEngine:
    """Get singleton engine instance"""
    global _engine
    if _engine is None:
        _engine = RealSignalIngestionEngine()
    return _engine


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    async def test():
        engine = get_signal_engine()
        results = await engine.ingest_all_signals()
        
        print(f"\n📊 RESULTS:")
        print(f"   Signals: {results['signals']['total']}")
        print(f"   Predictions: {results['predictions']['total']}")
        
        print(f"\n🎯 TOP 5 PREDICTED OPPORTUNITIES:")
        for opp in results['predictions']['opportunities'][:5]:
            print(f"   - {opp['company_name']}: {opp['predicted_need']} (${opp['estimated_value']:,.0f}, {opp['confidence']:.0%})")
    
    asyncio.run(test())
