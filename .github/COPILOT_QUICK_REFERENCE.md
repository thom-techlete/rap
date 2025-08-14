# GitHub Copilot Quick Reference for SV Rap 8

## 🚀 Getting Started with GitHub Copilot

The GitHub Copilot coding agent environment is now configured for your Django football team management application. Here's what you need to know:

### 📋 Pre-configured Environment

✅ **Django 5.2.5** - Web framework with REST API support  
✅ **PostgreSQL 17** - Primary database  
✅ **Redis 7** - Cache and Celery broker  
✅ **Celery 5.5.3** - Async task queue  
✅ **Dutch Language UI** - All templates and messages  
✅ **Football Domain Context** - Player positions, events, attendance  

### 🔧 Quick Commands

```bash
# Validate Copilot setup
./scripts/validate-copilot-setup.sh

# Start development environment
cd docker && docker-compose -f docker-compose.dev.yml up -d

# Run Django development server
cd web && python manage.py runserver

# Run tests
cd web && python manage.py test

# Code formatting
black . && ruff check .
```

### 🎯 Key Context for Copilot

- **Language**: All UI text must be in Dutch
- **Domain**: Football team management (SV Rap 8)
- **Apps**: users, events, attendance, notifications
- **Security**: CSRF, rate limiting, CSP headers
- **Email**: Brevo SMTP with Dutch templates

### 📁 Important Files

```
web/
├── users/models.py          # CustomUser, Player models
├── events/models.py         # Event, EventType models
├── attendance/models.py     # Attendance tracking
├── notifications/tasks.py   # Email notifications
└── templates/              # Dutch language templates

.github/
├── workflows/copilot-setup-steps.yml  # Environment setup
├── copilot-instructions.md            # Detailed project context
└── COPILOT_SETUP.md                   # Setup documentation
```

### 🔍 Common Patterns

**Model Creation:**
```python
# Use Dutch field names and validation
class Event(models.Model):
    naam = models.CharField(max_length=100, verbose_name="Evenement naam")
    datum = models.DateTimeField(verbose_name="Datum en tijd")
    verplicht = models.BooleanField(default=False, verbose_name="Verplicht")
```

**Template Structure:**
```html
{% extends 'base.html' %}
{% load i18n %}

{% block title %}Evenementen - SV Rap 8{% endblock %}
{% block content %}
    <h1>Komende Evenementen</h1>
    <!-- Dutch content -->
{% endblock %}
```

**View Patterns:**
```python
class EventListView(LoginRequiredMixin, ListView):
    model = Event
    template_name = 'events/event_list.html'
    context_object_name = 'evenementen'
    
    def get_queryset(self):
        return Event.objects.filter(
            datum__gte=timezone.now()
        ).select_related('event_type')
```

### 🎨 Styling Guidelines

- **Colors**: Blue (#1e40af), Green (#16a34a), Red (#dc2626)
- **Design**: Modern SaaS with football theme
- **Responsive**: Mobile-first design
- **Dutch**: All labels, buttons, messages in Dutch

### 🧪 Testing

```bash
# Run all tests
cd web && python manage.py test

# Run specific app tests
cd web && python manage.py test events

# Check coverage
cd web && coverage run --source='.' manage.py test
cd web && coverage report
```

### 📧 Email Context

All email notifications use Dutch templates with Brevo SMTP:
- Event reminders
- New event notifications
- Weekly summaries
- HTML and plain text versions

### 🚦 Environment Variables

Key variables for development:
```bash
DJANGO_SECRET_KEY=development-key
DJANGO_DEBUG=True
DATABASE_URL=postgres://postgres:postgres@localhost:5432/rap_web
REDIS_URL=redis://localhost:6379/0
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### 🎯 Next Steps

1. **Test the setup**: Run `./scripts/validate-copilot-setup.sh`
2. **Start coding**: GitHub Copilot now has full context
3. **Follow patterns**: Use existing code patterns for consistency
4. **Check roadmap**: See `docs/roadmap.md` for current status

---

**Ready to code!** 🚀 GitHub Copilot coding agent is configured with comprehensive context about your SV Rap 8 Django application.
