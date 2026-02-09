# Branching Basics

## Overview

Branches are one of Git's killer features. They let you work on new features, experiments, or bug fixes in isolation without affecting the main codebase. This lesson covers what branches are, why they're essential, and how to create and use them.

**Duration:** ~10 minutes

## What Are Branches?

A **branch** is simply a movable pointer to a commit. That's it!

```
main:      A ← B ← C  (HEAD)
                     ↑
                   main
```

When you create a branch, you're creating a new pointer:

```
main:      A ← B ← C
                     ↑
                   main
                     ↑
              feature-branch (HEAD)
```

**Key insight:** Branches are incredibly lightweight in Git—just a 41-byte file containing a commit hash.

## Why Use Branches?

### Isolation
Work on a feature without breaking `main`:

```
main:          A ← B ← C  (stable)
                     ↓
feature:             D ← E  (experimental)
```

### Parallel Work
Multiple features simultaneously:

```
main:          A ← B ← C
                     ├─→ D (feature-1)
                     └─→ E (feature-2)
```

### Safe Experimentation
Try something risky without consequences:

```
experiment:    A ← B ← X ← Y  (if it works, merge it)
                     ↓
main:                C ← D    (if not, delete branch)
```

**In data engineering:**
- Test new SQL query on a branch
- Develop Airflow DAG without breaking production
- Experiment with different transformation logic

## Viewing Branches

### `git branch` - List Branches

```bash
# List local branches
git branch

# Output:
# * main
#   feature-auth

# The * indicates your current branch
```

### See All Branches

```bash
# Include remote branches
git branch -a

# Output:
# * main
#   feature-auth
#   remotes/origin/main
#   remotes/origin/feature-auth
```

### Verbose Output

```bash
# See last commit on each branch
git branch -v

# Output:
# * main         a3f2b1c Initial commit
#   feature-auth b2c3d4e Add auth logic
```

## Creating Branches

### `git branch` - Create a Branch

```bash
# Create new branch (doesn't switch to it)
git branch feature-validation

# Verify it exists
git branch
# Output:
#   feature-validation
# * main
```

### `git switch -c` - Create and Switch

The modern way (Git 2.23+):

```bash
# Create and switch in one command
git switch -c feature-validation

# Verify you're on the new branch
git branch
# Output:
# * feature-validation
#   main
```

### Old Way: `git checkout -b`

Still works, but `git switch` is clearer:

```bash
# Old command (still valid)
git checkout -b feature-validation

# Same result as: git switch -c feature-validation
```

## Switching Branches

### `git switch` - Change Branches

```bash
# Switch to existing branch
git switch main

# Verify
git branch
# Output:
# * main
#   feature-validation
```

### Old Way: `git checkout`

```bash
# Old command
git checkout main

# Same as: git switch main
```

**Why `git switch`?** Git 2.23 split `git checkout` into two clearer commands:
- `git switch` - Change branches
- `git restore` - Restore files

## Working with Branches

### Complete Workflow Example

```bash
# 1. Create and switch to new branch
git switch -c feature-data-validation

# 2. Make changes
cat > validate.py << EOF
def validate_schema(df):
    required_cols = ['id', 'name', 'email']
    return all(col in df.columns for col in required_cols)
EOF

# 3. Stage and commit
git add validate.py
git commit -m "Add schema validation function"

# 4. Make more changes
echo "# Tests for validation" > test_validate.py
git add test_validate.py
git commit -m "Add validation tests"

# 5. View history on this branch
git log --oneline
# Output:
# b2c3d4e (HEAD -> feature-data-validation) Add validation tests
# a1b2c3d Add schema validation function
# (previous commits from main)

# 6. Switch back to main
git switch main

# 7. Your work is safe on the feature branch
git log --oneline
# (doesn't show feature commits)
```

### Branch Timeline Visualization

```
Before branching:
main: A ← B ← C (HEAD)

After git switch -c feature:
main: A ← B ← C
                ↓
feature:        (HEAD)

After 2 commits on feature:
main: A ← B ← C
                ↓
feature:        D ← E (HEAD)

After git switch main:
main: A ← B ← C (HEAD)
                ↓
feature:        D ← E
```

## Branch Naming Conventions

### Good Branch Names

```bash
feature/user-authentication
feature/data-validation
bugfix/fix-sql-injection
hotfix/prod-crash
experiment/try-new-algo
```

### Common Patterns

```bash
# Feature development
feature/add-logging
feature/user-dashboard

# Bug fixes
bugfix/fix-null-pointer
fix/correct-date-format

# Hotfixes (urgent production fixes)
hotfix/critical-security-patch

# Experimental work
experiment/test-kafka-integration
spike/evaluate-dbt

# Personal work
doron/prototype-new-feature
```

**Pro tip:** Use descriptive names. Avoid `temp`, `test`, `new-branch`.

## Checking Branch Status

### What Branch Am I On?

```bash
# Method 1: git branch
git branch
# * feature-validation
#   main

# Method 2: git status
git status
# On branch feature-validation

# Method 3: Command line prompt (if configured)
# Shows in terminal: (feature-validation)
```

### What's Different Between Branches?

```bash
# Compare current branch to main
git diff main

# Compare two branches
git diff main..feature-validation

# See commit differences
git log main..feature-validation --oneline
# Output:
# b2c3d4e Add validation tests
# a1b2c3d Add schema validation
```

## Deleting Branches

### Delete Merged Branch

```bash
# After merging feature into main
git branch -d feature-validation

# Git checks if branch is merged
# If merged: deletes safely
# If not merged: refuses (safety check)
```

### Force Delete Unmerged Branch

```bash
# Delete branch even if not merged
git branch -D experimental-feature

# Warning: loses any unmerged commits!
```

### Delete Remote Branch

```bash
# Delete branch on GitHub/remote
git push origin --delete feature-old-branch
```

## Practical Scenarios

### Scenario 1: Develop a New Feature

```bash
# Start from main
git switch main

# Create feature branch
git switch -c feature/add-etl-logging

# Develop
echo "import logging" > logger.py
git add logger.py
git commit -m "Add logging module"

# More work
echo "def log_error(msg): ..." >> logger.py
git commit -am "Add error logging function"

# Feature complete - merge later (next lesson)
```

### Scenario 2: Emergency Bug Fix

```bash
# Currently on feature branch
git branch
# * feature/new-dashboard
#   main

# Urgent bug in production!
git switch main

# Create hotfix branch
git switch -c hotfix/fix-sql-query

# Fix bug
git add fixed_query.py
git commit -m "Fix SQL injection vulnerability"

# Deploy hotfix (merge to main)
# Return to feature work
git switch feature/new-dashboard
```

### Scenario 3: Experiment Safely

```bash
# Want to try risky refactor
git switch -c experiment/refactor-pipeline

# Try new approach
# ... make changes ...
git commit -am "Complete refactor"

# Test it
# ... runs tests ...

# If it works: keep branch for merging
# If it fails: delete branch
git switch main
git branch -D experiment/refactor-pipeline
```

## HEAD: What Am I Looking At?

**HEAD** is a pointer to your current location:

```bash
# HEAD points to a branch (normal)
main: A ← B ← C ← HEAD (main)

# After switching:
feature: A ← B ← C ← D ← HEAD (feature)
main:    A ← B ← C
```

**Advanced Note:** HEAD usually points to a branch, but it can point directly to a commit ("detached HEAD"). We'll cover this in advanced topics.

## Key Takeaways

1. **Branches are lightweight** - Just pointers to commits
2. **`git switch -c`** - Create and switch to new branch
3. **`git switch`** - Change to existing branch
4. **`git branch`** - List branches
5. **Name branches descriptively** - `feature/add-validation` not `temp`
6. **Delete merged branches** - Keep repo clean with `-d`
7. **Experiment freely** - Branches make trying new ideas safe

## Best Practices

1. **Branch for every feature** - Even small ones
2. **Keep branches short-lived** - Merge within days, not months
3. **Name branches clearly** - Future you will appreciate it
4. **Delete merged branches** - Reduce clutter
5. **Start branches from main** - Ensures clean base

## Practice Exercises

1. **Create 3 branches** - Practice `git switch -c`
2. **Switch between branches** - Use `git switch`
3. **Make commits on different branches** - See how they stay isolated
4. **Compare branches** - Use `git diff branch1..branch2`
5. **Delete a branch** - Practice cleanup

## What's Next?

You now understand branches and how to work on them. Next, you'll learn about **merging and conflict resolution**—how to combine work from different branches.

---

**Navigation:**
- **Previous:** [05 - Undoing Changes](05-undoing-changes.md)
- **Next:** [07 - Merging and Conflicts](07-merging-and-conflicts.md)
- **Home:** [Git Course Overview](README.md)
