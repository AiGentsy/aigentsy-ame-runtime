"""
FEATURE FLAGS: Gradual Rollout System

Features:
- Boolean flags
- Percentage rollouts
- User/segment targeting
- Environment overrides
"""

import logging
import hashlib
import os
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class FeatureFlag:
    """Feature flag definition"""
    name: str
    enabled: bool = False
    rollout_percentage: int = 0  # 0-100
    description: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    targets: List[str] = field(default_factory=list)  # Specific user/segment IDs
    environment: Optional[str] = None  # Restrict to specific env


# Default flags
DEFAULT_FLAGS: Dict[str, Dict] = {
    # Discovery flags
    'discovery_v2': {
        'enabled': True,
        'rollout_percentage': 100,
        'description': 'Use v2 discovery pipeline',
    },
    'parallel_discovery': {
        'enabled': True,
        'rollout_percentage': 100,
        'description': 'Run platform discovery in parallel',
    },

    # Enrichment flags
    'llm_extraction': {
        'enabled': False,
        'rollout_percentage': 0,
        'description': 'Use LLM for zero-shot extraction',
    },
    'selector_healing': {
        'enabled': True,
        'rollout_percentage': 50,
        'description': 'Enable LLM-powered selector healing',
    },

    # Routing flags
    'fast_path_execution': {
        'enabled': True,
        'rollout_percentage': 100,
        'description': 'Enable fast-path for high-priority opportunities',
    },
    'thompson_sampling': {
        'enabled': True,
        'rollout_percentage': 100,
        'description': 'Use Thompson Sampling for routing',
    },

    # Execution flags
    'auto_execution': {
        'enabled': False,
        'rollout_percentage': 0,
        'description': 'Automatically execute high-confidence opportunities',
    },
    'browser_automation': {
        'enabled': True,
        'rollout_percentage': 100,
        'description': 'Use browser automation for execution',
    },

    # Safety flags
    'strict_compliance': {
        'enabled': True,
        'rollout_percentage': 100,
        'description': 'Enforce strict compliance checks',
    },
    'anti_abuse_v2': {
        'enabled': True,
        'rollout_percentage': 100,
        'description': 'Use v2 anti-abuse detection',
    },
}


class FeatureFlags:
    """
    Feature flag management system.

    Supports:
    - Boolean on/off
    - Percentage rollouts
    - Targeted rollouts
    - Environment-specific flags
    """

    def __init__(self, flags: Optional[Dict[str, Dict]] = None):
        self.flags: Dict[str, FeatureFlag] = {}

        # Load default flags
        for name, config in (flags or DEFAULT_FLAGS).items():
            self.flags[name] = FeatureFlag(
                name=name,
                enabled=config.get('enabled', False),
                rollout_percentage=config.get('rollout_percentage', 0),
                description=config.get('description', ''),
                targets=config.get('targets', []),
                environment=config.get('environment'),
            )

        # Environment overrides
        self._load_env_overrides()

        self.stats = {
            'checks': 0,
            'enabled_checks': 0,
            'disabled_checks': 0,
        }

    def _load_env_overrides(self):
        """Load flag overrides from environment variables"""
        # Pattern: FEATURE_FLAG_{NAME}=true/false
        for key, value in os.environ.items():
            if key.startswith('FEATURE_FLAG_'):
                flag_name = key[13:].lower()
                if flag_name in self.flags:
                    self.flags[flag_name].enabled = value.lower() in ('true', '1', 'yes')
                    logger.info(f"[feature_flags] Override from env: {flag_name}={value}")

    def is_enabled(
        self,
        flag_name: str,
        user_id: Optional[str] = None,
        default: bool = False
    ) -> bool:
        """
        Check if feature flag is enabled.

        Args:
            flag_name: Name of the flag
            user_id: Optional user/request ID for percentage rollout
            default: Default value if flag not found

        Returns:
            True if flag is enabled
        """
        self.stats['checks'] += 1

        if flag_name not in self.flags:
            return default

        flag = self.flags[flag_name]

        # Check environment restriction
        current_env = os.environ.get('ENVIRONMENT', 'development')
        if flag.environment and flag.environment != current_env:
            self.stats['disabled_checks'] += 1
            return False

        # Check if completely disabled
        if not flag.enabled:
            self.stats['disabled_checks'] += 1
            return False

        # Check targeted rollout
        if flag.targets and user_id:
            if user_id in flag.targets:
                self.stats['enabled_checks'] += 1
                return True

        # Check percentage rollout
        if flag.rollout_percentage < 100:
            if user_id:
                # Deterministic hash-based rollout
                hash_input = f"{flag_name}:{user_id}"
                hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
                bucket = hash_value % 100

                if bucket >= flag.rollout_percentage:
                    self.stats['disabled_checks'] += 1
                    return False
            else:
                # Random rollout without user ID
                import random
                if random.randint(0, 99) >= flag.rollout_percentage:
                    self.stats['disabled_checks'] += 1
                    return False

        self.stats['enabled_checks'] += 1
        return True

    def set_flag(
        self,
        flag_name: str,
        enabled: bool,
        rollout_percentage: Optional[int] = None
    ):
        """Set flag state"""
        if flag_name in self.flags:
            self.flags[flag_name].enabled = enabled
            if rollout_percentage is not None:
                self.flags[flag_name].rollout_percentage = rollout_percentage
        else:
            self.flags[flag_name] = FeatureFlag(
                name=flag_name,
                enabled=enabled,
                rollout_percentage=rollout_percentage or (100 if enabled else 0),
            )

        logger.info(f"[feature_flags] Set {flag_name}={enabled}")

    def add_target(self, flag_name: str, target: str):
        """Add target to flag's targeted rollout"""
        if flag_name in self.flags:
            if target not in self.flags[flag_name].targets:
                self.flags[flag_name].targets.append(target)

    def get_flag(self, flag_name: str) -> Optional[FeatureFlag]:
        """Get flag details"""
        return self.flags.get(flag_name)

    def list_flags(self) -> List[Dict]:
        """List all flags with their status"""
        return [
            {
                'name': f.name,
                'enabled': f.enabled,
                'rollout_percentage': f.rollout_percentage,
                'description': f.description,
                'targets_count': len(f.targets),
                'environment': f.environment,
            }
            for f in self.flags.values()
        ]

    def get_stats(self) -> Dict:
        """Get flag stats"""
        enabled_count = sum(1 for f in self.flags.values() if f.enabled)

        return {
            **self.stats,
            'total_flags': len(self.flags),
            'enabled_flags': enabled_count,
            'disabled_flags': len(self.flags) - enabled_count,
        }


# Singleton
_feature_flags: Optional[FeatureFlags] = None


def get_feature_flags() -> FeatureFlags:
    """Get or create feature flags instance"""
    global _feature_flags
    if _feature_flags is None:
        _feature_flags = FeatureFlags()
    return _feature_flags


def is_enabled(flag_name: str, user_id: Optional[str] = None, default: bool = False) -> bool:
    """Convenience function to check flag"""
    return get_feature_flags().is_enabled(flag_name, user_id, default)
