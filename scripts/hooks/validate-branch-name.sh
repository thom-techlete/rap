#!/usr/bin/env bash
# Validate branch names used locally and in GitHub Actions.

set -euo pipefail

if [[ -n "${GITHUB_HEAD_REF:-}" ]]; then
    branch_name="$GITHUB_HEAD_REF"
else
    branch_name="$(git rev-parse --abbrev-ref HEAD)"
fi

if [[ "$branch_name" == "HEAD" && -z "${GITHUB_HEAD_REF:-}" ]]; then
    echo "Skipping branch name validation (detached HEAD state)."
    exit 0
fi

case "$branch_name" in
    main|staging|master|prod|feature/*|bug/*|refactor/*|security/*|breaking/*|question/*|docs/*|chore/*)
        exit 0
        ;;
esac

cat >&2 <<EOF

Branch name validation failed for: "$branch_name"

Use one of these prefixes:
  feature/ bug/ refactor/ security/ breaking/ question/ docs/ chore/

Example: feature/add-login-page
EOF
exit 1
