# Development Environment

## Overview

The Sundowns WPA project uses a Docker-based local development environment to ensure consistency across development, testing, staging, and future production deployments.

The development environment is designed to support:

- Django + DRF backend development
- PostgreSQL database integration
- Redis and Celery foundations
- Tailwind frontend development
- JWT authentication workflows
- Docker-based local execution
- Environment-specific settings management

---

# Development Stack

## Core Technologies

- Python 3.12 (local)
- Django
- Django REST Framework
- PostgreSQL
- Redis
- Celery
- Docker
- Docker Compose
- Tailwind CSS
- JWT Authentication (`djangorestframework-simplejwt`)

---

# Project Architecture

## Hybrid Frontend/API Architecture

The project separates:

- frontend/template routes
- DRF/API routes

Structure:

```text
frontend_urls.py -> frontend/template views
urls.py -> DRF/API endpoints
```

This separation improves:

- frontend organization
- API maintainability
- testing clarity
- deployment flexibility

---

# Docker Development Environment

## Main Services

The Docker development environment includes:

| Service | Purpose |
|---|---|
| web | Django application |
| db | PostgreSQL database |
| redis | Redis service |
| celery | Celery worker |

---

## Docker Compose Workflow

### Start development environment

```bash
docker compose up -d
```

### Rebuild containers

```bash
docker compose up --build
```

### Stop containers

```bash
docker compose down
```

### View running containers

```bash
docker compose ps
```

### View logs

```bash
docker compose logs -f
```

---

# Development Settings

## Settings Structure

Environment-specific settings are separated into:

```text
sundowns_app/settings/
├── base.py
├── dev.py
├── test.py
├── staging.py
├── prod.py
```

---

## Development Settings

Typical development environment:

```python
DEBUG = True
```

Development settings are intended for:

- local debugging
- rapid iteration
- frontend development
- local API testing

---

# Environment Variables

## Local Environment File

Development variables are stored in:

```text
.env.dev
```

Example variables:

```env
DEBUG=True
SECRET_KEY=your-dev-secret-key
DB_NAME=sundowns_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
```

---

# Database Development Workflow

## Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## Create superuser

```bash
python manage.py createsuperuser
```

---

## Open Django shell

```bash
python manage.py shell
```

---

# Running the Application

## Local Development Server

```bash
python manage.py runserver
```

---

## Docker Development Server

```bash
docker compose exec web python manage.py runserver 0.0.0.0:8000
```

---

# Frontend Development

## Tailwind CSS

The frontend uses Tailwind CSS for:

- responsive layouts
- dashboard styling
- membership pages
- ticket booking UI
- transport flows
- admin dashboard styling

---

## Current Frontend Features

Implemented frontend modules:

- Authentication
- Dashboard
- Membership
- Payments
- Matches
- Ticket Booking
- QR Tickets
- Transport
- Settings/Profile Management
- Password Change
- Admin Dashboard

---

# Authentication System

## JWT Authentication

The project uses:

```text
djangorestframework-simplejwt
```

Features:

- access tokens
- refresh tokens
- authenticated API routes
- role-based access control

---

# Branch System

## Branch Requirements

Business rule:

```text
Every user must belong to a branch.
```

Branch selection occurs during registration.

Branch logic is integrated into:

- registration
- memberships
- transport
- dashboard display
- settings/profile management

---

# Membership System

## Membership Workflow

Membership flow:

```text
Register
→ Membership created inactive
→ Payment completed
→ Membership activated
```

Ticket booking requires:

```text
membership.status == active
```

---

# Ticketing System

## Ticket Workflow

```text
Book Ticket
→ Ticket created
→ Redirect to transport prompt
→ Transport selection
→ QR ticket generated
```

---

## QR Verification

QR verification is restricted to admin users.

Verification flow:

```text
booked
→ verified
→ used
```

---

# Transport System

## Transport Rules

Transport is linked to:

- branches
- matches
- tickets

Business rules:

- transport capacity cannot be exceeded
- ticket and transport matches must align
- invalid transport bookings are blocked

---

# Testing During Development

## Running Tests

```bash
docker compose exec web python manage.py test --settings=sundowns_app.settings.test
```

---

## Current Testing Coverage

Implemented tests include:

- registration validation
- login/JWT authentication
- payment activation workflow
- inactive membership ticket restriction
- ticket booking redirect flow
- QR verification permissions
- duplicate ticket prevention
- transport capacity validation
- transport match consistency

---

# Common Development Issues

## Database Connection Errors

Inside Docker:

```python
HOST = "db"
```

Do NOT use:

```python
HOST = "localhost"
```

---

## Missing Python Modules

Install missing dependencies:

```bash
pip install package_name
pip freeze > requirements.txt
```

Rebuild Docker afterward:

```bash
docker compose up --build
```

---

## Merge Conflicts

When resolving merge conflicts:

- remove all conflict markers
- verify frontend/API routes remain intact
- rerun tests after merge resolution

Conflict markers:

```text
<<<<<<< HEAD
=======
>>>>>>> branch-name
```

---

# Git Workflow

## Recommended Workflow

```text
feature branch
→ develop
→ master
```

---

## Example Workflow

```bash
git checkout -b feature/testing-environment
```

Merge into develop:

```bash
git checkout develop
git merge feature/testing-environment
```

Merge into master:

```bash
git checkout master
git merge develop
```

---

# Documentation Structure

Current documentation:

```text
docs/
├── architecture.md
├── deployment_plan.md
├── docker_troubleshooting.md
├── staging_setup.md
├── testing_environment.md
```

---

# Development Readiness Status

Current project state:

- frontend implemented
- backend workflows implemented
- testing environment implemented
- business-rule validation implemented
- transport workflows implemented
- documentation structure implemented
- deployment preparation phase started

---

# Next Phase

Upcoming deployment preparation work:

- production Docker setup
- Gunicorn configuration
- Nginx configuration
- static/media handling
- environment hardening
- staging deployment
- CI/CD integration
- AWS deployment
