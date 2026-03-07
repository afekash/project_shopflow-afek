---
kernelspec:
  name: python3
  display_name: Python 3
  language: python
---

# Common Patterns

```{note}
This lesson requires the Redis lab. Run `make lab-redis` before starting.
```

Key-value stores solve a specific class of problems extremely well. This lesson walks through six patterns that appear constantly in production systems -- each one a natural fit for Redis's data model and O(1) lookup semantics.

---

## Setup

```{code-cell} python
import redis
import json
import time
import uuid

r = redis.Redis(host="redis", port=6379, decode_responses=True)
r.flushdb()
```

---

## Session Storage

Web sessions are naturally key-value: a session token maps to user state. The requirements align perfectly with Redis's strengths: random access by token, TTL for expiration, fast reads on every request.

A hash per session stores multiple fields efficiently without deserializing a JSON blob to read one field.

```{code-cell} python
token = str(uuid.uuid4())

# Store session as a hash -- each field accessible independently
r.hset(f"session:{token}", mapping={
    "user_id": "42",
    "role": "admin",
    "cart_items": "3",
    "last_seen": "2024-01-15T10:30:00",
})
r.expire(f"session:{token}", 3600)  # expire in 1 hour

# Reading: only fetch what you need
user_id = r.hget(f"session:{token}", "user_id")
role = r.hget(f"session:{token}", "role")
ttl = r.ttl(f"session:{token}")

print(f"Session {token[:8]}...")
print(f"  user_id: {user_id}, role: {role}")
print(f"  expires in: {ttl}s")
```

---

## Rate Limiting

Rate limiting requires: count requests per time window per identity, reject when over the limit. Redis's atomic `INCR` makes this trivially safe even with many concurrent clients -- no race conditions, no double-counting.

```{code-cell} python
def is_rate_limited(r, ip: str, limit: int = 5, window: int = 60) -> bool:
    # Key includes the current minute bucket -- auto-resets each minute
    minute_bucket = int(time.time() // window)
    key = f"rate:{ip}:{minute_bucket}"

    count = r.incr(key)
    if count == 1:
        r.expire(key, window)  # set TTL only on first increment

    return count > limit

# Simulate 7 requests from the same IP
ip = "192.168.1.100"
for i in range(7):
    limited = is_rate_limited(r, ip, limit=5)
    status = "BLOCKED" if limited else "OK"
    print(f"Request {i+1}: {status}")
```

The key insight: `INCR` is atomic. Whether 1 client or 1000 clients are incrementing simultaneously, each increment happens exactly once in sequence. No locking needed.

---

## Real-Time Leaderboard

A leaderboard needs: insert/update a score, query the top N, look up a player's rank. Redis sorted sets do all three in O(log n).

> **Core Concept:** See [Trees for Storage](../../core-concepts/02-data-structures/02-trees-for-storage.md) for why O(log n) is the right complexity for ordered operations. The sorted set uses a skip list -- a probabilistic data structure that achieves O(log n) for inserts and rank queries.

```{code-cell} python
players = [
    ("alice", 9850), ("bob", 9200), ("carol", 9500),
    ("dave", 8900), ("eve", 9700), ("frank", 7500),
]
for name, score in players:
    r.zadd("leaderboard:global", {name: score})

# Top 3 with scores
top3 = r.zrange("leaderboard:global", 0, 2, withscores=True, rev=True)
print("Top 3:")
for rank, (player, score) in enumerate(top3, 1):
    print(f"  #{rank} {player}: {int(score)}")

# Player's rank
total = r.zcard("leaderboard:global")
bobs_rank_from_bottom = r.zrank("leaderboard:global", "bob")
bobs_rank = total - bobs_rank_from_bottom
print(f"\nbob's rank: #{bobs_rank} of {total}")

# Score update -- O(log n)
r.zadd("leaderboard:global", {"bob": 9900})
print(f"bob's new score: {int(r.zscore('leaderboard:global', 'bob'))}")
```

---

## Job Queue

A queue needs: push jobs in, pop jobs out in order, ensure a job is processed by exactly one worker. Redis lists model this directly. `BRPOP` (blocking pop) is the key: a worker waits efficiently until a job is available, with no polling.

```{code-cell} python
# Producer: push jobs to queue
for i in range(5):
    job = json.dumps({"id": i, "task": "resize_image", "url": f"img_{i}.jpg"})
    r.lpush("queue:image_jobs", job)

print(f"Jobs in queue: {r.llen('queue:image_jobs')}")

# Consumer: pop and process (non-blocking version for demo)
while r.llen("queue:image_jobs") > 0:
    raw = r.rpop("queue:image_jobs")
    job = json.loads(raw)
    print(f"Processing job {job['id']}: {job['task']} on {job['url']}")
```

In production, workers use `BRPOP queue:image_jobs 0` -- blocking with no timeout. When the queue is empty, the worker sleeps efficiently instead of busy-polling. Multiple workers competing on the same queue means each job is processed by exactly one worker (Redis guarantees one `BRPOP` winner per item).

---

## Pub/Sub and Streams

Redis supports two messaging models. Pub/sub is fire-and-forget (no persistence). Streams are a durable append-only log with consumer groups.

> **Core Concept:** See [Pub/Sub and Messaging Patterns](../../core-concepts/07-application-patterns/02-pubsub-and-messaging.md) for the general concepts: fan-out vs queues, delivery guarantees, persistence tradeoffs.

**Redis Pub/Sub** -- use when real-time delivery matters more than durability. If a consumer is offline, the message is gone.

**Redis Streams** -- use when you need durability and replay. Each message gets a unique ID and is stored until explicitly deleted. Consumer groups allow multiple workers to process a stream in parallel, each getting different messages.

```{code-cell} python
# Streams: append events and read them back
msg_id1 = r.xadd("events:orders", {"type": "order.placed", "user_id": "42", "amount": "99.99"})
msg_id2 = r.xadd("events:orders", {"type": "order.paid", "order_id": "ord_1", "amount": "99.99"})
msg_id3 = r.xadd("events:orders", {"type": "order.shipped", "order_id": "ord_1"})

print(f"Stream length: {r.xlen('events:orders')} messages")

messages = r.xrange("events:orders", "-", "+")
for msg_id, data in messages:
    print(f"  [{msg_id}] {data['type']}")
```

The key difference from a list: messages in a stream are never removed by reading. Multiple consumer groups can each process the full stream independently -- analytics, notifications, and audit logging all consuming the same event stream.

---

## Feature Flags

Feature flags need to be read on every request (latency matters) and updated without deploys. Redis is ideal: a single GET is sub-millisecond, and updates propagate instantly to all application instances.

```{code-cell} python
r.set("feature:dark_mode", "true")
r.set("feature:new_checkout", "false")
r.set("feature:ai_recommendations", "true")

# Structured flags with rollout percentage
r.hset("feature:beta_dashboard", mapping={
    "enabled": "true",
    "rollout_pct": "20",
    "min_plan": "pro",
})

def is_enabled(r, flag: str) -> bool:
    val = r.get(f"feature:{flag}")
    return val == "true"

for flag in ["dark_mode", "new_checkout", "ai_recommendations"]:
    print(f"  {flag}: {is_enabled(r, flag)}")
```

---

**Next:** [Caching and Expiration →](04-caching-and-expiration.md)

---

[← Back: Value Types and Key Design](02-value-types-and-key-design.md) | [Course Home](../README.md)
