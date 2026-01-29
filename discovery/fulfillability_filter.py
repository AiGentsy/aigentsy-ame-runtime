"""
FULFILLABILITY FILTER

Filters discovery results to only keep opportunities that AiGentsy can
actually fulfill right now using the SKU catalog.

Three stages:
1. Reject non-fulfillable (full-time salary jobs, permanent roles)
2. Match to SKU catalog (keyword scoring against 20 SKUs)
3. Parse urgency signals (immediate / short_term / normal)
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import Counter

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"

# ─── REJECTION PATTERNS ─────────────────────────────────────────────────────
# These indicate full-time/permanent employment, not fulfillable gigs

REJECT_PHRASES = [
    "full-time", "full time", "fulltime",
    "salary", "annual compensation", "base pay",
    "benefits", "401k", "401(k)", "health insurance", "dental", "vision plan",
    "pto", "paid time off", "vacation days",
    "on-site", "onsite", "in-office", "hybrid position",
    "years of experience", "years experience", "yrs experience",
    "permanent", "permanent role", "permanent position",
    "w-2", "w2 employee",
    "equity", "stock options", "rsu",
    "relocation", "relocation assistance",
    "bachelor's degree", "master's degree", "phd required",
    "we are hiring", "we're hiring", "join our team",
    "apply now", "submit your resume", "send your cv",
]

# ─── URGENCY SIGNALS ────────────────────────────────────────────────────────

IMMEDIATE_SIGNALS = [
    "asap", "need today", "urgent", "right now", "need it done",
    "deadline today", "emergency", "immediately", "within hours",
    "need this today", "today only", "rush job", "critical deadline",
    "need done asap", "need help now", "looking for someone now",
]

SHORT_TERM_SIGNALS = [
    "this week", "by friday", "need soon", "quick turnaround",
    "fast", "rush", "tight deadline", "by end of week",
    "next few days", "couple days", "within a week",
    "need by monday", "need by tuesday", "need by wednesday",
    "need by thursday",
]

# ─── SKU KEYWORD MAP ────────────────────────────────────────────────────────
# Maps each SKU ID to keywords that indicate a match

SKU_KEYWORDS = {
    "react-component": [
        "react", "component", "tsx", "jsx", "frontend widget",
        "react component", "react app", "next.js", "nextjs",
    ],
    "api-endpoint": [
        "api", "endpoint", "rest api", "graphql", "api development",
        "backend api", "api integration", "microservice",
    ],
    "bug-fix-triage": [
        "bug", "fix", "broken", "error", "crash", "issue", "debug",
        "not working", "bug fix", "troubleshoot", "patch",
    ],
    "landing-page": [
        "landing page", "one-pager", "squeeze page", "sales page",
        "marketing page", "conversion page", "lead capture",
    ],
    "shopify-theme-fix": [
        "shopify", "theme", "liquid", "store fix", "shopify store",
        "shopify theme", "ecommerce fix", "woocommerce",
    ],
    "zapier-workflow": [
        "zapier", "automation", "workflow", "n8n", "make.com",
        "automate", "integration", "webhook", "no-code automation",
    ],
    "data-pipeline": [
        "data pipeline", "etl", "data flow", "data ingestion",
        "data processing", "batch processing", "streaming data",
    ],
    "email-sequence": [
        "email sequence", "drip", "email campaign", "newsletter setup",
        "email automation", "welcome sequence", "onboarding emails",
        "email flow", "mailchimp", "klaviyo", "convertkit",
    ],
    "logo-design": [
        "logo", "brand mark", "icon design", "logo design",
        "brand identity", "logomark", "wordmark",
    ],
    "ui-mockup": [
        "mockup", "wireframe", "prototype", "figma", "ui design",
        "ux design", "user interface", "app design", "screen design",
    ],
    "social-media-kit": [
        "social media", "social kit", "instagram templates",
        "social graphics", "social media design", "post templates",
    ],
    "blog-post-seo": [
        "blog", "article", "seo", "content writing", "blog post",
        "seo article", "seo content", "blog writing",
    ],
    "email-copy-set": [
        "email copy", "email writing", "sales email", "cold email",
        "email template", "email copywriting",
    ],
    "product-descriptions": [
        "product description", "product copy", "listing description",
        "ecommerce copy", "product listing", "amazon listing",
    ],
    "analytics-dashboard": [
        "analytics", "dashboard", "reporting", "data visualization",
        "analytics dashboard", "kpi dashboard", "metrics dashboard",
        "tableau", "power bi", "looker",
    ],
    "data-cleanup": [
        "data cleanup", "data cleaning", "data normalization",
        "dedup", "data quality", "messy data", "spreadsheet cleanup",
        "csv cleanup", "data migration",
    ],
    "db-migration": [
        "database migration", "db migration", "schema migration",
        "data transfer", "database upgrade", "postgres migration",
        "mysql migration", "mongodb migration",
    ],
    "responsive-page": [
        "responsive", "mobile-friendly", "mobile responsive",
        "responsive design", "css fix", "mobile fix",
        "cross-browser", "responsive conversion",
    ],
    "ad-creative-set": [
        "ad creative", "ad design", "banner ads", "display ads",
        "facebook ads", "google ads", "ad copy", "campaign creative",
        "ad graphics", "paid media",
    ],
    "landing-page-copy": [
        "landing page copy", "sales copy", "conversion copy",
        "headline", "copywriting", "landing copy", "web copy",
        "cta copy", "value proposition",
    ],
}

# ─── GIG SIGNALS ─────────────────────────────────────────────────────────────
# Positive signals that this IS a fulfillable gig/task (not a job posting)

GIG_SIGNALS = [
    "need someone to", "looking for someone to", "need help with",
    "can someone", "who can", "hire someone to",
    "freelancer needed", "contractor needed", "freelance",
    "project", "task", "gig", "one-time", "contract work",
    "build me", "create a", "make a", "design a", "fix my",
    "need a", "looking for a developer to", "looking for a designer to",
    "[hiring]", "[for hire]", "budget", "paying", "paid",
    "bounty", "reward",
]


def _load_sku_catalog() -> List[Dict]:
    """Load the v2 SKU catalog"""
    v2_file = DATA_DIR / "sku_catalog_v2.json"
    if not v2_file.exists():
        return []
    try:
        data = json.loads(v2_file.read_text())
        return data.get("skus", [])
    except Exception:
        return []


def _is_rejected(text: str) -> Optional[str]:
    """Check if opportunity text matches rejection patterns. Returns reason or None."""
    text_lower = text.lower()
    for phrase in REJECT_PHRASES:
        if phrase in text_lower:
            return f"rejected:{phrase}"
    return None


def _has_gig_signal(text: str) -> bool:
    """Check if the opportunity has positive gig/task signals."""
    text_lower = text.lower()
    return any(signal in text_lower for signal in GIG_SIGNALS)


def _match_sku(text: str) -> Tuple[Optional[str], float]:
    """
    Match opportunity text against SKU catalog keywords.
    Returns (best_sku_id, confidence 0-1).
    """
    text_lower = text.lower()
    best_sku = None
    best_score = 0

    for sku_id, keywords in SKU_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in text_lower)
        if hits > 0:
            # Confidence = hits / total keywords, capped at 1.0
            confidence = min(hits / max(len(keywords) * 0.3, 1), 1.0)
            if confidence > best_score:
                best_score = confidence
                best_sku = sku_id

    return best_sku, round(best_score, 2)


def _parse_urgency(text: str) -> str:
    """Detect urgency level from text."""
    text_lower = text.lower()

    for signal in IMMEDIATE_SIGNALS:
        if signal in text_lower:
            return "immediate"

    for signal in SHORT_TERM_SIGNALS:
        if signal in text_lower:
            return "short_term"

    return "normal"


def filter_fulfillable(opportunities: List[Dict]) -> List[Dict]:
    """
    Filter and enrich opportunities for fulfillability.

    Keeps only opportunities that:
    - Are NOT full-time salary jobs
    - AND (match a SKU OR have gig signals)

    Each kept opportunity is enriched with:
    - _fulfillable: True
    - _matched_sku: best matching SKU ID or None
    - _sku_confidence: 0-1 confidence score
    - _urgency: "immediate" | "short_term" | "normal"

    Returns: filtered list (only fulfillable opportunities)
    """
    fulfillable = []
    rejected_count = 0
    urgency_counts = Counter()
    sku_counts = Counter()

    for opp in opportunities:
        title = opp.get("title", "")
        body = opp.get("body", "") or opp.get("text_preview", "") or opp.get("description", "")
        text = f"{title} {body}"

        # Stage 1: Reject non-fulfillable
        reject_reason = _is_rejected(text)
        if reject_reason:
            rejected_count += 1
            continue

        # Stage 2: Match to SKU catalog
        matched_sku, sku_confidence = _match_sku(text)

        # Stage 3: Check gig signals
        has_gig = _has_gig_signal(text)

        # Keep if matches a SKU OR has gig signals
        if not matched_sku and not has_gig:
            rejected_count += 1
            continue

        # Stage 4: Parse urgency
        urgency = _parse_urgency(text)

        # Enrich opportunity
        opp["_fulfillable"] = True
        opp["_matched_sku"] = matched_sku
        opp["_sku_confidence"] = sku_confidence
        opp["_urgency"] = urgency

        # If matched to a SKU, use the SKU's base price as value if opp has no value
        if matched_sku and not opp.get("value") and not opp.get("estimated_value"):
            skus = _load_sku_catalog()
            for sku in skus:
                if sku.get("sku_id") == matched_sku:
                    opp["value"] = sku.get("base_price", 0)
                    opp["_value_source"] = "sku_catalog"
                    break

        fulfillable.append(opp)
        urgency_counts[urgency] += 1
        if matched_sku:
            sku_counts[matched_sku] += 1

    logger.info(
        f"Fulfillability filter: {len(fulfillable)} kept, {rejected_count} rejected "
        f"(of {len(opportunities)} total). "
        f"Urgency: {dict(urgency_counts)}. "
        f"Top SKUs: {sku_counts.most_common(5)}"
    )

    return fulfillable


def get_filter_stats(opportunities: List[Dict]) -> Dict:
    """Get fulfillability stats without modifying the list."""
    total = len(opportunities)
    fulfillable = [o for o in opportunities if o.get("_fulfillable")]
    return {
        "total_before_filter": total,
        "fulfillable": len(fulfillable),
        "rejected": total - len(fulfillable),
        "by_urgency": dict(Counter(o.get("_urgency", "normal") for o in fulfillable)),
        "top_matched_skus": dict(Counter(
            o["_matched_sku"] for o in fulfillable if o.get("_matched_sku")
        ).most_common(10)),
    }
