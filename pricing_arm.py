
# pricing_arm.py
from typing import Dict, Any, List
from collections import defaultdict
import random
class PricingARM:
    def __init__(self, epsilon: float = 0.1):
        self.epsilon = epsilon; self.stats = defaultdict(lambda: {"n":0, "sum":0.0})
    def start_bundle_test(self, bundles: List[str]): return self.select_best_arm(bundles)
    def record_outcome(self, bundle_id: str, rev_usd: float):
        s = self.stats[bundle_id]; s["n"] += 1; s["sum"] += float(rev_usd)
    def mean(self, bundle_id: str) -> float:
        s = self.stats[bundle_id]; return 0.0 if s["n"] == 0 else s["sum"]/s["n"]
    def select_best_arm(self, bundles: List[str]):
        if not bundles: return None
        return random.choice(bundles) if random.random() < self.epsilon else max(bundles, key=lambda b: self.mean(b))
ARM = PricingARM()
