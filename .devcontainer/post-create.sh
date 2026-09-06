#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${repo_root}"

echo "Installing locked Python dependencies with uv..."
uv sync --frozen --all-groups

echo "Applying Django migrations..."
uv run python web/manage.py migrate --noinput

if [[ -d .git ]]; then
  uv run pre-commit install --install-hooks
fi

echo "Devcontainer setup complete."
echo "Start Django with: uv run python web/manage.py runserver 0.0.0.0:8000"
