"""
Proposal Generator - Wrapper for proposal_delivery
Provides backward compatibility for ame_pitches imports
"""

# Re-export from proposal_delivery
try:
    from proposal_delivery import deliver_proposal, format_universal_dm
except ImportError:
    # Fallback stub if proposal_delivery isn't available
    def deliver_proposal(query, matches, originator):
        return {"webhook": False, "email": False, "dm": False}
    
    def format_universal_dm(recipient, platform, proposal):
        return f"DM to {recipient}: {proposal}"
