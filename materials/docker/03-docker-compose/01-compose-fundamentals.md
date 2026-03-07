---
kernelspec:
  name: python3
  language: python
  display_name: Python 3
---

# Docker Compose Fundamentals

## Overview

Managing multiple containers with `docker run` becomes tedious quickly. **Docker Compose** is a tool for defining and running multi-container applications using a YAML configuration file. With a single command, you can start all services, networks, and volumes your application needs.

In this section, you'll learn Docker Compose syntax, essential commands, and how to orchestrate multi-service applications.

## What is Docker Compose?

Docker Compose lets you define your entire application stack in a `docker-compose.yml` file:

```yaml
services:
  web:
    image: nginx
    ports:
      - "8080:80"
  db:
    image: postgres
    environment:
      POSTGRES_PASSWORD: secret
```

**One command to start everything:**
```bash
docker compose up
```

**Benefits:**
- **Declarative configuration:** Define your infrastructure as code
- **Reproducibility:** Same setup on every machine
- **Simplified workflow:** No memorizing long `docker run` commands
- **Service dependencies:** Control startup order
- **Environment-specific configs:** Override settings for dev/staging/prod

**Use cases:**
- Local development environments (web app + database + Redis + worker)
- Testing multi-service systems
- Small-scale deployments (not for production at scale—use Kubernetes for that)

## Installing Docker Compose

Docker Compose is included with **Docker Desktop** (macOS, Windows). On Linux, install it separately:

```bash
# Docker Compose V2 (recommended, included with Docker Desktop)
docker compose version

# Legacy V1 (older, uses docker-compose with hyphen)
docker-compose version
```

**Note:** This course uses **V2** (`docker compose` without hyphen). If you have V1, the syntax is identical but the command is `docker-compose`.

## Basic `docker-compose.yml` Structure

A `docker-compose.yml` file defines **services**, **networks**, and **volumes**.

**Minimal example:**
```yaml
services:
  web:
    image: nginx
    ports:
      - "8080:80"
```

**Run it:**
```bash
docker compose up
```

Docker Compose:
1. Creates a default network
2. Starts the `web` service (pulls `nginx` if needed)
3. Maps port 8080 on host to port 80 in container

**Stop it:**
```bash
docker compose down
```

This stops and removes containers (but not volumes, unless you add `--volumes`).

## Defining Services

Each service corresponds to a container. You can specify the image or build from a Dockerfile.

### Using an Image

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

### Building from a Dockerfile

```yaml
services:
  web:
    build: .
    ports:
      - "8000:8000"
```

Docker Compose builds the image from the Dockerfile in the current directory (`.`).

**Specify a custom Dockerfile:**
```yaml
services:
  web:
    build:
      context: .
      dockerfile: Dockerfile.dev
```

### Environment Variables

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: myapp
```

**Or use an env file:**
```yaml
services:
  db:
    image: postgres:16
    env_file:
      - .env
```

**`.env` file:**
```
POSTGRES_PASSWORD=secret
POSTGRES_DB=myapp
```

**Best Practice:** Store secrets in `.env` files and add `.env` to `.gitignore` to avoid committing them.

### Ports

Map host ports to container ports:

```yaml
services:
  web:
    image: nginx
    ports:
      - "8080:80"        # host:container
      - "8443:443"
```

### Volumes

**Named volume:**
```yaml
services:
  db:
    image: postgres
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

**Bind mount (host directory):**
```yaml
services:
  web:
    image: nginx
    volumes:
      - ./html:/usr/share/nginx/html  # relative path on host
```

### Container Name

By default, Compose generates names like `myapp-web-1`. Override with:

```yaml
services:
  web:
    container_name: my-custom-web
    image: nginx
```

**Best Practice:** Let Compose generate names unless you have a specific reason to override (e.g., connecting from outside Compose).

### Restart Policy

```yaml
services:
  web:
    image: nginx
    restart: unless-stopped
```

Options: `no`, `always`, `unless-stopped`, `on-failure`.

## Networking in Docker Compose

Compose automatically creates a **default network** for your application. All services can reach each other by **service name**.

**Example:**
```yaml
services:
  web:
    image: nginx
  redis:
    image: redis
```

Inside the `web` container:
```bash
ping redis
# Works! DNS resolves redis to the redis container's IP
```

### Custom Networks

Define multiple networks for segmentation:

```yaml
services:
  frontend:
    image: nginx
    networks:
      - frontend-net
  backend:
    image: myapi
    networks:
      - frontend-net
      - backend-net
  db:
    image: postgres
    networks:
      - backend-net

networks:
  frontend-net:
  backend-net:
```

**Result:**
- `frontend` and `backend` can communicate (both on `frontend-net`)
- `backend` and `db` can communicate (both on `backend-net`)
- `frontend` **cannot** reach `db` (no shared network)

## Dependencies with `depends_on`

Control service startup order:

```yaml
services:
  web:
    image: myapp
    depends_on:
      - db
      - redis
  db:
    image: postgres
  redis:
    image: redis
```

Compose starts `db` and `redis` before `web`.

**Limitation:** `depends_on` only waits for containers to **start**, not for services to be **ready**. If your app requires the database to accept connections before starting, use a wait script or health checks.

**Advanced: Health checks (Compose V2.1+)**
```yaml
services:
  db:
    image: postgres
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
  web:
    image: myapp
    depends_on:
      db:
        condition: service_healthy
```

Now `web` waits until `db` passes its health check.

## Essential Commands

### `docker compose up`

Start all services:

```bash
docker compose up
```

**Options:**
- **`-d`**: Detached mode (run in background)
- **`--build`**: Rebuild images before starting
- **`--scale service=N`**: Run N instances of a service

**Example:**
```bash
docker compose up -d
# Starts all services in background
```

### `docker compose down`

Stop and remove containers, networks (but not volumes):

```bash
docker compose down
```

**Remove volumes too:**
```bash
docker compose down --volumes
```

### `docker compose ps`

List running services:

```bash
docker compose ps
```

### `docker compose logs`

View logs from all services:

```bash
docker compose logs

# Follow logs (like tail -f)
docker compose logs -f

# Logs from a specific service
docker compose logs web

# Last 100 lines
docker compose logs --tail 100
```

### `docker compose exec`

Execute a command in a running service:

```bash
docker compose exec web bash
# Opens a shell in the web container

docker compose exec db psql -U postgres
# Opens psql in the db container
```

### `docker compose build`

Build or rebuild service images:

```bash
docker compose build

# Build a specific service
docker compose build web
```

### `docker compose restart`

Restart services without recreating containers:

```bash
docker compose restart web
```

### `docker compose stop` / `docker compose start`

Stop services without removing containers:

```bash
docker compose stop
docker compose start
```

## Full Example: Web App with Database and Redis

**Project structure:**
```
my-app/
├── docker-compose.yml
├── app/
│   ├── Dockerfile
│   ├── app.py
│   └── requirements.txt
└── .env
```

**docker-compose.yml:**
```yaml
services:
  web:
    build: ./app
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://postgres:secret@db/myapp
      REDIS_URL: redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./app:/app  # Bind mount for development (hot reload)

  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: myapp
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  pgdata:
```

**app/Dockerfile:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

**app/requirements.txt:**
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
psycopg2-binary==2.9.9
redis==5.0.1
```

**app/app.py:**
```{code-cell} python
from fastapi import FastAPI
import psycopg2
import redis
import os

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello from Compose!"}

@app.get("/db")
def test_db():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()[0]
    conn.close()
    return {"database": version}

@app.get("/redis")
def test_redis():
    r = redis.from_url(os.getenv("REDIS_URL"))
    r.set("test", "hello")
    value = r.get("test").decode()
    return {"redis": value}
```

**Run it:**
```bash
docker compose up --build
# Builds web image, starts all services

# Test endpoints
curl http://localhost:8000
curl http://localhost:8000/db
curl http://localhost:8000/redis

# View logs
docker compose logs -f web

# Stop everything
docker compose down
```

## Environment-Specific Configurations

Override settings for different environments with multiple Compose files.

**Base config (`docker-compose.yml`):**
```yaml
services:
  web:
    build: .
    ports:
      - "8000:8000"
```

**Development overrides (`docker-compose.override.yml`):**
```yaml
services:
  web:
    volumes:
      - ./app:/app  # Bind mount for hot reload
    command: uvicorn app:app --reload
```

**Production overrides (`docker-compose.prod.yml`):**
```yaml
services:
  web:
    restart: always
    environment:
      DEBUG: "false"
```

**Usage:**
```bash
# Dev (automatically loads docker-compose.override.yml)
docker compose up

# Prod (explicitly specify override file)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up
```

## Scaling Services

Run multiple instances of a service:

```bash
docker compose up -d --scale worker=3
```

This starts 3 instances of the `worker` service. Useful for load balancing or parallel processing.

**Best Practice:** Stateless services (workers, APIs) scale horizontally. Stateful services (databases) typically don't.

## At Scale: When to Use Docker Compose

**Good for:**
- **Local development:** Spin up your entire stack with one command
- **Testing:** Reproducible test environments
- **Small deployments:** Single-host applications (personal projects, small services)

**Not suitable for:**
- **Production at scale:** Compose doesn't handle multi-host orchestration, load balancing, or self-healing
- **High availability:** No built-in failover or health monitoring
- **Complex scheduling:** Limited control over resource allocation and placement

**For production:** Use **Kubernetes**, **Docker Swarm** (though Kubernetes is more common), or managed container services (AWS ECS, Google Cloud Run).

## Common Pitfalls

**1. Forgetting to rebuild after Dockerfile changes:**
```bash
docker compose up
# Uses cached image—need --build to rebuild
docker compose up --build
```

**2. Hardcoding localhost in connection strings:**
```python
# Bad: Assumes database is on localhost
conn = psycopg2.connect("postgresql://postgres:secret@localhost/myapp")

# Good: Use service name
conn = psycopg2.connect("postgresql://postgres:secret@db/myapp")
```

**3. Not using `.env` files for secrets:**
```yaml
# Bad: Secrets in docker-compose.yml
environment:
  API_KEY: abc123

# Good: Use .env file
env_file:
  - .env
```

**4. Leaving containers running after development:**
```bash
docker compose down
# Stops and removes containers (volumes persist)
```

## Summary

Docker Compose simplifies multi-container applications by defining services, networks, and volumes in a single YAML file. Use `docker compose up` to start everything, `docker compose down` to stop, and `docker compose logs` to view output. Services communicate by name on an automatically created network. Compose is ideal for local development but not production at scale.

**Key Takeaways:**
- **`docker-compose.yml`** defines services, networks, and volumes
- **`docker compose up`** starts all services
- **`docker compose down`** stops and removes containers
- Services communicate by **service name** via automatic DNS
- Use **`depends_on`** to control startup order
- Use **`.env` files** for environment-specific configuration
- Compose is for **development and small deployments**, not large-scale production

---

**Previous:** [Volumes and Networking](../02-working-with-docker/03-volumes-and-networking.md) | **Next:** [Distributed System Demo](02-distributed-system-demo.md)
