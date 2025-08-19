# GitHub Copilot Custom Instructions for SV Rap 8 Event Presence Webapp

## Project Overview
This repository contains a Django-based web application for managing event presence for the football team SV Rap 8. The app allows team members to mark attendance for events, and admins to manage events and users. The default UI language is Dutch. The stack includes Django, PostgreSQL, Celery, Redis, Nginx, and Docker Compose.

## Technology Stack & Dependencies
- **Backend**: Django 5.2.5, Django REST Framework
- **Database**: PostgreSQL 17 with psycopg2-binary
- **Task Queue**: Celery 5.5.3 with Redis 6.4.0 as broker
- **Web Server**: Gunicorn (production), Django dev server (development)
- **Reverse Proxy**: Nginx (production)
- **Containerization**: Docker & Docker Compose
- **Email**: Django-anymail with Brevo SMTP integration
- **Security**: django-axes, django-ratelimit, django-csp, django-cors-headers
- **Static Files**: WhiteNoise for static file serving
- **Media Handling**: Pillow for image processing

## Project Structure
```
/web/                   # Main Django project directory
├── manage.py          # Django management script
├── rap_web/           # Project settings and configuration
├── users/             # User management and authentication
├── events/            # Event creation and management
├── attendance/        # Attendance tracking and history
├── notifications/     # Email notifications and reminders
├── static/            # Static assets (CSS, JS, images)
├── templates/         # HTML templates (Dutch language)
└── media/             # User-uploaded files (profile pics)

/docker/               # Docker configurations
├── docker-compose.dev.yml      # Development environment
├── docker-compose.prod.yml     # Production environment
└── nginx/             # Nginx configuration files

/docs/                 # Project documentation
/scripts/              # Deployment and utility scripts
```

## Key Django Apps

### 1. Users App (`web/users/`)
- **Models**: CustomUser extending AbstractUser, Player model with football-specific fields
- **Features**: User registration/login, profile management, role-based permissions
- **Key Fields**: position, jersey_number, profile_photo, contact_info
- **Templates**: registration, login, profile pages (Dutch)

### 2. Events App (`web/events/`)
- **Models**: Event, EventType with recurring event support
- **Features**: Event creation/management, recurring events, participant limits
- **Key Fields**: event_type, is_mandatory, max_participants, recurrence patterns
- **Views**: Dashboard, calendar view, event CRUD operations
- **Templates**: Event list/detail, calendar, admin dashboard (Dutch)

### 3. Attendance App (`web/attendance/`)
- **Models**: Attendance with history tracking
- **Features**: Mark attendance, view history, statistics generation
- **Key Fields**: status (attending/not_attending/maybe), timestamp tracking
- **Analytics**: Attendance rates, player statistics, admin reporting

### 4. Notifications App (`web/notifications/`)
- **Features**: Email notifications via Celery tasks
- **Integration**: Brevo SMTP service, HTML/plain text templates
- **Automation**: Event reminders, new event notifications
- **Language**: All notifications in Dutch

## Coding Standards & Best Practices

### Python/Django Style
- Follow PEP 8 formatting (enforced by Black with 88-character line length)
- Use Django best practices: CBVs, model methods, form validation
- Type hints encouraged (Python 3.12+ features supported)
- Use `select_related()` and `prefetch_related()` for query optimization
- Follow Django's security best practices

### Frontend Guidelines
- **Language**: All UI text, labels, and messages in Dutch
- **Design**: Modern SaaS aesthetic with football/sports theme
- **Colors**: Team colors (blue #1e40af, green #16a34a, red #dc2626)
- **Responsive**: Mobile-first design with Bootstrap-like grid
- **Components**: Reusable CSS classes for cards, buttons, forms

### Template Structure
- Extend from `base.html` with Dutch navigation
- Use semantic HTML5 elements
- Include CSRF tokens for forms
- Mobile-responsive design patterns
- Accessible form labels and ARIA attributes

## Development Environment

### Runtime and tools
Always assume Python 3.12 with Ubuntu runner. The repository provides a Postgres and Redis service via `.github/workflows/copilot-setup-steps.yml`.

### Databases and services
Use the Postgres service on `db:5432` with database `rap_web`, user `rap_user`, password `rap_db_password`. Use Redis at `redis://redis:6379/0`. Do not start new databases and do not switch to SQLite.

### Environment variables
Read variables from the repository environment named `copilot`. Use:
- `DATABASE_URL`
- `REDIS_URL`
- `DJANGO_SETTINGS_MODULE`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `DJANGO_SECRET_KEY`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`

Never create new credentials in code or change the database location. If a variable is missing, stop and ask for it to be added to the `copilot` environment.

### Install, migrate, test
1. `python -m pip install --upgrade pip`
2. `pip install -r requirements.txt` and `pip install -r requirements-dev.txt`
4. Run tests with `pytest -q` when `pytest.ini` or `pyproject.toml` defines pytest, otherwise `python manage.py test`

### Conventions
- Keep changes minimal and aligned with existing project structure
- When adding dependencies, add them to `pyproject.toml` and compile the new `requirements.txt` and `requirements-dev.txt` files using pip-tools. Never manually ad requirements using pip or manually edit the requirements files.

### Required Environment Variables
```bash
# Database Configuration
DATABASE_URL=postgres://rap_user:rap_db_password@db:5432/rap_web
POSTGRES_DB=rap_web
POSTGRES_USER=rap_user
POSTGRES_PASSWORD=rap_db_password
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Redis Configuration
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Django Settings
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
```

### Common Commands
```bash
# Start Celery worker
cd web && celery -A rap_web worker --loglevel=info

# Start Celery beat scheduler
cd web && celery -A rap_web beat --loglevel=info

# Run tests
cd web && python manage.py test

# Code formatting
black .
ruff check .
```

## Database Schema Overview

### Key Models & Relationships
- **CustomUser** → **Player** (OneToOne): Extended user with football-specific data
- **Event** → **EventType** (ForeignKey): Categorized events (training, match, etc.)
- **Event** → **Attendance** (ManyToMany through): Player attendance tracking
- **Event**: Supports recurring patterns with `recurrence_rule` field
- **Attendance**: Tracks status changes with timestamps for history

## Testing & Quality Assurance

### Test Coverage
- Unit tests for models, views, and forms
- Integration tests for key user workflows
- Email notification testing
- Authentication and permission testing

### Quality Tools
- **Black**: Code formatting (88-character line length)
- **Ruff**: Fast Python linting and import sorting
- **pip-audit**: Security vulnerability scanning
- **Django's check framework**: Deployment readiness validation

## Deployment & DevOps

### CI/CD Pipeline
- **GitHub Actions**: Automated testing, building, and deployment
- **Container Registry**: GitHub Container Registry (ghcr.io)
- **Production**: Docker Compose with Nginx reverse proxy
- **Health Checks**: Automated deployment verification
- **Environment**: Production secrets managed via GitHub environments

### Production Configuration
- PostgreSQL database with persistent volumes
- Redis for caching and Celery broker
- Nginx reverse proxy with SSL termination
- Static files served via WhiteNoise
- Email via Brevo SMTP service
- Automated backups and monitoring

## Special Considerations

### Dutch Language
- All user-facing text must be in Dutch
- Date/time formatting follows Dutch conventions
- Email templates in Dutch with HTML and plain text versions
- Form validation messages in Dutch

### Football/Sports Context
- Player positions: Keeper, Verdediging, Middenveld, Aanval
- Event types: Training, Wedstrijd, Toernooi, Teambuilding
- Jersey numbers and player-specific data
- Team-focused UI and terminology

### Security & Performance
- CSRF protection on all forms
- Rate limiting on authentication endpoints
- SQL injection prevention via Django ORM
- XSS protection with CSP headers
- Optimized database queries for performance
- Media file security and validation

This configuration provides GitHub Copilot with comprehensive context about your Django football team management application, enabling it to provide accurate and relevant code suggestions that align with your project's architecture, coding standards, and domain-specific requirements.
