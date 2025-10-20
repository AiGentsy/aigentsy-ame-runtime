
# risk_policies.py
def score(play: str, region: str, channel: str) -> float:
    base = 0.1
    if region not in ("US","CA","UK","EU"): base += 0.2
    if channel in ("sms","cold_email"): base += 0.3
    return min(1.0, base)
def should_throttle(score_val: float) -> bool: return score_val >= 0.5
