"""
HYBRID DISCOVERY ENGINE: Perplexity + Direct Platform API Enrichment
=====================================================================

PROBLEM:
- Perplexity discovery returns AI summaries without original poster info
- Customer loop needs author/contact to send proposals
- 20+ outreach channels are wired but unused because no contact data

SOLUTION:
- Phase 1: Use Perplexity for broad internet-wide discovery (fast)
- Phase 2: Enrich each opportunity by fetching original source URL
- Phase 3: Extract author/contact from original post using platform APIs

PLATFORM API PACKS USED:
- platforms/packs/reddit_pack.py - Reddit JSON API for author extraction
- platforms/packs/twitter_v2_api.py - Twitter API for handle extraction
- platforms/packs/github_enhanced.py - GitHub API for username extraction
- platforms/packs/linkedin_api.py - LinkedIn API for profile extraction
- platforms/packs/hackernews_pack.py - HN API for username extraction

EXPECTED IMPACT:
- Before: 0-10% of opportunities have contact info
- After: 80-95% of opportunities have contact info
"""

import os
import re
import json
import logging
import hashlib
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)


class HybridDiscoveryEngine:
    """
    Hybrid discovery: Perplexity-first with direct API enrichment.

    This closes the gap between discovery and customer outreach by ensuring
    every opportunity has extractable contact info.
    """

    def __init__(self):
        self.perplexity_key = os.getenv('PERPLEXITY_API_KEY')

        # Stats tracking
        self.stats = {
            'phase1_discovered': 0,
            'phase2_enriched': 0,
            'phase2_with_contact': 0,
            'platforms_hit': {},
            'errors': []
        }

        # Platform API configs
        # Twitter: check for bearer token OR API key (for OAuth)
        self.twitter_bearer = os.getenv('TWITTER_BEARER_TOKEN')
        self.twitter_api_key = os.getenv('TWITTER_API_KEY')
        self.twitter_configured = bool(self.twitter_bearer or self.twitter_api_key)
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.reddit_configured = True  # Reddit JSON API is public
        self.linkedin_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
        self.instagram_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')

        # Import existing discovery if available
        try:
            from discovery.perplexity_first import PerplexityFirstDiscovery
            self._perplexity_engine = PerplexityFirstDiscovery()
            self._has_perplexity = True
        except ImportError:
            self._has_perplexity = False
            self._perplexity_engine = None

        # Import contact extractor
        try:
            from universal_contact_extraction import UniversalContactExtractor, enrich_opportunity_with_contact
            self._contact_extractor = UniversalContactExtractor()
            self._enrich_contact = enrich_opportunity_with_contact
            self._has_extractor = True
        except ImportError:
            self._has_extractor = False
            self._contact_extractor = None
            self._enrich_contact = None

    async def discover_with_contact(self, max_opportunities: int = 100) -> List[Dict]:
        """
        Complete hybrid discovery with contact enrichment.

        THREE-PHASE APPROACH:
        1. PERPLEXITY (PRIMARY) - Discovers across ENTIRE INTERNET
        2. DIRECT APIs (ENRICHMENT) - Adds author/contact info to Perplexity results
        3. DIRECT PLATFORMS (SUPPLEMENT) - Adds platform-native opps with built-in contact

        Returns opportunities with contact info ready for outreach.
        """
        logger.info("=" * 80)
        logger.info("🔍 HYBRID DISCOVERY - PERPLEXITY PRIMARY")
        logger.info("=" * 80)

        # ===================================================================
        # PHASE 1: PERPLEXITY - DISCOVER ACROSS ENTIRE INTERNET (PRIMARY)
        # ===================================================================
        logger.info("\n📡 PHASE 1: Perplexity Internet-Wide Discovery (PRIMARY)")

        perplexity_opportunities = await self._phase1_perplexity()
        self.stats['phase1_discovered'] = len(perplexity_opportunities)
        logger.info(f"✅ Phase 1: {len(perplexity_opportunities)} opportunities from Perplexity")

        # ===================================================================
        # PHASE 2: ENRICH PERPLEXITY RESULTS WITH CONTACT INFO
        # ===================================================================
        logger.info(f"\n🔗 PHASE 2: Enriching Perplexity Results with Direct APIs")

        # Limit before enrichment to avoid rate limits
        opps_to_enrich = perplexity_opportunities[:max_opportunities]
        enriched = await self._phase2_enrich(opps_to_enrich)

        # Count enrichment success
        enriched_with_contact = sum(1 for o in enriched if self._has_contact(o))
        logger.info(f"✅ Phase 2: {enriched_with_contact}/{len(enriched)} enriched with contact info")

        # ===================================================================
        # PHASE 3: ALWAYS ADD DIRECT PLATFORM DISCOVERIES
        # ===================================================================
        # These have contact info built-in, so ALWAYS include them
        logger.info(f"\n📍 PHASE 3: Adding Direct Platform APIs (guaranteed contact info)")
        platform_opps = await self._phase1_5_direct_platforms()
        logger.info(f"✅ Phase 3: {len(platform_opps)} opportunities from direct platforms")

        # ===================================================================
        # COMBINE & PRIORITIZE: Contact info first
        # ===================================================================
        # Platform opps (with contact) + Perplexity enriched (may have contact)
        all_opportunities = []

        # First: add platform opportunities (guaranteed contact)
        for opp in platform_opps:
            all_opportunities.append(opp)

        # Second: add Perplexity opportunities (may have contact after enrichment)
        for opp in enriched:
            # Avoid duplicates by URL
            existing_urls = {o.get('url') for o in all_opportunities if o.get('url')}
            if opp.get('url') not in existing_urls:
                all_opportunities.append(opp)

        # Sort: opportunities WITH contact come first
        all_opportunities.sort(key=lambda o: (
            0 if self._has_contact(o) else 1,  # With contact first
            0 if o.get('contact', {}).get('email') else 1,  # Email preferred
        ))

        # Take top max_opportunities
        final_opportunities = all_opportunities[:max_opportunities]

        # Final stats
        with_contact = sum(1 for o in final_opportunities if self._has_contact(o))
        self.stats['phase2_enriched'] = len(final_opportunities)
        self.stats['phase2_with_contact'] = with_contact

        logger.info("\n" + "=" * 80)
        logger.info("📊 HYBRID DISCOVERY COMPLETE")
        logger.info("=" * 80)
        logger.info(f"   Total opportunities: {len(final_opportunities)}")
        logger.info(f"   With contact info:   {with_contact} ({with_contact/len(final_opportunities)*100:.1f}%)" if final_opportunities else "   With contact: 0")
        logger.info(f"   Platform-sourced:    {len([o for o in final_opportunities if o.get('source', '').endswith('_api')])}")
        logger.info(f"   Perplexity-sourced:  {len([o for o in final_opportunities if 'perplexity' in o.get('id', '')])}")
        logger.info(f"   Ready for outreach:  {with_contact}")

        return final_opportunities

    async def _phase1_perplexity(self) -> List[Dict]:
        """Phase 1: Use Perplexity for broad discovery"""
        if self._has_perplexity and self._perplexity_engine:
            try:
                return await self._perplexity_engine.discover_all()
            except Exception as e:
                logger.error(f"Perplexity discovery failed: {e}")
                self.stats['errors'].append({'phase': 1, 'error': str(e)})

        # Fallback: direct Perplexity API call
        return await self._direct_perplexity_search()

    async def _direct_perplexity_search(self) -> List[Dict]:
        """
        Direct Perplexity API search - 100+ DIVERSIFIED QUERIES.

        Covers: 15+ industries, 20+ platforms, 30+ job types, all contact methods.
        Targets opportunities with EMAIL, TWITTER, LINKEDIN, INSTAGRAM, PHONE contact info.
        """
        if not self.perplexity_key:
            logger.warning("No Perplexity API key, skipping Phase 1")
            return []

        opportunities = []

        # ═══════════════════════════════════════════════════════════════════════════
        # 100+ DIVERSIFIED QUERIES - Organized by Category
        # ═══════════════════════════════════════════════════════════════════════════
        queries = self._get_diversified_queries()

        # Run queries in batches to avoid rate limits
        batch_size = 10
        for i in range(0, len(queries), batch_size):
            batch = queries[i:i + batch_size]
            batch_results = await asyncio.gather(*[
                self._run_single_perplexity_query(q) for q in batch
            ], return_exceptions=True)

            for result in batch_results:
                if isinstance(result, list):
                    opportunities.extend(result)

            # Small delay between batches
            if i + batch_size < len(queries):
                await asyncio.sleep(0.5)

        logger.info(f"Perplexity total: {len(opportunities)} opportunities from {len(queries)} queries")
        return opportunities

    def _get_diversified_queries(self) -> List[str]:
        """
        Generate 100+ diversified queries using site: prefixes for targeted platform search.

        Format: "site:platform.com keywords" for precise platform targeting
        """
        queries = []

        # ═══════════════════════════════════════════════════════════════════════════
        # CATEGORY 1: EMAIL-BASED OPPORTUNITIES (20 queries - highest conversion)
        # ═══════════════════════════════════════════════════════════════════════════
        queries.extend([
            "hiring developer contact email React Vue Angular immediate start",
            "freelance work email Python Django FastAPI remote contract opportunity",
            "job opportunity email mobile iOS Android Swift Kotlin urgent",
            "contract position email data science ML TensorFlow PyTorch",
            "consulting email DevOps AWS Docker Kubernetes infrastructure",
            "project needs developer email API integration microservices",
            "startup hiring CTO technical email cofounder equity opportunity",
            "email contact full-stack developer MERN MEAN stack needed",
            "blockchain developer email Solidity Web3 smart contracts DeFi",
            "automation developer email RPA Python Selenium scraping bot",
            "database expert email PostgreSQL MySQL MongoDB optimization",
            "security consultant email penetration testing audit compliance",
            "WordPress developer email plugin customization WooCommerce store",
            "Shopify expert email theme customization liquid development",
            "email contact QA automation testing Cypress Jest Playwright",
            "cloud architect email GCP Azure multi-cloud migration project",
            "frontend developer email Tailwind Next.js TypeScript SPA",
            "backend engineer email Node Express Go Rust high performance",
            "AI engineer email GPT LangChain vector databases RAG chatbot",
            "game developer email Unity Unreal C++ multiplayer network",
        ])

        # ═══════════════════════════════════════════════════════════════════════════
        # CATEGORY 2: TWITTER/X OPPORTUNITIES (15 queries with site: prefix)
        # ═══════════════════════════════════════════════════════════════════════════
        queries.extend([
            "site:twitter.com hiring developer React open work DM immediately",
            "site:twitter.com looking engineer freelance available contract",
            "site:twitter.com seeking consultant project paid remote DM",
            "site:twitter.com need developer help urgent project deadline",
            "site:x.com hiring remote developer immediate start contract",
            "site:twitter.com technical cofounder equity startup DM open",
            "site:twitter.com contract work Python automation available now",
            "site:x.com freelance mobile developer iOS Android needed",
            "site:twitter.com web3 developer needed Solidity DM open",
            "site:twitter.com DevOps engineer AWS Kubernetes available",
            "site:x.com data scientist ML project freelance contract",
            "site:twitter.com full-stack developer MERN available DM",
            "site:twitter.com API integration developer needed urgent",
            "site:x.com frontend React developer remote contract work",
            "site:twitter.com blockchain developer Web3 DM open hiring",
        ])

        # ═══════════════════════════════════════════════════════════════════════════
        # CATEGORY 3: LINKEDIN OPPORTUNITIES (15 queries)
        # ═══════════════════════════════════════════════════════════════════════════
        queries.extend([
            "site:linkedin.com hiring developer remote immediate start",
            "site:linkedin.com seeking consultant freelance contract urgent",
            "site:linkedin.com job opening software engineer contact now",
            "site:linkedin.com looking developer project work paid",
            "site:linkedin.com technical architect needed cloud AWS GCP",
            "site:linkedin.com full-stack developer React Node urgent",
            "site:linkedin.com data engineer Python Spark immediate",
            "site:linkedin.com mobile developer iOS Android contract",
            "site:linkedin.com DevOps engineer Kubernetes Docker remote",
            "site:linkedin.com security engineer penetration testing",
            "site:linkedin.com blockchain developer Solidity Web3 DeFi",
            "site:linkedin.com AI engineer machine learning GPT LLM",
            "site:linkedin.com frontend developer TypeScript React Vue",
            "site:linkedin.com backend engineer Go Rust microservices",
            "site:linkedin.com QA automation engineer Selenium Cypress",
        ])

        # ═══════════════════════════════════════════════════════════════════════════
        # CATEGORY 4: UPWORK/FREELANCE PLATFORMS (12 queries)
        # ═══════════════════════════════════════════════════════════════════════════
        queries.extend([
            "site:upwork.com React Vue web development high budget urgent",
            "site:upwork.com Python automation scraping expert needed",
            "site:upwork.com mobile app iOS Android Swift urgent project",
            "site:upwork.com blockchain Solidity Web3 smart contracts",
            "site:upwork.com DevOps AWS Kubernetes infrastructure setup",
            "site:freelancer.com full-stack MERN developer high paying",
            "site:freelancer.com data science ML model expert urgent",
            "site:freelancer.com API integration microservices expert",
            "site:fiverr.com custom enterprise development React expert",
            "site:fiverr.com automation bot Python Selenium advanced",
            "site:toptal.com developer needed urgent high budget contract",
            "site:gun.io software engineer contract remote high rate",
        ])

        # ═══════════════════════════════════════════════════════════════════════════
        # CATEGORY 5: GITHUB (Discovery only - NO auto-comments!) (5 queries)
        # ═══════════════════════════════════════════════════════════════════════════
        queries.extend([
            "site:github.com issue bounty payment reward bug fix",
            "site:github.com seeking contributors paid compensation open",
            "site:github.com help wanted bounty open source paid",
            "site:github.com feature request bounty payment offer",
            "site:github.com sponsorship opportunity open source maintainer",
        ])

        # ═══════════════════════════════════════════════════════════════════════════
        # CATEGORY 6: INDIE HACKERS / STARTUP COMMUNITIES (8 queries)
        # ═══════════════════════════════════════════════════════════════════════════
        queries.extend([
            "site:indiehackers.com looking developer cofounder equity",
            "site:indiehackers.com technical cofounder needed startup",
            "site:producthunt.com seeking developer partner equity share",
            "site:ycombinator.com hiring developer startup YC funded",
            "site:news.ycombinator.com hiring developer remote contract",
            "site:wellfound.com startup developer equity cofounder",
            "site:betalist.com technical cofounder developer needed",
            "site:crunchbase.com startup hiring developer remote funded",
        ])

        # ═══════════════════════════════════════════════════════════════════════════
        # CATEGORY 7: REDDIT (5 queries - limited to avoid noise)
        # ═══════════════════════════════════════════════════════════════════════════
        queries.extend([
            "site:reddit.com/r/forhire hiring developer budget email",
            "site:reddit.com/r/slavelabour developer needed urgent paid",
            "site:reddit.com/r/freelance_forhire technical project paid",
            "site:reddit.com/r/workonline developer contract remote",
            "site:reddit.com/r/startups technical cofounder needed equity",
        ])

        # ═══════════════════════════════════════════════════════════════════════════
        # CATEGORY 8: DISCORD/TELEGRAM COMMUNITIES (5 queries)
        # ═══════════════════════════════════════════════════════════════════════════
        queries.extend([
            "discord server hiring developer moderator paid position",
            "telegram group developer needed paid contract work",
            "discord community job posting developer remote paid",
            "telegram channel hiring developer blockchain Web3 crypto",
            "discord hiring React developer full-time contract remote",
        ])

        # ═══════════════════════════════════════════════════════════════════════════
        # CATEGORY 9: NICHE JOB BOARDS (10 queries)
        # ═══════════════════════════════════════════════════════════════════════════
        queries.extend([
            "site:weworkremotely.com developer remote contract urgent",
            "site:remoteok.io developer urgent hiring immediate start",
            "site:authenticjobs.com developer contract freelance work",
            "site:stackoverflow.com/jobs developer remote contract",
            "site:dribbble.com hiring designer developer collaboration",
            "site:behance.net project developer designer needed urgent",
            "site:angel.co developer startup equity remote contract",
            "site:hired.com developer urgent remote high salary",
            "site:dice.com developer contract remote immediate",
            "site:indeed.com developer contract remote email contact",
        ])

        # ═══════════════════════════════════════════════════════════════════════════
        # CATEGORY 10: TECH COMMUNITIES (8 queries)
        # ═══════════════════════════════════════════════════════════════════════════
        queries.extend([
            "site:dev.to hiring developer freelance contract paid",
            "site:hashnode.com developer needed technical writing",
            "site:medium.com hiring developer technical content paid",
            "site:substack.com developer needed newsletter automation",
            "site:notion.so hiring developer automation integration",
            "site:airtable.com developer needed custom automation",
            "site:zapier.com developer integration custom workflow",
            "site:make.com developer scenario automation expert needed",
        ])

        # ═══════════════════════════════════════════════════════════════════════════
        # CATEGORY 11: SPECIFIC TECH SKILLS (10 queries)
        # ═══════════════════════════════════════════════════════════════════════════
        queries.extend([
            "React.js Next.js developer hiring remote contract email contact",
            "Python developer automation data pipeline ETL hiring email",
            "Node.js Express backend developer opportunities contract",
            "iOS Android mobile app development jobs hiring email",
            "DevOps Kubernetes cloud infrastructure jobs AWS GCP",
            "AI ML engineer data scientist job hiring email contact",
            "blockchain Web3 Solidity developer opportunities crypto",
            "WordPress Shopify e-commerce developer jobs email",
            "API development integration specialist jobs microservices",
            "no-code low-code automation specialist Zapier Make n8n",
        ])

        # ═══════════════════════════════════════════════════════════════════════════
        # CATEGORY 12: INDUSTRY-SPECIFIC (10 queries)
        # ═══════════════════════════════════════════════════════════════════════════
        queries.extend([
            "fintech companies hiring developers payment crypto trading",
            "healthtech medtech startups engineer HIPAA healthcare",
            "edtech companies hiring platform LMS learning developer",
            "e-commerce businesses Shopify developer store automation",
            "real estate tech proptech companies developer MLS",
            "legaltech companies developer contract management",
            "marketing agencies hiring developer automation analytics",
            "gaming studios indie game developer Unity Unreal C++",
            "SaaS companies hiring full-stack developer B2B",
            "media content companies developer CMS video streaming",
        ])

        # ═══════════════════════════════════════════════════════════════════════════
        # CATEGORY 13: CONSULTING & AGENCIES (8 queries)
        # ═══════════════════════════════════════════════════════════════════════════
        queries.extend([
            "consulting firms hiring contract developers enterprise",
            "digital agencies freelance developers web mobile",
            "dev shops software agencies contractor positions",
            "IT consulting companies client projects developer",
            "design agencies frontend developer UX implementation",
            "staff augmentation companies developer placement",
            "managed services providers technical staff hiring",
            "fractional CTO technical advisor opportunities startup",
        ])

        # ═══════════════════════════════════════════════════════════════════════════
        # CATEGORY 14: PROJECT-BASED & GIGS (8 queries)
        # ═══════════════════════════════════════════════════════════════════════════
        queries.extend([
            "one-time coding project quick fix needed budget",
            "MVP development project startup founder email",
            "website redesign project small business owner",
            "mobile app project entrepreneur budget deadline",
            "automation scripting task paid Python budget",
            "bug fixing debugging paid task urgent developer",
            "landing page marketing site project budget email",
            "API integration webhook setup project deadline",
        ])

        # ═══════════════════════════════════════════════════════════════════════════
        # CATEGORY 15: GEOGRAPHIC/REMOTE (8 queries)
        # ═══════════════════════════════════════════════════════════════════════════
        queries.extend([
            "fully remote developer jobs US company worldwide",
            "European remote developer opportunities timezone",
            "async-first companies hiring developers remote",
            "remote-first startups hiring globally developer",
            "digital nomad friendly developer jobs anywhere",
            "work from anywhere tech positions developer",
            "LATAM developer remote jobs US company contract",
            "distributed team company hiring engineer remote",
        ])

        # ═══════════════════════════════════════════════════════════════════════════
        # CATEGORY 16: NON-TECH NEEDING TECH HELP (10 queries)
        # ═══════════════════════════════════════════════════════════════════════════
        queries.extend([
            "small business owner needing website help email contact",
            "restaurant local business online ordering system developer",
            "fitness trainer coach needing app built budget",
            "content creator needing website tool development",
            "real estate agent property website MLS integration",
            "lawyer attorney client portal legal tech developer",
            "doctor healthcare provider booking system HIPAA",
            "teacher educator learning platform LMS development",
            "artist musician portfolio site custom development",
            "non-profit volunteer management system developer",
        ])

        return queries

    async def _run_single_perplexity_query(self, query: str) -> List[Dict]:
        """
        Execute a single Perplexity query with improved prompting.

        Key improvements:
        - Explicit JSON structure in prompt
        - Platform detection from URLs
        - Better error logging
        """
        try:
            # Determine if query targets a specific platform
            target_platform = None
            if 'site:twitter.com' in query or 'site:x.com' in query:
                target_platform = 'twitter'
            elif 'site:linkedin.com' in query:
                target_platform = 'linkedin'
            elif 'site:upwork.com' in query:
                target_platform = 'upwork'
            elif 'site:reddit.com' in query:
                target_platform = 'reddit'
            elif 'site:github.com' in query:
                target_platform = 'github'

            # Build enhanced prompt with explicit JSON structure
            system_prompt = """You are a job opportunity finder searching the internet for real opportunities.

IMPORTANT: Return ONLY a valid JSON array. No explanations, no markdown, just JSON.

Each opportunity must have this exact structure:
[
  {
    "title": "Job title or opportunity description",
    "url": "Full URL to the opportunity",
    "platform": "twitter/linkedin/upwork/reddit/github/web",
    "description": "Brief description",
    "contact": "Email, @handle, or username if visible"
  }
]

Focus on RECENT opportunities (last 7 days). Include the actual URL where the opportunity was posted."""

            user_prompt = f"""Find 10 real job/project opportunities matching: {query}

Requirements:
- Must be actual job postings or project requests
- Include the real URL for each opportunity
- Extract any contact info (email, @handle, username)
- Focus on opportunities from the last week

Return as JSON array only."""

            async with httpx.AsyncClient(timeout=45) as client:
                response = await client.post(
                    "https://api.perplexity.ai/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.perplexity_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama-3.1-sonar-large-128k-online",  # Use larger model for better results
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "max_tokens": 4000,
                        "temperature": 0.1,  # Lower temperature for more focused results
                        "return_related_questions": False,
                        "search_recency_filter": "week"  # Focus on recent results
                    }
                )

                if response.is_success:
                    data = response.json()
                    content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

                    # Parse JSON
                    results = self._parse_json_from_text(content)

                    # Post-process: detect platform from URL if not set
                    processed = []
                    for r in results:
                        if isinstance(r, dict):
                            url = r.get('url', '')

                            # Detect platform from URL
                            detected_platform = self._detect_platform_from_url(url)
                            if detected_platform:
                                r['platform'] = detected_platform
                            elif target_platform:
                                r['platform'] = target_platform
                            elif not r.get('platform'):
                                r['platform'] = 'web'

                            # Add source tracking
                            r['source'] = f'perplexity_{r.get("platform", "web")}'

                            # Generate ID
                            r['id'] = f"pplx_{hashlib.md5(url.encode()).hexdigest()[:12]}"

                            processed.append(r)

                    if processed:
                        platforms = set([p.get('platform') for p in processed])
                        logger.info(f"📡 Perplexity: {len(processed)} results, platforms: {platforms}")

                    return processed
                else:
                    logger.warning(f"Perplexity API error: {response.status_code} - {response.text[:200]}")
                    return []
        except Exception as e:
            logger.error(f"Perplexity query failed: {e}")
            return []

    def _detect_platform_from_url(self, url: str) -> Optional[str]:
        """Detect platform from URL."""
        if not url:
            return None

        url_lower = url.lower()

        if 'twitter.com' in url_lower or 'x.com' in url_lower:
            return 'twitter'
        elif 'linkedin.com' in url_lower:
            return 'linkedin'
        elif 'github.com' in url_lower:
            return 'github'
        elif 'reddit.com' in url_lower or 'redd.it' in url_lower:
            return 'reddit'
        elif 'upwork.com' in url_lower:
            return 'upwork'
        elif 'freelancer.com' in url_lower:
            return 'freelancer'
        elif 'fiverr.com' in url_lower:
            return 'fiverr'
        elif 'indiehackers.com' in url_lower:
            return 'indiehackers'
        elif 'news.ycombinator.com' in url_lower:
            return 'hackernews'
        elif 'producthunt.com' in url_lower:
            return 'producthunt'
        elif 'wellfound.com' in url_lower or 'angel.co' in url_lower:
            return 'angellist'
        elif 'weworkremotely.com' in url_lower:
            return 'weworkremotely'
        elif 'remoteok.io' in url_lower or 'remoteok.com' in url_lower:
            return 'remoteok'

        return None

    async def _direct_perplexity_search_legacy(self) -> List[Dict]:
        """Legacy method - kept for reference."""
        return await self._direct_perplexity_search()

    async def _original_perplexity_search(self) -> List[Dict]:
        """Original simple search - deprecated in favor of diversified queries."""
        if not self.perplexity_key:
            return []

        opportunities = []
        queries = [
            'Find job postings for developers with email contact. Return JSON array.',
        ]

        async with httpx.AsyncClient(timeout=30) as client:
            for query in queries:
                try:
                    response = await client.post(
                        "https://api.perplexity.ai/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.perplexity_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "llama-3.1-sonar-small-128k-online",
                            "messages": [
                                {"role": "system", "content": "You are a job opportunity finder. Return only valid JSON arrays."},
                                {"role": "user", "content": query}
                            ],
                            "max_tokens": 4000,
                            "temperature": 0.2,
                            "return_related_questions": False
                        }
                    )

                    if response.is_success:
                        data = response.json()
                        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                        parsed = self._parse_json_from_text(content)
                        opportunities.extend(parsed)
                        logger.info(f"Perplexity: {len(parsed)} opportunities from query")
                    else:
                        logger.warning(f"Perplexity API error: {response.status_code}")

                except Exception as e:
                    logger.error(f"Perplexity query failed: {e}")

        return opportunities

    async def _phase1_5_direct_platforms(self) -> List[Dict]:
        """
        Phase 1.5: Direct platform discovery with author info built-in.

        Unlike Perplexity, direct platform APIs return the actual poster info:
        - Reddit: author field with username
        - Twitter: user.screen_name with handle
        - GitHub: user.login with username

        This ensures we have contact info for outreach.
        """
        opportunities = []

        # Reddit: Fetch from r/forhire, r/hiring, etc.
        if self.reddit_configured:
            reddit_opps = await self._discover_reddit_direct()
            opportunities.extend(reddit_opps)
            logger.info(f"Reddit direct: {len(reddit_opps)} opportunities with author info")

        # Twitter: Search for hiring tweets (using bearer token if available)
        if self.twitter_configured and self.twitter_bearer:
            twitter_opps = await self._discover_twitter_direct()
            opportunities.extend(twitter_opps)
            logger.info(f"Twitter direct: {len(twitter_opps)} opportunities with author info")
        elif self.twitter_configured:
            logger.info(f"Twitter: API key available but bearer token needed for search API")

        # GitHub: Search for bounty/help-wanted issues
        if self.github_token or True:  # GitHub search works without auth (with rate limits)
            github_opps = await self._discover_github_direct()
            opportunities.extend(github_opps)
            logger.info(f"GitHub direct: {len(github_opps)} opportunities with author info")

        return opportunities

    async def _discover_reddit_direct(self) -> List[Dict]:
        """Discover from Reddit directly (with author info)"""
        opportunities = []
        subreddits = ['forhire', 'hiring', 'remotejobs', 'slavelabour']

        async with httpx.AsyncClient(timeout=15) as client:
            for subreddit in subreddits[:2]:  # Limit to avoid rate limits
                try:
                    url = f"https://www.reddit.com/r/{subreddit}/new.json?limit=10"
                    response = await client.get(
                        url,
                        headers={'User-Agent': 'AiGentsy/1.0'}
                    )

                    if response.is_success:
                        data = response.json()
                        posts = data.get('data', {}).get('children', [])

                        for post in posts:
                            post_data = post.get('data', {})
                            author = post_data.get('author')

                            if author and author != '[deleted]':
                                opp = {
                                    'id': f"reddit_{post_data.get('id', '')}",
                                    'title': post_data.get('title', ''),
                                    'body': post_data.get('selftext', ''),
                                    'url': f"https://reddit.com{post_data.get('permalink', '')}",
                                    'platform': 'reddit',
                                    'source': 'reddit_api',
                                    'contact': {
                                        'platform': 'reddit',
                                        'platform_user_id': author,
                                        'reddit_username': author,
                                        'preferred_outreach': 'reddit_dm',
                                        'extraction_source': 'reddit_api_direct'
                                    },
                                    'metadata': {
                                        'subreddit': subreddit,
                                        'poster_username': author,
                                        'score': post_data.get('score', 0),
                                    }
                                }
                                opportunities.append(opp)

                    await asyncio.sleep(1)  # Reddit rate limit

                except Exception as e:
                    logger.debug(f"Reddit direct discovery failed for r/{subreddit}: {e}")

        return opportunities

    async def _discover_twitter_direct(self) -> List[Dict]:
        """Discover from Twitter directly (with author info)"""
        if not self.twitter_bearer:
            return []

        opportunities = []

        queries = [
            'hiring developer -is:retweet lang:en',
            'looking for freelancer -is:retweet lang:en',
        ]

        async with httpx.AsyncClient(timeout=15) as client:
            for query in queries[:1]:  # Limit to avoid rate limits
                try:
                    response = await client.get(
                        'https://api.twitter.com/2/tweets/search/recent',
                        params={
                            'query': query,
                            'max_results': 10,
                            'tweet.fields': 'created_at,author_id',
                            'expansions': 'author_id',
                            'user.fields': 'username'
                        },
                        headers={'Authorization': f'Bearer {self.twitter_bearer}'}
                    )

                    if response.is_success:
                        data = response.json()
                        tweets = data.get('data', [])
                        users = {u['id']: u for u in data.get('includes', {}).get('users', [])}

                        for tweet in tweets:
                            user = users.get(tweet.get('author_id'), {})
                            username = user.get('username')

                            if username:
                                opp = {
                                    'id': f"twitter_{tweet.get('id', '')}",
                                    'title': tweet.get('text', '')[:100],
                                    'body': tweet.get('text', ''),
                                    'url': f"https://twitter.com/{username}/status/{tweet.get('id')}",
                                    'platform': 'twitter',
                                    'source': 'twitter_api',
                                    'contact': {
                                        'platform': 'twitter',
                                        'platform_user_id': username,
                                        'twitter_handle': username,
                                        'preferred_outreach': 'twitter_dm',
                                        'extraction_source': 'twitter_api_direct'
                                    },
                                    'metadata': {
                                        'poster_handle': username,
                                        'tweet_id': tweet.get('id'),
                                    }
                                }
                                opportunities.append(opp)

                except Exception as e:
                    logger.debug(f"Twitter direct discovery failed: {e}")

        return opportunities

    async def _discover_github_direct(self) -> List[Dict]:
        """Discover from GitHub directly (with author info)"""
        opportunities = []

        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'AiGentsy-Discovery'
        }
        if self.github_token:
            headers['Authorization'] = f'token {self.github_token}'

        queries = [
            'bounty OR paid in:title is:open',
            'help wanted in:labels is:open',
        ]

        async with httpx.AsyncClient(timeout=15) as client:
            for query in queries[:1]:  # Limit
                try:
                    response = await client.get(
                        'https://api.github.com/search/issues',
                        params={
                            'q': query,
                            'sort': 'created',
                            'order': 'desc',
                            'per_page': 10
                        },
                        headers=headers
                    )

                    if response.is_success:
                        data = response.json()
                        issues = data.get('items', [])

                        for issue in issues:
                            user = issue.get('user', {})
                            username = user.get('login')

                            if username:
                                opp = {
                                    'id': f"github_{issue.get('id', '')}",
                                    'title': issue.get('title', ''),
                                    'body': issue.get('body', ''),
                                    'url': issue.get('html_url', ''),
                                    'platform': 'github',
                                    'source': 'github_api',
                                    'contact': {
                                        'platform': 'github',
                                        'platform_user_id': username,
                                        'github_username': username,
                                        'preferred_outreach': 'github_comment',
                                        'extraction_source': 'github_api_direct'
                                    },
                                    'metadata': {
                                        'poster_username': username,
                                        'issue_number': issue.get('number'),
                                        'labels': [l.get('name') for l in issue.get('labels', [])],
                                    }
                                }
                                opportunities.append(opp)

                except Exception as e:
                    logger.debug(f"GitHub direct discovery failed: {e}")

        return opportunities

    async def _phase2_enrich(self, opportunities: List[Dict]) -> List[Dict]:
        """
        Phase 2: Enrich opportunities with author/contact from original source.

        For each opportunity:
        1. Detect platform from URL
        2. Fetch original post via platform API
        3. Extract author/contact info
        """
        enriched = []

        # Group by platform for efficient batching
        by_platform = self._group_by_platform(opportunities)

        # Enrich Reddit opportunities
        if by_platform.get('reddit'):
            reddit_enriched = await self._enrich_reddit(by_platform['reddit'])
            enriched.extend(reddit_enriched)
            self.stats['platforms_hit']['reddit'] = len(reddit_enriched)

        # Enrich Twitter opportunities
        if by_platform.get('twitter'):
            twitter_enriched = await self._enrich_twitter(by_platform['twitter'])
            enriched.extend(twitter_enriched)
            self.stats['platforms_hit']['twitter'] = len(twitter_enriched)

        # Enrich GitHub opportunities
        if by_platform.get('github'):
            github_enriched = await self._enrich_github(by_platform['github'])
            enriched.extend(github_enriched)
            self.stats['platforms_hit']['github'] = len(github_enriched)

        # Enrich HackerNews opportunities
        if by_platform.get('hackernews'):
            hn_enriched = await self._enrich_hackernews(by_platform['hackernews'])
            enriched.extend(hn_enriched)
            self.stats['platforms_hit']['hackernews'] = len(hn_enriched)

        # Enrich LinkedIn (if we have token)
        if by_platform.get('linkedin') and os.getenv('LINKEDIN_ACCESS_TOKEN'):
            linkedin_enriched = await self._enrich_linkedin(by_platform['linkedin'])
            enriched.extend(linkedin_enriched)
            self.stats['platforms_hit']['linkedin'] = len(linkedin_enriched)

        # Other platforms - pass through with basic enrichment
        for platform in ['upwork', 'fiverr', 'other']:
            if by_platform.get(platform):
                for opp in by_platform[platform]:
                    opp = self._basic_enrich(opp)
                    enriched.append(opp)
                self.stats['platforms_hit'][platform] = len(by_platform.get(platform, []))

        return enriched

    def _group_by_platform(self, opportunities: List[Dict]) -> Dict[str, List[Dict]]:
        """Group opportunities by platform based on URL"""
        grouped: Dict[str, List[Dict]] = {}

        for opp in opportunities:
            url = opp.get('url', '') or opp.get('canonical_url', '')
            platform = self._detect_platform(url)

            if platform not in grouped:
                grouped[platform] = []
            grouped[platform].append(opp)

        return grouped

    def _detect_platform(self, url: str) -> str:
        """Detect platform from URL"""
        if not url:
            return 'other'

        url_lower = url.lower()

        if 'reddit.com' in url_lower or 'redd.it' in url_lower:
            return 'reddit'
        elif 'twitter.com' in url_lower or 'x.com' in url_lower:
            return 'twitter'
        elif 'github.com' in url_lower:
            return 'github'
        elif 'news.ycombinator.com' in url_lower or 'hackernews' in url_lower:
            return 'hackernews'
        elif 'linkedin.com' in url_lower:
            return 'linkedin'
        elif 'upwork.com' in url_lower:
            return 'upwork'
        elif 'fiverr.com' in url_lower:
            return 'fiverr'
        else:
            return 'other'

    # =========================================================================
    # PLATFORM-SPECIFIC ENRICHMENT
    # =========================================================================

    async def _enrich_reddit(self, opportunities: List[Dict]) -> List[Dict]:
        """
        Enrich Reddit opportunities with author from JSON API.

        Reddit's .json endpoint returns post author without authentication.
        """
        enriched = []

        async with httpx.AsyncClient(timeout=15) as client:
            for opp in opportunities:
                url = opp.get('url', '')

                # Convert to JSON API endpoint
                json_url = self._reddit_to_json_url(url)
                if not json_url:
                    enriched.append(self._basic_enrich(opp))
                    continue

                try:
                    response = await client.get(
                        json_url,
                        headers={'User-Agent': 'AiGentsy/1.0'},
                        follow_redirects=True
                    )

                    if response.is_success:
                        data = response.json()
                        author = self._extract_reddit_author(data)

                        if author:
                            opp['contact'] = {
                                'platform': 'reddit',
                                'platform_user_id': author,
                                'reddit_username': author,
                                'preferred_outreach': 'reddit_dm',
                                'extraction_source': 'reddit_json_api'
                            }
                            opp['metadata'] = opp.get('metadata', {})
                            opp['metadata']['poster_username'] = author
                            logger.debug(f"Reddit enriched: u/{author}")

                    enriched.append(opp)

                    # Rate limit respect
                    await asyncio.sleep(0.5)

                except Exception as e:
                    logger.debug(f"Reddit enrichment failed for {url}: {e}")
                    enriched.append(self._basic_enrich(opp))

        return enriched

    def _reddit_to_json_url(self, url: str) -> Optional[str]:
        """Convert Reddit URL to JSON API endpoint"""
        if not url or 'reddit' not in url.lower():
            return None

        # Clean URL
        url = url.rstrip('/')

        # Handle various Reddit URL formats
        # https://www.reddit.com/r/forhire/comments/abc123/title -> .json
        if '/comments/' in url:
            return url + '.json'

        # Handle short URLs
        if 'redd.it' in url:
            return None  # Need to resolve first

        return url + '.json'

    def _extract_reddit_author(self, data: Any) -> Optional[str]:
        """Extract author from Reddit JSON response"""
        try:
            # Reddit returns array [post_listing, comments_listing]
            if isinstance(data, list) and len(data) > 0:
                post_data = data[0].get('data', {}).get('children', [{}])[0].get('data', {})
                author = post_data.get('author')
                if author and author != '[deleted]':
                    return author

            # Handle direct post response
            if isinstance(data, dict):
                if 'data' in data:
                    children = data.get('data', {}).get('children', [])
                    if children:
                        author = children[0].get('data', {}).get('author')
                        if author and author != '[deleted]':
                            return author
        except Exception as e:
            logger.debug(f"Reddit author extraction failed: {e}")

        return None

    async def _enrich_twitter(self, opportunities: List[Dict]) -> List[Dict]:
        """
        Enrich Twitter opportunities with author handle.

        Uses Twitter v2 API if bearer token available.
        """
        enriched = []

        if not self.twitter_bearer:
            # Fallback: extract handle from URL
            for opp in opportunities:
                url = opp.get('url', '')
                handle = self._extract_twitter_handle_from_url(url)
                if handle:
                    opp['contact'] = {
                        'platform': 'twitter',
                        'platform_user_id': handle,
                        'twitter_handle': handle,
                        'preferred_outreach': 'twitter_dm',
                        'extraction_source': 'url_parse'
                    }
                    opp['metadata'] = opp.get('metadata', {})
                    opp['metadata']['poster_handle'] = handle
                enriched.append(opp)
            return enriched

        async with httpx.AsyncClient(timeout=15) as client:
            for opp in opportunities:
                url = opp.get('url', '')
                tweet_id = self._extract_tweet_id(url)

                if tweet_id:
                    try:
                        response = await client.get(
                            f'https://api.twitter.com/2/tweets/{tweet_id}',
                            params={
                                'expansions': 'author_id',
                                'user.fields': 'username'
                            },
                            headers={'Authorization': f'Bearer {self.twitter_bearer}'}
                        )

                        if response.is_success:
                            data = response.json()
                            users = data.get('includes', {}).get('users', [])
                            if users:
                                handle = users[0].get('username')
                                if handle:
                                    opp['contact'] = {
                                        'platform': 'twitter',
                                        'platform_user_id': handle,
                                        'twitter_handle': handle,
                                        'preferred_outreach': 'twitter_dm',
                                        'extraction_source': 'twitter_api'
                                    }
                                    opp['metadata'] = opp.get('metadata', {})
                                    opp['metadata']['poster_handle'] = handle
                                    logger.debug(f"Twitter enriched: @{handle}")

                        await asyncio.sleep(0.2)

                    except Exception as e:
                        logger.debug(f"Twitter enrichment failed: {e}")

                enriched.append(opp)

        return enriched

    def _extract_twitter_handle_from_url(self, url: str) -> Optional[str]:
        """Extract Twitter handle from URL"""
        # https://twitter.com/username/status/123
        match = re.search(r'(?:twitter\.com|x\.com)/([^/]+)/status', url)
        if match:
            return match.group(1)
        return None

    def _extract_tweet_id(self, url: str) -> Optional[str]:
        """Extract tweet ID from URL"""
        match = re.search(r'/status/(\d+)', url)
        if match:
            return match.group(1)
        return None

    async def _enrich_github(self, opportunities: List[Dict]) -> List[Dict]:
        """
        Enrich GitHub opportunities with author username.

        Uses GitHub REST API.
        """
        enriched = []

        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'AiGentsy-Discovery'
        }
        if self.github_token:
            headers['Authorization'] = f'token {self.github_token}'

        async with httpx.AsyncClient(timeout=15) as client:
            for opp in opportunities:
                url = opp.get('url', '')
                api_url = self._github_to_api_url(url)

                if api_url:
                    try:
                        response = await client.get(api_url, headers=headers)

                        if response.is_success:
                            data = response.json()
                            user = data.get('user', {})
                            username = user.get('login')

                            if username:
                                opp['contact'] = {
                                    'platform': 'github',
                                    'platform_user_id': username,
                                    'github_username': username,
                                    'preferred_outreach': 'github_comment',
                                    'extraction_source': 'github_api'
                                }
                                opp['metadata'] = opp.get('metadata', {})
                                opp['metadata']['poster_username'] = username
                                logger.debug(f"GitHub enriched: {username}")

                        await asyncio.sleep(0.2)

                    except Exception as e:
                        logger.debug(f"GitHub enrichment failed: {e}")

                enriched.append(opp)

        return enriched

    def _github_to_api_url(self, url: str) -> Optional[str]:
        """Convert GitHub URL to API endpoint"""
        # https://github.com/owner/repo/issues/123
        match = re.search(r'github\.com/([^/]+)/([^/]+)/issues/(\d+)', url)
        if match:
            owner, repo, issue_num = match.groups()
            return f'https://api.github.com/repos/{owner}/{repo}/issues/{issue_num}'

        # https://github.com/owner/repo/discussions/123
        match = re.search(r'github\.com/([^/]+)/([^/]+)/discussions/(\d+)', url)
        if match:
            owner, repo, disc_num = match.groups()
            return f'https://api.github.com/repos/{owner}/{repo}/discussions/{disc_num}'

        return None

    async def _enrich_hackernews(self, opportunities: List[Dict]) -> List[Dict]:
        """
        Enrich HackerNews opportunities with author username.

        Uses HN Firebase API (public, no auth needed).
        """
        enriched = []

        async with httpx.AsyncClient(timeout=15) as client:
            for opp in opportunities:
                url = opp.get('url', '')
                item_id = self._extract_hn_item_id(url)

                if item_id:
                    try:
                        response = await client.get(
                            f'https://hacker-news.firebaseio.com/v0/item/{item_id}.json'
                        )

                        if response.is_success:
                            data = response.json()
                            if data:
                                author = data.get('by')
                                if author:
                                    opp['contact'] = {
                                        'platform': 'hackernews',
                                        'platform_user_id': author,
                                        'hackernews_username': author,
                                        'preferred_outreach': 'hn_reply',
                                        'extraction_source': 'hn_api'
                                    }
                                    opp['metadata'] = opp.get('metadata', {})
                                    opp['metadata']['poster_username'] = author
                                    logger.debug(f"HN enriched: {author}")

                        await asyncio.sleep(0.1)

                    except Exception as e:
                        logger.debug(f"HN enrichment failed: {e}")

                enriched.append(opp)

        return enriched

    def _extract_hn_item_id(self, url: str) -> Optional[str]:
        """Extract HN item ID from URL"""
        match = re.search(r'id=(\d+)', url)
        if match:
            return match.group(1)
        return None

    async def _enrich_linkedin(self, opportunities: List[Dict]) -> List[Dict]:
        """Enrich LinkedIn opportunities (requires OAuth token)"""
        # LinkedIn API requires OAuth - pass through with URL-based enrichment
        enriched = []
        for opp in opportunities:
            url = opp.get('url', '')
            # Extract job ID from URL
            match = re.search(r'/jobs/view/(\d+)', url)
            if match:
                job_id = match.group(1)
                opp['contact'] = {
                    'platform': 'linkedin',
                    'platform_user_id': job_id,
                    'preferred_outreach': 'linkedin_apply',
                    'extraction_source': 'url_parse'
                }
            enriched.append(opp)
        return enriched

    def _basic_enrich(self, opp: Dict) -> Dict:
        """
        Basic enrichment for platforms without direct API access.

        Extracts ALL contact methods from opportunity body:
        - Email addresses
        - Twitter handles (@username)
        - LinkedIn URLs
        - Discord usernames
        - Telegram handles
        - Phone numbers
        - Website URLs with contact pages
        """
        if self._has_extractor and self._enrich_contact:
            try:
                opp = self._enrich_contact(opp)
            except Exception:
                pass

        # Combine all text fields for extraction
        text = ' '.join([
            opp.get('body', '') or '',
            opp.get('summary', '') or '',
            opp.get('title', '') or '',
            opp.get('description', '') or '',
        ])

        if not text.strip():
            return opp

        opp['contact'] = opp.get('contact', {})

        # 1. Extract email (highest priority)
        email_match = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', text)
        if email_match:
            email = email_match.group(0)
            # Filter out common non-contact emails
            if not any(x in email.lower() for x in ['example.com', 'test.com', 'noreply', 'no-reply']):
                opp['contact']['email'] = email
                opp['contact']['preferred_outreach'] = 'email'

        # 2. Extract Twitter handle
        twitter_match = re.search(r'(?:twitter\.com/|@)([a-zA-Z0-9_]{1,15})\b', text, re.IGNORECASE)
        if twitter_match:
            handle = twitter_match.group(1)
            if handle.lower() not in ['twitter', 'x', 'com']:
                opp['contact']['twitter_handle'] = handle
                if not opp['contact'].get('preferred_outreach'):
                    opp['contact']['preferred_outreach'] = 'twitter_dm'

        # 3. Extract LinkedIn URL/ID
        linkedin_match = re.search(r'linkedin\.com/in/([a-zA-Z0-9-]+)', text, re.IGNORECASE)
        if linkedin_match:
            opp['contact']['linkedin_id'] = linkedin_match.group(1)
            if not opp['contact'].get('preferred_outreach'):
                opp['contact']['preferred_outreach'] = 'linkedin_message'

        # 4. Extract Discord username
        discord_match = re.search(r'(?:discord(?:\.gg)?[:\s]+)?([a-zA-Z0-9_]+#\d{4})', text, re.IGNORECASE)
        if discord_match:
            opp['contact']['discord'] = discord_match.group(1)

        # 5. Extract Telegram handle
        telegram_match = re.search(r'(?:t\.me/|telegram[:\s]+@?)([a-zA-Z0-9_]{5,32})', text, re.IGNORECASE)
        if telegram_match:
            opp['contact']['telegram'] = telegram_match.group(1)

        # 6. Extract phone number (basic pattern)
        phone_match = re.search(r'\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
        if phone_match:
            opp['contact']['phone'] = phone_match.group(0)
            if not opp['contact'].get('preferred_outreach'):
                opp['contact']['preferred_outreach'] = 'sms'

        # 7. Extract Instagram handle
        insta_match = re.search(r'(?:instagram\.com/|ig[:\s]+@?)([a-zA-Z0-9_.]+)', text, re.IGNORECASE)
        if insta_match:
            handle = insta_match.group(1)
            if handle.lower() not in ['instagram', 'com', 'p', 'reel']:
                opp['contact']['instagram_handle'] = handle
                if not opp['contact'].get('preferred_outreach'):
                    opp['contact']['preferred_outreach'] = 'instagram_dm'

        # Set platform if we found any contact
        if opp['contact'] and not opp['contact'].get('platform'):
            opp['contact']['platform'] = opp.get('platform', 'other')
            opp['contact']['extraction_source'] = 'text_extraction'

        return opp

    def _has_contact(self, opp: Dict) -> bool:
        """Check if opportunity has contact info"""
        contact = opp.get('contact', {})
        if not contact:
            return False

        # Check for any valid contact method
        return any([
            contact.get('email'),
            contact.get('twitter_handle'),
            contact.get('reddit_username'),
            contact.get('github_username'),
            contact.get('hackernews_username'),
            contact.get('platform_user_id'),
        ])

    def _parse_json_from_text(self, text: str) -> List[Dict]:
        """Parse JSON array from text response"""
        opportunities = []

        # Try to find JSON array in response
        try:
            # Try direct parse
            data = json.loads(text)
            if isinstance(data, list):
                return data
        except:
            pass

        # Try to extract JSON from markdown code block
        code_block_match = re.search(r'```(?:json)?\s*(\[[\s\S]*?\])\s*```', text)
        if code_block_match:
            try:
                return json.loads(code_block_match.group(1))
            except:
                pass

        # Try to find array anywhere in text
        array_match = re.search(r'\[[\s\S]*\]', text)
        if array_match:
            try:
                return json.loads(array_match.group(0))
            except:
                pass

        return []

    def get_stats(self) -> Dict[str, Any]:
        """Get enrichment statistics"""
        total = self.stats['phase2_enriched']
        with_contact = self.stats['phase2_with_contact']

        return {
            'phase1_discovered': self.stats['phase1_discovered'],
            'phase2_enriched': self.stats['phase2_enriched'],
            'phase2_with_contact': with_contact,
            'contact_rate': f"{with_contact/total*100:.1f}%" if total > 0 else "0%",
            'platforms_hit': self.stats['platforms_hit'],
            'errors': self.stats['errors']
        }


# Singleton instance
_hybrid_engine: Optional[HybridDiscoveryEngine] = None


def get_hybrid_discovery() -> HybridDiscoveryEngine:
    """Get singleton hybrid discovery engine"""
    global _hybrid_engine
    if _hybrid_engine is None:
        _hybrid_engine = HybridDiscoveryEngine()
    return _hybrid_engine


async def discover_with_contact(max_opportunities: int = 100) -> List[Dict]:
    """
    Convenience function for hybrid discovery with contact enrichment.

    Use this in integration routes:

        from discovery.hybrid_discovery import discover_with_contact
        opportunities = await discover_with_contact(max_opportunities=50)
    """
    engine = get_hybrid_discovery()
    return await engine.discover_with_contact(max_opportunities)
