# VSCode Dev Containers

## Overview

The **Dev Containers** extension (formerly Remote - Containers) for Visual Studio Code lets you develop **inside** a Docker container. Your entire development environment—runtime, dependencies, tools, and extensions—lives in the container, ensuring consistency across your team.

In this section, you'll learn how to attach VSCode to running containers, create custom dev containers, and use this workflow effectively.

## Why Dev Containers?

**Problem:** Team members have different setups:
- Different OS versions (macOS, Windows, Linux)
- Different Python/Node/Ruby versions
- Different installed tools (databases, compilers)
- Different editor configurations

**Solution:** Define the development environment in a `Dockerfile` or `devcontainer.json`. Everyone uses the same containerized environment.

**Benefits:**
- **Consistency:** Everyone develops in identical environments
- **Onboarding:** New team members run one command to get started
- **Isolation:** Projects don't pollute your local system
- **Reproducibility:** Development environment versioned in Git

## Installing the Dev Containers Extension

1. Open VSCode
2. Install the **Dev Containers** extension:
   - Press `Cmd+Shift+X` (macOS) or `Ctrl+Shift+X` (Windows/Linux)
   - Search for "Dev Containers"
   - Install the extension by Microsoft

**Prerequisite:** Docker Desktop must be running.

## Attaching to a Running Container

The simplest use case: attach VSCode to a container that's already running.

**1. Start a container:**
```bash
docker run -d --name myapp-dev -v $(pwd):/workspace -w /workspace python:3.11 tail -f /dev/null
```

This starts a Python container with your current directory mounted at `/workspace`. The `tail -f /dev/null` keeps the container running.

**2. Attach VSCode:**
- Press `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Windows/Linux) to open the command palette
- Type "Dev Containers: Attach to Running Container"
- Select `myapp-dev`

**3. VSCode opens a new window connected to the container:**
- Open the terminal (`` Ctrl+` ``) — you're inside the container
- Open the file explorer — you see `/workspace` (your project files)
- Install extensions — they install inside the container, not on your host

**4. Develop normally:**
```bash
# Inside container terminal
python --version
# Output: Python 3.11.x

pip install fastapi uvicorn
python app.py
```

**5. Detach:**
Close the VSCode window. The container keeps running. Reattach anytime by repeating step 2.

**Use case:** Quickly attach to any running container for debugging or development.

## Creating a Dev Container Configuration

For a more integrated experience, define a `.devcontainer/devcontainer.json` file in your project.

**Project structure:**
```
myproject/
├── .devcontainer/
│   ├── devcontainer.json
│   └── Dockerfile (optional)
├── app.py
└── requirements.txt
```

**Basic `.devcontainer/devcontainer.json`:**
```json
{
  "name": "Python 3.11 Dev Container",
  "image": "python:3.11",
  "workspaceFolder": "/workspace",
  "workspaceMount": "source=${localWorkspaceFolder},target=/workspace,type=bind",
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.vscode-pylance"
      ]
    }
  },
  "postCreateCommand": "pip install -r requirements.txt",
  "remoteUser": "root"
}
```

**How to use:**
1. Open the project in VSCode
2. Command palette: "Dev Containers: Reopen in Container"
3. VSCode builds the container (if using a Dockerfile) or pulls the image, then reopens the project inside the container

**Explanation of fields:**
- **`name`**: Display name for the dev container
- **`image`**: Base Docker image to use
- **`workspaceFolder`**: Path inside container where your project is mounted
- **`customizations.vscode.extensions`**: VSCode extensions to install automatically
- **`postCreateCommand`**: Command to run after container is created (e.g., install dependencies)
- **`remoteUser`**: User to run as inside the container (default is often `root`, but can specify a non-root user)

## Using a Custom Dockerfile

For more control, use a custom Dockerfile.

**.devcontainer/Dockerfile:**
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python tools
RUN pip install --no-cache-dir \
    black \
    flake8 \
    pytest

# Set working directory
WORKDIR /workspace
```

**.devcontainer/devcontainer.json:**
```json
{
  "name": "Custom Python Dev Container",
  "build": {
    "dockerfile": "Dockerfile"
  },
  "workspaceFolder": "/workspace",
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.vscode-pylance",
        "ms-python.black-formatter"
      ],
      "settings": {
        "python.formatting.provider": "black",
        "python.linting.enabled": true,
        "python.linting.flake8Enabled": true
      }
    }
  },
  "postCreateCommand": "pip install -r requirements.txt"
}
```

**Open in container:**
- Command palette: "Dev Containers: Reopen in Container"
- VSCode builds the Dockerfile and opens the project inside

**Benefits:**
- Full control over the environment (install any tools, libraries)
- Extensions and settings configured automatically
- Team members get the exact same environment

## Docker Compose Integration

If your project uses Docker Compose (e.g., web app + database), you can develop inside one of the services.

**docker-compose.yml:**
```yaml
services:
  app:
    build: .
    volumes:
      - .:/workspace
    working_dir: /workspace
    command: tail -f /dev/null  # Keep container running
    depends_on:
      - db

  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: myapp
```

**.devcontainer/devcontainer.json:**
```json
{
  "name": "App with Database",
  "dockerComposeFile": "../docker-compose.yml",
  "service": "app",
  "workspaceFolder": "/workspace",
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python"
      ]
    }
  },
  "postCreateCommand": "pip install -r requirements.txt"
}
```

**How it works:**
- VSCode starts the entire Compose stack (`app` + `db`)
- Attaches to the `app` service
- You can access the database from inside the container (`postgresql://postgres:secret@db/myapp`)

**Use case:** Develop with full stack (web app, database, cache) running locally.

## Rebuilding the Container

If you modify the Dockerfile or `devcontainer.json`:
- Command palette: "Dev Containers: Rebuild Container"
- VSCode rebuilds and reopens

## Port Forwarding

VSCode automatically forwards ports from the container to your host.

**Example:** Your app runs on port 8000 inside the container. VSCode detects this and forwards it to `localhost:8000` on your host.

**Manual port forwarding:**
- Open the **Ports** panel (View → Ports)
- Click "Forward a Port"
- Enter the port number (e.g., 8000)

Now you can access `http://localhost:8000` in your browser, even though the app is running inside the container.

## Running Commands Inside the Container

**Terminal:**
- Open the integrated terminal (`` Ctrl+` ``)
- You're inside the container — run any command (`python`, `pip`, `git`)

**Example:**
```bash
# Install a package
pip install requests

# Run tests
pytest

# Check environment
env | grep DATABASE_URL
```

## Practical Example: Full Stack Dev Container

**Project structure:**
```
myproject/
├── .devcontainer/
│   ├── devcontainer.json
│   └── Dockerfile
├── docker-compose.yml
├── app/
│   ├── main.py
│   └── requirements.txt
└── README.md
```

**docker-compose.yml:**
```yaml
services:
  app:
    build: .
    volumes:
      - .:/workspace
    working_dir: /workspace
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://postgres:secret@db/myapp
    depends_on:
      - db

  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: myapp
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

**.devcontainer/Dockerfile:**
```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y git curl && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
```

**.devcontainer/devcontainer.json:**
```json
{
  "name": "Full Stack App",
  "dockerComposeFile": "../docker-compose.yml",
  "service": "app",
  "workspaceFolder": "/workspace",
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.vscode-pylance",
        "mtxr.sqltools",
        "mtxr.sqltools-driver-pg"
      ]
    }
  },
  "postCreateCommand": "pip install -r app/requirements.txt",
  "forwardPorts": [8000]
}
```

**Workflow:**
1. Open project in VSCode
2. Command palette: "Dev Containers: Reopen in Container"
3. VSCode starts `app` and `db` services
4. Edit `app/main.py` — changes trigger hot reload (uvicorn `--reload`)
5. Access app at `http://localhost:8000`
6. Connect to database from inside container:
   ```bash
   psql postgresql://postgres:secret@db/myapp
   ```

**Benefits:**
- Entire team uses identical environment (Python version, database, extensions)
- No "it works on my machine" issues
- New team members: clone repo, open in container, start coding

## At Scale: Team Adoption

**1. Standardize dev containers across projects:**
- Create organization-wide base images (Python with company tools, Node with linters)
- Share `devcontainer.json` templates

**2. Document the workflow:**
- Add setup instructions to `README.md`
- Record a demo video for new team members

**3. CI/CD alignment:**
- Use the same Dockerfile for dev containers and CI builds
- Ensures parity between local dev and CI environments

**4. Optimize build times:**
- Use layer caching in Dockerfiles
- Cache dependencies in CI

## Common Pitfalls

**1. Forgetting to rebuild after Dockerfile changes:**
- Run "Dev Containers: Rebuild Container" after modifying Dockerfile or `devcontainer.json`

**2. Bind mounts on macOS/Windows are slow:**
- For heavy I/O (npm install, large datasets), use Docker volumes instead of bind mounts
- Or use VSCode's "Clone Repository in Container Volume" for better performance

**3. Extensions installed locally, not in container:**
- Extensions must be reinstalled in the container
- Add them to `devcontainer.json` for automatic installation

**4. Container keeps stopping:**
- Ensure the main process doesn't exit (use `tail -f /dev/null` or a long-running command)

## Summary

VSCode Dev Containers let you develop inside Docker containers, ensuring consistent environments across your team. Attach to running containers for quick debugging, or define `.devcontainer/devcontainer.json` for a fully configured environment. Use Docker Compose integration for full-stack development with databases and services. This workflow eliminates "works on my machine" issues and speeds up onboarding.

**Key Takeaways:**
- **Dev Containers** extension connects VSCode to Docker containers
- **Attach to running containers** for quick debugging
- **`.devcontainer/devcontainer.json`** defines the environment (image, extensions, settings)
- **Custom Dockerfiles** give full control over the environment
- **Docker Compose integration** runs multi-service stacks (app + database)
- **Port forwarding** makes containerized apps accessible from the host
- Team-wide adoption ensures consistency and eliminates setup issues

---

**Previous:** [CI/CD and Cloud Deployment](02-cicd-and-cloud-deployment.md) | **Next:** [Containerize a FastAPI App](../05-exercises/01-containerize-fastapi-app.md)
