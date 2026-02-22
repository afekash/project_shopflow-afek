#!/bin/bash
# Initialize a full MongoDB sharded cluster:
#   - Config server replica set (configrs)
#   - Shard 1 replica set (shard1rs)
#   - Shard 2 replica set (shard2rs)
#   - mongos router
# Run AFTER docker compose up -d

set -e

echo "Waiting for all MongoDB nodes to start..."
sleep 15

# ─── Step 1: Initialize Config Server Replica Set ───────────────────────────
echo ""
echo ">>> Initializing config server replica set (configrs)..."
docker exec cfg1 mongosh --eval "
rs.initiate({
  _id: 'configrs',
  configsvr: true,
  members: [
    { _id: 0, host: 'cfg1:27017' },
    { _id: 1, host: 'cfg2:27017' },
    { _id: 2, host: 'cfg3:27017' }
  ]
})
"
sleep 5

# ─── Step 2: Initialize Shard 1 Replica Set ─────────────────────────────────
echo ""
echo ">>> Initializing shard 1 replica set (shard1rs)..."
docker exec shard1a mongosh --eval "
rs.initiate({
  _id: 'shard1rs',
  members: [
    { _id: 0, host: 'shard1a:27017', priority: 2 },
    { _id: 1, host: 'shard1b:27017', priority: 1 },
    { _id: 2, host: 'shard1c:27017', priority: 1 }
  ]
})
"
sleep 5

# ─── Step 3: Initialize Shard 2 Replica Set ─────────────────────────────────
echo ""
echo ">>> Initializing shard 2 replica set (shard2rs)..."
docker exec shard2a mongosh --eval "
rs.initiate({
  _id: 'shard2rs',
  members: [
    { _id: 0, host: 'shard2a:27017', priority: 2 },
    { _id: 1, host: 'shard2b:27017', priority: 1 },
    { _id: 2, host: 'shard2c:27017', priority: 1 }
  ]
})
"
sleep 10

# ─── Step 4: Add Shards to the Cluster via mongos ───────────────────────────
echo ""
echo ">>> Adding shards to the cluster via mongos..."
docker exec mongos mongosh --eval "
sh.addShard('shard1rs/shard1a:27017,shard1b:27017,shard1c:27017')
sh.addShard('shard2rs/shard2a:27017,shard2b:27017,shard2c:27017')
"
sleep 3

# ─── Step 5: Enable Sharding on the Demo Database ───────────────────────────
echo ""
echo ">>> Enabling sharding on the 'demo' database..."
docker exec mongos mongosh --eval "sh.enableSharding('demo')"

# ─── Step 6: Create Sharded Collections ─────────────────────────────────────
echo ""
echo ">>> Creating sharded collections..."
docker exec mongos mongosh --eval "
// Collection 1: hashed sharding on user_id (even distribution)
db.adminCommand({
  shardCollection: 'demo.events_hashed',
  key: { user_id: 'hashed' }
})

// Collection 2: ranged sharding on user_id (ordered distribution)
db.adminCommand({
  shardCollection: 'demo.events_ranged',
  key: { user_id: 1 }
})

print('Sharded collections created')
sh.status()
"

# ─── Step 7: Insert Test Data ───────────────────────────────────────────────
echo ""
echo ">>> Inserting 50,000 test documents into events_hashed..."
docker exec mongos mongosh --eval "
use demo

// Generate 50K events distributed across 1000 users
let count = 0
for (let userId = 1; userId <= 1000; userId++) {
  let batch = []
  for (let j = 0; j < 50; j++) {
    batch.push({
      user_id: 'user_' + String(userId).padStart(4, '0'),
      event_type: ['page_view', 'click', 'purchase', 'search'][j % 4],
      url: '/page/' + Math.floor(Math.random() * 100),
      timestamp: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000),
      session_id: 'sess_' + userId + '_' + Math.floor(j / 10),
      device: ['mobile', 'desktop', 'tablet'][j % 3]
    })
    count++
  }
  db.events_hashed.insertMany(batch)
}
print('Inserted ' + count + ' documents into events_hashed')
"

echo ""
echo ">>> Inserting 50,000 test documents into events_ranged..."
docker exec mongos mongosh --eval "
use demo
let count = 0
for (let userId = 1; userId <= 1000; userId++) {
  let batch = []
  for (let j = 0; j < 50; j++) {
    batch.push({
      user_id: 'user_' + String(userId).padStart(4, '0'),
      event_type: ['page_view', 'click', 'purchase', 'search'][j % 4],
      url: '/page/' + Math.floor(Math.random() * 100),
      timestamp: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000)
    })
    count++
  }
  db.events_ranged.insertMany(batch)
}
print('Inserted ' + count + ' documents into events_ranged')
"

# ─── Done ────────────────────────────────────────────────────────────────────
echo ""
echo "================================================================"
echo "Sharded cluster is ready!"
echo ""
echo "Application entry point (connect here):"
echo "  mongosh 'mongodb://localhost:27017'"
echo ""
echo "Component ports:"
echo "  mongos:  27017  (application entry point)"
echo "  cfg1:    27100"
echo "  cfg2:    27101"
echo "  cfg3:    27102"
echo "  shard1a: 27110  (shard1 primary)"
echo "  shard2a: 27120  (shard2 primary)"
echo ""
echo "Useful commands:"
echo "  sh.status()                                  -- cluster overview"
echo "  db.events_hashed.getShardDistribution()      -- chunk distribution"
echo "  db.events_hashed.find({user_id:'user_0001'}).explain('executionStats')"
echo "================================================================"
