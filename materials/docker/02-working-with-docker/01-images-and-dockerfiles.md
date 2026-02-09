# Images and Dockerfiles

## Overview

A **Dockerfile** is a text file containing instructions for building a Docker image. It's like a recipe—each instruction adds a layer to the image, defining what software, files, and configuration the final container will have.

In this section, you'll learn Dockerfile syntax, how to build images efficiently, and how layer caching works.

## Anatomy of a Dockerfile

Here's a simple Dockerfile that containerizes a Python script:

```dockerfile
# Start from a base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variable
ENV PYTHONUNBUFFERED=1

# Expose port (documentation only, doesn't actually publish the port)
EXPOSE 8000

# Define the command to run when container starts
CMD ["python", "app.py"]
```

Let's break down each instruction.

## Core Dockerfile Instructions

### `FROM`: Choose a Base Image

Every Dockerfile starts with `FROM`, which specifies the base image to build upon.

```dockerfile
FROM python:3.11-slim
```

**Common base images:**
- `python:3.11` - Full Python installation (~900 MB)
- `python:3.11-slim` - Minimal Python (~150 MB, recommended for most apps)
- `python:3.11-alpine` - Ultra-minimal based on Alpine Linux (~50 MB, but can have compatibility issues)
- `ubuntu:22.04` - Ubuntu base (build your own stack)
- `scratch` - Empty image (for static binaries, advanced use case)

**Best Practice:** Use `-slim` variants for a balance between size and compatibility. Alpine images are smaller but may require additional packages for C extensions.

**Advanced Note:** You can use multiple `FROM` statements for **multi-stage builds** (covered later). Each `FROM` starts a new build stage.

### `WORKDIR`: Set the Working Directory

`WORKDIR` sets the directory for subsequent instructions (`RUN`, `COPY`, `CMD`). If the directory doesn't exist, Docker creates it.

```dockerfile
WORKDIR /app
```

This is equivalent to `cd /app` on the command line, but it also creates the directory if needed.

**Best Practice:** Always use `WORKDIR` instead of `RUN cd /app`. It's clearer and works reliably across instructions.

### `COPY` and `ADD`: Copy Files into the Image

`COPY` copies files from your build context (usually your project directory) into the image.

```dockerfile
COPY requirements.txt .
COPY . .
```

- **`COPY requirements.txt .`** - Copies `requirements.txt` from the build context to the current `WORKDIR` (`.` means current directory)
- **`COPY . .`** - Copies everything from the build context to the `WORKDIR`

**`ADD` vs `COPY`:** `ADD` has extra features (auto-extracting tar files, fetching URLs), but `COPY` is preferred for clarity. Use `COPY` unless you need `ADD`'s special behavior.

**Best Practice:** Copy dependency files (like `requirements.txt`) before copying application code. This optimizes layer caching (explained below).

### `RUN`: Execute Commands During Build

`RUN` executes a command inside the container **during the build process** and commits the result as a new layer.

```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
```

**Common uses:**
- Installing packages: `RUN apt-get update && apt-get install -y curl`
- Running build tools: `RUN npm install`, `RUN make`

**Best Practice:** Chain commands with `&&` to reduce layers:

```dockerfile
# Good: One layer
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Bad: Three layers
RUN apt-get update
RUN apt-get install -y curl
RUN apt-get install -y git
```

**Note:** `--no-cache-dir` for `pip` prevents caching downloaded packages, reducing image size.

### `ENV`: Set Environment Variables

`ENV` sets environment variables available in the container at build time and runtime.

```dockerfile
ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=postgresql://localhost/mydb
```

**Use cases:**
- Configuration: database URLs, API keys (avoid hardcoding secrets—use runtime environment variables instead)
- Behavior: `PYTHONUNBUFFERED=1` forces Python to output logs immediately (important for Docker logs)

**Best Practice:** Set environment variables with `ENV` for build-time configuration, but override them at runtime with `docker run -e` or Docker Compose for secrets and environment-specific values.

### `EXPOSE`: Document Port Usage

`EXPOSE` documents which ports the container listens on. It **does not** actually publish the port—it's metadata for documentation.

```dockerfile
EXPOSE 8000
```

To actually publish the port, use the `-p` flag with `docker run`:
```bash
docker run -p 8000:8000 myimage
```

**Best Practice:** Always `EXPOSE` ports your application uses, even though it's not strictly necessary. It helps users understand the image.

### `CMD`: Default Command to Run

`CMD` specifies the command to execute when a container starts from the image.

```dockerfile
CMD ["python", "app.py"]
```

**Two forms:**
- **Exec form (preferred):** `CMD ["executable", "arg1", "arg2"]`
- **Shell form:** `CMD python app.py` (runs in a shell, less efficient)

**Exec form vs shell form:**
- **Exec form:** Runs the command directly, no shell wrapping. Signals (like SIGTERM) reach the process.
- **Shell form:** Runs the command in a shell (`/bin/sh -c`). Signals go to the shell, not your app (problematic for graceful shutdown).

**Best Practice:** Use exec form for better signal handling.

**Note:** `CMD` can be overridden when running the container:
```bash
docker run myimage python other_script.py
# Overrides CMD to run other_script.py instead of app.py
```

### `ENTRYPOINT`: Fixed Command with Arguments

`ENTRYPOINT` is similar to `CMD`, but it's **not** easily overridden. It defines the executable, and `CMD` provides default arguments.

```dockerfile
ENTRYPOINT ["python"]
CMD ["app.py"]
```

When you run the container:
```bash
docker run myimage              # Runs: python app.py
docker run myimage other.py     # Runs: python other.py
```

**Use case:** When you want the container to always run a specific tool (e.g., a CLI utility) but allow users to pass arguments.

**Best Practice:** For simple apps, `CMD` alone is sufficient. Use `ENTRYPOINT` + `CMD` for more complex cases where the executable is fixed.

## Building an Image

To build an image from a Dockerfile, use `docker build`:

```bash
docker build -t myapp:latest .
```

**Explanation:**
- **`-t myapp:latest`** - Tags the image as `myapp` with the `latest` tag
- **`.`** - The build context (current directory—Docker sends all files in this directory to the daemon)

**Build output:**
```
[+] Building 12.5s (10/10) FINISHED
 => [1/5] FROM docker.io/library/python:3.11-slim
 => [2/5] WORKDIR /app
 => [3/5] COPY requirements.txt .
 => [4/5] RUN pip install -r requirements.txt
 => [5/5] COPY . .
 => exporting to image
```

Each step corresponds to a Dockerfile instruction and creates a layer.

**Advanced options:**
```bash
# Build with a different Dockerfile name
docker build -f Dockerfile.prod -t myapp:prod .

# Build without cache (forces rebuild of all layers)
docker build --no-cache -t myapp:latest .

# Build for a specific platform (cross-platform builds)
docker buildx build --platform linux/amd64,linux/arm64 -t myapp:latest .
```

## Layer Caching: Why Order Matters

Docker caches each layer. If a layer hasn't changed, Docker reuses the cached version, speeding up builds.

**Example:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .                        # Layer 3: Copy all files
RUN pip install -r requirements.txt  # Layer 4: Install dependencies
CMD ["python", "app.py"]
```

**Problem:** If you change a single line in `app.py`, Docker rebuilds layer 3 (copying files) and layer 4 (installing dependencies). Installing dependencies is slow, but it didn't need to be rebuilt—only the code changed.

**Solution:** Copy dependencies file first, install, then copy code:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .         # Layer 3: Copy only requirements
RUN pip install -r requirements.txt  # Layer 4: Install (cached unless requirements.txt changes)
COPY . .                        # Layer 5: Copy code (rebuilt on every code change)
CMD ["python", "app.py"]
```

Now, when you change `app.py`:
- Layers 1-4 are cached (no rebuild needed)
- Only layer 5 rebuilds (fast—just copying files)

**Best Practice:** Order Dockerfile instructions from least frequently changed to most frequently changed.

**Visual:**
```
Change app.py
    ↓
Layer 5 (COPY . .) invalidated → rebuild
    ↓
Layer 4 (RUN pip install) cached → reuse (fast!)
Layer 3 (COPY requirements.txt) cached → reuse
Layer 2 (WORKDIR) cached → reuse
Layer 1 (FROM) cached → reuse
```

## `.dockerignore`: Exclude Files from Build Context

The build context (the directory you specify in `docker build . `) is sent to the Docker daemon. If your project has large files you don't need in the image (e.g., `node_modules/`, `.git/`, test data), exclude them with a `.dockerignore` file.

**Example `.dockerignore`:**
```
# Ignore version control
.git
.gitignore

# Ignore build artifacts
__pycache__
*.pyc
*.pyo
.pytest_cache

# Ignore local environment
.env
venv/
env/

# Ignore OS files
.DS_Store
Thumbs.db

# Ignore large test data
tests/data/*.csv
```

**Why it matters:**
- **Faster builds:** Smaller build context = faster upload to Docker daemon
- **Smaller images:** Ignored files won't accidentally get copied with `COPY . .`
- **Security:** Prevents accidentally copying secrets (like `.env` files) into images

**Best Practice:** Always create a `.dockerignore` file for any non-trivial project.

## Multi-Stage Builds: Production-Ready Images

Multi-stage builds use multiple `FROM` statements to create intermediate images, then copy only necessary artifacts into the final image. This drastically reduces image size.

**Example: Building a Go application**

```dockerfile
# Stage 1: Build stage
FROM golang:1.21 AS builder
WORKDIR /app
COPY . .
RUN go build -o myapp

# Stage 2: Runtime stage
FROM alpine:3.18
WORKDIR /app
COPY --from=builder /app/myapp .
CMD ["./myapp"]
```

**How it works:**
1. **Stage 1 (builder):** Uses a large Go image (~800 MB) to compile the app
2. **Stage 2 (final):** Uses a tiny Alpine image (~5 MB), copies only the compiled binary from stage 1
3. **Result:** Final image is ~10 MB instead of ~800 MB

**Python example: Installing build dependencies**

```dockerfile
# Stage 1: Build wheels
FROM python:3.11 AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/*
COPY . .
CMD ["python", "app.py"]
```

**Benefits:**
- Build dependencies (compilers, headers) don't end up in the final image
- Final image contains only runtime dependencies

**Best Practice:** Use multi-stage builds for production images to minimize size and attack surface.

## Real-World Example: Containerizing a FastAPI App

Let's containerize a simple FastAPI application.

**Project structure:**
```
my-fastapi-app/
├── app.py
├── requirements.txt
└── Dockerfile
```

**app.py:**
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello from Docker!"}

@app.get("/health")
def health():
    return {"status": "healthy"}
```

**requirements.txt:**
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
```

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy and install dependencies first (for caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Expose the port FastAPI will run on
EXPOSE 8000

# Run uvicorn server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Build and run:**
```bash
# Build the image
docker build -t my-fastapi-app:latest .

# Run the container
docker run -d -p 8000:8000 --name fastapi-container my-fastapi-app:latest

# Test it
curl http://localhost:8000
# Output: {"message": "Hello from Docker!"}

# View logs
docker logs fastapi-container

# Stop and remove
docker stop fastapi-container
docker rm fastapi-container
```

## At Scale: Image Size and Build Performance

In production, image size matters:
- **Faster deployments:** Smaller images transfer to servers quicker
- **Lower storage costs:** Registries charge for storage
- **Reduced attack surface:** Fewer packages = fewer vulnerabilities

**Optimization tips:**
1. **Use slim base images:** `python:3.11-slim` instead of `python:3.11`
2. **Multi-stage builds:** Exclude build tools from final image
3. **Clean up in the same layer:**
   ```dockerfile
   RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
   ```
   This prevents package lists from persisting in the layer.
4. **Use `.dockerignore`:** Prevent unnecessary files from bloating the image

**Build performance in CI/CD:**
- **Layer caching:** CI systems can cache layers between builds (e.g., GitHub Actions with Docker layer caching)
- **BuildKit:** Docker's modern build engine (enabled by default in recent versions) improves caching and parallelization

## Summary

Dockerfiles define how to build images through a series of instructions. Each instruction creates a layer, and layers are cached to speed up builds. By ordering instructions strategically (stable layers first, changing layers last) and using `.dockerignore`, you optimize build performance. Multi-stage builds reduce final image size by excluding build dependencies.

**Key Takeaways:**
- **`FROM`** sets the base image
- **`COPY`** adds files; copy dependencies before code for better caching
- **`RUN`** executes commands during build
- **`CMD`** defines the default command to run
- **Layer order matters:** Stable layers first, changing layers last
- **`.dockerignore`** excludes unnecessary files from the build context
- **Multi-stage builds** produce smaller production images

---

**Previous:** [Docker Across Platforms](../01-introduction/03-docker-across-platforms.md) | **Next:** [Running Containers](02-running-containers.md)
