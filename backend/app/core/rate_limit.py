import time
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import HTTPException, Request, status

# Simple in-memory limiter for MVP. Replace with Redis-based limiter in production scale.
_request_buckets: Dict[str, Deque[float]] = defaultdict(deque)


def limit_requests(key_prefix: str, window_seconds: int, max_requests: int):
    async def dependency(request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        key = f"{key_prefix}:{client_ip}"
        now = time.time()
        bucket = _request_buckets[key]
        while bucket and bucket[0] <= now - window_seconds:
            bucket.popleft()
        if len(bucket) >= max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again shortly.",
            )
        bucket.append(now)

    return dependency
