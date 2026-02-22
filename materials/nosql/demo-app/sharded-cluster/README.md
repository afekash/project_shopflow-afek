# Sharded Cluster Demo

A full MongoDB sharded cluster running in Docker:
- 1 config server replica set (3 nodes)
- 2 shard replica sets (3 nodes each)
- 1 mongos router

## Architecture

```
Application
    │
    ▼
mongos:27017  ← Connect here (port 27017 on localhost)
    │
    ├── Config RS:  cfg1:27017, cfg2:27017, cfg3:27017
    ├── Shard 1 RS: shard1a:27017, shard1b:27017, shard1c:27017
    └── Shard 2 RS: shard2a:27017, shard2b:27017, shard2c:27017
```

## Port Mapping (host → container)

| Container | Host Port | Role |
|-----------|-----------|------|
| mongos | 27017 | Application entry point |
| cfg1 | 27100 | Config server 1 |
| cfg2 | 27101 | Config server 2 |
| cfg3 | 27102 | Config server 3 |
| shard1a | 27110 | Shard 1 primary |
| shard1b | 27111 | Shard 1 secondary |
| shard1c | 27112 | Shard 1 secondary |
| shard2a | 27120 | Shard 2 primary |
| shard2b | 27121 | Shard 2 secondary |
| shard2c | 27122 | Shard 2 secondary |

## Quick Start

```bash
# Start all 10 containers
docker compose up -d

# Initialize replica sets, add shards, and insert test data (~1-2 minutes)
bash init-sharding.sh

# Connect via mongos (the application entry point)
mongosh "mongodb://localhost:27017"
```

## Useful Commands

```bash
# Check all containers
docker compose ps

# View mongos logs to see routing decisions
docker logs mongos -f

# Tear down everything including data volumes
docker compose down -v
```
