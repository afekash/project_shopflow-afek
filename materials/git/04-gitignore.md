# Git Ignore

## Overview

Not every file should be tracked by Git. This lesson teaches you how to use `.gitignore` to exclude files that don't belong in version control—like secrets, build artifacts, and large datasets.

**Duration:** ~8 minutes

## Why Ignore Files?

Certain files should never be committed:

### Security Risks
- **Environment files** - `.env`, `secrets.json`, `credentials.yaml`
- **API keys** - `config/api_keys.py`
- **Passwords** - Database connection strings
- **SSH keys** - `id_rsa`, private certificates

### Build Artifacts
- **Python** - `__pycache__/`, `*.pyc`, `.Python`, `*.egg-info/`
- **Node.js** - `node_modules/`, `dist/`, `build/`
- **Java** - `*.class`, `target/`, `*.jar`

### IDE & OS Files
- **VSCode** - `.vscode/settings.json`
- **PyCharm** - `.idea/`
- **macOS** - `.DS_Store`
- **Windows** - `Thumbs.db`, `desktop.ini`

### Large Data Files
- **Datasets** - `data/*.csv`, `*.parquet`, `datasets/`
- **Models** - `*.pkl`, `*.h5`, `models/*.pth`
- **Databases** - `*.db`, `*.sqlite`

**Why this matters:** Committing secrets can expose credentials. Committing large files bloats your repository forever.

## Creating a .gitignore

### Basic .gitignore File

```bash
# Create .gitignore in repository root
cat > .gitignore << EOF
# Python
__pycache__/
*.py[cod]
*.so
.Python

# Virtual environments
venv/
env/
ENV/

# Environment variables
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Data
data/*.csv
*.parquet
*.db
EOF

# Stage and commit
git add .gitignore
git commit -m "Add .gitignore for Python project"
```

Now Git will ignore all files matching these patterns.

## .gitignore Patterns

### Basic Patterns

```bash
# Ignore specific file
secrets.json

# Ignore all .log files
*.log

# Ignore entire directory
logs/
temp/

# Ignore files in root only
/TODO.txt

# Ignore all .txt files in doc/ directory
doc/**/*.txt
```

### Advanced Patterns

```bash
# Ignore everything in directory except one file
logs/*
!logs/.gitkeep

# Ignore all .txt files except important.txt
*.txt
!important.txt

# Ignore files matching pattern anywhere
**/temp/

# Ignore files with multiple extensions
*.log.*
*.tmp.*
```

### Pattern Examples

```bash
# Match any file or directory named test
test

# Match only test directory (trailing slash)
test/

# Match test files anywhere in subdirectories
**/test_*.py

# Match all CSV files
*.csv

# Match CSV files only in data directory
data/*.csv

# Match CSV files anywhere under data (recursive)
data/**/*.csv
```

**Advanced Note:** Git uses glob patterns similar to shell wildcards. `*` matches any string, `?` matches one character, `**` matches nested directories.

## Common .gitignore Templates

### Python Data Engineering

```bash
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class
*.so

# Virtual environments
venv/
env/
ENV/
.venv

# Environment variables & secrets
.env
.env.local
.env.*.local
secrets.yaml
credentials.json

# Jupyter Notebook checkpoints
.ipynb_checkpoints/
*.ipynb_checkpoints

# Data files
data/raw/*.csv
data/processed/*.parquet
*.db
*.sqlite
*.sqlite3

# ML models
models/*.pkl
models/*.h5
models/*.pth
*.ckpt

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
logs/
*.log

# Distribution / packaging
dist/
build/
*.egg-info/
```

### Node.js / JavaScript

```bash
# Dependencies
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Production build
dist/
build/

# Environment
.env
.env.local

# IDE
.vscode/
.idea/

# OS
.DS_Store
```

### General Data Science

```bash
# Data
*.csv
*.xlsx
*.parquet
*.feather
*.h5
*.hdf5

# Models
*.pkl
*.joblib
*.pth
*.pb

# Notebooks
.ipynb_checkpoints/

# Virtual envs
venv/
.conda/
```

## Using .gitignore

### Check if File is Ignored

```bash
# Check if specific file is ignored
git check-ignore -v data/secret.csv

# Output:
# .gitignore:10:data/*.csv	data/secret.csv
```

Shows which line in `.gitignore` is matching.

### List All Ignored Files

```bash
# See what Git is ignoring
git status --ignored

# Or more detailed
git ls-files --others --ignored --exclude-standard
```

## Ignoring Already-Tracked Files

**Problem:** You already committed a file before adding it to `.gitignore`.

```bash
# File is tracked
git ls-files | grep secrets.json
# secrets.json

# Add to .gitignore
echo "secrets.json" >> .gitignore

# Git still tracks it!
git status
# nothing to commit
```

**Solution:** Remove from Git (but keep the file):

```bash
# Remove from Git index (keep file on disk)
git rm --cached secrets.json

# Commit the removal
git commit -m "Stop tracking secrets.json"

# Now Git ignores it
git status
# nothing to commit
```

For directories:

```bash
# Remove directory from Git (recursively)
git rm -r --cached __pycache__/

# Commit
git commit -m "Stop tracking pycache"
```

**Warning:** This removes the file from Git history going forward, but it's still in old commits. Use tools like `git filter-branch` or BFG Repo-Cleaner to remove from history entirely (advanced topic).

## Global .gitignore

Ignore files across all repositories:

```bash
# Create global gitignore
cat > ~/.gitignore_global << EOF
# OS
.DS_Store
Thumbs.db

# IDEs
.vscode/
.idea/
*.swp

# Python
__pycache__/
*.pyc
EOF

# Configure Git to use it
git config --global core.excludesfile ~/.gitignore_global
```

Now these patterns apply to every repository on your system.

## .gitignore for Specific Files

### Ignore All Except Specific Pattern

```bash
# Ignore everything in logs/
logs/*

# But keep .gitkeep (ensures directory is tracked)
!logs/.gitkeep
```

### Keep Directory Structure Without Files

```bash
# data/raw/ directory structure:
# data/raw/
# data/raw/.gitkeep

# In .gitignore:
data/raw/*
!data/raw/.gitkeep
```

The `.gitkeep` file (empty file) ensures Git tracks the empty directory.

## gitignore.io - Template Generator

Use [gitignore.io](https://www.toptal.com/developers/gitignore) to generate templates:

```bash
# Generate for Python + VSCode + macOS
curl -L https://www.toptal.com/developers/gitignore/api/python,vscode,macos > .gitignore

# Or visit the website and select your stack
```

**Pro tip:** Start with a template, then customize for your project.

## Real-World Scenarios

### Data Engineering Project

```bash
# Directory structure:
# project/
# ├── src/
# ├── data/
# │   ├── raw/
# │   └── processed/
# ├── config/
# └── logs/

# .gitignore:
# Ignore all data files
data/raw/*.csv
data/processed/*.parquet

# Ignore secrets
config/credentials.yaml
.env

# Ignore logs
logs/*.log

# But keep directory structure
!data/raw/.gitkeep
!data/processed/.gitkeep
!logs/.gitkeep
```

### Machine Learning Project

```bash
# Ignore datasets
datasets/
*.csv
*.h5
*.hdf5

# Ignore trained models
models/*.pkl
models/*.pth
checkpoints/

# Ignore experiment tracking
mlruns/
wandb/

# Keep model configs
!models/config.yaml
```

## Debugging .gitignore

### File Not Being Ignored?

```bash
# 1. Check if already tracked
git ls-files | grep filename

# If tracked, remove it:
git rm --cached filename

# 2. Check pattern
git check-ignore -v filename

# 3. Check for typos in .gitignore
cat .gitignore
```

### Accidentally Ignored Important File?

```bash
# Force add ignored file
git add -f important_config.yaml

# Or remove pattern from .gitignore
```

## Key Takeaways

1. **Use `.gitignore`** - Keep secrets and build artifacts out
2. **Security first** - Never commit `.env`, API keys, passwords
3. **Keep it clean** - Ignore `__pycache__/`, `.DS_Store`, IDE files
4. **Data doesn't belong in Git** - Ignore CSVs, parquets, models
5. **Use templates** - Start with gitignore.io
6. **Already tracked?** - Use `git rm --cached` to untrack
7. **Global ignore** - Set up `~/.gitignore_global` for OS/IDE files

## Practice Exercises

1. **Create .gitignore** - For a Python data project
2. **Test patterns** - Use `git check-ignore -v`
3. **Untrack a file** - Practice `git rm --cached`
4. **Use gitignore.io** - Generate a template for your stack
5. **Set up global ignore** - Add your OS and IDE files

## What's Next?

You now know how to keep unwanted files out of Git. Next, you'll learn about **undoing changes**—how to safely fix mistakes and revert commits.

---

**Navigation:**
- **Previous:** [03 - Viewing History](03-viewing-history.md)
- **Next:** [05 - Undoing Changes](05-undoing-changes.md)
- **Home:** [Git Course Overview](README.md)
