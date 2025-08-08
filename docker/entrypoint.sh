#!/bin/bash

# Docker entrypoint script for RAP Web Application
# This script runs database migrations, collects static files, and starts the application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Wait for database to be ready
wait_for_db() {
    log_info "Waiting for database to be ready..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if python manage.py check --database default >/dev/null 2>&1; then
            log_success "Database is ready!"
            return 0
        fi
        
        log_info "Database not ready yet (attempt $attempt/$max_attempts). Waiting 2 seconds..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    log_error "Database failed to become ready after $max_attempts attempts"
    exit 1
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    if python manage.py migrate --noinput; then
        log_success "Database migrations completed successfully"
    else
        log_error "Database migrations failed"
        exit 1
    fi
}

# Collect static files
collect_static() {
    log_info "Collecting static files..."
    
    if python manage.py collectstatic --noinput --clear; then
        log_success "Static files collected successfully"
    else
        log_error "Static file collection failed"
        exit 1
    fi
}

# Create superuser if it doesn't exist (for development/first run)
create_superuser_if_needed() {
    if [ "$CREATE_SUPERUSER" = "true" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
        log_info "Creating superuser..."
        python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='$DJANGO_SUPERUSER_USERNAME').exists():
    User.objects.create_superuser('$DJANGO_SUPERUSER_USERNAME', '$DJANGO_SUPERUSER_EMAIL', '$DJANGO_SUPERUSER_PASSWORD')
    print('Superuser created successfully')
else:
    print('Superuser already exists')
EOF
        log_success "Superuser check completed"
    fi
}

# Load initial data if specified
load_initial_data() {
    if [ "$LOAD_INITIAL_DATA" = "true" ]; then
        log_info "Loading initial data..."
        
        # Load fixtures if they exist
        for fixture in fixtures/*.json; do
            if [ -f "$fixture" ]; then
                log_info "Loading fixture: $fixture"
                python manage.py loaddata "$fixture"
            fi
        done
        
        log_success "Initial data loading completed"
    fi
}

# Clear cache if Redis is available
clear_cache() {
    if [ "$CLEAR_CACHE_ON_START" = "true" ]; then
        log_info "Clearing application cache..."
        python manage.py shell << 'EOF'
try:
    from django.core.cache import cache
    cache.clear()
    print("Cache cleared successfully")
except Exception as e:
    print(f"Cache clear failed: {e}")
EOF
    fi
}

# Validate Django configuration
validate_django() {
    log_info "Validating Django configuration..."
    
    if python manage.py check --deploy; then
        log_success "Django configuration is valid"
    else
        log_error "Django configuration validation failed"
        exit 1
    fi
}

# Main entrypoint logic
main() {
    log_info "Starting RAP Web Application initialization..."
    
    # Change to the app directory
    cd /app
    
    # Wait for database
    wait_for_db
    
    # Run migrations
    run_migrations
    
    # Collect static files
    collect_static
    
    # Validate Django configuration
    validate_django
    
    # Optional: Create superuser
    create_superuser_if_needed
    
    # Optional: Load initial data
    load_initial_data
    
    # Optional: Clear cache
    clear_cache
    
    log_success "Application initialization completed successfully!"
    
    # Execute the main command
    log_info "Starting application server..."
    exec "$@"
}

# Handle different commands
case "$1" in
    "gunicorn")
        # Production server
        main gunicorn --bind 0.0.0.0:8000 --workers 3 --worker-class gevent --worker-connections 1000 --max-requests 1000 --max-requests-jitter 50 --timeout 120 --keep-alive 2 --preload --access-logfile - --error-logfile - rap_web.wsgi:application
        ;;
    "runserver")
        # Development server
        main python manage.py runserver 0.0.0.0:8000
        ;;
    "celery-worker")
        # Celery worker
        wait_for_db
        log_info "Starting Celery worker..."
        exec celery -A rap_web worker --loglevel=info --concurrency=2
        ;;
    "celery-beat")
        # Celery beat scheduler
        wait_for_db
        log_info "Starting Celery beat scheduler..."
        exec celery -A rap_web beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
        ;;
    "bash" | "sh")
        # Shell access
        exec "$@"
        ;;
    "manage")
        # Django management command
        wait_for_db
        shift
        exec python manage.py "$@"
        ;;
    *)
        # Default: run the provided command
        main "$@"
        ;;
esac
