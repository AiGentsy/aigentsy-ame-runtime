"""
AiGentsy MetaBridge - Auto-Assemble JV Teams
Autonomous team formation for complex jobs based on skill matching
"""
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from uuid import uuid4

def _now():
    return datetime.now(timezone.utc).isoformat()


# Team formation rules
TEAM_RULES = {
    "min_budget_for_team": 2000,  # Jobs under $2k don't trigger team formation
    "max_team_size": 5,
    "min_skill_coverage": 0.80,  # Must cover 80% of required skills
    "compatibility_threshold": 0.6,
    "auto_propose_enabled": True
}

# Role-based default splits
ROLE_SPLITS = {
    "lead": 0.40,        # Project lead/coordinator
    "specialist": 0.30,  # Domain specialist
    "support": 0.20,     # Support role
    "advisor": 0.10      # Advisor/consultant
}


def analyze_intent_complexity(
    intent: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze if intent requires a team
    """
    budget = float(intent.get("budget", 0))
    required_skills = set(intent.get("required_skills", []))
    estimated_hours = intent.get("estimated_hours", 0)
    
    # Complexity score
    complexity_factors = []
    
    # Budget factor
    if budget >= TEAM_RULES["min_budget_for_team"]:
        complexity_factors.append("high_budget")
    
    # Skill diversity factor
    if len(required_skills) >= 3:
        complexity_factors.append("diverse_skills")
    
    # Time factor
    if estimated_hours >= 100:
        complexity_factors.append("large_scope")
    
    # Determine if team needed
    requires_team = len(complexity_factors) >= 2
    
    return {
        "requires_team": requires_team,
        "complexity_factors": complexity_factors,
        "budget": budget,
        "required_skills": list(required_skills),
        "skill_count": len(required_skills),
        "estimated_hours": estimated_hours
    }


def find_complementary_agents(
    intent: Dict[str, Any],
    all_agents: List[Dict[str, Any]],
    max_team_size: int = None
) -> Dict[str, Any]:
    """
    Find agents with complementary skills for the intent
    """
    if not max_team_size:
        max_team_size = TEAM_RULES["max_team_size"]
    
    required_skills = set(intent.get("required_skills", []))
    
    if not required_skills:
        return {
            "ok": False,
            "error": "no_required_skills",
            "message": "Intent must specify required skills"
        }
    
    # Score each agent
    candidates = []
    
    for agent in all_agents:
        username = agent.get("consent", {}).get("username") or agent.get("username")
        agent_skills = set(agent.get("profile", {}).get("skills", []))
        outcome_score = int(agent.get("outcomeScore", 0))
        
        # Skip if no skills
        if not agent_skills:
            continue
        
        # Calculate skill coverage
        covered_skills = required_skills.intersection(agent_skills)
        coverage = len(covered_skills) / len(required_skills) if required_skills else 0
        
        # Skip if coverage too low
        if coverage < 0.2:  # Must cover at least 20% of skills
            continue
        
        # Calculate composite score
        reputation_score = outcome_score / 100
        skill_score = coverage
        
        composite_score = (reputation_score * 0.4) + (skill_score * 0.6)
        
        candidates.append({
            "username": username,
            "agent": agent,
            "skills": list(agent_skills),
            "covered_skills": list(covered_skills),
            "skill_coverage": round(coverage, 2),
            "outcome_score": outcome_score,
            "composite_score": round(composite_score, 3)
        })
    
    # Sort by composite score
    candidates.sort(key=lambda c: c["composite_score"], reverse=True)
    
    return {
        "ok": True,
        "total_candidates": len(candidates),
        "candidates": candidates,
        "required_skills": list(required_skills)
    }


def optimize_team_composition(
    intent: Dict[str, Any],
    candidates: List[Dict[str, Any]],
    max_team_size: int = None
) -> Dict[str, Any]:
    """
    Select optimal team that maximizes skill coverage
    """
    if not max_team_size:
        max_team_size = TEAM_RULES["max_team_size"]
    
    required_skills = set(intent.get("required_skills", []))
    min_coverage = TEAM_RULES["min_skill_coverage"]
    
    # Greedy algorithm: add agents that cover most uncovered skills
    team = []
    covered_skills = set()
    
    remaining_candidates = candidates.copy()
    
    while len(team) < max_team_size and remaining_candidates:
        best_candidate = None
        best_new_coverage = 0
        
        for candidate in remaining_candidates:
            candidate_skills = set(candidate["covered_skills"])
            new_skills = candidate_skills - covered_skills
            new_coverage = len(new_skills)
            
            if new_coverage > best_new_coverage:
                best_new_coverage = new_coverage
                best_candidate = candidate
        
        if not best_candidate or best_new_coverage == 0:
            break  # No more useful additions
        
        # Add to team
        team.append(best_candidate)
        covered_skills.update(best_candidate["covered_skills"])
        remaining_candidates.remove(best_candidate)
        
        # Check if we've covered enough
        coverage_rate = len(covered_skills) / len(required_skills) if required_skills else 0
        if coverage_rate >= min_coverage:
            break
    
    # Calculate final coverage
    final_coverage = len(covered_skills) / len(required_skills) if required_skills else 0
    missing_skills = required_skills - covered_skills
    
    meets_requirements = final_coverage >= min_coverage
    
    return {
        "ok": True,
        "team": team,
        "team_size": len(team),
        "covered_skills": list(covered_skills),
        "missing_skills": list(missing_skills),
        "skill_coverage": round(final_coverage, 2),
        "meets_requirements": meets_requirements
    }


def assign_team_roles(
    team: List[Dict[str, Any]],
    intent: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Assign roles to team members based on skills and reputation
    """
    if not team:
        return {"ok": False, "error": "no_team_members"}
    
    # Sort by composite score
    sorted_team = sorted(team, key=lambda m: m["composite_score"], reverse=True)
    
    roles = []
    
    # Assign lead (highest score)
    if len(sorted_team) >= 1:
        roles.append({
            "username": sorted_team[0]["username"],
            "role": "lead",
            "covered_skills": sorted_team[0]["covered_skills"],
            "outcome_score": sorted_team[0]["outcome_score"]
        })
    
    # Assign specialists (next 1-2)
    specialist_count = min(2, len(sorted_team) - 1)
    for i in range(1, 1 + specialist_count):
        if i < len(sorted_team):
            roles.append({
                "username": sorted_team[i]["username"],
                "role": "specialist",
                "covered_skills": sorted_team[i]["covered_skills"],
                "outcome_score": sorted_team[i]["outcome_score"]
            })
    
    # Assign support (remaining)
    for i in range(1 + specialist_count, len(sorted_team)):
        roles.append({
            "username": sorted_team[i]["username"],
            "role": "support",
            "covered_skills": sorted_team[i]["covered_skills"],
            "outcome_score": sorted_team[i]["outcome_score"]
        })
    
    return {
        "ok": True,
        "roles": roles,
        "team_composition": {
            "lead": len([r for r in roles if r["role"] == "lead"]),
            "specialist": len([r for r in roles if r["role"] == "specialist"]),
            "support": len([r for r in roles if r["role"] == "support"])
        }
    }


def calculate_team_splits(
    roles: List[Dict[str, Any]],
    intent_budget: float
) -> Dict[str, Any]:
    """
    Calculate revenue splits based on roles
    """
    # Count roles
    role_counts = {}
    for member in roles:
        role = member["role"]
        role_counts[role] = role_counts.get(role, 0) + 1
    
    # Calculate splits
    splits = {}
    total_allocation = 0.0
    
    for member in roles:
        role = member["role"]
        username = member["username"]
        
        # Base split from role
        base_split = ROLE_SPLITS.get(role, 0.20)
        
        # If multiple in same role, divide equally
        role_count = role_counts[role]
        member_split = base_split / role_count
        
        splits[username] = member_split
        total_allocation += member_split
    
    # Normalize to 1.0 if needed
    if abs(total_allocation - 1.0) > 0.01:
        normalization_factor = 1.0 / total_allocation
        splits = {k: v * normalization_factor for k, v in splits.items()}
    
    # Calculate amounts
    split_amounts = {
        username: round(intent_budget * split_pct, 2)
        for username, split_pct in splits.items()
    }
    
    return {
        "ok": True,
        "splits": {k: round(v, 3) for k, v in splits.items()},
        "split_amounts": split_amounts,
        "total_budget": round(intent_budget, 2),
        "role_distribution": role_counts
    }


def create_team_proposal(
    intent: Dict[str, Any],
    team_roles: List[Dict[str, Any]],
    splits: Dict[str, float]
) -> Dict[str, Any]:
    """
    Create a JV team proposal for voting
    """
    proposal_id = f"team_{uuid4().hex[:12]}"
    
    # Collect team members
    team_members = [member["username"] for member in team_roles]
    lead = next((m["username"] for m in team_roles if m["role"] == "lead"), team_members[0])
    
    proposal = {
        "id": proposal_id,
        "type": "metabridge_team",
        "intent_id": intent.get("id"),
        "intent_budget": float(intent.get("budget", 0)),
        "status": "PENDING_VOTES",
        "created_at": _now(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
        
        "team": {
            "lead": lead,
            "members": team_members,
            "roles": team_roles,
            "size": len(team_members)
        },
        
        "splits": splits,
        
        "votes": {member: "PENDING" for member in team_members},
        
        "required_votes": len(team_members),
        "received_votes": 0,
        
        "formation_reason": "metabridge_auto_assembly",
        "skill_coverage": 0.0,  # Will be set by caller
        
        "events": [
            {"type": "PROPOSAL_CREATED", "at": _now(), "by": "metabridge"}
        ]
    }
    
    return {
        "ok": True,
        "proposal": proposal
    }


def vote_on_team_proposal(
    proposal: Dict[str, Any],
    voter: str,
    vote: str,
    feedback: str = ""
) -> Dict[str, Any]:
    """
    Vote on team proposal
    """
    if proposal["status"] != "PENDING_VOTES":
        return {
            "ok": False,
            "error": "proposal_not_pending",
            "status": proposal["status"]
        }
    
    if voter not in proposal["team"]["members"]:
        return {
            "ok": False,
            "error": "not_team_member",
            "voter": voter
        }
    
    if vote.upper() not in ["APPROVED", "REJECTED"]:
        return {
            "ok": False,
            "error": "invalid_vote",
            "valid_votes": ["APPROVED", "REJECTED"]
        }
    
    # Record vote
    proposal["votes"][voter] = vote.upper()
    proposal["received_votes"] += 1
    
    proposal["events"].append({
        "type": f"VOTE_{vote.upper()}",
        "by": voter,
        "feedback": feedback,
        "at": _now()
    })
    
    # Check if all voted
    all_votes = list(proposal["votes"].values())
    
    if "REJECTED" in all_votes:
        # Any rejection = proposal rejected
        proposal["status"] = "REJECTED"
        proposal["rejected_at"] = _now()
        
        return {
            "ok": True,
            "status": "REJECTED",
            "message": "Team proposal rejected"
        }
    
    if all(v == "APPROVED" for v in all_votes):
        # All approved = team formed
        proposal["status"] = "APPROVED"
        proposal["approved_at"] = _now()
        
        return {
            "ok": True,
            "status": "APPROVED",
            "message": "Team formed successfully",
            "team_size": len(proposal["team"]["members"])
        }
    
    # Still pending
    votes_remaining = proposal["required_votes"] - proposal["received_votes"]
    
    return {
        "ok": True,
        "status": "PENDING_VOTES",
        "votes_remaining": votes_remaining,
        "message": f"Vote recorded, {votes_remaining} votes remaining"
    }


def execute_metabridge(
    intent: Dict[str, Any],
    all_agents: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Execute complete MetaBridge pipeline
    """
    # 1. Analyze complexity
    complexity = analyze_intent_complexity(intent)
    
    if not complexity["requires_team"]:
        return {
            "ok": False,
            "action": "no_team_needed",
            "complexity_analysis": complexity,
            "message": "Intent does not require team formation"
        }
    
    # 2. Find candidates
    candidates_result = find_complementary_agents(intent, all_agents)
    
    if not candidates_result["ok"] or candidates_result["total_candidates"] == 0:
        return {
            "ok": False,
            "action": "no_candidates_found",
            "complexity_analysis": complexity,
            "message": "No suitable agents found"
        }
    
    # 3. Optimize team
    team_result = optimize_team_composition(intent, candidates_result["candidates"])
    
    if not team_result["meets_requirements"]:
        return {
            "ok": False,
            "action": "insufficient_coverage",
            "complexity_analysis": complexity,
            "team_attempt": team_result,
            "message": f"Could not achieve {TEAM_RULES['min_skill_coverage']*100}% skill coverage"
        }
    
    # 4. Assign roles
    roles_result = assign_team_roles(team_result["team"], intent)
    
    # 5. Calculate splits
    splits_result = calculate_team_splits(roles_result["roles"], float(intent.get("budget", 0)))
    
    # 6. Create proposal
    proposal_result = create_team_proposal(intent, roles_result["roles"], splits_result["splits"])
    proposal = proposal_result["proposal"]
    
    # Add skill coverage to proposal
    proposal["skill_coverage"] = team_result["skill_coverage"]
    
    return {
        "ok": True,
        "action": "team_proposal_created",
        "complexity_analysis": complexity,
        "team_composition": team_result,
        "roles": roles_result["roles"],
        "splits": splits_result,
        "proposal": proposal,
        "message": f"Team of {len(roles_result['roles'])} agents proposed with {int(team_result['skill_coverage']*100)}% skill coverage"
    }


def get_metabridge_stats(
    proposals: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Get MetaBridge performance statistics
    """
    total_proposals = len(proposals)
    
    by_status = {}
    for proposal in proposals:
        status = proposal.get("status", "unknown")
        by_status[status] = by_status.get(status, 0) + 1
    
    approved = by_status.get("APPROVED", 0)
    rejected = by_status.get("REJECTED", 0)
    pending = by_status.get("PENDING_VOTES", 0)
    
    approval_rate = (approved / total_proposals) if total_proposals > 0 else 0
    
    # Average team size
    avg_team_size = 0
    if proposals:
        total_members = sum([len(p.get("team", {}).get("members", [])) for p in proposals])
        avg_team_size = total_members / len(proposals)
    
    return {
        "total_proposals": total_proposals,
        "approved": approved,
        "rejected": rejected,
        "pending": pending,
        "approval_rate": round(approval_rate, 2),
        "avg_team_size": round(avg_team_size, 1)
    }
