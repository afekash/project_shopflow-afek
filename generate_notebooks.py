"""Generate Jupyter notebooks from markdown source files."""

import subprocess
from pathlib import Path


def main():
    """Convert all lesson markdown files to Jupyter notebooks."""
    project_root = Path(__file__).parent
    materials_dir = project_root / "materials"

    # Find all .md files in materials/python/ (excluding README files and checkpoints)
    md_files = [
        f for f in materials_dir.glob("python/**/*.md")
        if f.name.lower() != "readme.md" and ".ipynb_checkpoints" not in str(f)
    ]

    if not md_files:
        print("No markdown files found to convert.")
        return

    print(f"Generating {len(md_files)} notebooks...")

    for md_file in sorted(md_files):
        rel_path = md_file.relative_to(project_root)
        print(f"  → {rel_path}")
        subprocess.run(
            ["jupytext", "--to", "notebook", str(md_file)],
            check=True,
            capture_output=True,
        )

    print("Done! Notebooks are ready to use.")


if __name__ == "__main__":
    main()
