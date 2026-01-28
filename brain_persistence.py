"""
═══════════════════════════════════════════════════════════════════════════════
BRAIN PERSISTENCE - Save/Load MetaHive + AI Family Learning
═══════════════════════════════════════════════════════════════════════════════

Persists learning data across restarts so the system actually learns over time.

STORAGE OPTIONS:
1. File-based (local JSON) - Default, works everywhere
2. JSONBin (cloud) - For persistence across deploys on Render

WHAT WE PERSIST:
- MetaHive patterns (platform-wide learnings)
- AI Family Brain state (model performance stats)
- Yield Memory (per-user patterns)
- Task history (for learning)

═══════════════════════════════════════════════════════════════════════════════
"""

import os
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import asdict

logger = logging.getLogger(__name__)

# Storage paths
DATA_DIR = Path(__file__).parent / "data"
METAHIVE_FILE = DATA_DIR / "metahive_learning.json"
AI_FAMILY_FILE = DATA_DIR / "ai_family_learning.json"
YIELD_MEMORY_FILE = DATA_DIR / "yield_memory.json"

# JSONBin config (for cloud persistence)
JSONBIN_URL = os.getenv("JSONBIN_URL", "")
JSONBIN_SECRET = os.getenv("JSONBIN_SECRET", "")
METAHIVE_BIN_URL = os.getenv("METAHIVE_BIN_URL", "")  # Separate bin for MetaHive


def _now() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"


class BrainPersistence:
    """
    Handles persistence for all AI learning systems.

    Uses file-based storage by default, with optional JSONBin for cloud persistence.
    """

    def __init__(self, use_jsonbin: bool = False):
        self.use_jsonbin = use_jsonbin and bool(JSONBIN_SECRET)
        self._ensure_data_dir()
        logger.info(f"🧠 BrainPersistence initialized (JSONBin: {self.use_jsonbin})")

    def _ensure_data_dir(self):
        """Create data directory if it doesn't exist"""
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # METAHIVE PERSISTENCE
    # ═══════════════════════════════════════════════════════════════════════════

    def save_metahive(
        self,
        hive_patterns: List[Dict],
        type_index: Dict[str, List[str]],
        ai_model_patterns: Dict[str, List[str]],
        task_category_patterns: Dict[str, List[str]],
        contributor_stats: Dict[str, Dict]
    ) -> bool:
        """Save MetaHive learning state"""

        state = {
            "saved_at": _now(),
            "version": "2.0",
            "hive_patterns": hive_patterns,
            "type_index": type_index,
            "ai_model_patterns": ai_model_patterns,
            "task_category_patterns": task_category_patterns,
            "contributor_stats": contributor_stats,
            "pattern_count": len(hive_patterns)
        }

        return self._save_to_file(METAHIVE_FILE, state)

    def load_metahive(self) -> Optional[Dict]:
        """Load MetaHive learning state"""
        return self._load_from_file(METAHIVE_FILE)

    # ═══════════════════════════════════════════════════════════════════════════
    # AI FAMILY BRAIN PERSISTENCE
    # ═══════════════════════════════════════════════════════════════════════════

    def save_ai_family(
        self,
        family_members: Dict[str, Dict],
        task_history: List[Dict],
        category_model_stats: Dict[str, Dict],
        teaching_moments: List[Dict],
        cross_pollinations: List[Dict]
    ) -> bool:
        """Save AI Family Brain learning state"""

        state = {
            "saved_at": _now(),
            "version": "1.0",
            "family_members": family_members,
            "task_history": task_history[-1000:],  # Keep last 1000
            "category_model_stats": category_model_stats,
            "teaching_moments": teaching_moments[-200:],  # Keep last 200
            "cross_pollinations": cross_pollinations[-200:]
        }

        return self._save_to_file(AI_FAMILY_FILE, state)

    def load_ai_family(self) -> Optional[Dict]:
        """Load AI Family Brain learning state"""
        return self._load_from_file(AI_FAMILY_FILE)

    # ═══════════════════════════════════════════════════════════════════════════
    # YIELD MEMORY PERSISTENCE
    # ═══════════════════════════════════════════════════════════════════════════

    def save_yield_memory(
        self,
        yield_memory: Dict[str, List[Dict]],
        user_ai_preferences: Dict[str, Dict]
    ) -> bool:
        """Save Yield Memory (per-user patterns)"""

        state = {
            "saved_at": _now(),
            "version": "2.0",
            "yield_memory": yield_memory,
            "user_ai_preferences": user_ai_preferences,
            "user_count": len(yield_memory)
        }

        return self._save_to_file(YIELD_MEMORY_FILE, state)

    def load_yield_memory(self) -> Optional[Dict]:
        """Load Yield Memory"""
        return self._load_from_file(YIELD_MEMORY_FILE)

    # ═══════════════════════════════════════════════════════════════════════════
    # FILE STORAGE
    # ═══════════════════════════════════════════════════════════════════════════

    def _save_to_file(self, filepath: Path, data: Dict) -> bool:
        """Save data to JSON file"""
        try:
            self._ensure_data_dir()

            # Write to temp file first, then rename (atomic)
            temp_path = filepath.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            temp_path.rename(filepath)
            logger.info(f"💾 Saved to {filepath.name}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to save {filepath.name}: {e}")
            return False

    def _load_from_file(self, filepath: Path) -> Optional[Dict]:
        """Load data from JSON file"""
        try:
            if filepath.exists():
                with open(filepath, 'r') as f:
                    data = json.load(f)
                logger.info(f"📂 Loaded from {filepath.name}")
                return data
            else:
                logger.info(f"📂 No existing {filepath.name} found")
                return None

        except Exception as e:
            logger.error(f"❌ Failed to load {filepath.name}: {e}")
            return None

    # ═══════════════════════════════════════════════════════════════════════════
    # JSONBIN STORAGE (Cloud backup)
    # ═══════════════════════════════════════════════════════════════════════════

    def save_all_to_jsonbin(self, combined_state: Dict) -> bool:
        """Save combined state to JSONBin for cloud persistence"""
        if not self.use_jsonbin or not METAHIVE_BIN_URL:
            return False

        try:
            import httpx

            headers = {
                "X-Master-Key": JSONBIN_SECRET,
                "Content-Type": "application/json"
            }

            response = httpx.put(
                METAHIVE_BIN_URL,
                headers=headers,
                json=combined_state,
                timeout=30
            )

            if response.status_code == 200:
                logger.info("☁️ Saved to JSONBin")
                return True
            else:
                logger.warning(f"⚠️ JSONBin save failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"❌ JSONBin save error: {e}")
            return False

    def load_from_jsonbin(self) -> Optional[Dict]:
        """Load combined state from JSONBin"""
        if not self.use_jsonbin or not METAHIVE_BIN_URL:
            return None

        try:
            import httpx

            headers = {"X-Master-Key": JSONBIN_SECRET}

            response = httpx.get(
                f"{METAHIVE_BIN_URL}/latest",
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                logger.info("☁️ Loaded from JSONBin")
                return data.get("record", data)
            else:
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
            "storage_type": "jsonbin" if self.use_jsonbin else "file",
            "data_dir": str(DATA_DIR),
            "files": {}
        }

        for name, path in [
            ("metahive", METAHIVE_FILE),
            ("ai_family", AI_FAMILY_FILE),
            ("yield_memory", YIELD_MEMORY_FILE)
        ]:
            if path.exists():
                stats["files"][name] = {
                    "exists": True,
                    "size_kb": round(path.stat().st_size / 1024, 2),
                    "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat()
                }
            else:
                stats["files"][name] = {"exists": False}

        return stats


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ═══════════════════════════════════════════════════════════════════════════════

_persistence: Optional[BrainPersistence] = None


def get_persistence() -> BrainPersistence:
    """Get singleton persistence instance"""
    global _persistence
    if _persistence is None:
        # Use JSONBin if METAHIVE_BIN_URL is configured
        use_jsonbin = bool(os.getenv("METAHIVE_BIN_URL"))
        _persistence = BrainPersistence(use_jsonbin=use_jsonbin)
    return _persistence


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def save_metahive_learning(
    hive_patterns: List[Dict],
    type_index: Dict[str, List[str]],
    ai_model_patterns: Dict[str, List[str]],
    task_category_patterns: Dict[str, List[str]],
    contributor_stats: Dict[str, Dict]
) -> bool:
    """Save MetaHive learning to persistent storage"""
    return get_persistence().save_metahive(
        hive_patterns, type_index, ai_model_patterns,
        task_category_patterns, contributor_stats
    )


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
    return get_persistence().save_ai_family(
        family_members, task_history, category_model_stats,
        teaching_moments, cross_pollinations
    )


def load_ai_family_learning() -> Optional[Dict]:
    """Load AI Family Brain learning from persistent storage"""
    return get_persistence().load_ai_family()


def save_yield_memory_learning(
    yield_memory: Dict[str, List[Dict]],
    user_ai_preferences: Dict[str, Dict]
) -> bool:
    """Save Yield Memory to persistent storage"""
    return get_persistence().save_yield_memory(yield_memory, user_ai_preferences)


def load_yield_memory_learning() -> Optional[Dict]:
    """Load Yield Memory from persistent storage"""
    return get_persistence().load_yield_memory()


print("""
═══════════════════════════════════════════════════════════════════════════════
💾 BRAIN PERSISTENCE INITIALIZED
═══════════════════════════════════════════════════════════════════════════════

   Storage: File-based (data/*.json) + Optional JSONBin cloud backup

   Persisted:
   ✓ MetaHive patterns (platform-wide)
   ✓ AI Family Brain stats (model performance)
   ✓ Yield Memory (per-user patterns)

   Learning now survives restarts!

═══════════════════════════════════════════════════════════════════════════════
""")
