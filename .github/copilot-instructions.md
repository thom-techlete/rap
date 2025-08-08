# GitHub Copilot Custom Instructions for SV Rap 8 Event Presence Webapp

## Project Overview
This repository contains a Django-based web application for managing event presence for the football team SV Rap 8. The app allows team members to mark attendance for events, and admins to manage events and users. The default UI language is Dutch. The stack includes Django, PostgreSQL, Celery, Redis, Nginx, and Docker Compose.

## Folder Structure
- `/web/` (single Django project folder containing all apps, templates, and static files)
- `/nginx`: Nginx configuration
- `/docs`: Documentation
- `/scripts`: Shell scripts for setup and automation
- `/tests`: Test suite
- `/utils`: Utility modules
- `/example`: Example usage and notebooks

## Libraries and Frameworks
- Django (web framework)
- PostgreSQL (database)
- Celery (task queue)
- Redis (cache and broker)
- Nginx (web server)
- Docker Compose (service orchestration)

## Coding Standards
- Use PEP8 for Python code formatting
- Use Dutch for all UI labels, messages, and notifications
- Use clear, descriptive variable and function names
- Organize Django apps by feature (users, events, attendance, notifications)

## Build and Validation Instructions
- To set up the project, use Docker Compose for all services
- To run the backend locally: `docker-compose up --build`
- To run tests: `pytest` (inside the backend container)
- To run code quality checks: `black .` and `flake8 .`
- To apply migrations: `python manage.py migrate` (inside backend container)
- To create a superuser: `python manage.py createsuperuser`
- Always install dependencies from `requirements.txt` and `requirements-dev.txt`

## UI Guidelines
- Modern, sleek SaaS look with a sports theme
- Responsive and mobile-friendly design
- All features are private and require authentication

## Additional Notes
- Attendance history is tracked for future statistics
- Admins can edit attendance for any player
- Events can be recurring
- Notifications are sent via email and push
- Future support for multiple teams is planned
## Roadmap Reference
Always refer to `docs/roadmap.md` for the current development roadmap. When making any edits or changes, check the roadmap and mark any completed points as fixed in the file. This ensures progress is tracked and development stays aligned with planned steps.
For more details, see `docs/project_description.md`, `docs/roadmap.md`, and `README.md`. Follow these instructions for consistent and efficient development in this repository.
For more details, see `docs/project_description.md` and `README.md`. Follow these instructions for consistent and efficient development in this repository.
