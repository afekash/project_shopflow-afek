---
kernelspec:
  name: python3
  language: python
  display_name: Python 3
---

# Exercise: Containerize a FastAPI App

## Overview

In this exercise, you'll containerize a FastAPI application from scratch. You'll write a Dockerfile, build an image, run the container, and test the API. This hands-on exercise reinforces everything you've learned about Docker images and containers.

**Duration:** 20-30 minutes

**Skills practiced:**
- Writing a Dockerfile
- Building and tagging images
- Running containers with port mapping
- Testing containerized applications

## Starting Code

You're provided with a simple FastAPI application. Your task is to containerize it.

**Project structure:**
```
fastapi-app/
├── main.py
├── requirements.txt
└── Dockerfile (you'll create this)
```

**main.py:**
```{code-cell} python
from fastapi import FastAPI
from pydantic import BaseModel
import datetime

app = FastAPI(title="My Containerized API")

# In-memory storage
items = []

class Item(BaseModel):
    name: str
    description: str | None = None

@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Containerized API!",
        "timestamp": datetime.datetime.now().isoformat(),
        "endpoints": {
            "GET /": "This message",
            "GET /health": "Health check",
            "GET /items": "List all items",
            "POST /items": "Create an item",
            "GET /docs": "Interactive API documentation"
        }
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat()
    }

@app.get("/items")
def list_items():
    return {"items": items, "count": len(items)}

@app.post("/items")
def create_item(item: Item):
    item_dict = item.model_dump()
    item_dict["id"] = len(items) + 1
    item_dict["created_at"] = datetime.datetime.now().isoformat()
    items.append(item_dict)
    return item_dict

@app.get("/items/{item_id}")
def get_item(item_id: int):
    for item in items:
        if item["id"] == item_id:
            return item
    return {"error": "Item not found"}, 404
```

**requirements.txt:**
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
```

## Task 1: Write a Dockerfile

Create a `Dockerfile` that:
1. Uses `python:3.11-slim` as the base image
2. Sets `/app` as the working directory
3. Copies `requirements.txt` and installs dependencies
4. Copies the application code
5. Exposes port 8000
6. Runs the application with `uvicorn`

**Checkpoint:** Before continuing, try writing the Dockerfile yourself.

<details>
<summary>Solution (click to reveal)</summary>

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy and install dependencies first (for layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Expose the port the app runs on
EXPOSE 8000

# Run uvicorn server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Explanation:**
- **`FROM python:3.11-slim`**: Start with a minimal Python image
- **`WORKDIR /app`**: Set working directory (all subsequent commands run here)
- **`COPY requirements.txt .`**: Copy dependencies file first
- **`RUN pip install ...`**: Install dependencies (this layer caches unless requirements.txt changes)
- **`COPY main.py .`**: Copy application code (changes frequently)
- **`EXPOSE 8000`**: Document the port (doesn't actually publish it—that's `-p` in `docker run`)
- **`CMD ["uvicorn", ...]`**: Run the FastAPI app with uvicorn

**Why this order?** If you change `main.py`, only the last two layers rebuild. The expensive `pip install` layer is cached.

</details>

## Task 2: Build the Image

Build the Docker image and tag it as `fastapi-app:latest`.

```bash
docker build -t fastapi-app:latest .
```

**Expected output:**
```
[+] Building 15.2s (10/10) FINISHED
 => [1/5] FROM docker.io/library/python:3.11-slim
 => [2/5] WORKDIR /app
 => [3/5] COPY requirements.txt .
 => [4/5] RUN pip install --no-cache-dir -r requirements.txt
 => [5/5] COPY main.py .
 => exporting to image
```

**Verify the image was created:**
```bash
docker images | grep fastapi-app
```

**Expected output:**
```
fastapi-app   latest    abc123def456   10 seconds ago   200MB
```

## Task 3: Run the Container

Run the container with port mapping so you can access the API from your browser.

```bash
docker run -d -p 8000:8000 --name fastapi-container fastapi-app:latest
```

**Explanation:**
- **`-d`**: Run in detached mode (background)
- **`-p 8000:8000`**: Map host port 8000 to container port 8000
- **`--name fastapi-container`**: Name the container for easy reference
- **`fastapi-app:latest`**: The image to run

**Verify the container is running:**
```bash
docker ps
```

**Expected output:**
```
CONTAINER ID   IMAGE                  COMMAND                  STATUS         PORTS
abc123...      fastapi-app:latest     "uvicorn main:app --…"   Up 5 seconds   0.0.0.0:8000->8000/tcp
```

## Task 4: Test the API

**1. Test the root endpoint:**
```bash
curl http://localhost:8000
```

**Expected output:**
```json
{
  "message": "Welcome to the Containerized API!",
  "timestamp": "2025-02-09T10:30:00.123456",
  "endpoints": {
    "GET /": "This message",
    "GET /health": "Health check",
    "GET /items": "List all items",
    "POST /items": "Create an item",
    "GET /docs": "Interactive API documentation"
  }
}
```

**2. Test the health check:**
```bash
curl http://localhost:8000/health
```

**Expected output:**
```json
{
  "status": "healthy",
  "timestamp": "2025-02-09T10:30:05.123456"
}
```

**3. Create an item:**
```bash
curl -X POST http://localhost:8000/items -H "Content-Type: application/json" -d '{"name": "Docker Book", "description": "Learning Docker"}'
```

**Expected output:**
```json
{
  "name": "Docker Book",
  "description": "Learning Docker",
  "id": 1,
  "created_at": "2025-02-09T10:30:10.123456"
}
```

**4. List items:**
```bash
curl http://localhost:8000/items
```

**Expected output:**
```json
{
  "items": [
    {
      "name": "Docker Book",
      "description": "Learning Docker",
      "id": 1,
      "created_at": "2025-02-09T10:30:10.123456"
    }
  ],
  "count": 1
}
```

**5. Visit the interactive docs:**

Open your browser and go to `http://localhost:8000/docs`. You'll see FastAPI's auto-generated Swagger UI where you can test all endpoints interactively.

## Task 5: View Logs

Check the container logs to see incoming requests:

```bash
docker logs fastapi-container
```

**Expected output:**
```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     172.17.0.1:52342 - "GET / HTTP/1.1" 200 OK
INFO:     172.17.0.1:52343 - "GET /health HTTP/1.1" 200 OK
INFO:     172.17.0.1:52344 - "POST /items HTTP/1.1" 200 OK
```

**Follow logs in real-time:**
```bash
docker logs -f fastapi-container
```

Press `Ctrl+C` to stop following.

## Task 6: Execute Commands Inside the Container

Open a shell inside the running container to explore:

```bash
docker exec -it fastapi-container bash
```

**Inside the container:**
```bash
# Check Python version
python --version

# List files
ls -la

# Check installed packages
pip list

# Exit
exit
```

## Task 7: Stop and Remove the Container

```bash
# Stop the container
docker stop fastapi-container

# Remove the container
docker rm fastapi-container
```

**Verify it's gone:**
```bash
docker ps -a | grep fastapi-container
# No output = container removed
```

## Bonus Challenges

### Bonus 1: Add a Health Check to the Dockerfile

Modify the Dockerfile to include a health check that pings the `/health` endpoint every 30 seconds.

**Hint:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 CMD curl -f http://localhost:8000/health || exit 1
```

**Note:** You'll need to install `curl` in the image:
```dockerfile
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
```

**Test it:**
```bash
docker build -t fastapi-app:latest .
docker run -d -p 8000:8000 --name fastapi-container fastapi-app:latest

# Wait a few seconds, then check health
docker inspect fastapi-container | grep -A 10 '"Health"'
```

### Bonus 2: Use Multi-Stage Build

Optimize the image size by using a multi-stage build. Install dependencies in a builder stage, then copy only the necessary files to a smaller runtime stage.

**Hint:**
```dockerfile
# Stage 1: Builder
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY main.py .
ENV PATH=/root/.local/bin:$PATH
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Compare image sizes:**
```bash
docker images fastapi-app
```

### Bonus 3: Add Environment Variables

Modify the Dockerfile to accept environment variables for configuration (e.g., `PORT`, `RELOAD`).

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

ENV PORT=8000
ENV RELOAD=false

EXPOSE ${PORT}

CMD uvicorn main:app --host 0.0.0.0 --port ${PORT} --reload=${RELOAD}
```

**Run with custom port:**
```bash
docker run -d -p 9000:9000 -e PORT=9000 --name fastapi-container fastapi-app:latest
curl http://localhost:9000
```

### Bonus 4: Use Docker Compose

Create a `docker-compose.yml` to run the app (and later add a database).

**docker-compose.yml:**
```yaml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - PORT=8000
    restart: unless-stopped
```

**Run with Compose:**
```bash
docker compose up --build
```

## Common Issues and Solutions

**Issue 1: Port already in use**
```
Error: Bind for 0.0.0.0:8000 failed: port is already allocated
```

**Solution:** Use a different host port:
```bash
docker run -d -p 8001:8000 --name fastapi-container fastapi-app:latest
curl http://localhost:8001
```

**Issue 2: Image not found**
```
Error: No such image: fastapi-app:latest
```

**Solution:** Build the image first:
```bash
docker build -t fastapi-app:latest .
```

**Issue 3: Container exits immediately**
```
docker ps
# No output (container not running)
```

**Solution:** Check logs for errors:
```bash
docker logs fastapi-container
```

Likely cause: Syntax error in `main.py` or missing dependencies.

## Summary

You've successfully containerized a FastAPI application! You wrote a Dockerfile, built an image, ran a container with port mapping, and tested the API. You also learned to view logs, execute commands inside containers, and explore bonus challenges like health checks and multi-stage builds.

**Key Skills Demonstrated:**
- Writing efficient Dockerfiles with proper layer ordering
- Building and tagging images
- Running containers with port mapping and environment variables
- Testing containerized applications
- Debugging with logs and `docker exec`
- Using `.dockerignore` to exclude unnecessary files
- Optimizing images with multi-stage builds

---

**Previous:** [VSCode Dev Containers](../04-docker-in-practice/03-vscode-dev-containers.md) | **Next:** [Build a Distributed System](02-build-a-distributed-system.md)
