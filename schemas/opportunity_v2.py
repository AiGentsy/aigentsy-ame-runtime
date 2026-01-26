"""
OPPORTUNITY V2 SCHEMA: Universal Opportunity Data Model

Production-grade schema with:
- 20+ fields for full opportunity lifecycle
- Validation and normalization
- Backward compatibility with existing structures
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
from enum import Enum
import hashlib
import re


class OpportunityType(Enum):
    """Opportunity classification"""
    JOB = "job"
    GIG = "gig"
    CONTRACT = "contract"
    PROJECT = "project"
    LEAD = "lead"
    RFP = "rfp"
    GRANT = "grant"
    BOUNTY = "bounty"
    UNKNOWN = "unknown"


class OpportunityStatus(Enum):
    """Lifecycle status"""
    DISCOVERED = "discovered"
    ENRICHED = "enriched"
    ROUTED = "routed"
    EXECUTING = "executing"
    WON = "won"
    LOST = "lost"
    EXPIRED = "expired"
    BLOCKED = "blocked"


@dataclass
class ContactInfo:
    """Contact information for opportunity"""
    email: Optional[str] = None
    phone: Optional[str] = None
    name: Optional[str] = None
    company: Optional[str] = None
    linkedin: Optional[str] = None
    twitter: Optional[str] = None


@dataclass
class PricingInfo:
    """Pricing/budget information"""
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    currency: str = "USD"
    pricing_type: str = "fixed"  # fixed, hourly, monthly, equity
    estimated_value: Optional[float] = None


@dataclass
class EnrichmentData:
    """Enrichment pipeline results"""
    contact_score: float = 0.0  # 0-1, how contactable
    payment_proximity: float = 0.0  # 0-1, how close to payment
    intent_score: float = 0.0  # 0-1, buyer intent
    urgency_score: float = 0.0  # 0-1, time sensitivity
    inventory_fit: float = 0.0  # 0-1, match to our offerings
    poster_reputation: float = 0.5  # 0-1, poster credibility
    risk_score: float = 0.0  # 0-1, scam/abuse risk
    language: str = "en"
    language_confidence: float = 1.0
    title_en: Optional[str] = None
    body_en: Optional[str] = None
    skills_extracted: List[str] = field(default_factory=list)
    budget_extracted: Optional[float] = None


@dataclass
class OpportunityV2:
    """
    Universal opportunity schema for the Access Panel.

    Designed for:
    - Cross-platform normalization
    - Full enrichment pipeline
    - Routing decisions
    - Execution tracking
    """

    # Core identifiers
    id: str = ""
    platform: str = ""
    url: str = ""
    canonical_url: str = ""

    # Content
    title: str = ""
    body: str = ""
    raw_html: Optional[str] = None

    # Classification
    type: OpportunityType = OpportunityType.UNKNOWN
    status: OpportunityStatus = OpportunityStatus.DISCOVERED
    category: str = ""
    tags: List[str] = field(default_factory=list)

    # Contact
    contact: ContactInfo = field(default_factory=ContactInfo)

    # Pricing
    pricing: PricingInfo = field(default_factory=PricingInfo)

    # Enrichment
    enrichment: EnrichmentData = field(default_factory=EnrichmentData)

    # Timestamps
    discovered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    posted_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    last_enriched_at: Optional[datetime] = None

    # Routing
    routed_to: Optional[str] = None
    routing_score: float = 0.0
    fast_path_eligible: bool = False

    # Execution
    execution_id: Optional[str] = None
    execution_attempts: int = 0

    # Metadata
    source_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Compliance
    compliance_flags: List[str] = field(default_factory=list)
    blocked_reason: Optional[str] = None

    def __post_init__(self):
        """Generate ID if not provided"""
        if not self.id and self.platform and self.url:
            self.id = self.generate_id()

    def generate_id(self) -> str:
        """Generate stable ID from platform + canonical URL"""
        key = f"{self.platform}:{self.canonical_url or self.url}".lower()
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        # Convert enums to strings
        data['type'] = self.type.value
        data['status'] = self.status.value
        # Convert datetimes to ISO strings
        for key in ['discovered_at', 'posted_at', 'expires_at', 'last_enriched_at']:
            if data.get(key):
                data[key] = data[key].isoformat() if isinstance(data[key], datetime) else data[key]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OpportunityV2':
        """Create from dictionary (handles legacy formats)"""
        # Handle type enum
        opp_type = data.get('type', 'unknown')
        if isinstance(opp_type, str):
            try:
                opp_type = OpportunityType(opp_type)
            except ValueError:
                opp_type = OpportunityType.UNKNOWN

        # Handle status enum
        status = data.get('status', 'discovered')
        if isinstance(status, str):
            try:
                status = OpportunityStatus(status)
            except ValueError:
                status = OpportunityStatus.DISCOVERED

        # Handle nested objects
        contact = data.get('contact', {})
        if isinstance(contact, dict):
            contact = ContactInfo(**{k: v for k, v in contact.items() if k in ContactInfo.__dataclass_fields__})

        pricing = data.get('pricing', {})
        if isinstance(pricing, dict):
            pricing = PricingInfo(**{k: v for k, v in pricing.items() if k in PricingInfo.__dataclass_fields__})

        enrichment = data.get('enrichment', {})
        if isinstance(enrichment, dict):
            enrichment = EnrichmentData(**{k: v for k, v in enrichment.items() if k in EnrichmentData.__dataclass_fields__})

        # Handle datetimes
        for key in ['discovered_at', 'posted_at', 'expires_at', 'last_enriched_at']:
            if key in data and isinstance(data[key], str):
                try:
                    data[key] = datetime.fromisoformat(data[key].replace('Z', '+00:00'))
                except:
                    data[key] = None

        # Build opportunity
        return cls(
            id=data.get('id', ''),
            platform=data.get('platform', ''),
            url=data.get('url', ''),
            canonical_url=data.get('canonical_url', ''),
            title=data.get('title', ''),
            body=data.get('body', ''),
            raw_html=data.get('raw_html'),
            type=opp_type,
            status=status,
            category=data.get('category', ''),
            tags=data.get('tags', []),
            contact=contact,
            pricing=pricing,
            enrichment=enrichment,
            discovered_at=data.get('discovered_at') or datetime.now(timezone.utc),
            posted_at=data.get('posted_at'),
            expires_at=data.get('expires_at'),
            last_enriched_at=data.get('last_enriched_at'),
            routed_to=data.get('routed_to'),
            routing_score=data.get('routing_score', 0.0),
            fast_path_eligible=data.get('fast_path_eligible', False),
            execution_id=data.get('execution_id'),
            execution_attempts=data.get('execution_attempts', 0),
            source_data=data.get('source_data', {}),
            metadata=data.get('metadata', {}),
            compliance_flags=data.get('compliance_flags', []),
            blocked_reason=data.get('blocked_reason'),
        )

    @classmethod
    def from_legacy(cls, legacy: Dict[str, Any]) -> 'OpportunityV2':
        """Convert legacy opportunity format to V2"""
        # Map legacy fields
        enrichment = EnrichmentData(
            contact_score=legacy.get('contactability', 0.0),
            payment_proximity=legacy.get('payment_proximity', 0.0),
            intent_score=legacy.get('intent_score', 0.0),
            urgency_score=legacy.get('urgency_score', 0.0),
            inventory_fit=legacy.get('inventory_fit', 0.0),
            poster_reputation=legacy.get('win_probability', 0.5),
            risk_score=legacy.get('risk_score', 0.0),
            language=legacy.get('language', 'en'),
            title_en=legacy.get('title_en'),
            body_en=legacy.get('body_en'),
            skills_extracted=legacy.get('skills', []),
            budget_extracted=legacy.get('value'),
        )

        pricing = PricingInfo(
            estimated_value=legacy.get('value'),
            currency=legacy.get('currency', 'USD'),
        )

        # Determine type from platform or content
        opp_type = cls._infer_type(legacy)

        return cls(
            id=legacy.get('id', ''),
            platform=legacy.get('platform', ''),
            url=legacy.get('url', ''),
            canonical_url=legacy.get('canonical_url', legacy.get('url', '')),
            title=legacy.get('title', ''),
            body=legacy.get('body', legacy.get('description', '')),
            type=opp_type,
            enrichment=enrichment,
            pricing=pricing,
            discovered_at=datetime.now(timezone.utc),
            source_data=legacy.get('source_data', {}),
            metadata=legacy,
        )

    @staticmethod
    def _infer_type(data: Dict[str, Any]) -> OpportunityType:
        """Infer opportunity type from content"""
        platform = data.get('platform', '').lower()
        title = data.get('title', '').lower()
        body = data.get('body', '').lower()
        text = f"{title} {body}"

        # Platform-based inference
        if 'upwork' in platform or 'freelancer' in platform or 'toptal' in platform:
            return OpportunityType.GIG
        if 'github' in platform and 'bounty' in text:
            return OpportunityType.BOUNTY
        if 'regulations.gov' in platform or 'grants.gov' in platform:
            return OpportunityType.GRANT
        if 'rfp' in text or 'request for proposal' in text:
            return OpportunityType.RFP

        # Content-based inference
        if any(word in text for word in ['hiring', 'job', 'position', 'role', 'salary']):
            return OpportunityType.JOB
        if any(word in text for word in ['freelance', 'gig', 'project-based']):
            return OpportunityType.GIG
        if any(word in text for word in ['contract', 'agreement', 'term']):
            return OpportunityType.CONTRACT
        if any(word in text for word in ['project', 'build', 'develop']):
            return OpportunityType.PROJECT

        return OpportunityType.UNKNOWN

    def compute_routing_score(self) -> float:
        """Compute weighted routing score based on enrichment"""
        weights = {
            'payment_proximity': 0.22,
            'contactability': 0.16,
            'inventory_fit': 0.10,
            'poster_reputation': 0.12,
            'intent_score': 0.15,
            'urgency_score': 0.10,
            'risk_penalty': -0.15,
        }

        score = (
            weights['payment_proximity'] * self.enrichment.payment_proximity +
            weights['contactability'] * self.enrichment.contact_score +
            weights['inventory_fit'] * self.enrichment.inventory_fit +
            weights['poster_reputation'] * self.enrichment.poster_reputation +
            weights['intent_score'] * self.enrichment.intent_score +
            weights['urgency_score'] * self.enrichment.urgency_score +
            weights['risk_penalty'] * self.enrichment.risk_score
        )

        self.routing_score = max(0.0, min(1.0, score))
        return self.routing_score

    def is_fast_path_eligible(self) -> bool:
        """Check if opportunity qualifies for fast-path execution"""
        self.fast_path_eligible = (
            self.enrichment.payment_proximity >= 0.7 and
            self.enrichment.contact_score >= 0.6 and
            self.enrichment.risk_score <= 0.3 and
            self.routing_score >= 0.5
        )
        return self.fast_path_eligible


def normalize_opportunity(raw: Dict[str, Any]) -> OpportunityV2:
    """
    Normalize any opportunity format to OpportunityV2.
    Handles legacy formats from existing discovery systems.
    """
    # Check if already V2 format
    if 'enrichment' in raw and isinstance(raw.get('enrichment'), dict):
        return OpportunityV2.from_dict(raw)

    # Legacy format - convert
    return OpportunityV2.from_legacy(raw)
