"""
═══════════════════════════════════════════════════════════════════════════════
BRAIN PERSISTENCE - Save/Load MetaHive + AI Family Learning
═══════════════════════════════════════════════════════════════════════════════

Persists learning data across restarts so the system actually learns over time.

STORAGE:
1. File-based (local JSON) - Always used as primary/backup
2. JSONBin (cloud) - Uses existing JSONBIN_URL for cross-deploy persistence

Uses your existing JSONBin setup - stores brain data under "brain_learning" key.

═══════════════════════════════════════════════════════════════════════════════
"""

import os
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Storage paths (local backup)
DATA_DIR = Path(__file__).parent / "data"
BRAIN_LEARNING_FILE = DATA_DIR / "brain_learning.json"

# JSONBin config - uses your existing env vars
JSONBIN_URL = os.getenv("JSONBIN_URL", "")
JSONBIN_SECRET = os.getenv("JSONBIN_SECRET", "")

# Key used to store brain data in JSONBin (won't conflict with user data)
BRAIN_DATA_KEY = "brain_learning"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"


class BrainPersistence:
    """
    Handles persistence for all AI learning systems.

    Uses existing JSONBin for cloud persistence + local file backup.
    Stores all brain data under "brain_learning" key to avoid conflicts.
    """

    def __init__(self):
        self.use_jsonbin = bool(JSONBIN_URL and JSONBIN_SECRET)
        self._ensure_data_dir()
        self._http_client = None
        logger.info(f"🧠 BrainPersistence initialized (JSONBin: {self.use_jsonbin})")

    def _ensure_data_dir(self):
        """Create data directory if it doesn't exist"""
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def _get_http_client(self):
        """Get HTTP client (lazy init)"""
        if self._http_client is None:
            try:
                import httpx
                self._http_client = httpx.Client(timeout=30)
            except ImportError:
                import requests
                self._http_client = requests
        return self._http_client

    # ═══════════════════════════════════════════════════════════════════════════
    # UNIFIED SAVE/LOAD - All brain data in one structure
    # ═══════════════════════════════════════════════════════════════════════════

    def save_all(
        self,
        metahive_data: Dict = None,
        ai_family_data: Dict = None,
        yield_memory_data: Dict = None
    ) -> bool:
        """Save all brain learning data"""

        # Build combined state
        state = {
            "saved_at": _now(),
            "version": "2.0",
            "metahive": metahive_data or {},
            "ai_family": ai_family_data or {},
            "yield_memory": yield_memory_data or {}
        }

        # Always save to local file first (backup)
        self._save_to_file(state)

        # Then save to JSONBin if configured
        if self.use_jsonbin:
            return self._save_to_jsonbin(state)

        return True

    def load_all(self) -> Optional[Dict]:
        """Load all brain learning data"""

        # Try JSONBin first (most up-to-date)
        if self.use_jsonbin:
            data = self._load_from_jsonbin()
            if data:
                # Also update local backup
                self._save_to_file(data)
                return data

        # Fall back to local file
        return self._load_from_file()

    # ═══════════════════════════════════════════════════════════════════════════
    # COMPONENT-SPECIFIC SAVE/LOAD
    # ═══════════════════════════════════════════════════════════════════════════

    def save_metahive(self, data: Dict) -> bool:
        """Save MetaHive data"""
        current = self.load_all() or {}
        current["metahive"] = data
        current["saved_at"] = _now()
        return self.save_all(
            metahive_data=data,
            ai_family_data=current.get("ai_family"),
            yield_memory_data=current.get("yield_memory")
        )

    def load_metahive(self) -> Optional[Dict]:
        """Load MetaHive data"""
        data = self.load_all()
        return data.get("metahive") if data else None

    def save_ai_family(self, data: Dict) -> bool:
        """Save AI Family Brain data"""
        current = self.load_all() or {}
        current["ai_family"] = data
        current["saved_at"] = _now()
        return self.save_all(
            metahive_data=current.get("metahive"),
            ai_family_data=data,
            yield_memory_data=current.get("yield_memory")
        )

    def load_ai_family(self) -> Optional[Dict]:
        """Load AI Family Brain data"""
        data = self.load_all()
        return data.get("ai_family") if data else None

    def save_yield_memory(self, data: Dict) -> bool:
        """Save Yield Memory data"""
        current = self.load_all() or {}
        current["yield_memory"] = data
        current["saved_at"] = _now()
        return self.save_all(
            metahive_data=current.get("metahive"),
            ai_family_data=current.get("ai_family"),
            yield_memory_data=data
        )

    def load_yield_memory(self) -> Optional[Dict]:
        """Load Yield Memory data"""
        data = self.load_all()
        return data.get("yield_memory") if data else None

    # ═══════════════════════════════════════════════════════════════════════════
    # FILE STORAGE (Local backup)
    # ═══════════════════════════════════════════════════════════════════════════

    def _save_to_file(self, data: Dict) -> bool:
        """Save data to local JSON file"""
        try:
            self._ensure_data_dir()

            # Write to temp file first, then rename (atomic)
            temp_path = BRAIN_LEARNING_FILE.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            temp_path.rename(BRAIN_LEARNING_FILE)
            logger.debug(f"💾 Saved to local file")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to save local file: {e}")
            return False

    def _load_from_file(self) -> Optional[Dict]:
        """Load data from local JSON file"""
        try:
            if BRAIN_LEARNING_FILE.exists():
                with open(BRAIN_LEARNING_FILE, 'r') as f:
                    data = json.load(f)
                logger.debug(f"📂 Loaded from local file")
                return data
            return None

        except Exception as e:
            logger.error(f"❌ Failed to load local file: {e}")
            return None

    # ═══════════════════════════════════════════════════════════════════════════
    # JSONBIN STORAGE (Cloud persistence)
    # ═══════════════════════════════════════════════════════════════════════════

    def _save_to_jsonbin(self, brain_data: Dict) -> bool:
        """Save brain data to JSONBin under 'brain_learning' key"""
        try:
            client = self._get_http_client()

            # First, get current JSONBin content
            headers = {"X-Master-Key": JSONBIN_SECRET}
            response = client.get(JSONBIN_URL, headers=headers)

            if response.status_code == 200:
                # Parse existing data
                result = response.json()
                existing = result.get("record", {})
                if isinstance(existing, list):
                    # Convert list to dict if needed
                    existing = {"users": existing}
            else:
                existing = {}

            # Update with brain data (preserves other keys like user data)
            existing[BRAIN_DATA_KEY] = brain_data

            # Save back to JSONBin
            headers["Content-Type"] = "application/json"
            response = client.put(JSONBIN_URL, headers=headers, json=existing)

            if response.status_code == 200:
                logger.info("☁️ Saved brain learning to JSONBin")
                return True
            else:
                logger.warning(f"⚠️ JSONBin save failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"❌ JSONBin save error: {e}")
            return False

    def _load_from_jsonbin(self) -> Optional[Dict]:
        """Load brain data from JSONBin"""
        try:
            client = self._get_http_client()

            headers = {"X-Master-Key": JSONBIN_SECRET}
            response = client.get(JSONBIN_URL, headers=headers)

            if response.status_code == 200:
                result = response.json()
                record = result.get("record", {})

                # Handle if record is a list (legacy format)
                if isinstance(record, list):
                    return None

                # Get brain data from the dedicated key
                brain_data = record.get(BRAIN_DATA_KEY)
                if brain_data:
                    logger.info("☁️ Loaded brain learning from JSONBin")
                    return brain_data

            return None

        except Exception as e:
            logger.error(f"❌ JSONBin load error: {e}")
            return None

    # ═══════════════════════════════════════════════════════════════════════════
    # STATS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        stats = {
            "jsonbin_enabled": self.use_jsonbin,
            "jsonbin_url": JSONBIN_URL[:50] + "..." if JSONBIN_URL else None,
            "local_file": str(BRAIN_LEARNING_FILE),
            "local_file_exists": BRAIN_LEARNING_FILE.exists()
        }

        if BRAIN_LEARNING_FILE.exists():
            stats["local_file_size_kb"] = round(BRAIN_LEARNING_FILE.stat().st_size / 1024, 2)
            stats["local_file_modified"] = datetime.fromtimestamp(
                BRAIN_LEARNING_FILE.stat().st_mtime
            ).isoformat()

        return stats


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ═══════════════════════════════════════════════════════════════════════════════

_persistence: Optional[BrainPersistence] = None


def get_persistence() -> BrainPersistence:
    """Get singleton persistence instance"""
    global _persistence
    if _persistence is None:
        _persistence = BrainPersistence()
    return _persistence


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS (used by brain modules)
# ═══════════════════════════════════════════════════════════════════════════════

def save_metahive_learning(
    hive_patterns: List[Dict],
    type_index: Dict[str, List[str]],
    ai_model_patterns: Dict[str, List[str]],
    task_category_patterns: Dict[str, List[str]],
    contributor_stats: Dict[str, Dict]
) -> bool:
    """Save MetaHive learning to persistent storage"""
    data = {
        "hive_patterns": hive_patterns,
        "type_index": type_index,
        "ai_model_patterns": ai_model_patterns,
        "task_category_patterns": task_category_patterns,
        "contributor_stats": contributor_stats,
        "pattern_count": len(hive_patterns),
        "saved_at": _now()
    }
    return get_persistence().save_metahive(data)


def load_metahive_learning() -> Optional[Dict]:
    """Load MetaHive learning from persistent storage"""
    return get_persistence().load_metahive()


def save_ai_family_learning(
    family_members: Dict[str, Dict],
    task_history: List[Dict],
    category_model_stats: Dict[str, Dict],
    teaching_moments: List[Dict],
    cross_pollinations: List[Dict]
) -> bool:
    """Save AI Family Brain learning to persistent storage"""
    data = {
        "family_members": family_members,
        "task_history": task_history,
        "category_model_stats": category_model_stats,
        "teaching_moments": teaching_moments,
        "cross_pollinations": cross_pollinations,
        "saved_at": _now()
    }
    return get_persistence().save_ai_family(data)


def load_ai_family_learning() -> Optional[Dict]:
    """Load AI Family Brain learning from persistent storage"""
    return get_persistence().load_ai_family()


def save_yield_memory_learning(
    yield_memory: Dict[str, List[Dict]],
    user_ai_preferences: Dict[str, Dict]
) -> bool:
    """Save Yield Memory to persistent storage"""
    data = {
        "yield_memory": yield_memory,
        "user_ai_preferences": user_ai_preferences,
        "user_count": len(yield_memory),
        "saved_at": _now()
    }
    return get_persistence().save_yield_memory(data)


def load_yield_memory_learning() -> Optional[Dict]:
    """Load Yield Memory from persistent storage"""
    return get_persistence().load_yield_memory()


print(f"""
═══════════════════════════════════════════════════════════════════════════════
💾 BRAIN PERSISTENCE INITIALIZED
═══════════════════════════════════════════════════════════════════════════════

   JSONBin Cloud Storage: {"✓ ENABLED" if JSONBIN_URL and JSONBIN_SECRET else "✗ Disabled (no JSONBIN_URL)"}
   Local File Backup: ✓ data/brain_learning.json

   Brain data stored under key: "{BRAIN_DATA_KEY}"
   (Won't conflict with your existing JSONBin user data)

   Learning now survives restarts AND redeploys!

═══════════════════════════════════════════════════════════════════════════════
""")
