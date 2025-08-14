# GitHub Copilot Environment Setup

This document explains how the GitHub Copilot coding agent environment is configured for the SV Rap 8 project.

## Setup Workflow Location

The environment setup is defined in `.github/workflows/copilot-setup-steps.yml`. This workflow:

1. Sets up a complete Django development environment
2. Installs all Python dependencies
3. Configures PostgreSQL and Redis services
4. Runs database migrations
5. Performs health checks
6. Verifies the development environment

## Environment Variables

The Copilot environment automatically configures these key variables:

```bash
# Database
DATABASE_URL=postgres://postgres:postgres@localhost:5432/rap_web
POSTGRES_DB=rap_web
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Redis/Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Django
DJANGO_SECRET_KEY=copilot-development-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
```

## Available Services

When Copilot starts working, it has access to:

- **PostgreSQL 17**: Database server on port 5432
- **Redis 7**: Cache and message broker on port 6379
- **Python 3.12**: With all project dependencies installed
- **Django**: Fully migrated and ready to run
- **Celery**: Worker and beat configurations verified

## Development Commands

The environment is ready for these common development tasks:

```bash
# Django development
cd web && python manage.py runserver
cd web && python manage.py shell
cd web && python manage.py test

# Database operations
cd web && python manage.py migrate
cd web && python manage.py makemigrations

# Celery operations
cd web && celery -A rap_web worker --loglevel=info
cd web && celery -A rap_web beat --loglevel=info
```

## Project Context

The environment provides Copilot with full context about:

- Django apps: users, events, attendance, notifications
- Models and relationships between entities
- Dutch language UI requirements
- Football/sports domain context
- Email notification system with Brevo integration
- Security configurations and best practices

## Testing the Setup

The setup workflow includes verification steps that:

- Check Django configuration validity
- Verify database connectivity
- Test static file collection
- Validate Celery configuration
- Confirm the project structure

This ensures Copilot has a fully functional development environment ready for any coding tasks.
