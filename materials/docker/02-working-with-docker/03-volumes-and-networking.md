---
kernelspec:
  name: python3
  language: python
  display_name: Python 3
---

# Volumes and Networking

## Overview

By default, containers are ephemeral—data created inside them disappears when the container is removed. **Volumes** solve this by persisting data outside the container's lifecycle. Similarly, containers are isolated by default, but **networking** allows them to communicate with each other and the outside world.

In this section, you'll learn how to persist data with volumes and bind mounts, and how to connect containers using Docker networks.

## The Problem: Ephemeral Containers

Containers use a writable layer on top of read-only image layers. When you remove the container, the writable layer is deleted.

**Example:**
```bash
# Start PostgreSQL container
docker run -d --name db -e POSTGRES_PASSWORD=secret postgres

# Create a database and table
docker exec db psql -U postgres -c "CREATE DATABASE myapp;"
docker exec db psql -U postgres -d myapp -c "CREATE TABLE users (id SERIAL, name TEXT);"
docker exec db psql -U postgres -d myapp -c "INSERT INTO users (name) VALUES ('Alice');"

# Verify data exists
docker exec db psql -U postgres -d myapp -c "SELECT * FROM users;"
# Output: id | name
#          1 | Alice

# Remove container
docker rm -f db

# Start a new container
docker run -d --name db -e POSTGRES_PASSWORD=secret postgres

# Data is gone!
docker exec db psql -U postgres -d myapp -c "SELECT * FROM users;"
# ERROR: database "myapp" does not exist
```

**The solution:** Use volumes to persist data outside the container.

## Volumes: Persistent Storage

**Volumes** are Docker-managed storage that persists independently of containers. They're stored on the host filesystem (in Docker's storage area) and can be shared across containers.

### Creating and Using Volumes

```bash
# Create a volume
docker volume create mydata

# List volumes
docker volume ls

# Inspect a volume
docker volume inspect mydata
```

**Mount a volume into a container:**
```bash
docker run -d --name db -e POSTGRES_PASSWORD=secret -v mydata:/var/lib/postgresql/data postgres
```

**Syntax:** `-v VOLUME_NAME:CONTAINER_PATH`

Now, data written to `/var/lib/postgresql/data` inside the container is stored in the `mydata` volume. If you remove the container and start a new one with the same volume, the data persists.

**Example with persistence:**
```bash
# Start container with volume
docker run -d --name db -e POSTGRES_PASSWORD=secret -v pgdata:/var/lib/postgresql/data postgres

# Create data
docker exec db psql -U postgres -c "CREATE DATABASE myapp;"

# Remove container
docker rm -f db

# Start new container with same volume
docker run -d --name db2 -e POSTGRES_PASSWORD=secret -v pgdata:/var/lib/postgresql/data postgres

# Data still exists!
docker exec db2 psql -U postgres -c "\l"
# Output: myapp database is listed
```

### Automatic Volume Creation

Docker automatically creates a volume if you reference one that doesn't exist:

```bash
docker run -d --name db -e POSTGRES_PASSWORD=secret -v mydb:/var/lib/postgresql/data postgres
# Volume "mydb" is created automatically if it doesn't exist
```

### Removing Volumes

```bash
# Remove a volume (only if no container is using it)
docker volume rm mydata

# Remove all unused volumes
docker volume prune
```

**Best Practice:** Name your volumes explicitly (`-v mydata:/path`) for clarity. Docker also creates anonymous volumes (e.g., when Dockerfile has `VOLUME` instruction), which clutter the system—remove them with `docker volume prune`.

## Bind Mounts: Host Directory as Volume

**Bind mounts** map a host directory or file directly into a container. Unlike volumes, bind mounts can be anywhere on the host filesystem.

**Syntax:**
```bash
docker run -v /host/path:/container/path image
```

**Example: Mount current directory into container**
```bash
# Mount current directory to /app in container
docker run -it --rm -v $(pwd):/app -w /app python:3.11 bash

# Inside container:
root@abc123:/app# ls
# Shows files from your host's current directory

root@abc123:/app# touch newfile.txt
# newfile.txt appears on your host immediately
```

**Use cases:**
1. **Development workflow:** Edit code on your host, see changes immediately in the container (hot reload)
2. **Configuration files:** Inject config files from host into container
3. **Logs:** Write logs to host filesystem for persistence

**Example: Running a web app with live code reload**
```bash
# Project structure:
# my-app/
# ├── app.py
# └── Dockerfile

# Run with bind mount (code changes reflected immediately)
docker run -d -p 8000:8000 -v $(pwd):/app myapp

# Edit app.py on host → container sees changes → app reloads (if configured)
```

### Volumes vs. Bind Mounts

| Aspect | Volumes | Bind Mounts |
|--------|---------|-------------|
| **Location** | Docker-managed (`/var/lib/docker/volumes/`) | Any host path |
| **Management** | Managed by Docker (create, list, remove) | Manual (just a directory) |
| **Performance** | Fast (especially on macOS/Windows Docker Desktop) | Can be slower on macOS/Windows due to filesystem sharing |
| **Portability** | Portable across Docker hosts | Host-specific paths (less portable) |
| **Use case** | Production data (databases, logs) | Development (code, config) |

**Best Practice:**
- Use **volumes** for production data (databases, persistent state)
- Use **bind mounts** for development (code, configuration)

## Read-Only Mounts

You can mount volumes or bind mounts as read-only to prevent the container from modifying data:

```bash
docker run -d -v mydata:/data:ro nginx
# Container can read from /data but cannot write
```

**Use case:** Mounting configuration files that shouldn't be modified by the container.

## Container Networking Basics

Docker provides networking to allow containers to communicate with each other and the outside world.

### Default Networks

When you install Docker, it creates three networks:

```bash
docker network ls
# Output:
# NETWORK ID     NAME      DRIVER    SCOPE
# abc123...      bridge    bridge    local
# def456...      host      host      local
# ghi789...      none      null      local
```

1. **bridge** (default): Containers on this network can communicate with each other via IP addresses
2. **host**: Container shares the host's network stack (no isolation)
3. **none**: No networking (isolated)

**By default, containers use the `bridge` network.**

### Container-to-Container Communication on Bridge Network

Containers on the same bridge network can communicate using each other's **IP addresses** or **container names** (via Docker's built-in DNS).

**Example: Two containers communicating**

```bash
# Start first container (Redis)
docker run -d --name redis redis

# Start second container (client)
docker run -it --rm alpine sh

# Inside client container, install redis-cli and connect to redis
apk add redis
redis-cli -h redis ping
# Output: PONG
```

**How it works:**
- Docker's internal DNS resolves `redis` (container name) to the Redis container's IP
- Both containers are on the default bridge network

**Limitation of default bridge:** Container name DNS resolution works, but Docker recommends using custom networks for better isolation.

### Creating Custom Networks

Custom networks provide better DNS resolution and isolation.

```bash
# Create a custom bridge network
docker network create mynetwork

# Start containers on this network
docker run -d --name redis --network mynetwork redis
docker run -d --name webapp --network mynetwork -p 8000:8000 mywebapp

# webapp can reach redis by name:
# redis://redis:6379
```

**Benefits of custom networks:**
- **Automatic DNS:** Containers resolve each other by name
- **Isolation:** Containers on different networks cannot communicate (unless connected to the same network)
- **Easy to manage:** Attach/detach containers from networks dynamically

### Connecting Multiple Networks

A container can be connected to multiple networks:

```bash
docker network create frontend
docker network create backend

# Start database on backend network
docker run -d --name db --network backend postgres

# Start API on both networks
docker run -d --name api --network backend myapi
docker network connect frontend api

# Start web server on frontend network
docker run -d --name web --network frontend nginx
```

**Result:**
- `web` can reach `api` (both on `frontend`)
- `api` can reach `db` (both on `backend`)
- `web` **cannot** reach `db` (not on the same network)

This provides network segmentation for security.

### Inspecting Networks

```bash
# List networks
docker network ls

# Inspect a network (see connected containers)
docker network inspect mynetwork

# View container's network settings
docker inspect -f '{{.NetworkSettings.Networks}}' mycontainer
```

### Host Network Mode

Use `--network host` to share the host's network stack:

```bash
docker run -d --network host nginx
# nginx listens on host's port 80 directly (no port mapping needed)
```

**Use case:** Maximum network performance (no NAT overhead). Rarely used because it eliminates network isolation.

## Real-World Example: Web App with Database

Let's run a web app (FastAPI) that connects to a PostgreSQL database.

**Project structure:**
```
my-app/
├── app.py
├── requirements.txt
├── Dockerfile
└── docker-compose.yml (covered in next section)
```

**app.py:**
```{code-cell} python
from fastapi import FastAPI
import psycopg2

app = FastAPI()

@app.get("/")
def read_root():
    conn = psycopg2.connect("postgresql://postgres:secret@db/myapp")
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()[0]
    conn.close()
    return {"message": "Connected to database", "version": version}
```

**Manual setup (we'll automate this with Docker Compose later):**

```bash
# Create a custom network
docker network create myapp-network

# Start PostgreSQL on the network
docker run -d --name db --network myapp-network -e POSTGRES_PASSWORD=secret -e POSTGRES_DB=myapp -v pgdata:/var/lib/postgresql/data postgres

# Build and start the web app on the same network
docker build -t myapp .
docker run -d --name webapp --network myapp-network -p 8000:8000 myapp

# Test it
curl http://localhost:8000
# Output: {"message": "Connected to database", "version": "PostgreSQL 16..."}
```

**How it works:**
- `webapp` container connects to `db` by name (`postgresql://...@db/myapp`)
- Both containers are on `myapp-network`, so DNS resolves `db` to the database container's IP
- The `-v pgdata:/var/lib/postgresql/data` persists database data across container restarts

## Volume Lifecycle Management

**Scenario:** You want to backup and restore database data.

**Backup:**
```bash
# Create a backup by running a temporary container
docker run --rm -v pgdata:/data -v $(pwd):/backup alpine tar czf /backup/pgdata-backup.tar.gz -C /data .

# Creates pgdata-backup.tar.gz on host
```

**Restore:**
```bash
# Restore from backup
docker run --rm -v pgdata:/data -v $(pwd):/backup alpine tar xzf /backup/pgdata-backup.tar.gz -C /data
```

**Best Practice:** Automate backups with scripts or orchestration tools (e.g., Kubernetes CronJobs).

## At Scale: Volume Drivers and Shared Storage

In production, you often need volumes that work across multiple hosts (e.g., in a Docker Swarm or Kubernetes cluster).

**Volume drivers:**
- **local** (default): Stored on the Docker host
- **nfs**: Network File System (shared across hosts)
- **aws-efs**: Amazon Elastic File System
- **gcsfuse**: Google Cloud Storage
- **azure-file**: Azure Files

**Example: NFS volume**
```bash
docker volume create --driver local --opt type=nfs --opt o=addr=192.168.1.100,rw --opt device=:/path/to/share nfs-volume

docker run -d -v nfs-volume:/data myapp
```

In cloud environments, managed volume services (EBS in AWS, Persistent Disks in GCP) integrate with orchestrators like Kubernetes.

## Cleaning Up Storage

Docker can consume significant disk space over time. Clean up unused resources:

```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune

# Remove everything unused (containers, images, volumes, networks)
docker system prune --volumes
```

**Check disk usage:**
```bash
docker system df
# Output:
# TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
# Images          10        5         2.5GB     1.2GB (48%)
# Containers      15        5         500MB     300MB (60%)
# Local Volumes   8         3         5GB       2GB (40%)
```

## Common Pitfalls

**1. Forgetting to use volumes for databases:**
```bash
docker run -d postgres
# Data disappears when container is removed—always use -v
```

**2. Using bind mounts in production:**
```bash
docker run -v /host/path:/data myapp
# Ties your container to a specific host—use volumes instead
```

**3. Not cleaning up volumes:**
```bash
docker rm mycontainer
# Volume still exists—need docker volume rm or docker volume prune
```

**4. Containers not finding each other by name:**
```bash
# Default bridge network requires --link (deprecated)
# Solution: Use custom networks
docker network create mynet
docker run --network mynet --name db postgres
docker run --network mynet myapp  # Can reach db by name
```

## Summary

Volumes persist data beyond container lifetime, while bind mounts map host directories into containers. Docker networks enable container-to-container communication via DNS. Use volumes for production data, bind mounts for development, and custom networks for isolated, name-based service discovery.

**Key Takeaways:**
- **Volumes** (`-v mydata:/path`) persist data managed by Docker
- **Bind mounts** (`-v $(pwd):/path`) map host directories for development
- **Custom networks** enable containers to communicate by name
- Containers on the same network resolve each other via DNS
- Use `docker volume prune` and `docker system prune` to clean up unused resources
- In production, use volumes with appropriate drivers (EBS, NFS) for multi-host scenarios

---

**Previous:** [Running Containers](02-running-containers.md) | **Next:** [Compose Fundamentals](../03-docker-compose/01-compose-fundamentals.md)
