---
name: author-lessons
description: Conventions for creating, editing, or reviewing lesson files under materials/, or modifying myst.yml. Use when writing new lessons, editing existing content, reviewing lesson structure, or configuring the MyST site.
---

# Authoring Lessons

## One Topic Per File

Each `.md` file under `materials/` teaches **one focused learning topic**. Guideline: aim for **~250 lines**. Longer files are acceptable for end-to-end walkthroughs, exercises, or interface specs, but a file growing past 250 lines is a signal to check whether it covers more than one topic. Update the parent README or `myst.yml` TOC when splitting.

- Scope each file to one concept before writing
- Prefer many small, focused files over fewer large ones
- Exceptions require explicit justification (e.g., end-to-end walkthrough where splitting breaks narrative)

## File Format

Source files are MyST Markdown. Naming: `NN-topic-name.md` in numbered folders (`01-introduction/`).

### Kernelspec Frontmatter

Every `.md` file with at least one `{code-cell}` must declare at the top:

```yaml
---
kernelspec:
  name: python3
  display_name: Python 3
  language: python
---
```

Files without code cells do not need it.

### Executable Code Cells

All executable cells use `{code-cell} python`. Cell magics select the language:

| Magic | Use for |
|-------|---------|
| *(none)* | Pure Python |
| `%%bash` | Shell commands (docker, curl, pip, git, etc.) |
| `%%sql` | Raw SQL (requires jupysql setup cell and `DATABASE_URL`) |

Examples:

````
```{code-cell} python
%%bash
docker ps
```
````

````
```{code-cell} python
%%sql
SELECT * FROM orders LIMIT 5;
```
````

### Setup Cells for SQL

Lessons using `%%sql` need a hidden setup cell at the top:

````
```{code-cell} python
:tags: [remove-input]
%load_ext sql
```
````

Connection is automatic via `DATABASE_URL` (set in the lab's `compose.yml`).

### Non-Executable Blocks

Plain fenced blocks (` ```python `, ` ```bash `, ` ```sql `) are illustrative only -- not executed.

### When to Use %%bash vs %%sql

- **`%%sql`** -- Pure SQL: SELECT, WITH, INSERT, UPDATE, CREATE, ALTER, etc.
- **`%%bash`** -- Anything needing a shell: `psql -c`, heredocs, system commands
- **Transaction control** -- Always use `%%bash` with `psql` heredoc for explicit BEGIN/COMMIT/ROLLBACK. The `%%sql` magic wraps each cell in its own transaction.

### Running Commands on the DB Container

The workspace container is separate from the DB container. Use these patterns in `%%bash` cells:

**`pgdb` wrapper** (no inner single quotes):
````
```{code-cell} python
%%bash
pgdb 'pg_ctl status -D $PGDATA'
```
````

**`docker exec -i` with heredoc** (when script has inner single quotes):
````
```{code-cell} python
%%bash
docker exec -i -u postgres "$DB_CONTAINER" bash <<'PGDB'
FILEPATH=$(psql -A -t -c "SELECT pg_relation_filepath('my_table');")
ls -lh "$PGDATA/$FILEPATH"
PGDB
```
````

Never nest heredocs in `%%bash` cells. Always use `docker exec -i` (not without `-i`) when piping a heredoc.

## Lab Notes

At the top of lessons requiring a lab:

````
```{note}
This lesson requires the ORM lab. Run `make lab-orm` before starting.
```
````

## Reproducibility

- All examples must run on the workspace container (Linux-based)
- Prefer SQLite and stdlib for lessons that don't need a sidecar
- Code cells must be runnable in sequence from top to bottom
- Embed sample data in code or provide seed scripts

## Concept Reuse

`materials/core-concepts/` is a tool-agnostic reference library. Technology-specific lessons **must** link back when a concept appears:

```
> **Core Concept:** See [Trees for Storage](../../core-concepts/02-data-structures/02-trees-for-storage.md) for how B-trees work in general. PostgreSQL uses B-trees for indexes because it needs sorted access for range scans.
```

The callout must explain **why this technology chose this concept**.

### Highlight Tradeoff Differences

When the current technology made a different choice than another technology students have seen:

```
> MongoDB uses B-trees (WiredTiger), while Cassandra uses LSM-trees -- same problem (disk-based storage), different tradeoff (read-optimized vs write-optimized).
```

### README Concept Maps

Each technology module's `README.md` should include a concept map table showing which core-concepts appear and why.

### Don't Duplicate -- Reference

Core-concepts files own the generic explanation. Technology lessons explain only the technology-specific application and link out. If explaining B-trees from scratch instead of linking, refactor.

When creating new content:
- Check `materials/core-concepts/README.md` for the concept-to-technology matrix
- If introducing a concept not yet in `core-concepts/`, create the generic file first
- Update the matrix when adding new columns or rows

## myst.yml Conventions

### Schema Layout

`toc` and `jupyter` belong under `project`, not `site`:

```yaml
version: 1
project:
  jupyter:
    binder: false
    server:
      url: http://localhost:8888/
      token: ""
    kernelName: python3
  toc:
    - file: ...
site:
  template: book-theme
  projects:
    - path: .
      slug: <project-slug>   # required
```

### TOC Structure

- `toc` lives under `project.toc`, not `site.toc`
- Group related files under `title:` + `children:` (no `file:` = collapsible section header)
- Top-level module entries use `file:` (the README) with `children:` for sub-topics

### Nav URLs

`site.nav` entries must use real page paths (not `/`):

```yaml
nav:
  - title: Home
    url: /welcome
```

### Jupyter Config

Do **not** use a `thebe:` key inside `project.jupyter`. The correct keys are `binder`, `server`, `kernelName`, `lite`.
