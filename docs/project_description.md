# SV Rap 8 Event Presence Management Webapp

## Project Overview
This web application is designed to help manage the presence of team members at events for the football team SV Rap 8. The platform will streamline event organization, attendance tracking, and team communication, providing both players and admins with a user-friendly interface and robust backend services.

## Key Requirements and Clarifications

- **Default Language:** The entire UI and all notifications will be in Dutch.
- **Teams:** The system will initially support one team (SV Rap 8), but is designed for future multi-team support.
- **User Model:** Each user will have:
	- Role: speler, coach, invaller
	- Basic info: email, phone, address
	- Position on field
- **Authentication:** Email/password login.
- **Attendance Management:**
	- Players and admins can mark attendance per event.
	- Admins can edit attendance for any player.
	- Attendance history is tracked (when someone submits, changes, etc.) for future statistics.
- **Notifications:** Email and push notifications for event reminders and attendance changes.
- **Events:** Support for recurring events (e.g., weekly training).
- **Privacy:** All features are private and require authentication; no public pages.
- **Design:** Modern, sleek SaaS look with a sports theme.

## Core Features

### User Accounts
- Each team member will have a personal account.
- Authentication and authorization will be handled securely.
- Roles: Player and Admin.

### Admin Capabilities
- Admins can create, edit, and delete events (trainings, matches, other team activities).
- Admins can view attendance for all events.
- Admins can manage team member accounts and assign admin roles.

### Player Capabilities
- Players can log in to view upcoming events.
- For each event, players can indicate their presence (attending/not attending).
- Players can view the attendance status of other team members for each event.

### Attendance History and Statistics
- The system will record when a user submits or changes their attendance for each event.
- This data will be used for future statistics and analytics on attendance.

### Event Management
- Events have types (training, match, other), date, time, location, and description.
- Attendance status is tracked per event and per player.
- Events can be recurring (e.g., weekly training sessions).

## Technical Stack

### Backend
- **Django**: Main web framework for rapid development and robust security.
- **PostgreSQL**: Relational database for storing user, event, and attendance data.
- **Celery**: Asynchronous task queue for background jobs (e.g., notifications, reminders).
- **Redis**: Used as a broker for Celery and for caching frequently accessed data.

### Frontend
- Django templates for initial implementation; can be extended to React or Vue.js in future.

### Internationalization
- All UI and notifications will be in Dutch by default.

### Infrastructure
- **Nginx**: Web server and reverse proxy for serving the application and static files.
- **Docker Compose**: Container orchestration for managing all services (Django, PostgreSQL, Redis, Nginx).

## Key Functional Requirements
- Secure user authentication and role-based access control.
- CRUD operations for events (by admins).
- Attendance marking for events (by players).
- Real-time or near-real-time updates of attendance lists (using Celery and Redis).
- Admin dashboard for event and attendance management.
- Player dashboard for viewing events and attendance.
- Email notifications for event reminders (optional, via Celery).

- Push notifications for events and attendance changes.
- Attendance history tracking for future statistics.

## Non-Functional Requirements
- Responsive and mobile-friendly UI.
- Scalable architecture for future growth.
- Secure handling of user data and authentication.
- Efficient caching and background processing.
- Easy deployment and maintenance via Docker Compose.

- Modern, sleek SaaS design with a sports theme.
## Future Extensions


## Project Structure (Planned)


## Roadmap Reference
Always refer to `docs/roadmap.md` for the current development roadmap. When making any edits or changes, check the roadmap and mark any completed points as fixed in the file. This ensures progress is tracked and development stays aligned with planned steps.
This document serves as the initial specification for the SV Rap 8 Event Presence Management Webapp. It will be updated as the project evolves.
## Project Structure (Planned)
