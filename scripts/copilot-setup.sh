#!/usr/bin/env bash
set -euo pipefail

# GitHub Copilot Development Environment Setup Script
# This script sets up a complete development & test environment for the SV Rap 8 webapp
# - Uses docker/docker-compose-base.yml for PostgreSQL and Redis services
# - Configures environment to use docker/.env file
# - Starts Celery worker and beat in background using Python
# - Ensures PostgreSQL is used as the database (not sqlite3)

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
error()  { echo -e "${RED}❌ $1${RESET}"; exit 1; }
info()   { echo -e "${BLUE}ℹ️ $1${RESET}"; }
section(){
  echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
  echo -e "${BLUE}🔧 $1${RESET}"
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
}

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$PROJECT_ROOT/venv"
DOCKER_DIR="$PROJECT_ROOT/docker"
WEB_DIR="$PROJECT_ROOT/web"

# Change to project root
cd "$PROJECT_ROOT"

setup_copilot_environment() {
    section "GITHUB COPILOT DEVELOPMENT SETUP"
    info "Setting up development environment for SV Rap 8 Event Presence Webapp"
    
    section "PREREQUISITES CHECK"
    step "Checking required tools..."
    
    # Check Python
    command -v python3 >/dev/null || error "Python 3 is not installed. Please install Python 3.12+."
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    success "Python $PYTHON_VERSION found."
    
    # Check Docker
    command -v docker >/dev/null || error "Docker is not installed. Please install Docker."
    success "Docker found."
    
    # Check Docker Compose
    if ! docker compose version >/dev/null 2>&1; then
        error "Docker Compose is not available. Please install Docker Compose v2+."
    fi
    success "Docker Compose found."
    
    # Check if we're in the right directory
    if [[ ! -f "docker/docker-compose-base.yml" ]] || [[ ! -f "docker/.env" ]]; then
        error "Please run this script from the rap project root directory."
    fi
    success "Project structure verified."
    
    section "DOCKER SERVICES SETUP"
    step "Starting PostgreSQL and Redis services using docker-compose-base.yml..."
    
    # Stop any existing containers
    cd "$DOCKER_DIR"
    docker compose -f docker-compose-base.yml down --remove-orphans || true
    
    # Start base services (PostgreSQL + Redis)
    docker compose -f docker-compose-base.yml up -d
    
    # Wait for services to be ready
    step "Waiting for PostgreSQL to be ready..."
    timeout=60
    counter=0
    while ! docker compose -f docker-compose-base.yml exec -T db pg_isready >/dev/null 2>&1; do
        if [ $counter -ge $timeout ]; then
            error "PostgreSQL failed to start within $timeout seconds"
        fi
        echo -n "."
        sleep 1
        ((counter++))
    done
    success "PostgreSQL is ready."
    
    step "Waiting for Redis to be ready..."
    counter=0
    while ! docker compose -f docker-compose-base.yml exec -T redis redis-cli ping >/dev/null 2>&1; do
        if [ $counter -ge $timeout ]; then
            error "Redis failed to start within $timeout seconds"
        fi
        echo -n "."
        sleep 1
        ((counter++))
    done
    success "Redis is ready."
    
    cd "$PROJECT_ROOT"
    
    section "PYTHON ENVIRONMENT SETUP"
    step "Setting up Python virtual environment..."
    
    if [[ -d "$VENV_DIR" ]]; then
        warn "Virtual environment already exists. Removing and recreating..."
        rm -rf "$VENV_DIR"
    fi
    
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    success "Virtual environment created and activated."
    
    step "Upgrading pip..."
    # Skip pip upgrade if network issues occur  
    pip install --upgrade pip || warn "Pip upgrade failed, continuing with existing version"
    success "pip ready."
    
    step "Installing Python dependencies..."
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    success "Dependencies installed."
    
    section "ENVIRONMENT CONFIGURATION"
    step "Setting up environment variables from docker/.env..."
    
    # Copy docker env to project root for local development
    if [[ -f ".env" ]]; then
        warn "Backing up existing .env file..."
        mv .env .env.backup
    fi
    
    # Create development .env based on docker/.env but with localhost hosts
    cat > .env << 'EOF'
# Development environment variables for GitHub Copilot
# Based on docker/.env but configured for local development

# Django settings
DJANGO_SECRET_KEY=change_me_in_production_copilot_dev
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database configuration (PostgreSQL running in Docker)
POSTGRES_DB=rap_db
POSTGRES_USER=rap_user
POSTGRES_PASSWORD=rap_db_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
DATABASE_URL=postgres://rap_user:rap_db_password@localhost:5432/rap_db

# Redis configuration (running in Docker)
REDIS_URL=redis://localhost:6379/0

# Celery configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Email settings for development
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Security settings for development
SECURE_SSL_REDIRECT=False
SECURE_HSTS_SECONDS=0
CSRF_COOKIE_SECURE=False
SESSION_COOKIE_SECURE=False
EOF
    
    success "Environment variables configured for local development."
    
    section "DJANGO SETUP"
    cd "$WEB_DIR"
    
    # Export environment variables for Django commands
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
    
    step "Running Django migrations..."
    python manage.py migrate
    success "Database migrations completed."
    
    step "Collecting static files..."
    python manage.py collectstatic --noinput
    success "Static files collected."
    
    step "Creating superuser (if needed)..."
    # Check if superuser already exists
    if python manage.py shell -c "from users.models import Player; print('exists' if Player.objects.filter(is_superuser=True).exists() else 'none')" | grep -q "exists"; then
        info "Superuser already exists."
    else
        info "Creating development superuser..."
        info "Username: admin"
        info "Email: admin@svrap8.nl"
        info "Password: admin123"
        python manage.py shell -c "
from users.models import Player
if not Player.objects.filter(username='admin').exists():
    Player.objects.create_superuser(
        username='admin',
        email='admin@svrap8.nl',
        first_name='Admin',
        last_name='User',
        password='admin123'
    )
    print('Superuser created successfully.')
else:
    print('Superuser already exists.')
"
        success "Development superuser ready."
    fi
    
    cd "$PROJECT_ROOT"
    
    section "CELERY BACKGROUND SERVICES"
    step "Starting Celery worker in background..."
    
    # Create directory for background process logs
    mkdir -p logs
    
    # Kill any existing celery processes
    pkill -f "celery.*worker" || true
    pkill -f "celery.*beat" || true
    sleep 2
    
    # Start Celery worker in background
    cd "$WEB_DIR"
    source "$VENV_DIR/bin/activate"
    
    # Start Celery worker
    celery -A rap_web worker --loglevel=info --detach --pidfile="$PROJECT_ROOT/logs/celery-worker.pid" --logfile="$PROJECT_ROOT/logs/celery-worker.log"
    success "Celery worker started in background."
    
    # Start Celery beat scheduler
    celery -A rap_web beat --loglevel=info --detach --pidfile="$PROJECT_ROOT/logs/celery-beat.pid" --logfile="$PROJECT_ROOT/logs/celery-beat.log" --scheduler django_celery_beat.schedulers:DatabaseScheduler
    success "Celery beat scheduler started in background."
    
    cd "$PROJECT_ROOT"
    
    section "VERIFICATION"
    step "Verifying setup..."
    
    # Check database connection
    cd "$WEB_DIR"
    if python manage.py check --database default >/dev/null 2>&1; then
        success "Database connection verified."
    else
        warn "Database connection issue detected."
    fi
    
    # Check Celery worker
    if [[ -f "$PROJECT_ROOT/logs/celery-worker.pid" ]] && kill -0 "$(cat "$PROJECT_ROOT/logs/celery-worker.pid")" 2>/dev/null; then
        success "Celery worker is running."
    else
        warn "Celery worker may not be running properly."
    fi
    
    # Check Celery beat
    if [[ -f "$PROJECT_ROOT/logs/celery-beat.pid" ]] && kill -0 "$(cat "$PROJECT_ROOT/logs/celery-beat.pid")" 2>/dev/null; then
        success "Celery beat is running."
    else
        warn "Celery beat may not be running properly."
    fi
    
    cd "$PROJECT_ROOT"
    
    section "SETUP COMPLETE"
    echo -e "\n${GREEN}🎉 GITHUB COPILOT DEVELOPMENT ENVIRONMENT READY!${RESET}\n"
    
    info "Services running:"
    echo "  • PostgreSQL (Docker): localhost:5432"
    echo "  • Redis (Docker): localhost:6379"
    echo "  • Celery Worker: background process"
    echo "  • Celery Beat: background process"
    
    echo -e "\n${BLUE}Next steps:${RESET}"
    echo "  1. Activate virtual environment: source venv/bin/activate"
    echo "  2. Start Django development server: cd web && python manage.py runserver"
    echo "  3. Open browser: http://localhost:8000"
    echo "  4. Admin login: admin@svrap8.nl / admin123"
    
    echo -e "\n${BLUE}Useful commands:${RESET}"
    echo "  • Run tests: cd web && python manage.py test"
    echo "  • Django shell: cd web && python manage.py shell"
    echo "  • View logs: tail -f logs/celery-worker.log"
    echo "  • Stop services: ./scripts/copilot-stop.sh"
    
    echo -e "\n${YELLOW}Important:${RESET}"
    echo "  • Uses PostgreSQL database (not sqlite3) ✓"
    echo "  • Environment configured from docker/.env ✓"
    echo "  • Celery running in background ✓"
    echo "  • Ready for development and testing ✓"
}

# Cleanup function
cleanup() {
    if [[ $? -ne 0 ]]; then
        error "Setup failed! Check logs and try again."
    fi
}

trap cleanup EXIT

# Main execution
setup_copilot_environment

success "Setup completed successfully!"