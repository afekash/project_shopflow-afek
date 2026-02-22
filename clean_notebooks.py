"""Remove all generated Jupyter notebooks from the materials directory."""

from pathlib import Path


def main():
    project_root = Path(__file__).parent
    materials_dir = project_root / "materials"

    notebooks = [
        f for f in materials_dir.glob("**/*.ipynb")
        if ".ipynb_checkpoints" not in str(f)
    ]

    if not notebooks:
        print("No notebooks found to remove.")
        return

    print(f"Removing {len(notebooks)} notebooks...")

    for notebook in sorted(notebooks):
        rel_path = notebook.relative_to(project_root)
        print(f"  → {rel_path}")
        notebook.unlink()

    print("Done!")


if __name__ == "__main__":
    main()
