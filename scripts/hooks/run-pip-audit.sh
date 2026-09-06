#!/usr/bin/env bash
# Build pip-audit ignore arguments from pyproject.toml [tool.pip-audit].

set -euo pipefail

tmp_audit_json=$(mktemp)
trap 'rm -f "$tmp_audit_json"' EXIT

python3 - "$tmp_audit_json" <<'PY'
from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path

config_path = Path("pyproject.toml")
audit_path = Path(sys.argv[1])

with config_path.open("rb") as config_file:
    config = tomllib.load(config_file)

ignore_list = config.get("tool", {}).get("pip-audit", {}).get("ignore", [])
if ignore_list:
    result = subprocess.run(
        [
            "uv", "run", "pip-audit", "--format", "json", "--aliases", "on",
            "--progress-spinner", "off", "--output", str(audit_path), ".",
        ],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode not in (0, 1):
        print(result.stderr, file=sys.stderr, end="")
        raise SystemExit(result.returncode)

    audit_data = json.loads(audit_path.read_text(encoding="utf-8"))
    active_ids: set[str] = set()
    for dependency in audit_data.get("dependencies", []):
        for vulnerability in dependency.get("vulns", []):
            if vulnerability.get("id"):
                active_ids.add(vulnerability["id"])
            active_ids.update(
                alias for alias in vulnerability.get("aliases", []) if alias
            )

    stale_ignores = [vuln_id for vuln_id in ignore_list if vuln_id not in active_ids]
    if stale_ignores:
        print(
            "Stale pip-audit ignore entries in pyproject.toml: "
            + ", ".join(stale_ignores),
            file=sys.stderr,
        )
        raise SystemExit(1)
PY

ignore_args=()
while IFS= read -r ignore_id; do
    ignore_args+=("--ignore-vuln" "$ignore_id")
done < <(
    python3 <<'PY'
import tomllib

with open("pyproject.toml", "rb") as config_file:
    config = tomllib.load(config_file)

for ignore_id in config.get("tool", {}).get("pip-audit", {}).get("ignore", []):
    print(ignore_id)
PY
)

uv run pip-audit "${ignore_args[@]}" "$@"
