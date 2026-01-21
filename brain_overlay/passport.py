"""
PROOF-OF-OUTCOME PASSPORT
=========================

Portable, signed passport with last 90-day outcomes + OCS deltas.
Required for:
- Prime placement
- IFX best-bid access
- Senior tranches

Partners integrate via verify endpoint → ecosystem dependence.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
import hashlib
import json
import base64


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"


def _sign_passport(data: dict) -> str:
    """Sign passport data (simplified - use proper signing in prod)"""
    payload = json.dumps(data, sort_keys=True, default=str)
    return f"sha256:{hashlib.sha256(payload.encode()).hexdigest()}"


class PassportEngine:
    """
    Proof-of-Outcome passport issuance and verification.

    Passports are portable credentials that:
    - Prove historical performance
    - Enable trust without re-verification
    - Create ecosystem lock-in
    """

    def __init__(self):
        self._passports: Dict[str, Dict[str, Any]] = {}
        self._verifications: List[Dict[str, Any]] = []
        self._passport_ttl_days = 90

    def issue(self, entity_id: str, include_details: bool = True) -> Dict[str, Any]:
        """
        Issue passport for entity.

        Args:
            entity_id: Entity identifier
            include_details: Include detailed attestations

        Returns:
            Signed passport
        """
        # Get OCS from ocs module
        try:
            from .ocs import _ocs_engine
            ocs_data = _ocs_engine.get_entity_details(entity_id)
            ocs = ocs_data.get("ocs", 50)
            tier = ocs_data.get("tier", "standard")
            proofs = ocs_data.get("proofs", 0)
            sla_hits = ocs_data.get("sla_hits", 0)
            disputes = ocs_data.get("disputes", 0)
        except:
            ocs = 50
            tier = "standard"
            proofs = 0
            sla_hits = 0
            disputes = 0

        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=self._passport_ttl_days)

        passport_data = {
            "entity_id": entity_id,
            "ocs": ocs,
            "tier": tier,
            "issued_at": now.isoformat() + "Z",
            "expires_at": expires.isoformat() + "Z",
            "issuer": "aigentsy_platform",
            "version": "1.0"
        }

        if include_details:
            passport_data["attestations"] = {
                "proofs": proofs,
                "sla_hits": sla_hits,
                "disputes": disputes,
                "reliability_rate": round(sla_hits / (sla_hits + disputes), 3) if (sla_hits + disputes) > 0 else 1.0
            }

        # Sign passport
        passport_data["signature"] = _sign_passport({
            k: v for k, v in passport_data.items() if k != "signature"
        })

        # Generate passport hash for quick lookup
        passport_hash = hashlib.sha256(json.dumps(passport_data, sort_keys=True).encode()).hexdigest()[:16]
        passport_data["passport_hash"] = passport_hash

        # Store
        self._passports[entity_id] = passport_data

        return {
            "ok": True,
            "passport": passport_data
        }

    def verify(self, passport: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify a passport is authentic and valid.

        Args:
            passport: Passport to verify

        Returns:
            Verification result
        """
        entity_id = passport.get("entity_id")
        if not entity_id:
            return {"ok": False, "valid": False, "error": "missing_entity_id"}

        # Check expiration
        expires_str = passport.get("expires_at")
        if expires_str:
            try:
                expires = datetime.fromisoformat(expires_str.replace("Z", "+00:00"))
                if expires < datetime.now(timezone.utc):
                    return {"ok": True, "valid": False, "error": "passport_expired"}
            except:
                pass

        # Verify signature
        stored_sig = passport.get("signature")
        passport_copy = {k: v for k, v in passport.items() if k not in ["signature", "passport_hash"]}
        expected_sig = _sign_passport(passport_copy)

        if stored_sig != expected_sig:
            return {"ok": True, "valid": False, "error": "signature_mismatch"}

        # Record verification
        self._verifications.append({
            "entity_id": entity_id,
            "passport_hash": passport.get("passport_hash"),
            "verified_at": _now_iso(),
            "ocs": passport.get("ocs")
        })

        return {
            "ok": True,
            "valid": True,
            "entity_id": entity_id,
            "ocs": passport.get("ocs"),
            "tier": passport.get("tier"),
            "expires_at": passport.get("expires_at")
        }

    def verify_by_hash(self, entity_id: str, passport_hash: str) -> Dict[str, Any]:
        """Verify passport by hash (quick lookup)"""
        stored = self._passports.get(entity_id)
        if not stored:
            return {"ok": False, "valid": False, "error": "passport_not_found"}

        if stored.get("passport_hash") != passport_hash:
            return {"ok": False, "valid": False, "error": "hash_mismatch"}

        return self.verify(stored)

    def get_passport(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get stored passport for entity"""
        return self._passports.get(entity_id)

    def refresh(self, entity_id: str) -> Dict[str, Any]:
        """Refresh passport with latest OCS"""
        return self.issue(entity_id)

    def revoke(self, entity_id: str, reason: str = "manual") -> Dict[str, Any]:
        """Revoke a passport"""
        if entity_id in self._passports:
            del self._passports[entity_id]
            return {"ok": True, "revoked": True, "reason": reason}
        return {"ok": False, "error": "passport_not_found"}

    def get_verification_history(self, entity_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get verification history"""
        history = self._verifications
        if entity_id:
            history = [v for v in history if v.get("entity_id") == entity_id]
        return list(reversed(history[-limit:]))

    def get_stats(self) -> Dict[str, Any]:
        """Get passport system statistics"""
        return {
            "total_passports": len(self._passports),
            "total_verifications": len(self._verifications),
            "avg_ocs": round(
                sum(p.get("ocs", 0) for p in self._passports.values()) / len(self._passports), 1
            ) if self._passports else 0
        }


# Module-level singleton
_passport_engine = PassportEngine()


def issue_passport(entity_id: str, **kwargs) -> Dict[str, Any]:
    """Issue passport for entity"""
    return _passport_engine.issue(entity_id, **kwargs)


def verify_passport(passport: Dict[str, Any]) -> Dict[str, Any]:
    """Verify passport"""
    return _passport_engine.verify(passport)


def get_passport(entity_id: str) -> Optional[Dict[str, Any]]:
    """Get passport for entity"""
    return _passport_engine.get_passport(entity_id)
