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
        """Generate 100+ diversified queries across industries, platforms, and job types."""
        queries = []

        # ═══════════════════════════════════════════════════════════════════════════
        # CATEGORY 1: EMAIL-BASED OPPORTUNITIES (Highest Conversion)
        # ═══════════════════════════════════════════════════════════════════════════
        queries.extend([
            'Find freelance job postings that include email contact. Return JSON: [{"title":"...","url":"...","email":"...","platform":"..."}]',
            'Find "email me at" or "contact:" in job postings for developers. Return JSON with email field.',
            'Find startup job posts on AngelList/Wellfound with founder email. Return JSON: [{"title":"...","url":"...","email":"...","company":"..."}]',
            'Find consulting gigs posted with direct email contact. Return JSON array with email field.',
            'Find remote job postings that say "apply via email" or include recruiter email. Return JSON.',
            'Find "send resume to" job postings for tech roles. Return JSON: [{"title":"...","url":"...","email":"..."}]',
            'Find small business owners posting jobs with their email on Craigslist, Indeed, ZipRecruiter. Return JSON.',
            'Find "reach out to me at" posts from people hiring developers. Return JSON with email.',
            'Find job posts in tech Facebook groups that include email contact. Return JSON array.',
            'Find newsletter job boards (like Pallet, Polywork) with direct contact emails. Return JSON.',
        ])

        # ═══════════════════════════════════════════════════════════════════════════
        # CATEGORY 2: TWITTER/X OPPORTUNITIES
        # ═══════════════════════════════════════════════════════════════════════════
        queries.extend([
            'Find tweets with "hiring" or "looking for" developers. Return JSON: [{"title":"...","url":"...","twitter_handle":"@...","platform":"twitter"}]',
            'Find Twitter posts from founders hiring their first engineer. Return JSON with twitter_handle.',
            'Find #hiring #remotework #developer tweets from the past week. Return JSON array.',
            'Find "DM me" job opportunity tweets for freelancers. Return JSON: [{"title":"...","twitter_handle":"@..."}]',
            'Find Twitter threads about startup job openings with contact info. Return JSON.',
            'Find tweets from indie hackers looking for co-founders or contractors. Return JSON with handle.',
            'Find "we\'re hiring" tweets from tech companies with < 50 employees. Return JSON.',
            'Find Twitter job posts for React, Python, Node.js developers. Return JSON with twitter_handle.',
            'Find #buildinpublic founders tweeting about hiring help. Return JSON array.',
            'Find Twitter posts offering paid bounties or bug fixes. Return JSON with contact.',
        ])

        # ═══════════════════════════════════════════════════════════════════════════
        # CATEGORY 3: LINKEDIN OPPORTUNITIES
        # ═══════════════════════════════════════════════════════════════════════════
        queries.extend([
            'Find LinkedIn posts from recruiters hiring developers. Return JSON: [{"title":"...","url":"...","linkedin_url":"...","platform":"linkedin"}]',
            'Find LinkedIn job posts from startup founders. Return JSON with linkedin_url.',
            'Find "open to work" connection requests or hiring managers posting jobs. Return JSON.',
            'Find LinkedIn articles about companies expanding their tech teams. Return JSON with contact.',
            'Find CTOs or VPs of Engineering posting about open roles on LinkedIn. Return JSON.',
            'Find LinkedIn posts about freelance or contract opportunities in tech. Return JSON.',
            'Find remote job announcements on LinkedIn from fully-remote companies. Return JSON.',
            'Find LinkedIn posts with "comment for info" about job openings. Return JSON with url.',
            'Find consulting opportunities posted by LinkedIn members. Return JSON array.',
            'Find LinkedIn job posts for AI/ML, data science, or DevOps roles. Return JSON.',
        ])

        # ═══════════════════════════════════════════════════════════════════════════
        # CATEGORY 4: REDDIT OPPORTUNITIES
        # ═══════════════════════════════════════════════════════════════════════════
        queries.extend([
            'Find r/forhire posts from people hiring developers with email in post. Return JSON: [{"title":"...","url":"...","email":"...","reddit_user":"...","platform":"reddit"}]',
            'Find r/hiring posts for remote software engineers. Return JSON with reddit_user.',
            'Find r/slavelabour paid tasks for programming or automation. Return JSON array.',
            'Find r/freelance job opportunities with budget mentioned. Return JSON with contact.',
            'Find r/remotejobs posts from startups hiring. Return JSON: [{"title":"...","url":"...","reddit_user":"..."}]',
            'Find r/webdev or r/learnprogramming posts where someone needs help building something. Return JSON.',
            'Find r/startups posts from founders looking for technical co-founders. Return JSON.',
            'Find r/entrepreneur posts about needing developer help. Return JSON with contact info.',
            'Find r/smallbusiness posts from owners needing websites or apps built. Return JSON.',
            'Find Reddit posts in any subreddit offering paid work for coding. Return JSON array.',
        ])

        # ═══════════════════════════════════════════════════════════════════════════
        # CATEGORY 5: FREELANCE PLATFORMS
        # ═══════════════════════════════════════════════════════════════════════════
        queries.extend([
            'Find new Upwork job posts for web development posted today. Return JSON: [{"title":"...","url":"...","budget":"...","platform":"upwork"}]',
            'Find Freelancer.com projects for Python or JavaScript developers. Return JSON.',
            'Find Fiverr buyer requests for app development. Return JSON array.',
            'Find Toptal or Turing job matches for senior developers. Return JSON with url.',
            'Find PeoplePerHour projects for automation or scripting. Return JSON.',
            'Find Guru.com projects for full-stack development. Return JSON with budget.',
            'Find 99designs or Dribbble job posts for developer+designer roles. Return JSON.',
            'Find Contra or Braintrust freelance opportunities for engineers. Return JSON.',
            'Find Arc.dev or Gun.io job listings for remote developers. Return JSON array.',
            'Find Flexjobs or We Work Remotely listings for software roles. Return JSON.',
        ])

        # ═══════════════════════════════════════════════════════════════════════════
        # CATEGORY 6: STARTUP & TECH JOBS
        # ═══════════════════════════════════════════════════════════════════════════
        queries.extend([
            'Find Y Combinator companies currently hiring engineers. Return JSON: [{"title":"...","url":"...","company":"...","email":"..."}]',
            'Find AngelList/Wellfound startup jobs with equity offered. Return JSON.',
            'Find Hacker News "Who is Hiring" thread jobs for this month. Return JSON array.',
            'Find Product Hunt launched startups that are hiring. Return JSON with contact.',
            'Find TechCrunch featured startups with open positions. Return JSON.',
            'Find Indie Hackers posts from founders looking for developers. Return JSON with email.',
            'Find startup accelerator companies (Techstars, 500) hiring. Return JSON.',
            'Find seed-stage startups posting engineering jobs. Return JSON with url.',
            'Find Series A companies expanding their engineering teams. Return JSON array.',
            'Find bootstrapped SaaS companies hiring developers. Return JSON with contact.',
        ])

        # ═══════════════════════════════════════════════════════════════════════════
        # CATEGORY 7: SPECIFIC TECH SKILLS
        # ═══════════════════════════════════════════════════════════════════════════
        queries.extend([
            'Find jobs specifically for React.js or Next.js developers. Return JSON: [{"title":"...","url":"...","contact":"...","skills":"react"}]',
            'Find Python developer jobs for automation or data work. Return JSON.',
            'Find Node.js or Express backend developer opportunities. Return JSON array.',
            'Find iOS or Android mobile app development jobs. Return JSON with contact.',
            'Find DevOps, Kubernetes, or cloud infrastructure jobs. Return JSON.',
            'Find AI/ML engineer or data scientist job postings. Return JSON with email.',
            'Find blockchain or Web3 developer opportunities. Return JSON array.',
            'Find WordPress, Shopify, or e-commerce developer jobs. Return JSON.',
            'Find API development or integration specialist jobs. Return JSON with contact.',
            'Find no-code/low-code automation specialist jobs (Zapier, Make). Return JSON.',
        ])

        # ═══════════════════════════════════════════════════════════════════════════
        # CATEGORY 8: INDUSTRY-SPECIFIC
        # ═══════════════════════════════════════════════════════════════════════════
        queries.extend([
            'Find fintech companies hiring developers. Return JSON: [{"title":"...","url":"...","industry":"fintech","contact":"..."}]',
            'Find healthtech or medtech startups looking for engineers. Return JSON.',
            'Find edtech companies hiring for their platforms. Return JSON array.',
            'Find e-commerce businesses needing Shopify developers. Return JSON with email.',
            'Find real estate tech companies hiring developers. Return JSON.',
            'Find legal tech (legaltech) companies with open positions. Return JSON.',
            'Find marketing agencies hiring developers for client work. Return JSON.',
            'Find gaming studios or indie game developers hiring. Return JSON with contact.',
            'Find SaaS companies hiring full-stack developers. Return JSON array.',
            'Find media or content companies needing tech help. Return JSON.',
        ])

        # ═══════════════════════════════════════════════════════════════════════════
        # CATEGORY 9: CONSULTING & AGENCIES
        # ═══════════════════════════════════════════════════════════════════════════
        queries.extend([
            'Find consulting firms hiring contract developers. Return JSON: [{"title":"...","url":"...","contact":"...","type":"consulting"}]',
            'Find digital agencies looking for freelance developers. Return JSON.',
            'Find dev shops or software agencies with open contractor positions. Return JSON.',
            'Find IT consulting companies hiring for client projects. Return JSON with email.',
            'Find design agencies needing frontend developer help. Return JSON array.',
            'Find boutique consulting firms hiring specialists. Return JSON.',
            'Find staff augmentation companies looking for developers. Return JSON with contact.',
            'Find managed services providers hiring technical staff. Return JSON.',
            'Find innovation labs or R&D consultancies hiring. Return JSON array.',
            'Find fractional CTO or technical advisor opportunities. Return JSON.',
        ])

        # ═══════════════════════════════════════════════════════════════════════════
        # CATEGORY 10: PROJECT-BASED & GIGS
        # ═══════════════════════════════════════════════════════════════════════════
        queries.extend([
            'Find one-time coding projects or quick fixes needed. Return JSON: [{"title":"...","url":"...","budget":"...","contact":"..."}]',
            'Find MVP development projects for startups. Return JSON with email.',
            'Find website redesign projects from small businesses. Return JSON.',
            'Find mobile app projects from entrepreneurs. Return JSON array.',
            'Find automation or scripting one-off tasks. Return JSON with contact.',
            'Find data migration or integration projects. Return JSON.',
            'Find bug fixing or debugging paid tasks. Return JSON with budget.',
            'Find code review or audit projects. Return JSON array.',
            'Find landing page or marketing site projects. Return JSON with email.',
            'Find API integration or webhook setup projects. Return JSON.',
        ])

        # ═══════════════════════════════════════════════════════════════════════════
        # CATEGORY 11: GEOGRAPHIC/REMOTE
        # ═══════════════════════════════════════════════════════════════════════════
        queries.extend([
            'Find fully remote developer jobs from US companies. Return JSON: [{"title":"...","url":"...","location":"remote","contact":"..."}]',
            'Find European remote developer opportunities. Return JSON.',
            'Find async-first companies hiring developers. Return JSON array.',
            'Find timezone-flexible remote tech jobs. Return JSON with contact.',
            'Find remote-first startups hiring globally. Return JSON.',
            'Find digital nomad friendly developer jobs. Return JSON with email.',
            'Find work-from-anywhere tech positions. Return JSON array.',
            'Find companies hiring remote developers in LATAM. Return JSON.',
            'Find APAC timezone remote developer jobs. Return JSON with url.',
            'Find distributed team companies hiring engineers. Return JSON.',
        ])

        # ═══════════════════════════════════════════════════════════════════════════
        # CATEGORY 12: EXPERIENCE LEVELS
        # ═══════════════════════════════════════════════════════════════════════════
        queries.extend([
            'Find junior developer or entry-level coding jobs. Return JSON: [{"title":"...","url":"...","level":"junior","contact":"..."}]',
            'Find mid-level software engineer positions. Return JSON.',
            'Find senior developer or tech lead jobs. Return JSON array.',
            'Find principal or staff engineer opportunities. Return JSON with contact.',
            'Find internship or apprenticeship programs for developers. Return JSON.',
            'Find bootcamp grad friendly job postings. Return JSON with email.',
            'Find career changer welcome developer jobs. Return JSON.',
            'Find mentorship-included junior positions. Return JSON array.',
            'Find self-taught developer friendly opportunities. Return JSON.',
            'Find no experience required coding tasks. Return JSON with contact.',
        ])

        # ═══════════════════════════════════════════════════════════════════════════
        # CATEGORY 13: DISCORD/TELEGRAM/COMMUNITY
        # ═══════════════════════════════════════════════════════════════════════════
        queries.extend([
            'Find Discord servers hiring moderators or developers. Return JSON: [{"title":"...","url":"...","platform":"discord","contact":"..."}]',
            'Find Telegram groups posting developer jobs. Return JSON.',
            'Find Slack communities with job channels. Return JSON array.',
            'Find developer community job boards. Return JSON with contact.',
            'Find tech Discord servers with freelance channels. Return JSON.',
            'Find crypto/Web3 Discord servers hiring developers. Return JSON with invite.',
            'Find gaming community Discord servers needing bot developers. Return JSON.',
            'Find open source project Discord servers looking for contributors. Return JSON.',
            'Find indie hacker Discord or Telegram groups with jobs. Return JSON array.',
            'Find community-based job posting platforms. Return JSON with url.',
        ])

        # ═══════════════════════════════════════════════════════════════════════════
        # CATEGORY 14: NICHE PLATFORMS
        # ═══════════════════════════════════════════════════════════════════════════
        queries.extend([
            'Find Hacker News job posts with contact info. Return JSON: [{"title":"...","url":"...","hn_user":"...","platform":"hackernews"}]',
            'Find Stack Overflow Jobs or Careers listings. Return JSON.',
            'Find dev.to or Hashnode job board postings. Return JSON array.',
            'Find GitHub Jobs or related platform listings. Return JSON.',
            'Find CodePen or Dribbble developer job posts. Return JSON with contact.',
            'Find Behance or creative platform tech jobs. Return JSON.',
            'Find ProductHunt ship job listings. Return JSON with email.',
            'Find Polywork or professional network opportunities. Return JSON.',
            'Find Lunchclub or networking platform jobs. Return JSON array.',
            'Find niche job boards for specific technologies. Return JSON.',
        ])

        # ═══════════════════════════════════════════════════════════════════════════
        # CATEGORY 15: NON-TECH NEEDING TECH HELP
        # ═══════════════════════════════════════════════════════════════════════════
        queries.extend([
            'Find small business owners needing website help. Return JSON: [{"title":"...","url":"...","business_type":"...","email":"..."}]',
            'Find restaurants or local businesses needing online ordering systems. Return JSON.',
            'Find fitness trainers or coaches needing apps built. Return JSON array.',
            'Find content creators needing website or tool development. Return JSON with contact.',
            'Find real estate agents needing property websites. Return JSON.',
            'Find lawyers or attorneys needing client portals. Return JSON with email.',
            'Find doctors or healthcare providers needing booking systems. Return JSON.',
            'Find teachers or educators needing learning platforms. Return JSON.',
            'Find artists or musicians needing portfolio sites. Return JSON array.',
            'Find non-profits needing volunteer management systems. Return JSON with contact.',
        ])

        return queries

    async def _run_single_perplexity_query(self, query: str) -> List[Dict]:
        """Execute a single Perplexity query and parse results."""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    "https://api.perplexity.ai/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.perplexity_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama-3.1-sonar-small-128k-online",
                        "messages": [
                            {"role": "system", "content": "You are a job opportunity finder. Return ONLY valid JSON arrays. No explanations."},
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
                    return self._parse_json_from_text(content)
                else:
                    logger.warning(f"Perplexity API error: {response.status_code}")
                    return []
        except Exception as e:
            logger.error(f"Perplexity query failed: {e}")
            return []

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
