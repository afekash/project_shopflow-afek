# Remote Repositories

## Overview

So far, we've worked entirely on your local machine. This lesson introduces remote repositories—how to clone projects, push your changes, and pull updates from GitHub or other hosting platforms.

**Duration:** ~12 minutes

## What is a Remote?

A **remote** is a version of your repository hosted elsewhere (usually on GitHub, GitLab, or Bitbucket):

```
Your Computer               GitHub
    ↓                         ↓
Local Repository  ←→  Remote Repository
```

**Why remotes?**
- **Backup** - Your code is safe in the cloud
- **Collaboration** - Share code with teammates
- **Deployment** - CI/CD pulls from remote
- **Portfolio** - Showcase your work publicly

## Common Remote Hosts

| Platform | Best For | URL Pattern |
|----------|----------|-------------|
| **GitHub** | Open source, most popular | `github.com/user/repo` |
| **GitLab** | CI/CD integration | `gitlab.com/user/repo` |
| **Bitbucket** | Atlassian ecosystem | `bitbucket.org/user/repo` |
| **Self-hosted** | Enterprise, privacy | `git.company.com/repo` |

We'll focus on GitHub (industry standard).

## Cloning a Repository

### `git clone` - Copy a Remote Repository

Download an existing repository:

```bash
# Clone a public repository
git clone https://github.com/username/repository.git

# Output:
# Cloning into 'repository'...
# remote: Counting objects: 100, done.
# remote: Compressing objects: 100% (75/75), done.
# Receiving objects: 100% (100/100), done.

# Change into the cloned directory
cd repository
```

**What `clone` does:**
1. Creates a local directory
2. Copies all commits and history
3. Sets up remote connection (called `origin`)
4. Checks out the default branch (usually `main`)

### Clone with Custom Name

```bash
# Clone into different directory name
git clone https://github.com/user/repo.git my-project

cd my-project
```

### HTTPS vs SSH

```bash
# HTTPS (asks for password or token)
git clone https://github.com/user/repo.git

# SSH (uses SSH keys - no password needed)
git clone git@github.com:user/repo.git
```

**Pro tip:** Set up SSH keys for password-free authentication. See GitHub docs for setup.

## Viewing Remotes

### `git remote` - List Remote Connections

```bash
# Show configured remotes
git remote

# Output:
# origin

# Show URLs
git remote -v

# Output:
# origin  https://github.com/user/repo.git (fetch)
# origin  https://github.com/user/repo.git (push)
```

**`origin`** is the default name for the remote you cloned from.

### Inspect Remote Details

```bash
# Detailed info about remote
git remote show origin

# Output:
# * remote origin
#   Fetch URL: https://github.com/user/repo.git
#   Push  URL: https://github.com/user/repo.git
#   HEAD branch: main
#   Remote branches:
#     main    tracked
#     develop tracked
```

## Pushing Changes

### `git push` - Send Commits to Remote

Upload your local commits to GitHub:

```bash
# Make some commits locally
git commit -m "Add new feature"

# Push to remote
git push origin main

# Output:
# Counting objects: 3, done.
# Writing objects: 100% (3/3), 280 bytes | 0 bytes/s, done.
# To https://github.com/user/repo.git
#    a3f2b1c..d4e5f6a  main -> main
```

**Syntax:** `git push <remote> <branch>`

### First Push of New Branch

```bash
# Create and switch to feature branch
git switch -c feature/add-validation

# Make commits
git commit -m "Add validation logic"

# Push and set upstream
git push -u origin feature/add-validation

# Output:
# Branch 'feature/add-validation' set up to track remote branch...
```

**What `-u` does:** Sets upstream tracking, so future pushes only need `git push`.

### Subsequent Pushes

```bash
# After first push with -u, just use:
git push

# Git knows to push to origin/feature/add-validation
```

## Pulling Changes

### `git pull` - Download and Merge Remote Changes

Get updates from remote:

```bash
# Pull changes from origin/main into your main
git pull origin main

# Output:
# remote: Counting objects: 5, done.
# Updating a3f2b1c..d4e5f6a
# Fast-forward
#  pipeline.py | 10 ++++++++--
#  1 file changed, 8 insertions(+), 2 deletions(-)
```

**What `pull` does:**
1. `git fetch` - Downloads commits from remote
2. `git merge` - Merges them into your branch

### Pull with Tracking Branch

```bash
# If upstream is set (from -u flag)
git pull

# Equivalent to:
git pull origin current-branch
```

## Fetching vs Pulling

### `git fetch` - Download Without Merging

```bash
# Download remote changes but don't merge
git fetch origin

# Output:
# remote: Counting objects: 5, done.
# From https://github.com/user/repo
#    a3f2b1c..d4e5f6a  main -> origin/main
```

**`fetch` vs `pull`:**

```
fetch:  Remote → Local remote-tracking branches (don't touch your files)
pull:   Remote → Local remote-tracking branches → Your working directory
```

**Use `fetch` when:**
- You want to see what changed before merging
- You're in the middle of work and don't want to merge yet

```bash
# Fetch updates
git fetch origin

# See what's new
git log origin/main --oneline

# Merge when ready
git merge origin/main
```

## Working with Remotes

### Complete Push/Pull Workflow

```bash
# 1. Start working (ensure up to date)
git pull origin main

# 2. Create feature branch
git switch -c feature/new-functionality

# 3. Make changes and commit
git add .
git commit -m "Implement new functionality"

# 4. Push feature branch
git push -u origin feature/new-functionality

# 5. Later, push more commits
git commit -m "Fix edge case"
git push

# 6. When done, merge via Pull Request on GitHub
```

### Syncing with Remote

```bash
# Check remote status
git fetch origin

# Compare your branch to remote
git log origin/main..main --oneline
# (shows commits you have that remote doesn't)

git log main..origin/main --oneline
# (shows commits remote has that you don't)

# Pull if behind
git pull origin main
```

## Adding Remotes

### `git remote add` - Connect to New Remote

For repositories created with `git init`:

```bash
# 1. Initialize local repo
git init
git add .
git commit -m "Initial commit"

# 2. Create repository on GitHub
# (via GitHub website)

# 3. Add remote connection
git remote add origin https://github.com/username/repo.git

# 4. Push to remote
git push -u origin main
```

### Multiple Remotes

```bash
# Add second remote (e.g., company GitLab)
git remote add company https://gitlab.company.com/repo.git

# List remotes
git remote -v
# origin   https://github.com/user/repo.git
# company  https://gitlab.company.com/repo.git

# Push to different remotes
git push origin main
git push company main
```

## Common Remote Operations

### Remove Remote

```bash
git remote remove origin
```

### Rename Remote

```bash
git remote rename origin upstream
```

### Change Remote URL

```bash
# Switch from HTTPS to SSH
git remote set-url origin git@github.com:user/repo.git
```

## Practical Scenarios

### Scenario 1: Join Existing Project

```bash
# 1. Clone repository
git clone https://github.com/company/data-pipeline.git
cd data-pipeline

# 2. Create feature branch
git switch -c feature/add-logging

# 3. Make changes
git commit -m "Add structured logging"

# 4. Push branch
git push -u origin feature/add-logging

# 5. Open Pull Request on GitHub (next lesson)
```

### Scenario 2: Start New Project

```bash
# 1. Create local repository
mkdir my-etl-project
cd my-etl-project
git init

# 2. Create initial files
echo "# My ETL Project" > README.md
git add README.md
git commit -m "Initial commit"

# 3. Create repository on GitHub
# (via web interface)

# 4. Connect and push
git remote add origin https://github.com/user/my-etl-project.git
git push -u origin main
```

### Scenario 3: Sync with Team Changes

```bash
# Morning: pull latest changes
git switch main
git pull origin main

# Work on feature
git switch -c feature/my-work
# ... make commits ...

# Before opening PR: sync with main
git fetch origin
git merge origin/main
# (resolve any conflicts)

# Push updated feature
git push origin feature/my-work
```

## Dealing with Conflicts on Push

### Rejected Push

```bash
git push origin main

# Error:
# ! [rejected]        main -> main (fetch first)
# error: failed to push some refs
```

**What happened:** Remote has commits you don't have.

**Solution:**

```bash
# 1. Pull remote changes
git pull origin main

# 2. Resolve any conflicts
# (see previous lesson on merging)

# 3. Push again
git push origin main
```

## Remote Branches

### View Remote Branches

```bash
# See all branches (local and remote)
git branch -a

# Output:
# * main
#   feature/local-branch
#   remotes/origin/main
#   remotes/origin/feature/remote-branch
```

### Check Out Remote Branch

```bash
# Create local branch tracking remote
git switch -c feature-branch origin/feature-branch

# Shorthand (Git figures it out)
git switch feature-branch
```

### Delete Remote Branch

```bash
# Delete branch on remote
git push origin --delete feature-old-work

# Or:
git push origin :feature-old-work
```

## Key Takeaways

1. **`git clone`** - Copy remote repository to local
2. **`git push`** - Upload commits to remote
3. **`git pull`** - Download and merge remote changes
4. **`git fetch`** - Download without merging
5. **`origin`** - Default name for primary remote
6. **`-u` flag** - Set upstream tracking for easy pushes
7. **Always pull before pushing** - Avoid conflicts

## Best Practices

1. **Pull before starting work** - Stay synced
2. **Commit locally, push often** - Backup your work
3. **Use SSH keys** - Avoid typing passwords
4. **Never force push to shared branches** - Dangerous!
5. **Delete remote branches after merge** - Keep clean

## Practice Exercises

1. **Clone a repository** - Pick any public GitHub repo
2. **Push a change** - Make a commit and push it
3. **Practice fetch** - Use `git fetch` then inspect changes
4. **Sync branches** - Pull changes and resolve a conflict
5. **Add a remote** - Create local repo and push to GitHub

## What's Next?

You now know how to work with remote repositories. Next, you'll learn the **GitHub workflow**—Pull Requests, code reviews, and the collaborative development process.

---

**Navigation:**
- **Previous:** [07 - Merging and Conflicts](07-merging-and-conflicts.md)
- **Next:** [09 - GitHub Workflow](09-github-workflow.md)
- **Home:** [Git Course Overview](README.md)
