"""
PROOF-OF-OUTCOME LEDGER: Immutable Record of Completed Deliverables
═══════════════════════════════════════════════════════════════════════════════

Creates verifiable proof records for all completed work.

Features:
- Immutable proof records with SHA-256 hashes
- Links to artifacts (PRs, files, deployments)
- Client-verifiable proof URLs
- Aggregated proof stats for portfolio

Updated: Jan 2026
"""

import logging
import hashlib
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class ProofRecord:
    """A single proof of completed work"""
    id: str
    opportunity_id: str
    contract_id: Optional[str] = None
    milestone_id: Optional[str] = None
    proof_type: str = "deliverable"  # deliverable, artifact, deployment, review
    title: str = ""
    description: str = ""
    artifacts: List[str] = field(default_factory=list)  # URLs/paths to artifacts
    evidence: Dict[str, Any] = field(default_factory=dict)  # Screenshots, logs, etc.
    hash: str = ""  # SHA-256 of proof content
    verified: bool = False
    verified_by: Optional[str] = None
    verified_at: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    public_url: Optional[str] = None


class ProofOfOutcomeLedger:
    """
    Manages proof-of-outcome records.

    Flow:
    1. Task completes with artifacts
    2. Create proof record
    3. Generate hash for immutability
    4. Generate public proof URL
    5. Client verifies and signs off
    """

    def __init__(self):
        self.proofs: Dict[str, ProofRecord] = {}
        self.stats = {
            'proofs_created': 0,
            'proofs_verified': 0,
            'total_value_proven_usd': 0.0,
            'artifacts_logged': 0,
        }

    def create_proof(
        self,
        opportunity_id: str,
        title: str,
        description: str,
        artifacts: List[str] = None,
        evidence: Dict[str, Any] = None,
        contract_id: str = None,
        milestone_id: str = None,
        proof_type: str = "deliverable",
    ) -> ProofRecord:
        """
        Create a proof record for completed work.

        Args:
            opportunity_id: The opportunity this proof is for
            title: Title of the proof
            description: Description of what was delivered
            artifacts: List of URLs/paths to artifacts
            evidence: Dict of evidence (screenshots, logs, etc.)
            contract_id: Associated contract ID
            milestone_id: Associated milestone ID
            proof_type: Type of proof

        Returns:
            ProofRecord with hash and public URL
        """
        artifacts = artifacts or []
        evidence = evidence or {}

        # Generate proof ID
        proof_id = f"proof_{hashlib.md5(f'{opportunity_id}_{datetime.now().isoformat()}'.encode()).hexdigest()[:12]}"

        # Create proof content for hashing
        proof_content = {
            'id': proof_id,
            'opportunity_id': opportunity_id,
            'contract_id': contract_id,
            'milestone_id': milestone_id,
            'title': title,
            'description': description,
            'artifacts': artifacts,
            'evidence_keys': list(evidence.keys()),
            'created_at': datetime.now(timezone.utc).isoformat(),
        }

        # Generate SHA-256 hash
        proof_hash = hashlib.sha256(
            json.dumps(proof_content, sort_keys=True).encode()
        ).hexdigest()

        # Generate public URL
        public_url = f"https://proofs.aigentsy.com/{proof_id}?hash={proof_hash[:16]}"

        # Create record
        proof = ProofRecord(
            id=proof_id,
            opportunity_id=opportunity_id,
            contract_id=contract_id,
            milestone_id=milestone_id,
            proof_type=proof_type,
            title=title,
            description=description,
            artifacts=artifacts,
            evidence=evidence,
            hash=proof_hash,
            public_url=public_url,
        )

        # Store
        self.proofs[proof_id] = proof
        self.stats['proofs_created'] += 1
        self.stats['artifacts_logged'] += len(artifacts)

        logger.info(f"Created proof {proof_id}: {title}")

        return proof

    def verify_proof(self, proof_id: str, verifier: str, value_usd: float = 0.0) -> bool:
        """
        Verify a proof record.

        Args:
            proof_id: The proof ID to verify
            verifier: Who is verifying (client, system, etc.)
            value_usd: Value of the verified work

        Returns:
            True if verified
        """
        proof = self.proofs.get(proof_id)
        if not proof:
            return False

        proof.verified = True
        proof.verified_by = verifier
        proof.verified_at = datetime.now(timezone.utc).isoformat()

        self.stats['proofs_verified'] += 1
        self.stats['total_value_proven_usd'] += value_usd

        logger.info(f"Proof {proof_id} verified by {verifier}")

        return True

    def add_artifact(self, proof_id: str, artifact_url: str) -> bool:
        """Add artifact to existing proof"""
        proof = self.proofs.get(proof_id)
        if not proof:
            return False

        proof.artifacts.append(artifact_url)
        self.stats['artifacts_logged'] += 1

        # Update hash
        proof.hash = self._rehash_proof(proof)

        return True

    def _rehash_proof(self, proof: ProofRecord) -> str:
        """Rehash proof after modification"""
        proof_content = {
            'id': proof.id,
            'opportunity_id': proof.opportunity_id,
            'artifacts': proof.artifacts,
            'evidence_keys': list(proof.evidence.keys()),
            'modified_at': datetime.now(timezone.utc).isoformat(),
        }
        return hashlib.sha256(
            json.dumps(proof_content, sort_keys=True).encode()
        ).hexdigest()

    def get_proofs_for_opportunity(self, opportunity_id: str) -> List[ProofRecord]:
        """Get all proofs for an opportunity"""
        return [p for p in self.proofs.values() if p.opportunity_id == opportunity_id]

    def get_proofs_for_contract(self, contract_id: str) -> List[ProofRecord]:
        """Get all proofs for a contract"""
        return [p for p in self.proofs.values() if p.contract_id == contract_id]

    def get_verified_proofs(self) -> List[ProofRecord]:
        """Get all verified proofs (for portfolio)"""
        return [p for p in self.proofs.values() if p.verified]

    def get_proof(self, proof_id: str) -> Optional[ProofRecord]:
        """Get proof by ID"""
        return self.proofs.get(proof_id)

    def render_share_card(self, proof_id: str, anonymize: bool = True) -> Optional[Dict[str, Any]]:
        """
        Render shareable proof card for Wall of Wins / testimonials.

        Args:
            proof_id: The proof ID
            anonymize: Whether to anonymize client details

        Returns:
            Share card data for rendering, or None
        """
        proof = self.proofs.get(proof_id)
        if not proof or not proof.verified:
            return None

        # Anonymize client info if requested
        client_display = "Client" if anonymize else proof.opportunity_id

        # Generate share URLs
        share_card = {
            'id': proof.id,
            'title': proof.title,
            'description': proof.description[:200] + '...' if len(proof.description) > 200 else proof.description,
            'client': client_display,
            'verified': True,
            'verified_at': proof.verified_at,
            'hash_preview': proof.hash[:16],
            'public_url': proof.public_url,
            'artifact_count': len(proof.artifacts),
            'share_links': {
                'linkedin': f"https://www.linkedin.com/sharing/share-offsite/?url={proof.public_url}",
                'twitter': f"https://twitter.com/intent/tweet?url={proof.public_url}&text=Completed: {proof.title}",
                'copy': proof.public_url,
            },
            'embed_html': f'''<div class="aigentsy-proof-card" data-proof-id="{proof.id}">
  <h3>{proof.title}</h3>
  <p>Verified ✓</p>
  <a href="{proof.public_url}">View Proof</a>
</div>''',
        }

        return share_card

    def get_wall_of_wins(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get Wall of Wins - collection of verified proof cards.

        Returns anonymized, shareable proof cards for public display.
        """
        verified = self.get_verified_proofs()

        # Sort by verification date (newest first)
        verified.sort(
            key=lambda p: p.verified_at or p.created_at,
            reverse=True
        )

        cards = []
        for proof in verified[:limit]:
            card = self.render_share_card(proof.id, anonymize=True)
            if card:
                cards.append(card)

        return cards

    def get_stats(self) -> Dict[str, Any]:
        """Get ledger stats"""
        return {
            **self.stats,
            'total_proofs': len(self.proofs),
            'verification_rate': round(
                self.stats['proofs_verified'] / self.stats['proofs_created'] * 100, 1
            ) if self.stats['proofs_created'] > 0 else 0,
        }

    def to_dict(self, proof: ProofRecord) -> Dict[str, Any]:
        """Convert proof to dict"""
        return {
            'id': proof.id,
            'opportunity_id': proof.opportunity_id,
            'contract_id': proof.contract_id,
            'milestone_id': proof.milestone_id,
            'proof_type': proof.proof_type,
            'title': proof.title,
            'description': proof.description,
            'artifacts': proof.artifacts,
            'evidence': proof.evidence,
            'hash': proof.hash,
            'verified': proof.verified,
            'verified_by': proof.verified_by,
            'verified_at': proof.verified_at,
            'created_at': proof.created_at,
            'public_url': proof.public_url,
        }

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary for public display"""
        verified = self.get_verified_proofs()

        # Group by type
        by_type = {}
        for proof in verified:
            ptype = proof.proof_type
            if ptype not in by_type:
                by_type[ptype] = []
            by_type[ptype].append({
                'id': proof.id,
                'title': proof.title,
                'public_url': proof.public_url,
                'created_at': proof.created_at,
            })

        return {
            'total_verified': len(verified),
            'total_value_usd': self.stats['total_value_proven_usd'],
            'by_type': by_type,
            'recent': [
                {
                    'id': p.id,
                    'title': p.title,
                    'public_url': p.public_url,
                }
                for p in sorted(verified, key=lambda x: x.created_at, reverse=True)[:10]
            ]
        }


# Global instance
_ledger: Optional[ProofOfOutcomeLedger] = None


def get_proof_ledger() -> ProofOfOutcomeLedger:
    """Get or create proof ledger singleton"""
    global _ledger
    if _ledger is None:
        _ledger = ProofOfOutcomeLedger()
    return _ledger


def create_proof(
    opportunity_id: str,
    title: str,
    description: str,
    artifacts: List[str] = None,
    **kwargs
) -> ProofRecord:
    """Convenience function"""
    return get_proof_ledger().create_proof(
        opportunity_id=opportunity_id,
        title=title,
        description=description,
        artifacts=artifacts,
        **kwargs
    )
