import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import Request
from fastapi.responses import JSONResponse

_bucket_lock = Lock()
_buckets: dict[str, deque[float]] = defaultdict(deque)


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "").strip()
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check_rate_limit(request: Request, key: str, limit: int, window_seconds: int) -> bool:
    """Return True when request is within limit, False when exceeded."""
    now = time.time()
    bucket_key = f"{key}:{_client_ip(request)}"
    with _bucket_lock:
        bucket = _buckets[bucket_key]
        cutoff = now - window_seconds
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= limit:
            return False
        bucket.append(now)
    return True


def rate_limit_response(message: str = "Too many requests. Please try again later.") -> JSONResponse:
    return JSONResponse(content={"status": "error", "message": message}, status_code=429)
