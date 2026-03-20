# Data Engineering Course

Local self-served teaching platform for data engineering, DBA, and DevOps lessons.

## Stack

- **Source**: MyST Markdown (`.md` files under `materials/`)
- **Student UI**: MyST docs site (port 3000) with executable `{code-cell}` blocks via Thebe
- **Execution**: Local Jupyter server (port 8888)
- **Labs**: Docker Compose environments under `labs/`, one per topic
- **Capstone**: Scaffold in `scaffold/` (FastAPI + PostgreSQL/MongoDB/Redis/Neo4j)
- **Package manager**: `uv`
- **Python**: 3.13

## Key Commands

```
make docs              # Start workspace only (MyST + Jupyter)
make lab-<name>        # Start workspace + lab services (orm, sql, nosql, replica-set, sharded, redis, neo4j, distributed, web, etc.)
make down              # Stop running lab
make reset             # Stop + remove all containers and volumes
make shell             # Bash into workspace container
make sql-restore       # Restore MSSQL demo databases (after lab-sql)
make convert FILE=path # Export MyST lesson to py:percent notebook
```

## Architecture

```
materials/             # Course content (MyST markdown with executable code cells)
  core-concepts/       # Shared building blocks referenced by all technology modules
  git/, sql/, python/, nosql/, docker/, project/
labs/                  # Docker Compose lab environments
  base/                # Shared workspace container (Dockerfile, compose.yml, init.sh)
  <name>/              # Per-lab overlay (compose.yml, pyproject.toml, optional init.sh)
scaffold/              # Capstone project (ShopFlow e-commerce pipeline)
```

## Content Principles

1. **Depth over breadth** -- advanced concepts alongside basics
2. **Practical examples required** -- runnable code with realistic data
3. **Big data perspective** -- how concepts scale, when they break down
4. **Best practices** -- industry patterns, anti-patterns, performance considerations
5. **Progressive complexity** -- build up within each topic
6. **Concept reuse** -- `core-concepts/` is a shared library; technology lessons link back to it

## Authoring & Lab Skills

When working on lesson files (`materials/**/*.md`) or `myst.yml`, reference:
- @.claude/skills/author-lessons/SKILL.md for content format, structure, and conventions

When working on lab environments (`labs/`, Makefile), reference:
- @.claude/skills/manage-labs/SKILL.md for Docker Compose architecture and conventions

## Dev Dependencies

Root `pyproject.toml` has dev tools only: `pytest`, `ruff`. Per-lab Python deps are in `labs/<name>/pyproject.toml`.

## Self-Documentation

When you establish a new convention or resolve an ambiguity that should persist, suggest documenting it. Use `/document-learnings` to route updates to the correct file (CLAUDE.md, skill, or memory).
