# Replica Set Demo

A 3-node MongoDB replica set running in Docker containers.

## Architecture

```
┌──────────────────────────────────────────┐
│  Replica Set: rs0                        │
│                                          │
│  mongo1:27017  ← Primary (priority 2)   │
│  mongo2:27017  ← Secondary (priority 1) │
│  mongo3:27017  ← Secondary (priority 1) │
└──────────────────────────────────────────┘

Port mapping (host → container):
  27017 → mongo1
  27018 → mongo2
  27019 → mongo3
```

## Quick Start

```bash
# Start all 3 nodes
docker compose up -d

# Initialize the replica set and insert test data
bash init-replica.sh

# Connect to the primary
mongosh "mongodb://localhost:27017"

# Connect to all nodes via replica set URI (recommended)
mongosh "mongodb://localhost:27017,localhost:27018,localhost:27019/?replicaSet=rs0"
```

## Useful Commands

```bash
# Check status
docker compose ps

# View logs for primary
docker compose logs mongo1 -f

# Stop only the primary (to trigger election)
docker compose stop mongo1

# Restart the primary (it will rejoin as secondary)
docker compose start mongo1

# Tear down everything including volumes
docker compose down -v
```

## Connection via pymongo

```python
from pymongo import MongoClient, ReadPreference

# Replica set connection string
client = MongoClient(
    "mongodb://localhost:27017,localhost:27018,localhost:27019/?replicaSet=rs0"
)
db = client["demo"]
```
