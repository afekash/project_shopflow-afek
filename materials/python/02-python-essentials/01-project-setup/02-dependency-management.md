# Dependency Management

Managing external packages is fundamental to Python development. This lesson compares traditional `pip` with modern alternatives like `uv`, and covers how dependencies are handled in production environments.

## The Standard Tool: pip

`pip` (Pip Installs Packages) is Python's default package installer. It downloads packages from the Python Package Index (PyPI) and installs them into your environment.

### Basic pip Usage

```python
import subprocess
import sys

# Install a package
subprocess.run([sys.executable, "-m", "pip", "install", "requests"], check=True)

# Install a specific version
subprocess.run([sys.executable, "-m", "pip", "install", "pandas==2.0.0"], check=True)

# Install multiple packages from a file
# First, let's create a requirements file
with open("requirements.txt", "w") as f:
    f.write("requests>=2.28.0\n")
    f.write("pandas==2.0.0\n")
    f.write("sqlalchemy<3.0\n")

subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
```

### Version Specifiers

```python
# Create a requirements.txt showing different version constraints
requirements_examples = """
# Exact version (most restrictive)
pandas==2.0.0

# Minimum version
requests>=2.28.0

# Compatible release (allows patch updates)
sqlalchemy~=2.0.0  # Allows 2.0.x but not 2.1.0

# Version range
numpy>=1.20.0,<2.0.0

# Exclude specific versions
flask!=2.0.0

# Latest version (not recommended for production)
beautifulsoup4
"""

with open("requirements-examples.txt", "w") as f:
    f.write(requirements_examples)

print("Version specifier examples written to requirements-examples.txt")
```

### The Problem with `requirements.txt`

```python
# requirements.txt
with open("requirements.txt", "w") as f:
    f.write("""pandas>=2.0.0
requests>=2.28.0
""")
```

What's the problem? These constraints allow different versions to be installed:

- Developer A installs today: gets `pandas==2.0.0`, `requests==2.28.0`
- Developer B installs next month: gets `pandas==2.1.0`, `requests==2.30.0`

Result: "It works on my machine" bugs.

### Solution: `pip freeze` and Lockfiles

```python
import subprocess
import sys

# After installing your dependencies, freeze them to capture exact versions
result = subprocess.run(
    [sys.executable, "-m", "pip", "freeze"],
    capture_output=True,
    text=True
)

# This shows ALL installed packages with exact versions
print("Currently installed packages:")
print(result.stdout)

# Save to a lockfile
with open("requirements-lock.txt", "w") as f:
    f.write(result.stdout)
```

**Two-file pattern** (common in production):

- `requirements.txt`: High-level dependencies with flexible versions
- `requirements-lock.txt`: Exact versions from `pip freeze`, for reproducible installs

```python
# Typical workflow
import subprocess
import sys

# 1. Developer specifies what they need
with open("requirements.txt", "w") as f:
    f.write("pandas>=2.0.0\n")

# 2. Install and generate lockfile
subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
result = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True)

with open("requirements-lock.txt", "w") as f:
    f.write(result.stdout)

print("Lockfile generated. In production, use:")
print("  pip install -r requirements-lock.txt")
```

### Problems with pip

1. **No lockfile by default**: You have to manually `pip freeze` and manage two files
2. **Slow dependency resolution**: pip historically had poor resolver performance
3. **No project metadata**: `requirements.txt` only lists dependencies, not project name, version, author, etc.
4. **Manual virtual env management**: You create and activate `venv` yourself

These issues led to the creation of modern alternatives.

## The Modern Alternative: uv

`uv` is a next-generation Python package manager written in Rust. It's dramatically faster than `pip` and provides first-class support for lockfiles and project management.

### Installing uv

```bash
# On macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or via pip (ironic, but works)
pip install uv
```

### Creating a Project with uv

```bash
# Initialize a new project
uv init my-project
cd my-project

# Project structure created:
# my-project/
# ├── .python-version    # Specifies Python version
# ├── pyproject.toml     # Project metadata + dependencies
# ├── README.md
# └── hello.py           # Sample script
```

The `pyproject.toml` is the single source of truth:

```python
# This would be in pyproject.toml (showing as Python for syntax highlighting)
example_pyproject = """
[project]
name = "my-project"
version = "0.1.0"
description = "My data pipeline"
requires-python = ">=3.10"
dependencies = [
    "pandas>=2.0.0",
    "requests>=2.28.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
"""

with open("example-pyproject.toml", "w") as f:
    f.write(example_pyproject)

print("Example pyproject.toml created")
```

### Adding Dependencies

```bash
# Add a dependency (automatically updates pyproject.toml and uv.lock)
uv add pandas

# Add a development dependency
uv add --dev pytest

# Add with version constraint
uv add "requests>=2.28.0,<3.0.0"
```

When you run `uv add`, uv:

1. Resolves all dependencies and their transitive dependencies
2. Updates `pyproject.toml` with your new dependency
3. Generates/updates `uv.lock` with exact versions of everything
4. Installs the packages

### The Lockfile: `uv.lock`

The `uv.lock` file captures the entire dependency tree with exact versions and hashes:

```python
example_lock = """
# Example snippet from uv.lock
[[package]]
name = "pandas"
version = "2.0.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "numpy" },
    { name = "python-dateutil" },
]
wheels = [
    { url = "https://files.pythonhosted.org/...", hash = "sha256:abc123..." },
]

[[package]]
name = "numpy"
version = "1.24.3"
source = { registry = "https://pypi.org/simple" }
wheels = [
    { url = "https://files.pythonhosted.org/...", hash = "sha256:def456..." },
]
"""

print("uv.lock contains exact versions and hashes for reproducibility")
print(example_lock)
```

This lockfile ensures **identical installs** across all environments.

### Running Code with uv

```bash
# Run a script (uv handles the virtual environment automatically)
uv run python main.py

# Run a module
uv run python -m my_package.main

# Install dependencies and run
uv sync  # Installs from uv.lock
uv run python main.py
```

**Key insight:** With `uv run`, you don't need to manually activate a virtual environment. `uv` creates and manages it for you.

### Syncing Dependencies

```bash
# Install exact versions from uv.lock
uv sync

# Install only production dependencies (skip dev dependencies)
uv sync --no-dev

# Update all dependencies to latest compatible versions
uv lock --upgrade
```

## pip vs uv: Feature Comparison

| Feature | pip | uv |
|---------|-----|-----|
| **Speed** | Moderate | 10-100x faster (Rust-based) |
| **Lockfile** | Manual (`pip freeze`) | Automatic (`uv.lock`) |
| **Virtual Envs** | Manual (`python -m venv`) | Automatic, transparent |
| **Project Metadata** | Not included (needs `setup.py` or `pyproject.toml` separately) | Built-in (`pyproject.toml`) |
| **Dependency Resolution** | Improved in recent versions, but slower | Very fast, considers all constraints |
| **UX** | Low-level, imperative | High-level, declarative |
| **Compatibility** | Standard, works everywhere | New, growing adoption |

**When to use pip:**

- Working on legacy projects
- Deployment environments that don't have `uv` installed
- You need guaranteed compatibility with older Python versions

**When to use uv:**

- New projects
- Local development (faster iteration)
- Projects you control end-to-end

**In practice:** Many teams use `uv` locally for speed, but still deploy with `pip` because CI/CD pipelines and Docker images have `pip` by default.

## Dependency Management in Production

In production environments (servers, containers, scheduled jobs), you need reproducible installs. Here's how Python dependencies are typically handled.

### Docker Deployment Pattern

Most Python applications are deployed in Docker containers. Here's the typical pattern:

```python
# Example Dockerfile (shown as Python string for Jupytext compatibility)
dockerfile_content = '''
FROM python:3.11-slim

WORKDIR /app

# Copy dependency files
COPY requirements-lock.txt .

# Install dependencies from lockfile
RUN pip install --no-cache-dir -r requirements-lock.txt

# Copy application code
COPY . .

# Run the application
CMD ["python", "-m", "my_app.main"]
'''

with open("Dockerfile.example", "w") as f:
    f.write(dockerfile_content)

print("Example Dockerfile created")
```

**Why this pattern:**

1. **Copy dependencies first**: Docker layers are cached. If `requirements-lock.txt` doesn't change, Docker reuses the installed packages layer (much faster builds)
2. **Use lockfile**: Ensures identical dependencies in dev, staging, and production
3. **`--no-cache-dir`**: Reduces image size by not storing pip's download cache

### Using uv in Docker

For faster builds, you can use `uv` in Docker:

```python
dockerfile_uv = '''
FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Run the application
CMD ["uv", "run", "python", "-m", "my_app.main"]
'''

with open("Dockerfile.uv.example", "w") as f:
    f.write(dockerfile_uv)

print("Example Dockerfile with uv created")
```

**Key flags:**

- `--frozen`: Don't update `uv.lock`, fail if it's out of sync
- `--no-dev`: Skip development dependencies in production

### Multi-Stage Docker Builds

For production, use multi-stage builds to minimize image size:

```python
dockerfile_multistage = '''
# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements-lock.txt .
RUN pip install --user --no-cache-dir -r requirements-lock.txt

# Stage 2: Runtime image
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Add local binaries to PATH
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

CMD ["python", "-m", "my_app.main"]
'''

with open("Dockerfile.multistage.example", "w") as f:
    f.write(dockerfile_multistage)

print("Multi-stage Dockerfile created")
```

This produces smaller images because the final stage doesn't include build tools.

### CI/CD Pipeline Example

```python
# Example GitHub Actions workflow
github_workflow = '''
name: Test and Deploy

on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install uv
        run: pip install uv
      
      - name: Install dependencies
        run: uv sync --frozen
      
      - name: Run tests
        run: uv run pytest
      
      - name: Build Docker image
        run: docker build -t my-app:${{ github.sha }} .
'''

with open("github-workflow.example.yml", "w") as f:
    f.write(github_workflow)

print("Example CI/CD workflow created")
```

### Why You Still Need to Understand pip

Even if you use `uv` locally, you'll encounter `pip` in:

1. **Legacy projects**: Millions of existing projects use `pip`
2. **Docker base images**: Official Python images have `pip`, not `uv`
3. **Third-party documentation**: Most tutorials assume `pip`
4. **Debugging**: Understanding `pip` helps when troubleshooting installations

**Best practice**: Learn both. Use `uv` for new projects, understand `pip` for everything else.

## Additional Tools and Patterns

### `.python-version` File

Specify which Python version your project needs:

```python
with open(".python-version", "w") as f:
    f.write("3.11\n")

print("Created .python-version file")
```

Tools like `pyenv` and `uv` automatically use this version when they see this file.

### Development vs Production Dependencies

Separate dependencies you need for development (testing, linting) from production dependencies:

```python
# In pyproject.toml
pyproject_with_dev_deps = """
[project]
name = "my-app"
dependencies = [
    "pandas>=2.0.0",
    "sqlalchemy>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "mypy>=1.0.0",
    "ruff>=0.1.0",
]
"""

print("Development dependencies go under [project.optional-dependencies]")
print(pyproject_with_dev_deps)
```

Install dev dependencies:

```bash
# With pip
pip install -e ".[dev]"

# With uv
uv sync  # Includes dev by default
uv sync --no-dev  # Production only
```

## At Scale: Enterprise Dependency Management

In large organizations, dependency management involves additional concerns:

### Private PyPI Registries

Companies often host internal packages on private registries (e.g., AWS CodeArtifact, JFrog Artifactory):

```python
# Configure pip to use private registry
pip_conf = """
[global]
index-url = https://pypi.org/simple
extra-index-url = https://my-company.jfrog.io/artifactory/api/pypi/pypi-local/simple
"""

print("pip can be configured to use private registries via pip.conf")
print(pip_conf)
```

### Dependency Scanning

Production systems scan dependencies for known vulnerabilities:

```bash
# Using pip-audit
pip install pip-audit
pip-audit  # Checks installed packages against vulnerability database

# Using safety
pip install safety
safety check -r requirements-lock.txt
```

### Monorepo Dependency Management

In monorepos with multiple Python projects:

```python
# Shared dependencies in root pyproject.toml
# Project-specific dependencies in subdirectories
monorepo_structure = """
monorepo/
├── pyproject.toml          # Shared dependencies
├── libs/
│   ├── data-models/
│   │   └── pyproject.toml  # Library-specific deps
│   └── data-utils/
│       └── pyproject.toml
└── services/
    ├── api/
    │   └── pyproject.toml  # Service-specific deps
    └── worker/
        └── pyproject.toml
"""

print("Monorepo structure:")
print(monorepo_structure)
```

Tools like `uv` are working on better monorepo support with workspace features.

## Summary

| Tool | Best For | Key Files |
|------|----------|-----------|
| **pip** | Standard installs, production, legacy | `requirements.txt`, `requirements-lock.txt` |
| **uv** | Modern projects, fast local dev | `pyproject.toml`, `uv.lock` |

**Key Concepts:**

- **Lockfiles** ensure reproducible installs across environments
- **`pyproject.toml`** is the modern standard for project metadata
- **Docker** is the most common Python deployment pattern
- **Separate dev and prod dependencies** to minimize production image size

**Recommended workflow:**

1. Use `uv` for local development (faster, better UX)
2. Generate `requirements-lock.txt` for Docker/CI/CD: `uv pip freeze > requirements-lock.txt`
3. Use `pip install -r requirements-lock.txt` in production environments
4. Commit both `pyproject.toml` (or `requirements.txt`) and the lockfile to version control

---

**Navigation:**
- **Previous**: [← Creating a Python Project](01-creating-a-python-project.md)
- **Next**: [Primitive Types →](../02-data-structures/01-primitive-types.md)
- **Home**: [Python Essentials](../README.md)
