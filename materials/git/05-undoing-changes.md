# Undoing Changes in Git

## Overview

Mistakes happen. Git provides multiple ways to undo changes safely. This lesson covers how to unstage files, discard changes, amend commits, and revert changes without losing work.

**Duration:** ~12 minutes

## The Undo Spectrum

Git has different undo commands depending on where your changes are:

```
Working Directory    Staging Area     Repository
     ↓                    ↓                ↓
 git restore         git restore      git revert
                     --staged         git commit --amend
```

Let's explore each scenario.

## Discarding Working Directory Changes

### `git restore` - Discard Uncommitted Changes

**Warning:** This is destructive—changes are lost forever!

```bash
# Make a change
echo "temporary code" >> pipeline.py

# Check status
git status
# modified:   pipeline.py

# Discard the change
git restore pipeline.py

# File is back to last commit
git status
# nothing to commit, working tree clean
```

### Restore Multiple Files

```bash
# Discard all changes
git restore .

# Discard changes in specific directory
git restore src/

# Discard specific files
git restore file1.py file2.py
```

### Old Command (Still Works)

```bash
# The old way (before Git 2.23)
git checkout -- pipeline.py

# Works the same as git restore
```

**Pro tip:** Always run `git diff` first to see what you're about to discard!

```bash
# See changes before discarding
git diff pipeline.py

# If sure, discard
git restore pipeline.py
```

## Unstaging Changes

### `git restore --staged` - Unstage Files

Remove files from staging area without losing changes:

```bash
# Stage a file
git add pipeline.py

# Check status
git status
# Changes to be committed:
#   modified:   pipeline.py

# Unstage it (keeps your changes)
git restore --staged pipeline.py

# Check status
git status
# Changes not staged for commit:
#   modified:   pipeline.py
```

### Unstage Everything

```bash
# Stage multiple files
git add .

# Unstage all
git restore --staged .

# Or old way:
git reset HEAD .
```

**Key difference:**
- `git restore --staged` - Unstage (keeps changes in working directory)
- `git restore` - Discard changes entirely

## Amending the Last Commit

### `git commit --amend` - Fix the Last Commit

Forgot to include a file? Typo in commit message?

#### Fix Commit Message

```bash
# Made a commit with typo
git commit -m "Add validaton logic"

# Fix the message
git commit --amend -m "Add validation logic"
```

#### Add Forgotten Files

```bash
# Make a commit
git commit -m "Add user authentication"

# Oops, forgot to add a file!
git add auth_helper.py

# Add to previous commit
git commit --amend --no-edit
```

**What `--amend` does:**
- Replaces the last commit with a new one
- Combines staged changes with previous commit
- Can change commit message

#### Amend and Edit Message

```bash
# Commit something
git commit -m "Initial implementation"

# Add more changes
echo "more code" >> feature.py
git add feature.py

# Amend with new message
git commit --amend -m "Complete implementation of feature"
```

### Warning: Only Amend Unpushed Commits

**Safe:**
```bash
# Local commits only
git log --oneline
# a3f2b1c (HEAD -> main) Latest commit (not pushed)

git commit --amend  # ✓ Safe
```

**Dangerous:**
```bash
# After pushing to remote
git push origin main

# DON'T amend now - it rewrites history others may have pulled
git commit --amend  # ✗ Dangerous
```

**Why?** Amending rewrites history. If others pulled your commit, their history diverges from yours.

## Reverting Commits

### `git revert` - Safe Undo

Create a new commit that undoes a previous commit:

```bash
# View history
git log --oneline
# c3d4e5f (HEAD -> main) Add buggy feature
# b2c3d4e Add logging
# a1b2c3d Initial commit

# Undo the last commit
git revert c3d4e5f

# Git creates a new commit that undoes it
git log --oneline
# d4e5f6a (HEAD -> main) Revert "Add buggy feature"
# c3d4e5f Add buggy feature
# b2c3d4e Add logging
# a1b2c3d Initial commit
```

**Key points:**
- History is preserved
- Creates a new "undo" commit
- Safe for shared branches
- Can revert any commit, not just the latest

### Revert Without Auto-Commit

```bash
# Revert but don't commit yet
git revert --no-commit c3d4e5f

# Make additional changes if needed
git status
# Changes to be committed:
#   (revert changes here)

# Commit when ready
git commit -m "Revert buggy feature and fix related issues"
```

### Revert Multiple Commits

```bash
# Revert a range of commits
git revert a1b2c3d..c3d4e5f

# Revert last 3 commits
git revert HEAD~3..HEAD
```

## Resetting (Advanced)

### `git reset` - Move Branch Pointer

**Warning:** Can lose work! Use with caution.

Three modes of reset:

#### Soft Reset (Keep Changes Staged)

```bash
# Move HEAD back one commit, keep changes staged
git reset --soft HEAD~1

# Effect:
# - Last commit is "uncommitted"
# - Changes are still staged
# - Working directory unchanged
```

**Use case:** Want to re-commit with a different message or more changes.

#### Mixed Reset (Default - Unstage)

```bash
# Move HEAD back one commit, unstage changes
git reset HEAD~1
# Same as: git reset --mixed HEAD~1

# Effect:
# - Last commit is "uncommitted"
# - Changes are unstaged
# - Working directory unchanged
```

**Use case:** Want to modify changes before re-committing.

#### Hard Reset (Discard Everything)

```bash
# Move HEAD back one commit, discard all changes
git reset --hard HEAD~1

# Effect:
# - Last commit is gone
# - All changes discarded
# - Working directory matches commit
```

**Use case:** Want to completely abandon recent commits (dangerous!).

### Reset Examples

```bash
# Undo last commit, keep changes
git reset HEAD~1

# Undo last 3 commits
git reset HEAD~3

# Reset to specific commit
git reset a1b2c3d

# Discard everything and match remote
git reset --hard origin/main
```

**Advanced Note:** `HEAD~1` means "one commit before HEAD". `HEAD~3` is three commits back. You can also use commit hashes.

## Recovering Lost Commits

### `git reflog` - Safety Net

Git keeps a log of where HEAD has been:

```bash
# View reflog
git reflog

# Output:
# d4e5f6a HEAD@{0}: commit: Add feature
# c3d4e5f HEAD@{1}: reset: moving to HEAD~1
# b2c3d4e HEAD@{2}: commit: Bad commit
# a1b2c3d HEAD@{3}: commit: Initial commit
```

### Recover Accidentally Reset Commit

```bash
# Accidentally did hard reset
git reset --hard HEAD~3

# Oh no! Lost 3 commits!

# Check reflog
git reflog
# c3d4e5f HEAD@{1}: commit: Important work

# Recover by resetting to that commit
git reset --hard c3d4e5f

# Your commits are back!
```

**Pro tip:** Reflog keeps entries for 90 days by default. You have time to recover mistakes.

## Practical Scenarios

### Scenario 1: Wrong File Staged

```bash
# Accidentally staged secret file
git add .
git status
# Changes to be committed:
#   new file:   .env

# Unstage it
git restore --staged .env

# Add to .gitignore
echo ".env" >> .gitignore
git add .gitignore
git commit -m "Add .gitignore"
```

### Scenario 2: Commit Too Early

```bash
# Committed incomplete work
git commit -m "Add validation"

# Realize you need to add more
echo "more validation" >> validate.py
git add validate.py

# Amend the commit
git commit --amend --no-edit
```

### Scenario 3: Committed on Wrong Branch

```bash
# Accidentally committed to main
git log --oneline
# a3f2b1c (HEAD -> main) Work for feature

# Create feature branch at current commit
git branch feature-branch

# Reset main to previous commit
git reset --hard HEAD~1

# Switch to feature branch (has your work)
git switch feature-branch
```

### Scenario 4: Bug in Production

```bash
# Bad commit made it to production
git log --oneline
# d4e5f6a (HEAD -> main) Add feature (breaks prod)
# c3d4e5f Previous stable version

# Revert it (safe for production)
git revert d4e5f6a

# Push the revert
git push origin main

# Production is fixed, debug later
```

## Decision Tree: Which Undo Command?

```
Changes in working directory only?
  → git restore <file>

Changes staged but not committed?
  → git restore --staged <file>

Last commit needs fixing (not pushed)?
  → git commit --amend

Need to undo a pushed commit?
  → git revert <commit>

Need to abandon recent commits (not pushed)?
  → git reset <commit>

Accidentally lost commits?
  → git reflog + git reset
```

## Key Takeaways

1. **`git restore`** - Discard working directory changes (destructive)
2. **`git restore --staged`** - Unstage files (safe)
3. **`git commit --amend`** - Fix last commit (only if not pushed)
4. **`git revert`** - Undo commits safely (creates new commit)
5. **`git reset`** - Move branch pointer (advanced, can lose work)
6. **`git reflog`** - Safety net for recovering lost commits
7. **When in doubt, use `git revert`** - Safest option

## Best Practices

1. **Always `git diff` before `git restore`** - Know what you're discarding
2. **Never amend pushed commits** - Others may have pulled them
3. **Use `git revert` for shared branches** - Preserves history
4. **`git reflog` is your friend** - Check it when something goes wrong
5. **Test in a branch** - Experiment with undo commands safely

## Practice Exercises

1. **Practice restore** - Make changes, discard them
2. **Amend a commit** - Add forgotten files
3. **Revert a commit** - Practice safe undo
4. **Check reflog** - See your command history
5. **Simulate recovery** - Reset and recover using reflog

## What's Next?

You now know how to undo mistakes in Git. Next, you'll learn about **branching**—how to work on features in isolation without affecting the main codebase.

---

**Navigation:**
- **Previous:** [04 - Git Ignore](04-gitignore.md)
- **Next:** [06 - Branching Basics](06-branching-basics.md)
- **Home:** [Git Course Overview](README.md)
