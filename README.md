
![Django](https://img.shields.io/badge/Django-5.2.5-092E20?style=flat&logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-316192?style=flat&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=flat&logo=redis&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-5.5.3-37B24D?style=flat&logo=celery&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)
![Test Coverage](./coverage.svg)

# ⚽ SV Rap 8 - Event Presence Management Webapp

Een moderne web-applicatie voor het beheren van aanwezigheid bij evenementen van voetbalteam SV Rap 8. De app stelt teamleden in staat om aanwezigheid te markeren voor trainingen en wedstrijden, terwijl beheerders evenementen kunnen beheren en statistieken kunnen bekijken.

> **Taal**: Alle gebruikersinterfaces en notificaties zijn in het Nederlands

## ✨ Belangrijkste Functies

🔐 **Gebruikersbeheer** - Veilige authenticatie met rollen (spelers, coaches, invaller)  
📅 **Evenementenbeheer** - Maak en beheer trainingen, wedstrijden en toernooien  
✅ **Aanwezigheidsregistratie** - Markeer aanwezigheid met volledige geschiedenis  
🔄 **Terugkerende Evenementen** - Ondersteuning voor wekelijkse trainingen  
📧 **Email Notificaties** - Automatische herinneringen en updates (Brevo SMTP)  
📊 **Statistieken & Analytics** - Uitgebreide aanwezigheidsstatistieken  
📱 **Mobiel Responsive** - Modern ontwerp geoptimaliseerd voor alle apparaten  
📅 **Kalender Export** - ICS export voor kalender-apps  
🚀 **CI/CD Pipeline** - Geautomatiseerde tests en deployment  

## 🚀 Quick Start

### GitHub Copilot Development Setup (Aanbevolen)

Voor gebruikers met GitHub Copilot, gebruik het speciale setup script voor directe ontwikkelomgeving:

```bash
./scripts/copilot-setup.sh
```

Dit zet automatisch op:
- PostgreSQL en Redis services via Docker
- Python omgeving met alle dependencies
- Django met migraties en superuser
- Celery worker en beat op de achtergrond
- Ready-to-develop omgeving

📖 **Complete gids**: [.github/COPILOT_SETUP.md](.github/COPILOT_SETUP.md)

### Vereisten

- Python 3.12 of hoger
- Docker & Docker Compose
- Git
- Moderne webbrowser

### Eenvoudige Setup

```bash
git clone https://github.com/thom-techlete/rap.git
cd rap
./scripts/setup.sh
```

Dit zet alles op wat je nodig hebt voor ontwikkeling!

## 🏗️ Technische Stack

### Backend
- **Django 5.2.5** - Krachtig web framework met ingebouwde beveiliging
- **PostgreSQL 17** - Relationele database voor gebruikers, evenementen en aanwezigheid
- **Celery 5.5.3** - Asynchrone taakverwerking voor email notificaties
- **Redis 7** - Message broker en caching systeem
- **Django REST Framework** - API endpoints voor toekomstige uitbreidingen

### Frontend & Styling
- **Django Templates** - Server-side rendering met moderne HTML5
- **Bootstrap-stijl CSS** - Responsieve grid en componenten
- **Mobiel-first ontwerp** - Geoptimaliseerd voor alle schermformaten
- **Nederlandse UI** - Alle labels, formulieren en berichten in het Nederlands

### DevOps & Deployment
- **Docker & Docker Compose** - Containerisatie voor consistente deployment
- **Nginx** - Reverse proxy en statische bestanden
- **GitHub Actions** - CI/CD pipeline met geautomatiseerde tests
- **Health Checks** - Monitoring en automatische rollback
- **Brevo SMTP** - Professionele email service integratie

## � Project Structuur

```
rap/
├── web/                            # Django hoofdproject
│   ├── manage.py                   # Django management script
│   ├── rap_web/                    # Project instellingen
│   │   ├── settings.py             # Django configuratie
│   │   ├── urls.py                 # URL routing
│   │   └── celery.py               # Celery configuratie
│   ├── users/                      # Gebruikersbeheer
│   │   ├── models.py               # CustomUser, Player modellen
│   │   ├── forms.py                # Registratie en login formulieren
│   │   └── views.py                # Authenticatie views
│   ├── events/                     # Evenementenbeheer
│   │   ├── models.py               # Event, EventType modellen
│   │   ├── views.py                # Dashboard en CRUD views
│   │   ├── forms.py                # Evenement formulieren
│   │   └── dashboard_views.py      # Admin dashboard
│   ├── attendance/                 # Aanwezigheidsregistratie
│   │   ├── models.py               # Attendance met geschiedenis
│   │   ├── views.py                # Aanwezigheids views
│   │   └── urls.py                 # URL routing
│   ├── notifications/              # Email notificaties
│   │   ├── tasks.py                # Celery email taken
│   │   ├── utils.py                # Email utilities
│   │   └── templates/              # Email templates (NL)
│   ├── templates/                  # HTML templates
│   │   ├── base.html               # Basis template
│   │   ├── dashboard/              # Dashboard templates
│   │   └── registration/           # Auth templates
│   └── static/                     # CSS, JS, afbeeldingen
├── docker/                         # Docker configuraties
│   ├── docker-compose.dev.yml     # Ontwikkeling
│   ├── docker-compose.prod.yml    # Productie
│   └── nginx/                      # Nginx configuratie
├── docs/                           # Documentatie
│   ├── project_description.md      # Project overzicht
│   ├── roadmap.md                  # Ontwikkelings roadmap
│   └── DEPLOYMENT.md               # Deployment gids
├── scripts/                        # Deployment scripts
│   ├── setup.sh                    # Lokale setup
│   ├── deploy.sh                   # Productie deployment
│   └── copilot-setup.sh            # GitHub Copilot setup
└── .github/                        # GitHub configuratie
    ├── workflows/                  # CI/CD pipelines
    ├── copilot-instructions.md     # Copilot context
    └── COPILOT_SETUP.md            # Copilot documentatie
```

## 🎯 Kernfunctionaliteiten

### 👥 Gebruikersrollen

**Spelers**
- Bekijk komende evenementen en trainingen
- Markeer aanwezigheid (aanwezig/afwezig/misschien)
- Bekijk aanwezigheid van teamgenoten
- Persoonlijke statistieken en geschiedenis
- Profiel met positie en rugnummer

**Beheerders**
- Maak, bewerk en verwijder evenementen
- Beheer terugkerende trainingen
- Bekijk en bewerk alle aanwezigheidsregistraties
- Toegang tot uitgebreide statistieken
- Gebruikersbeheer en rolletoewijzing

### 📅 Evenementenbeheer

- **Evenement Types**: Training, Wedstrijd, Toernooi, Teambuilding
- **Terugkerende Events**: Wekelijkse trainingen met automatische generatie
- **Deelnemerslimieten**: Maximaal aantal deelnemers per evenement
- **Verplichte Aanwezigheid**: Markeer belangrijke evenementen
- **Kalender Export**: ICS bestanden voor externe kalenders

### 📊 Statistieken & Analytics

- **Aanwezigheidspercentages**: Per speler en per evenement type
- **Trending Data**: Maandelijkse en seizoensstatistieken
- **Team Overzicht**: Wie komt het meest/minst naar trainingen
- **Admin Dashboard**: Visuele rapportage en inzichten

## 🔧 Ontwikkeling

### Lokale Development Environment

```bash
# Start PostgreSQL en Redis
cd docker && docker-compose -f docker-compose.dev.yml up -d

# Activeer Python omgeving
source venv/bin/activate

# Start Django development server
cd web && python manage.py runserver

# Start Celery worker (nieuwe terminal)
cd web && celery -A rap_web worker --loglevel=info

# Start Celery beat scheduler (nieuwe terminal)
cd web && celery -A rap_web beat --loglevel=info
```

### Belangrijke Commando's

```bash
# Database migraties
cd web && python manage.py makemigrations
cd web && python manage.py migrate

# Superuser aanmaken
cd web && python manage.py createsuperuser

# Tests draaien
cd web && python manage.py test

# Code formatting
black .
ruff check . --fix

# Sample data laden
cd web && python manage.py populate_events
```

### Environment Variabelen

```bash
# Database
DATABASE_URL=postgres://postgres:password@localhost:5432/rap_web
POSTGRES_DB=rap_web
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password

# Redis & Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0

# Django
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Email (Brevo)
EMAIL_BACKEND=anymail.backends.brevo.EmailBackend
ANYMAIL_BREVO_API_KEY=your-api-key
DEFAULT_FROM_EMAIL=noreply@rap8.nl
```

## 🚀 Productie Deployment

### Eenvoudige VPS Deployment

Deploy naar een productieserver met één commando:

```bash
# Op je VPS server (Ubuntu 20.04+):
curl -fsSL https://raw.githubusercontent.com/thom-techlete/rap/main/scripts/vps-setup.sh | bash
```

### Handmatige Productie Setup

```bash
# Clone repository
git clone https://github.com/thom-techlete/rap.git /opt/rap
cd /opt/rap

# Genereer productie secrets
./scripts/generate_secrets.sh your-domain.com

# Deploy met SSL en security features
./scripts/deploy.sh your-domain.com --setup
```

### Productie Features
- 🔒 **SSL/TLS versleuteling** met Let's Encrypt
- 🛡️ **Security hardening** (firewall, rate limiting, secure headers)
- 🐳 **Docker containerisatie** met health checks
- 📊 **Monitoring** met health endpoints
- 🔄 **Geautomatiseerde backups** en updates
- ⚡ **High performance** met Nginx reverse proxy

Zie **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** voor gedetailleerde productie setup gids.

## 🧪 Testing & Code Kwaliteit

### Tests Draaien

```bash
# Alle tests (met SQLite voor snelheid)
cd web && python manage.py test --settings=rap_web.test_settings

# Specifieke app tests
cd web && python manage.py test users --settings=rap_web.test_settings
cd web && python manage.py test events --settings=rap_web.test_settings

# Met uitgebreide output
cd web && python manage.py test --settings=rap_web.test_settings --verbosity=2

# Met coverage
cd web && coverage run --source='.' manage.py test --settings=rap_web.test_settings
cd web && coverage report
cd web && coverage html  # HTML rapport in htmlcov/
```

**Opmerking**: De tests gebruiken een SQLite in-memory database voor snelheid en isolatie. Dit zorgt ervoor dat tests onder de 2 minuten blijven en deterministisch zijn.

### Code Kwaliteit Tools

```bash
# Code formatting
black .

# Linting en import sorting
ruff check . --fix

# Pre-commit hooks
pre-commit run --all-files

# Security audit
pip-audit

# Dependency check
cd web && python manage.py check --deploy
```

## 📱 Gebruikerservaring

### Mobiele App Features
- **Responsive Design**: Optimaal voor telefoons en tablets
- **Touch-friendly**: Grote knoppen en eenvoudige navigatie
- **Offline Indicaties**: Duidelijke feedback bij netwerkproblemen
- **Snelle Toegang**: Directe links naar meest gebruikte functies

### Desktop Features
- **Dashboard Overzicht**: Uitgebreid overzicht voor beheerders
- **Bulk Acties**: Beheer meerdere evenementen tegelijk
- **Statistieken**: Gedetailleerde grafieken en rapporten
- **Kalender Integratie**: Export naar Outlook, Google Calendar, etc.

## 🔐 Beveiliging & Privacy

- **CSRF Bescherming**: Tegen cross-site request forgery
- **Rate Limiting**: Bescherming tegen brute force aanvallen
- **Secure Headers**: CSP, HSTS, X-Frame-Options
- **Input Validatie**: Bescherming tegen XSS en SQL injection
- **Privacy**: Alle data privé en alleen toegankelijk na login
- **Wachtwoord Beleid**: Sterke wachtwoorden vereist

## 📚 Documentatie

| Document | Beschrijving |
|----------|-------------|
| **[Project Beschrijving](docs/project_description.md)** | Volledige project overzicht en requirements |
| **[Roadmap](docs/roadmap.md)** | Ontwikkelingsstatus en toekomstige features |
| **[Deployment](docs/DEPLOYMENT.md)** | Productie deployment gids |
| **[CI/CD Setup](docs/CI_CD_SETUP.md)** | GitHub Actions configuratie |
| **[Email Notificaties](docs/email_notifications.md)** | Email systeem documentatie |
| **[Beveiliging](docs/security.md)** | Security best practices |
| **[Copilot Setup](.github/COPILOT_SETUP.md)** | GitHub Copilot ontwikkelomgeving |

## 🎯 Huidige Status

✅ **Voltooid**
- Gebruikersauthenticatie en rolbeheer
- Evenementenbeheer met terugkerende events
- Aanwezigheidsregistratie en geschiedenis
- Email notificaties en herinneringen
- Moderne responsive UI in het Nederlands
- Statistieken en analytics dashboard
- CI/CD pipeline en productie deployment
- Kalender features en ICS export

🔄 **In Ontwikkeling**
- Advanced analytics uitbreidingen
- Multi-team ondersteuning voorbereiding
- API documentatie

Zie **[docs/roadmap.md](docs/roadmap.md)** voor gedetailleerde status updates.

## 🤝 Bijdragen

Dit project is ontwikkeld voor SV Rap 8. Voor vragen over bijdragen of aanpassingen, neem contact op met het ontwikkelteam.

### Development Workflow

```bash
# Nieuwe feature branch
./scripts/new-branch.sh feature/nieuwe-functie

# Code wijzigingen maken
# ...

# Tests en kwaliteitscontroles
cd web && python manage.py test
black .
ruff check . --fix

# Commit en push
git add .
git commit -m "Voeg nieuwe functie toe"
git push origin feature/nieuwe-functie
```

## 🛟 Troubleshooting

### Veelvoorkomende Problemen

**Database connectie problemen:**
```bash
# Check of PostgreSQL draait
docker-compose -f docker/docker-compose.dev.yml ps

# Herstart database
docker-compose -f docker/docker-compose.dev.yml restart postgres
```

**Celery email problemen:**
```bash
# Check Celery worker status
cd web && celery -A rap_web inspect active

# Herstart Celery
cd web && pkill -f celery
cd web && celery -A rap_web worker --loglevel=info &
```

**Static files niet geladen:**
```bash
cd web && python manage.py collectstatic
```

**Environment variabelen:**
```bash
# Check .env bestand
cat .env

# Herlaad direnv
direnv reload
```

## 📄 Licentie

Dit project is gelicenseerd onder de MIT License - zie het LICENSE bestand voor details.

---

**⚽ Klaar om te voetballen met moderne technologie!** 

Voor meer informatie of ondersteuning, neem contact op met het SV Rap 8 ontwikkelteam.
