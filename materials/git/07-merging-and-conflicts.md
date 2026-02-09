# Merging and Conflict Resolution

## Overview

After working on a branch, you need to integrate your changes back into main. This lesson covers merging strategies, handling merge conflicts, and resolving them like a pro.

**Duration:** ~15 minutes

## What is Merging?

**Merging** combines changes from different branches:

```
Before merge:
main:    A ← B ← C
               ↓
feature:       D ← E

After merge:
main:    A ← B ← C ← M
               ↓     ↗
feature:       D ← E
```

The merge commit `M` combines changes from both branches.

## Basic Merging

### `git merge` - Combine Branches

```bash
# 1. Start on main branch
git switch main

# 2. Merge feature branch into main
git merge feature-validation

# Output:
# Updating a3f2b1c..b2c3d4e
# Fast-forward
#  validate.py | 10 ++++++++++
#  1 file changed, 10 insertions(+)
```

**Important:** Always merge **into** your current branch, **from** the named branch.

### Complete Merge Example

```bash
# 1. Create and work on feature branch
git switch -c feature/add-logging
echo "import logging" > logger.py
git add logger.py
git commit -m "Add logging module"

# 2. Switch back to main
git switch main

# 3. Merge feature into main
git merge feature/add-logging

# 4. Delete merged branch (cleanup)
git branch -d feature/add-logging
```

## Types of Merges

### Fast-Forward Merge

When main hasn't changed since you branched:

```
Before:
main:    A ← B
            ↓
feature:    C ← D

After fast-forward:
main:    A ← B ← C ← D
```

Git just moves the `main` pointer forward. No merge commit created.

```bash
git merge feature
# Updating a3f2b1c..d4e5f6a
# Fast-forward
```

### Three-Way Merge

When both branches have new commits:

```
Before:
main:    A ← B ← C
            ↓
feature:    D ← E

After merge:
main:    A ← B ← C ← M
            ↓       ↗
feature:    D ← E
```

Git creates a merge commit `M` with two parents (`C` and `E`).

#### How the Three-Way Merge Algorithm Works

The key insight is in the name: **three-way**. Git doesn't just compare the two branch tips — it uses three snapshots:

1. **Base (B):** The common ancestor — the last commit both branches share
2. **Ours (C):** The tip of the current branch (`main`)
3. **Theirs (E):** The tip of the branch being merged (`feature`)

For **every file** in the repository, Git compares all three versions:

| Base (B) | Ours (C) | Theirs (E) | Result |
|----------|----------|------------|--------|
| unchanged | unchanged | unchanged | Keep as-is |
| unchanged | **changed** | unchanged | Take **ours** |
| unchanged | unchanged | **changed** | Take **theirs** |
| unchanged | **changed** | **changed** (same) | Take either (identical change) |
| unchanged | **changed** | **changed** (different) | **CONFLICT** — manual resolution needed |

This is how Git reaches a consistent state automatically in most cases: if only one side modified a file (or a specific section within a file), Git knows that change is the intended one and applies it. When both sides changed the **same lines differently**, Git cannot decide which version is correct — that's when you get a merge conflict.

The resulting merge commit `M` contains the combined work from both branches and records both `C` and `E` as its parents, preserving the full history of how the code evolved on each branch.

```bash
git merge feature
# Merge made by the 'recursive' strategy.
```

**Advanced Note:** Git uses the "recursive" merge strategy by default (called "ort" in newer versions). It finds the common ancestor of both branches and performs the three-way comparison described above. In rare cases where branches have **multiple common ancestors** (criss-cross merges), the recursive strategy merges the ancestors first to create a virtual base — hence the name "recursive."

## Merge Conflicts

### What Causes Conflicts?

Conflicts occur when both branches modify the same lines of code:

```
main:    A ← B (modify line 5)
            ↓
feature:    C (modify line 5 differently)
```

Git doesn't know which change to keep, so it asks you.

### Recognizing a Conflict

```bash
git merge feature/update-pipeline

# Output:
# Auto-merging pipeline.py
# CONFLICT (content): Merge conflict in pipeline.py
# Automatic merge failed; fix conflicts and then commit the result.
```

### Conflict Status

```bash
git status

# Output:
# On branch main
# You have unmerged paths.
#   (fix conflicts and run "git commit")
#
# Unmerged paths:
#   (use "git add <file>..." to mark resolution)
#	both modified:   pipeline.py
```

## Reading Conflict Markers

Git adds markers to conflicted files:

```python
def process_data(data):
<<<<<<< HEAD
    # Main branch version
    return data.dropna()
=======
    # Feature branch version
    return data.fillna(0)
>>>>>>> feature/update-pipeline
```

**Reading the markers:**
- `<<<<<<< HEAD` - Your current branch (main)
- `=======` - Separator
- `>>>>>>> feature/update-pipeline` - The branch you're merging

## Resolving Conflicts

### Step-by-Step Resolution

```bash
# 1. Identify conflicted files
git status
# Unmerged paths:
#   both modified:   pipeline.py

# 2. Open the file in your editor
# (VSCode shows a nice diff view)

# 3. Choose which version to keep, or combine them
# Remove conflict markers manually:

# Original conflict:
# <<<<<<< HEAD
#     return data.dropna()
# =======
#     return data.fillna(0)
# >>>>>>> feature/update-pipeline

# Resolved (keep both, use fillna then dropna):
    return data.fillna(0).dropna()

# 4. Stage the resolved file
git add pipeline.py

# 5. Check status
git status
# All conflicts fixed: run "git commit"

# 6. Complete the merge
git commit -m "Merge feature/update-pipeline

Resolved conflict by combining both approaches."
```

### Conflict Resolution Strategies

#### Option 1: Keep Current Branch (Ours)

```bash
# Keep your version (main)
git checkout --ours pipeline.py
git add pipeline.py
```

#### Option 2: Keep Incoming Branch (Theirs)

```bash
# Keep their version (feature branch)
git checkout --theirs pipeline.py
git add pipeline.py
```

#### Option 3: Manual Resolution

Edit the file, remove markers, keep the best parts:

```python
# Original conflict
<<<<<<< HEAD
result = df.dropna()
=======
result = df.fillna(method='ffill')
>>>>>>> feature

# Resolved - combine approaches
result = df.fillna(method='ffill').dropna(subset=['critical_column'])
```

## Aborting a Merge

Changed your mind mid-merge?

```bash
# Cancel the merge, return to pre-merge state
git merge --abort

# Your working directory is restored
git status
# On branch main, nothing to commit
```

## Practical Merge Workflows

### Workflow 1: Feature Complete

```bash
# Feature branch is done
git switch feature/new-dashboard

# Make sure it's up to date with main first
git switch main
git pull origin main

# Merge main into feature (get latest changes)
git switch feature/new-dashboard
git merge main
# (resolve any conflicts here)

# Now merge feature into main
git switch main
git merge feature/new-dashboard

# Push to remote
git push origin main

# Cleanup
git branch -d feature/new-dashboard
```

### Workflow 2: Conflict During Merge

```bash
# Attempt merge
git merge feature/data-validation

# Conflict!
# Auto-merging validate.py
# CONFLICT (content): Merge conflict in validate.py

# Check what's conflicted
git status

# Resolve in editor
code validate.py
# (fix conflicts)

# Stage resolved file
git add validate.py

# Complete merge
git commit -m "Merge feature/data-validation

Resolved conflicts in validate.py by combining both validation approaches."
```

### Workflow 3: Multiple Conflicts

```bash
# Merge with many conflicts
git merge feature/big-refactor

# CONFLICT in file1.py, file2.py, file3.py

# Resolve one by one
code file1.py
# (fix conflicts)
git add file1.py

code file2.py
# (fix conflicts)
git add file2.py

code file3.py
# (fix conflicts)
git add file3.py

# Check all resolved
git status
# All conflicts fixed

# Complete merge
git commit
# (Git provides default merge message)
```

## Visualizing Merges

### Graph View

```bash
# See branch structure with merges
git log --oneline --graph --all

# Output:
# *   d4e5f6a (HEAD -> main) Merge feature/add-validation
# |\  
# | * c3d4e5f (feature/add-validation) Add tests
# | * b2c3d4e Add validation logic
# |/  
# * a1b2c3d Initial commit
```

### Merge History

```bash
# See only merge commits
git log --merges --oneline

# See non-merge commits only
git log --no-merges --oneline
```

## Preventing Conflicts

### Best Practices

1. **Commit often** - Small commits = smaller conflicts
2. **Pull regularly** - Stay synced with main
3. **Communicate** - Know what teammates are working on
4. **Small branches** - Merge within days, not weeks
5. **Modular code** - Different people work on different files

### Keep Feature Branch Updated

```bash
# While working on feature, regularly merge main
git switch feature/my-feature

# Pull latest main
git fetch origin main

# Merge main into feature
git merge origin/main

# Resolve any conflicts now (not later during final merge)
```

## Merge vs Rebase

### Quick Comparison

```bash
# Merge: Creates merge commit, preserves history
git merge feature

# Rebase: Replays commits, linear history (advanced topic)
git rebase main
```

**For now:** Stick with merge. Rebase is powerful but more complex.

## Real-World Scenarios

### Scenario 1: Clean Merge

```bash
# Feature development complete
git switch main
git merge feature/add-logging
# Fast-forward
git branch -d feature/add-logging
git push origin main
```

### Scenario 2: Conflict in SQL Query

```bash
# Merge attempt
git merge feature/optimize-query
# CONFLICT in queries.sql

# Both changed the same query
# HEAD version:
SELECT user_id, COUNT(*) FROM orders GROUP BY user_id;

# Feature version:
SELECT user_id, SUM(total) FROM orders GROUP BY user_id;

# Resolved version (combine both):
SELECT user_id, COUNT(*) as order_count, SUM(total) as total_spent
FROM orders GROUP BY user_id;

git add queries.sql
git commit -m "Merge optimize-query with count and sum"
```

### Scenario 3: Conflicting Configuration

```bash
# Both branches modified config.yaml
# Resolve by keeping both settings
git merge feature/new-config

# Edit config.yaml - combine both features
git add config.yaml
git commit
```

## Key Takeaways

1. **`git merge`** - Combine branches
2. **Fast-forward** - Simple merge when no divergence
3. **Three-way merge** - Creates merge commit for divergent branches
4. **Conflicts are normal** - Happen when same lines change
5. **Resolve conflicts** - Edit file, remove markers, stage, commit
6. **`git merge --abort`** - Cancel problematic merge
7. **Keep branches updated** - Merge main into feature regularly

## Best Practices

1. **Always merge from main** - Ensure you're on the target branch
2. **Review before merging** - `git diff main..feature`
3. **Test after merging** - Run tests before pushing
4. **Keep commits atomic** - Makes conflicts easier to resolve
5. **Delete merged branches** - Keep repository clean

## Practice Exercises

1. **Create and merge** - Feature branch with no conflicts
2. **Simulate conflict** - Edit same line on two branches, merge
3. **Resolve conflict** - Practice all three resolution methods
4. **Abort merge** - Practice `git merge --abort`
5. **View merge history** - Use `git log --graph`

## What's Next?

You can now merge branches and resolve conflicts. Next, you'll learn about **remote repositories and collaboration**—how to work with GitHub, push/pull code, and collaborate with others.

---

**Navigation:**
- **Previous:** [06 - Branching Basics](06-branching-basics.md)
- **Next:** [08 - Remote Basics](08-remote-basics.md)
- **Home:** [Git Course Overview](README.md)
