#!/usr/bin/env bash
set -e

# Activate your local venv (adjust path if needed)
source venv/bin/activate

# Synchronize the development environment from the committed lockfile
uv sync --locked --extra dev --no-install-project

# Run pytest with coverage and beartype runtime checks
pytest --cov --cov-fail-under=80 --beartype-packages=utils,example
