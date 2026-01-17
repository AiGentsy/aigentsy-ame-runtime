"""
AUTONOMOUS DEAL GRAPH - Relationship Memory System
===================================================

THE MOAT:
Every deal seeds future deals. Network effects on relationships.
Customer acquisition cost → $0 over time.

WHAT IT DOES:
1. Track relationships between clients across all deals
2. Detect connection opportunities (Client A knows Client B)
3. Auto-generate warm intro opportunities
4. Compound relationship value over time

RELATIONSHIP TYPES:
- Client completed a job → Strong connection
- Client referred someone → Very strong connection
- Same industry/vertical → Weak connection
- Mutual connections (social) → Medium connection
- Repeat client → Very strong connection

INTEGRATES WITH:
- jv_mesh.py (partnership tracking)
- metabridge.py (team formation)
- intent_exchange.py (deal flow)
- yield_memory.py (pattern storage)

v2.0 AI FAMILY BRAIN INTEGRATION:
- AI-powered need prediction
- AI-generated intro messages
- Learning from successful intros
- Cross-pollination with MetaHive patterns
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from uuid import uuid4
from collections import defaultdict
import json

# ============================================================
# AI FAMILY BRAIN INTEGRATION
# ============================================================

try:
    from ai_family_brain import (
        get_brain, ai_execute, ai_content, TaskCategory,
        record_quality, get_family_stats
    )
    AI_FAMILY_AVAILABLE = True
except ImportError:
    AI_FAMILY_AVAILABLE = False

try:
    from metahive_brain import contribute_to_hive, query_hive
    METAHIVE_AVAILABLE = True
except ImportError:
    METAHIVE_AVAILABLE = False

try:
    from yield_memory import store_pattern, get_best_action
    YIELD_AVAILABLE = True
except ImportError:
    YIELD_AVAILABLE = False


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _generate_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


# ============================================================
# RELATIONSHIP TYPES & WEIGHTS
# ============================================================

class RelationshipType(str, Enum):
    """Types of relationships between entities"""
    JOB_COMPLETED = "job_completed"  # You completed work for them
    JOB_RECEIVED = "job_received"  # They completed work for you
    REFERRAL_GIVEN = "referral_given"  # They referred you to someone
    REFERRAL_RECEIVED = "referral_received"  # You referred them
    MUTUAL_CONNECTION = "mutual_connection"  # LinkedIn/social connection
    SAME_INDUSTRY = "same_industry"  # Same vertical
    SAME_COMPANY = "same_company"  # Works at same company
    JV_PARTNER = "jv_partner"  # JV partnership
    TEAM_MEMBER = "team_member"  # Worked on team together
    REPEAT_CLIENT = "repeat_client"  # Multiple jobs
    WARM_INTRO = "warm_intro"  # Introduced by someone


# Relationship strength weights
RELATIONSHIP_WEIGHTS = {
    RelationshipType.JOB_COMPLETED: 0.5,
    RelationshipType.JOB_RECEIVED: 0.4,
    RelationshipType.REFERRAL_GIVEN: 0.8,
    RelationshipType.REFERRAL_RECEIVED: 0.7,
    RelationshipType.MUTUAL_CONNECTION: 0.2,
    RelationshipType.SAME_INDUSTRY: 0.1,
    RelationshipType.SAME_COMPANY: 0.3,
    RelationshipType.JV_PARTNER: 0.6,
    RelationshipType.TEAM_MEMBER: 0.5,
    RelationshipType.REPEAT_CLIENT: 0.9,
    RelationshipType.WARM_INTRO: 0.6,
}

# Decay rates (strength decays over time)
DECAY_RATES = {
    RelationshipType.JOB_COMPLETED: 0.95,  # Per 30 days
    RelationshipType.REFERRAL_GIVEN: 0.98,  # Referrals decay slowly
    RelationshipType.MUTUAL_CONNECTION: 0.99,  # Social barely decays
    RelationshipType.REPEAT_CLIENT: 1.0,  # Never decays
}


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class Entity:
    """A person or company in the graph"""
    entity_id: str
    entity_type: str  # person, company, agent
    name: str
    email: Optional[str] = None
    domain: Optional[str] = None
    industry: Optional[str] = None
    linkedin_url: Optional[str] = None
    company_id: Optional[str] = None  # If person, their company
    
    # Metadata
    first_seen: str = field(default_factory=_now)
    last_interaction: str = field(default_factory=_now)
    total_interactions: int = 0
    total_deal_value: float = 0.0
    
    # Tags
    tags: List[str] = field(default_factory=list)
    
    # AI Family tracking (NEW)
    ai_predicted_needs: List[str] = field(default_factory=list)
    ai_engagement_score: float = 0.5
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Relationship:
    """A relationship between two entities"""
    relationship_id: str
    source_entity_id: str
    target_entity_id: str
    relationship_type: RelationshipType
    
    # Strength (0.0 - 1.0)
    base_strength: float
    current_strength: float
    
    # Context
    context: Dict[str, Any] = field(default_factory=dict)
    deal_ids: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: str = field(default_factory=_now)
    last_interaction: str = field(default_factory=_now)
    interaction_count: int = 1
    
    # AI Family tracking (NEW)
    ai_quality_score: float = 0.5
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result["relationship_type"] = self.relationship_type.value
        return result
    
    def decay_strength(self, days_since_interaction: int):
        """Apply time decay to relationship strength"""
        decay_rate = DECAY_RATES.get(self.relationship_type, 0.95)
        periods = days_since_interaction / 30  # Monthly decay
        self.current_strength = self.base_strength * (decay_rate ** periods)


@dataclass
class IntroOpportunity:
    """A potential warm intro opportunity"""
    opportunity_id: str
    
    # The path
    source_entity_id: str  # You
    connector_entity_id: str  # Person who can intro
    target_entity_id: str  # Who you want to reach
    
    # Relationship chain
    source_to_connector: Relationship
    connector_to_target: Relationship
    
    # Strength
    path_strength: float  # Combined strength of the path
    confidence: float
    
    # Target's predicted need
    predicted_need: Optional[str] = None
    estimated_value: float = 0.0
    
    # Suggested action
    suggested_message: str = ""
    urgency: str = "medium"
    
    # Status
    status: str = "pending"  # pending, requested, completed, declined
    created_at: str = field(default_factory=_now)
    
    # AI Family tracking (NEW)
    ai_model_used: str = ""
    ai_task_id: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "opportunity_id": self.opportunity_id,
            "source_entity_id": self.source_entity_id,
            "connector_entity_id": self.connector_entity_id,
            "target_entity_id": self.target_entity_id,
            "path_strength": self.path_strength,
            "confidence": self.confidence,
            "predicted_need": self.predicted_need,
            "estimated_value": self.estimated_value,
            "suggested_message": self.suggested_message,
            "urgency": self.urgency,
            "status": self.status,
            "created_at": self.created_at,
            "ai_model_used": self.ai_model_used
        }


# ============================================================
# RELATIONSHIP GRAPH
# ============================================================

class RelationshipGraph:
    """
    Graph database for tracking relationships
    
    Structure:
    - Entities (nodes): People, companies, agents
    - Relationships (edges): Connections with weights
    """
    
    def __init__(self):
        # Entity storage
        self._entities: Dict[str, Entity] = {}
        self._entities_by_email: Dict[str, str] = {}  # email -> entity_id
        self._entities_by_domain: Dict[str, List[str]] = defaultdict(list)  # domain -> entity_ids
        
        # Relationship storage
        self._relationships: Dict[str, Relationship] = {}
        self._outgoing: Dict[str, List[str]] = defaultdict(list)  # entity_id -> relationship_ids
        self._incoming: Dict[str, List[str]] = defaultdict(list)  # entity_id -> relationship_ids
        
        # Industry index
        self._entities_by_industry: Dict[str, List[str]] = defaultdict(list)
    
    # ==================== ENTITY OPERATIONS ====================
    
    def add_entity(
        self,
        entity_type: str,
        name: str,
        email: str = None,
        domain: str = None,
        industry: str = None,
        linkedin_url: str = None,
        company_id: str = None,
        tags: List[str] = None
    ) -> Entity:
        """Add or update an entity"""
        
        # Check if entity already exists
        existing_id = None
        if email and email in self._entities_by_email:
            existing_id = self._entities_by_email[email]
        
        if existing_id:
            # Update existing
            entity = self._entities[existing_id]
            entity.last_interaction = _now()
            entity.total_interactions += 1
            if industry and not entity.industry:
                entity.industry = industry
            if tags:
                entity.tags = list(set(entity.tags + tags))
            return entity
        
        # Create new
        entity_id = _generate_id("ent")
        
        entity = Entity(
            entity_id=entity_id,
            entity_type=entity_type,
            name=name,
            email=email,
            domain=domain,
            industry=industry,
            linkedin_url=linkedin_url,
            company_id=company_id,
            tags=tags or []
        )
        
        # Store
        self._entities[entity_id] = entity
        
        # Index
        if email:
            self._entities_by_email[email] = entity_id
        if domain:
            self._entities_by_domain[domain].append(entity_id)
        if industry:
            self._entities_by_industry[industry].append(entity_id)
        
        return entity
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID"""
        return self._entities.get(entity_id)
    
    def find_entity_by_email(self, email: str) -> Optional[Entity]:
        """Find entity by email"""
        entity_id = self._entities_by_email.get(email)
        if entity_id:
            return self._entities.get(entity_id)
        return None
    
    def find_entities_by_industry(self, industry: str) -> List[Entity]:
        """Find all entities in an industry"""
        entity_ids = self._entities_by_industry.get(industry, [])
        return [self._entities[eid] for eid in entity_ids if eid in self._entities]
    
    # ==================== RELATIONSHIP OPERATIONS ====================
    
    def add_relationship(
        self,
        source_entity_id: str,
        target_entity_id: str,
        relationship_type: RelationshipType,
        context: Dict = None,
        deal_id: str = None
    ) -> Relationship:
        """Add or strengthen a relationship"""
        
        # Check if relationship already exists
        existing_rel = self._find_relationship(source_entity_id, target_entity_id, relationship_type)
        
        if existing_rel:
            # Strengthen existing relationship
            existing_rel.interaction_count += 1
            existing_rel.last_interaction = _now()
            
            # Increase base strength (compound effect)
            existing_rel.base_strength = min(1.0, existing_rel.base_strength * 1.1)
            existing_rel.current_strength = existing_rel.base_strength
            
            if deal_id:
                existing_rel.deal_ids.append(deal_id)
            if context:
                existing_rel.context.update(context)
            
            return existing_rel
        
        # Create new relationship
        rel_id = _generate_id("rel")
        base_strength = RELATIONSHIP_WEIGHTS.get(relationship_type, 0.3)
        
        relationship = Relationship(
            relationship_id=rel_id,
            source_entity_id=source_entity_id,
            target_entity_id=target_entity_id,
            relationship_type=relationship_type,
            base_strength=base_strength,
            current_strength=base_strength,
            context=context or {},
            deal_ids=[deal_id] if deal_id else []
        )
        
        # Store
        self._relationships[rel_id] = relationship
        self._outgoing[source_entity_id].append(rel_id)
        self._incoming[target_entity_id].append(rel_id)
        
        return relationship
    
    def _find_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: RelationshipType
    ) -> Optional[Relationship]:
        """Find existing relationship between two entities"""
        rel_ids = self._outgoing.get(source_id, [])
        
        for rel_id in rel_ids:
            rel = self._relationships.get(rel_id)
            if rel and rel.target_entity_id == target_id and rel.relationship_type == rel_type:
                return rel
        
        return None
    
    def get_relationships(self, entity_id: str, direction: str = "both") -> List[Relationship]:
        """Get all relationships for an entity"""
        relationships = []
        
        if direction in ["outgoing", "both"]:
            for rel_id in self._outgoing.get(entity_id, []):
                rel = self._relationships.get(rel_id)
                if rel:
                    relationships.append(rel)
        
        if direction in ["incoming", "both"]:
            for rel_id in self._incoming.get(entity_id, []):
                rel = self._relationships.get(rel_id)
                if rel:
                    relationships.append(rel)
        
        return relationships
    
    def get_connection_strength(self, entity1_id: str, entity2_id: str) -> float:
        """Get total connection strength between two entities"""
        total_strength = 0.0
        
        # Check outgoing
        for rel_id in self._outgoing.get(entity1_id, []):
            rel = self._relationships.get(rel_id)
            if rel and rel.target_entity_id == entity2_id:
                total_strength += rel.current_strength
        
        # Check incoming
        for rel_id in self._incoming.get(entity1_id, []):
            rel = self._relationships.get(rel_id)
            if rel and rel.source_entity_id == entity2_id:
                total_strength += rel.current_strength
        
        return min(1.0, total_strength)
    
    # ==================== PATH FINDING ====================
    
    def find_paths(
        self,
        source_id: str,
        target_id: str,
        max_hops: int = 2
    ) -> List[List[Tuple[str, Relationship]]]:
        """
        Find all paths between source and target
        Returns list of paths, each path is list of (entity_id, relationship)
        """
        paths = []
        
        # Direct connection
        direct_rels = []
        for rel_id in self._outgoing.get(source_id, []):
            rel = self._relationships.get(rel_id)
            if rel and rel.target_entity_id == target_id:
                direct_rels.append(rel)
        
        for rel in direct_rels:
            paths.append([(target_id, rel)])
        
        # 2-hop paths
        if max_hops >= 2:
            for rel_id in self._outgoing.get(source_id, []):
                rel1 = self._relationships.get(rel_id)
                if not rel1:
                    continue
                
                connector_id = rel1.target_entity_id
                if connector_id == target_id:
                    continue
                
                # Check if connector connects to target
                for rel2_id in self._outgoing.get(connector_id, []):
                    rel2 = self._relationships.get(rel2_id)
                    if rel2 and rel2.target_entity_id == target_id:
                        paths.append([
                            (connector_id, rel1),
                            (target_id, rel2)
                        ])
        
        return paths
    
    def find_connectors(self, source_id: str, target_industry: str = None) -> List[Dict]:
        """
        Find entities that can connect source to new opportunities
        
        Returns entities that source is connected to AND have connections
        in the target industry (or generally well-connected)
        """
        connectors = []
        
        # Get all entities source is connected to
        for rel_id in self._outgoing.get(source_id, []):
            rel = self._relationships.get(rel_id)
            if not rel or rel.current_strength < 0.3:  # Only strong connections
                continue
            
            connector = self._entities.get(rel.target_entity_id)
            if not connector:
                continue
            
            # Count connector's connections
            connector_rels = self.get_relationships(connector.entity_id, "outgoing")
            
            # Filter by industry if specified
            if target_industry:
                relevant_rels = [
                    r for r in connector_rels
                    if self._entities.get(r.target_entity_id, Entity("", "", "")).industry == target_industry
                ]
            else:
                relevant_rels = connector_rels
            
            if len(relevant_rels) > 0:
                connectors.append({
                    "connector": connector,
                    "relationship_to_source": rel,
                    "connection_count": len(relevant_rels),
                    "target_connections": [
                        {
                            "entity": self._entities.get(r.target_entity_id),
                            "relationship": r
                        }
                        for r in relevant_rels[:5]  # Top 5
                    ]
                })
        
        # Sort by connection strength and reach
        connectors.sort(
            key=lambda c: c["relationship_to_source"].current_strength * c["connection_count"],
            reverse=True
        )
        
        return connectors


# ============================================================
# DEAL GRAPH - Tracks Deals and Extracts Relationships
# ============================================================

class DealGraph:
    """
    Tracks deals and automatically extracts relationships
    
    When a deal completes:
    1. Extract entities (client, team members)
    2. Create/strengthen relationships
    3. Detect intro opportunities
    
    v2.0: AI Family Brain Integration
    - Uses AI to predict needs
    - AI-generated personalized intro messages
    - Learns from successful intros via MetaHive
    """
    
    def __init__(self):
        self.graph = RelationshipGraph()
        self._deals: Dict[str, Dict] = {}
        self._intro_opportunities: Dict[str, IntroOpportunity] = {}
        
        # Your entity (AiGentsy/user)
        self._self_entity_id: Optional[str] = None
        
        # AI Family tracking (NEW)
        self._ai_tasks: List[Dict] = []
        self._intro_outcomes: List[Dict] = []
    
    def set_self(self, name: str, email: str) -> str:
        """Set the 'self' entity (you/AiGentsy)"""
        entity = self.graph.add_entity(
            entity_type="agent",
            name=name,
            email=email,
            tags=["self"]
        )
        self._self_entity_id = entity.entity_id
        return entity.entity_id
    
    def record_deal(
        self,
        deal_id: str,
        client_name: str,
        client_email: str,
        client_company: str = None,
        client_industry: str = None,
        deal_value: float = 0.0,
        service_type: str = None,
        team_members: List[Dict] = None,
        referrer: Dict = None,
        status: str = "completed"
    ) -> Dict[str, Any]:
        """
        Record a completed deal and extract relationships
        """
        
        # 1. Create/update client entity
        client_entity = self.graph.add_entity(
            entity_type="person",
            name=client_name,
            email=client_email,
            domain=client_email.split("@")[1] if "@" in client_email else None,
            industry=client_industry,
            tags=["client"]
        )
        client_entity.total_deal_value += deal_value
        
        # 2. Create company entity if provided
        company_entity = None
        if client_company:
            company_entity = self.graph.add_entity(
                entity_type="company",
                name=client_company,
                domain=client_email.split("@")[1] if "@" in client_email else None,
                industry=client_industry,
                tags=["client_company"]
            )
            client_entity.company_id = company_entity.entity_id
        
        # 3. Create relationship: Self → Client (job completed)
        if self._self_entity_id:
            # Check if repeat client
            existing_rel = self.graph._find_relationship(
                self._self_entity_id,
                client_entity.entity_id,
                RelationshipType.JOB_COMPLETED
            )
            
            rel_type = RelationshipType.REPEAT_CLIENT if existing_rel else RelationshipType.JOB_COMPLETED
            
            self.graph.add_relationship(
                source_entity_id=self._self_entity_id,
                target_entity_id=client_entity.entity_id,
                relationship_type=rel_type,
                context={
                    "deal_value": deal_value,
                    "service_type": service_type,
                    "completed_at": _now()
                },
                deal_id=deal_id
            )
        
        # 4. Record referrer relationship if exists
        referrer_entity = None
        if referrer:
            referrer_entity = self.graph.add_entity(
                entity_type="person",
                name=referrer.get("name"),
                email=referrer.get("email"),
                industry=referrer.get("industry"),
                tags=["referrer"]
            )
            
            # Referrer → Client (they know each other)
            self.graph.add_relationship(
                source_entity_id=referrer_entity.entity_id,
                target_entity_id=client_entity.entity_id,
                relationship_type=RelationshipType.MUTUAL_CONNECTION,
                context={"referral_context": True},
                deal_id=deal_id
            )
            
            # Self → Referrer (they referred us)
            if self._self_entity_id:
                self.graph.add_relationship(
                    source_entity_id=self._self_entity_id,
                    target_entity_id=referrer_entity.entity_id,
                    relationship_type=RelationshipType.REFERRAL_RECEIVED,
                    context={"referred_client": client_entity.entity_id},
                    deal_id=deal_id
                )
        
        # 5. Record team member relationships
        team_entities = []
        if team_members:
            for member in team_members:
                member_entity = self.graph.add_entity(
                    entity_type="person",
                    name=member.get("name"),
                    email=member.get("email"),
                    tags=["team_member"]
                )
                team_entities.append(member_entity)
                
                # Self → Team member
                if self._self_entity_id:
                    self.graph.add_relationship(
                        source_entity_id=self._self_entity_id,
                        target_entity_id=member_entity.entity_id,
                        relationship_type=RelationshipType.TEAM_MEMBER,
                        deal_id=deal_id
                    )
                
                # Team member → Client (they worked together)
                self.graph.add_relationship(
                    source_entity_id=member_entity.entity_id,
                    target_entity_id=client_entity.entity_id,
                    relationship_type=RelationshipType.JOB_COMPLETED,
                    deal_id=deal_id
                )
        
        # 6. Store deal
        self._deals[deal_id] = {
            "deal_id": deal_id,
            "client_entity_id": client_entity.entity_id,
            "company_entity_id": company_entity.entity_id if company_entity else None,
            "referrer_entity_id": referrer_entity.entity_id if referrer_entity else None,
            "team_entity_ids": [e.entity_id for e in team_entities],
            "deal_value": deal_value,
            "service_type": service_type,
            "status": status,
            "recorded_at": _now()
        }
        
        # 7. Detect new intro opportunities (v2.0: AI-enhanced)
        new_intros = self._detect_intro_opportunities(client_entity)
        
        # 8. v2.0: Contribute successful deal pattern to MetaHive
        if METAHIVE_AVAILABLE and status == "completed" and deal_value > 0:
            import asyncio
            try:
                asyncio.create_task(contribute_to_hive(
                    username="aigentsy",
                    pattern_type="deal_completion",
                    context={
                        "industry": client_industry,
                        "service_type": service_type,
                        "had_referrer": referrer is not None,
                        "had_team": len(team_entities) > 0
                    },
                    action={"deal_flow": "standard"},
                    outcome={
                        "roas": deal_value / max(100, deal_value * 0.1),  # Estimate
                        "revenue_usd": deal_value,
                        "quality_score": 0.8
                    }
                ))
            except:
                pass
        
        return {
            "ok": True,
            "deal_id": deal_id,
            "client_entity_id": client_entity.entity_id,
            "relationships_created": 2 + len(team_entities) + (2 if referrer else 0),
            "new_intro_opportunities": len(new_intros),
            "intro_opportunities": [i.to_dict() for i in new_intros]
        }
    
    def _detect_intro_opportunities(self, new_client: Entity) -> List[IntroOpportunity]:
        """
        Detect warm intro opportunities through new client
        
        Logic: New client may know people who need our services
        
        v2.0: Uses AI Family Brain for predictions and message generation
        """
        opportunities = []
        
        if not self._self_entity_id:
            return opportunities
        
        # Get new client's other relationships (who else do they know?)
        client_connections = self.graph.get_relationships(new_client.entity_id, "outgoing")
        
        for rel in client_connections:
            target = self.graph.get_entity(rel.target_entity_id)
            if not target:
                continue
            
            # Skip if target is self or already a client
            if target.entity_id == self._self_entity_id:
                continue
            
            if "client" in target.tags:
                continue  # Already a client
            
            # Check if we have existing relationship with target
            existing_strength = self.graph.get_connection_strength(
                self._self_entity_id,
                target.entity_id
            )
            
            if existing_strength > 0.5:
                continue  # Already well connected
            
            # Calculate path strength
            # Self → New Client → Target
            self_to_client = self.graph.get_connection_strength(
                self._self_entity_id,
                new_client.entity_id
            )
            client_to_target = rel.current_strength
            
            path_strength = self_to_client * client_to_target
            
            if path_strength >= 0.2:  # Minimum threshold
                # v2.0: AI-enhanced predictions
                predicted_need, ai_model, ai_task_id = self._predict_need_ai(target)
                suggested_message = self._generate_intro_message_ai(new_client, target, predicted_need)
                
                # Create intro opportunity
                intro = IntroOpportunity(
                    opportunity_id=_generate_id("intro"),
                    source_entity_id=self._self_entity_id,
                    connector_entity_id=new_client.entity_id,
                    target_entity_id=target.entity_id,
                    source_to_connector=self.graph._find_relationship(
                        self._self_entity_id,
                        new_client.entity_id,
                        RelationshipType.JOB_COMPLETED
                    ) or self.graph._find_relationship(
                        self._self_entity_id,
                        new_client.entity_id,
                        RelationshipType.REPEAT_CLIENT
                    ),
                    connector_to_target=rel,
                    path_strength=path_strength,
                    confidence=min(0.9, path_strength + 0.2),
                    predicted_need=predicted_need,
                    estimated_value=self._estimate_intro_value(target),
                    suggested_message=suggested_message,
                    urgency="medium",
                    ai_model_used=ai_model,
                    ai_task_id=ai_task_id
                )
                
                opportunities.append(intro)
                self._intro_opportunities[intro.opportunity_id] = intro
        
        return opportunities
    
    def _predict_need_ai(self, entity: Entity) -> Tuple[str, str, str]:
        """
        v2.0: Use AI Family Brain to predict entity's needs
        
        Returns: (predicted_need, ai_model_used, task_id)
        """
        if not AI_FAMILY_AVAILABLE:
            return self._predict_need(entity), "", ""
        
        import asyncio
        
        try:
            prompt = f"""Analyze this business contact and predict their most likely need:

Name: {entity.name}
Company Type: {entity.entity_type}
Industry: {entity.industry or 'Unknown'}
Domain: {entity.domain or 'Unknown'}

Based on typical needs in their industry, predict ONE specific service they might need.
Return ONLY the service type (e.g., "api_integration", "marketing_automation", "content_creation", "data_analysis").
"""
            
            # Run synchronously for now (could be made async)
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Can't await in sync context, use fallback
                return self._predict_need(entity), "", ""
            
            result = loop.run_until_complete(ai_execute(prompt, "consulting", 100, "speed"))
            
            if result.get("ok"):
                predicted = result.get("response", "").strip().lower()
                model = result.get("model", "")
                task_id = result.get("task_id", "")
                
                # Store for learning
                self._ai_tasks.append({
                    "task_id": task_id,
                    "type": "need_prediction",
                    "entity_id": entity.entity_id,
                    "prediction": predicted,
                    "model": model,
                    "timestamp": _now()
                })
                
                return predicted, model, task_id
        except:
            pass
        
        return self._predict_need(entity), "", ""
    
    def _predict_need(self, entity: Entity) -> Optional[str]:
        """Predict what the entity might need (fallback)"""
        # Simple heuristic based on industry
        industry_needs = {
            "saas": "product_development",
            "ecommerce": "marketing",
            "fintech": "compliance",
            "healthcare": "integration_work",
            "education": "content_creation",
        }
        
        if entity.industry:
            return industry_needs.get(entity.industry.lower(), "consulting")
        return "consulting"
    
    def _estimate_intro_value(self, entity: Entity) -> float:
        """Estimate value of intro opportunity"""
        # Base value + modifiers
        base = 2000
        
        if entity.entity_type == "company":
            base *= 2
        
        return base
    
    def _generate_intro_message_ai(self, connector: Entity, target: Entity, predicted_need: str) -> str:
        """
        v2.0: Use AI Family Brain to generate personalized intro message
        """
        if not AI_FAMILY_AVAILABLE:
            return self._generate_intro_message(connector, target)
        
        import asyncio
        
        try:
            prompt = f"""Write a brief, warm introduction request message.

Connector (person who can introduce us): {connector.name}
Target (person we want to meet): {target.name}
Target's Industry: {target.industry or 'Unknown'}
Predicted Need: {predicted_need}

Write a message to {connector.name} asking for an introduction to {target.name}.
Keep it:
1. Personal and warm (reference working together)
2. Specific about the value you can provide
3. Easy to say yes to
4. Under 100 words

Message:"""
            
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return self._generate_intro_message(connector, target)
            
            result = loop.run_until_complete(ai_content(prompt, 200))
            
            if result.get("ok"):
                message = result.get("response", "").strip()
                
                # Store for learning
                self._ai_tasks.append({
                    "task_id": result.get("task_id", ""),
                    "type": "intro_message",
                    "connector_id": connector.entity_id,
                    "target_id": target.entity_id,
                    "model": result.get("model", ""),
                    "timestamp": _now()
                })
                
                return message
        except:
            pass
        
        return self._generate_intro_message(connector, target)
    
    def _generate_intro_message(self, connector: Entity, target: Entity) -> str:
        """Generate suggested intro request message (fallback)"""
        return f"Hi {connector.name}, I really enjoyed working together! I noticed you're connected with {target.name}. Would you be open to making an introduction? I think I could help them with [specific value prop]."
    
    # ==================== QUERIES ====================
    
    def find_intro_opportunities(
        self,
        industry: str = None,
        min_path_strength: float = 0.2,
        limit: int = 10
    ) -> List[IntroOpportunity]:
        """Find warm intro opportunities"""
        opportunities = list(self._intro_opportunities.values())
        
        # Filter by industry
        if industry:
            opportunities = [
                o for o in opportunities
                if self.graph.get_entity(o.target_entity_id) and
                self.graph.get_entity(o.target_entity_id).industry == industry
            ]
        
        # Filter by strength
        opportunities = [o for o in opportunities if o.path_strength >= min_path_strength]
        
        # Filter by status
        opportunities = [o for o in opportunities if o.status == "pending"]
        
        # Sort by confidence and value
        opportunities.sort(key=lambda o: o.confidence * o.estimated_value, reverse=True)
        
        return opportunities[:limit]
    
    def get_network_stats(self) -> Dict[str, Any]:
        """Get network statistics"""
        if not self._self_entity_id:
            return {"error": "self_not_set"}
        
        relationships = self.graph.get_relationships(self._self_entity_id, "both")
        
        # Count by type
        by_type = defaultdict(int)
        for rel in relationships:
            by_type[rel.relationship_type.value] += 1
        
        # Total relationship strength
        total_strength = sum(rel.current_strength for rel in relationships)
        
        # v2.0: AI Family stats
        ai_stats = {}
        if AI_FAMILY_AVAILABLE:
            try:
                ai_stats = get_family_stats()
            except:
                pass
        
        return {
            "total_entities": len(self.graph._entities),
            "total_relationships": len(self.graph._relationships),
            "total_deals": len(self._deals),
            "total_deal_value": sum(d.get("deal_value", 0) for d in self._deals.values()),
            "direct_connections": len(relationships),
            "relationships_by_type": dict(by_type),
            "total_relationship_strength": round(total_strength, 2),
            "pending_intro_opportunities": len([
                o for o in self._intro_opportunities.values()
                if o.status == "pending"
            ]),
            "ai_family_available": AI_FAMILY_AVAILABLE,
            "ai_tasks_executed": len(self._ai_tasks),
            "ai_family_stats": ai_stats
        }
    
    def get_strongest_connections(self, limit: int = 10) -> List[Dict]:
        """Get strongest connections"""
        if not self._self_entity_id:
            return []
        
        relationships = self.graph.get_relationships(self._self_entity_id, "outgoing")
        relationships.sort(key=lambda r: r.current_strength, reverse=True)
        
        results = []
        for rel in relationships[:limit]:
            entity = self.graph.get_entity(rel.target_entity_id)
            if entity:
                results.append({
                    "entity": entity.to_dict(),
                    "relationship_type": rel.relationship_type.value,
                    "strength": round(rel.current_strength, 2),
                    "interactions": rel.interaction_count,
                    "deals": len(rel.deal_ids)
                })
        
        return results
    
    def request_intro(self, opportunity_id: str) -> Dict[str, Any]:
        """Mark intro opportunity as requested"""
        opp = self._intro_opportunities.get(opportunity_id)
        if not opp:
            return {"ok": False, "error": "opportunity_not_found"}
        
        opp.status = "requested"
        
        return {
            "ok": True,
            "opportunity_id": opportunity_id,
            "status": "requested",
            "suggested_message": opp.suggested_message,
            "ai_model_used": opp.ai_model_used
        }
    
    def record_intro_outcome(
        self,
        opportunity_id: str,
        success: bool,
        deal_value: float = None,
        notes: str = None
    ) -> Dict[str, Any]:
        """
        v2.0: Record intro outcome for AI Family learning
        """
        opp = self._intro_opportunities.get(opportunity_id)
        if not opp:
            return {"ok": False, "error": "opportunity_not_found"}
        
        opp.status = "completed" if success else "declined"
        
        outcome = {
            "opportunity_id": opportunity_id,
            "success": success,
            "deal_value": deal_value,
            "ai_model_used": opp.ai_model_used,
            "ai_task_id": opp.ai_task_id,
            "predicted_need": opp.predicted_need,
            "timestamp": _now()
        }
        self._intro_outcomes.append(outcome)
        
        # Record quality feedback to AI Family
        if AI_FAMILY_AVAILABLE and opp.ai_task_id:
            quality = 0.9 if success else 0.3
            record_quality(opp.ai_task_id, quality, deal_value)
        
        # Contribute to MetaHive if successful
        if METAHIVE_AVAILABLE and success and deal_value:
            import asyncio
            try:
                asyncio.create_task(contribute_to_hive(
                    username="aigentsy",
                    pattern_type="warm_intro",
                    context={
                        "path_strength": opp.path_strength,
                        "predicted_need": opp.predicted_need,
                        "target_industry": self.graph.get_entity(opp.target_entity_id).industry if self.graph.get_entity(opp.target_entity_id) else None
                    },
                    action={
                        "intro_flow": "warm",
                        "ai_model": opp.ai_model_used
                    },
                    outcome={
                        "roas": deal_value / 100,  # Cost estimate
                        "revenue_usd": deal_value,
                        "quality_score": 0.9
                    }
                ))
            except:
                pass
        
        return {"ok": True, "outcome": outcome}


# ============================================================
# SINGLETON
# ============================================================

_deal_graph: Optional[DealGraph] = None


def get_deal_graph() -> DealGraph:
    """Get singleton DealGraph instance"""
    global _deal_graph
    if _deal_graph is None:
        _deal_graph = DealGraph()
    return _deal_graph


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print("=" * 70)
    print("AUTONOMOUS DEAL GRAPH v2.0 - AI FAMILY BRAIN INTEGRATION")
    print("=" * 70)
    print(f"AI Family Available: {AI_FAMILY_AVAILABLE}")
    print(f"MetaHive Available: {METAHIVE_AVAILABLE}")
    print(f"Yield Memory Available: {YIELD_AVAILABLE}")
    
    graph = get_deal_graph()
    
    # 1. Set self
    print("\n1. Setting self entity...")
    graph.set_self("AiGentsy", "wade@aigentsy.com")
    
    # 2. Record first deal
    print("\n2. Recording first deal...")
    result = graph.record_deal(
        deal_id="deal_001",
        client_name="Alice Chen",
        client_email="alice@startup.com",
        client_company="TechStartup Inc",
        client_industry="saas",
        deal_value=5000,
        service_type="api_integration"
    )
    print(f"   Relationships created: {result['relationships_created']}")
    
    # 3. Alice refers Bob
    print("\n3. Recording second deal (with referral)...")
    result = graph.record_deal(
        deal_id="deal_002",
        client_name="Bob Smith",
        client_email="bob@ecommerce.com",
        client_company="ShopCo",
        client_industry="ecommerce",
        deal_value=3000,
        service_type="marketing",
        referrer={"name": "Alice Chen", "email": "alice@startup.com"}
    )
    print(f"   Relationships created: {result['relationships_created']}")
    print(f"   New intro opportunities: {result['new_intro_opportunities']}")
    
    # 4. Record team deal
    print("\n4. Recording team deal...")
    result = graph.record_deal(
        deal_id="deal_003",
        client_name="Charlie Wilson",
        client_email="charlie@fintech.io",
        client_company="FinTech Pro",
        client_industry="fintech",
        deal_value=10000,
        service_type="software_development",
        team_members=[
            {"name": "Designer Dan", "email": "dan@design.com"},
            {"name": "Dev Diana", "email": "diana@dev.com"}
        ]
    )
    print(f"   Relationships created: {result['relationships_created']}")
    
    # 5. Get network stats
    print("\n5. Network stats...")
    stats = graph.get_network_stats()
    print(f"   Total entities: {stats['total_entities']}")
    print(f"   Total relationships: {stats['total_relationships']}")
    print(f"   Total deal value: ${stats['total_deal_value']:,.0f}")
    print(f"   Pending intros: {stats['pending_intro_opportunities']}")
    print(f"   AI Family: {stats['ai_family_available']}")
    print(f"   AI Tasks: {stats['ai_tasks_executed']}")
    
    # 6. Get strongest connections
    print("\n6. Strongest connections...")
    strongest = graph.get_strongest_connections(5)
    for conn in strongest:
        print(f"   - {conn['entity']['name']}: {conn['strength']} strength ({conn['relationship_type']})")
    
    # 7. Find intro opportunities
    print("\n7. Intro opportunities...")
    intros = graph.find_intro_opportunities()
    for intro in intros[:3]:
        connector = graph.graph.get_entity(intro.connector_entity_id)
        target = graph.graph.get_entity(intro.target_entity_id)
        print(f"   - Via {connector.name if connector else 'Unknown'} → {target.name if target else 'Unknown'}")
        print(f"     Path strength: {intro.path_strength:.2f}, Value: ${intro.estimated_value:,.0f}")
        if intro.ai_model_used:
            print(f"     AI Model: {intro.ai_model_used}")
    
    print("\n" + "=" * 70)
    print("✅ Deal Graph v2.0 test complete!")
    print("=" * 70)
