# Running Containers

## Overview

Building images is only half the story—now we'll run them as containers. In this section, you'll learn how to start containers, map ports, manage their lifecycle, view logs, and execute commands inside running containers.

## The `docker run` Command

`docker run` creates and starts a container from an image. It combines several operations: `docker create` (creates the container) + `docker start` (starts it).

**Basic syntax:**
```bash
docker run [OPTIONS] IMAGE [COMMAND]
```

**Simplest example:**
```bash
docker run ubuntu echo "Hello from container"
# Output: Hello from container
```

This:
1. Pulls the `ubuntu` image (if not already present)
2. Creates a container from it
3. Runs `echo "Hello from container"` inside the container
4. Exits and stops the container

**Common options:**

| Option | Description | Example |
|--------|-------------|---------|
| `-d` | Detached mode (run in background) | `docker run -d nginx` |
| `-p` | Publish port (host:container) | `docker run -p 8080:80 nginx` |
| `--name` | Assign a name to the container | `docker run --name myapp nginx` |
| `-e` | Set environment variable | `docker run -e DB_HOST=localhost myapp` |
| `-v` | Mount volume or bind mount | `docker run -v /data:/app/data myapp` |
| `--rm` | Remove container when it exits | `docker run --rm ubuntu echo "hi"` |
| `-it` | Interactive terminal (combine `-i` and `-t`) | `docker run -it ubuntu bash` |

## Running Containers in the Background

Use `-d` (detached mode) to run containers in the background:

```bash
docker run -d --name mynginx nginx
# Output: container ID (e.g., a3f2c1b9e8d7...)
```

The container runs silently in the background. To see it:
```bash
docker ps
# Output:
# CONTAINER ID   IMAGE     COMMAND                  CREATED         STATUS         PORTS     NAMES
# a3f2c1b9e8d7   nginx     "/docker-entrypoint.…"   5 seconds ago   Up 4 seconds   80/tcp    mynginx
```

**Best Practice:** Use `-d` for long-running services (web servers, databases, workers). Use foreground mode (no `-d`) for short-lived tasks or debugging.

## Port Mapping: Connecting to Containers

Containers run in an isolated network. To access a service inside a container from your host machine, **map ports** with the `-p` flag.

**Syntax:**
```bash
docker run -p HOST_PORT:CONTAINER_PORT image
```

**Example: Running nginx on port 8080**
```bash
docker run -d -p 8080:80 --name webserver nginx
```

- **Container port 80:** nginx inside the container listens on port 80
- **Host port 8080:** Your machine forwards requests from `localhost:8080` to the container's port 80

**Diagram:**
```
Your Browser
    ↓
localhost:8080 (host)
    ↓ (port mapping)
container:80 (nginx inside container)
```

**Test it:**
```bash
curl http://localhost:8080
# Output: nginx welcome page HTML
```

**Multiple ports:**
```bash
docker run -d -p 8080:80 -p 8443:443 nginx
# Maps both HTTP (80) and HTTPS (443)
```

**Bind to specific host IP:**
```bash
docker run -d -p 127.0.0.1:8080:80 nginx
# Only accessible from localhost (not from other machines on the network)
```

**Advanced Note:** Without `-p`, the container's ports are **not** accessible from the host. The `EXPOSE` instruction in the Dockerfile is just documentation—it doesn't publish ports. You must explicitly use `-p` or `-P` (publish all exposed ports to random host ports).

**Container-to-Container Communication:** Containers on the same Docker network can reach each other's exposed ports directly (without `-p`) using the container name or IP. The `EXPOSE` instruction helps document which ports are available for inter-container communication.

## Environment Variables

Pass configuration to containers with `-e`:

```bash
docker run -d -e POSTGRES_PASSWORD=secret -e POSTGRES_DB=mydb postgres
```

**Multiple variables:**
```bash
docker run -d -e DATABASE_URL=postgresql://localhost/mydb -e API_KEY=abc123 -e DEBUG=true myapp
```

**Load from file:**
```bash
# Create a .env file
cat > .env <<EOF
DATABASE_URL=postgresql://localhost/mydb
API_KEY=abc123
EOF

# Load variables from file
docker run --env-file .env myapp
```

**Best Practice:** Use environment variables for configuration that changes between environments (dev/staging/prod). Avoid hardcoding secrets in Dockerfiles—pass them at runtime with `-e` or `--env-file`.

## Container Lifecycle Commands

### Listing Containers

```bash
# List running containers
docker ps

# List all containers (including stopped)
docker ps -a

# List only container IDs
docker ps -q
```

**Example output:**
```
CONTAINER ID   IMAGE     COMMAND                  STATUS          PORTS                  NAMES
a3f2c1b9e8d7   nginx     "/docker-entrypoint.…"   Up 2 minutes    0.0.0.0:8080->80/tcp   webserver
```

### Stopping Containers

```bash
# Graceful stop (sends SIGTERM, waits 10s, then SIGKILL)
docker stop webserver

# Stop multiple containers
docker stop container1 container2

# Forceful stop (sends SIGKILL immediately)
docker kill webserver
```

**Best Practice:** Use `docker stop` for graceful shutdown. It allows applications to clean up (close connections, flush buffers). Use `docker kill` only if `stop` hangs.

### Starting Stopped Containers

```bash
# Start a stopped container
docker start webserver

# Start and attach to output (see logs)
docker start -a webserver
```

### Restarting Containers

```bash
# Restart (stop + start)
docker restart webserver
```

### Removing Containers

```bash
# Remove a stopped container
docker rm webserver

# Force remove a running container
docker rm -f webserver

# Remove all stopped containers
docker container prune
```

**Best Practice:** Use `--rm` when running temporary containers to auto-delete them on exit:
```bash
docker run --rm ubuntu echo "This container will be auto-deleted"
```

## Viewing Logs

Containers send stdout/stderr to Docker's logging system. View logs with `docker logs`:

```bash
# View logs
docker logs webserver

# Follow logs (like tail -f)
docker logs -f webserver

# Show last 100 lines
docker logs --tail 100 webserver

# Show logs with timestamps
docker logs -t webserver

# Follow logs since last 5 minutes
docker logs -f --since 5m webserver
```

**Example:**
```bash
docker run -d --name myapp myapp-image
docker logs -f myapp
# Output: Real-time application logs
```

**Best Practice:** Always log to stdout/stderr in your applications. Docker captures this output, making logs accessible via `docker logs` and compatible with log aggregation tools (like CloudWatch, ELK stack).

**Advanced Note:** Docker supports multiple log drivers (json-file, syslog, journald, fluentd). The default is `json-file`, which stores logs in JSON files on the host. In production, you often configure a different driver to send logs to a centralized system.

## Executing Commands Inside Running Containers

Use `docker exec` to run commands in an already-running container.

**Interactive shell:**
```bash
docker exec -it webserver bash
# Opens a bash shell inside the container
```

**Flags:**
- **`-i`**: Interactive (keep stdin open)
- **`-t`**: Allocate a pseudo-TTY (terminal)

**Example session:**
```bash
$ docker exec -it webserver bash
root@a3f2c1b9e8d7:/# ls
bin  boot  dev  etc  home  ...
root@a3f2c1b9e8d7:/# cat /etc/nginx/nginx.conf
# nginx configuration...
root@a3f2c1b9e8d7:/# exit
```

**Running a single command:**
```bash
docker exec webserver ls /usr/share/nginx/html
# Output: index.html ...
```

**Use cases:**
- **Debugging:** Inspect files, check processes, test network connectivity
- **Database operations:** Run SQL commands, create users
- **File modifications:** Edit configuration files (though prefer rebuilding the image for permanent changes)

**Example: Database operations**
```bash
# Start PostgreSQL
docker run -d --name postgres -e POSTGRES_PASSWORD=secret postgres

# Create a database
docker exec postgres psql -U postgres -c "CREATE DATABASE myapp;"

# Open interactive psql shell
docker exec -it postgres psql -U postgres
```

**Best Practice:** Use `docker exec` for troubleshooting and one-off tasks. For persistent configuration changes, modify the Dockerfile and rebuild the image.

## Interactive Containers

For containers that run shells or interactive programs, use `-it`:

```bash
docker run -it ubuntu bash
# Opens a bash shell inside an Ubuntu container
```

**Explanation:**
- **`-i`**: Keep stdin open (so you can type)
- **`-t`**: Allocate a pseudo-terminal (for proper shell rendering)

**When you exit, the container stops** (because the main process, `bash`, has exited).

**Running Python interactively:**
```bash
docker run -it python:3.11 python
# Opens Python REPL
>>> print("Hello from Docker")
Hello from Docker
>>> exit()
```

## Inspecting Containers

Get detailed information about a container:

```bash
docker inspect webserver
# Output: JSON with all container details (network, volumes, environment, etc.)
```

**Filter specific fields:**
```bash
# Get container IP address
docker inspect -f '{{.NetworkSettings.IPAddress}}' webserver

# Get container status
docker inspect -f '{{.State.Status}}' webserver
```

**View container stats (CPU, memory usage):**
```bash
docker stats webserver
# Real-time stats
```

## Restart Policies

Containers can automatically restart on failure or host reboot.

```bash
docker run -d --restart unless-stopped --name myapp myapp-image
```

**Restart policies:**

| Policy | Behavior |
|--------|----------|
| `no` (default) | Never restart |
| `always` | Always restart, even after host reboot |
| `unless-stopped` | Restart always, unless manually stopped |
| `on-failure[:max-retries]` | Restart only if container exits with non-zero code |

**Example with `on-failure`:**
```bash
docker run -d --restart on-failure:3 --name myapp myapp-image
# Restarts up to 3 times if it crashes
```

**Best Practice:** Use `unless-stopped` for production services. This ensures containers restart after server reboots but respects manual stops.

## Real-World Example: Running a PostgreSQL Database

```bash
# Start PostgreSQL with persistent data (volume) and password
docker run -d --name postgres-db --restart unless-stopped -e POSTGRES_PASSWORD=mypassword -e POSTGRES_DB=myapp -p 5432:5432 -v pgdata:/var/lib/postgresql/data postgres:16

# Verify it's running
docker ps

# View logs
docker logs postgres-db

# Connect with psql
docker exec -it postgres-db psql -U postgres -d myapp

# Stop and remove (data persists in volume)
docker stop postgres-db
docker rm postgres-db

# Start again (data still there)
docker run -d --name postgres-db -e POSTGRES_PASSWORD=mypassword -p 5432:5432 -v pgdata:/var/lib/postgresql/data postgres:16
```

## Container Naming

Docker auto-generates names (e.g., `quirky_einstein`) if you don't specify one. Use `--name` for clarity:

```bash
docker run -d --name my-redis redis
# Better than auto-generated "eager_fermi"
```

**Best Practice:** Name containers descriptively, especially in development. In production, orchestration tools (Docker Compose, Kubernetes) handle naming automatically.

## At Scale: Resource Limits

In production, always set resource limits to prevent runaway containers from consuming all host resources.

**Memory limit:**
```bash
docker run -d --memory="512m" --memory-swap="512m" nginx
# Container can use max 512 MB RAM
```

**CPU limit:**
```bash
docker run -d --cpus="1.5" nginx
# Container can use 1.5 CPU cores
```

**CPU shares (relative weight):**
```bash
docker run -d --cpu-shares=512 nginx
# Lower priority compared to default (1024)
```

**Best Practice:** In cloud environments (ECS, Kubernetes), always define resource requests and limits. This ensures fair resource distribution and prevents noisy neighbor issues.

## Common Pitfalls

**1. Forgetting `-d` for background services:**
```bash
docker run nginx
# Blocks your terminal—should use -d
```

**2. Forgetting `-p` to expose ports:**
```bash
docker run -d nginx
curl localhost:80
# Connection refused—need -p 8080:80
```

**3. Not using `--rm` for short-lived containers:**
```bash
docker run ubuntu echo "test"
# Container stops but isn't removed—clutters docker ps -a
# Use: docker run --rm ubuntu echo "test"
```

**4. Hardcoding environment variables in Dockerfiles:**
```dockerfile
# Bad: Secrets in image
ENV API_KEY=abc123

# Good: Pass at runtime
docker run -e API_KEY=abc123 myapp
```

## Summary

`docker run` creates and starts containers from images. Use `-d` for background services, `-p` to map ports, `-e` for environment variables, and `--name` for clarity. Manage lifecycle with `docker stop/start/restart/rm`. View logs with `docker logs` and troubleshoot with `docker exec`. Always set resource limits and restart policies in production.

**Key Takeaways:**
- **`docker run -d`** runs containers in the background
- **`-p HOST:CONTAINER`** maps ports to make services accessible
- **`-e`** passes environment variables for configuration
- **`docker logs`** shows container output
- **`docker exec -it`** opens a shell for debugging
- **`--restart unless-stopped`** ensures containers restart after host reboot
- **Resource limits** prevent containers from consuming all host resources

---

**Previous:** [Images and Dockerfiles](01-images-and-dockerfiles.md) | **Next:** [Volumes and Networking](03-volumes-and-networking.md)
