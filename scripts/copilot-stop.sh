#!/usr/bin/env bash
set -euo pipefail

# GitHub Copilot Development Environment Stop Script
# Stops all services started by copilot-setup.sh

# Colors for output
GREEN='\033[0;32m'
CYAN='\033[1;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
RESET='\033[0m'

step()   { echo -e "${CYAN}👉 $1${RESET}"; }
success(){ echo -e "${GREEN}✅ $1${RESET}"; }
warn()   { echo -e "${YELLOW}⚠️ $1${RESET}"; }
error()  { echo -e "${RED}❌ $1${RESET}"; }
info()   { echo -e "${BLUE}ℹ️ $1${RESET}"; }

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCKER_DIR="$PROJECT_ROOT/docker"

cd "$PROJECT_ROOT"

echo -e "${BLUE}🛑 Stopping GitHub Copilot Development Environment${RESET}\n"

step "Stopping Celery processes..."
# Stop Celery worker
if [[ -f "logs/celery-worker.pid" ]]; then
    if kill -TERM "$(cat logs/celery-worker.pid)" 2>/dev/null; then
        success "Celery worker stopped."
    else
        warn "Celery worker PID file exists but process not found."
    fi
    rm -f logs/celery-worker.pid
else
    # Try to kill by process name as fallback
    if pkill -f "celery.*worker"; then
        success "Celery worker processes terminated."
    else
        info "No Celery worker processes found."
    fi
fi

# Stop Celery beat
if [[ -f "logs/celery-beat.pid" ]]; then
    if kill -TERM "$(cat logs/celery-beat.pid)" 2>/dev/null; then
        success "Celery beat stopped."
    else
        warn "Celery beat PID file exists but process not found."
    fi
    rm -f logs/celery-beat.pid
else
    # Try to kill by process name as fallback
    if pkill -f "celery.*beat"; then
        success "Celery beat processes terminated."
    else
        info "No Celery beat processes found."
    fi
fi

step "Stopping Docker services..."
cd "$DOCKER_DIR"
if docker compose -f docker-compose-base.yml down; then
    success "Docker services stopped."
else
    warn "Failed to stop Docker services or they were not running."
fi

cd "$PROJECT_ROOT"

echo -e "\n${GREEN}✅ Development environment stopped successfully!${RESET}"
echo -e "${BLUE}To restart: ./scripts/copilot-setup.sh${RESET}"