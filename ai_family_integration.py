"""
═══════════════════════════════════════════════════════════════════════════════
AIGENTSY AI FAMILY INTEGRATION - MASTER RUNTIME ENHANCEMENT
═══════════════════════════════════════════════════════════════════════════════

This module integrates the AI Family Brain into the Master Runtime.

USAGE IN MASTER RUNTIME:
    from ai_family_integration import (
        AIFamilyIntegration,
        execute_with_family,
        run_family_learning_sync,
        get_family_dashboard
    )

═══════════════════════════════════════════════════════════════════════════════
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

def _now() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"

# Import the core modules
try:
    from ai_family_brain import (
        get_brain, ai_execute, ai_research, ai_content, ai_code,
        ai_ensemble, ai_chain, get_family_stats, get_synergy_score, record_quality,
        TaskCategory, export_to_metahive as brain_export_metahive,
        import_from_metahive as brain_import_metahive
    )
    AI_FAMILY_AVAILABLE = True
    print("✅ ai_family_brain")
except ImportError as e:
    AI_FAMILY_AVAILABLE = False
    print(f"❌ ai_family_brain: {e}")

try:
    from metahive_brain import (
        contribute_to_hive, query_hive, get_hive_stats, get_best_ai_routing,
        contribute_ai_family_learning, export_for_ai_family as hive_export_family,
        import_from_ai_family as hive_import_family
    )
    METAHIVE_AVAILABLE = True
    print("✅ metahive_brain (v2)")
except ImportError as e:
    METAHIVE_AVAILABLE = False
    print(f"❌ metahive_brain: {e}")

try:
    from yield_memory import (
        store_pattern, get_best_action, get_memory_stats,
        get_user_ai_recommendation, get_user_ai_stats, export_for_metahive as yield_export_hive
    )
    YIELD_MEMORY_AVAILABLE = True
    print("✅ yield_memory (v2)")
except ImportError as e:
    YIELD_MEMORY_AVAILABLE = False
    print(f"❌ yield_memory: {e}")


class AIFamilyIntegration:
    """Integration layer between Master Runtime and AI Family systems."""
    
    def __init__(self, username: str = "aigentsy"):
        self.username = username
        self.brain = get_brain() if AI_FAMILY_AVAILABLE else None
        self._pending_results: List[Dict[str, Any]] = []
        self._last_sync = None
        
        print(f"🧠 AI Family Integration: Brain={'✓' if AI_FAMILY_AVAILABLE else '✗'} | MetaHive={'✓' if METAHIVE_AVAILABLE else '✗'} | Yield={'✓' if YIELD_MEMORY_AVAILABLE else '✗'}")
    
    async def execute(self, prompt: str, task_type: str = "content_generation",
                      context: Dict[str, Any] = None, optimize_for: str = "balanced",
                      max_tokens: int = 2000) -> Dict[str, Any]:
        """Execute AI task with full family learning."""
        
        if not AI_FAMILY_AVAILABLE:
            return {"ok": False, "error": "AI Family Brain not available"}
        
        # Check MetaHive for recommendations
        if METAHIVE_AVAILABLE:
            hive_rec = get_best_ai_routing(task_type)
            if hive_rec.get("ok") and hive_rec.get("recommendation"):
                print(f"   🐝 MetaHive: {hive_rec['recommendation']} for {task_type}")
        
        # Check Yield Memory for user preferences
        if YIELD_MEMORY_AVAILABLE:
            user_rec = get_user_ai_recommendation(self.username, task_type)
            if user_rec.get("ok") and user_rec.get("recommended_model"):
                print(f"   👤 User prefers: {user_rec['recommended_model']}")
        
        # Execute
        result = await ai_execute(prompt, task_type, max_tokens, optimize_for)
        
        if result.get("ok"):
            self._pending_results.append({
                "task_id": result.get("task_id"),
                "model": result.get("model"),
                "task_category": task_type,
                "prompt_summary": prompt[:100],
                "context": context,
                "timestamp": _now()
            })
        
        return result
    
    async def execute_research(self, prompt: str, context: Dict = None) -> Dict[str, Any]:
        return await self.execute(prompt, "research", context)
    
    async def execute_content(self, prompt: str, context: Dict = None) -> Dict[str, Any]:
        return await self.execute(prompt, "content_generation", context)
    
    async def execute_code(self, prompt: str, context: Dict = None) -> Dict[str, Any]:
        return await self.execute(prompt, "code_generation", context)
    
    async def execute_pitch(self, prompt: str, context: Dict = None) -> Dict[str, Any]:
        return await self.execute(prompt, "pitch_creation", context)
    
    async def execute_discovery(self, prompt: str, context: Dict = None) -> Dict[str, Any]:
        return await self.execute(prompt, "opportunity_discovery", context)
    
    async def execute_ensemble(self, prompt: str, task_type: str = "content_generation",
                               aggregation: str = "synthesize") -> Dict[str, Any]:
        if not AI_FAMILY_AVAILABLE:
            return {"ok": False, "error": "AI Family Brain not available"}
        return await ai_ensemble(prompt, task_type, aggregation)
    
    async def execute_chain(self, prompt: str, task_type: str = "content_generation") -> Dict[str, Any]:
        if not AI_FAMILY_AVAILABLE:
            return {"ok": False, "error": "AI Family Brain not available"}
        return await ai_chain(prompt, task_type)
    
    def record_outcome(self, task_id: str, success: bool, quality_score: float = None,
                       revenue_generated: float = None, context: Dict[str, Any] = None):
        """Record outcome for learning."""
        
        if AI_FAMILY_AVAILABLE and quality_score:
            record_quality(task_id, quality_score, revenue_generated)
        
        pending = next((r for r in self._pending_results if r.get("task_id") == task_id), None)
        
        if pending and success:
            roas = (revenue_generated / 1.0) if revenue_generated else (quality_score * 2 if quality_score else 1.0)
            
            if YIELD_MEMORY_AVAILABLE:
                store_pattern(
                    username=self.username,
                    pattern_type=pending.get("task_category", "general"),
                    context=context or pending.get("context", {}),
                    action={"prompt_summary": pending.get("prompt_summary")},
                    outcome={"roas": roas, "quality_score": quality_score, "revenue_usd": revenue_generated},
                    ai_model=pending.get("model"),
                    task_category=pending.get("task_category")
                )
            
            if METAHIVE_AVAILABLE and roas >= 1.5:
                asyncio.create_task(contribute_to_hive(
                    username=self.username,
                    pattern_type=pending.get("task_category", "general"),
                    context=context or pending.get("context", {}),
                    action={"prompt_summary": pending.get("prompt_summary")},
                    outcome={"roas": roas, "quality_score": quality_score, "revenue_usd": revenue_generated},
                    ai_model=pending.get("model"),
                    task_category=pending.get("task_category")
                ))
            
            self._pending_results = [r for r in self._pending_results if r.get("task_id") != task_id]
    
    async def run_learning_sync(self) -> Dict[str, Any]:
        """Run full learning synchronization across all layers."""
        
        print("\n" + "=" * 70)
        print("🧠 AI FAMILY LEARNING SYNC")
        print("=" * 70)
        
        results = {"started_at": _now(), "brain_stats": None, "metahive_stats": None,
                   "yield_stats": None, "synergy": None, "exports": {}, "imports": {}}
        
        if AI_FAMILY_AVAILABLE:
            results["brain_stats"] = get_family_stats()
            results["synergy"] = get_synergy_score()
            print(f"   🧠 Synergy: {results['synergy'].get('synergy_score', 0):.3f}")
            print(f"   📚 Teachings: {results['synergy'].get('teachings', 0)}")
        
        if AI_FAMILY_AVAILABLE and METAHIVE_AVAILABLE:
            try:
                family_export = brain_export_metahive()
                if family_export:
                    import_result = hive_import_family(family_export)
                    results["exports"]["brain_to_metahive"] = import_result
                    print(f"   ➡️  Exported to MetaHive")
            except Exception as e:
                print(f"   ❌ Export error: {e}")
        
        if METAHIVE_AVAILABLE and AI_FAMILY_AVAILABLE:
            try:
                hive_export = hive_export_family()
                if hive_export.get("ok"):
                    brain_import_metahive(hive_export)
                    results["imports"]["metahive_to_brain"] = True
                    print(f"   ⬅️  Imported from MetaHive")
            except Exception as e:
                print(f"   ❌ Import error: {e}")
        
        if YIELD_MEMORY_AVAILABLE and METAHIVE_AVAILABLE:
            try:
                patterns = yield_export_hive(self.username)
                for p in patterns[:10]:
                    await contribute_to_hive(
                        username=self.username, pattern_type=p.get("pattern_type", "general"),
                        context=p.get("context", {}), action=p.get("action", {}),
                        outcome=p.get("outcome", {}), ai_model=p.get("ai_model"),
                        task_category=p.get("task_category")
                    )
                results["exports"]["yield_to_metahive"] = len(patterns)
                print(f"   ➡️  Contributed {len(patterns)} from Yield Memory")
            except Exception as e:
                print(f"   ❌ Yield export error: {e}")
        
        if METAHIVE_AVAILABLE:
            results["metahive_stats"] = get_hive_stats()
            print(f"   🐝 MetaHive: {results['metahive_stats'].get('total_patterns', 0)} patterns")
        
        if YIELD_MEMORY_AVAILABLE:
            results["yield_stats"] = get_memory_stats(self.username)
            print(f"   👤 Yield: {results['yield_stats'].get('total_patterns', 0)} patterns")
        
        results["completed_at"] = _now()
        self._last_sync = _now()
        print(f"✅ Learning sync complete")
        print("=" * 70)
        
        return results
    
    def get_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive AI Family dashboard."""
        
        dashboard = {
            "timestamp": _now(),
            "status": {"brain": AI_FAMILY_AVAILABLE, "metahive": METAHIVE_AVAILABLE, "yield": YIELD_MEMORY_AVAILABLE},
            "family": get_family_stats() if AI_FAMILY_AVAILABLE else None,
            "synergy": get_synergy_score() if AI_FAMILY_AVAILABLE else None,
            "hive": get_hive_stats() if METAHIVE_AVAILABLE else None,
            "user": get_memory_stats(self.username) if YIELD_MEMORY_AVAILABLE else None,
            "pending": len(self._pending_results),
            "last_sync": self._last_sync
        }
        return dashboard


# Singleton and convenience functions
_integration: Optional[AIFamilyIntegration] = None

def get_integration(username: str = "aigentsy") -> AIFamilyIntegration:
    global _integration
    if _integration is None:
        _integration = AIFamilyIntegration(username)
    return _integration

async def execute_with_family(prompt: str, task_type: str = "content_generation",
                              context: Dict = None, optimize_for: str = "balanced") -> Dict[str, Any]:
    return await get_integration().execute(prompt, task_type, context, optimize_for)

async def run_family_learning_sync(username: str = "aigentsy") -> Dict[str, Any]:
    return await get_integration(username).run_learning_sync()

def get_family_dashboard(username: str = "aigentsy") -> Dict[str, Any]:
    return get_integration(username).get_dashboard()

def record_family_outcome(task_id: str, success: bool, quality: float = None,
                          revenue: float = None, context: Dict = None):
    get_integration().record_outcome(task_id, success, quality, revenue, context)


print("""
═══════════════════════════════════════════════════════════════════════════════
🔗 AI FAMILY INTEGRATION READY
═══════════════════════════════════════════════════════════════════════════════
   Use: execute_with_family() for AI operations
        run_family_learning_sync() for learning
        get_family_dashboard() for monitoring
═══════════════════════════════════════════════════════════════════════════════
""")
