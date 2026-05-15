# Development and Testing Flow

# Overview

This document explains how the Sundowns WPA project moves from feature development into automated testing before eventually reaching staging and production environments.

The goal is to create a clear engineering workflow that supports:

* safe feature development
* business-rule validation
* regression prevention
* deployment readiness
* environment consistency

---

# Project Environment Lifecycle

The project progresses through environments in this order:

```text
Development
→ Testing
→ Staging
→ Production
```

Each environment has a different responsibility.

---

# 1. Development Environment

## Purpose

The development environment is where features are built and debugged.

Primary goals:

* rapid development
* manual feature testing
* debugging
* frontend iteration
* API development
* workflow implementation

---

## Development Characteristics

| Feature        | Development Environment   |
| -------------- | ------------------------- |
| DEBUG          | True                      |
| Server         | Django development server |
| Database       | PostgreSQL container      |
| Infrastructure | Docker Compose            |
| Testing style  | Manual + browser testing  |
| Purpose        | Feature building          |

---

## Development Environment

The development environment runs inside Docker Compose for consistency.

It uses:

* Django development server
* `sundowns_app.settings.dev`
* `.env.dev`
* PostgreSQL container
* Redis container
* Celery container
* `DEBUG=True`
* manual browser testing

Typical command:

```bash
docker compose up -d
```

Then access:

```text
http://127.0.0.1:8000/
```

---

## Development Runtime Flow

When running:

```bash
python manage.py runserver
```

Django flow:

```text
manage.py
↓
DJANGO_SETTINGS_MODULE
↓
sundowns_app.settings.dev
↓
Django loads:
- apps
- models
- URLs
- views
- templates
↓
runserver starts
↓
Browser sends request
↓
URL routing occurs
↓
View logic executes
↓
Response returned
```

---

## Development Workflow

Typical development workflow:

```text
Create feature branch
↓
Implement feature
↓
Run development server
↓
Open browser
↓
Test feature manually
↓
Fix bugs
↓
Commit working milestone
```

---

## Example Development Flow: Ticket Booking

```text
User opens /matches/
↓
Clicks Book Ticket
↓
book_ticket_page executes
↓
Membership validation occurs
↓
Duplicate ticket validation occurs
↓
Ticket is created
↓
User redirected to transport prompt
```

During development, the workflow is validated manually in the browser.

---

# 2. Testing Environment

## Purpose

The testing environment validates business rules automatically.

Primary goals:

* automated validation
* regression prevention
* workflow protection
* permission validation
* business-rule verification
* deployment confidence

---

## Testing Characteristics

| Feature       | Testing Environment       |
| ------------- | ------------------------- |
| DEBUG         | Usually False or isolated |
| Database      | Temporary test database   |
| Testing style | Automated                 |
| Execution     | Docker-based              |
| Purpose       | Workflow validation       |

---

## Testing Environment

The testing environment also runs inside Docker Compose, but uses:

* `sundowns_app.settings.test`
* temporary test database
* automated Django/DRF tests
* isolated test data

---

## Test Execution

Tests run inside Docker:

```bash
docker compose exec web python manage.py test --settings=sundowns_app.settings.test
```

---

## Testing Runtime Flow

```text
Docker web container
↓
manage.py test
↓
settings.test
↓
Django creates temporary test database
↓
Test files execute
↓
Fake data created
↓
Business rules validated
↓
Assertions checked
↓
Temporary database destroyed
```

---

## Example Testing Flow: Ticket Booking

The test automatically:

```text
Creates branch
↓
Creates user
↓
Creates active membership
↓
Creates match
↓
Attempts ticket booking
↓
Verifies ticket exists
↓
Verifies redirect behavior
```

Unlike development, testing does not rely on manual browser interaction.

---

# Development vs Testing

## Development

Development answers:

```text
Does the feature work while I build it?
```

Characteristics:

* manual
* interactive
* fast iteration
* browser-based validation
* debugging-focused

---

## Testing

Testing answers:

```text
Will the feature continue working after future changes?
```

Characteristics:

* automated
* repeatable
* isolated
* regression-focused
* business-rule-focused

---

# Why Both Environments Matter

Development alone is insufficient because:

* future changes may break older features
* hidden regressions may appear
* permissions may fail silently
* workflows may become inconsistent

Testing protects the system from accidental breakage.

---

# Current Development Workflow

The current engineering workflow for Sundowns WPA is:

```text
Create feature branch
↓
Develop feature locally
↓
Run manual browser checks
↓
Add/update automated tests
↓
Run Docker test suite
↓
Update documentation
↓
Commit feature
↓
Merge into develop
↓
Run tests again
↓
Merge into master
```

---

# Git Workflow

## Branch Structure

```text
feature branch
→ develop
→ master
```

---

## Feature Branch Purpose

Feature branches isolate work during development.

Examples:

```text
feature/authentication
feature/payments
feature/testing-environment
```

---

## Develop Branch Purpose

The develop branch acts as the integration branch.

Purpose:

* combine completed features
* validate merges
* run full testing
* stabilize workflows

---

## Master Branch Purpose

The master branch represents the most stable version of the application.

Only tested and validated features should reach master.

---

# Docker Workflow

## Development Containers

Main development services:

| Service | Purpose             |
| ------- | ------------------- |
| web     | Django application  |
| db      | PostgreSQL database |
| redis   | Redis service       |
| celery  | Celery worker       |

---

## Start Containers

```bash
docker compose up -d
```

---

## Rebuild Containers

```bash
docker compose up --build
```

---

## Stop Containers

```bash
docker compose down
```

---

# Current Automated Test Coverage

Implemented automated tests currently validate:

* registration with required branch
* JWT login authentication
* successful membership activation
* inactive membership ticket restriction
* ticket booking redirect flow
* transport prompt workflow
* QR verification workflow
* admin-only QR verification
* duplicate ticket prevention
* transport capacity validation
* transport-match consistency

---

# Documentation Workflow

Documentation updates should occur when:

* new workflows are added
* business rules change
* architecture changes
* deployment setup changes
* testing coverage expands
* major bugs are resolved

---

# Common Development Mistakes

## Incorrect Docker Database Host

Inside Docker:

```python
HOST = "db"
```

Do NOT use:

```python
HOST = "localhost"
```

---

## Unresolved Merge Conflicts

Conflict markers must always be removed:

```text
<conflict-start>
Current branch changes
<separator>
Incoming branch changes
<conflict-end>
```

After resolving conflicts:

```bash
git add .
git commit
```

---

## Missing Dependencies

If dependencies are added:

```bash
pip install package_name
pip freeze > requirements.txt
```

Then rebuild Docker:

```bash
docker compose up --build
```

---

# Why Testing Matters Before Production

Testing becomes critical as complexity grows.

The project now contains:

* authentication
* permissions
* memberships
* payments
* ticketing
* QR workflows
* transport logic
* branch logic
* frontend/API separation
* Docker environments
* automated tests

Without testing, future development becomes risky.

---

# Current Project State

The project currently includes:

* modular Django apps
* frontend/API separation
* Docker-based development
* Docker-based testing
* PostgreSQL integration
* Redis/Celery foundations
* Tailwind frontend
* tested business rules
* deployment preparation phase

---

# Next Phase

After development and testing stabilization, the project will move into:

```text
Staging Environment
↓
Production Environment
```

Upcoming focus areas:

* production Docker setup
* Gunicorn
* Nginx
* static/media handling
* environment hardening
* CI/CD integration
* AWS deployment
