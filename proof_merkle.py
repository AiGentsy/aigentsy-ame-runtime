"""
PROOF-OF-EXECUTION MERKLE RECEIPTS
==================================

Builds Merkle tree from execution proofs for verifiable delivery.
- Each execution's proof bundle → Merkle leaf
- Roll up per-day → single Merkle root
- Store root in ledger (optional: anchor to public chain later)

Benefits:
- Verifiable delivery receipts
- Lower disputes
- Higher close rates
- Enables insurance/reinsurance capacity
- Partner trust rails

Usage:
    from proof_merkle import add_proof_leaf, get_receipt, get_daily_root

    # On execution complete
    leaf = add_proof_leaf(execution_id, proofs)

    # Get verifiable receipt
    receipt = get_receipt(execution_id)

    # Get daily rollup
    root = get_daily_root("2026-01-21")
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from collections import defaultdict


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _hash_leaf(data: Any) -> str:
    """Hash data into a Merkle leaf"""
    if isinstance(data, dict):
        data = json.dumps(data, sort_keys=True, default=str)
    elif not isinstance(data, str):
        data = str(data)
    return hashlib.sha256(data.encode()).hexdigest()


def _hash_pair(left: str, right: str) -> str:
    """Hash two nodes together"""
    combined = left + right if left < right else right + left
    return hashlib.sha256(combined.encode()).hexdigest()


class MerkleTree:
    """Simple Merkle tree for proof verification"""

    def __init__(self):
        self._leaves: List[str] = []
        self._leaf_data: Dict[str, Dict] = {}  # leaf_hash -> data

    def add_leaf(self, data: Dict[str, Any]) -> str:
        """Add a leaf and return its hash"""
        leaf_hash = _hash_leaf(data)
        self._leaves.append(leaf_hash)
        self._leaf_data[leaf_hash] = data
        return leaf_hash

    def get_root(self) -> str:
        """Calculate Merkle root"""
        if not self._leaves:
            return _hash_leaf("empty")

        level = self._leaves.copy()

        while len(level) > 1:
            next_level = []
            for i in range(0, len(level), 2):
                if i + 1 < len(level):
                    next_level.append(_hash_pair(level[i], level[i + 1]))
                else:
                    next_level.append(level[i])  # Odd leaf promotes
            level = next_level

        return level[0]

    def get_proof(self, leaf_hash: str) -> List[Dict[str, str]]:
        """Get inclusion proof for a leaf"""
        if leaf_hash not in self._leaves:
            return []

        proof = []
        index = self._leaves.index(leaf_hash)
        level = self._leaves.copy()

        while len(level) > 1:
            if index % 2 == 0:
                # We're on the left, sibling is on the right
                if index + 1 < len(level):
                    proof.append({"position": "right", "hash": level[index + 1]})
            else:
                # We're on the right, sibling is on the left
                proof.append({"position": "left", "hash": level[index - 1]})

            # Move to next level
            next_level = []
            for i in range(0, len(level), 2):
                if i + 1 < len(level):
                    next_level.append(_hash_pair(level[i], level[i + 1]))
                else:
                    next_level.append(level[i])
            level = next_level
            index = index // 2

        return proof

    @property
    def leaf_count(self) -> int:
        return len(self._leaves)


class ProofMerkleStore:
    """
    Stores execution proofs in Merkle trees, rolled up daily.

    Structure:
    - Each execution → leaf (hash of proofs)
    - Each day → one Merkle tree with all executions
    - Daily root stored in ledger for verification
    """

    def __init__(self):
        self._daily_trees: Dict[str, MerkleTree] = defaultdict(MerkleTree)
        self._execution_index: Dict[str, Dict[str, Any]] = {}  # execution_id -> {date, leaf_hash}
        self._daily_roots: Dict[str, str] = {}  # date -> root_hash

    def add_proof_leaf(
        self,
        execution_id: str,
        proofs: List[Dict[str, Any]],
        *,
        coi_id: str = None,
        entity_id: str = None,
        connector: str = None,
        revenue: float = 0.0
    ) -> Dict[str, Any]:
        """
        Add execution proofs as a Merkle leaf.

        Args:
            execution_id: Unique execution identifier
            proofs: List of proof objects from execution
            coi_id: Optional COI reference
            entity_id: Optional provider entity ID
            connector: Connector used
            revenue: Revenue from execution

        Returns:
            Leaf info with hash and inclusion data
        """
        date = _today()
        tree = self._daily_trees[date]

        # Build leaf data
        leaf_data = {
            "execution_id": execution_id,
            "coi_id": coi_id,
            "entity_id": entity_id,
            "connector": connector,
            "revenue": revenue,
            "proof_count": len(proofs),
            "proofs_hash": _hash_leaf(proofs),
            "timestamp": _now_iso()
        }

        # Add to tree
        leaf_hash = tree.add_leaf(leaf_data)

        # Index for retrieval
        self._execution_index[execution_id] = {
            "date": date,
            "leaf_hash": leaf_hash,
            "leaf_data": leaf_data,
            "tree_position": tree.leaf_count - 1
        }

        return {
            "ok": True,
            "execution_id": execution_id,
            "leaf_hash": leaf_hash,
            "date": date,
            "tree_position": tree.leaf_count - 1,
            "current_root": tree.get_root()
        }

    def get_receipt(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Get verifiable receipt for an execution.

        Returns leaf data + inclusion proof + root.
        """
        if execution_id not in self._execution_index:
            return None

        info = self._execution_index[execution_id]
        date = info["date"]
        leaf_hash = info["leaf_hash"]
        tree = self._daily_trees[date]

        # Get inclusion proof
        proof = tree.get_proof(leaf_hash)

        return {
            "execution_id": execution_id,
            "leaf_hash": leaf_hash,
            "leaf_data": info["leaf_data"],
            "merkle_proof": proof,
            "merkle_root": tree.get_root(),
            "date": date,
            "tree_size": tree.leaf_count,
            "verifiable": True,
            "generated_at": _now_iso()
        }

    def verify_receipt(self, receipt: Dict[str, Any]) -> bool:
        """Verify a receipt's inclusion proof"""
        leaf_hash = receipt.get("leaf_hash")
        proof = receipt.get("merkle_proof", [])
        expected_root = receipt.get("merkle_root")

        # Reconstruct root from leaf + proof
        current = leaf_hash
        for step in proof:
            if step["position"] == "left":
                current = _hash_pair(step["hash"], current)
            else:
                current = _hash_pair(current, step["hash"])

        return current == expected_root

    def finalize_daily_root(self, date: str = None) -> Dict[str, Any]:
        """
        Finalize and store the daily Merkle root.
        Call this at end of day or when anchoring to chain.
        """
        date = date or _today()

        if date not in self._daily_trees:
            return {"ok": False, "error": "no_executions_for_date"}

        tree = self._daily_trees[date]
        root = tree.get_root()

        # Store finalized root
        self._daily_roots[date] = root

        # Post to ledger
        try:
            from monetization.ledger import post_entry
            post_entry(
                entry_type="merkle_root",
                ref=f"merkle:{date}",
                debit=0,
                credit=0,
                meta={
                    "root": root,
                    "leaf_count": tree.leaf_count,
                    "date": date,
                    "finalized_at": _now_iso()
                }
            )
        except ImportError:
            pass

        return {
            "ok": True,
            "date": date,
            "root": root,
            "leaf_count": tree.leaf_count,
            "finalized_at": _now_iso()
        }

    def get_daily_root(self, date: str = None) -> Dict[str, Any]:
        """Get the Merkle root for a specific date"""
        date = date or _today()

        if date in self._daily_roots:
            return {
                "date": date,
                "root": self._daily_roots[date],
                "finalized": True
            }

        if date in self._daily_trees:
            tree = self._daily_trees[date]
            return {
                "date": date,
                "root": tree.get_root(),
                "leaf_count": tree.leaf_count,
                "finalized": False
            }

        return {"date": date, "root": None, "error": "no_data"}

    def get_stats(self) -> Dict[str, Any]:
        """Get Merkle store statistics"""
        total_leaves = sum(t.leaf_count for t in self._daily_trees.values())

        return {
            "total_executions": len(self._execution_index),
            "total_leaves": total_leaves,
            "days_tracked": len(self._daily_trees),
            "roots_finalized": len(self._daily_roots),
            "dates": list(self._daily_trees.keys())
        }


# Module-level singleton
_merkle_store = ProofMerkleStore()


def add_proof_leaf(execution_id: str, proofs: List[Dict], **kwargs) -> Dict[str, Any]:
    """Add execution proofs as Merkle leaf"""
    return _merkle_store.add_proof_leaf(execution_id, proofs, **kwargs)


def get_receipt(execution_id: str) -> Optional[Dict[str, Any]]:
    """Get verifiable receipt for execution"""
    return _merkle_store.get_receipt(execution_id)


def verify_receipt(receipt: Dict[str, Any]) -> bool:
    """Verify a receipt's inclusion proof"""
    return _merkle_store.verify_receipt(receipt)


def get_daily_root(date: str = None) -> Dict[str, Any]:
    """Get daily Merkle root"""
    return _merkle_store.get_daily_root(date)


def finalize_daily_root(date: str = None) -> Dict[str, Any]:
    """Finalize and store daily root"""
    return _merkle_store.finalize_daily_root(date)


def get_merkle_stats() -> Dict[str, Any]:
    """Get Merkle store statistics"""
    return _merkle_store.get_stats()
