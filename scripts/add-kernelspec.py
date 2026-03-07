#!/usr/bin/env python3
"""Add kernelspec frontmatter to all MyST Markdown files that contain {code-cell} blocks."""

import re
from pathlib import Path

KERNELSPEC = """\
---
kernelspec:
  name: python3
  language: python
  display_name: Python 3
---"""

FRONTMATTER_RE = re.compile(r"^---\n.*?\n---\n", re.DOTALL)
CODE_CELL_RE = re.compile(r"```\{code-cell\}")
KERNELSPEC_RE = re.compile(r"kernelspec:")

materials = Path(__file__).parent.parent / "materials"
files = list(materials.rglob("*.md"))

added, skipped, already = [], [], []

for path in sorted(files):
    content = path.read_text(encoding="utf-8")

    if not CODE_CELL_RE.search(content):
        continue

    match = FRONTMATTER_RE.match(content)

    if match:
        frontmatter = match.group(0)
        if KERNELSPEC_RE.search(frontmatter):
            already.append(path)
            continue
        # Insert kernelspec into existing frontmatter (before closing ---)
        new_frontmatter = frontmatter.rstrip()[:-3] + "kernelspec:\n  name: python3\n  language: python\n  display_name: Python 3\n---\n"
        new_content = new_frontmatter + content[match.end():]
    else:
        new_content = KERNELSPEC + "\n\n" + content

    path.write_text(new_content, encoding="utf-8")
    added.append(path)

print(f"Added kernelspec to {len(added)} files:")
for p in added:
    print(f"  + {p.relative_to(materials.parent)}")

if already:
    print(f"\nAlready had kernelspec ({len(already)} files):")
    for p in already:
        print(f"  = {p.relative_to(materials.parent)}")

if skipped:
    print(f"\nSkipped ({len(skipped)} files):")
    for p in skipped:
        print(f"  - {p.relative_to(materials.parent)}")
