# Viewing Git History

## Overview

Git records every change you make. This lesson teaches you how to view and analyze your project's history using `git log` and `git diff`—essential skills for understanding what changed, when, and why.

**Duration:** ~10 minutes

## Viewing Commit History

### `git log` - See Your Commits

View the complete history:

```bash
git log
```

**Output:**
```
commit a3f2b1c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0 (HEAD -> main)
Author: Jane Doe <jane@example.com>
Date:   Mon Feb 9 10:30:00 2026 -0500

    Add data validation to ETL pipeline
    
    Validate schema before loading to prevent bad data.
    Added unit tests for validation logic.

commit b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1
Author: Jane Doe <jane@example.com>
Date:   Mon Feb 9 09:15:00 2026 -0500

    Initial ETL pipeline structure
```

**Reading the output:**
- **Commit hash** - Unique identifier (`a3f2b1c...`)
- **Author** - Who made the change
- **Date** - When it was committed
- **Message** - What changed and why
- **HEAD -> main** - Current location

### Compact Log Format

The default format is verbose. Use `--oneline` for brevity:

```bash
git log --oneline
```

**Output:**
```
a3f2b1c (HEAD -> main) Add data validation to ETL pipeline
b2c3d4e Initial ETL pipeline structure
```

Much cleaner! This is my go-to format.

### Limiting Log Output

```bash
# Show last 5 commits
git log -5

# Show last 3 commits, one-line format
git log --oneline -3

# Output:
# a3f2b1c (HEAD -> main) Add validation
# b2c3d4e Add transform module
# a1b2c3d Initial structure
```

### Visual Branch History

```bash
# See branch structure graphically
git log --oneline --graph --all

# Output:
# * d4e5f6a (HEAD -> main) Merge feature-branch
# |\  
# | * c3d4e5f (feature-branch) Add new feature
# | * b2c3d4e Work in progress
# |/  
# * a1b2c3d Initial commit
```

**Advanced Note:** The `--graph` flag draws ASCII art showing how branches diverge and merge. The `--all` flag shows all branches, not just your current one.

## Searching Commit History

### Filter by Author

```bash
# See commits by specific person
git log --author="Jane"

# Case-insensitive search
git log --author="jane" -i
```

### Filter by Message

```bash
# Find commits mentioning "bug"
git log --grep="bug"

# Find commits mentioning "fix" or "hotfix"
git log --grep="fix" --grep="hotfix"

# Case-insensitive
git log --grep="bug" -i
```

### Filter by Date

```bash
# Commits from last week
git log --since="1 week ago"

# Commits from specific date range
git log --since="2026-02-01" --until="2026-02-09"

# Last 2 weeks
git log --since="2 weeks ago"

# Commits from yesterday
git log --since="yesterday"
```

### Filter by File

```bash
# See commits that changed a specific file
git log -- pipeline.py

# With one-line format
git log --oneline -- src/transform.py

# All commits affecting files in a directory
git log -- src/
```

**Pro tip:** The `--` separates options from file paths. It's optional but prevents ambiguity if your filename looks like a branch name.

## Viewing File Changes

### `git log` with Diffs

```bash
# Show what changed in each commit
git log -p

# Show last 2 commits with changes
git log -p -2

# Show changes for specific file
git log -p -- pipeline.py
```

### `git log --stat` - File Statistics

See which files changed and how much:

```bash
git log --stat
```

**Output:**
```
commit a3f2b1c (HEAD -> main)
Author: Jane Doe <jane@example.com>
Date:   Mon Feb 9 10:30:00 2026 -0500

    Add data validation

 src/validate.py | 45 ++++++++++++++++++++++++++++
 tests/test_validate.py | 32 +++++++++++++++++++
 2 files changed, 77 insertions(+)
```

**Reading stats:**
- `45 +++++++...` - 45 lines added
- `2 files changed, 77 insertions(+)` - Summary

### One-line with Stats

```bash
git log --oneline --stat
```

Compact commits with file statistics—very useful!

## Comparing Changes

### `git diff` - See Unstaged Changes

View changes in your working directory:

```bash
# Make a change
echo 'print("Updated!")' >> hello.py

# See the diff
git diff
```

**Output:**
```diff
diff --git a/hello.py b/hello.py
index e75154b..d88e9f4 100644
--- a/hello.py
+++ b/hello.py
@@ -1 +1,2 @@
 print("Hello, Git!")
+print("Updated!")
```

**Reading diffs:**
- `--- a/hello.py` - Original file (before)
- `+++ b/hello.py` - Modified file (after)
- `@@ -1 +1,2 @@` - Line numbers (starts at line 1)
- `-` lines removed (red in terminal)
- `+` lines added (green in terminal)

### `git diff --staged` - See Staged Changes

View what you're about to commit:

```bash
# Stage a change
git add hello.py

# Regular diff shows nothing (no unstaged changes)
git diff
# (no output)

# See staged changes
git diff --staged
```

**Also works:** `git diff --cached` (same as `--staged`)

**Pro tip:** Always run `git diff --staged` before committing to review what you're about to save.

### Comparing Commits

```bash
# Diff between two commits
git diff a1b2c3d b2c3d4e

# Diff between HEAD and 3 commits ago
git diff HEAD~3 HEAD

# Diff between main and feature-branch
git diff main feature-branch
```

### Comparing Specific Files

```bash
# Diff for one file only
git diff hello.py

# Staged changes for one file
git diff --staged pipeline.py

# Compare file between commits
git diff a1b2c3d b2c3d4e -- pipeline.py
```

## Advanced Diff Options

### Word-level Diff

Instead of line-by-line, see word-by-word changes:

```bash
git diff --word-diff
```

**Output:**
```
print("Hello, [-Git!-]{+World!+}")
```

Useful for text or documentation changes.

### Ignore Whitespace

```bash
# Ignore whitespace changes
git diff -w

# Ignore whitespace at end of lines
git diff --ignore-space-at-eol
```

**Use case:** Someone reformatted code with different indentation—ignore it to see real changes.

### Summary Only

```bash
# Just show which files changed
git diff --name-only

# Output:
# hello.py
# pipeline.py

# Show status too (added, modified, deleted)
git diff --name-status

# Output:
# M	hello.py
# A	new_file.py
# D	old_file.py
```

## Viewing a Specific Commit

### `git show` - Inspect One Commit

```bash
# Show the most recent commit
git show

# Show a specific commit
git show a3f2b1c

# Show commit message only
git show --no-patch a3f2b1c

# Show files changed
git show --stat a3f2b1c

# Show specific file from a commit
git show a3f2b1c:pipeline.py
```

## Practical Workflows

### Review Before Committing

```bash
# 1. Make changes
echo "new feature" >> feature.py

# 2. Stage
git add feature.py

# 3. Review what you're committing
git diff --staged

# 4. If looks good, commit
git commit -m "Add new feature"
```

### Find When a Bug Was Introduced

```bash
# Search commit messages
git log --oneline --grep="authentication"

# See what changed
git show a3f2b1c

# Check specific file history
git log -p -- auth.py
```

### Compare Your Branch to Main

```bash
# See what's different
git diff main..feature-branch

# See commits only on feature-branch
git log main..feature-branch --oneline
```

### Debugging: What Changed Recently?

```bash
# Last 5 commits with files
git log --oneline --stat -5

# Changes in the last day
git log --since="1 day ago" -p

# Who changed this file?
git log --oneline -- problematic_file.py
```

## Formatting Log Output

### Custom Format

```bash
# Custom format with placeholders
git log --pretty=format:"%h - %an, %ar : %s"

# Output:
# a3f2b1c - Jane Doe, 2 hours ago : Add validation
# b2c3d4e - Jane Doe, 1 day ago : Initial structure
```

**Common placeholders:**
- `%h` - Short hash
- `%H` - Full hash
- `%an` - Author name
- `%ae` - Author email
- `%ar` - Relative date (2 hours ago)
- `%ad` - Absolute date
- `%s` - Subject (commit message)

### Useful Aliases

Add these to your Git config:

```bash
# Pretty log with graph
git config --global alias.lg "log --oneline --graph --all"

# Log with files changed
git config --global alias.ls "log --stat"

# Use them:
git lg
git ls
```

## Key Takeaways

1. **`git log`** - View commit history
2. **`git log --oneline`** - Compact view (most useful)
3. **`git log --grep`** - Search commit messages
4. **`git log -- file`** - File-specific history
5. **`git diff`** - See unstaged changes
6. **`git diff --staged`** - Review before commit
7. **`git show`** - Inspect specific commits

## Practice Exercises

1. **View your history** - Use `git log` with different flags
2. **Search commits** - Find commits by author and message
3. **Compare changes** - Use `git diff` before and after staging
4. **Create aliases** - Set up shortcuts for common log commands
5. **Inspect a commit** - Use `git show` to see what changed

## What's Next?

You can now view and analyze your project's history. Next, you'll learn about **`.gitignore`**—how to tell Git which files to never track.

---

**Navigation:**
- **Previous:** [02 - Basic Commands](02-basic-commands.md)
- **Next:** [04 - Git Ignore](04-gitignore.md)
- **Home:** [Git Course Overview](README.md)
