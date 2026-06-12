# CRM System

A production-ready Customer Relationship Management system built with **Django 5+ / Django REST Framework / PostgreSQL / Bootstrap 5**. Runs entirely on a single Linux host — no Docker, Redis, Celery or microservices.

## Features

| Module | Highlights |
|---|---|
| **Authentication** | Email login, registration with email verification, JWT for the API, password change/reset, "remember me", profile with avatar |
| **RBAC** | 5 roles (Super Admin, Admin, Manager, Sales Agent, Support Agent) enforced by one central permission matrix for both web and API |
| **Dashboard** | KPI cards, monthly revenue / lead conversion / customer growth / employee performance charts (Chart.js + AJAX) |
| **Customers** | Full CRUD, search & filters, tags, documents with upload validation, activity timeline |
| **Leads** | Sources, 6-stage pipeline, assignment with notifications, notes, one-click convert-to-customer |
| **Deals** | Drag-and-drop Kanban board (AJAX stage updates), list view, revenue tracking |
| **Tasks** | Priorities, statuses, due dates with overdue flag, comments, attachments |
| **Tickets** | Auto numbering (`TKT-2026-0001`), priorities, replies, assignment notifications |
| **Invoices** | Auto numbering, tax calculation, PDF download, print view |
| **Notifications** | Stored in PostgreSQL, navbar dropdown + AJAX mark-as-read |
| **Reports** | 6 reports, each exportable to **Excel** and **PDF** |
| **Activity Log** | Append-only audit trail with user, action, IP and timestamp |
| **REST API** | `/api/v1/` ViewSets for every entity, JWT auth, filtering, search, pagination, throttling |

## Tech stack

Python 3.12+ · Django 5+ · Django REST Framework · SimpleJWT · PostgreSQL · Bootstrap 5 · Chart.js · Gunicorn · Nginx · WhiteNoise

## Quick start (development)

```bash
# 1. PostgreSQL database
sudo -u postgres psql -c "CREATE ROLE crm_user WITH LOGIN PASSWORD 'devpass' CREATEDB;"
sudo -u postgres psql -c "CREATE DATABASE crm_db OWNER crm_user;"

# 2. Python environment
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. Configuration
cp .env.example .env    # edit values

# 4. Database & admin user
python manage.py migrate
python manage.py createsuperuser

# 5. Run
python manage.py runserver
```

Open http://127.0.0.1:8000 and sign in.

## Project structure

```
crm_system/
├── config/              # settings (base / development / production), root urls, wsgi
├── core/                # TimeStampedModel, RBAC matrix, mixins, DRF permissions, validators
├── accounts/            # custom User, auth views, JWT, profile
├── dashboard/           # KPI view + chart JSON endpoints
├── customers/           # customers, tags, documents
├── leads/               # leads, notes, convert-to-customer
├── deals/               # deals, kanban board, stage AJAX
├── tasks/               # tasks, comments, attachments
├── tickets/             # support tickets, replies
├── invoices/            # invoices, PDF generation
├── reports/             # report builders, Excel/PDF export
├── notifications/       # DB-backed notifications
├── activity_logs/       # audit trail
├── templates/           # Bootstrap 5 UI (sidebar, dark mode, kanban, charts)
├── static/              # css / js
└── deploy/              # nginx.conf, gunicorn.service, DEPLOYMENT.md
```

## REST API

Obtain a token, then call any endpoint with `Authorization: Bearer <access>`:

```bash
curl -X POST http://127.0.0.1:8000/api/token/ \
     -d "email=you@company.com" -d "password=secret"

curl http://127.0.0.1:8000/api/v1/customers/?search=acme \
     -H "Authorization: Bearer <access>"
```

| Endpoint | Description |
|---|---|
| `POST /api/token/` · `/refresh/` · `/verify/` | JWT lifecycle |
| `/api/v1/users/` | User admin (Admin+) |
| `/api/v1/customers/` · `/api/v1/tags/` | Customers & tags |
| `/api/v1/leads/` (+`POST {id}/add_note/`) | Leads |
| `/api/v1/deals/` | Deals |
| `/api/v1/tasks/` (+`POST {id}/add_comment/`) | Tasks |
| `/api/v1/tickets/` (+`POST {id}/reply/`) | Tickets |
| `/api/v1/invoices/` | Invoices |
| `/api/v1/notifications/` (+`POST mark_all_read/`) | Own notifications |
| `/api/v1/activity-logs/` | Audit log (read-only, Admin+) |

All list endpoints support `?page=`, `?page_size=`, `?search=`, `?ordering=` and model-specific filters (e.g. `?status=`, `?stage=`).

## Roles & permissions

| Module | Super Admin | Admin | Manager | Sales Agent | Support Agent |
|---|---|---|---|---|---|
| Customers | full | full | full | full | view |
| Leads / Deals | full | full | full | full | — |
| Tasks | full | full | full | full | full |
| Tickets | full | full | full | — | full |
| Invoices / Reports | full | full | full | — | — |
| Activity Log / Users | full | view | — | — | — |

## Tests

```bash
coverage run manage.py test && coverage report
```

90 tests, **94% coverage** (unit, integration and API tests).

## Production deployment

See [`deploy/DEPLOYMENT.md`](deploy/DEPLOYMENT.md) for the full Arch Linux + PostgreSQL + Nginx + Gunicorn guide (systemd unit and Nginx config included).

## Security

CSRF protection on all forms · XSS-safe template escaping · ORM-only queries (no raw SQL) · JWT with rotation + blacklist · PBKDF2 password hashing with strong validators · file upload extension/size whitelist · per-module RBAC checks on every view · HTTPS/HSTS/secure-cookie hardening in production settings · API rate throttling.
