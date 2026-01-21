"""
FEATURE STORE
=============

Single source of truth for all learning features.
Keyed by (actor_id, sku_id, connector_id, pdl_id, segment).

Stores model-ready records for:
- OCS (Outcome Credit Score)
- Historical conversion rates
- Pricing signals
- Connector health
- Tranche performance
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import json


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"


class FeatureStore:
    """
    In-memory feature store with TTL and versioning.

    Features are keyed by composite keys and support:
    - Point lookups
    - Range scans
    - TTL expiration
    - Version history
    """

    def __init__(self, default_ttl_hours: int = 24 * 7):
        self._features: Dict[str, Dict[str, Any]] = {}
        self._versions: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._default_ttl = timedelta(hours=default_ttl_hours)
        self._max_versions = 10

    def _make_key(self, keys: Dict[str, str]) -> str:
        """Create composite key from key dict"""
        sorted_keys = sorted(keys.items())
        return "|".join(f"{k}={v}" for k, v in sorted_keys if v)

    def update(self, keys: Dict[str, str], features: Dict[str, Any], ttl_hours: int = None):
        """
        Update features for a key.

        Args:
            keys: Composite key dict (actor_id, sku_id, etc.)
            features: Feature values to update
            ttl_hours: Optional TTL override
        """
        key = self._make_key(keys)
        now = datetime.now(timezone.utc)
        ttl = timedelta(hours=ttl_hours) if ttl_hours else self._default_ttl

        # Get or create record
        if key not in self._features:
            self._features[key] = {
                "_keys": keys,
                "_created_at": _now_iso(),
                "_updated_at": _now_iso(),
                "_expires_at": (now + ttl).isoformat() + "Z",
                "_version": 1
            }
        else:
            # Save version history
            old_record = {**self._features[key]}
            self._versions[key].append(old_record)
            if len(self._versions[key]) > self._max_versions:
                self._versions[key] = self._versions[key][-self._max_versions:]

            self._features[key]["_updated_at"] = _now_iso()
            self._features[key]["_expires_at"] = (now + ttl).isoformat() + "Z"
            self._features[key]["_version"] += 1

        # Update features
        self._features[key].update(features)

        return {"ok": True, "key": key, "version": self._features[key]["_version"]}

    def get(self, keys: Dict[str, str], features: List[str] = None) -> Dict[str, Any]:
        """
        Get features for a key.

        Args:
            keys: Composite key dict
            features: Optional list of specific features to return

        Returns:
            Feature dict or None if not found/expired
        """
        key = self._make_key(keys)
        record = self._features.get(key)

        if not record:
            return None

        # Check expiration
        expires = datetime.fromisoformat(record["_expires_at"].replace("Z", "+00:00"))
        if expires < datetime.now(timezone.utc):
            del self._features[key]
            return None

        # Return specific features or all
        if features:
            return {f: record.get(f) for f in features if f in record}
        return {k: v for k, v in record.items() if not k.startswith("_")}

    def get_ocs(self, actor_id: str) -> float:
        """Get OCS for actor (convenience method)"""
        features = self.get({"actor_id": actor_id}, ["ocs"])
        return features.get("ocs", 50) if features else 50

    def scan(self, prefix_keys: Dict[str, str], limit: int = 100) -> List[Dict[str, Any]]:
        """
        Scan features matching prefix keys.

        Args:
            prefix_keys: Keys to match (partial match)
            limit: Max results

        Returns:
            List of matching feature records
        """
        results = []
        now = datetime.now(timezone.utc)

        for key, record in self._features.items():
            # Check expiration
            expires = datetime.fromisoformat(record["_expires_at"].replace("Z", "+00:00"))
            if expires < now:
                continue

            # Check prefix match
            match = True
            record_keys = record.get("_keys", {})
            for k, v in prefix_keys.items():
                if record_keys.get(k) != v:
                    match = False
                    break

            if match:
                results.append(record)
                if len(results) >= limit:
                    break

        return results

    def delete(self, keys: Dict[str, str]) -> bool:
        """Delete features for a key"""
        key = self._make_key(keys)
        if key in self._features:
            del self._features[key]
            return True
        return False

    def get_versions(self, keys: Dict[str, str], limit: int = 5) -> List[Dict[str, Any]]:
        """Get version history for a key"""
        key = self._make_key(keys)
        return list(reversed(self._versions.get(key, [])[-limit:]))

    def expire_old(self) -> int:
        """Expire old records (for periodic cleanup)"""
        now = datetime.now(timezone.utc)
        expired = []

        for key, record in self._features.items():
            expires = datetime.fromisoformat(record["_expires_at"].replace("Z", "+00:00"))
            if expires < now:
                expired.append(key)

        for key in expired:
            del self._features[key]

        return len(expired)

    def get_stats(self) -> Dict[str, Any]:
        """Get feature store statistics"""
        now = datetime.now(timezone.utc)
        active = 0
        expired = 0

        for record in self._features.values():
            expires = datetime.fromisoformat(record["_expires_at"].replace("Z", "+00:00"))
            if expires < now:
                expired += 1
            else:
                active += 1

        return {
            "total_records": len(self._features),
            "active_records": active,
            "expired_records": expired,
            "version_histories": len(self._versions)
        }


# Module-level singleton
_feature_store = FeatureStore()


def get_feature_store() -> FeatureStore:
    """Get default feature store"""
    return _feature_store


def update_features(keys: Dict[str, str], features: Dict[str, Any], **kwargs):
    """Update features in default store"""
    return _feature_store.update(keys, features, **kwargs)


def get_features(keys: Dict[str, str], features: List[str] = None) -> Dict[str, Any]:
    """Get features from default store"""
    return _feature_store.get(keys, features)


def get_ocs(actor_id: str) -> float:
    """Get OCS for actor from default store"""
    return _feature_store.get_ocs(actor_id)
