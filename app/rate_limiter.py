import time
from collections import defaultdict, deque

class TokenBucketRateLimiter:
    def __init__(self, rate: int, per: float):
        self.rate = rate
        self.per = per
        self.buckets = defaultdict(lambda: deque())

    def allow(self, key: str) -> bool:
        now = time.time()
        q = self.buckets[key]

        while q and now - q[0] > self.per:
            q.popleft()

        if len(q) < self.rate:
            q.append(now)
            return True
        return False


rate_limiter = TokenBucketRateLimiter(rate=5, per=1.0)
