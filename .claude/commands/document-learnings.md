Review the current session and persist valuable knowledge for future sessions.

## Step 1 -- Identify Learnings

List each discrete piece of knowledge from this session. For each:

- **What**: one-sentence description
- **Type**: `claude-md` (project-wide convention) | `skill` (domain-specific pattern) | `memory` (user preference or project context) | `skip`
- **Scope**: which files or tasks it applies to

Skip anything that is:
- A one-off decision with no future relevance
- Already documented in CLAUDE.md, a skill, or memory
- Common knowledge that doesn't need explicit documentation

## Step 2 -- Route Each Learning

```
Is it a project-wide convention or constraint?
  YES -> Propose update to CLAUDE.md
  NO -> Is it specific to lesson authoring or lab environments?
    YES -> Propose update to the relevant skill (author-lessons or manage-labs)
    NO -> Is it a user preference, project context, or reference?
      YES -> Save as memory (use the memory system)
      NO -> Skip
```

### Before Updating

- Check that the target file's scope still covers the new content
- Verify the new content doesn't introduce a second concern into a focused file
- If CLAUDE.md would exceed ~80 lines, move conditional content to a skill instead

## Step 3 -- Propose Changes

For each update, show:

1. **Target**: file path or memory type
2. **Content**: the exact lines to add
3. **Rationale**: one sentence on why this belongs here

## Step 4 -- Apply After Approval

Only write changes after user confirms. When writing:
- Append new content in the appropriate section
- Match existing style and heading levels
- Do not rewrite existing content unless correcting a conflict

$ARGUMENTS
