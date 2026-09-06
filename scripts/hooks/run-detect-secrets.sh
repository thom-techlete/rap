#!/usr/bin/env bash
# Run detect-secrets with repository exclusions from pyproject.toml.

set -euo pipefail

usage() {
    cat <<'EOF'
Usage:
  scripts/hooks/run-detect-secrets.sh [--non-interactive]
  scripts/hooks/run-detect-secrets.sh --pre-commit [files ...]

Normal mode scans with .secret.baseline and reviews findings interactively.
Pre-commit mode checks supplied files without modifying the baseline.
EOF
}

mode="scan"
positional=()
while (($# > 0)); do
    case "$1" in
        --help|-h) usage; exit 0 ;;
        --non-interactive) mode="non-interactive"; shift ;;
        --pre-commit) mode="pre-commit"; shift ;;
        --) shift; positional+=("$@"); break ;;
        *) positional+=("$1"); shift ;;
    esac
done

exclude_regex="$(uv run python - <<'PY'
from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

try:
    with Path("pyproject.toml").open("rb") as config_file:
        config = tomllib.load(config_file)
except (OSError, tomllib.TOMLDecodeError) as exc:
    print(f"Error reading pyproject.toml: {exc}", file=sys.stderr)
    raise SystemExit(1) from exc

patterns = config.get("tool", {}).get("detect-secrets", {}).get("exclude_files", [])
if not isinstance(patterns, list) or not all(isinstance(pattern, str) for pattern in patterns):
    print("[tool.detect-secrets].exclude_files must be a list of strings", file=sys.stderr)
    raise SystemExit(1)

try:
    for pattern in patterns:
        re.compile(pattern)
except re.error as exc:
    print(f"Invalid detect-secrets exclude regex: {exc}", file=sys.stderr)
    raise SystemExit(1) from exc

print("|".join(f"(?:{pattern})" for pattern in patterns))
PY
)"

exclude_args=()
if [[ -n "$exclude_regex" ]]; then
    exclude_args=(--exclude-files "$exclude_regex")
fi

baseline_backup=""
progress_pid=""
cleanup() {
    if [[ -n "$progress_pid" ]]; then
        kill "$progress_pid" 2>/dev/null || true
        wait "$progress_pid" 2>/dev/null || true
    fi
    if [[ -n "$baseline_backup" ]]; then
        rm -f "$baseline_backup"
    fi
}
trap cleanup EXIT

if [[ "$mode" == "pre-commit" ]]; then
    if [[ ! -f .secret.baseline ]]; then
        echo "Missing .secret.baseline; create it with: uv run detect-secrets scan > .secret.baseline" >&2
        exit 1
    fi

    uv run detect-secrets-hook \
        --baseline .secret.baseline \
        "${exclude_args[@]}" \
        "${positional[@]}"
    exit $?
fi

if ((${#positional[@]} > 0)); then
    echo "Unexpected positional arguments in scan mode: ${positional[*]}" >&2
    usage >&2
    exit 2
fi

if [[ ! -f .secret.baseline ]]; then
    echo "Missing .secret.baseline." >&2
    echo "Create and review it with: uv run detect-secrets scan > .secret.baseline" >&2
    exit 2
fi

baseline_backup="$(mktemp)"
cp .secret.baseline "$baseline_backup"

if [[ "$mode" == "non-interactive" || ! -t 0 || ! -t 1 ]]; then
    uv run detect-secrets scan --baseline .secret.baseline "${exclude_args[@]}"
    echo "Secret scan complete. Interactive audit skipped."
    exit 0
fi

uv run detect-secrets scan --baseline .secret.baseline "${exclude_args[@]}"
uv run detect-secrets audit .secret.baseline
