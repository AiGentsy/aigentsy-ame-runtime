"""
Proposal Generator - Wrapper for proposal_delivery
Provides backward compatibility for ame_pitches imports
"""

# Re-export from proposal_delivery
try:
    from proposal_delivery import (
        deliver_proposal,
        generate_proposal,
        send_proposal
    )
except ImportError:
    # Fallback stub if proposal_delivery isn't available
    def deliver_proposal(query, matches, originator):
        return {"ok": False, "error": "proposal_delivery not available"}
    
    def generate_proposal(*args, **kwargs):
        return {"ok": False, "error": "proposal_delivery not available"}
    
    def send_proposal(*args, **kwargs):
        return {"ok": False, "error": "proposal_delivery not available"}
