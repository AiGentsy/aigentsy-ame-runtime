# franchise_engine.py
"""
AiGentsy Template Franchise Rights Engine - Feature #12

Standalone template licensing and franchise system.
Creators license outcome templates, franchisees execute them.

Features:
- Template licensing (one-time or recurring)
- Territory/niche exclusivity
- Revenue sharing between creator and franchisee
- Performance tracking and leaderboards
- Template marketplace

Example:
- Creator builds "LinkedIn Lead Gen" template
- Licenses to franchisees for $500/month
- Franchisee uses template to deliver outcomes
- Creator gets 10% of franchisee revenue
- Franchisee gets proven system + ongoing support
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List

# License types
LICENSE_TYPES = {
    "basic": {
        "name": "Basic License",
        "type": "one_time",
        "cost": 99.00,
        "revenue_share_pct": 5.0,  # Creator gets 5% of franchisee revenue
        "territory_exclusive": False,
        "support_included": False,
        "updates_included": True,
        "max_uses_per_month": 10,
        "description": "One-time fee, 5% revenue share, non-exclusive",
        "icon": "📄"
    },
    "professional": {
        "name": "Professional License",
        "type": "monthly",
        "cost": 299.00,
        "revenue_share_pct": 10.0,  # Creator gets 10%
        "territory_exclusive": False,
        "support_included": True,
        "updates_included": True,
        "max_uses_per_month": 50,
        "description": "$299/mo, 10% revenue share, priority support",
        "icon": "⭐"
    },
    "exclusive": {
        "name": "Exclusive Territory",
        "type": "monthly",
        "cost": 999.00,
        "revenue_share_pct": 15.0,  # Creator gets 15%
        "territory_exclusive": True,
        "support_included": True,
        "updates_included": True,
        "max_uses_per_month": None,  # Unlimited
        "description": "$999/mo, 15% revenue share, exclusive territory",
        "icon": "👑"
    },
    "master_franchise": {
        "name": "Master Franchise",
        "type": "one_time",
        "cost": 10000.00,
        "revenue_share_pct": 20.0,  # Creator gets 20%
        "territory_exclusive": True,
        "support_included": True,
        "updates_included": True,
        "max_uses_per_month": None,  # Unlimited
        "can_sublicense": True,  # Can license to others
        "sublicense_share_pct": 50.0,  # Master gets 50% of sublicense fees
        "description": "$10k one-time, 20% revenue share, can sublicense",
        "icon": "💎"
    }
}

# Template categories
TEMPLATE_CATEGORIES = {
    "marketing": {
        "name": "Marketing & Growth",
        "icon": "📈",
        "examples": ["LinkedIn Lead Gen", "Email Campaigns", "Content Marketing"]
    },
    "sales": {
        "name": "Sales & Outreach",
        "icon": "💼",
        "examples": ["Cold Email Sequences", "Sales Funnels", "Pitch Decks"]
    },
    "operations": {
        "name": "Operations & Process",
        "icon": "⚙️",
        "examples": ["SOP Creation", "Workflow Automation", "Data Analysis"]
    },
    "creative": {
        "name": "Creative & Design",
        "icon": "🎨",
        "examples": ["Social Media Graphics", "Video Scripts", "Brand Guidelines"]
    },
    "technical": {
        "name": "Technical & Development",
        "icon": "💻",
        "examples": ["API Integration", "Web Scraping", "Automation Scripts"]
    }
}

# In-memory storage (use JSONBin in production)
TEMPLATES_DB = {}
LICENSES_DB = {}
FRANCHISE_REVENUE_DB = {}
TERRITORY_CLAIMS_DB = {}


def create_template(
    creator_username: str,
    template_name: str,
    category: str,
    description: str,
    base_price: float,
    available_licenses: List[str] = ["basic", "professional"],
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a franchisable template.
    
    Args:
        creator_username: Template creator
        template_name: Template name
        category: Template category
        description: Template description
        base_price: Base price for outcomes using template
        available_licenses: License types offered
        metadata: Template files, instructions, etc.
    
    Returns:
        Created template
    """
    if category not in TEMPLATE_CATEGORIES:
        raise ValueError(f"Invalid category: {category}")
    
    for license_type in available_licenses:
        if license_type not in LICENSE_TYPES:
            raise ValueError(f"Invalid license type: {license_type}")
    
    template_id = f"template_{creator_username}_{int(datetime.now(timezone.utc).timestamp())}"
    
    template = {
        "template_id": template_id,
        "creator_username": creator_username,
        "template_name": template_name,
        "category": category,
        "category_info": TEMPLATE_CATEGORIES[category],
        "description": description,
        "base_price": base_price,
        "available_licenses": available_licenses,
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "total_licenses_sold": 0,
        "total_revenue_generated": 0.0,
        "total_franchise_revenue": 0.0,
        "avg_rating": 0.0,
        "total_outcomes_delivered": 0,
        "metadata": metadata or {},
        "version": "1.0"
    }
    
    TEMPLATES_DB[template_id] = template
    
    return {
        "success": True,
        "template": template,
        "message": f"Template '{template_name}' created successfully!"
    }


def purchase_license(
    franchisee_username: str,
    template_id: str,
    license_type: str,
    territory: Optional[str] = None,
    niche: Optional[str] = None
) -> Dict[str, Any]:
    """
    Purchase a template license.
    
    Args:
        franchisee_username: Franchisee purchasing
        template_id: Template to license
        license_type: Type of license
        territory: Geographic territory (for exclusive)
        niche: Industry niche (for exclusive)
    
    Returns:
        License agreement
    """
    if template_id not in TEMPLATES_DB:
        raise ValueError(f"Template not found: {template_id}")
    
    if license_type not in LICENSE_TYPES:
        raise ValueError(f"Invalid license type: {license_type}")
    
    template = TEMPLATES_DB[template_id]
    license_config = LICENSE_TYPES[license_type]
    
    # Check if license type is available for this template
    if license_type not in template["available_licenses"]:
        raise ValueError(f"License type '{license_type}' not available for this template")
    
    # Check territory exclusivity
    if license_config.get("territory_exclusive") and territory:
        if _is_territory_claimed(template_id, territory):
            raise ValueError(f"Territory '{territory}' already claimed")
    
    license_id = f"license_{template_id}_{franchisee_username}_{int(datetime.now(timezone.utc).timestamp())}"
    
    # Calculate billing
    next_billing_date = None
    if license_config["type"] == "monthly":
        next_billing_date = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    
    license = {
        "license_id": license_id,
        "template_id": template_id,
        "template_name": template["template_name"],
        "creator_username": template["creator_username"],
        "franchisee_username": franchisee_username,
        "license_type": license_type,
        "license_config": license_config,
        "territory": territory,
        "niche": niche,
        "status": "active",
        "purchased_at": datetime.now(timezone.utc).isoformat(),
        "license_cost": license_config["cost"],
        "revenue_share_pct": license_config["revenue_share_pct"],
        "billing_type": license_config["type"],
        "next_billing_date": next_billing_date,
        "total_outcomes_delivered": 0,
        "total_revenue_generated": 0.0,
        "total_creator_share_paid": 0.0,
        "uses_this_month": 0,
        "last_used_at": None
    }
    
    LICENSES_DB[license_id] = license
    
    # Claim territory if exclusive
    if license_config.get("territory_exclusive") and territory:
        _claim_territory(template_id, territory, license_id, franchisee_username)
    
    # Update template stats
    template["total_licenses_sold"] += 1
    
    return {
        "success": True,
        "license": license,
        "payment_due": {
            "amount": license_config["cost"],
            "type": license_config["type"],
            "next_billing": next_billing_date
        },
        "terms": {
            "revenue_share": f"{license_config['revenue_share_pct']}% to creator",
            "exclusivity": "Exclusive territory" if license_config.get("territory_exclusive") else "Non-exclusive",
            "support": "Included" if license_config.get("support_included") else "Not included",
            "max_uses": license_config.get("max_uses_per_month", "Unlimited")
        },
        "message": f"License purchased! Start using '{template['template_name']}'"
    }


def _is_territory_claimed(template_id: str, territory: str) -> bool:
    """Check if territory is already claimed for template."""
    claim_key = f"{template_id}_{territory}"
    return claim_key in TERRITORY_CLAIMS_DB


def _claim_territory(
    template_id: str,
    territory: str,
    license_id: str,
    franchisee_username: str
) -> None:
    """Claim exclusive territory."""
    claim_key = f"{template_id}_{territory}"
    
    TERRITORY_CLAIMS_DB[claim_key] = {
        "template_id": template_id,
        "territory": territory,
        "license_id": license_id,
        "franchisee_username": franchisee_username,
        "claimed_at": datetime.now(timezone.utc).isoformat()
    }


def record_franchise_outcome(
    license_id: str,
    outcome_id: str,
    revenue_amount: float,
    buyer_username: str
) -> Dict[str, Any]:
    """
    Record outcome delivered using franchised template.
    
    Args:
        license_id: Franchisee's license
        outcome_id: Outcome delivered
        revenue_amount: Revenue from outcome
        buyer_username: Who paid for outcome
    
    Returns:
        Revenue split and creator payment
    """
    if license_id not in LICENSES_DB:
        raise ValueError(f"License not found: {license_id}")
    
    license = LICENSES_DB[license_id]
    
    if license["status"] != "active":
        raise ValueError(f"License not active: {license['status']}")
    
    # Check monthly usage limit
    if license["license_config"].get("max_uses_per_month"):
        if license["uses_this_month"] >= license["license_config"]["max_uses_per_month"]:
            raise ValueError(f"Monthly usage limit exceeded")
    
    # Calculate creator share
    creator_share_pct = license["revenue_share_pct"] / 100
    creator_share = revenue_amount * creator_share_pct
    franchisee_net = revenue_amount - creator_share
    
    revenue_id = f"franchise_rev_{license_id}_{outcome_id}"
    
    revenue_record = {
        "revenue_id": revenue_id,
        "license_id": license_id,
        "template_id": license["template_id"],
        "outcome_id": outcome_id,
        "creator_username": license["creator_username"],
        "franchisee_username": license["franchisee_username"],
        "buyer_username": buyer_username,
        "revenue_amount": revenue_amount,
        "creator_share_pct": license["revenue_share_pct"],
        "creator_share": round(creator_share, 2),
        "franchisee_net": round(franchisee_net, 2),
        "recorded_at": datetime.now(timezone.utc).isoformat()
    }
    
    FRANCHISE_REVENUE_DB[revenue_id] = revenue_record
    
    # Update license stats
    license["total_outcomes_delivered"] += 1
    license["total_revenue_generated"] += revenue_amount
    license["total_creator_share_paid"] += creator_share
    license["uses_this_month"] += 1
    license["last_used_at"] = datetime.now(timezone.utc).isoformat()
    
    # Update template stats
    template = TEMPLATES_DB[license["template_id"]]
    template["total_outcomes_delivered"] += 1
    template["total_revenue_generated"] += revenue_amount
    template["total_franchise_revenue"] += creator_share
    
    return {
        "success": True,
        "revenue_split": {
            "total_revenue": revenue_amount,
            "creator_share": round(creator_share, 2),
            "creator_pct": license["revenue_share_pct"],
            "franchisee_net": round(franchisee_net, 2),
            "franchisee_pct": 100 - license["revenue_share_pct"]
        },
        "usage": {
            "uses_this_month": license["uses_this_month"],
            "max_uses": license["license_config"].get("max_uses_per_month", "Unlimited"),
            "total_outcomes": license["total_outcomes_delivered"]
        },
        "message": f"Creator earns ${creator_share:.2f}, Franchisee nets ${franchisee_net:.2f}"
    }


def get_template_marketplace(
    category: Optional[str] = None,
    sort_by: str = "popular"
) -> Dict[str, Any]:
    """
    Get template marketplace listings.
    
    Args:
        category: Filter by category
        sort_by: popular/revenue/recent/rating
    
    Returns:
        Marketplace listings
    """
    templates = list(TEMPLATES_DB.values())
    
    # Filter by category
    if category:
        templates = [t for t in templates if t["category"] == category]
    
    # Sort templates
    if sort_by == "popular":
        templates.sort(key=lambda x: x["total_licenses_sold"], reverse=True)
    elif sort_by == "revenue":
        templates.sort(key=lambda x: x["total_revenue_generated"], reverse=True)
    elif sort_by == "recent":
        templates.sort(key=lambda x: x["created_at"], reverse=True)
    elif sort_by == "rating":
        templates.sort(key=lambda x: x["avg_rating"], reverse=True)
    
    listings = []
    for template in templates:
        # Get cheapest license
        cheapest_license = min(
            [LICENSE_TYPES[lt] for lt in template["available_licenses"]],
            key=lambda x: x["cost"]
        )
        
        listings.append({
            "template_id": template["template_id"],
            "template_name": template["template_name"],
            "creator": template["creator_username"],
            "category": template["category"],
            "category_icon": TEMPLATE_CATEGORIES[template["category"]]["icon"],
            "description": template["description"],
            "base_price": template["base_price"],
            "starting_at": cheapest_license["cost"],
            "licenses_sold": template["total_licenses_sold"],
            "outcomes_delivered": template["total_outcomes_delivered"],
            "avg_rating": template["avg_rating"],
            "available_licenses": template["available_licenses"]
        })
    
    return {
        "templates": listings,
        "total_templates": len(listings),
        "category": category,
        "sort_by": sort_by
    }


def get_franchisee_dashboard(franchisee_username: str) -> Dict[str, Any]:
    """
    Get franchisee's dashboard.
    
    Args:
        franchisee_username: Franchisee's username
    
    Returns:
        Franchisee's licenses and performance
    """
    franchisee_licenses = [
        l for l in LICENSES_DB.values()
        if l["franchisee_username"] == franchisee_username
    ]
    
    total_licenses = len(franchisee_licenses)
    total_outcomes = sum(l["total_outcomes_delivered"] for l in franchisee_licenses)
    total_revenue = sum(l["total_revenue_generated"] for l in franchisee_licenses)
    total_creator_share = sum(l["total_creator_share_paid"] for l in franchisee_licenses)
    net_revenue = total_revenue - total_creator_share
    
    active_licenses = []
    for license in franchisee_licenses:
        if license["status"] == "active":
            active_licenses.append({
                "license_id": license["license_id"],
                "template_name": license["template_name"],
                "license_type": license["license_type"],
                "outcomes_delivered": license["total_outcomes_delivered"],
                "revenue_generated": round(license["total_revenue_generated"], 2),
                "creator_share_paid": round(license["total_creator_share_paid"], 2),
                "uses_this_month": license["uses_this_month"],
                "max_uses": license["license_config"].get("max_uses_per_month", "Unlimited")
            })
    
    return {
        "franchisee_username": franchisee_username,
        "summary": {
            "total_licenses": total_licenses,
            "active_licenses": len(active_licenses),
            "total_outcomes": total_outcomes,
            "total_revenue": round(total_revenue, 2),
            "creator_share_paid": round(total_creator_share, 2),
            "net_revenue": round(net_revenue, 2)
        },
        "active_licenses": active_licenses
    }


def get_creator_dashboard(creator_username: str) -> Dict[str, Any]:
    """
    Get template creator's dashboard.
    
    Args:
        creator_username: Creator's username
    
    Returns:
        Creator's templates and earnings
    """
    creator_templates = [
        t for t in TEMPLATES_DB.values()
        if t["creator_username"] == creator_username
    ]
    
    total_templates = len(creator_templates)
    total_licenses_sold = sum(t["total_licenses_sold"] for t in creator_templates)
    total_franchise_revenue = sum(t["total_franchise_revenue"] for t in creator_templates)
    total_outcomes = sum(t["total_outcomes_delivered"] for t in creator_templates)
    
    templates_summary = []
    for template in creator_templates:
        templates_summary.append({
            "template_id": template["template_id"],
            "template_name": template["template_name"],
            "category": template["category"],
            "licenses_sold": template["total_licenses_sold"],
            "outcomes_delivered": template["total_outcomes_delivered"],
            "franchise_revenue": round(template["total_franchise_revenue"], 2),
            "avg_rating": template["avg_rating"]
        })
    
    # Sort by revenue
    templates_summary.sort(key=lambda x: x["franchise_revenue"], reverse=True)
    
    return {
        "creator_username": creator_username,
        "summary": {
            "total_templates": total_templates,
            "total_licenses_sold": total_licenses_sold,
            "total_franchise_revenue": round(total_franchise_revenue, 2),
            "total_outcomes_delivered": total_outcomes,
            "avg_outcomes_per_license": round(total_outcomes / total_licenses_sold, 1) if total_licenses_sold > 0 else 0
        },
        "templates": templates_summary
    }


def get_template_performance(template_id: str) -> Dict[str, Any]:
    """
    Get detailed template performance metrics.
    
    Args:
        template_id: Template ID
    
    Returns:
        Performance metrics
    """
    if template_id not in TEMPLATES_DB:
        raise ValueError(f"Template not found: {template_id}")
    
    template = TEMPLATES_DB[template_id]
    
    # Get all licenses for this template
    template_licenses = [
        l for l in LICENSES_DB.values()
        if l["template_id"] == template_id
    ]
    
    # Calculate metrics
    active_licenses = [l for l in template_licenses if l["status"] == "active"]
    total_franchisees = len(set(l["franchisee_username"] for l in template_licenses))
    
    # Revenue by license type
    revenue_by_license = {}
    for license in template_licenses:
        lt = license["license_type"]
        if lt not in revenue_by_license:
            revenue_by_license[lt] = 0
        revenue_by_license[lt] += license["total_revenue_generated"]
    
    # Top franchisees
    franchisee_performance = {}
    for license in template_licenses:
        fn = license["franchisee_username"]
        if fn not in franchisee_performance:
            franchisee_performance[fn] = {
                "outcomes": 0,
                "revenue": 0.0
            }
        franchisee_performance[fn]["outcomes"] += license["total_outcomes_delivered"]
        franchisee_performance[fn]["revenue"] += license["total_revenue_generated"]
    
    top_franchisees = sorted(
        [{"username": k, **v} for k, v in franchisee_performance.items()],
        key=lambda x: x["revenue"],
        reverse=True
    )[:5]
    
    return {
        "template": {
            "template_id": template_id,
            "template_name": template["template_name"],
            "creator": template["creator_username"],
            "category": template["category"]
        },
        "metrics": {
            "total_licenses_sold": template["total_licenses_sold"],
            "active_licenses": len(active_licenses),
            "total_franchisees": total_franchisees,
            "total_outcomes": template["total_outcomes_delivered"],
            "total_revenue": round(template["total_revenue_generated"], 2),
            "franchise_revenue": round(template["total_franchise_revenue"], 2),
            "avg_rating": template["avg_rating"]
        },
        "revenue_by_license_type": revenue_by_license,
        "top_franchisees": top_franchisees
    }


def get_all_license_types() -> Dict[str, Any]:
    """Get all available license types."""
    licenses = []
    
    for license_type, config in LICENSE_TYPES.items():
        licenses.append({
            "license_type": license_type,
            "name": config["name"],
            "icon": config["icon"],
            "description": config["description"],
            "cost": config["cost"],
            "billing_type": config["type"],
            "revenue_share_pct": config["revenue_share_pct"],
            "territory_exclusive": config.get("territory_exclusive", False),
            "support_included": config.get("support_included", False),
            "max_uses": config.get("max_uses_per_month", "Unlimited")
        })
    
    return {
        "license_types": licenses,
        "total_types": len(licenses)
    }


# Example usage
if __name__ == "__main__":
    # Create template
    template = create_template(
        "wade999",
        "LinkedIn Lead Gen System",
        "marketing",
        "Proven system for generating 50+ leads/month on LinkedIn",
        2500.0,
        ["basic", "professional", "exclusive"]
    )
    print(f"Template created: {template['template']['template_name']}")
    
    # Purchase license
    license = purchase_license(
        "franchisee123",
        template['template']['template_id'],
        "professional",
        territory="New York"
    )
    print(f"\nLicense purchased: {license['license']['license_type']}")
    print(f"Cost: ${license['payment_due']['amount']}")
    
    # Record franchise outcome
    revenue = record_franchise_outcome(
        license['license']['license_id'],
        "outcome_456",
        2500.0,
        "buyer789"
    )
    print(f"\nRevenue split:")
    print(f"Creator: ${revenue['revenue_split']['creator_share']}")
    print(f"Franchisee: ${revenue['revenue_split']['franchisee_net']}")
