"""
SYSTEM HEALTH DETAIL - Detailed health check for debugging
Returns specific broken systems with error messages
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import traceback


class SystemHealthDetail:
    """
    Detailed health checker that tracks individual system failures
    Extends the quick health check with specific error details
    """
    
    def __init__(self):
        self.system_registry = {}
        self.last_check_time = None
        self.last_errors = {}
    
    def register_system(
        self, 
        system_id: str, 
        check_function: callable,
        category: str = "general"
    ):
        """
        Register a system for health checking
        
        Args:
            system_id: Unique identifier (e.g., "source.github.scraper")
            check_function: Async or sync function that returns True if healthy
            category: Category for grouping (e.g., "discovery", "payment", "storage")
        """
        self.system_registry[system_id] = {
            "id": system_id,
            "check": check_function,
            "category": category,
            "status": "unknown",
            "last_error": None,
            "last_check": None
        }
    
    async def check_system(self, system_id: str) -> Dict[str, Any]:
        """
        Check health of a single system
        
        Returns:
            {
                "id": "system_id",
                "healthy": True/False,
                "error": "error message if unhealthy",
                "checked_at": "timestamp"
            }
        """
        if system_id not in self.system_registry:
            return {
                "id": system_id,
                "healthy": False,
                "error": "System not registered",
                "checked_at": datetime.now(timezone.utc).isoformat()
            }
        
        system = self.system_registry[system_id]
        
        try:
            # Run the check function
            check_func = system["check"]
            
            # Handle async checks
            if hasattr(check_func, '__call__'):
                if asyncio.iscoroutinefunction(check_func):
                    result = await check_func()
                else:
                    result = check_func()
            else:
                result = True
            
            # Update status
            system["status"] = "healthy" if result else "broken"
            system["last_error"] = None if result else "Check returned False"
            system["last_check"] = datetime.now(timezone.utc).isoformat()
            
            return {
                "id": system_id,
                "healthy": result,
                "error": None if result else "Check returned False",
                "checked_at": system["last_check"]
            }
            
        except Exception as e:
            # Capture error details
            error_msg = f"{type(e).__name__}: {str(e)}"
            system["status"] = "broken"
            system["last_error"] = error_msg
            system["last_check"] = datetime.now(timezone.utc).isoformat()
            
            return {
                "id": system_id,
                "healthy": False,
                "error": error_msg,
                "traceback": traceback.format_exc(),
                "checked_at": system["last_check"]
            }
    
    async def check_all_systems(self) -> Dict[str, Any]:
        """
        Check health of all registered systems
        
        Returns:
            Detailed health report with all systems and their statuses
        """
        import asyncio
        
        # Check all systems
        check_tasks = [
            self.check_system(system_id)
            for system_id in self.system_registry.keys()
        ]
        
        results = await asyncio.gather(*check_tasks, return_exceptions=True)
        
        # Categorize results
        healthy_systems = []
        broken_systems = []
        stub_systems = []
        unknown_systems = []
        
        for result in results:
            if isinstance(result, Exception):
                broken_systems.append({
                    "id": "unknown",
                    "error": str(result),
                    "category": "error"
                })
                continue
            
            system_info = self.system_registry.get(result["id"], {})
            result["category"] = system_info.get("category", "unknown")
            
            if result["healthy"]:
                healthy_systems.append(result)
            elif result.get("error") == "Not implemented - stub":
                stub_systems.append(result)
            else:
                broken_systems.append(result)
        
        # Calculate totals
        total = len(self.system_registry)
        working = len(healthy_systems)
        broken = len(broken_systems)
        stub = len(stub_systems)
        
        self.last_check_time = datetime.now(timezone.utc).isoformat()
        
        return {
            "ok": True,
            "checked_at": self.last_check_time,
            "summary": {
                "total": total,
                "working": working,
                "broken": broken,
                "stub": stub,
                "working_percentage": round((working / total * 100), 2) if total > 0 else 0
            },
            "healthy_systems": healthy_systems,
            "broken_systems": broken_systems,
            "stub_systems": stub_systems,
            "categories": self._categorize_systems(healthy_systems, broken_systems, stub_systems)
        }
    
    def _categorize_systems(
        self, 
        healthy: List[Dict], 
        broken: List[Dict], 
        stub: List[Dict]
    ) -> Dict[str, Dict[str, int]]:
        """Group systems by category with counts"""
        categories = {}
        
        for system in healthy + broken + stub:
            cat = system.get("category", "unknown")
            if cat not in categories:
                categories[cat] = {"total": 0, "healthy": 0, "broken": 0, "stub": 0}
            
            categories[cat]["total"] += 1
            if system in healthy:
                categories[cat]["healthy"] += 1
            elif system in broken:
                categories[cat]["broken"] += 1
            elif system in stub:
                categories[cat]["stub"] += 1
        
        return categories
    
    def get_broken_systems_summary(self) -> List[Dict[str, str]]:
        """
        Get a clean summary of just the broken systems
        Perfect for quick debugging
        
        Returns:
            [
                {"id": "source.github.scraper", "error": "403 Forbidden", "category": "discovery"},
                ...
            ]
        """
        broken = []
        
        for system_id, system in self.system_registry.items():
            if system["status"] == "broken" and system["last_error"]:
                broken.append({
                    "id": system_id,
                    "error": system["last_error"],
                    "category": system.get("category", "unknown"),
                    "last_check": system.get("last_check")
                })
        
        return broken


# Example system checks (these would be replaced with real checks)

def check_jsonbin_write():
    """Check if JSONBin write is working"""
    try:
        # Placeholder - real implementation would test JSONBin
        return True
    except Exception as e:
        raise Exception(f"JSONBin write failed: {e}")


def check_github_scraper():
    """Check if GitHub scraper is working"""
    try:
        # Placeholder - real implementation would test GitHub API
        # Example failure simulation:
        # raise Exception("403 Forbidden - Rate limited")
        return True
    except Exception as e:
        raise Exception(f"GitHub scraper failed: {e}")


def check_proposal_inbox():
    """Check if proposal inbox is operational"""
    try:
        # Placeholder - real implementation would test inbox
        return True
    except Exception as e:
        raise Exception(f"Proposal inbox failed: {e}")


def check_stripe_connect():
    """Check if Stripe Connect is operational"""
    try:
        # Placeholder - real implementation would test Stripe
        return True
    except Exception as e:
        raise Exception(f"Stripe Connect failed: {e}")


def check_outcome_oracle():
    """Check if Outcome Oracle is operational"""
    try:
        # Placeholder - real implementation would test oracle
        return True
    except Exception as e:
        raise Exception(f"Outcome Oracle failed: {e}")


# Create global health checker instance
health_checker = SystemHealthDetail()

# Register example systems (these would be registered in main.py)
health_checker.register_system("storage.jsonbin.write", check_jsonbin_write, "storage")
health_checker.register_system("source.github.scraper", check_github_scraper, "discovery")
health_checker.register_system("proposal.inbox.emit", check_proposal_inbox, "workflow")
health_checker.register_system("payment.stripe.connect", check_stripe_connect, "payment")
health_checker.register_system("analytics.outcome.oracle", check_outcome_oracle, "analytics")


# FastAPI route example (to be added to main.py)
"""
@router.get("/execution/health/detail")
async def health_detail():
    '''
    Detailed health check showing exactly which systems are broken
    
    Returns:
        - summary: Quick stats (total, working, broken, stub)
        - broken_systems: List of systems with errors
        - healthy_systems: List of working systems
        - categories: Systems grouped by category
    '''
    from system_health_detail import health_checker
    
    result = await health_checker.check_all_systems()
    return result


@router.get("/execution/health/broken")
async def health_broken_only():
    '''
    Just the broken systems for quick debugging
    
    Returns:
        List of broken systems with error messages
    '''
    from system_health_detail import health_checker
    
    broken = health_checker.get_broken_systems_summary()
    return {
        "ok": True,
        "broken_count": len(broken),
        "broken_systems": broken
    }
"""


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("=" * 80)
        print("TESTING SYSTEM HEALTH DETAIL")
        print("=" * 80)
        
        # Run full health check
        result = await health_checker.check_all_systems()
        
        print(f"\nSUMMARY:")
        print(f"  Total systems: {result['summary']['total']}")
        print(f"  Working: {result['summary']['working']}")
        print(f"  Broken: {result['summary']['broken']}")
        print(f"  Stub: {result['summary']['stub']}")
        print(f"  Health: {result['summary']['working_percentage']:.1f}%")
        
        if result['broken_systems']:
            print(f"\nBROKEN SYSTEMS ({len(result['broken_systems'])}):")
            for system in result['broken_systems']:
                print(f"  ❌ {system['id']}")
                print(f"     Error: {system['error']}")
                print(f"     Category: {system['category']}")
        
        if result['healthy_systems']:
            print(f"\nHEALTHY SYSTEMS ({len(result['healthy_systems'])}):")
            for system in result['healthy_systems']:
                print(f"  ✅ {system['id']} ({system['category']})")
        
        print(f"\nCATEGORIES:")
        for cat, stats in result['categories'].items():
            print(f"  {cat}: {stats['healthy']}/{stats['total']} healthy")
        
        # Test broken summary
        print(f"\nBROKEN SUMMARY:")
        broken = health_checker.get_broken_systems_summary()
        for system in broken:
            print(f"  - {system['id']}: {system['error']}")
    
    asyncio.run(test())
