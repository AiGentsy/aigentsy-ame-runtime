import hashlib, time, random, requests, datetime as dt
HTTP = requests.Session()
HTTP.headers.update({"User-Agent": "AiGentsy/MetaBridge 1.1"})
def _id_key(payload: dict) -> str:
    try: raw = repr(sorted(payload.items())).encode("utf-8")
    except Exception: raw = repr(payload).encode("utf-8")
    import hashlib; return hashlib.sha1(raw).hexdigest()[:16]
def http_post_json(url: str, payload: dict, retries: int = 3, timeout: int = 12):
    headers = {"Content-Type": "application/json",
               "X-Idempotency-Key": _id_key(payload),
               "X-Correlation-Id": payload.get("correlation_id", _id_key(payload)),
               "X-Sent-At": dt.datetime.utcnow().isoformat()}
    last = {"error":"no attempt"}
    for i in range(retries):
        try:
            r = HTTP.post(url, json=payload, headers=headers, timeout=timeout)
            if r.status_code // 100 == 2:
                if r.headers.get("content-type","").lower().startswith("application/json"):
                    return True, r.json()
                return True, {"text": r.text}
            if r.status_code >= 500:
                time.sleep((2**i) + random.random()*0.2); continue
            return False, {"status": r.status_code, "text": r.text[:500]}
        except Exception as e:
            last = {"error": str(e)}
            time.sleep((2**i) + random.random()*0.2)
    return False, last
