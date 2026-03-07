---
kernelspec:
  name: python3
  language: python
  display_name: Python 3
---

# Consistent Hashing

## The Problem

You're distributing data across N nodes. The naive approach: `node_index = hash(key) % N`.

This works until you add or remove a node. When N changes to N+1:
- Every key's `hash(key) % N` produces a different result than `hash(key) % (N+1)`
- Almost every key maps to a *different* node than before
- You must move ~(N/(N+1)) of all keys -- nearly 100% of your data

```
3 nodes, hash(key) % 3:
  "user:1001" → hash % 3 = 2 → Node C
  "user:1002" → hash % 3 = 0 → Node A
  "user:1003" → hash % 3 = 1 → Node B

Add a 4th node, hash(key) % 4:
  "user:1001" → hash % 4 = 1 → Node B  (moved!)
  "user:1002" → hash % 4 = 2 → Node C  (moved!)
  "user:1003" → hash % 4 = 3 → Node D  (moved!)
```

All three keys moved. For a cluster with millions of keys, this is catastrophic -- a massive data migration every time you scale.

## The Solution

**Consistent hashing** -- place both nodes and keys on a virtual ring (a circular hash space from 0 to 2^32). Keys are assigned to the nearest node clockwise on the ring. When you add or remove a node, only the keys in one ring segment move -- a fraction proportional to 1/N of all keys.

## How It Works

### The Virtual Ring

Imagine a number line from 0 to 2^32 bent into a circle. Both nodes and keys are placed on this ring using their hash values.

```
                    ┌─── [Node 1: 0°] ───┐
                   ╱                      ╲
       Key D (340°)                        Key A (30°)
                 ╱                          ╲
      [Node 4: 270°]                    [Node 2: 90°]
                 ╲                          ╱
       Key C (240°)                        Key B (120°)
                   ╲                      ╱
                    └── [Node 3: 180°] ──┘

Each key routes clockwise to the nearest node:
  Key A ( 30°) → Node 2 ( 90°)
  Key B (120°) → Node 3 (180°)
  Key C (240°) → Node 4 (270°)
  Key D (340°) → Node 1 (  0°)  ← wraps around the ring
```

**Assignment rule**: each key belongs to the first node encountered when moving clockwise from the key's position.

### Adding a Node

A new node is placed at a position on the ring. Only the keys between the new node and its counterclockwise neighbor need to move.

```
Adding Node 5 at 60° (between Node 1 at 0° and Node 2 at 90°):

  Before:  Keys in range (0°, 90°] all land on Node 2

  After:   Keys in (0°, 60°]  → Node 5  (only these move)
           Keys in (60°, 90°] → Node 2  (unchanged)
           All other nodes and keys: completely unaffected ✓

                    ┌─── [Node 1: 0°] ─────────┐
                   ╱                             ╲
       Key D (340°)                   Key A (30°) ╲
                 ╱                           [Node 5: 60°] ← new
      [Node 4: 270°]                               │
                 ╲                           [Node 2: 90°]
       Key C (240°)╲              Key B (120°)    ╱
                    ╲                            ╱
                     └────── [Node 3: 180°] ─────┘

  Key A ( 30°) → Node 5 ( 60°)  ← moved! was going to Node 2
  Key B (120°) → Node 3 (180°)  ← unchanged
  Key C (240°) → Node 4 (270°)  ← unchanged
  Key D (340°) → Node 1 (  0°)  ← unchanged
```

With N existing nodes, adding one node moves only ~1/N of all keys. For a 10-node cluster, adding a node moves ~10% of keys -- not 100%.

### Removing a Node

The node's keys are reassigned to the next clockwise neighbor. Only the removed node's keys move.

```
Remove Node 3 (180°):
  Keys that were in (90°, 180°] → now go to Node 4 (270°)
  All other keys: unaffected ✓
```

### The Hotspot Problem: Virtual Nodes

With only a few physical nodes, their positions on the ring may be uneven, causing unequal load distribution. One node might own 40% of the ring while another owns 10%.

**Virtual nodes** solve this: instead of placing each physical node once on the ring, place it at many positions (100-300 virtual nodes per physical node). The ring positions for each physical node are spread evenly, producing statistically even load distribution.

```
Physical node → multiple ring positions (virtual nodes):
  Node A → positions at 12°, 87°, 143°, 201°, 267°, 318°...
  Node B → positions at  5°, 54°, 109°, 178°, 234°, 291°...
  Node C → positions at 31°, 73°, 168°, 215°, 248°, 337°...

Each key routes to the nearest virtual node clockwise,
which maps to a physical node.
```

Adding a physical node still moves only ~1/N of keys in total, but the moved keys come from small segments distributed across the ring rather than one large contiguous segment.

### Implementation Sketch

```{code-cell} python
import hashlib
import bisect

class ConsistentHashRing:
    def __init__(self, nodes=None, virtual_nodes=150):
        self.virtual_nodes = virtual_nodes
        self.ring = {}        # hash_position → node_name
        self.sorted_keys = [] # sorted ring positions
        for node in (nodes or []):
            self.add_node(node)

    def _hash(self, key):
        return int(hashlib.md5(key.encode()).hexdigest(), 16)

    def add_node(self, node):
        for i in range(self.virtual_nodes):
            position = self._hash(f"{node}:{i}")
            self.ring[position] = node
            bisect.insort(self.sorted_keys, position)

    def remove_node(self, node):
        for i in range(self.virtual_nodes):
            position = self._hash(f"{node}:{i}")
            del self.ring[position]
            self.sorted_keys.remove(position)

    def get_node(self, key):
        position = self._hash(key)
        idx = bisect.bisect(self.sorted_keys, position)
        if idx == len(self.sorted_keys):
            idx = 0  # wrap around
        return self.ring[self.sorted_keys[idx]]
```

## Trade-offs

**What you gain:**
- Adding or removing a node moves only ~1/N of all keys (vs. ~100% with modulo hashing)
- No global remapping required -- only neighbors are affected
- Works well for independent keys (no relationships between keys)

**What you give up:**
- Requires maintaining ring state (which node owns which position)
- Virtual nodes add implementation complexity
- Range queries across the ring are expensive -- consecutive keys may be on different nodes
- When keys are *not* independent (joins between them are needed), consistent hashing across nodes requires cross-node queries for every join

## An Alternative: Hash Slots

Instead of a continuous ring, some systems divide the hash space into a **fixed number of discrete slots** (commonly 16,384). Every key maps to a slot via `slot = hash(key) % NUM_SLOTS`. The slots themselves are then explicitly assigned to physical nodes -- and that assignment is fully operator-controlled.

```
Total: 16,384 slots

Node A → slots     0 – 5,460   (1/3 of slots)
Node B → slots 5,461 – 10,922  (1/3 of slots)
Node C → slots 10,923 – 16,383 (1/3 of slots)

hash("user:1001") % 16384 = 3271  → Node A
hash("user:1002") % 16384 = 8102  → Node B
hash("user:1003") % 16384 = 12500 → Node C
```

The critical insight: the `hash(key) → slot` mapping is computed and **never changes**. Only the `slot → node` assignment changes when you scale. This separates the two concerns cleanly.

### Adding a Node

When you add Node D, you decide which slots to migrate and from which existing nodes:

```
Before:
  Node A → slots     0 – 5,460
  Node B → slots 5,461 – 10,922
  Node C → slots 10,923 – 16,383

After adding Node D (operator reassigns manually):
  Node A → slots     0 – 4,095    (donated 1,365 slots to D)
  Node B → slots 5,461 – 9,556    (donated 1,365 slots to D)
  Node C → slots 10,923 – 15,018  (donated 1,365 slots to D)
  Node D → slots 4,096 – 5,460,   ← receives donated slots
                 9,557 – 10,922,
                15,019 – 16,383
```

Only keys that map to the migrated slots actually move. You control exactly how much data transfers -- but you must do the math and initiate the migration yourself.

### Key Co-location with Hash Tags

A powerful capability of hash slots: you can **force multiple keys to land in the same slot** by tagging them with a shared identifier. The hash function only uses the portion inside `{}`:

```
hash("user:1001")               → slot 3271  (Node A)
hash("session:1001")            → slot 9102  (Node B) ← different node!

# With hash tags -- only the bracketed part is hashed:
hash("{user:1001}.profile")     → hash("user:1001") → slot 3271 (Node A)
hash("{user:1001}.session")     → hash("user:1001") → slot 3271 (Node A)
hash("{user:1001}.preferences") → hash("user:1001") → slot 3271 (Node A)
```

All three keys land on the same node. Multi-key operations on related data (atomic updates, local joins) require no cross-node coordination. This is impossible in consistent hashing -- two keys hash independently and land wherever the ring puts them.

### Intentional Uneven Distribution

Because slot assignment is explicit, you can deliberately give a more powerful node a larger share of the data:

```
Node A (8 cores, 64 GB RAM) → slots     0 – 8,191   (50% of data)
Node B (4 cores, 32 GB RAM) → slots 8,192 – 12,287  (25% of data)
Node C (4 cores, 32 GB RAM) → slots 12,288 – 16,383 (25% of data)
```

Consistent hashing can approximate this with more virtual nodes on Node A, but it remains probabilistic. With hash slots the proportion is exact.

### The Risk: Operator-Controlled Means Operator-Responsible

Hash slots trade automation for control. The system will not protect you from poor decisions:

- Assign too many slots to a weak node → that node becomes a bottleneck for a predictable fraction of all keys
- Forget to rebalance after adding a node → one node stays overloaded indefinitely
- Use hash tags aggressively → all tagged keys pile onto one slot, creating a hot spot

With consistent hashing, virtual nodes smooth out imbalances probabilistically. With hash slots, the distribution is exactly what you configured -- good or bad.

## Consistent Hashing vs. Hash Slots

| | Consistent Hashing | Hash Slots |
|---|---|---|
| Adding a node | Automatic (ring position determines what moves) | Manual (operator decides which slots migrate) |
| Load balance | Statistical (virtual nodes spread load) | Exact (operator controls slot counts) |
| Key co-location | Not supported | Supported via hash tags |
| Heterogeneous nodes | Approximated (more virtual nodes) | Exact (assign proportional slot counts) |
| Risk of imbalance | Low -- probabilistically even | High -- operator error leads to hard skew |
| Operational complexity | Lower | Higher |

> **Advanced Note:** Hash slots are best suited for workloads where you need fine-grained control over data placement: co-locating related keys, accommodating hardware heterogeneity, or applying tiered storage policies. If your keys are independent and nodes are homogeneous, consistent hashing reaches a good distribution automatically.

## Where You'll See This

- **Distributed caches**: Cache clusters use consistent hashing so that adding a cache node doesn't invalidate every cached item
- **Distributed key-value stores**: Each key maps to one node without a central coordinator
- **Content delivery**: Routing requests for a URL to the same edge cache server consistently
- **Load balancers**: Sticky session routing (same client always reaches the same server) using consistent hashing on the client IP

---

**Next:** [CAP Theorem →](../04-distributed-systems/01-cap-theorem.md)
