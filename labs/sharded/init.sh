#!/usr/bin/env bash
set -euo pipefail

echo "Initializing config server replica set..."
docker exec cfg1 mongosh --port 27017 --quiet --eval \
  'rs.initiate({
    _id: "configrs",
    configsvr: true,
    members: [
      { _id: 0, host: "cfg1:27017" },
      { _id: 1, host: "cfg2:27017" },
      { _id: 2, host: "cfg3:27017" }
    ]
  })'

sleep 3

echo "Initializing shard 1 replica set..."
docker exec shard1a mongosh --port 27017 --quiet --eval \
  'rs.initiate({
    _id: "shard1rs",
    members: [
      { _id: 0, host: "shard1a:27017" },
      { _id: 1, host: "shard1b:27017" },
      { _id: 2, host: "shard1c:27017" }
    ]
  })'

echo "Initializing shard 2 replica set..."
docker exec shard2a mongosh --port 27017 --quiet --eval \
  'rs.initiate({
    _id: "shard2rs",
    members: [
      { _id: 0, host: "shard2a:27017" },
      { _id: 1, host: "shard2b:27017" },
      { _id: 2, host: "shard2c:27017" }
    ]
  })'

sleep 5

echo "Adding shards to mongos..."
docker exec mongos mongosh --port 27017 --quiet --eval \
  'sh.addShard("shard1rs/shard1a:27017,shard1b:27017,shard1c:27017")' 2>/dev/null || true
docker exec mongos mongosh --port 27017 --quiet --eval \
  'sh.addShard("shard2rs/shard2a:27017,shard2b:27017,shard2c:27017")' 2>/dev/null || true

echo "Sharded cluster initialized. mongos on localhost:27017"
