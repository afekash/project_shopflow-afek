# Git & Version Control for Data Engineering

Welcome to the Git course! This module covers everything you need to know about version control with Git, from basic concepts to real-world workflows including CI/CD and GitHub collaboration.

## Course Overview

Git is the industry-standard version control system used by virtually every software and data engineering team. This course teaches you how to track changes, collaborate with teams, and integrate Git into modern data engineering workflows.

## Prerequisites

- No prior Git experience required
- Python installed (for exercises)
- VSCode or any text editor installed
- GitHub account (free tier is fine)

## Learning Path

| Module | Topics | Time | Key Concepts |
|--------|--------|------|--------------|
| **01 - Introduction** | [What is Version Control](01-introduction-to-git.md) | 15 min | Version control fundamentals, Git mental model, setup |
| **02 - Basic Commands** | [Init, Add, Commit](02-basic-commands.md) | 15 min | Repository basics, staging, committing |
| **03 - Viewing History** | [Log & Diff](03-viewing-history.md) | 10 min | Reviewing commits, comparing changes |
| **04 - Git Ignore** | [Excluding Files](04-gitignore.md) | 8 min | .gitignore patterns, security, best practices |
| **05 - Undoing Changes** | [Restore, Revert, Amend](05-undoing-changes.md) | 12 min | Fixing mistakes, safe undo operations |
| **06 - Branching Basics** | [Creating Branches](06-branching-basics.md) | 10 min | What are branches, creating, switching |
| **07 - Merging & Conflicts** | [Combining Work](07-merging-and-conflicts.md) | 15 min | Merge strategies, conflict resolution |
| **08 - Remote Basics** | [Clone, Push, Pull](08-remote-basics.md) | 12 min | Working with GitHub, syncing code |
| **09 - GitHub Workflow** | [Pull Requests & Review](09-github-workflow.md) | 15 min | PRs, code review, GitHub Flow |
| **10 - Real World Git** | [Production Workflows](10-git-in-real-world.md) | 15 min | CI/CD, GitHub Actions, data engineering |
| **11 - VSCode Integration** | [IDE Tools](11-vscode-git-guide.md) | 5 min | Source Control panel, extensions |
| **12 - Hands-On Exercises** | [Calculator Project](12-exercises.md) | 20 min | Complete workflow with conflicts |

**Total Duration:** ~2.5 hours

## Quick Start

### 1. Install Git

**macOS:**
```bash
# Git comes with Xcode Command Line Tools
xcode-select --install

# Or install via Homebrew
brew install git
```

**Windows:**
```bash
# Download from git-scm.com
# Or use winget
winget install --id Git.Git -e --source winget
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt-get install git

# Fedora
sudo dnf install git
```

### 2. Configure Git

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### 3. Start Learning

Begin with [Module 01 - Introduction to Git](01-introduction-to-git.md) and work through the modules sequentially. Each lesson builds on the previous one.

## What You'll Learn

By the end of this module, you'll be able to:

- **Version control fundamentals**: Track changes, revert mistakes, understand project history
- **Daily Git operations**: Create commits, stage changes, write good commit messages
- **Branch management**: Create feature branches, merge code, resolve conflicts
- **Remote collaboration**: Push/pull code, create pull requests, conduct code reviews
- **Professional workflows**: Use GitHub Flow, integrate CI/CD, follow industry best practices
- **Data engineering context**: Version control SQL migrations, dbt projects, Airflow DAGs, pipeline configs

## Why Git Matters for Data Engineers

As a data engineer, you'll use Git to:

- **Version control SQL migrations** - Track database schema changes over time
- **Collaborate on dbt projects** - Share and review data transformation code
- **Manage Airflow DAGs** - Version control your data pipelines
- **Deploy infrastructure** - Track changes to Terraform, Docker configs, K8s manifests
- **Document changes** - Maintain a clear history of what changed and why
- **Enable CI/CD** - Automate testing and deployment of data pipelines

Git isn't just for application developers—it's a fundamental tool in modern data engineering.

## Learning Tips

1. **Practice with real projects** - Don't just read, actually use Git on your code
2. **Make mistakes safely** - Git is designed to be forgiving; experiment with confidence
3. **Commit early and often** - Small, frequent commits are better than large, infrequent ones
4. **Read commit messages** - Good commit messages tell the story of a project
5. **Use branches liberally** - Branches are cheap; create them for every feature or experiment
6. **Ask for code reviews** - Reviewing and being reviewed makes you a better engineer

## Git Philosophy

Git follows these key principles:

- **Distributed is better than centralized** - Every developer has a full copy of the history
- **Branches are lightweight** - Creating and switching branches should be instant
- **History matters** - Preserve a clear record of what changed and why
- **Trust but verify** - Code review before merging keeps quality high

## Common Git Workflows

This course focuses on **GitHub Flow**, a simple yet powerful workflow used by many teams:

1. Create a branch from `main`
2. Make changes and commit
3. Open a Pull Request
4. Code review and discussion
5. Merge to `main`
6. Deploy automatically

We'll also cover how this integrates with CI/CD pipelines in Module 05.

## Additional Resources

- [Official Git Documentation](https://git-scm.com/doc)
- [GitHub Docs](https://docs.github.com)
- [Oh Shit, Git!?!](https://ohshitgit.com/) - Common Git problems and solutions
- [Learn Git Branching](https://learngitbranching.js.org/) - Interactive tutorial
- [Conventional Commits](https://www.conventionalcommits.org/) - Commit message standard

## Course Format

Each lesson includes:

- **Core concepts** explained clearly with diagrams
- **Practical examples** you can run in your terminal
- **Best practices** from industry experience
- **Advanced notes** for deeper understanding
- **Real-world context** connecting to data engineering

## Getting Help

If you're stuck:

1. Check the [exercises](07-exercises.md) for hands-on practice
2. Review the [VSCode guide](06-vscode-git-guide.md) for UI-based alternatives
3. Read the "Advanced Notes" sections for deeper explanations
4. Ask questions—Git has a learning curve but it's worth it!

---

**Ready to begin?** Start with [01 - Introduction to Git](01-introduction-to-git.md)
