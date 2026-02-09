# VSCode Git Integration

## Overview

VSCode has powerful built-in Git features that make version control faster and more visual. This quick reference covers the Source Control panel, inline diffs, extensions, and tips for using Git within your IDE.

**Duration:** ~5 minutes

## Source Control Panel

### Opening Source Control

```
Keyboard: Ctrl+Shift+G (Windows/Linux) or Cmd+Shift+G (Mac)
Menu: View → Source Control
Icon: Click the branch icon in the Activity Bar (left sidebar)
```

### Panel Overview

```
┌─────────────────────────────┐
│ SOURCE CONTROL              │
│                             │
│ Changes (3)                 │
│   M modified.py             │
│   A new_file.py             │
│   D deleted.py              │
│                             │
│ Staged Changes (0)          │
│                             │
│ Message: _______________    │
│                             │
│ [✓ Commit] [⟳ Sync]        │
└─────────────────────────────┘
```

## Basic Operations in VSCode

### Staging Files

**Stage one file:**
- Click `+` next to filename

**Stage all files:**
- Click `+` next to "Changes" header

**Unstage file:**
- Click `-` next to filename in "Staged Changes"

### Committing

1. Type commit message in text box
2. Click ✓ checkmark or press `Ctrl+Enter` / `Cmd+Enter`

**Tip:** Click the `...` menu for more options:
- Commit All
- Commit Staged
- Commit & Push
- Commit & Sync

### Viewing Changes

**See diff:**
- Click on modified file in Source Control panel
- Opens side-by-side diff view

**Inline diff:**
- Changes shown with colored gutters in editor
- Green = added lines
- Red = removed lines
- Blue = modified lines

### Discarding Changes

**Discard changes in file:**
- Click `↶` (curved arrow) next to filename

**Warning:** This is permanent!

### Switching Branches

**Bottom-left corner:**
- Click branch name
- Select branch from dropdown
- Or type to create new branch

**Quick command:**
```
Ctrl+Shift+P → "Git: Checkout to..."
```

## Git Timeline

### File History

**View commits for current file:**
1. Right-click file in Explorer
2. Select "Open Timeline"
3. See all commits that touched this file

**Timeline panel:**
- Shows when file changed
- Click commit to see diff
- Useful for "who changed this and when?"

## Inline Git Features

### Git Gutters

**Left gutter indicators:**
- **Green bar** - Added lines
- **Blue bar** - Modified lines
- **Red triangle** - Deleted lines

**Click gutter indicator:**
- Shows inline diff
- Options to revert or stage hunk

### Blame Annotations

**See who wrote each line:**
```
Right-click in editor → "Git: Toggle Blame Annotations"
```

Shows author and commit for each line inline.

**Or use GitLens** (see Extensions below).

## Git Graph Visualization

**Built-in graph:**
```
Ctrl+Shift+P → "Git: View History"
```

Shows branch structure visually (if Git Graph extension installed).

## Merge Conflicts in VSCode

### Conflict Resolution

When merge conflict occurs, VSCode shows:

```python
<<<<<<< Current Change
def process(data):
    return data.dropna()
=======
def process(data):
    return data.fillna(0)
>>>>>>> Incoming Change
```

**VSCode adds clickable options:**
- Accept Current Change
- Accept Incoming Change
- Accept Both Changes
- Compare Changes

**Much easier than manual editing!**

### Side-by-Side Conflict View

```
Ctrl+Shift+P → "Merge Conflict: Compare Current Conflict"
```

Opens 3-way merge view.

## Git Commands via Command Palette

### Quick Access

```
Ctrl+Shift+P (Windows/Linux) or Cmd+Shift+P (Mac)
Type "Git: " to see all Git commands
```

**Useful commands:**
- `Git: Pull`
- `Git: Push`
- `Git: Fetch`
- `Git: Create Branch`
- `Git: Merge Branch`
- `Git: Stash`
- `Git: Undo Last Commit`

## Integrated Terminal

### Run Git Commands

```
Terminal → New Terminal (Ctrl+`)
```

Use any Git command:

```bash
git log --oneline --graph
git diff main..feature
git rebase -i HEAD~3
```

**Pro tip:** Terminal shares VSCode's context, so relative paths work.

## Recommended Extensions

### 1. GitLens

**Most popular Git extension**

**Features:**
- Inline blame (see who wrote each line)
- Commit search
- File history
- Compare branches
- Rich hovers with commit info

**Install:**
```
Extensions (Ctrl+Shift+X) → Search "GitLens"
```

**Usage:**
- Hover over any line → see blame
- Click commit hash → see details
- File history in sidebar

### 2. Git Graph

**Visual branch viewer**

**Features:**
- Graph of all branches and commits
- Click commit to see details
- Merge, rebase, cherry-pick from UI
- Beautiful visualization

**Install:**
```
Extensions → Search "Git Graph"
```

**Usage:**
```
Ctrl+Shift+P → "Git Graph: View Git Graph"
```

### 3. Git History

**File and line history**

**Features:**
- View history of file
- Compare commits
- View commit details

**Usage:**
- Right-click file → "Git: View File History"

### 4. GitHub Pull Requests

**Manage PRs from VSCode**

**Features:**
- View PRs
- Create PRs
- Review code
- Approve/comment
- Merge PRs

**Install:**
```
Extensions → Search "GitHub Pull Requests and Issues"
```

## Settings to Tweak

### Useful Git Settings

```json
// settings.json (Ctrl+,)
{
  // Auto-fetch from remote every 3 minutes
  "git.autofetch": true,
  "git.autofetchPeriod": 180,
  
  // Confirm before pushing
  "git.confirmSync": true,
  
  // Show inline blame
  "gitlens.currentLine.enabled": true,
  
  // Enable Git Graph on startup
  "git.enableSmartCommit": true,
  
  // Automatically stage all changes on commit
  "git.enableSmartCommit": true,
  
  // Always show staged changes
  "git.showPushSuccessNotification": true
}
```

### GitLens Configuration

```json
{
  // Show blame on current line
  "gitlens.currentLine.enabled": true,
  
  // Code lens at top of file
  "gitlens.codeLens.enabled": true,
  
  // File history in side bar
  "gitlens.views.fileHistory.enabled": true
}
```

## Keyboard Shortcuts

### Default Git Shortcuts

| Action | Windows/Linux | Mac |
|--------|---------------|-----|
| Source Control | `Ctrl+Shift+G` | `Cmd+Shift+G` |
| Commit | `Ctrl+Enter` | `Cmd+Enter` |
| View Changes | Click file | Click file |
| Next Change | `F7` | `F7` |
| Previous Change | `Shift+F7` | `Shift+F7` |
| Command Palette | `Ctrl+Shift+P` | `Cmd+Shift+P` |

### Custom Shortcuts (Optional)

```json
// keybindings.json
[
  {
    "key": "ctrl+shift+a",
    "command": "git.stageAll"
  },
  {
    "key": "ctrl+shift+u",
    "command": "git.unstageAll"
  }
]
```

## Tips & Tricks

### 1. Stage Hunks (Partial Staging)

Don't want to stage entire file?

1. Open file diff
2. Right-click changed section
3. Select "Stage Selected Ranges"

Stages only that change!

### 2. Stashing from UI

```
Source Control menu (...)
→ Stash → Stash (Include Untracked)
```

**Retrieve stash:**
```
Source Control menu → Stash → Pop Latest Stash
```

### 3. Branch Comparison

```
Ctrl+Shift+P → "Git: Compare References"
Select two branches to compare
```

### 4. Quick Commit

```
Stage files → Type message → Ctrl+Enter
```

Commit in 3 seconds!

### 5. Blame Without Extension

```
Right-click in editor
→ "Toggle Blame Annotations"
```

Built-in blame (basic).

## Common Workflows

### Daily Development

```
1. Open VSCode
2. Click Source Control (Ctrl+Shift+G)
3. Pull latest (... menu → Pull)
4. Create branch (bottom-left → "Create Branch")
5. Make changes
6. Stage files (click +)
7. Write commit message
8. Commit (✓ or Ctrl+Enter)
9. Push (... menu → Push)
```

### Reviewing PR

With GitHub Pull Requests extension:

```
1. GitHub icon in Activity Bar
2. Select PR
3. View changes
4. Add comments
5. Approve or request changes
```

### Resolving Conflicts

```
1. Attempt merge (conflict occurs)
2. VSCode highlights conflicts
3. Click "Accept Current/Incoming/Both"
4. Save file
5. Stage resolved file
6. Commit
```

## Key Takeaways

1. **Source Control panel** - Visual Git interface
2. **Inline diffs** - See changes in editor
3. **GitLens** - Most popular Git extension
4. **Git Graph** - Visualize branches
5. **Conflict resolution** - Click to resolve
6. **Integrated terminal** - Full Git power
7. **Command palette** - All Git commands

## Best Practices

1. **Use visual diffs** - Easier than terminal
2. **Install GitLens** - Essential for blame and history
3. **Stage hunks** - Commit precisely
4. **Review diffs before commit** - Catch mistakes
5. **Use integrated terminal** - For advanced commands

## Practice Exercises

1. **Stage and commit** - Use Source Control panel only
2. **View file history** - Use Git Timeline
3. **Resolve a conflict** - Use visual conflict resolver
4. **Install GitLens** - Explore inline blame
5. **Create branch** - Use bottom-left switcher

## What's Next?

You now know how to use Git through VSCode. The final lesson provides **hands-on exercises**—a complete project to practice everything you've learned.

---

**Navigation:**
- **Previous:** [10 - Git in the Real World](10-git-in-real-world.md)
- **Next:** [12 - Exercises](12-exercises.md)
- **Home:** [Git Course Overview](README.md)
