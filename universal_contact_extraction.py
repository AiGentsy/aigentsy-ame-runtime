"""
UNIVERSAL CONTACT EXTRACTION
=============================
Extracts contact info from ALL 27+ platform discovery sources.
Integrates with ultimate_discovery_engine.py and direct_outreach_engine.py.

CONTACT TYPES BY PLATFORM:
- Reddit → username (for DM)
- Twitter → @handle (for DM)
- GitHub → username (for discussion/email via profile)
- HackerNews → username (for message)
- LinkedIn → profile URL (for InMail)
- Upwork → client_id (for platform message via bid)
- Fiverr → buyer_request_id (for custom offer)
- Discord → username (for DM)
- ProductHunt → maker profile (for message)
- All others → email extraction from post content

PHILOSOPHY:
- Extract contact from EVERY discovered opportunity
- Standardize to common format for outreach engine
- Prioritize: email > platform_dm > platform_comment
"""

import re
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class ExtractedContact:
    """Standardized contact info extracted from any platform"""
    # Identifiers
    platform: str
    platform_user_id: str  # Reddit username, GitHub username, etc.
    
    # Direct contact methods (in priority order)
    email: Optional[str] = None
    twitter_handle: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_username: Optional[str] = None
    reddit_username: Optional[str] = None
    discord_username: Optional[str] = None
    hackernews_username: Optional[str] = None
    producthunt_username: Optional[str] = None
    
    # Platform-specific IDs for in-platform messaging
    platform_dm_id: Optional[str] = None  # For sending DM via platform
    platform_post_id: Optional[str] = None  # For commenting on post
    
    # Metadata
    name: Optional[str] = None
    company: Optional[str] = None
    extraction_confidence: float = 0.5
    preferred_outreach: str = "email"  # email, twitter_dm, reddit_dm, platform_comment, etc.
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'platform': self.platform,
            'platform_user_id': self.platform_user_id,
            'email': self.email,
            'twitter_handle': self.twitter_handle,
            'linkedin_url': self.linkedin_url,
            'github_username': self.github_username,
            'reddit_username': self.reddit_username,
            'discord_username': self.discord_username,
            'hackernews_username': self.hackernews_username,
            'producthunt_username': self.producthunt_username,
            'platform_dm_id': self.platform_dm_id,
            'platform_post_id': self.platform_post_id,
            'name': self.name,
            'company': self.company,
            'extraction_confidence': self.extraction_confidence,
            'preferred_outreach': self.preferred_outreach
        }


class UniversalContactExtractor:
    """
    Extracts contact info from opportunities discovered on ANY platform.
    Works with ultimate_discovery_engine output format.
    """
    
    def __init__(self):
        # Email regex
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        
        # Twitter handle regex
        self.twitter_pattern = re.compile(r'@([A-Za-z0-9_]{1,15})')
        
        # LinkedIn URL regex
        self.linkedin_pattern = re.compile(
            r'linkedin\.com/in/([A-Za-z0-9_-]+)'
        )
        
        # Discord username regex (username#1234 or just username)
        self.discord_pattern = re.compile(
            r'([A-Za-z0-9_]{2,32}(?:#\d{4})?)'
        )
        
        # GitHub username from URL
        self.github_url_pattern = re.compile(
            r'github\.com/([A-Za-z0-9_-]+)'
        )
    
    def extract_from_opportunity(self, opportunity: Dict[str, Any]) -> ExtractedContact:
        """
        Extract contact info from a discovered opportunity.
        Works with output format from ultimate_discovery_engine.
        """
        source = opportunity.get('source', '').lower()
        
        # Route to platform-specific extractor
        extractor_map = {
            'reddit': self._extract_reddit,
            'github': self._extract_github,
            'github_bounty': self._extract_github,
            'hackernews': self._extract_hackernews,
            'twitter': self._extract_twitter,
            'linkedin': self._extract_linkedin,
            'upwork': self._extract_upwork,
            'fiverr': self._extract_fiverr,
            'freelancer': self._extract_freelancer,
            'producthunt': self._extract_producthunt,
            'dribbble': self._extract_dribbble,
            'behance': self._extract_behance,
            'discord': self._extract_discord,
            'indiehackers': self._extract_indiehackers,
            '99designs': self._extract_99designs,
            'remoteok': self._extract_remoteok,
            'weworkremotely': self._extract_weworkremotely,
        }
        
        extractor = extractor_map.get(source, self._extract_generic)
        contact = extractor(opportunity)
        
        # Also try to extract from text content
        self._extract_from_text(opportunity, contact)
        
        return contact
    
    def _extract_reddit(self, opp: Dict) -> ExtractedContact:
        """Extract from Reddit opportunity"""
        # Reddit opportunities have author in the data
        author = opp.get('author') or opp.get('reddit_username') or ''
        post_id = opp.get('platform_id') or opp.get('id', '').replace('reddit_', '')
        
        # Try to get author from URL if not in data
        if not author:
            url = opp.get('url', '')
            # Reddit URLs: /r/subreddit/comments/id/title/
            # Author is in post data, not URL
            pass
        
        contact = ExtractedContact(
            platform='reddit',
            platform_user_id=author,
            reddit_username=author if author else None,
            platform_dm_id=author,  # Can DM via reddit username
            platform_post_id=post_id,
            extraction_confidence=0.8 if author else 0.3,
            preferred_outreach='reddit_dm' if author else 'platform_comment'
        )
        
        return contact
    
    def _extract_github(self, opp: Dict) -> ExtractedContact:
        """Extract from GitHub opportunity"""
        # GitHub issues/PRs have username in data
        username = opp.get('author') or opp.get('github_username') or opp.get('user', {}).get('login', '')
        issue_number = opp.get('platform_id') or opp.get('number')
        repo = opp.get('repo') or opp.get('repository', '')
        
        # Try to extract from URL
        if not username:
            url = opp.get('url', '')
            # GitHub URLs: github.com/owner/repo/issues/123
            match = re.search(r'github\.com/([^/]+)/', url)
            if match:
                # This is repo owner, not issue author
                pass
        
        contact = ExtractedContact(
            platform='github',
            platform_user_id=username,
            github_username=username if username else None,
            platform_dm_id=None,  # GitHub doesn't have DMs
            platform_post_id=f"{repo}#{issue_number}" if repo and issue_number else None,
            extraction_confidence=0.85 if username else 0.3,
            preferred_outreach='github_comment' if username else 'platform_comment'
        )
        
        return contact
    
    def _extract_hackernews(self, opp: Dict) -> ExtractedContact:
        """Extract from HackerNews opportunity"""
        username = opp.get('author') or opp.get('by') or opp.get('hn_username', '')
        item_id = opp.get('platform_id') or opp.get('id', '').replace('hn_', '')
        
        contact = ExtractedContact(
            platform='hackernews',
            platform_user_id=username,
            hackernews_username=username if username else None,
            platform_dm_id=None,  # HN doesn't have DMs, but has email in profile sometimes
            platform_post_id=item_id,
            extraction_confidence=0.7 if username else 0.3,
            preferred_outreach='hn_reply' if username else 'platform_comment'
        )
        
        return contact
    
    def _extract_twitter(self, opp: Dict) -> ExtractedContact:
        """Extract from Twitter opportunity"""
        handle = opp.get('author') or opp.get('twitter_handle') or opp.get('screen_name', '')
        tweet_id = opp.get('platform_id') or opp.get('tweet_id', '')
        
        # Clean handle
        if handle and handle.startswith('@'):
            handle = handle[1:]
        
        contact = ExtractedContact(
            platform='twitter',
            platform_user_id=handle,
            twitter_handle=handle if handle else None,
            platform_dm_id=handle,  # Can DM via handle
            platform_post_id=tweet_id,
            extraction_confidence=0.9 if handle else 0.3,
            preferred_outreach='twitter_dm' if handle else 'twitter_reply'
        )
        
        return contact
    
    def _extract_linkedin(self, opp: Dict) -> ExtractedContact:
        """Extract from LinkedIn opportunity"""
        profile_url = opp.get('linkedin_url') or opp.get('author_url', '')
        author_name = opp.get('author') or opp.get('name', '')
        post_id = opp.get('platform_id') or opp.get('post_id', '')
        
        # Extract username from URL
        username = ''
        if profile_url:
            match = self.linkedin_pattern.search(profile_url)
            if match:
                username = match.group(1)
        
        contact = ExtractedContact(
            platform='linkedin',
            platform_user_id=username or author_name,
            linkedin_url=profile_url if profile_url else None,
            name=author_name if author_name else None,
            platform_dm_id=profile_url,  # InMail via profile
            platform_post_id=post_id,
            extraction_confidence=0.85 if profile_url else 0.4,
            preferred_outreach='linkedin_message' if profile_url else 'linkedin_comment'
        )
        
        return contact
    
    def _extract_upwork(self, opp: Dict) -> ExtractedContact:
        """Extract from Upwork opportunity"""
        # Upwork jobs come from RSS, limited contact info
        job_id = opp.get('platform_id') or opp.get('id', '').replace('upwork_', '')
        client_name = opp.get('client') or opp.get('author', '')
        
        contact = ExtractedContact(
            platform='upwork',
            platform_user_id=job_id,
            name=client_name if client_name else None,
            platform_dm_id=None,  # Can't DM on Upwork directly
            platform_post_id=job_id,
            extraction_confidence=0.5,
            preferred_outreach='upwork_proposal'  # Submit proposal via platform
        )
        
        return contact
    
    def _extract_fiverr(self, opp: Dict) -> ExtractedContact:
        """Extract from Fiverr opportunity"""
        request_id = opp.get('platform_id') or opp.get('id', '').replace('fiverr_', '')
        
        contact = ExtractedContact(
            platform='fiverr',
            platform_user_id=request_id,
            platform_dm_id=None,
            platform_post_id=request_id,
            extraction_confidence=0.5,
            preferred_outreach='fiverr_offer'  # Custom offer via platform
        )
        
        return contact
    
    def _extract_freelancer(self, opp: Dict) -> ExtractedContact:
        """Extract from Freelancer.com opportunity"""
        project_id = opp.get('platform_id') or opp.get('id', '').replace('freelancer_', '')
        employer = opp.get('employer') or opp.get('author', '')
        
        contact = ExtractedContact(
            platform='freelancer',
            platform_user_id=project_id,
            name=employer if employer else None,
            platform_dm_id=None,
            platform_post_id=project_id,
            extraction_confidence=0.5,
            preferred_outreach='freelancer_bid'
        )
        
        return contact
    
    def _extract_producthunt(self, opp: Dict) -> ExtractedContact:
        """Extract from ProductHunt opportunity"""
        maker = opp.get('maker') or opp.get('author') or opp.get('user', {}).get('username', '')
        product_id = opp.get('platform_id') or opp.get('id', '').replace('ph_', '')
        twitter = opp.get('twitter_handle', '')
        
        contact = ExtractedContact(
            platform='producthunt',
            platform_user_id=maker,
            producthunt_username=maker if maker else None,
            twitter_handle=twitter if twitter else None,
            platform_dm_id=maker,
            platform_post_id=product_id,
            extraction_confidence=0.75 if maker else 0.4,
            preferred_outreach='twitter_dm' if twitter else 'producthunt_comment'
        )
        
        return contact
    
    def _extract_dribbble(self, opp: Dict) -> ExtractedContact:
        """Extract from Dribbble opportunity"""
        username = opp.get('author') or opp.get('designer', '')
        shot_id = opp.get('platform_id') or opp.get('id', '').replace('dribbble_', '')
        
        contact = ExtractedContact(
            platform='dribbble',
            platform_user_id=username,
            platform_dm_id=username,  # Dribbble has messaging
            platform_post_id=shot_id,
            extraction_confidence=0.7 if username else 0.3,
            preferred_outreach='dribbble_message' if username else 'dribbble_comment'
        )
        
        return contact
    
    def _extract_behance(self, opp: Dict) -> ExtractedContact:
        """Extract from Behance opportunity"""
        username = opp.get('author') or opp.get('creator', '')
        project_id = opp.get('platform_id') or opp.get('id', '').replace('behance_', '')
        
        contact = ExtractedContact(
            platform='behance',
            platform_user_id=username,
            platform_dm_id=username,
            platform_post_id=project_id,
            extraction_confidence=0.7 if username else 0.3,
            preferred_outreach='behance_message' if username else 'behance_comment'
        )
        
        return contact
    
    def _extract_discord(self, opp: Dict) -> ExtractedContact:
        """Extract from Discord opportunity"""
        username = opp.get('author') or opp.get('discord_username', '')
        message_id = opp.get('platform_id') or opp.get('message_id', '')
        server_id = opp.get('server_id') or opp.get('guild_id', '')
        
        contact = ExtractedContact(
            platform='discord',
            platform_user_id=username,
            discord_username=username if username else None,
            platform_dm_id=username,  # Can DM via username
            platform_post_id=f"{server_id}/{message_id}" if server_id else message_id,
            extraction_confidence=0.8 if username else 0.3,
            preferred_outreach='discord_dm' if username else 'discord_reply'
        )
        
        return contact
    
    def _extract_indiehackers(self, opp: Dict) -> ExtractedContact:
        """Extract from IndieHackers opportunity"""
        username = opp.get('author') or opp.get('ih_username', '')
        post_id = opp.get('platform_id') or opp.get('id', '').replace('ih_', '')
        twitter = opp.get('twitter_handle', '')
        
        contact = ExtractedContact(
            platform='indiehackers',
            platform_user_id=username,
            twitter_handle=twitter if twitter else None,
            platform_dm_id=username,  # IH has messaging
            platform_post_id=post_id,
            extraction_confidence=0.7 if username else 0.4,
            preferred_outreach='twitter_dm' if twitter else 'ih_message'
        )
        
        return contact
    
    def _extract_99designs(self, opp: Dict) -> ExtractedContact:
        """Extract from 99designs opportunity"""
        contest_id = opp.get('platform_id') or opp.get('id', '').replace('99d_', '')
        
        contact = ExtractedContact(
            platform='99designs',
            platform_user_id=contest_id,
            platform_dm_id=None,
            platform_post_id=contest_id,
            extraction_confidence=0.5,
            preferred_outreach='99designs_entry'  # Submit design entry
        )
        
        return contact
    
    def _extract_remoteok(self, opp: Dict) -> ExtractedContact:
        """Extract from RemoteOK opportunity"""
        job_id = opp.get('platform_id') or opp.get('id', '').replace('remoteok_', '')
        company = opp.get('company', '')
        
        contact = ExtractedContact(
            platform='remoteok',
            platform_user_id=job_id,
            company=company if company else None,
            platform_dm_id=None,
            platform_post_id=job_id,
            extraction_confidence=0.5,
            preferred_outreach='remoteok_apply'
        )
        
        return contact
    
    def _extract_weworkremotely(self, opp: Dict) -> ExtractedContact:
        """Extract from WeWorkRemotely opportunity"""
        job_id = opp.get('platform_id') or opp.get('id', '').replace('wwr_', '')
        company = opp.get('company', '')
        
        contact = ExtractedContact(
            platform='weworkremotely',
            platform_user_id=job_id,
            company=company if company else None,
            platform_dm_id=None,
            platform_post_id=job_id,
            extraction_confidence=0.5,
            preferred_outreach='wwr_apply'
        )
        
        return contact
    
    def _extract_generic(self, opp: Dict) -> ExtractedContact:
        """Generic extraction for unknown platforms"""
        source = opp.get('source', 'unknown')
        platform_id = opp.get('platform_id') or opp.get('id', '')
        author = opp.get('author', '')
        
        contact = ExtractedContact(
            platform=source,
            platform_user_id=author or platform_id,
            platform_post_id=platform_id,
            extraction_confidence=0.3,
            preferred_outreach='platform_comment'
        )
        
        return contact
    
    def _extract_from_text(self, opp: Dict, contact: ExtractedContact) -> None:
        """
        Extract additional contact info from text content.
        Modifies contact in place.
        """
        # Combine all text fields
        text = ' '.join([
            str(opp.get('title', '')),
            str(opp.get('description', '')),
            str(opp.get('body', '')),
            str(opp.get('selftext', '')),
            str(opp.get('content', ''))
        ])
        
        # Extract email
        if not contact.email:
            emails = self.email_pattern.findall(text)
            if emails:
                # Filter out common fake/example emails
                real_emails = [e for e in emails if not any(
                    fake in e.lower() for fake in ['example.com', 'test.com', 'email.com', 'domain.com']
                )]
                if real_emails:
                    contact.email = real_emails[0]
                    contact.extraction_confidence = max(contact.extraction_confidence, 0.9)
                    contact.preferred_outreach = 'email'
        
        # Extract Twitter handle
        if not contact.twitter_handle:
            handles = self.twitter_pattern.findall(text)
            if handles:
                # Filter out common non-user handles
                real_handles = [h for h in handles if h.lower() not in ['here', 'me', 'us', 'example']]
                if real_handles:
                    contact.twitter_handle = real_handles[0]
                    if not contact.email:
                        contact.preferred_outreach = 'twitter_dm'
        
        # Extract LinkedIn URL
        if not contact.linkedin_url:
            matches = self.linkedin_pattern.findall(text)
            if matches:
                contact.linkedin_url = f"https://linkedin.com/in/{matches[0]}"
                if not contact.email and not contact.twitter_handle:
                    contact.preferred_outreach = 'linkedin_message'
        
        # Extract GitHub username from text
        if not contact.github_username:
            matches = self.github_url_pattern.findall(text)
            if matches:
                contact.github_username = matches[0]
        
        # Try to extract name from common patterns
        if not contact.name:
            # Patterns like "I'm John" or "My name is John"
            name_patterns = [
                r"(?:I'm|I am|my name is|call me)\s+([A-Z][a-z]+)",
                r"(?:^|\n)([A-Z][a-z]+)\s+here",
                r"(?:regards|best|thanks),?\s*\n?\s*([A-Z][a-z]+)",
            ]
            for pattern in name_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    contact.name = match.group(1)
                    break


# ============================================================
# INTEGRATION FUNCTIONS
# ============================================================

def enrich_opportunity_with_contact(opportunity: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add contact info to a discovered opportunity.
    Returns opportunity dict with 'contact' field added.
    """
    extractor = UniversalContactExtractor()
    contact = extractor.extract_from_opportunity(opportunity)
    
    opportunity['contact'] = contact.to_dict()
    opportunity['has_contact'] = bool(
        contact.email or 
        contact.twitter_handle or 
        contact.reddit_username or
        contact.github_username or
        contact.linkedin_url or
        contact.platform_dm_id
    )
    
    return opportunity


def enrich_all_opportunities(opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Add contact info to all discovered opportunities.
    """
    extractor = UniversalContactExtractor()
    
    enriched = []
    for opp in opportunities:
        contact = extractor.extract_from_opportunity(opp)
        opp['contact'] = contact.to_dict()
        opp['has_contact'] = bool(
            contact.email or 
            contact.twitter_handle or 
            contact.reddit_username or
            contact.github_username or
            contact.linkedin_url or
            contact.platform_dm_id
        )
        enriched.append(opp)
    
    return enriched


async def discover_with_contacts(username: str, user_profile: Dict[str, Any], platforms: List[str] = None) -> Dict[str, Any]:
    """
    Run discovery and automatically enrich with contacts.
    Drop-in replacement for discover_all_opportunities that adds contacts.
    """
    # Import here to avoid circular dependency
    from ultimate_discovery_engine import discover_all_opportunities
    
    # Run standard discovery
    results = await discover_all_opportunities(
        username=username,
        user_profile=user_profile,
        platforms=platforms
    )
    
    # Enrich with contacts
    opportunities = results.get('opportunities', [])
    enriched_opps = enrich_all_opportunities(opportunities)
    
    # Update results
    results['opportunities'] = enriched_opps
    results['with_contact'] = len([o for o in enriched_opps if o.get('has_contact')])
    results['contact_rate'] = results['with_contact'] / len(enriched_opps) if enriched_opps else 0
    
    return results


# ============================================================
# SINGLETON FOR EASY ACCESS
# ============================================================

_extractor_instance = None

def get_contact_extractor() -> UniversalContactExtractor:
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = UniversalContactExtractor()
    return _extractor_instance
