# Introduction to Git

## Overview

Version control is one of the most important tools in software and data engineering. This lesson introduces the fundamental concepts of version control, explains why Git has become the industry standard, and establishes the mental model you'll need to use Git effectively.

**Duration:** ~15 minutes

## The Problem: Why Version Control Exists

### The "Final Version" Nightmare

We've all been there:

```
project_final.py
project_final_v2.py
project_final_v2_REAL.py
project_final_v2_REAL_fixed.py
project_final_v2_REAL_fixed_THIS_ONE.py
```

Or with documents:

```
analysis_report.docx
analysis_report_john_edits.docx
analysis_report_john_edits_sarah_comments.docx
analysis_report_FINAL.docx
analysis_report_FINAL_revised.docx
```

This approach has serious problems:

1. **No clear history** - Which version has which changes?
2. **Merge nightmare** - How do you combine changes from multiple people?
3. **Lost work** - Someone accidentally overwrites a file
4. **Fear of change** - Scared to refactor because you might break something
5. **Storage waste** - Dozens of near-identical copies taking up space

### The Real-World Impact

For data engineers, this chaos manifests as:

- SQL migration scripts with unclear versioning
- Airflow DAGs where you're afraid to change anything
- Lost work when two engineers edit the same pipeline
- No audit trail for regulatory compliance
- Inability to roll back a broken deployment

**Version control systems solve all of these problems.**

## What is Version Control?

Version control (also called "source control") is a system that:

1. **Records changes** to files over time
2. **Allows you to recall** specific versions later
3. **Enables collaboration** without stepping on each other's toes
4. **Maintains a complete history** of who changed what and why

Think of it like an **unlimited undo button** combined with **parallel universes** for your code.

### Key Benefits

| Benefit | Description | Example |
|---------|-------------|---------|
| **History** | See every change ever made | "Who wrote this SQL query and why?" |
| **Backup** | Never lose work | Computer dies? Clone from GitHub |
| **Collaboration** | Multiple people, same codebase | 10 engineers working on one pipeline |
| **Experimentation** | Try risky changes safely | Test a new algorithm on a branch |
| **Rollback** | Undo mistakes | "The deployment broke production—revert it!" |
| **Audit trail** | Compliance and accountability | "Show me all changes to this PII query" |

## Why Git?

Git is the most popular version control system in the world. Here's why:

### Distributed vs Centralized

**Old centralized systems (SVN, CVS):**
- Central server has the "one true copy"
- You need network access to commit
- Server goes down = everyone stops working

**Git (distributed):**
- Every developer has a full copy of the history
- Commit locally, push when ready
- Work offline
- No single point of failure

### Git's Advantages

1. **Speed** - Most operations are local and instant
2. **Branching** - Creating branches is cheap and fast
3. **Merging** - Sophisticated merge algorithms
4. **Industry standard** - Used by virtually every tech company
5. **Ecosystem** - GitHub, GitLab, Bitbucket, etc.

**Advanced Note:** Git was created by Linus Torvalds in 2005 to manage Linux kernel development. The kernel has thousands of contributors and Git was designed to handle that scale efficiently.

## The Git Mental Model

Understanding Git's mental model is crucial. Here's how Git thinks about your code:

### Three Areas

Git has three main areas where your files can live:

```
┌─────────────────────┐
│  Working Directory  │  ← Where you edit files
│                     │
│  my_script.py       │
│  config.yaml        │
└──────────┬──────────┘
           │ git add
           ↓
┌─────────────────────┐
│   Staging Area      │  ← Files ready to commit
│   (Index)           │
│                     │
│  my_script.py ✓     │
└──────────┬──────────┘
           │ git commit
           ↓
┌─────────────────────┐
│    Repository       │  ← Permanent snapshots
│    (.git folder)    │
│                     │
│  Commit history     │
└─────────────────────┘
```

1. **Working Directory** - Your actual files on disk
2. **Staging Area** (Index) - Files marked for the next commit
3. **Repository** - The `.git` folder with complete history

### Snapshots, Not Diffs

**Important:** Git stores *snapshots* of your entire project, not individual file changes.

When you commit, Git:
1. Takes a picture of what all files look like right now
2. Stores a reference to that snapshot
3. If files haven't changed, just keeps a link to the previous version

This is different from older systems that stored deltas (diffs) between versions.

**Why this matters:** Git can switch between branches instantly because it's just pointing to different snapshots.

### Commits: The Building Blocks

A **commit** is:

- A snapshot of your project at a point in time
- Metadata (author, date, message)
- A unique identifier (SHA-1 hash like `a3f2b1c`)
- A pointer to its parent commit(s)

```
commit a3f2b1c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0
Author: Jane Doe <jane@example.com>
Date:   Mon Feb 9 10:30:00 2026 -0500

    Add data validation to ETL pipeline
    
    - Validate schema before loading
    - Reject malformed records
    - Log validation errors
```

Commits form a **chain**:

```
(earlier) C1 ← C2 ← C3 ← C4 ← C5 (latest)
```

**Advanced Note:** Each commit is identified by a SHA-1 hash. You can reference a commit by its full hash (`a3f2b1c4d5e6f7a8...`) or just the first 7 characters (`a3f2b1c`). Git is smart enough to figure out which commit you mean.

## Installation & First-Time Setup

### Installing Git

**macOS:**
```bash
# Check if already installed
git --version

# Install via Xcode Command Line Tools
xcode-select --install

# Or via Homebrew
brew install git
```

**Windows:**
```bash
# Download installer from https://git-scm.com/download/win
# Or use Windows Package Manager
winget install --id Git.Git -e --source winget

# Verify installation
git --version
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install git

# Fedora
sudo dnf install git

# Verify
git --version
```

### First-Time Configuration

Before you start using Git, configure your identity:

```bash
# Set your name (appears in commits)
git config --global user.name "Jane Doe"

# Set your email (must match your GitHub email eventually)
git config --global user.email "jane.doe@example.com"

# Verify configuration
git config --list
```

**What `--global` means:** These settings apply to all repositories on your computer. You can override them per-repository if needed.

### Optional but Recommended Settings

```bash
# Set default branch name to 'main' (modern convention)
git config --global init.defaultBranch main

# Use VS Code as default editor for commit messages
git config --global core.editor "code --wait"

# Enable colors in terminal output
git config --global color.ui auto

# Cache credentials for HTTPS (avoid typing password repeatedly)
# macOS:
git config --global credential.helper osxkeychain
# Windows:
git config --global credential.helper wincred
# Linux:
git config --global credential.helper cache
```

### Verify Your Setup

```bash
# Check Git version
git --version
# Output: git version 2.39.0 (or higher)

# View all your configuration
git config --list --show-origin
# Shows where each setting comes from
```

## Git Terminology Quick Reference

| Term | Definition |
|------|------------|
| **Repository (repo)** | A project tracked by Git (the `.git` folder + working files) |
| **Commit** | A snapshot of your project at a specific time |
| **Branch** | A movable pointer to a commit (like a parallel timeline) |
| **HEAD** | A pointer to the current branch/commit you're on |
| **Staging Area** | Files marked for the next commit |
| **Remote** | A version of your repo hosted elsewhere (e.g., GitHub) |
| **Clone** | Copy a repository from a remote to your computer |
| **Push** | Send commits from your computer to a remote |
| **Pull** | Download commits from a remote to your computer |
| **Merge** | Combine changes from different branches |
| **Conflict** | When Git can't automatically merge changes |

Don't worry if these don't all make sense yet—we'll cover each one in detail.

## At Scale: Version Control in Large Organizations

**How this scales:**

- **Google** - Monorepo with billions of lines of code (custom VCS based on Git concepts)
- **Microsoft** - Transitioned Windows development to Git (~3.5 million files)
- **Netflix** - Hundreds of repos, automated Git workflows for deployments
- **Your future company** - Will almost certainly use Git

Git is designed to handle:
- Repositories with millions of files
- Tens of thousands of commits
- Hundreds of concurrent branches
- Distributed teams across continents

## Key Takeaways

1. **Version control solves real problems** - No more `final_v2_REAL.py`
2. **Git is distributed** - Everyone has a full copy of the history
3. **Git uses snapshots** - Not diffs between files
4. **Three areas** - Working directory → Staging → Repository
5. **Commits are snapshots** - With metadata and parent pointers
6. **Configuration matters** - Set your name/email before first commit

## What's Next?

Now that you understand *why* Git exists and *how* it thinks about your code, the next lesson covers the **core daily workflow**: initializing repositories, staging changes, and making commits.

**Advanced Note:** If you're curious about Git internals, the `.git` folder contains:
- `objects/` - All commits, trees, and blobs (the actual data)
- `refs/` - Pointers to commits (branches, tags)
- `HEAD` - What you're currently looking at
- `config` - Repository-specific settings
- `index` - The staging area

You don't need to understand these details to use Git effectively, but they're fascinating if you want to dive deeper.

---

**Navigation:**
- **Next:** [02 - Basic Commands](02-basic-commands.md) - Learn the daily Git loop
- **Home:** [Git Course Overview](README.md)
