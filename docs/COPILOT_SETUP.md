# GitHub Copilot Development Setup Guide

This guide provides GitHub Copilot with everything needed to quickly set up a complete development and test environment for the SV Rap 8 Event Presence Webapp.

## Quick Start (One Command)

```bash
./scripts/copilot-setup.sh
```

This script will:
- ✅ Start PostgreSQL and Redis using `docker/docker-compose-base.yml`
- ✅ Configure environment variables from `docker/.env`
- ✅ Set up Python virtual environment with all dependencies
- ✅ Run Django migrations on PostgreSQL database
- ✅ Start Celery worker and beat in background using Python
- ✅ Create development superuser account
- ✅ Verify all services are working

## What You Get

### Services Running
- **PostgreSQL** (Docker): `localhost:5432` - Primary database
- **Redis** (Docker): `localhost:6379` - Cache and Celery broker
- **Celery Worker**: Background task processing
- **Celery Beat**: Scheduled task management

### Environment Configuration
- Uses `docker/.env` for base configuration
- PostgreSQL database (NOT sqlite3) ✓
- All environment variables properly configured
- Development-friendly settings enabled

### Ready for Development
- Virtual environment: `venv/`
- Django superuser: `admin@svrap8.nl` / `admin123`
- All migrations applied
- Static files collected
- Background services running

## Manual Setup (Alternative)

If you prefer to set up manually or need to troubleshoot:

### 1. Prerequisites
```bash
# Check requirements
python3 --version  # Should be 3.12+
docker --version
docker compose version
```

### 2. Start Base Services
```bash
cd docker/
docker compose -f docker-compose-base.yml up -d
```

### 3. Python Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 4. Environment Variables
```bash
# Copy and modify docker/.env for local development
cp docker/.env .env
# Edit .env to use localhost instead of container names
```

### 5. Django Setup
```bash
cd web/
source ../.env  # Load environment variables
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser  # Create admin account
```

### 6. Background Services
```bash
# Start Celery worker
celery -A rap_web worker --loglevel=info --detach

# Start Celery beat
celery -A rap_web beat --loglevel=info --detach --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

## Development Workflow

### Starting Development Server
```bash
source venv/bin/activate
cd web/
python manage.py runserver
```
Then open: http://localhost:8000

### Running Tests
```bash
source venv/bin/activate
cd web/
python manage.py test
```

### Django Management
```bash
source venv/bin/activate
cd web/
python manage.py shell          # Django shell
python manage.py makemigrations # Create migrations
python manage.py migrate        # Apply migrations
```

### Monitoring Background Services
```bash
# View Celery logs
tail -f logs/celery-worker.log
tail -f logs/celery-beat.log

# Check if services are running
ps aux | grep celery
```

## Stopping Services

```bash
./scripts/copilot-stop.sh
```

This will:
- Stop Celery worker and beat processes
- Stop Docker containers (PostgreSQL + Redis)
- Clean up PID files

## Troubleshooting

### Common Issues

**PostgreSQL Connection Issues:**
```bash
# Check if PostgreSQL is running
docker compose -f docker/docker-compose-base.yml ps

# Check PostgreSQL logs
docker compose -f docker/docker-compose-base.yml logs db
```

**Celery Not Starting:**
```bash
# Check Redis connection
redis-cli -h localhost ping

# Manually start Celery for debugging
cd web/
celery -A rap_web worker --loglevel=debug
```

**Environment Variables:**
```bash
# Verify environment is loaded
cd web/
python manage.py shell -c "import os; print(os.environ.get('DATABASE_URL'))"
```

**Permission Issues:**
```bash
# Make scripts executable
chmod +x scripts/copilot-*.sh
```

### Reset Everything
```bash
# Stop all services
./scripts/copilot-stop.sh

# Remove virtual environment
rm -rf venv/

# Remove development database data (WARNING: loses data)
docker compose -f docker/docker-compose-base.yml down -v

# Start fresh
./scripts/copilot-setup.sh
```

## Key Features Verified

✅ **PostgreSQL Database**: Uses PostgreSQL as primary database (not sqlite3)  
✅ **Docker Services**: Uses `docker/docker-compose-base.yml` for PostgreSQL and Redis  
✅ **Environment Config**: Properly loads and uses `docker/.env` configuration  
✅ **Celery Background**: Runs Celery worker and beat using Python in background  
✅ **Django Ready**: All migrations applied, superuser created, static files collected  
✅ **Development Mode**: Debug enabled, console email backend, secure settings disabled  

## Project Structure

```
rap/
├── docker/
│   ├── docker-compose-base.yml  # PostgreSQL + Redis services
│   └── .env                     # Environment configuration
├── web/                         # Django application
│   ├── manage.py
│   ├── rap_web/                 # Main Django project
│   ├── users/                   # User management
│   ├── events/                  # Event management
│   ├── attendance/              # Attendance tracking
│   └── notifications/           # Notification system
├── scripts/
│   ├── copilot-setup.sh        # Full setup script
│   └── copilot-stop.sh         # Stop services script
├── venv/                       # Python virtual environment
└── logs/                       # Celery logs
```

This setup provides a complete development environment matching production requirements while being optimized for development and testing workflows.