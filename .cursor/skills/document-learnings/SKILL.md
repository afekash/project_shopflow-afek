---
name: document-learnings
description: Document new conventions, patterns, and workflow knowledge into the correct cursor rule or skill file. Use when the agent has established a new convention, resolved an ambiguity, discovered a constraint, or the user asks to capture learnings from the current session.
---

# Document Learnings

Persist session knowledge into `.cursor/rules/` (conventions/constraints) or `.cursor/skills/` (workflows/procedures) so future sessions benefit.

## When to Use

- You established a new convention or pattern worth reusing
- You resolved an ambiguity that would trip up future agents
- You discovered a constraint (tool limitation, project quirk, breaking edge case)
- The user explicitly asks to document learnings

## Step 1 — Identify Learnings

Review the session and list each discrete piece of knowledge. For each, write:

- **What**: one-sentence description
- **Type**: `rule` (convention/constraint tied to files) or `skill` (multi-step workflow/procedure)
- **Scope**: which files it applies to (glob) or which task triggers it

Skip anything that is:
- A one-off decision with no future relevance
- Already documented in an existing rule or skill
- Common knowledge the agent would already know

## Step 2 — Build an Index of Existing Files

Scan the workspace to understand what already exists:

1. Read frontmatter of every `.cursor/rules/*.mdc` — collect `{filename, description, globs, alwaysApply}`
2. Read frontmatter of every `.cursor/skills/*/SKILL.md` — collect `{name, description}`

Present the index to yourself before routing.

## Step 3 — Route Each Learning

For each learning, decide where it belongs:

```
Is it a convention/constraint tied to file types?
  YES → Rule
    Does an existing rule's description + globs cover this scope?
      YES → Append to that rule
      NO  → Propose a new .mdc file
  NO → Is it a multi-step workflow or procedural knowledge?
    YES → Skill
      Does an existing skill's description cover this task?
        YES → Append to that skill
        NO  → Propose a new skill directory
    NO → Skip (not worth persisting)
```

### Single Responsibility Check

Before appending, verify:
- The target file's description still accurately covers the new content
- The new content doesn't introduce a **second concern** into the file
- If it does, propose a new file instead of bloating an existing one

### Size Limits

- Rules: keep under **50 lines** of content (excluding frontmatter)
- Skills: keep SKILL.md under **500 lines**
- If a file would exceed the limit after appending, split into a new focused file

## Step 4 — Propose Changes

For each update, show the user:

1. **Target file** (existing path or proposed new path)
2. **What will be added** (the exact lines)
3. **Why this file** (one sentence on how it matches the scope)

If proposing a **new rule file**, include the full frontmatter:

```yaml
---
description: <what this rule covers>
globs: <file patterns>
alwaysApply: false
---
```

If proposing a **new skill**, include the directory name and SKILL.md frontmatter:

```yaml
---
name: <skill-name>
description: <what and when>
---
```

## Step 5 — Apply After Approval

Only write changes after the user confirms. When writing:

- Append new sections at the end of the file (before any closing checklist if one exists)
- Use the same heading level and style as the rest of the file
- Do not rewrite existing content unless correcting a conflict
- Do not add redundant comments explaining the change

## Naming Conventions

| Type | Pattern | Examples |
|------|---------|----------|
| Rule | `kebab-case.mdc` matching the concern | `content-format.mdc`, `docker-conventions.mdc` |
| Skill | `kebab-case/SKILL.md` matching the task | `document-learnings/`, `plan-course-materials/` |

## Examples

**Learning**: "MyST admonition directives must use `{note}`, `{warning}`, `{tip}` — not `:::note` syntax"
→ **Route**: Append to `content-format.mdc` (globs `materials/**/*.md`, already covers MyST format)

**Learning**: "When restoring a SQL Server `.bak` file in a container, the logical file names must be discovered with `RESTORE FILELISTONLY` first"
→ **Route**: Append to `lab-environment.mdc` (globs `labs/**,Makefile`, covers lab setup procedures)

**Learning**: "A new multi-step process for setting up Redis labs was established"
→ **Route**: New skill if complex enough, or append to `lab-environment.mdc` if it's just a convention
