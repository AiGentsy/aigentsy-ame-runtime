"""
PROTOCOL GATEWAY - API for External Agents
==========================================

This is the public API surface that external AI agents use to:
- Register in the protocol
- Settle transactions
- Build reputation
- Participate in the AI economy

This is what transforms AiGentsy from a product into infrastructure.
Any AI agent can connect - ours or anyone else's.
"""

import hashlib
import hmac
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from uuid import uuid4


# Import protocol components
from aigx_protocol import (
    get_protocol,
    AIGxProtocol,
    PROTOCOL_VERSION,
    PROTOCOL_FEE_PERCENT
)

from agent_registry import (
    get_registry,
    AgentRegistry,
    Capability,
    AgentType,
    ReputationTier,
    TIER_BADGES
)


# ============================================================
# API AUTHENTICATION
# ============================================================

class APIKeyManager:
    """Manages API keys for protocol access"""
    
    def __init__(self):
        self._keys: Dict[str, Dict] = {}
        self._agent_keys: Dict[str, str] = {}
        self._rate_limits: Dict[str, List[float]] = {}
        self._rate_limit_window = 60
        self._rate_limit_max = 100
    
    def generate_key(self, agent_id: str, permissions: List[str] = None) -> Dict:
        """Generate API key for an agent"""
        key_data = f"{agent_id}:{uuid4().hex}:{time.time()}"
        api_key = f"aigx_{hashlib.sha256(key_data.encode()).hexdigest()[:32]}"
        
        self._keys[api_key] = {
            "agent_id": agent_id,
            "permissions": permissions or ["read", "settle", "stake"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_used": None,
            "request_count": 0
        }
        self._agent_keys[agent_id] = api_key
        
        return {
            "ok": True,
            "api_key": api_key,
            "agent_id": agent_id,
            "permissions": self._keys[api_key]["permissions"]
        }
    
    def validate_key(self, api_key: str) -> Dict:
        """Validate an API key"""
        if api_key not in self._keys:
            return {"valid": False, "error": "invalid_key"}
        
        key_data = self._keys[api_key]
        
        if not self._check_rate_limit(api_key):
            return {"valid": False, "error": "rate_limit_exceeded"}
        
        key_data["last_used"] = datetime.now(timezone.utc).isoformat()
        key_data["request_count"] += 1
        
        return {
            "valid": True,
            "agent_id": key_data["agent_id"],
            "permissions": key_data["permissions"]
        }
    
    def _check_rate_limit(self, api_key: str) -> bool:
        """Check if request is within rate limit"""
        now = time.time()
        
        if api_key not in self._rate_limits:
            self._rate_limits[api_key] = []
        
        self._rate_limits[api_key] = [
            ts for ts in self._rate_limits[api_key]
            if now - ts < self._rate_limit_window
        ]
        
        if len(self._rate_limits[api_key]) >= self._rate_limit_max:
            return False
        
        self._rate_limits[api_key].append(now)
        return True


# ============================================================
# PROTOCOL GATEWAY
# ============================================================

class ProtocolGateway:
    """
    The public API gateway for the AIGx Protocol
    """
    
    def __init__(self):
        self.protocol = get_protocol()
        self.registry = get_registry()
        self.api_keys = APIKeyManager()
    
    # ==================== REGISTRATION ====================
    
    def register_agent(
        self,
        agent_type: str,
        name: str,
        description: str,
        capabilities: List[str],
        owner_id: str = None,
        api_endpoint: str = None,
        initial_aigx: float = 0.0
    ) -> Dict[str, Any]:
        """Register a new agent in the protocol"""
        
        reg_result = self.registry.register(
            agent_type=agent_type,
            name=name,
            description=description,
            capabilities=capabilities,
            owner_id=owner_id,
            api_endpoint=api_endpoint
        )
        
        if not reg_result.get("ok"):
            return reg_result
        
        agent_id = reg_result["agent_id"]
        key_result = self.api_keys.generate_key(agent_id)
        
        if initial_aigx > 0:
            self.protocol.credit_balance(agent_id, initial_aigx, "registration_bonus")
        
        return {
            "ok": True,
            "agent_id": agent_id,
            "api_key": key_result["api_key"],
            "name": name,
            "agent_type": agent_type,
            "capabilities": reg_result["capabilities"],
            "initial_balance": initial_aigx,
            "protocol_version": PROTOCOL_VERSION,
            "next_steps": [
                "Store your API key securely",
                "Stake 100+ AIGx to become verified",
                "Complete 5 jobs to build reputation",
                "Use /protocol/settle to receive payments"
            ]
        }
    
    # ==================== SETTLEMENT ====================
    
    def settle(
        self,
        api_key: str,
        to_agent: str,
        amount_aigx: float,
        work_hash: str,
        proof_of_work: Dict = None,
        metadata: Dict = None
    ) -> Dict[str, Any]:
        """Settle a payment between agents"""
        
        auth = self.api_keys.validate_key(api_key)
        if not auth["valid"]:
            return {"ok": False, "error": auth["error"]}
        
        from_agent = auth["agent_id"]
        
        if "settle" not in auth["permissions"]:
            return {"ok": False, "error": "permission_denied"}
        
        recipient = self.registry.get_agent(to_agent)
        if not recipient:
            return {"ok": False, "error": "recipient_agent_not_found"}
        
        result = self.protocol.settle(
            from_agent=from_agent,
            to_agent=to_agent,
            amount=amount_aigx,
            work_hash=work_hash,
            proof_of_work=proof_of_work,
            auto_confirm=True
        )
        
        if result.get("ok"):
            self.registry.update_reputation(
                agent_id=to_agent,
                job_completed=True,
                on_time=True,
                aigx_earned=result.get("net_amount", 0)
            )
        
        return result
    
    # ==================== STAKING ====================
    
    def stake(self, api_key: str, amount_aigx: float) -> Dict[str, Any]:
        """Stake AIGx in the protocol"""
        
        auth = self.api_keys.validate_key(api_key)
        if not auth["valid"]:
            return {"ok": False, "error": auth["error"]}
        
        agent_id = auth["agent_id"]
        
        result = self.protocol.stake(agent_id, amount_aigx)
        
        if result.get("ok"):
            self.registry.update_stake(agent_id, result.get("total_stake", 0))
        
        return result
    
    def unstake(self, api_key: str, amount_aigx: float) -> Dict[str, Any]:
        """Unstake AIGx from the protocol"""
        
        auth = self.api_keys.validate_key(api_key)
        if not auth["valid"]:
            return {"ok": False, "error": auth["error"]}
        
        agent_id = auth["agent_id"]
        result = self.protocol.unstake(agent_id, amount_aigx)
        
        if result.get("ok"):
            self.registry.update_stake(agent_id, result.get("remaining_stake", 0))
        
        return result
    
    # ==================== BALANCE ====================
    
    def get_balance(self, api_key: str) -> Dict[str, Any]:
        """Get AIGx balance"""
        
        auth = self.api_keys.validate_key(api_key)
        if not auth["valid"]:
            return {"ok": False, "error": auth["error"]}
        
        agent_id = auth["agent_id"]
        balance = self.protocol.get_balance(agent_id)
        stake_info = self.protocol.get_stake_info(agent_id)
        
        return {
            "ok": True,
            "agent_id": agent_id,
            "balance": balance,
            "staked": stake_info.get("staked", 0),
            "total": balance + stake_info.get("staked", 0)
        }
    
    # ==================== AGENT LOOKUP ====================
    
    def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """Get public agent info"""
        return self.registry.get_agent_public(agent_id)
    
    def search_agents(
        self,
        capability: str = None,
        agent_type: str = None,
        min_reputation: int = 0,
        verified_only: bool = False,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Search for agents"""
        return self.registry.search_agents(
            capability=capability,
            agent_type=agent_type,
            min_reputation=min_reputation,
            verified_only=verified_only,
            limit=limit
        )
    
    def get_leaderboard(self, limit: int = 20) -> Dict[str, Any]:
        """Get agent leaderboard"""
        return self.registry.get_leaderboard(limit)
    
    # ==================== TRANSACTIONS ====================
    
    def get_transaction(self, tx_id: str) -> Dict[str, Any]:
        """Get transaction details"""
        return self.protocol.get_transaction(tx_id)
    
    def verify_transaction(self, tx_id: str) -> Dict[str, Any]:
        """Verify a transaction exists and is valid"""
        return self.protocol.verify_transaction(tx_id)
    
    def get_agent_history(self, api_key: str, limit: int = 50) -> Dict[str, Any]:
        """Get agent's transaction history"""
        
        auth = self.api_keys.validate_key(api_key)
        if not auth["valid"]:
            return {"ok": False, "error": auth["error"]}
        
        return self.protocol.get_agent_history(auth["agent_id"], limit)
    
    # ==================== PROTOCOL INFO ====================
    
    def get_protocol_info(self) -> Dict[str, Any]:
        """Get protocol information"""
        return {
            "ok": True,
            "protocol": "AIGx",
            "version": PROTOCOL_VERSION,
            "fee_rate": f"{PROTOCOL_FEE_PERCENT * 100}%",
            "description": "Settlement layer for AI-to-AI transactions",
            "features": [
                "Immutable transaction ledger",
                "Agent reputation system",
                "Staking with yield",
                "Cross-platform settlement"
            ],
            "stats": self.protocol.get_protocol_stats()
        }
    
    def get_capabilities_list(self) -> Dict[str, Any]:
        """Get list of all capabilities"""
        return {"ok": True, "capabilities": [c.value for c in Capability]}
    
    def get_agent_types_list(self) -> Dict[str, Any]:
        """Get list of all agent types"""
        return {"ok": True, "agent_types": [t.value for t in AgentType]}


# ============================================================
# SINGLETON
# ============================================================

_gateway_instance: Optional[ProtocolGateway] = None


def get_gateway() -> ProtocolGateway:
    """Get singleton gateway instance"""
    global _gateway_instance
    if _gateway_instance is None:
        _gateway_instance = ProtocolGateway()
    return _gateway_instance


# ============================================================
# FASTAPI ENDPOINTS FOR MAIN.PY
# ============================================================

PROTOCOL_ENDPOINTS = '''
# ============================================================
# PROTOCOL GATEWAY ENDPOINTS - Add to main.py
# ============================================================

from protocol_gateway import get_gateway

@app.post("/protocol/register")
async def protocol_register(body: Dict = Body(...)):
    """Register new agent in the AIGx Protocol"""
    gateway = get_gateway()
    return gateway.register_agent(
        agent_type=body.get("agent_type", "custom"),
        name=body.get("name"),
        description=body.get("description", ""),
        capabilities=body.get("capabilities", []),
        owner_id=body.get("owner_id"),
        api_endpoint=body.get("api_endpoint"),
        initial_aigx=body.get("initial_aigx", 0)
    )

@app.post("/protocol/settle")
async def protocol_settle(body: Dict = Body(...)):
    """Settle AI-to-AI payment"""
    gateway = get_gateway()
    return gateway.settle(
        api_key=body.get("api_key"),
        to_agent=body.get("to_agent"),
        amount_aigx=body.get("amount_aigx"),
        work_hash=body.get("work_hash"),
        proof_of_work=body.get("proof_of_work"),
        metadata=body.get("metadata")
    )

@app.post("/protocol/stake")
async def protocol_stake(body: Dict = Body(...)):
    """Stake AIGx"""
    gateway = get_gateway()
    return gateway.stake(body.get("api_key"), body.get("amount_aigx"))

@app.post("/protocol/unstake")
async def protocol_unstake(body: Dict = Body(...)):
    """Unstake AIGx"""
    gateway = get_gateway()
    return gateway.unstake(body.get("api_key"), body.get("amount_aigx"))

@app.get("/protocol/balance")
async def protocol_balance(api_key: str):
    """Get AIGx balance"""
    gateway = get_gateway()
    return gateway.get_balance(api_key)

@app.get("/protocol/agent/{agent_id}")
async def protocol_agent(agent_id: str):
    """Get agent info (public)"""
    gateway = get_gateway()
    return gateway.get_agent(agent_id)

@app.get("/protocol/agents/search")
async def protocol_search(
    capability: str = None,
    agent_type: str = None,
    min_reputation: int = 0,
    verified_only: bool = False,
    limit: int = 50
):
    """Search for agents (public)"""
    gateway = get_gateway()
    return gateway.search_agents(capability, agent_type, min_reputation, verified_only, limit)

@app.get("/protocol/leaderboard")
async def protocol_leaderboard(limit: int = 20):
    """Get agent leaderboard (public)"""
    gateway = get_gateway()
    return gateway.get_leaderboard(limit)

@app.get("/protocol/tx/{tx_id}")
async def protocol_tx(tx_id: str):
    """Get transaction (public)"""
    gateway = get_gateway()
    return gateway.get_transaction(tx_id)

@app.get("/protocol/verify/{tx_id}")
async def protocol_verify(tx_id: str):
    """Verify transaction (public)"""
    gateway = get_gateway()
    return gateway.verify_transaction(tx_id)

@app.get("/protocol/history")
async def protocol_history(api_key: str, limit: int = 50):
    """Get agent transaction history"""
    gateway = get_gateway()
    return gateway.get_agent_history(api_key, limit)

@app.get("/protocol/info")
async def protocol_info():
    """Get protocol information (public)"""
    gateway = get_gateway()
    return gateway.get_protocol_info()

@app.get("/protocol/capabilities")
async def protocol_capabilities():
    """Get capabilities list (public)"""
    gateway = get_gateway()
    return gateway.get_capabilities_list()

@app.get("/protocol/agent-types")
async def protocol_agent_types():
    """Get agent types list (public)"""
    gateway = get_gateway()
    return gateway.get_agent_types_list()
'''


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print("=" * 70)
    print("PROTOCOL GATEWAY - API for External Agents")
    print("=" * 70)
    
    gateway = get_gateway()
    
    print("\n1. Register external Claude agent...")
    claude_result = gateway.register_agent(
        agent_type="claude",
        name="External Claude Worker",
        description="Code generation specialist",
        capabilities=["code_generation", "code_review"],
        owner_id="external_platform",
        initial_aigx=500.0
    )
    print(f"   Agent ID: {claude_result.get('agent_id')}")
    print(f"   API Key: {claude_result.get('api_key')[:20]}...")
    claude_key = claude_result.get("api_key")
    claude_id = claude_result.get("agent_id")
    
    print("\n2. Register external GPT agent...")
    gpt_result = gateway.register_agent(
        agent_type="gpt",
        name="External GPT Assistant",
        description="Content writing expert",
        capabilities=["content_writing", "copywriting"],
        owner_id="another_platform",
        initial_aigx=300.0
    )
    gpt_key = gpt_result.get("api_key")
    gpt_id = gpt_result.get("agent_id")
    print(f"   Agent ID: {gpt_id}")
    
    print("\n3. GPT pays Claude 100 AIGx for code work...")
    work_hash = hashlib.sha256(b"completed_api_integration").hexdigest()
    
    settle_result = gateway.settle(
        api_key=gpt_key,
        to_agent=claude_id,
        amount_aigx=100.0,
        work_hash=work_hash,
        proof_of_work={"type": "api_integration", "endpoints": 5}
    )
    print(f"   Settlement: {settle_result.get('ok')}")
    print(f"   TX Hash: {settle_result.get('tx_hash', 'N/A')[:20]}...")
    
    print("\n4. Check balances...")
    claude_balance = gateway.get_balance(claude_key)
    gpt_balance = gateway.get_balance(gpt_key)
    print(f"   Claude: {claude_balance.get('balance')} AIGx")
    print(f"   GPT: {gpt_balance.get('balance')} AIGx")
    
    print("\n5. Claude stakes 100 AIGx...")
    stake_result = gateway.stake(claude_key, 100.0)
    print(f"   Staked: {stake_result.get('amount_staked')} AIGx")
    
    print("\n6. Search for code agents...")
    search_result = gateway.search_agents(capability="code_generation")
    print(f"   Found: {search_result.get('count')} agents")
    
    print("\n7. Get protocol info...")
    info = gateway.get_protocol_info()
    print(f"   Protocol: {info.get('protocol')} v{info.get('version')}")
    print(f"   Fee Rate: {info.get('fee_rate')}")
    
    print("\n8. Verify transaction...")
    if settle_result.get("settlement_id"):
        verify = gateway.verify_transaction(settle_result["settlement_id"])
        print(f"   Verified: {verify.get('verified')}")
    
    print("\n9. Get leaderboard...")
    leaderboard = gateway.get_leaderboard(5)
    for entry in leaderboard.get("leaderboard", []):
        print(f"   #{entry['rank']}: {entry['name']} - {entry['score']} pts")
    
    print("\n" + "=" * 70)
    print("Protocol Gateway test complete!")
    print("=" * 70)
