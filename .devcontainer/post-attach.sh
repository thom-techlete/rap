#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${repo_root}"

if [[ "${DEVCONTAINER_CI:-false}" == "true" ]]; then
  echo "Skipping development service startup in CI."
  exit 0
fi

bash .devcontainer/dev-services.sh restart
