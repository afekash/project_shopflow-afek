#!/usr/bin/env bash
# init-project.sh
#
# Copies the capstone project scaffold into a target directory.
# Works in two scenarios:
#
#   1. Fresh start — target does not exist yet:
#        bash materials/project/init-project.sh ~/my-capstone
#
#   2. Already cloned an empty GitHub repo:
#        git clone https://github.com/you/my-capstone ~/my-capstone
#        bash materials/project/init-project.sh ~/my-capstone
#
# The script detects whether the target is an empty/new-clone directory and
# copies scaffold contents into it rather than failing.

set -euo pipefail

SCAFFOLD_DIR="$(cd "$(dirname "$0")/../../scaffold" && pwd)"
TARGET_DIR="${1:-}"

# ── Validate arguments ────────────────────────────────────────────────────────

if [[ -z "$TARGET_DIR" ]]; then
  echo "Usage: bash init-project.sh <target-directory>"
  echo "Example: bash init-project.sh ~/my-capstone"
  exit 1
fi

# ── Decide how to place the scaffold ─────────────────────────────────────────

if [[ ! -e "$TARGET_DIR" ]]; then
  # Target doesn't exist — create it by copying the scaffold directory.
  echo "Creating $TARGET_DIR from scaffold..."
  cp -r "$SCAFFOLD_DIR" "$TARGET_DIR"

elif [[ -d "$TARGET_DIR" ]]; then
  # Target already exists. Allow it only if it looks like an empty or
  # freshly-cloned repo (the only thing present may be a .git/ directory).
  non_git_files=$(ls -A "$TARGET_DIR" | grep -v '^\.git$' || true)
  if [[ -n "$non_git_files" ]]; then
    echo "Error: '$TARGET_DIR' already exists and is not empty."
    echo "Remove its contents first, or choose a different target directory."
    exit 1
  fi

  echo "Detected existing directory (freshly cloned repo). Copying scaffold contents into $TARGET_DIR..."
  # Copy everything including hidden files (.env.example, .gitignore, etc.)
  cp -r "$SCAFFOLD_DIR"/. "$TARGET_DIR/"

else
  echo "Error: '$TARGET_DIR' exists but is not a directory."
  exit 1
fi

# ── Set up .env ───────────────────────────────────────────────────────────────

if [[ -f "$TARGET_DIR/.env.example" && ! -f "$TARGET_DIR/.env" ]]; then
  cp "$TARGET_DIR/.env.example" "$TARGET_DIR/.env"
  echo "Created .env from .env.example — fill in your credentials."
fi

# ── Done ──────────────────────────────────────────────────────────────────────

echo ""
echo "Done! Your project is ready at: $TARGET_DIR"
echo ""
echo "Next steps:"
echo "  cd $TARGET_DIR"
echo "  git add . && git commit -m 'Initial scaffold'        # if using git"
echo "  docker compose up -d                                 # start all 4 databases"
echo "  uv sync --all-extras                                 # install Python dependencies"
echo "  uv run uvicorn ecommerce_pipeline.api.app:app --reload  # start the API"
echo ""
echo "Open http://localhost:8000/docs to see all available endpoints."
echo "Then open src/ecommerce_pipeline/db_access.py and start implementing!"
