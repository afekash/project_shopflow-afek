# NoSQL Theory Exercises

These exercises test your understanding of NoSQL concepts, CAP theorem, and database selection. They work best as group discussions during class.

---

## Part 1: CAP Theorem Scenarios

For each scenario below, a network partition has occurred. Decide whether the system should prioritize **Consistency (C)** or **Availability (A)**, and justify your reasoning.

**Scenario 1: Online Banking Transfer**
> A user transfers €500 from account A to account B. A network partition separates the two database nodes. Node 1 has processed the debit from account A. Node 2 has not yet received the credit to account B.
>
> Should the system: (a) reject all further reads and writes until the partition is healed, or (b) continue serving reads that may show stale balances?

<details>
<summary>Discussion points</summary>

- This is a clear **CP** case. Showing stale balances (A appears debited, B appears not credited) could cause double-spending or user panic.
- Banks historically choose CP -- they'd rather be briefly unavailable than show incorrect balances.
- Real-world nuance: many banking systems use queued transfers with eventual consistency internally, but from the user's perspective the interface is synchronous and shows the correct final state.

</details>

---

**Scenario 2: Social Media "Like" Counter**
> Instagram's like counter on a photo shows 14,302 likes. The network partition means some nodes still show 14,301 (the previous value before one user liked the post). Users in different regions may see different counts for up to 30 seconds.
>
> Is this acceptable? What would you choose?

<details>
<summary>Discussion points</summary>

- This is a clear **AP** case. The cost of seeing a like count off by 1-2 is zero.
- Instagram (and most social media) uses eventual consistency for engagement counters. Facebook's actual implementation uses CRDTs (Conflict-free Replicated Data Types) which converge automatically without coordination.
- Choosing CP here would mean the like button becomes unavailable during a partition -- unacceptable for user experience.

</details>

---

**Scenario 3: E-Commerce Inventory**
> An e-commerce site shows "3 items in stock" for a limited-edition sneaker. A network partition occurs. Two users in different regions both try to buy the last item simultaneously. Each sees "1 in stock."
>
> What are the consequences of CP vs AP here? Which would you choose for the checkout step vs the product listing page?

<details>
<summary>Discussion points</summary>

- This is nuanced -- it depends on which operation.
- **Product listing page**: AP is acceptable. Showing "1 in stock" when it's actually 0 (or vice versa) on the listing page is annoying but not catastrophic. Use eventual consistency for inventory display.
- **Checkout/payment step**: CP is required. Both users cannot successfully purchase the same last item. The checkout must verify inventory atomically -- prefer CP or use optimistic concurrency (try to reserve, fail gracefully if already taken).
- Real pattern: many systems use a "soft reservation" -- reserve inventory in a fast CP system (Redis with SETNX) at checkout, display from eventually consistent catalog.

</details>

---

**Scenario 4: DNS Record Update**
> You update a DNS A record to point to a new IP address. DNS propagation takes up to 48 hours because DNS resolvers cache records and serve from cache (stale data) until the TTL expires.
>
> Is this an AP or CP system? Is this acceptable?

<details>
<summary>Discussion points</summary>

- **AP** system -- DNS serves stale data (the old IP) during propagation. Resolvers continue serving cached responses even though the authoritative server has different data.
- This is by design and widely acceptable because: (a) most records are stable, (b) short TTLs mitigate staleness, (c) availability of DNS is critical for the entire internet.
- Imagine if DNS chose CP: every resolution would require consensus with authoritative servers worldwide -- the latency would be unacceptable.

</details>

---

## Part 2: ACID vs BASE

**Exercise 5: Classify the Transaction**

For each operation below, decide whether it requires **ACID** guarantees or whether **BASE** (eventual consistency) is acceptable. Explain why.

| Operation | ACID or BASE? | Why? |
|-----------|--------------|------|
| User places an order and pays | | |
| User watches a video (view count +1) | | |
| User updates their profile bio | | |
| Refund processed to a credit card | | |
| User's recommended feed generated | | |
| Flight seat reservation during booking | | |
| Product review submitted | | |

<details>
<summary>Answers</summary>

| Operation | ACID or BASE? | Why? |
|-----------|--------------|------|
| User places an order and pays | ACID | Money movement, inventory deduction -- must be atomic and durable |
| User watches a video (view count +1) | BASE | Losing a few view counts is acceptable. Use eventual consistency. |
| User updates their profile bio | Depends | Read-your-writes is needed (user must see their own change), but true global consistency can be eventual |
| Refund processed to a credit card | ACID | Financial transaction -- must be durable and exactly-once |
| User's recommended feed generated | BASE | Stale recommendations are fine; this is a background computation |
| Flight seat reservation | ACID | Double-booking is catastrophic -- must be atomic across inventory and payment |
| Product review submitted | BASE | Slight delay before review appears globally is acceptable |

</details>

---

## Part 3: Database Selection

**Exercise 6: Choose the Right Database**

For each system below, recommend a database type (or combination) and explain your reasoning. Reference the decision framework from [Choosing the Right Database](../02-nosql-types/05-choosing-the-right-database.md).

**System A: Real-time game leaderboard**
> A mobile game with 5 million daily active players. Players earn points throughout the day. The app shows the top 100 players globally, updated within seconds of any score change. The game also shows each player their own rank.

<details>
<summary>Discussion</summary>

**Redis sorted set** is the obvious choice.
- `ZADD leaderboard <score> <player_id>` -- O(log n) update
- `ZRANGE leaderboard 0 99 WITHSCORES REV` -- top 100 in O(log n + 100)
- `ZRANK leaderboard <player_id>` -- player's own rank in O(log n)
- Sub-millisecond for all operations at any scale
- Persistence: use Redis AOF for durability, or accept losing ~1 second of data on restart

Additional consideration: a relational database with `ORDER BY score LIMIT 100` would work for thousands of players but degrades at millions of rows with frequent updates.

</details>

---

**System B: Medical records system**
> A hospital's electronic health records system. Doctors view and update patient records. Multiple departments may update the same patient record simultaneously (diagnostics, pharmacy, nursing notes). Regulatory compliance requires a full audit trail of all changes.

<details>
<summary>Discussion</summary>

**PostgreSQL (or another relational database)** is the right choice.
- ACID transactions are required -- two doctors updating the same record must not corrupt data
- Complex joins: patient → diagnoses → medications → prescriptions → lab results
- Audit trail: relational triggers or event sourcing with an append-only table
- Regulatory compliance (HIPAA, GDPR) favors well-understood, mature databases

MongoDB could work for unstructured clinical notes (variable fields per specialty), but the transactional requirements favor relational.

Hybrid option: PostgreSQL for core records with JSONB for flexible clinical notes.

</details>

---

**System C: IoT sensor platform**
> 50,000 IoT sensors each report temperature, humidity, and pressure readings every 10 seconds. That's 5,000 writes per second, 15 values per write. You need to query: "give me all readings for sensor X in the last 24 hours" and run 5-minute aggregations across all sensors.

<details>
<summary>Discussion</summary>

**Apache Cassandra** (or a purpose-built time-series DB like InfluxDB or TimescaleDB).
- 5,000 writes/second sustained → LSM-tree write path handles this comfortably
- Data model: partition key = sensor_id + date_bucket, clustering key = timestamp → "all readings for sensor X in the last 24 hours" is a targeted single-partition query
- Wide rows store all time-series points for a sensor in one partition
- Aggregations: Cassandra itself doesn't do complex aggregations well -- pair with Apache Spark or a time-series aggregation layer

If the team already uses PostgreSQL and scale is moderate: TimescaleDB (PostgreSQL extension for time-series) is a pragmatic option that avoids adding a new system.

</details>

---

## Part 4: Architecture Design

**Exercise 7: Design the Data Layer**

Design the data layer for the following system. Specify which database(s) to use, what data lives where, and why.

**System: Video Streaming Platform (similar to YouTube)**

Requirements:
- 100 million registered users
- 500 million videos
- Each video has: title, description, tags, views count, likes count, comments (potentially thousands per video)
- Users subscribe to channels (other users)
- Home feed: "latest videos from channels I subscribe to"
- Search: full-text search on video title and description
- Recommendation: "videos similar to what you watched"
- Analytics: video view counts, watch time, geographic distribution of viewers

Questions to answer:
1. What databases would you use?
2. What data lives in each database?
3. What are the access patterns for each data store?
4. What is the eventual consistency story for view counts?

There is no single right answer -- this is a design exercise with trade-offs.

---

**Next:** [MongoDB Exercises →](02-mongodb-exercises.md)

---

[← Back: Hands-On Sharded Cluster](../05-mongodb-sharding/02-hands-on-sharded-cluster.md) | [Course Home](../README.md)
