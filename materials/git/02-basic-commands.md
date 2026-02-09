# Basic Git Commands

## Overview

This lesson covers the essential Git commands you'll use every day: initializing repositories, staging changes, and creating commits. These form the foundation of your daily workflow.

**Duration:** ~15 minutes

## The Basic Loop

Understanding this pattern is key to using Git effectively:

```
┌──────────────────────────────────────┐
│  1. Edit files                       │
│     (working directory)              │
└───────────────┬──────────────────────┘
                │
                ↓
┌──────────────────────────────────────┐
│  2. Stage changes (git add)          │
│     (staging area)                   │
└───────────────┬──────────────────────┘
                │
                ↓
┌──────────────────────────────────────┐
│  3. Commit snapshot (git commit)     │
│     (repository)                     │
└───────────────┬──────────────────────┘
                │
                ↓
        Repeat as needed
```

## Creating a Repository

### `git init` - Initialize a New Repository

Start tracking a project with Git:

```bash
# Create a new project directory
mkdir my-data-pipeline
cd my-data-pipeline

# Initialize Git
git init

# Output:
# Initialized empty Git repository in /path/to/my-data-pipeline/.git/
```

**What just happened?**
- Git created a hidden `.git` folder
- This folder contains the entire repository
- Your directory is now tracked by Git

```bash
# See the .git folder
ls -la

# Output includes:
# drwxr-xr-x  10 user  staff   320 Feb  9 10:00 .git
```

**Advanced Note:** The `.git` folder is self-contained. Delete it and you lose all history (but keep your files). Copy it and you've cloned the repository.

## Checking Status

### `git status` - See Current State

This is your most-used command:

```bash
git status
```

**When repository is empty:**
```
On branch main

No commits yet

nothing to commit (create/copy files and use "git add" to track)
```

Let's create a file:

```bash
# Create a Python script
echo 'print("Hello, Git!")' > hello.py

# Check status
git status
```

**Output:**
```
On branch main

No commits yet

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	hello.py

nothing added to commit but untracked files present (use "git add" to track)
```

**Understanding the output:**
- `hello.py` exists in your working directory
- Git sees it but isn't tracking it yet
- You need `git add` to start tracking

**Pro tip:** Run `git status` constantly. It tells you exactly what state you're in and what commands to run next.

## Staging Changes

### `git add` - Prepare Files for Commit

Staging lets you choose exactly what goes into each commit:

```bash
# Stage a specific file
git add hello.py

# Check status
git status
```

**Output:**
```
On branch main

No commits yet

Changes to be committed:
  (use "git rm --cached <file>..." to unstage)
	new file:   hello.py
```

The file is now **staged** (ready to commit).

### Staging Multiple Files

```bash
# Create more files
echo "# My Pipeline" > README.md
echo "pandas==2.0.0" > requirements.txt
mkdir src
echo 'def process(): pass' > src/pipeline.py

# Stage all files
git add .

# Or stage specific files
git add README.md requirements.txt

# Or stage an entire directory
git add src/

# Check what's staged
git status
```

**Common staging patterns:**

```bash
git add <file>          # Stage one specific file
git add <directory>     # Stage entire directory
git add .               # Stage all in current directory
git add *.py            # Stage all Python files
git add -A              # Stage everything (new, modified, deleted)
```

**Advanced Note:** You can stage parts of a file using `git add -p` (patch mode). This lets you interactively select specific changes to stage, enabling very precise commits.

## Creating Commits

### `git commit` - Save a Snapshot

A commit permanently records the staged changes:

```bash
# Commit with a message
git commit -m "Initial commit: add hello script and docs"
```

**Output:**
```
[main (root-commit) a3f2b1c] Initial commit: add hello script and docs
 3 files changed, 4 insertions(+)
 create mode 100644 README.md
 create mode 100644 hello.py
 create mode 100644 requirements.txt
```

**What happened:**
- Git took a snapshot of staged files
- Created commit with hash `a3f2b1c`
- This is now permanent history

### The Edit-Stage-Commit Cycle

Let's do the complete cycle:

```bash
# 1. Edit a file
echo 'print("Updated!")' >> hello.py

# 2. Check what changed
git status
# Output: modified:   hello.py

# 3. Stage the change
git add hello.py

# 4. Commit
git commit -m "Add updated message to hello script"

# 5. Verify
git status
# Output: nothing to commit, working tree clean
```

## Writing Good Commit Messages

### Bad Examples

```bash
git commit -m "fixed stuff"
git commit -m "update"
git commit -m "asdfasdf"
git commit -m "changes"
git commit -m "wip"
```

**Why bad?** Future you won't know what was changed or why.

### Good Examples

```bash
git commit -m "Add input validation to ETL script"
git commit -m "Fix SQL injection in query builder"
git commit -m "Update pandas from 1.5.0 to 2.0.0"
git commit -m "Remove deprecated Airflow operators"
```

**Why good?** Clear, specific, understandable in 6 months.

### Commit Message Best Practices

1. **Use imperative mood** - "Add feature" not "Added feature"
2. **Be specific** - Say what changed
3. **Keep subject under 50 chars** - Be concise
4. **Explain why, not what** - Code shows what, message shows why

### Multi-line Commits

For complex changes, add details:

```bash
git commit -m "Add retry logic to S3 upload

The upload was failing intermittently due to network timeouts.
This adds exponential backoff with 3 retries before failing.

Fixes: #123"
```

**Using an editor:**

```bash
# Open your editor for a detailed message
git commit

# Git provides a template:
# 
# Please enter the commit message for your changes.
# Lines starting with '#' will be ignored.
#
# On branch main
# Changes to be committed:
#	modified:   pipeline.py
```

### Atomic Commits

**Principle:** One commit = one logical change

**Bad (too much in one commit):**
```bash
git commit -m "Add logging, fix bug, refactor, update docs"
```

**Good (separate commits):**
```bash
git commit -m "Add structured logging to pipeline"
git commit -m "Fix off-by-one error in date range"
git commit -m "Extract SQL queries to separate module"
git commit -m "Update README with setup instructions"
```

**Why atomic commits matter:**
- Easier to review
- Easier to revert if needed
- Clearer history
- Better for `git bisect` (finding bugs)

## Practical Example

Complete workflow for a data pipeline:

```bash
# 1. Initialize
mkdir etl-pipeline
cd etl-pipeline
git init

# 2. Create initial file
cat > extract.py << EOF
import pandas as pd

def extract_data(source):
    """Extract data from CSV source"""
    return pd.read_csv(source)
EOF

# 3. Stage and commit
git add extract.py
git commit -m "Add data extraction module"

# 4. Add transform module
cat > transform.py << EOF
def clean_data(df):
    """Remove null values and duplicates"""
    df = df.dropna()
    df = df.drop_duplicates()
    return df
EOF

# 5. Stage and commit
git add transform.py
git commit -m "Add data transformation module"

# 6. Add load module
cat > load.py << EOF
def load_to_warehouse(df, target):
    """Load cleaned data to parquet"""
    df.to_parquet(target, index=False)
EOF

# 7. Stage and commit
git add load.py
git commit -m "Add data loading module"

# 8. Check history
git log --oneline
# Output:
# c3d4e5f (HEAD -> main) Add data loading module
# b2c3d4e Add data transformation module
# a1b2c3d Add data extraction module
```

## Common Patterns

### Staging All Modified Files

```bash
# See what's modified
git status

# Stage all modified files (not new files)
git add -u

# Stage everything including new files
git add -A
```

### Quick Commit

```bash
# Stage all and commit in one command
# (only for tracked files)
git commit -am "Quick fix to validation"
```

**Warning:** This skips the review step. Use carefully!

### Checking Before Commit

```bash
# Always check what you're about to commit
git status

# See exactly what changes are staged
git diff --staged

# Then commit
git commit -m "Your message"
```

## Key Takeaways

1. **`git init`** - Start tracking a project
2. **`git status`** - Check current state (use constantly!)
3. **`git add`** - Stage changes for commit
4. **`git commit -m "message"`** - Save a snapshot
5. **Good commit messages** - Future you will be grateful
6. **Atomic commits** - One logical change per commit
7. **Stage intentionally** - Don't just `git add .` blindly

## Practice Exercises

1. **Initialize a repo** - Create a new project and initialize Git
2. **Make 3 commits** - Each with a different file
3. **Modify and commit** - Change an existing file and commit
4. **Write good messages** - Practice the imperative mood
5. **Check your status** - Run `git status` between each step

## What's Next?

You now know how to create commits. Next, you'll learn how to **view and review your history** using `git log` and `git diff`.

---

**Navigation:**
- **Previous:** [01 - Introduction to Git](01-introduction-to-git.md)
- **Next:** [03 - Viewing History](03-viewing-history.md)
- **Home:** [Git Course Overview](README.md)
