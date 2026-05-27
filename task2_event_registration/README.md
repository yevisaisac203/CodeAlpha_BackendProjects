#  EventHub � Event Registration System

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Django](https://img.shields.io/badge/Django-5.2-green)
![DRF](https://img.shields.io/badge/DRF-API-red)
![JWT](https://img.shields.io/badge/Auth-JWT-black)
![SQLite](https://img.shields.io/badge/Database-SQLite-003B57)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Overview
EventHub is a backend-first event registration platform built with Django and Django REST Framework. It supports role-based access for attendees and organizers, secure JWT authentication, event publishing workflows, and real-time registration handling with automatic waitlist promotion. The project is designed as a production-style API foundation for web or mobile event products.

In a real-world setting, EventHub can power conference portals, meetup ecosystems, corporate training events, and community activities where seat limits and attendee flow matter. Organizers can publish and manage events, while attendees discover events, register, and receive ticket codes. The system enforces capacity constraints and promotes waitlisted users when cancellations happen, creating a reliable registration lifecycle.

## Features by Role
- Attendees: browse events, register, receive ticket code, view my registrations, cancel registration
- Organizers: create and manage events, view attendees, check-in readiness support, event statistics
- System: automatic waitlist promotion, unique ticket code generation, capacity-aware registration management

## Tech Stack
| Technology | Purpose | Version |
|---|---|---|
| Python | Core programming language | 3.11 |
| Django | Web framework and ORM | 5.2.x |
| Django REST Framework | REST API toolkit | 3.x |
| SimpleJWT | JWT auth tokens | 5.x |
| django-filter | API filtering support | 24.x |
| SQLite | Default development database | 3 |

## Quick Start
1. Clone the repository:
```bash
git clone https://github.com/yevisaisac203/CodeAlpha_BackendProjects.git
cd CodeAlpha_BackendProjects/task2_event_registration
```
2. Create and activate a virtual environment:
```bash
python -m venv venv
# Windows PowerShell
venv\Scripts\Activate.ps1
# Windows CMD
venv\Scripts\activate.bat
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```
4. Apply migrations:
```bash
python manage.py migrate
```
5. Seed demo data:
```bash
python manage.py seed_events
```
6. Create an admin user:
```bash
python manage.py createsuperuser
```
7. Run the development server:
```bash
python manage.py runserver
```
8. Open:
- API root: `http://127.0.0.1:8000/api/`
- Admin: `http://127.0.0.1:8000/admin/`

## API Reference
### Auth
| Method | URL | Description | Auth | Request Body |
|---|---|---|---|---|
| POST | `/api/auth/register/` | Register a new user account | No | `username, email, password, password2, role` |
| POST | `/api/auth/login/` | Login with username or email | No | `username_or_email, password` |
| GET | `/api/auth/profile/` | Get current user profile | Bearer Token | None |
| PATCH | `/api/auth/profile/` | Update profile fields and picture | Bearer Token | `bio, phone_number, profile_picture` |
| POST | `/api/auth/token/` | Obtain access/refresh token pair | No | `username, password` |
| POST | `/api/auth/token/refresh/` | Refresh access token | No | `refresh` |

### Events
| Method | URL | Description | Auth | Request Body |
|---|---|---|---|---|
| GET | `/api/events/` | List published events | No | None |
| GET | `/api/events/{slug}/` | Get event details | No | None |
| POST | `/api/events/` | Create event | Organizer/Admin | Event fields |
| PATCH | `/api/events/{slug}/` | Update event | Owner/Admin | Any editable event fields |
| DELETE | `/api/events/{slug}/` | Delete event | Owner/Admin | None |
| GET | `/api/events/upcoming/` | Next 10 upcoming published events | No | None |
| POST | `/api/events/{slug}/register/` | Register for event | Bearer Token | `notes` (optional) |
| DELETE | `/api/events/{slug}/unregister/` | Cancel registration | Bearer Token | None |
| GET | `/api/events/{slug}/attendees/` | List confirmed attendees | Owner/Admin | None |
| GET | `/api/events/{slug}/stats/` | Event registration stats | Owner/Admin | None |

### Registrations
| Method | URL | Description | Auth | Request Body |
|---|---|---|---|---|
| GET | `/api/registrations/` | List registrations (self, or all for admin) | Bearer Token | None |
| GET | `/api/registrations/mine/` | Current user's registrations | Bearer Token | None |
| GET | `/api/registrations/ticket/{ticket_code}/` | Lookup registration by ticket code | Owner/Organizer | None |

## Test Credentials
| Role | Email | Password |
|---|---|---|
| Organizer | organizer@test.com | TestPass123 |
| Attendee | attendee@test.com | TestPass123 |

## Entity Relationship Diagram
```text
+------------------+
|      User        |
|------------------|
| id (PK)          |
| username         |
| email            |
| role             |
+--------+---------+
         |
         | 1..*
         v
+------------------+        *..1       +------------------+
| Registration     |------------------>| Event            |
|------------------|                   |------------------|
| id (PK)          |                   | id (PK)          |
| user_id (FK)     |                   | organizer_id (FK)|
| event_id (FK)    |                   | category_id (FK) |
| status           |                   | title, slug      |
| ticket_code      |                   | start/end time   |
+------------------+                   +---------+--------+
                                                  |
                                                  | *..1
                                                  v
                                         +------------------+
                                         | Category         |
                                         |------------------|
                                         | id (PK)          |
                                         | name, slug       |
                                         +------------------+
```

## Deployment Notes
For free-tier deployment, Render and Railway are strong options for Django APIs. You can host the web service there, configure environment variables (`SECRET_KEY`, `DEBUG`, database URL), and switch from SQLite to PostgreSQL for production persistence.

## License
MIT
