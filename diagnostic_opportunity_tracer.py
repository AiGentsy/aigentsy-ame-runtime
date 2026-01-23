"""
DIAGNOSTIC OPPORTUNITY TRACER
═══════════════════════════════════════════════════════════════════════════════

Traces opportunities through the complete funnel to identify bottlenecks:
1. Discovery → What gaps are being found?
2. Scoring → How are they being ranked?
3. Routing → Which PDLs are selected?
4. Execution → Are they actually posted/submitted?
5. Response → Are we getting engagement?
6. Contract → Are we sending agreements?
7. Payment → Is revenue being collected?

Also audits internet-wide browser-based discovery:
- Which platforms are we scanning?
- Are we limited to 27 known platforms or discovering new ones?
- Is Universal Fabric being used for browser-based opportunities?
- What's our coverage beyond the standard 7 dimensions?

Updated: Jan 2026
"""

import os
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict

# ═══════════════════════════════════════════════════════════════════════════════
# FUNNEL STAGE DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

FUNNEL_STAGES = [
    "discovered",      # Gap/opportunity detected
    "scored",          # EV and OCS calculated
    "routed",          # PDL selected for execution
    "queued",          # Added to execution queue
    "attempted",       # Execution attempted
    "posted",          # Successfully posted/submitted
    "engaged",         # Got response/interaction
    "contracted",      # Agreement/contract sent
    "paid"             # Revenue collected
]

# ═══════════════════════════════════════════════════════════════════════════════
# OPPORTUNITY TRACER
# ═══════════════════════════════════════════════════════════════════════════════

class OpportunityTracer:
    """Trace opportunities through the complete funnel"""
    
    def __init__(self):
        self.opportunities = []
        self.funnel_metrics = defaultdict(int)
        self.drop_off_reasons = defaultdict(list)
        self.platform_coverage = {}
        
    def trace_cycle(self, cycle_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trace a complete cycle and identify bottlenecks.
        
        Expected cycle_data structure:
        {
            "cycle_id": "cycle_xxx",
            "phases": {
                "discovery": {"opportunities": [...]},
                "polymorphic": {"queued": [...], "executed": [...]},
                "revenue": {"collected": 0}
            }
        }
        """
        
        trace_results = {
            "cycle_id": cycle_data.get("cycle_id", "unknown"),
            "traced_at": datetime.now(timezone.utc).isoformat(),
            "funnel_analysis": {},
            "drop_off_points": [],
            "bottleneck": None,
            "opportunities_traced": []
        }
        
        # Extract opportunities from discovery phase
        discovery = cycle_data.get("phases", {}).get("discovery", {})
        opportunities = discovery.get("opportunities", [])
        
        if not opportunities:
            trace_results["error"] = "No opportunities found in cycle data"
            return trace_results
        
        # Trace each opportunity
        for opp in opportunities[:20]:  # Trace first 20 for performance
            opp_trace = self._trace_single_opportunity(opp, cycle_data)
            trace_results["opportunities_traced"].append(opp_trace)
            
        # Calculate funnel metrics
        funnel_counts = defaultdict(int)
        for opp_trace in trace_results["opportunities_traced"]:
            final_stage = opp_trace.get("final_stage", "discovered")
            funnel_counts[final_stage] += 1
            
        # Build funnel analysis
        total = len(trace_results["opportunities_traced"])
        funnel_analysis = {}
        conversion_rates = {}
        
        for stage in FUNNEL_STAGES:
            count = sum(1 for ot in trace_results["opportunities_traced"] 
                       if self._reached_stage(ot, stage))
            funnel_analysis[stage] = {
                "count": count,
                "percentage": round(count / total * 100, 1) if total > 0 else 0
            }
            
            # Calculate conversion rate from previous stage
            if stage != "discovered":
                prev_stage_idx = FUNNEL_STAGES.index(stage) - 1
                prev_stage = FUNNEL_STAGES[prev_stage_idx]
                prev_count = funnel_analysis.get(prev_stage, {}).get("count", 0)
                if prev_count > 0:
                    conversion_rates[f"{prev_stage}_to_{stage}"] = round(count / prev_count * 100, 1)
        
        trace_results["funnel_analysis"] = funnel_analysis
        trace_results["conversion_rates"] = conversion_rates
        
        # Identify biggest drop-off
        max_drop = 0
        bottleneck_stage = None
        for i in range(len(FUNNEL_STAGES) - 1):
            current_stage = FUNNEL_STAGES[i]
            next_stage = FUNNEL_STAGES[i + 1]
            current_count = funnel_analysis.get(current_stage, {}).get("count", 0)
            next_count = funnel_analysis.get(next_stage, {}).get("count", 0)
            drop = current_count - next_count
            
            if drop > max_drop:
                max_drop = drop
                bottleneck_stage = f"{current_stage} → {next_stage}"
        
        trace_results["bottleneck"] = {
            "stage": bottleneck_stage,
            "opportunities_lost": max_drop,
            "percentage_lost": round(max_drop / total * 100, 1) if total > 0 else 0
        }
        
        # Collect drop-off reasons
        drop_off_summary = defaultdict(int)
        for opp_trace in trace_results["opportunities_traced"]:
            reason = opp_trace.get("drop_off_reason")
            if reason:
                drop_off_summary[reason] += 1
        
        trace_results["drop_off_reasons"] = dict(drop_off_summary)
        
        return trace_results
    
    def _trace_single_opportunity(self, opp: Dict[str, Any], cycle_data: Dict[str, Any]) -> Dict[str, Any]:
        """Trace a single opportunity through all stages"""
        
        opp_id = opp.get("id") or opp.get("opportunity_id") or "unknown"
        
        trace = {
            "opportunity_id": opp_id,
            "platform": opp.get("platform", "unknown"),
            "ev": opp.get("ev", 0),
            "ocs": opp.get("ocs", 0),
            "stages_reached": [],
            "final_stage": "discovered",
            "drop_off_reason": None,
            "execution_method": None,
            "pdl_selected": None
        }
        
        # Stage 1: Discovered (always true if we're tracing it)
        trace["stages_reached"].append("discovered")
        
        # Stage 2: Scored (check if EV/OCS exist)
        if opp.get("ev") is not None and opp.get("ocs") is not None:
            trace["stages_reached"].append("scored")
            trace["final_stage"] = "scored"
        else:
            trace["drop_off_reason"] = "missing_score"
            return trace
        
        # Stage 3: Routed (check if PDL selected)
        pdl = opp.get("pdl") or opp.get("selected_pdl")
        if pdl:
            trace["stages_reached"].append("routed")
            trace["final_stage"] = "routed"
            trace["pdl_selected"] = pdl
        else:
            trace["drop_off_reason"] = "no_pdl_selected"
            return trace
        
        # Stage 4: Queued (check polymorphic phase)
        polymorphic = cycle_data.get("phases", {}).get("polymorphic", {})
        queued = polymorphic.get("queued", [])
        
        if self._is_in_list(opp_id, queued):
            trace["stages_reached"].append("queued")
            trace["final_stage"] = "queued"
        else:
            # Might have skipped queue and gone straight to execution
            pass
        
        # Stage 5: Attempted (check execution attempts)
        executed = polymorphic.get("executed", [])
        if self._is_in_list(opp_id, executed):
            trace["stages_reached"].append("attempted")
            trace["final_stage"] = "attempted"
        else:
            if "queued" in trace["stages_reached"]:
                trace["drop_off_reason"] = "queued_but_not_executed"
            else:
                trace["drop_off_reason"] = "not_attempted"
            return trace
        
        # Stage 6: Posted (check if execution succeeded)
        execution_result = self._find_execution_result(opp_id, cycle_data)
        if execution_result and execution_result.get("status") == "success":
            trace["stages_reached"].append("posted")
            trace["final_stage"] = "posted"
        else:
            trace["drop_off_reason"] = execution_result.get("error") if execution_result else "execution_failed"
            return trace
        
        # Stage 7: Engaged (check for responses)
        if execution_result.get("responses") or execution_result.get("engaged"):
            trace["stages_reached"].append("engaged")
            trace["final_stage"] = "engaged"
        else:
            trace["drop_off_reason"] = "no_engagement"
            return trace
        
        # Stage 8: Contracted (check if contract sent)
        if execution_result.get("contract_sent") or execution_result.get("proposal_sent"):
            trace["stages_reached"].append("contracted")
            trace["final_stage"] = "contracted"
        else:
            trace["drop_off_reason"] = "engagement_no_contract"
            return trace
        
        # Stage 9: Paid (check revenue collection)
        revenue = cycle_data.get("phases", {}).get("revenue", {})
        if self._is_in_revenue(opp_id, revenue):
            trace["stages_reached"].append("paid")
            trace["final_stage"] = "paid"
        else:
            trace["drop_off_reason"] = "contract_not_paid"
            return trace
        
        return trace
    
    def _reached_stage(self, opp_trace: Dict, stage: str) -> bool:
        """Check if opportunity reached a specific stage"""
        return stage in opp_trace.get("stages_reached", [])
    
    def _is_in_list(self, opp_id: str, item_list: List) -> bool:
        """Check if opportunity is in a list (by ID)"""
        if not item_list:
            return False
        
        for item in item_list:
            if isinstance(item, dict):
                if item.get("id") == opp_id or item.get("opportunity_id") == opp_id:
                    return True
            elif isinstance(item, str) and item == opp_id:
                return True
        
        return False
    
    def _find_execution_result(self, opp_id: str, cycle_data: Dict) -> Optional[Dict]:
        """Find execution result for an opportunity"""
        execution_results = cycle_data.get("phases", {}).get("polymorphic", {}).get("results", [])
        
        for result in execution_results:
            if result.get("opportunity_id") == opp_id:
                return result
        
        return None
    
    def _is_in_revenue(self, opp_id: str, revenue_data: Dict) -> bool:
        """Check if opportunity generated revenue"""
        collected = revenue_data.get("collected", [])
        return self._is_in_list(opp_id, collected)


# ═══════════════════════════════════════════════════════════════════════════════
# INTERNET-WIDE COVERAGE AUDIT
# ═══════════════════════════════════════════════════════════════════════════════

class InternetCoverageAuditor:
    """Audit what platforms we're discovering and how"""
    
    STANDARD_PLATFORMS = [
        # 7 Dimensions, 27+ Platforms
        "reddit", "hackernews", "twitter", "linkedin", "instagram",
        "github", "stackoverflow", "medium", "dev.to",
        "upwork", "fiverr", "freelancer", "toptal",
        "stripe", "shopify", "woocommerce", "square",
        "producthunt", "indiehackers", "betalist",
        "angellist", "crunchbase", "builtwith",
        "amazon", "ebay", "etsy", "alibaba"
    ]
    
    def audit_discovery_coverage(self, pdl_catalog: Dict[str, Any]) -> Dict[str, Any]:
        """Audit what platforms we can discover opportunities on"""
        
        audit = {
            "audited_at": datetime.now(timezone.utc).isoformat(),
            "platform_coverage": {},
            "discovery_methods": {},
            "internet_wide_capable": False,
            "browser_based_discovery": [],
            "api_based_discovery": [],
            "beyond_standard_platforms": []
        }
        
        # Analyze each PDL
        for pdl_name, pdl_config in pdl_catalog.items():
            platform = pdl_config.get("platform", "unknown")
            execution_method = pdl_config.get("execution_method", "unknown")
            
            # Track platform
            if platform not in audit["platform_coverage"]:
                audit["platform_coverage"][platform] = {
                    "pdls": [],
                    "discovery_capable": False,
                    "execution_capable": False,
                    "browser_required": False
                }
            
            audit["platform_coverage"][platform]["pdls"].append(pdl_name)
            
            # Check if this PDL does discovery
            if "discover" in pdl_name.lower() or "scrape" in pdl_name.lower() or "search" in pdl_name.lower():
                audit["platform_coverage"][platform]["discovery_capable"] = True
            
            # Check execution method
            if execution_method in ["browser", "universal_fabric", "hybrid"]:
                audit["platform_coverage"][platform]["browser_required"] = True
                audit["browser_based_discovery"].append(pdl_name)
            elif execution_method == "api":
                audit["api_based_discovery"].append(pdl_name)
            
            if pdl_config.get("can_execute", False):
                audit["platform_coverage"][platform]["execution_capable"] = True
        
        # Identify platforms beyond the standard 27
        for platform in audit["platform_coverage"].keys():
            if platform.lower() not in [p.lower() for p in self.STANDARD_PLATFORMS]:
                audit["beyond_standard_platforms"].append(platform)
        
        # Check if we have internet-wide discovery capability
        universal_fabric_available = os.getenv("PLAYWRIGHT_AVAILABLE") or os.path.exists("universal_fulfillment_fabric.py")
        audit["internet_wide_capable"] = universal_fabric_available
        
        # Summary stats
        audit["summary"] = {
            "total_platforms": len(audit["platform_coverage"]),
            "standard_platforms_covered": len([p for p in audit["platform_coverage"].keys() 
                                              if p.lower() in [sp.lower() for sp in self.STANDARD_PLATFORMS]]),
            "beyond_standard_platforms": len(audit["beyond_standard_platforms"]),
            "browser_based_pdls": len(audit["browser_based_discovery"]),
            "api_based_pdls": len(audit["api_based_discovery"]),
            "discovery_capable_platforms": len([p for p, data in audit["platform_coverage"].items() 
                                               if data["discovery_capable"]])
        }
        
        return audit
    
    def check_universal_fabric_usage(self, recent_cycles: List[Dict]) -> Dict[str, Any]:
        """Check if Universal Fabric is actually being used for discovery"""
        
        usage_stats = {
            "checked_cycles": len(recent_cycles),
            "universal_fabric_executions": 0,
            "browser_based_discoveries": 0,
            "platforms_accessed_via_browser": set(),
            "sample_executions": []
        }
        
        for cycle in recent_cycles:
            # Look for universal fabric execution indicators
            phases = cycle.get("phases", {})
            
            # Check polymorphic phase
            polymorphic = phases.get("polymorphic", {})
            executed = polymorphic.get("executed", [])
            
            for execution in executed:
                method = execution.get("method")
                if method in ["browser", "universal_fabric"]:
                    usage_stats["universal_fabric_executions"] += 1
                    platform = execution.get("platform")
                    if platform:
                        usage_stats["platforms_accessed_via_browser"].add(platform)
                    
                    # Sample first 5
                    if len(usage_stats["sample_executions"]) < 5:
                        usage_stats["sample_executions"].append({
                            "cycle_id": cycle.get("cycle_id"),
                            "platform": platform,
                            "pdl": execution.get("pdl"),
                            "url": execution.get("url", "")[:100]
                        })
        
        usage_stats["platforms_accessed_via_browser"] = list(usage_stats["platforms_accessed_via_browser"])
        
        return usage_stats


# ═══════════════════════════════════════════════════════════════════════════════
# FASTAPI INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

def include_diagnostic_endpoints(app):
    """Add diagnostic endpoints to FastAPI app"""
    
    tracer = OpportunityTracer()
    auditor = InternetCoverageAuditor()
    
    @app.post("/diagnostic/trace-cycle")
    async def trace_cycle(cycle_data: Dict[str, Any]):
        """
        Trace a complete cycle and identify bottlenecks.
        
        Pass in the full cycle result from /orchestrator/unified-cycle
        """
        return tracer.trace_cycle(cycle_data)
    
    @app.get("/diagnostic/coverage-audit")
    async def coverage_audit():
        """
        Audit internet-wide discovery coverage.
        
        Shows:
        - Which platforms we're discovering on
        - Which use browser vs API
        - What's beyond the standard 27 platforms
        - Is Universal Fabric being used?
        """
        try:
            from pdl_polymorphic_catalog import get_pdl_catalog
            pdl_catalog = get_pdl_catalog()
            return auditor.audit_discovery_coverage(pdl_catalog)
        except Exception as e:
            return {"error": str(e)}
    
    @app.get("/diagnostic/universal-fabric-usage")
    async def universal_fabric_usage():
        """
        Check if Universal Fabric is being used for browser-based discovery.
        
        Analyzes recent cycles to see browser automation in action.
        """
        try:
            # Get recent cycles from wherever they're stored
            # This would need to be wired to your actual cycle storage
            recent_cycles = []  # TODO: Load from database/logs
            
            return auditor.check_universal_fabric_usage(recent_cycles)
        except Exception as e:
            return {"error": str(e)}
    
    @app.get("/diagnostic/funnel-health")
    async def funnel_health():
        """
        Get overall funnel health across all recent cycles.
        
        Shows aggregate conversion rates and identifies systemic bottlenecks.
        """
        # This would aggregate data across multiple cycles
        return {
            "status": "not_implemented",
            "note": "Wire this to your cycle storage to get aggregate funnel metrics"
        }
    
    print("🔍 DIAGNOSTIC ENDPOINTS LOADED")
    print("   • POST /diagnostic/trace-cycle - Trace opportunities through funnel")
    print("   • GET  /diagnostic/coverage-audit - Audit platform coverage")
    print("   • GET  /diagnostic/universal-fabric-usage - Check browser automation usage")
    print("   • GET  /diagnostic/funnel-health - Overall funnel health")


# ═══════════════════════════════════════════════════════════════════════════════
# CLI TESTING
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Test tracer with mock data
    print("\n" + "="*80)
    print("TESTING OPPORTUNITY TRACER")
    print("="*80)
    
    mock_cycle = {
        "cycle_id": "cycle_test_001",
        "phases": {
            "discovery": {
                "opportunities": [
                    {"id": "opp_1", "platform": "reddit", "ev": 25.50, "ocs": 0.8, "pdl": "reddit.reply"},
                    {"id": "opp_2", "platform": "hackernews", "ev": 12.00, "ocs": 0.6, "pdl": "hn.comment"},
                    {"id": "opp_3", "platform": "upwork", "ev": 150.00, "ocs": 0.9, "pdl": "upwork.submit_proposal"}
                ]
            },
            "polymorphic": {
                "queued": [
                    {"id": "opp_1"},
                    {"id": "opp_2"}
                ],
                "executed": [
                    {"id": "opp_1"}
                ],
                "results": [
                    {"opportunity_id": "opp_1", "status": "success", "responses": 2}
                ]
            },
            "revenue": {
                "collected": []
            }
        }
    }
    
    tracer = OpportunityTracer()
    result = tracer.trace_cycle(mock_cycle)
    
    print(json.dumps(result, indent=2))
    print("\n" + "="*80)
