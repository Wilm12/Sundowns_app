````markdown
# Sundowns WPA Platform

A production-style Django membership and operations platform for managing supporter memberships, branches, match tickets, payments, transport bookings, and verification workflows.

This project was built as a backend, DevOps, and cloud deployment portfolio project, focusing on real-world application delivery, containerization, CI/CD, infrastructure operations, and production-readiness practices.

---

## Project Overview

Sundowns WPA is a membership platform that allows supporters to:

- Register and belong to a branch
- Manage membership status
- View matches
- Book match tickets
- Generate and verify ticket QR codes
- Book transport linked to match tickets
- Verify transport boarding
- Handle membership payment activation flows

The project also includes production-style infrastructure using Docker, Nginx, Gunicorn, PostgreSQL, Redis, health checks, logging, automated backups, and AWS EC2 deployment.

---

## Tech Stack

### Backend

- Python
- Django
- Django REST Framework
- JWT authentication
- PostgreSQL
- Redis
- Celery foundation

### Frontend

- Django Templates
- Tailwind CSS

### DevOps & Infrastructure

- Docker
- Docker Compose
- Nginx reverse proxy
- Gunicorn application server
- GitHub Actions CI/CD
- AWS EC2
- Linux server administration
- Cron-based database backups
- Health checks
- Production logging

---

## Key Features

- User registration and authentication
- Branch assignment during registration
- Membership management
- Membership activation through payment flow
- Match listing
- Ticket booking
- QR code ticket generation
- Admin-only ticket verification
- Transport booking after ticket booking
- Transport boarding verification using ticket QR code
- Branch overview with supporter count
- Production health endpoint
- Dockerized development and production runtime

---

## Architecture

```text
Browser
→ Nginx
→ Gunicorn
→ Django
→ PostgreSQL
→ Redis
````

### Container Services

```text
nginx   → reverse proxy and static/media serving
web     → Django application running through Gunicorn
db      → PostgreSQL database
redis   → Redis broker/cache foundation
celery  → background worker foundation
```

---

## Development Environment

The development environment uses Docker Compose with:

* Django development server
* PostgreSQL container
* Redis container
* Celery container
* `.env.dev`
* `sundowns_app.settings.dev`

Run development stack:

```bash
docker compose up -d
```

Access app:

```text
http://127.0.0.1:8000/
```

---

## Production-Style Runtime

The production-style runtime uses:

* Nginx
* Gunicorn
* PostgreSQL
* Redis
* Docker Compose production override
* `.env.prod`
* `sundowns_app.settings.prod`

Run production-style stack:

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

Check containers:

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps
```

---

## Environment Variables

Real environment files are not committed to Git.

Use:

```text
.env.prod.example
```

as a template.

Required production variables include:

```env
DJANGO_SETTINGS_MODULE=sundowns_app.settings.prod
SECRET_KEY=
ALLOWED_HOSTS=
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=
CELERY_BROKER_URL=
CELERY_RESULT_BACKEND=
```

---

## Health Check

The application includes a production health endpoint:

```text
/common/health/
```

Expected response:

```json
{
  "status": "healthy",
  "database": "connected"
}
```

This verifies that Django can respond and connect to the database.

---

## CI/CD

GitHub Actions is configured to:

* Install dependencies
* Start PostgreSQL and Redis services
* Run Django checks
* Run migrations
* Run automated tests
* Validate Docker image build

Workflow file:

```text
.github/workflows/ci.yml
```

---

## Database Backups

The project includes a backup script:

```bash
scripts/backup_db.sh
```

Run manually:

```bash
./scripts/backup_db.sh
```

Backups are stored in:

```text
backups/
```

Backups are ignored by Git.

A cron job can be configured for automated daily backups.

---

## Logging and Observability

The project includes:

* Django console logging
* Gunicorn access logs
* Gunicorn error logs
* Docker container health checks
* Health endpoint monitoring
* Docker stats inspection

Logs are stored in:

```text
logs/
```

---

## Testing

Run tests locally:

```bash
python manage.py test --settings=sundowns_app.settings.test
```

Run tests inside Docker:

```bash
docker compose exec web python manage.py test --settings=sundowns_app.settings.test
```

---

## Deployment Status

Current deployment maturity:

* Local development environment complete
* Production-style Docker runtime complete
* Nginx reverse proxy configured
* Health checks configured
* GitHub Actions CI/CD configured
* AWS EC2 deployment tested
* Elastic IP configured
* Backup automation started
* Logging and observability started

---

## Future Improvements

* HTTPS with Let’s Encrypt
* Domain-based deployment
* Prometheus and Grafana monitoring
* Centralized logging
* AWS RDS migration
* Redis managed service migration
* Kubernetes deployment
* Helm charts
* GitOps with ArgoCD
* Terraform infrastructure automation
* Automated deployment pipeline

---

## Author

William Mabelane
GitHub: [Wilm12](https://github.com/Wilm12)
Portfolio: [DevOps Portfolio](https://github.com/Wilm12/devops)

````
