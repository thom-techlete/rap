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

### Required Environment Variables
```bash
# Database Configuration
DATABASE_URL=postgres://postgres:password@localhost:5432/rap_web
POSTGRES_DB=rap_web
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Django Settings
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Email Configuration (Brevo)
EMAIL_BACKEND=anymail.backends.brevo.EmailBackend
ANYMAIL_BREVO_API_KEY=your-api-key
DEFAULT_FROM_EMAIL=noreply@rap8.nl
```

### Common Commands
```bash
# Development server
cd web && python manage.py runserver

# Run migrations
cd web && python manage.py migrate

# Create superuser
cd web && python manage.py createsuperuser

# Collect static files
cd web && python manage.py collectstatic

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

### Docker Development
```bash
# Start development environment
cd docker && docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Execute commands in container
docker-compose -f docker-compose.dev.yml exec web python manage.py shell
```

## Database Schema Overview

### Key Models & Relationships
- **CustomUser** → **Player** (OneToOne): Extended user with football-specific data
- **Event** → **EventType** (ForeignKey): Categorized events (training, match, etc.)
- **Event** → **Attendance** (ManyToMany through): Player attendance tracking
- **Event**: Supports recurring patterns with `recurrence_rule` field
- **Attendance**: Tracks status changes with timestamps for history

### Important Queries
```python
# Optimized event list with attendance counts
events = Event.objects.select_related('event_type').prefetch_related('attendances')

# Player attendance statistics
player.attendance_set.filter(status='attending').count()

# Upcoming events for dashboard
Event.objects.filter(date__gte=timezone.now()).order_by('date')
```

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

## Feature Roadmap Reference
Always refer to `docs/roadmap.md` for current development status. Most core features are completed:
- ✅ User authentication and role management
- ✅ Event management with recurring events
- ✅ Attendance tracking and history
- ✅ Email notifications and reminders
- ✅ Modern responsive UI in Dutch
- ✅ Statistics and analytics dashboard
- ✅ CI/CD pipeline and production deployment
- ✅ Calendar features and ICS export

When making changes, update the roadmap to mark completed items and track progress.

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
