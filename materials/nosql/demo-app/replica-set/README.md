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

### Step 1 — Add hostnames to your hosts file

The replica set members advertise themselves as `mongo1`, `mongo2`, `mongo3` (Docker container names). Your machine needs to resolve those names to `127.0.0.1` so PyMongo can reach them after RS discovery.

**macOS / Linux:**
```bash
sudo sh -c 'echo "127.0.0.1 mongo1 mongo2 mongo3" >> /etc/hosts'
```

**Windows (WSL recommended):**
Running Docker Desktop with WSL 2 is the easiest path — open your WSL terminal and run the same command as Linux above. It will apply inside WSL where Python runs.

If you are running Python natively on Windows (not in WSL), open Notepad **as Administrator**, edit `C:\Windows\System32\drivers\etc\hosts`, and add:
```
127.0.0.1 mongo1 mongo2 mongo3
```

### Step 2 — Start and initialise the replica set

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
