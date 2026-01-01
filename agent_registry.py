"""
AGENT REGISTRY - Public Identity System for AI Agents
======================================================

This provides the identity layer for the AIGx Protocol.
Any AI agent (internal or external) can register and build reputation.

FEATURES:
- Unique agent identifiers
- Capability declarations
- Portable reputation that travels with agents
- Verification of agent authenticity
- Public API for querying agent info

ANALOGY:
- Like a professional license + LinkedIn profile for AI agents
- Any platform can verify an agent's credentials
- Reputation is earned and portable
"""

import hashlib
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from uuid import uuid4


# ============================================================
# AGENT TYPES & CAPABILITIES
# ============================================================

class AgentType(str, Enum):
    """Types of AI agents"""
    CLAUDE = "claude"
    GPT = "gpt"
    GEMINI = "gemini"
    LLAMA = "llama"
    MISTRAL = "mistral"
    STABLE_DIFFUSION = "stable_diffusion"
    MIDJOURNEY = "midjourney"
    ELEVENLABS = "elevenlabs"
    PERPLEXITY = "perplexity"
    CUSTOM = "custom"
    HYBRID = "hybrid"  # Multi-model agent


class Capability(str, Enum):
    """Agent capabilities"""
    # Code
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    DEBUGGING = "debugging"
    ARCHITECTURE = "architecture"
    
    # Content
    CONTENT_WRITING = "content_writing"
    COPYWRITING = "copywriting"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"
    
    # Creative
    IMAGE_GENERATION = "image_generation"
    VIDEO_GENERATION = "video_generation"
    AUDIO_GENERATION = "audio_generation"
    MUSIC_GENERATION = "music_generation"
    
    # Analysis
    DATA_ANALYSIS = "data_analysis"
    RESEARCH = "research"
    MARKET_ANALYSIS = "market_analysis"
    FINANCIAL_ANALYSIS = "financial_analysis"
    
    # Interaction
    CONVERSATION = "conversation"
    CUSTOMER_SERVICE = "customer_service"
    SALES = "sales"
    NEGOTIATION = "negotiation"
    
    # Specialized
    LEGAL_ANALYSIS = "legal_analysis"
    MEDICAL_ANALYSIS = "medical_analysis"
    SCIENTIFIC_RESEARCH = "scientific_research"


class ReputationTier(str, Enum):
    """Reputation tiers"""
    UNVERIFIED = "unverified"  # New agent, no track record
    BRONZE = "bronze"  # Score 0-49
    SILVER = "silver"  # Score 50-69
    GOLD = "gold"  # Score 70-84
    PLATINUM = "platinum"  # Score 85-94
    DIAMOND = "diamond"  # Score 95-100


TIER_THRESHOLDS = {
    ReputationTier.UNVERIFIED: (None, 0),
    ReputationTier.BRONZE: (0, 49),
    ReputationTier.SILVER: (50, 69),
    ReputationTier.GOLD: (70, 84),
    ReputationTier.PLATINUM: (85, 94),
    ReputationTier.DIAMOND: (95, 100)
}

TIER_BADGES = {
    ReputationTier.UNVERIFIED: "⚪",
    ReputationTier.BRONZE: "🥉",
    ReputationTier.SILVER: "🥈",
    ReputationTier.GOLD: "🥇",
    ReputationTier.PLATINUM: "💎",
    ReputationTier.DIAMOND: "💠"
}


# ============================================================
# AGENT DATA STRUCTURES
# ============================================================

@dataclass
class AgentReputation:
    """Agent's reputation metrics"""
    score: int = 0  # 0-100
    tier: ReputationTier = ReputationTier.UNVERIFIED
    jobs_completed: int = 0
    jobs_failed: int = 0
    total_earned_aigx: float = 0.0
    total_paid_aigx: float = 0.0
    on_time_rate: float = 0.0
    dispute_rate: float = 0.0
    avg_rating: float = 0.0
    rating_count: int = 0
    first_job_at: Optional[str] = None
    last_job_at: Optional[str] = None
    streak_days: int = 0
    badges: List[str] = field(default_factory=list)
    
    def update_tier(self):
        """Update tier based on score"""
        for tier, (min_score, max_score) in TIER_THRESHOLDS.items():
            if min_score is None:
                if self.jobs_completed == 0:
                    self.tier = tier
                    return
            elif min_score <= self.score <= max_score:
                self.tier = tier
                return
    
    def calculate_score(self):
        """Calculate reputation score from metrics"""
        if self.jobs_completed == 0:
            self.score = 0
            self.tier = ReputationTier.UNVERIFIED
            return
        
        # Weighted components
        completion_rate = (self.jobs_completed / (self.jobs_completed + self.jobs_failed)) if (self.jobs_completed + self.jobs_failed) > 0 else 0
        
        score = (
            (completion_rate * 30) +  # 30% completion rate
            (self.on_time_rate * 25) +  # 25% on-time delivery
            ((1 - self.dispute_rate) * 20) +  # 20% no disputes
            ((self.avg_rating / 5.0) * 15 if self.avg_rating > 0 else 15) +  # 15% ratings
            (min(self.jobs_completed / 100, 1.0) * 10)  # 10% experience
        )
        
        self.score = int(min(100, max(0, score)))
        self.update_tier()


@dataclass
class RegisteredAgent:
    """A registered agent in the protocol"""
    agent_id: str
    agent_type: AgentType
    name: str
    description: str
    capabilities: List[Capability]
    owner_id: Optional[str]  # Platform/user that owns this agent
    api_endpoint: Optional[str]  # Where to reach this agent
    public_key: Optional[str]  # For verification
    reputation: AgentReputation
    stake_aigx: float = 0.0
    is_verified: bool = False
    is_active: bool = True
    registered_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_active_at: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    
    def to_public_dict(self) -> Dict:
        """Return public-safe representation"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type.value,
            "name": self.name,
            "description": self.description,
            "capabilities": [c.value for c in self.capabilities],
            "reputation": {
                "score": self.reputation.score,
                "tier": self.reputation.tier.value,
                "badge": TIER_BADGES[self.reputation.tier],
                "jobs_completed": self.reputation.jobs_completed,
                "on_time_rate": round(self.reputation.on_time_rate, 2),
                "avg_rating": round(self.reputation.avg_rating, 1),
                "rating_count": self.reputation.rating_count
            },
            "stake_aigx": self.stake_aigx,
            "is_verified": self.is_verified,
            "is_active": self.is_active,
            "registered_at": self.registered_at,
            "last_active_at": self.last_active_at
        }
    
    def to_full_dict(self) -> Dict:
        """Return full representation (for owner only)"""
        data = self.to_public_dict()
        data["owner_id"] = self.owner_id
        data["api_endpoint"] = self.api_endpoint
        data["metadata"] = self.metadata
        data["reputation_details"] = asdict(self.reputation)
        return data


# ============================================================
# AGENT REGISTRY
# ============================================================

class AgentRegistry:
    """
    The central registry for all AI agents
    
    This is like a combination of:
    - Domain name registry (unique identifiers)
    - Professional licensing board (capability verification)
    - Credit bureau (reputation tracking)
    """
    
    def __init__(self):
        self._agents: Dict[str, RegisteredAgent] = {}
        self._agents_by_owner: Dict[str, List[str]] = {}
        self._agents_by_capability: Dict[Capability, Set[str]] = {cap: set() for cap in Capability}
        self._agents_by_type: Dict[AgentType, Set[str]] = {t: set() for t in AgentType}
        self._reserved_names: Set[str] = set()
    
    def register(
        self,
        agent_type: str,
        name: str,
        description: str,
        capabilities: List[str],
        owner_id: str = None,
        api_endpoint: str = None,
        public_key: str = None,
        initial_stake: float = 0.0,
        metadata: Dict = None
    ) -> Dict[str, Any]:
        """
        Register a new agent in the protocol
        
        Args:
            agent_type: Type of AI (claude, gpt, custom, etc.)
            name: Display name
            description: What this agent does
            capabilities: List of capability strings
            owner_id: Who owns/operates this agent
            api_endpoint: Where to reach this agent
            public_key: For message verification
            initial_stake: AIGx to stake on registration
            metadata: Additional info
        """
        # Validate agent type
        try:
            agent_type_enum = AgentType(agent_type.lower())
        except ValueError:
            agent_type_enum = AgentType.CUSTOM
        
        # Validate capabilities
        capability_enums = []
        for cap in capabilities:
            try:
                capability_enums.append(Capability(cap.lower()))
            except ValueError:
                pass  # Skip invalid capabilities
        
        if not capability_enums:
            return {"ok": False, "error": "at_least_one_valid_capability_required"}
        
        # Check name availability
        normalized_name = name.lower().replace(" ", "_")
        if normalized_name in self._reserved_names:
            return {"ok": False, "error": "name_already_taken"}
        
        # Generate agent ID
        agent_id = f"agent_{uuid4().hex[:16]}"
        
        # Create agent
        agent = RegisteredAgent(
            agent_id=agent_id,
            agent_type=agent_type_enum,
            name=name,
            description=description,
            capabilities=capability_enums,
            owner_id=owner_id,
            api_endpoint=api_endpoint,
            public_key=public_key,
            reputation=AgentReputation(),
            stake_aigx=initial_stake,
            is_verified=False,
            is_active=True,
            metadata=metadata or {}
        )
        
        # Store
        self._agents[agent_id] = agent
        self._reserved_names.add(normalized_name)
        
        # Index by owner
        if owner_id:
            if owner_id not in self._agents_by_owner:
                self._agents_by_owner[owner_id] = []
            self._agents_by_owner[owner_id].append(agent_id)
        
        # Index by capability
        for cap in capability_enums:
            self._agents_by_capability[cap].add(agent_id)
        
        # Index by type
        self._agents_by_type[agent_type_enum].add(agent_id)
        
        return {
            "ok": True,
            "agent_id": agent_id,
            "name": name,
            "agent_type": agent_type_enum.value,
            "capabilities": [c.value for c in capability_enums],
            "stake_required_for_verification": 100.0,  # Need 100 AIGx stake to verify
            "message": "Agent registered. Stake 100+ AIGx and complete 5 jobs to verify."
        }
    
    def get_agent(self, agent_id: str) -> Optional[RegisteredAgent]:
        """Get agent by ID"""
        return self._agents.get(agent_id)
    
    def get_agent_public(self, agent_id: str) -> Dict:
        """Get public agent info"""
        agent = self._agents.get(agent_id)
        if not agent:
            return {"ok": False, "error": "agent_not_found"}
        return {"ok": True, "agent": agent.to_public_dict()}
    
    def search_agents(
        self,
        capability: str = None,
        agent_type: str = None,
        min_reputation: int = 0,
        verified_only: bool = False,
        active_only: bool = True,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Search for agents by criteria
        """
        # Start with all agents
        candidates = set(self._agents.keys())
        
        # Filter by capability
        if capability:
            try:
                cap_enum = Capability(capability.lower())
                candidates &= self._agents_by_capability.get(cap_enum, set())
            except ValueError:
                pass
        
        # Filter by type
        if agent_type:
            try:
                type_enum = AgentType(agent_type.lower())
                candidates &= self._agents_by_type.get(type_enum, set())
            except ValueError:
                pass
        
        # Apply other filters
        results = []
        for agent_id in candidates:
            agent = self._agents[agent_id]
            
            if active_only and not agent.is_active:
                continue
            
            if verified_only and not agent.is_verified:
                continue
            
            if agent.reputation.score < min_reputation:
                continue
            
            results.append(agent.to_public_dict())
        
        # Sort by reputation score
        results.sort(key=lambda x: x["reputation"]["score"], reverse=True)
        
        return {
            "ok": True,
            "count": len(results[:limit]),
            "total_matching": len(results),
            "agents": results[:limit]
        }
    
    def update_reputation(
        self,
        agent_id: str,
        job_completed: bool,
        on_time: bool,
        rating: float = None,
        aigx_earned: float = 0.0,
        disputed: bool = False
    ) -> Dict[str, Any]:
        """
        Update agent's reputation after a job
        """
        agent = self._agents.get(agent_id)
        if not agent:
            return {"ok": False, "error": "agent_not_found"}
        
        rep = agent.reputation
        now = datetime.now(timezone.utc).isoformat()
        
        # Update job counts
        if job_completed:
            rep.jobs_completed += 1
            rep.last_job_at = now
            if not rep.first_job_at:
                rep.first_job_at = now
        else:
            rep.jobs_failed += 1
        
        # Update on-time rate (rolling average)
        total_jobs = rep.jobs_completed + rep.jobs_failed
        if job_completed:
            rep.on_time_rate = ((rep.on_time_rate * (rep.jobs_completed - 1)) + (1.0 if on_time else 0.0)) / rep.jobs_completed if rep.jobs_completed > 0 else 0
        
        # Update dispute rate
        if disputed:
            rep.dispute_rate = ((rep.dispute_rate * (total_jobs - 1)) + 1.0) / total_jobs
        
        # Update rating
        if rating is not None and 1.0 <= rating <= 5.0:
            if rep.rating_count == 0:
                rep.avg_rating = rating
            else:
                rep.avg_rating = ((rep.avg_rating * rep.rating_count) + rating) / (rep.rating_count + 1)
            rep.rating_count += 1
        
        # Update earnings
        rep.total_earned_aigx += aigx_earned
        
        # Recalculate score and tier
        rep.calculate_score()
        
        # Check for verification eligibility
        if not agent.is_verified and rep.jobs_completed >= 5 and agent.stake_aigx >= 100:
            agent.is_verified = True
            rep.badges.append("verified")
        
        # Update active timestamp
        agent.last_active_at = now
        
        return {
            "ok": True,
            "agent_id": agent_id,
            "new_score": rep.score,
            "tier": rep.tier.value,
            "badge": TIER_BADGES[rep.tier],
            "jobs_completed": rep.jobs_completed,
            "is_verified": agent.is_verified
        }
    
    def update_stake(self, agent_id: str, new_stake: float) -> Dict:
        """Update agent's stake amount"""
        agent = self._agents.get(agent_id)
        if not agent:
            return {"ok": False, "error": "agent_not_found"}
        
        old_stake = agent.stake_aigx
        agent.stake_aigx = new_stake
        
        # Check verification eligibility
        if not agent.is_verified and agent.reputation.jobs_completed >= 5 and new_stake >= 100:
            agent.is_verified = True
            agent.reputation.badges.append("verified")
        
        return {
            "ok": True,
            "agent_id": agent_id,
            "old_stake": old_stake,
            "new_stake": new_stake,
            "is_verified": agent.is_verified
        }
    
    def deactivate_agent(self, agent_id: str, owner_id: str) -> Dict:
        """Deactivate an agent (owner only)"""
        agent = self._agents.get(agent_id)
        if not agent:
            return {"ok": False, "error": "agent_not_found"}
        
        if agent.owner_id != owner_id:
            return {"ok": False, "error": "not_owner"}
        
        agent.is_active = False
        
        return {"ok": True, "agent_id": agent_id, "status": "deactivated"}
    
    def get_owner_agents(self, owner_id: str) -> Dict:
        """Get all agents owned by a user"""
        agent_ids = self._agents_by_owner.get(owner_id, [])
        agents = [self._agents[aid].to_full_dict() for aid in agent_ids if aid in self._agents]
        
        return {
            "ok": True,
            "owner_id": owner_id,
            "agent_count": len(agents),
            "agents": agents
        }
    
    def get_leaderboard(self, limit: int = 20) -> Dict:
        """Get top agents by reputation"""
        agents = list(self._agents.values())
        agents.sort(key=lambda a: (a.reputation.score, a.reputation.jobs_completed), reverse=True)
        
        leaderboard = []
        for rank, agent in enumerate(agents[:limit], 1):
            leaderboard.append({
                "rank": rank,
                "agent_id": agent.agent_id,
                "name": agent.name,
                "agent_type": agent.agent_type.value,
                "score": agent.reputation.score,
                "tier": agent.reputation.tier.value,
                "badge": TIER_BADGES[agent.reputation.tier],
                "jobs_completed": agent.reputation.jobs_completed,
                "total_earned": round(agent.reputation.total_earned_aigx, 2)
            })
        
        return {
            "ok": True,
            "leaderboard": leaderboard,
            "total_agents": len(self._agents)
        }
    
    def get_stats(self) -> Dict:
        """Get registry statistics"""
        active_agents = len([a for a in self._agents.values() if a.is_active])
        verified_agents = len([a for a in self._agents.values() if a.is_verified])
        
        # Capability distribution
        capability_counts = {
            cap.value: len(agents) 
            for cap, agents in self._agents_by_capability.items()
        }
        
        # Type distribution
        type_counts = {
            t.value: len(agents)
            for t, agents in self._agents_by_type.items()
        }
        
        # Tier distribution
        tier_counts = {tier.value: 0 for tier in ReputationTier}
        for agent in self._agents.values():
            tier_counts[agent.reputation.tier.value] += 1
        
        return {
            "ok": True,
            "total_agents": len(self._agents),
            "active_agents": active_agents,
            "verified_agents": verified_agents,
            "capabilities": capability_counts,
            "agent_types": type_counts,
            "reputation_tiers": tier_counts
        }
    
    def verify_agent_signature(
        self,
        agent_id: str,
        message: str,
        signature: str
    ) -> Dict:
        """
        Verify a message was signed by an agent
        (Placeholder - would use actual cryptography in production)
        """
        agent = self._agents.get(agent_id)
        if not agent:
            return {"ok": False, "verified": False, "error": "agent_not_found"}
        
        if not agent.public_key:
            return {"ok": False, "verified": False, "error": "agent_has_no_public_key"}
        
        # In production, verify signature with public key
        # For now, simple hash check
        expected = hashlib.sha256(f"{message}{agent.public_key}".encode()).hexdigest()[:32]
        
        return {
            "ok": True,
            "verified": signature == expected,
            "agent_id": agent_id
        }


# ============================================================
# SINGLETON
# ============================================================

_registry_instance: Optional[AgentRegistry] = None


def get_registry() -> AgentRegistry:
    """Get singleton registry instance"""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = AgentRegistry()
    return _registry_instance


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================

def register_agent(
    agent_type: str,
    name: str,
    description: str,
    capabilities: List[str],
    owner_id: str = None
) -> Dict:
    """Register a new agent"""
    return get_registry().register(
        agent_type=agent_type,
        name=name,
        description=description,
        capabilities=capabilities,
        owner_id=owner_id
    )


def lookup_agent(agent_id: str) -> Dict:
    """Look up agent by ID"""
    return get_registry().get_agent_public(agent_id)


def find_agents(capability: str = None, min_reputation: int = 0) -> Dict:
    """Find agents by criteria"""
    return get_registry().search_agents(
        capability=capability,
        min_reputation=min_reputation
    )


def agent_leaderboard() -> Dict:
    """Get agent leaderboard"""
    return get_registry().get_leaderboard()


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print("=" * 70)
    print("AGENT REGISTRY - Public Identity System for AI Agents")
    print("=" * 70)
    
    registry = get_registry()
    
    print("\n1. Register Claude agent...")
    result = registry.register(
        agent_type="claude",
        name="Claude Code Master",
        description="Expert code generation and review agent",
        capabilities=["code_generation", "code_review", "debugging"],
        owner_id="aigentsy_platform"
    )
    print(f"   Result: {result}")
    claude_id = result["agent_id"]
    
    print("\n2. Register GPT agent...")
    result = registry.register(
        agent_type="gpt",
        name="GPT Content Writer",
        description="Content writing and copywriting specialist",
        capabilities=["content_writing", "copywriting", "translation"],
        owner_id="external_platform_xyz"
    )
    print(f"   Result: {result}")
    gpt_id = result["agent_id"]
    
    print("\n3. Simulate jobs and update reputation...")
    for i in range(7):
        registry.update_reputation(
            agent_id=claude_id,
            job_completed=True,
            on_time=i < 6,  # 6 out of 7 on time
            rating=4.5 if i % 2 == 0 else 5.0,
            aigx_earned=50.0
        )
    
    print("\n4. Update stake to verify agent...")
    registry.update_stake(claude_id, 150.0)
    
    print("\n5. Look up Claude agent...")
    agent_info = registry.get_agent_public(claude_id)
    print(f"   Agent: {json.dumps(agent_info, indent=2)}")
    
    print("\n6. Search for code agents...")
    search = registry.search_agents(capability="code_generation")
    print(f"   Found: {search['count']} agents")
    
    print("\n7. Leaderboard...")
    leaderboard = registry.get_leaderboard(5)
    for entry in leaderboard["leaderboard"]:
        print(f"   #{entry['rank']}: {entry['name']} - Score: {entry['score']} {entry['badge']}")
    
    print("\n8. Registry stats...")
    stats = registry.get_stats()
    print(f"   Total agents: {stats['total_agents']}")
    print(f"   Verified: {stats['verified_agents']}")
    
    print("\n" + "=" * 70)
    print("Registry test complete!")
    print("=" * 70)
