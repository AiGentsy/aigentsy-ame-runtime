"""
AUTONOMOUS PARTNER MESH
=======================

Automated partner onboarding, JV creation, and revenue sharing.
Partners can plug into AiGentsy's outcome infrastructure with minimal friction.

Partner types:
- Referral: Earn commission on referred outcomes
- Integration: Build on AiGentsy APIs
- White-label: Full white-label outcome platform
- Strategic: Co-development partnerships

Revenue:
- 0.5% mesh coordination fee on all partner transactions

Usage:
    from partner_mesh import onboard_partner, create_auto_jv, route_to_partner, get_partner_performance
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from uuid import uuid4
from collections import defaultdict

def _now():
    return datetime.now(timezone.utc).isoformat() + "Z"


# Partner tier definitions
PARTNER_TIERS = {
    "referral": {
        "name": "Referral Partner",
        "commission_pct": 0.10,  # 10% on referred outcomes
        "requirements": {},
        "features": ["Referral links", "Basic dashboard", "Monthly payouts"]
    },
    "integration": {
        "name": "Integration Partner",
        "commission_pct": 0.15,
        "requirements": {"min_volume": 1000},  # $1K monthly
        "features": ["API access", "Webhooks", "Custom integrations", "Priority support"]
    },
    "white_label": {
        "name": "White-Label Partner",
        "commission_pct": 0.20,
        "requirements": {"min_volume": 10000, "min_ocs": 60},
        "features": ["Full white-label", "Custom branding", "Dedicated support", "SLA guarantee"]
    },
    "strategic": {
        "name": "Strategic Partner",
        "commission_pct": 0.25,  # Negotiable
        "requirements": {"min_volume": 50000, "min_ocs": 75},
        "features": ["Co-development", "Revenue sharing", "Equity partnership", "Board seat"]
    }
}

# Mesh fee
MESH_COORDINATION_FEE_PCT = 0.005  # 0.5%

# Auto-JV rules
AUTO_JV_THRESHOLD = 5000  # $5K mutual volume triggers JV suggestion
AUTO_JV_MIN_OCS = 60  # Minimum OCS for auto-JV

# Storage
_PARTNERS: Dict[str, Dict[str, Any]] = {}
_JVS: Dict[str, Dict[str, Any]] = {}
_TRANSACTIONS: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
_ROUTING_RULES: Dict[str, Dict[str, Any]] = {}


class PartnerMesh:
    """
    Autonomous partner management and JV orchestration.
    """

    def __init__(self):
        self.tiers = PARTNER_TIERS
        self.mesh_fee = MESH_COORDINATION_FEE_PCT
        self.auto_jv_threshold = AUTO_JV_THRESHOLD

    def onboard_partner(
        self,
        partner_id: str,
        tier: str,
        *,
        company_name: str = "",
        contact_email: str = "",
        website: str = None,
        api_callback_url: str = None,
        branding: dict = None,
        categories: list = None,
        metadata: dict = None
    ) -> Dict[str, Any]:
        """
        Onboard a new partner to the mesh.

        Args:
            partner_id: Unique partner ID
            tier: Partner tier (referral, integration, white_label, strategic)
            company_name: Company name
            contact_email: Contact email
            website: Partner website
            api_callback_url: Webhook URL for events
            branding: Custom branding config
            categories: Categories partner handles
            metadata: Additional info

        Returns:
            Partner onboarding details
        """
        if tier not in self.tiers:
            return {"ok": False, "error": "invalid_tier", "valid_tiers": list(self.tiers.keys())}

        if partner_id in _PARTNERS:
            return {"ok": False, "error": "partner_already_exists"}

        tier_config = self.tiers[tier]

        # Generate API key
        api_key = f"pk_{uuid4().hex}"

        partner = {
            "id": partner_id,
            "tier": tier,
            "tier_name": tier_config["name"],
            "company_name": company_name,
            "contact_email": contact_email,
            "website": website,
            "api_key": api_key,
            "api_callback_url": api_callback_url,
            "branding": branding or {},
            "categories": categories or ["all"],
            "commission_pct": tier_config["commission_pct"],
            "metadata": metadata or {},
            "status": "ACTIVE",
            "onboarded_at": _now(),
            "stats": {
                "total_volume": 0.0,
                "total_transactions": 0,
                "total_commissions": 0.0,
                "avg_outcome_value": 0.0,
                "success_rate": 0.0
            },
            "jvs": [],
            "events": [{"type": "PARTNER_ONBOARDED", "tier": tier, "at": _now()}]
        }

        _PARTNERS[partner_id] = partner

        return {
            "ok": True,
            "partner": partner,
            "api_key": api_key,
            "commission_pct": tier_config["commission_pct"],
            "features": tier_config["features"]
        }

    def create_auto_jv(
        self,
        partner_a_id: str,
        partner_b_id: str,
        *,
        title: str = None,
        revenue_split: dict = None,
        duration_days: int = 90,
        categories: list = None
    ) -> Dict[str, Any]:
        """
        Create an automatic JV between two partners.

        Args:
            partner_a_id: First partner ID
            partner_b_id: Second partner ID
            title: JV title
            revenue_split: Custom split (default 50/50)
            duration_days: JV duration
            categories: Categories covered

        Returns:
            JV details
        """
        partner_a = _PARTNERS.get(partner_a_id)
        partner_b = _PARTNERS.get(partner_b_id)

        if not partner_a:
            return {"ok": False, "error": "partner_a_not_found"}
        if not partner_b:
            return {"ok": False, "error": "partner_b_not_found"}

        if partner_a_id == partner_b_id:
            return {"ok": False, "error": "cannot_jv_with_self"}

        # Default 50/50 split
        if revenue_split is None:
            revenue_split = {partner_a_id: 0.50, partner_b_id: 0.50}

        # Validate split totals 100%
        if abs(sum(revenue_split.values()) - 1.0) > 0.01:
            return {"ok": False, "error": "revenue_split_must_equal_100_percent"}

        jv_id = f"jv_{uuid4().hex[:8]}"

        jv = {
            "id": jv_id,
            "partners": [partner_a_id, partner_b_id],
            "title": title or f"JV: {partner_a['company_name']} + {partner_b['company_name']}",
            "revenue_split": revenue_split,
            "duration_days": duration_days,
            "categories": categories or ["all"],
            "status": "ACTIVE",
            "created_at": _now(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=duration_days)).isoformat() + "Z",
            "stats": {
                "total_volume": 0.0,
                "total_transactions": 0,
                "distributions": []
            },
            "events": [{"type": "JV_CREATED", "at": _now()}]
        }

        _JVS[jv_id] = jv

        # Add to partners
        partner_a["jvs"].append(jv_id)
        partner_b["jvs"].append(jv_id)

        partner_a["events"].append({"type": "JV_JOINED", "jv_id": jv_id, "at": _now()})
        partner_b["events"].append({"type": "JV_JOINED", "jv_id": jv_id, "at": _now()})

        return {
            "ok": True,
            "jv": jv,
            "message": f"JV created between {partner_a['company_name']} and {partner_b['company_name']}"
        }

    def route_to_partner(
        self,
        outcome_id: str,
        amount: float,
        *,
        category: str = "general",
        source_partner_id: str = None,
        jv_id: str = None
    ) -> Dict[str, Any]:
        """
        Route an outcome to partner(s) and process commissions.

        Args:
            outcome_id: Outcome ID
            amount: Outcome value
            category: Outcome category
            source_partner_id: Referring/source partner
            jv_id: JV to use (if applicable)

        Returns:
            Routing and commission details
        """
        transaction_id = f"ptx_{uuid4().hex[:8]}"
        mesh_fee = round(amount * self.mesh_fee, 2)
        commissions = []

        # Process source partner commission
        if source_partner_id:
            partner = _PARTNERS.get(source_partner_id)
            if partner and partner["status"] == "ACTIVE":
                commission = round(amount * partner["commission_pct"], 2)
                commissions.append({
                    "partner_id": source_partner_id,
                    "type": "referral",
                    "amount": commission
                })

                # Update partner stats
                partner["stats"]["total_volume"] += amount
                partner["stats"]["total_transactions"] += 1
                partner["stats"]["total_commissions"] += commission

                _TRANSACTIONS[source_partner_id].append({
                    "id": transaction_id,
                    "outcome_id": outcome_id,
                    "amount": amount,
                    "commission": commission,
                    "at": _now()
                })

        # Process JV distribution
        if jv_id:
            jv = _JVS.get(jv_id)
            if jv and jv["status"] == "ACTIVE":
                net_amount = amount - mesh_fee
                for partner_id, split_pct in jv["revenue_split"].items():
                    partner_share = round(net_amount * split_pct, 2)
                    commissions.append({
                        "partner_id": partner_id,
                        "type": "jv_share",
                        "amount": partner_share,
                        "jv_id": jv_id
                    })

                    partner = _PARTNERS.get(partner_id)
                    if partner:
                        partner["stats"]["total_commissions"] += partner_share

                jv["stats"]["total_volume"] += amount
                jv["stats"]["total_transactions"] += 1
                jv["stats"]["distributions"].append({
                    "outcome_id": outcome_id,
                    "amount": amount,
                    "distributed_at": _now()
                })

        # Post mesh fee to ledger
        try:
            from monetization.ledger import post_entry
            post_entry(
                entry_type="mesh_coordination_fee",
                ref=f"mesh:{transaction_id}",
                debit=0,
                credit=mesh_fee,
                meta={
                    "outcome_id": outcome_id,
                    "source_partner": source_partner_id,
                    "jv_id": jv_id
                }
            )

            # Post commissions
            for comm in commissions:
                post_entry(
                    entry_type="partner_commission",
                    ref=f"mesh:{transaction_id}:{comm['partner_id']}",
                    debit=0,
                    credit=comm["amount"],
                    meta=comm
                )
        except ImportError:
            pass

        return {
            "ok": True,
            "transaction_id": transaction_id,
            "outcome_id": outcome_id,
            "amount": amount,
            "mesh_fee": mesh_fee,
            "commissions": commissions,
            "total_distributed": sum(c["amount"] for c in commissions)
        }

    def suggest_jv(self, partner_id: str) -> Dict[str, Any]:
        """
        Suggest potential JV partners based on complementary activity.
        """
        partner = _PARTNERS.get(partner_id)
        if not partner:
            return {"ok": False, "error": "partner_not_found"}

        # Find partners with complementary categories and good volume
        suggestions = []
        partner_categories = set(partner.get("categories", ["all"]))

        for other_id, other in _PARTNERS.items():
            if other_id == partner_id:
                continue
            if other["status"] != "ACTIVE":
                continue

            # Skip if already in JV
            shared_jvs = set(partner.get("jvs", [])) & set(other.get("jvs", []))
            if shared_jvs:
                continue

            other_categories = set(other.get("categories", ["all"]))

            # Check for complementary categories
            overlap = partner_categories & other_categories
            complement = partner_categories ^ other_categories

            if complement or "all" in partner_categories or "all" in other_categories:
                # Calculate synergy score
                combined_volume = partner["stats"]["total_volume"] + other["stats"]["total_volume"]
                synergy_score = min(1.0, combined_volume / self.auto_jv_threshold)

                suggestions.append({
                    "partner_id": other_id,
                    "company_name": other["company_name"],
                    "tier": other["tier"],
                    "categories": list(other_categories),
                    "volume": other["stats"]["total_volume"],
                    "synergy_score": round(synergy_score, 2),
                    "recommended_split": {partner_id: 0.50, other_id: 0.50}
                })

        # Sort by synergy score
        suggestions.sort(key=lambda x: x["synergy_score"], reverse=True)

        return {
            "ok": True,
            "partner_id": partner_id,
            "suggestions": suggestions[:5],  # Top 5
            "auto_jv_threshold": self.auto_jv_threshold
        }

    def add_routing_rule(
        self,
        rule_id: str,
        *,
        category: str = None,
        min_value: float = None,
        max_value: float = None,
        target_partner_id: str = None,
        target_jv_id: str = None,
        priority: int = 0
    ) -> Dict[str, Any]:
        """
        Add an automatic routing rule.
        """
        rule = {
            "id": rule_id,
            "category": category,
            "min_value": min_value,
            "max_value": max_value,
            "target_partner_id": target_partner_id,
            "target_jv_id": target_jv_id,
            "priority": priority,
            "status": "ACTIVE",
            "created_at": _now()
        }

        _ROUTING_RULES[rule_id] = rule

        return {"ok": True, "rule": rule}

    def get_partner_performance(self, partner_id: str) -> Dict[str, Any]:
        """Get partner performance metrics"""
        partner = _PARTNERS.get(partner_id)
        if not partner:
            return {"ok": False, "error": "partner_not_found"}

        transactions = _TRANSACTIONS.get(partner_id, [])
        recent = [t for t in transactions if t["at"] >= (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()]

        return {
            "partner_id": partner_id,
            "company_name": partner["company_name"],
            "tier": partner["tier"],
            "total_volume": round(partner["stats"]["total_volume"], 2),
            "total_transactions": partner["stats"]["total_transactions"],
            "total_commissions": round(partner["stats"]["total_commissions"], 2),
            "recent_30d": {
                "transactions": len(recent),
                "volume": round(sum(t["amount"] for t in recent), 2),
                "commissions": round(sum(t["commission"] for t in recent), 2)
            },
            "active_jvs": len([jv_id for jv_id in partner["jvs"] if _JVS.get(jv_id, {}).get("status") == "ACTIVE"]),
            "commission_rate": partner["commission_pct"]
        }

    def upgrade_partner_tier(self, partner_id: str, new_tier: str) -> Dict[str, Any]:
        """Upgrade partner to higher tier"""
        partner = _PARTNERS.get(partner_id)
        if not partner:
            return {"ok": False, "error": "partner_not_found"}

        if new_tier not in self.tiers:
            return {"ok": False, "error": "invalid_tier"}

        new_config = self.tiers[new_tier]

        # Check requirements
        reqs = new_config.get("requirements", {})
        if "min_volume" in reqs and partner["stats"]["total_volume"] < reqs["min_volume"]:
            return {
                "ok": False,
                "error": "insufficient_volume",
                "required": reqs["min_volume"],
                "current": partner["stats"]["total_volume"]
            }

        old_tier = partner["tier"]
        partner["tier"] = new_tier
        partner["tier_name"] = new_config["name"]
        partner["commission_pct"] = new_config["commission_pct"]

        partner["events"].append({
            "type": "TIER_UPGRADED",
            "from": old_tier,
            "to": new_tier,
            "at": _now()
        })

        return {
            "ok": True,
            "partner_id": partner_id,
            "old_tier": old_tier,
            "new_tier": new_tier,
            "new_commission_pct": new_config["commission_pct"],
            "new_features": new_config["features"]
        }

    def get_partner(self, partner_id: str) -> Optional[Dict[str, Any]]:
        """Get partner details"""
        return _PARTNERS.get(partner_id)

    def get_jv(self, jv_id: str) -> Optional[Dict[str, Any]]:
        """Get JV details"""
        return _JVS.get(jv_id)

    def get_stats(self) -> Dict[str, Any]:
        """Get mesh statistics"""
        total_partners = len(_PARTNERS)
        active_partners = len([p for p in _PARTNERS.values() if p["status"] == "ACTIVE"])
        total_jvs = len(_JVS)
        active_jvs = len([j for j in _JVS.values() if j["status"] == "ACTIVE"])

        total_volume = sum(p["stats"]["total_volume"] for p in _PARTNERS.values())
        total_commissions = sum(p["stats"]["total_commissions"] for p in _PARTNERS.values())
        total_mesh_fees = total_volume * self.mesh_fee

        return {
            "total_partners": total_partners,
            "active_partners": active_partners,
            "by_tier": {
                tier: len([p for p in _PARTNERS.values() if p["tier"] == tier])
                for tier in self.tiers.keys()
            },
            "total_jvs": total_jvs,
            "active_jvs": active_jvs,
            "total_volume": round(total_volume, 2),
            "total_commissions_paid": round(total_commissions, 2),
            "total_mesh_fees": round(total_mesh_fees, 2),
            "routing_rules": len(_ROUTING_RULES)
        }


# Module-level singleton
_mesh = PartnerMesh()


def onboard_partner(partner_id: str, tier: str, **kwargs) -> Dict[str, Any]:
    """Onboard new partner"""
    return _mesh.onboard_partner(partner_id, tier, **kwargs)


def create_auto_jv(partner_a_id: str, partner_b_id: str, **kwargs) -> Dict[str, Any]:
    """Create automatic JV"""
    return _mesh.create_auto_jv(partner_a_id, partner_b_id, **kwargs)


def route_to_partner(outcome_id: str, amount: float, **kwargs) -> Dict[str, Any]:
    """Route outcome to partner(s)"""
    return _mesh.route_to_partner(outcome_id, amount, **kwargs)


def suggest_jv(partner_id: str) -> Dict[str, Any]:
    """Suggest JV partners"""
    return _mesh.suggest_jv(partner_id)


def add_routing_rule(rule_id: str, **kwargs) -> Dict[str, Any]:
    """Add routing rule"""
    return _mesh.add_routing_rule(rule_id, **kwargs)


def get_partner_performance(partner_id: str) -> Dict[str, Any]:
    """Get partner performance"""
    return _mesh.get_partner_performance(partner_id)


def upgrade_partner_tier(partner_id: str, new_tier: str) -> Dict[str, Any]:
    """Upgrade partner tier"""
    return _mesh.upgrade_partner_tier(partner_id, new_tier)


def get_partner(partner_id: str) -> Optional[Dict[str, Any]]:
    """Get partner details"""
    return _mesh.get_partner(partner_id)


def get_jv(jv_id: str) -> Optional[Dict[str, Any]]:
    """Get JV details"""
    return _mesh.get_jv(jv_id)


def get_mesh_stats() -> Dict[str, Any]:
    """Get mesh statistics"""
    return _mesh.get_stats()
