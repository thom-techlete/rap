#!/usr/bin/env bash
set -euo pipefail

if git diff --cached --name-only | grep -Eq '^(pyproject\.toml|uv\.lock)$'; then
  command -v uv >/dev/null || {
    echo "ERROR: uv is required to verify uv.lock."
    exit 1
  }
  uv lock --check
fi
