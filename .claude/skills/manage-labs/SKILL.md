---
name: manage-labs
description: Docker Compose lab architecture and conventions. Use when creating, modifying, or debugging lab environments under labs/, editing lab-related Makefile targets, or adding new sidecar services.
---

# Lab Environment

## Directory Structure

Each lab is a self-contained directory under `labs/`:

```
labs/
  base/
    Dockerfile          # shared workspace image (MyST + Jupyter + uv)
    compose.yml         # workspace service definition
    pyproject.toml      # base Python deps (JupyterLab, ipykernel)
    init.sh             # boot script (Jupyter + MyST)
  <name>/
    compose.yml         # sidecar services + workspace overrides
    pyproject.toml      # Python deps for this lab only
    init.sh             # post-start init script (optional)
    data/               # seed data, .bak files, schemas (optional)
    Dockerfile.<svc>    # custom sidecar image (optional)
```

## Compose Merge Pattern

Every `make lab-<name>` merges the base with the lab overlay:

```
docker compose -f labs/base/compose.yml -f labs/<name>/compose.yml up -d --build --remove-orphans
```

`--remove-orphans` is mandatory on every `up` invocation. It makes lab startup idempotent and removes stale containers from a previously running lab.

Lab `compose.yml` files must **never** duplicate the full workspace service -- only add sidecar services and workspace overrides (extra `environment`, `depends_on`, `build.args`).

## Python Dependencies

- `labs/base/pyproject.toml` -- shared base deps, always installed
- `labs/<name>/pyproject.toml` -- per-lab runtime deps, installed on top of base at build time
- The root `pyproject.toml` is for project metadata and dev tooling only
- The workspace Dockerfile installs base deps first, then per-lab deps via the `LAB` build arg:

```yaml
# labs/<name>/compose.yml
services:
  workspace:
    build:
      args:
        LAB: <name>
```

## Init Scripts

Operations requiring running containers (e.g., `rs.initiate`, shard registration, cluster creation) go in `labs/<name>/init.sh`. The Makefile calls them after `docker compose up`:

```makefile
lab-replica-set: down
	$(BASE) -f labs/replica-set/compose.yml up -d --build --remove-orphans
	bash labs/replica-set/init.sh
```

## Adding a New Lab

1. Create `labs/<name>/` with `compose.yml` and `pyproject.toml`
2. Add `make lab-<name>` target in the Makefile: `$(BASE) -f labs/<name>/compose.yml up -d --build --remove-orphans`
3. Add init scripts, data files, or custom Dockerfiles as needed
4. Document the lab in the lesson with a `{note}` directive
5. Update the README lab table

## Conventions

- Services communicate by container/service name inside the compose network
- Connection strings use service names (e.g., `postgresql://postgres:postgres@postgres:5432/db`)
- Lab-specific env vars go in the overlay's `workspace.environment` list
- `depends_on` with health checks go in the overlay's `workspace.depends_on`
- All sidecar services must declare `container_name` matching their service name -- ensures predictable names for `docker exec`/`docker logs` and is required for cluster configs (Redis Sentinel, Redis Cluster). Only omit if intentionally scaling with `--scale`, and document why.
