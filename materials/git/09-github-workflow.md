# GitHub Workflow & Pull Requests

## Overview

Pull Requests (PRs) are how teams collaborate on code. This lesson covers the GitHub Flow workflow, creating PRs, conducting code reviews, and merging changes professionally.

**Duration:** ~15 minutes

## What is a Pull Request?

A **Pull Request** is a request to merge your branch into another branch (usually `main`):

```
Your feature branch  →  PR  →  main branch
                         ↓
                    Code Review
```

**Why PRs matter:**
- **Code review** - Catch bugs before merging
- **Discussion** - Collaborate on implementation
- **Documentation** - PR describes what changed and why
- **CI/CD** - Automated tests run on PR
- **History** - Clear record of what was merged and when

## GitHub Flow

The most popular workflow for teams:

```
1. Create branch from main
         ↓
2. Make commits
         ↓
3. Push branch
         ↓
4. Open Pull Request
         ↓
5. Code review & discussion
         ↓
6. Merge to main
         ↓
7. Deploy (optional automation)
```

**Why this works:**
- `main` is always deployable
- Features developed in isolation
- Everything reviewed before merging
- Simple and predictable

## Creating a Pull Request

### Complete PR Workflow

```bash
# 1. Start from updated main
git switch main
git pull origin main

# 2. Create feature branch
git switch -c feature/add-email-validation

# 3. Make changes and commit
echo "def validate_email(email): ..." > validate.py
git add validate.py
git commit -m "Add email validation function"

echo "def test_validate_email(): ..." > test_validate.py
git add test_validate.py
git commit -m "Add tests for email validation"

# 4. Push branch to GitHub
git push -u origin feature/add-email-validation

# Output includes PR link:
# remote: Create a pull request for 'feature/add-email-validation' on GitHub:
# remote:   https://github.com/user/repo/pull/new/feature/add-email-validation
```

### On GitHub Website

1. **Navigate to repository**
2. **Click "Compare & pull request"** (appears after push)
3. **Fill out PR template:**
   - **Title** - Descriptive summary (e.g., "Add email validation")
   - **Description** - What changed and why
   - **Reviewers** - Assign teammates
   - **Labels** - bug, feature, documentation, etc.
4. **Click "Create pull request"**

### Good PR Description

```markdown
## Summary
Add email validation to user registration form.

## Changes
- Add `validate_email()` function using regex
- Add unit tests covering valid/invalid emails
- Update registration endpoint to use validation

## Why
Current implementation allows invalid emails, causing issues downstream.

## Testing
- All unit tests pass
- Tested manually with 10+ email formats
- No breaking changes to existing API

## Screenshots (if UI changes)
[Attach screenshots]

## Related Issues
Fixes #123
```

## Code Review Process

### As the Author

```bash
# 1. Respond to review comments
# (on GitHub website)

# 2. Make requested changes locally
git switch feature/add-email-validation
echo "# Updated based on review" >> validate.py
git commit -am "Address review feedback"

# 3. Push updates
git push

# PR automatically updates with new commits
```

### As a Reviewer

**What to look for:**
- **Correctness** - Does it work?
- **Tests** - Are there tests? Do they cover edge cases?
- **Style** - Follows team conventions?
- **Performance** - Any obvious bottlenecks?
- **Security** - Any vulnerabilities?
- **Documentation** - Complex logic explained?

**Good review comments:**

```
✓ "Consider using `emailRegex.test()` instead of `match()` for better performance"
✓ "Can you add a test for emails with special characters?"
✓ "Nice refactor! Much more readable now."

✗ "This is wrong"
✗ "Why did you do it this way?"
✗ "I would have done it differently"
```

**Be constructive:** Suggest solutions, ask questions, praise good code.

### Review Actions on GitHub

- **Comment** - General feedback
- **Approve** - LGTM (Looks Good To Me)
- **Request changes** - Must be addressed before merge
- **Suggested edits** - GitHub can apply small changes directly

## Merging Pull Requests

### Merge Strategies on GitHub

#### 1. Merge Commit (Default)

```
main:    A ← B ← C ← M
              ↓     ↗
feature:      D ← E
```

Preserves all commits and history.

```bash
# Equivalent to:
git switch main
git merge --no-ff feature/add-validation
```

**Use when:** You want full history preserved.

#### 2. Squash and Merge

```
main:    A ← B ← C ← D'

feature: (disappeared, squashed into D')
```

Combines all feature commits into one.

```bash
# Equivalent to:
git switch main
git merge --squash feature/add-validation
git commit -m "Add email validation (#42)"
```

**Use when:** Feature has many small "wip" commits you want to clean up.

#### 3. Rebase and Merge

```
main:    A ← B ← C ← D ← E

feature: (disappeared, commits moved to main)
```

Linear history without merge commit.

**Use when:** You want clean linear history (advanced).

### After Merging

```bash
# 1. Pull updated main
git switch main
git pull origin main

# 2. Delete local feature branch
git branch -d feature/add-email-validation

# 3. Delete remote branch (if not auto-deleted)
git push origin --delete feature/add-email-validation
```

GitHub can auto-delete branch after merge (configure in settings).

## Draft Pull Requests

Open a PR that's not ready for review:

1. **Create PR** as usual
2. **Select "Create draft pull request"**
3. **Mark as "Ready for review"** when done

**Use draft PRs for:**
- Early feedback on approach
- CI/CD testing
- Showing progress to team

## PR Best Practices

### Keep PRs Small

**Bad:**
- 2000 lines changed
- 20 files modified
- Multiple unrelated features

**Good:**
- 200 lines changed
- 3-5 files modified
- One focused change

**Why:** Small PRs are easier to review, faster to merge, less likely to have bugs.

### Commit Messages in PRs

```bash
# Bad commits
git commit -m "fix"
git commit -m "update"
git commit -m "more changes"

# Good commits
git commit -m "Add email validation regex"
git commit -m "Add tests for email validation"
git commit -m "Handle edge case for international emails"
```

### Update PR Title and Description

If PR scope changes during development:
- Update title to reflect final state
- Update description with new context
- Add comments explaining significant changes

### Respond to All Comments

- Mark resolved when fixed
- Explain if you disagree
- Thank reviewers for feedback

## Handling PR Conflicts

### Conflict Detected

```
This branch has conflicts that must be resolved
```

**Resolution:**

```bash
# 1. Pull latest main
git switch main
git pull origin main

# 2. Switch to feature branch
git switch feature/add-validation

# 3. Merge main into feature
git merge main

# 4. Resolve conflicts
# (see Merging lesson)

# 5. Push resolution
git push

# PR automatically updates
```

### Keep Feature Updated

```bash
# While PR is open, regularly sync with main
git switch feature/my-feature
git fetch origin
git merge origin/main
git push
```

Prevents large conflicts at merge time.

## CI/CD Integration

### Automated Checks on PRs

Typical GitHub Actions workflow:

```yaml
# .github/workflows/test.yml
name: Tests

on: [pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          python -m pytest
      - name: Lint
        run: |
          flake8 .
```

**PR shows:**
- ✓ All checks passed
- ✗ Some checks failed

**Best practice:** Don't merge if checks fail.

## Protecting Main Branch

### Branch Protection Rules

Configure on GitHub:

1. **Settings** → **Branches** → **Add rule**
2. **Branch name pattern:** `main`
3. **Enable:**
   - ✓ Require pull request before merging
   - ✓ Require approvals (1-2 reviewers)
   - ✓ Require status checks to pass
   - ✓ Require branches to be up to date
   - ✓ Include administrators

**Result:** Can't push directly to main, must go through PR.

## Real-World Scenarios

### Scenario 1: Simple Feature PR

```bash
# 1. Create feature
git switch -c feature/add-logging
# ... develop ...
git push -u origin feature/add-logging

# 2. Open PR on GitHub
# Title: "Add structured logging to ETL pipeline"

# 3. Reviewer approves
# 4. Squash and merge
# 5. Delete branch
```

### Scenario 2: PR with Review Feedback

```bash
# 1. Open PR
git push -u origin feature/refactor-query

# 2. Reviewer requests changes:
# "Please add error handling for NULL values"

# 3. Make changes
git switch feature/refactor-query
# ... add error handling ...
git commit -m "Add NULL value error handling"
git push

# 4. Re-review
# 5. Approved and merged
```

### Scenario 3: Emergency Hotfix

```bash
# 1. Critical bug in production
git switch main
git pull origin main

# 2. Create hotfix branch
git switch -c hotfix/fix-sql-injection

# 3. Fix bug
git commit -m "Fix SQL injection in user query"

# 4. Push and open PR
git push -u origin hotfix/fix-sql-injection

# 5. Fast review and merge
# 6. Deploy immediately
```

## Key Takeaways

1. **Pull Requests** - Request to merge your branch
2. **GitHub Flow** - Branch → Commit → PR → Review → Merge
3. **Code review** - Essential for quality and knowledge sharing
4. **Keep PRs small** - Easier to review, faster to merge
5. **CI/CD on PRs** - Automated testing before merge
6. **Protect main** - Require PRs and reviews
7. **Communicate clearly** - Good descriptions and commit messages

## Best Practices

1. **One PR = one feature** - Keep changes focused
2. **Write good descriptions** - Explain what and why
3. **Respond to feedback** - Be open to suggestions
4. **Review thoughtfully** - Look for bugs and improvements
5. **Keep branches updated** - Merge main regularly
6. **Delete merged branches** - Keep repository clean

## Practice Exercises

1. **Fork a repo** - Practice on your own fork
2. **Open a PR** - Make a small change and create PR
3. **Review a PR** - Review someone else's code
4. **Handle conflict** - Create conflicting changes and resolve
5. **Use draft PR** - Practice early feedback workflow

## What's Next?

You now understand the GitHub workflow and Pull Requests. Next, you'll learn about **Git in the real world**—how companies use Git, CI/CD integration, and data engineering-specific practices.

---

**Navigation:**
- **Previous:** [08 - Remote Basics](08-remote-basics.md)
- **Next:** [10 - Git in the Real World](10-git-in-real-world.md)
- **Home:** [Git Course Overview](README.md)
