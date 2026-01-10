"""
AIGENTSY MASTER RUNTIME
=======================
The central nervous system that makes all engines FIRE.

This is the missing piece that:
1. Triggers discovery on schedule
2. Routes opportunities to execution
3. Runs AMG cycles for revenue optimization
4. Posts monetizable content to social
5. Feeds learnings back to Yield Memory & MetaHive
6. Tracks outcomes through the funnel

ARCHITECTURE:
┌─────────────────────────────────────────────────────────────┐
│                   MASTER RUNTIME (This File)                │
│                                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│  │Discovery│  │Execute  │  │ Learn   │  │Monetize │       │
│  │ Engine  │→│ Router  │→│ Memory  │→│ Track   │       │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘       │
└─────────────────────────────────────────────────────────────┘

SCHEDULES:
- Every 15 min: Discovery scan
- Every 1 hour: AMG cycle + social posts
- Every 6 hours: R3 reallocation
- Daily: MetaHive sync + pattern compression

USAGE:
    # Run continuously
    python aigentsy_master_runtime.py
    
    # Run single cycle (for cron/GitHub Actions)
    python aigentsy_master_runtime.py --once
    
    # Run specific module
    python aigentsy_master_runtime.py --discovery
    python aigentsy_master_runtime.py --execute
    python aigentsy_master_runtime.py --social
"""

import asyncio
import os
import sys
import json
import argparse
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import signal


def _now() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"


def _now_dt() -> datetime:
    return datetime.now(timezone.utc)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class RuntimeConfig:
    """Master runtime configuration"""
    
    # Discovery settings
    discovery_interval_minutes: int = 15
    discovery_dimensions: List[int] = field(default_factory=lambda: [1, 2, 3, 4])
    discovery_platforms: List[str] = field(default_factory=lambda: [
        'github', 'reddit', 'twitter', 'upwork'
    ])
    
    # Execution settings
    auto_execute_threshold: float = 0.75  # Win probability threshold
    max_parallel_executions: int = 5
    execution_cooldown_minutes: int = 5
    
    # Social posting settings
    social_interval_minutes: int = 60
    social_platforms: List[str] = field(default_factory=lambda: ['twitter'])
    posts_per_cycle: int = 2
    
    # AMG settings
    amg_cycle_interval_minutes: int = 60
    
    # Learning settings
    metahive_sync_interval_hours: int = 24
    yield_memory_compress_interval_hours: int = 6
    
    # R3 settings
    r3_reallocation_interval_hours: int = 6


DEFAULT_CONFIG = RuntimeConfig()


# =============================================================================
# SYSTEM IMPORTS (with graceful fallbacks)
# =============================================================================

# Discovery
try:
    from alpha_discovery_engine import AlphaDiscoveryEngine
    DISCOVERY_AVAILABLE = True
except ImportError:
    DISCOVERY_AVAILABLE = False
    print("⚠️ alpha_discovery_engine not available")

# Platform APIs (Real)
try:
    from platform_apis_REAL import get_platform_router, PlatformExecutorRouter
    PLATFORM_APIS_AVAILABLE = True
except ImportError:
    try:
        from platform_apis import PlatformExecutorRouter
        PLATFORM_APIS_AVAILABLE = True
        def get_platform_router():
            return PlatformExecutorRouter()
    except ImportError:
        PLATFORM_APIS_AVAILABLE = False
        print("⚠️ platform_apis not available")

# Execution
try:
    from execution_orchestrator import ExecutionOrchestrator
    EXECUTION_AVAILABLE = True
except ImportError:
    EXECUTION_AVAILABLE = False
    print("⚠️ execution_orchestrator not available")

# AMG
try:
    from amg_orchestrator import AMGOrchestrator
    AMG_AVAILABLE = True
except ImportError:
    AMG_AVAILABLE = False
    print("⚠️ amg_orchestrator not available")

# Learning
try:
    from yield_memory import store_pattern, get_best_action, get_memory_stats, compress_memory
    YIELD_MEMORY_AVAILABLE = True
except ImportError:
    YIELD_MEMORY_AVAILABLE = False
    print("⚠️ yield_memory not available")

try:
    from metahive_brain import contribute_to_hive, query_hive, get_hive_stats
    METAHIVE_AVAILABLE = True
except ImportError:
    METAHIVE_AVAILABLE = False
    print("⚠️ metahive_brain not available")

# Tracking
try:
    from outcome_oracle_max import on_event, get_user_funnel_stats
    OUTCOME_TRACKING_AVAILABLE = True
except ImportError:
    OUTCOME_TRACKING_AVAILABLE = False
    print("⚠️ outcome_oracle_max not available")

# Pricing
try:
    from pricing_oracle import calculate_dynamic_price, recommend_price_for_opportunity
    PRICING_AVAILABLE = True
except ImportError:
    PRICING_AVAILABLE = False
    print("⚠️ pricing_oracle not available")

# Social
try:
    from social_autoposting_engine import get_social_engine
    SOCIAL_AVAILABLE = True
except ImportError:
    SOCIAL_AVAILABLE = False
    print("⚠️ social_autoposting_engine not available")

# Conductor
try:
    from aigentsy_conductor import get_conductor, run_autonomous_cycle
    CONDUCTOR_AVAILABLE = True
except ImportError:
    CONDUCTOR_AVAILABLE = False
    print("⚠️ aigentsy_conductor not available")


# =============================================================================
# MASTER RUNTIME CLASS
# =============================================================================

class AiGentsyMasterRuntime:
    """
    The central orchestrator that makes all AiGentsy systems work together.
    """
    
    def __init__(self, config: RuntimeConfig = None):
        self.config = config or DEFAULT_CONFIG
        
        # State tracking
        self.cycle_count = 0
        self.last_discovery = None
        self.last_amg_cycle = None
        self.last_social_post = None
        self.last_r3_allocation = None
        self.last_metahive_sync = None
        
        # Statistics
        self.stats = {
            'total_opportunities_discovered': 0,
            'total_opportunities_executed': 0,
            'total_revenue_generated': 0.0,
            'total_posts_made': 0,
            'started_at': _now()
        }
        
        # Running state
        self._running = False
        self._shutdown_event = asyncio.Event()
        
        print("\n" + "=" * 70)
        print("🚀 AIGENTSY MASTER RUNTIME INITIALIZED")
        print("=" * 70)
        self._print_system_status()
    
    def _print_system_status(self):
        """Print status of all subsystems"""
        
        print("\n📊 SUBSYSTEM STATUS:")
        
        systems = [
            ("Discovery Engine", DISCOVERY_AVAILABLE),
            ("Platform APIs", PLATFORM_APIS_AVAILABLE),
            ("Execution Orchestrator", EXECUTION_AVAILABLE),
            ("AMG Orchestrator", AMG_AVAILABLE),
            ("Yield Memory", YIELD_MEMORY_AVAILABLE),
            ("MetaHive Brain", METAHIVE_AVAILABLE),
            ("Outcome Tracking", OUTCOME_TRACKING_AVAILABLE),
            ("Pricing Oracle", PRICING_AVAILABLE),
            ("Social Engine", SOCIAL_AVAILABLE),
            ("Conductor", CONDUCTOR_AVAILABLE),
        ]
        
        for name, available in systems:
            status = "✅" if available else "❌"
            print(f"   {status} {name}")
        
        # Platform API status
        if PLATFORM_APIS_AVAILABLE:
            print("\n📡 PLATFORM API STATUS:")
            router = get_platform_router()
            platform_status = router.get_platform_status()
            for platform, info in platform_status.items():
                status = "✅" if info.get('configured') else "❌"
                print(f"   {status} {platform}")
        
        print()
    
    # =========================================================================
    # DISCOVERY MODULE
    # =========================================================================
    
    async def run_discovery(self) -> Dict[str, Any]:
        """
        Run discovery across all configured platforms
        
        Returns opportunities found and routed
        """
        
        print("\n" + "=" * 70)
        print("🔍 DISCOVERY CYCLE")
        print(f"   Timestamp: {_now()}")
        print("=" * 70)
        
        if not DISCOVERY_AVAILABLE:
            print("   ⚠️ Discovery engine not available")
            return {'ok': False, 'error': 'discovery_not_available'}
        
        try:
            engine = AlphaDiscoveryEngine()
            
            results = await engine.discover_and_route(
                platforms=self.config.discovery_platforms,
                dimensions=self.config.discovery_dimensions,
                score_opportunities=True,
                auto_execute=False  # We'll handle execution ourselves
            )
            
            self.last_discovery = _now()
            self.stats['total_opportunities_discovered'] += results.get('total_opportunities', 0)
            
            print(f"\n✅ Discovery complete: {results.get('total_opportunities', 0)} opportunities")
            
            return results
            
        except Exception as e:
            print(f"❌ Discovery error: {e}")
            return {'ok': False, 'error': str(e)}
    
    # =========================================================================
    # EXECUTION MODULE
    # =========================================================================
    
    async def execute_opportunities(
        self,
        opportunities: List[Dict],
        auto_approve: bool = True
    ) -> Dict[str, Any]:
        """
        Execute opportunities through platform APIs
        """
        
        print("\n" + "=" * 70)
        print("⚡ EXECUTION CYCLE")
        print(f"   Opportunities to process: {len(opportunities)}")
        print("=" * 70)
        
        if not PLATFORM_APIS_AVAILABLE:
            print("   ⚠️ Platform APIs not available")
            return {'ok': False, 'error': 'platform_apis_not_available'}
        
        router = get_platform_router()
        
        results = {
            'executed': 0,
            'failed': 0,
            'skipped': 0,
            'executions': []
        }
        
        for opp in opportunities:
            # Check win probability threshold
            win_prob = opp.get('routing', {}).get('execution_score', {}).get('win_probability', 0)
            
            if win_prob < self.config.auto_execute_threshold:
                results['skipped'] += 1
                continue
            
            # Execute
            try:
                exec_result = await router.execute_opportunity(opp.get('opportunity', opp))
                
                if exec_result.get('ok'):
                    results['executed'] += 1
                    
                    # Track outcome
                    if OUTCOME_TRACKING_AVAILABLE:
                        on_event({
                            'kind': 'OPPORTUNITY_EXECUTED',
                            'username': 'aigentsy',
                            'opportunity_id': opp.get('id'),
                            'platform': exec_result.get('platform'),
                            'timestamp': _now()
                        })
                    
                    # Store pattern in yield memory
                    if YIELD_MEMORY_AVAILABLE:
                        store_pattern(
                            username='aigentsy',
                            pattern_type='execution',
                            context={
                                'platform': exec_result.get('platform'),
                                'opportunity_type': opp.get('type'),
                                'value': opp.get('value', 0)
                            },
                            action={'executed': True},
                            outcome={'status': 'pending'}
                        )
                else:
                    results['failed'] += 1
                
                results['executions'].append(exec_result)
                
                # Cooldown between executions
                await asyncio.sleep(self.config.execution_cooldown_minutes * 60 / 10)
                
            except Exception as e:
                print(f"   ❌ Execution error: {e}")
                results['failed'] += 1
        
        self.stats['total_opportunities_executed'] += results['executed']
        
        print(f"\n✅ Execution complete: {results['executed']} executed, {results['failed']} failed, {results['skipped']} skipped")
        
        return results
    
    # =========================================================================
    # SOCIAL POSTING MODULE
    # =========================================================================
    
    async def run_social_cycle(self) -> Dict[str, Any]:
        """
        Generate and post monetizable content to social platforms
        """
        
        print("\n" + "=" * 70)
        print("📱 SOCIAL POSTING CYCLE")
        print("=" * 70)
        
        if not SOCIAL_AVAILABLE:
            print("   ⚠️ Social engine not available")
            return {'ok': False, 'error': 'social_not_available'}
        
        results = {
            'posts_created': 0,
            'posts_failed': 0,
            'posts': []
        }
        
        try:
            engine = get_social_engine()
            
            # Generate monetizable content topics
            topics = [
                "AI automation tip of the day",
                "How to save 10 hours/week with automation",
                "The future of work is autonomous",
                "Stop trading time for money",
            ]
            
            for i, topic in enumerate(topics[:self.config.posts_per_cycle]):
                for platform in self.config.social_platforms:
                    try:
                        result = await engine.create_and_post(
                            user_id='aigentsy',
                            platform=platform,
                            content_type='text',
                            topic=topic,
                            style='engaging'
                        )
                        
                        if result.get('success'):
                            results['posts_created'] += 1
                        else:
                            results['posts_failed'] += 1
                        
                        results['posts'].append(result)
                        
                    except Exception as e:
                        print(f"   ❌ Post error ({platform}): {e}")
                        results['posts_failed'] += 1
            
            self.last_social_post = _now()
            self.stats['total_posts_made'] += results['posts_created']
            
            print(f"\n✅ Social cycle complete: {results['posts_created']} posts created")
            
        except Exception as e:
            print(f"❌ Social cycle error: {e}")
            results['error'] = str(e)
        
        return results
    
    # =========================================================================
    # AMG CYCLE MODULE
    # =========================================================================
    
    async def run_amg_cycle(self) -> Dict[str, Any]:
        """
        Run AMG (App Monetization Graph) optimization cycle
        
        10 stages: SENSE → SCORE → PRICE → BUDGET → FINANCE → 
                   ROUTE → ASSURE → SETTLE → ATTRIBUTE → RE-ALLOCATE
        """
        
        print("\n" + "=" * 70)
        print("💰 AMG CYCLE")
        print("=" * 70)
        
        if not AMG_AVAILABLE:
            print("   ⚠️ AMG orchestrator not available")
            return {'ok': False, 'error': 'amg_not_available'}
        
        try:
            orchestrator = AMGOrchestrator()
            
            # Initialize graph if needed
            orchestrator.initialize_graph()
            
            # Run full cycle
            result = await orchestrator.run_cycle()
            
            self.last_amg_cycle = _now()
            
            print(f"\n✅ AMG cycle complete")
            
            return result
            
        except Exception as e:
            print(f"❌ AMG cycle error: {e}")
            return {'ok': False, 'error': str(e)}
    
    # =========================================================================
    # LEARNING MODULE
    # =========================================================================
    
    async def run_learning_sync(self) -> Dict[str, Any]:
        """
        Sync learnings to MetaHive and compress Yield Memory
        """
        
        print("\n" + "=" * 70)
        print("🧠 LEARNING SYNC")
        print("=" * 70)
        
        results = {
            'yield_memory_compressed': False,
            'metahive_synced': False
        }
        
        # Compress Yield Memory
        if YIELD_MEMORY_AVAILABLE:
            try:
                stats = get_memory_stats('aigentsy')
                print(f"   Yield Memory: {stats.get('total_patterns', 0)} patterns")
                
                if stats.get('total_patterns', 0) > 80:
                    compress_memory('aigentsy')
                    results['yield_memory_compressed'] = True
                    print("   ✅ Yield Memory compressed")
                    
            except Exception as e:
                print(f"   ⚠️ Yield Memory error: {e}")
        
        # Sync to MetaHive
        if METAHIVE_AVAILABLE:
            try:
                stats = get_hive_stats()
                print(f"   MetaHive: {stats.get('total_patterns', 0)} shared patterns")
                results['metahive_synced'] = True
                
            except Exception as e:
                print(f"   ⚠️ MetaHive error: {e}")
        
        self.last_metahive_sync = _now()
        
        return results
    
    # =========================================================================
    # MAIN CYCLE
    # =========================================================================
    
    async def run_full_cycle(self) -> Dict[str, Any]:
        """
        Run a complete cycle of all systems
        """
        
        self.cycle_count += 1
        
        print("\n" + "=" * 70)
        print(f"🔄 FULL CYCLE #{self.cycle_count}")
        print(f"   Started: {_now()}")
        print("=" * 70)
        
        results = {
            'cycle': self.cycle_count,
            'started_at': _now(),
            'phases': {}
        }
        
        # Phase 1: Discovery
        discovery_result = await self.run_discovery()
        results['phases']['discovery'] = discovery_result
        
        # Phase 2: Execute high-confidence opportunities
        if discovery_result.get('ok'):
            routing = discovery_result.get('routing', {})
            
            # Get opportunities to execute
            opportunities_to_execute = []
            
            for category in ['aigentsy_routed', 'user_routed']:
                category_opps = routing.get(category, {}).get('opportunities', [])
                opportunities_to_execute.extend(category_opps)
            
            if opportunities_to_execute:
                exec_result = await self.execute_opportunities(opportunities_to_execute)
                results['phases']['execution'] = exec_result
        
        # Phase 3: Social posting (if interval elapsed)
        if self._should_run_social():
            social_result = await self.run_social_cycle()
            results['phases']['social'] = social_result
        
        # Phase 4: AMG cycle (if interval elapsed)
        if self._should_run_amg():
            amg_result = await self.run_amg_cycle()
            results['phases']['amg'] = amg_result
        
        # Phase 5: Learning sync (if interval elapsed)
        if self._should_run_learning():
            learning_result = await self.run_learning_sync()
            results['phases']['learning'] = learning_result
        
        results['completed_at'] = _now()
        results['stats'] = self.stats
        
        print("\n" + "=" * 70)
        print(f"✅ CYCLE #{self.cycle_count} COMPLETE")
        print(f"   Total opportunities discovered: {self.stats['total_opportunities_discovered']}")
        print(f"   Total opportunities executed: {self.stats['total_opportunities_executed']}")
        print(f"   Total posts made: {self.stats['total_posts_made']}")
        print("=" * 70)
        
        return results
    
    def _should_run_social(self) -> bool:
        """Check if social posting interval has elapsed"""
        if not self.last_social_post:
            return True
        
        last = datetime.fromisoformat(self.last_social_post.replace('Z', '+00:00'))
        elapsed = (_now_dt() - last).total_seconds() / 60
        return elapsed >= self.config.social_interval_minutes
    
    def _should_run_amg(self) -> bool:
        """Check if AMG cycle interval has elapsed"""
        if not self.last_amg_cycle:
            return True
        
        last = datetime.fromisoformat(self.last_amg_cycle.replace('Z', '+00:00'))
        elapsed = (_now_dt() - last).total_seconds() / 60
        return elapsed >= self.config.amg_cycle_interval_minutes
    
    def _should_run_learning(self) -> bool:
        """Check if learning sync interval has elapsed"""
        if not self.last_metahive_sync:
            return True
        
        last = datetime.fromisoformat(self.last_metahive_sync.replace('Z', '+00:00'))
        elapsed = (_now_dt() - last).total_seconds() / 3600
        return elapsed >= self.config.metahive_sync_interval_hours
    
    # =========================================================================
    # CONTINUOUS RUNNING
    # =========================================================================
    
    async def run_continuous(self):
        """
        Run the master runtime continuously
        """
        
        print("\n🚀 Starting continuous runtime...")
        print(f"   Discovery interval: {self.config.discovery_interval_minutes} minutes")
        print(f"   Press Ctrl+C to stop\n")
        
        self._running = True
        
        while self._running:
            try:
                # Run full cycle
                await self.run_full_cycle()
                
                # Wait for next cycle
                print(f"\n⏳ Waiting {self.config.discovery_interval_minutes} minutes until next cycle...")
                
                try:
                    await asyncio.wait_for(
                        self._shutdown_event.wait(),
                        timeout=self.config.discovery_interval_minutes * 60
                    )
                    break  # Shutdown requested
                except asyncio.TimeoutError:
                    pass  # Continue to next cycle
                    
            except KeyboardInterrupt:
                print("\n\n🛑 Shutdown requested...")
                break
            except Exception as e:
                print(f"\n❌ Cycle error: {e}")
                print("   Waiting 60 seconds before retry...")
                await asyncio.sleep(60)
        
        self._running = False
        print("\n👋 Master runtime stopped.")
    
    def stop(self):
        """Signal the runtime to stop"""
        self._running = False
        self._shutdown_event.set()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get runtime statistics"""
        return {
            **self.stats,
            'cycle_count': self.cycle_count,
            'last_discovery': self.last_discovery,
            'last_amg_cycle': self.last_amg_cycle,
            'last_social_post': self.last_social_post,
            'last_metahive_sync': self.last_metahive_sync,
            'running': self._running
        }


# =============================================================================
# SINGLETON
# =============================================================================

_runtime: Optional[AiGentsyMasterRuntime] = None


def get_master_runtime(config: RuntimeConfig = None) -> AiGentsyMasterRuntime:
    """Get or create the master runtime singleton"""
    global _runtime
    if _runtime is None:
        _runtime = AiGentsyMasterRuntime(config)
    return _runtime


# =============================================================================
# CLI
# =============================================================================

async def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(description='AiGentsy Master Runtime')
    parser.add_argument('--once', action='store_true', help='Run single cycle and exit')
    parser.add_argument('--discovery', action='store_true', help='Run only discovery')
    parser.add_argument('--execute', action='store_true', help='Run only execution')
    parser.add_argument('--social', action='store_true', help='Run only social posting')
    parser.add_argument('--amg', action='store_true', help='Run only AMG cycle')
    parser.add_argument('--learning', action='store_true', help='Run only learning sync')
    parser.add_argument('--status', action='store_true', help='Show system status')
    
    args = parser.parse_args()
    
    runtime = get_master_runtime()
    
    # Handle specific modules
    if args.status:
        runtime._print_system_status()
        return
    
    if args.discovery:
        await runtime.run_discovery()
        return
    
    if args.execute:
        # Would need opportunities from discovery first
        print("Execute mode requires discovery results. Use --once instead.")
        return
    
    if args.social:
        await runtime.run_social_cycle()
        return
    
    if args.amg:
        await runtime.run_amg_cycle()
        return
    
    if args.learning:
        await runtime.run_learning_sync()
        return
    
    if args.once:
        await runtime.run_full_cycle()
        return
    
    # Default: run continuously
    # Setup signal handlers
    def signal_handler(sig, frame):
        print("\n\n🛑 Shutdown signal received...")
        runtime.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    await runtime.run_continuous()


if __name__ == "__main__":
    asyncio.run(main())
