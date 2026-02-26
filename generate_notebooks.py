"""Generate Jupyter notebooks from markdown source files."""

import argparse
import subprocess
from pathlib import Path


def find_md_files(directory: Path) -> list[Path]:
    """Return all lesson markdown files with Python code blocks under a directory."""
    return [
        f for f in directory.glob("**/*.md")
        if f.name.lower() != "readme.md"
        and ".ipynb_checkpoints" not in str(f)
        and "```python" in f.read_text(encoding="utf-8")
    ]


def convert(md_file: Path) -> None:
    subprocess.run(
        ["jupytext", "--to", "notebook", "--set-kernel", "python3", str(md_file)],
        check=True,
        capture_output=True,
    )


def main():
    project_root = Path(__file__).parent

    parser = argparse.ArgumentParser(
        description="Convert markdown lesson files to Jupyter notebooks."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-f", "--file",
        metavar="FILE",
        help="Relative path (from repo root) to a specific .md file to convert.",
    )
    group.add_argument(
        "-d", "--dir",
        metavar="DIR",
        default="materials",
        help="Relative path (from repo root) to a directory; all matching .md files "
             "inside it are converted recursively. (default: materials)",
    )
    args = parser.parse_args()

    if args.file:
        target = project_root / args.file
        if not target.exists():
            print(f"Error: '{args.file}' does not exist.")
            return
        if target.suffix.lower() != ".md":
            print(f"Error: '{args.file}' is not a markdown file.")
            return
        md_files = [target]
    else:
        target_dir = project_root / args.dir
        if not target_dir.is_dir():
            print(f"Error: '{args.dir}' is not a directory.")
            return
        md_files = find_md_files(target_dir)

    if not md_files:
        print("No markdown files found to convert.")
        return

    print(f"Generating {len(md_files)} notebook(s)...")
    for md_file in sorted(md_files):
        rel_path = md_file.relative_to(project_root)
        print(f"  → {rel_path}")
        convert(md_file)

    print("Done! Notebooks are ready to use.")


if __name__ == "__main__":
    main()
