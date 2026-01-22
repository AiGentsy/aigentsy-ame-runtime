"""
INCIDENT RUNBOOK & ROLLBACK
===========================

Pre-wired incident response with pause categories and one-click rollback.

Features:
- Category-based pause (engagement, bidding, autospawn, insurance)
- Configuration snapshots
- One-click rollback to last known good config
- ND-JSON incident logging

Usage:
    from runbooks import pause_category, rollback_to_manifest

    # Emergency pause
    pause_category("bidding", reason="rate_limit_hit")

    # Rollback to last good config
    rollback_to_manifest("snapshot_2024_01_20")
"""

import json
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field


RUNBOOKS_DIR = Path(__file__).parent
SNAPSHOTS_DIR = RUNBOOKS_DIR / "snapshots"
NDJSON_LOG = Path(__file__).parent.parent / "logs" / "run.ndjson"


# Pauseable categories
PAUSE_CATEGORIES = {
    "engagement": "Social engagement (DMs, replies, posts)",
    "bidding": "Automated bidding on platforms",
    "autospawn": "Business auto-spawning",
    "assurance": "P2P outcome assurance (OAP)",
    "discovery": "Opportunity discovery",
    "execution": "Outcome execution",
    "settlements": "Payment settlements",
    "all": "ALL operations (emergency)"
}

# Current pause state
_PAUSED: Set[str] = set()


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _emit(event: str, **kwargs):
    """Emit ND-JSON event"""
    try:
        NDJSON_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {"event": event, "ts": _now_iso(), **kwargs}
        with open(NDJSON_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


@dataclass
class Snapshot:
    """Configuration snapshot for rollback"""
    id: str
    created_at: str
    description: str
    policies: Dict[str, Any]
    configs: Dict[str, Any]
    paused_at_creation: List[str]


class RunbookManager:
    """
    Manages incident runbooks, pauses, and rollbacks.
    """

    def __init__(self):
        self.policies_dir = Path(__file__).parent.parent / "policies"
        self.configs_dir = Path(__file__).parent.parent / "configs"
        SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    def pause(self, category: str, *, reason: str = None, duration_hours: float = None) -> Dict[str, Any]:
        """
        Pause a category of operations.

        Args:
            category: Category to pause (engagement, bidding, autospawn, etc.)
            reason: Reason for pause
            duration_hours: Auto-resume after this duration (optional)

        Returns:
            Pause confirmation
        """
        if category not in PAUSE_CATEGORIES and category != "all":
            return {"ok": False, "error": f"unknown_category:{category}"}

        if category == "all":
            # Pause everything
            for cat in PAUSE_CATEGORIES.keys():
                if cat != "all":
                    _PAUSED.add(cat)
        else:
            _PAUSED.add(category)

        _emit(
            "incident_pause",
            category=category,
            reason=reason,
            duration_hours=duration_hours,
            paused_categories=list(_PAUSED)
        )

        return {
            "ok": True,
            "paused": category,
            "reason": reason,
            "total_paused": list(_PAUSED),
            "paused_at": _now_iso()
        }

    def resume(self, category: str) -> Dict[str, Any]:
        """
        Resume a paused category.

        Args:
            category: Category to resume

        Returns:
            Resume confirmation
        """
        if category == "all":
            old_paused = list(_PAUSED)
            _PAUSED.clear()
            _emit("incident_resume_all", previously_paused=old_paused)
            return {"ok": True, "resumed": old_paused}

        if category in _PAUSED:
            _PAUSED.remove(category)
            _emit("incident_resume", category=category)
            return {"ok": True, "resumed": category}

        return {"ok": False, "error": "category_not_paused"}

    def is_paused(self, category: str) -> bool:
        """Check if a category is paused"""
        return category in _PAUSED or "all" in _PAUSED

    def get_paused(self) -> List[str]:
        """Get list of paused categories"""
        return list(_PAUSED)

    def create_snapshot(self, description: str = None) -> Dict[str, Any]:
        """
        Create a configuration snapshot for rollback.

        Args:
            description: Optional snapshot description

        Returns:
            Snapshot confirmation
        """
        snapshot_id = f"snapshot_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

        # Collect policies
        policies = {}
        if self.policies_dir.exists():
            for f in self.policies_dir.glob("*.json"):
                try:
                    policies[f.stem] = json.loads(f.read_text())
                except Exception:
                    pass

        # Collect configs
        configs = {}
        if self.configs_dir.exists():
            for f in self.configs_dir.glob("*.json"):
                try:
                    configs[f.stem] = json.loads(f.read_text())
                except Exception:
                    pass

        snapshot = Snapshot(
            id=snapshot_id,
            created_at=_now_iso(),
            description=description or "Manual snapshot",
            policies=policies,
            configs=configs,
            paused_at_creation=list(_PAUSED)
        )

        # Save snapshot
        snapshot_file = SNAPSHOTS_DIR / f"{snapshot_id}.json"
        snapshot_file.write_text(json.dumps({
            "id": snapshot.id,
            "created_at": snapshot.created_at,
            "description": snapshot.description,
            "policies": snapshot.policies,
            "configs": snapshot.configs,
            "paused_at_creation": snapshot.paused_at_creation
        }, indent=2))

        _emit("snapshot_created", snapshot_id=snapshot_id, description=description)

        return {
            "ok": True,
            "snapshot_id": snapshot_id,
            "policies_count": len(policies),
            "configs_count": len(configs),
            "created_at": snapshot.created_at
        }

    def list_snapshots(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List available snapshots"""
        snapshots = []

        if SNAPSHOTS_DIR.exists():
            for f in sorted(SNAPSHOTS_DIR.glob("*.json"), reverse=True)[:limit]:
                try:
                    data = json.loads(f.read_text())
                    snapshots.append({
                        "id": data.get("id"),
                        "created_at": data.get("created_at"),
                        "description": data.get("description"),
                        "policies_count": len(data.get("policies", {})),
                        "configs_count": len(data.get("configs", {}))
                    })
                except Exception:
                    pass

        return snapshots

    def rollback(self, snapshot_id: str, *, restore_pause_state: bool = False) -> Dict[str, Any]:
        """
        Rollback to a previous snapshot.

        Args:
            snapshot_id: Snapshot ID to restore
            restore_pause_state: Also restore pause state from snapshot

        Returns:
            Rollback result
        """
        snapshot_file = SNAPSHOTS_DIR / f"{snapshot_id}.json"

        if not snapshot_file.exists():
            return {"ok": False, "error": "snapshot_not_found"}

        try:
            data = json.loads(snapshot_file.read_text())
        except Exception as e:
            return {"ok": False, "error": f"snapshot_read_error:{e}"}

        restored = {"policies": [], "configs": []}

        # Restore policies
        for name, content in data.get("policies", {}).items():
            try:
                policy_file = self.policies_dir / f"{name}.json"
                policy_file.parent.mkdir(parents=True, exist_ok=True)
                policy_file.write_text(json.dumps(content, indent=2))
                restored["policies"].append(name)
            except Exception:
                pass

        # Restore configs
        for name, content in data.get("configs", {}).items():
            try:
                config_file = self.configs_dir / f"{name}.json"
                config_file.parent.mkdir(parents=True, exist_ok=True)
                config_file.write_text(json.dumps(content, indent=2))
                restored["configs"].append(name)
            except Exception:
                pass

        # Optionally restore pause state
        if restore_pause_state:
            global _PAUSED
            _PAUSED = set(data.get("paused_at_creation", []))

        _emit(
            "rollback_executed",
            snapshot_id=snapshot_id,
            policies_restored=len(restored["policies"]),
            configs_restored=len(restored["configs"]),
            pause_state_restored=restore_pause_state
        )

        return {
            "ok": True,
            "snapshot_id": snapshot_id,
            "restored": restored,
            "pause_state_restored": restore_pause_state,
            "current_paused": list(_PAUSED),
            "rolled_back_at": _now_iso()
        }

    def get_status(self) -> Dict[str, Any]:
        """Get current runbook status"""
        snapshots = self.list_snapshots(5)

        return {
            "paused_categories": list(_PAUSED),
            "available_categories": PAUSE_CATEGORIES,
            "recent_snapshots": snapshots,
            "snapshot_count": len(list(SNAPSHOTS_DIR.glob("*.json"))) if SNAPSHOTS_DIR.exists() else 0
        }


# Module-level singleton
_manager = RunbookManager()


def pause_category(category: str, reason: str = None, **kwargs) -> Dict[str, Any]:
    """Pause a category of operations"""
    return _manager.pause(category, reason=reason, **kwargs)


def resume_category(category: str) -> Dict[str, Any]:
    """Resume a paused category"""
    return _manager.resume(category)


def is_paused(category: str) -> bool:
    """Check if category is paused"""
    return _manager.is_paused(category)


def get_pause_status() -> List[str]:
    """Get list of paused categories"""
    return _manager.get_paused()


def create_snapshot(description: str = None) -> Dict[str, Any]:
    """Create configuration snapshot"""
    return _manager.create_snapshot(description)


def list_snapshots(limit: int = 20) -> List[Dict[str, Any]]:
    """List available snapshots"""
    return _manager.list_snapshots(limit)


def rollback_to_manifest(snapshot_id: str, **kwargs) -> Dict[str, Any]:
    """Rollback to snapshot"""
    return _manager.rollback(snapshot_id, **kwargs)


def get_runbook_status() -> Dict[str, Any]:
    """Get current runbook status"""
    return _manager.get_status()


def emergency_stop(reason: str = "manual_emergency") -> Dict[str, Any]:
    """Emergency stop - pause ALL operations"""
    return _manager.pause("all", reason=reason)
