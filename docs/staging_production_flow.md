# Sundowns — Staging & Production Flow

This document describes the full evolution of the Sundowns WPA platform from local Docker development through production-style deployment on AWS EC2. It explains why each stage exists, how components (Docker, Nginx, Gunicorn, PostgreSQL, Redis, GitHub Actions, HTTPS, health checks, backups, logging) are used in this project, and contains operational guidance, commands, and architecture diagrams.

## 1. Purpose

This guide documents the platform lifecycle and operational patterns used for Sundowns: from developer machines running Docker Compose, to a testing/QA environment, to a production-style runtime on AWS EC2. The goal is to make deployments repeatable, secure, and observable while keeping developer feedback quick during local development.

Why this stage-by-stage approach:

- Reduces risk by matching behavior across environments.
- Makes debugging and rollbacks predictable.
- Enables automated CI/CD and repeatable infrastructure changes.

## 2. Development Environment

What it is:

- A developer machine running the application via `docker-compose.yml` or `docker-compose.dev.yml` with code mounted into containers for fast iteration.

Why it's necessary:

- Fast edit–reload feedback loop.
- Matches runtime dependencies (Python, PostgreSQL, Redis) without polluting the host OS.

Key components and notes:

- Docker Compose: orchestrates `web`, `worker`, `db`, and `redis` containers for local development.
- Gunicorn: in dev we often use Django's `runserver` or Gunicorn with lower worker counts to replicate production entrypoint behavior.
- PostgreSQL: uses a local Docker container; volumes persist test data between runs.
- Redis: used for Celery and caching; runs as a container.

Common developer commands:

```bash
# Start dev stack (foreground)
docker-compose -f docker-compose.dev.yml up --build

# Start dev stack (detached)
docker-compose -f docker-compose.dev.yml up -d --build

# Stop dev stack
docker-compose -f docker-compose.dev.yml down -v
```

Architecture (local dev):

Developer Machine -> Docker Compose -> [web (Gunicorn/Django), db(Postgres), cache(Redis), worker(Celery)]

## 3. Testing Environment

What it is:

- A controlled, ephemeral environment intended for automated tests and manual QA staging. It is configured to be as close to production runtime as practical while still supporting repeated tear-down and automation.

Why it's necessary:

- Validates build artifacts (images), migrations, and integration with external services before production.
- Acts as a gate in CI pipelines (unit tests, integration tests, smoke tests).

How it differs from development:

- Builds production-style images (no bind mounts).
- Uses the same entrypoints (Gunicorn + Nginx) and similar process counts.
- May run on a dedicated small EC2 instance, a container-hosting service, or ephemeral runners.

CI-oriented commands (example GitHub Actions job):

```yaml
# Build and test job (simplified)
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker image
        run: docker build -t sundowns:ci .
      - name: Run tests
        run: docker run --rm sundowns:ci python manage.py test --verbosity=2
```

Architecture (testing):

CI Runner -> Build Image -> Test Container -> (DB/Redis: ephemeral managed containers or test doubles)

## 4. Production-Style Runtime

What it is:

- The runtime used for production-like environments: Docker images built with production settings, Gunicorn as the WSGI server, Nginx as reverse proxy, PostgreSQL as the persistent data store, and Redis for caching and Celery queues.

Why it's necessary:

- Ensures the runtime characteristics (process model, HTTP timeouts, database pooling) are consistent with production.

Key runtime components:

- Docker: packages the app and its dependencies into immutable images.
- Nginx: handles TLS termination, static file serving, and buffering.
- Gunicorn: runs multiple worker processes to serve Django WSGI app.
- PostgreSQL: production-grade RDBMS for persistent storage.
- Redis: fast in-memory store for caching, sessions, and Celery broker.

Production deployment command (example):

```bash
# From repo root on the target host
docker-compose -f docker-compose.prod.yml up -d --build
```

Architecture (production-style):

Internet -> Load Balancer / Nginx -> Gunicorn Workers -> Django -> PostgreSQL (RDS or self-hosted) + Redis

## 5. Reverse Proxy

Role in this project:

- Nginx sits in front of Gunicorn to:
  - Terminate TLS (HTTPS)
  - Serve static files efficiently
  - Buffer and protect upstream application from slow clients
  - Implement rate-limiting, HSTS, and other HTTP hardening

Typical Nginx → Gunicorn configuration (conceptual):

```
client -> nginx -> upstream (gunicorn:8000)
```

Why this stage is necessary:

- Offloads TLS and static delivery from application processes.
- Provides a stable public-facing surface for WAFs, logging, and observability.

Example minimal Nginx snippet (production):

```nginx
server {
    listen 80;
    server_name example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name example.com;

    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    location /static/ { root /srv/app; }
    location /media/ { root /srv/app; }

    location / {
        proxy_pass http://gunicorn:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 6. Environment Separation

Environments and differences:

- Development:
  - Config: local overrides, debug flags enabled, mount code with volumes.
  - Purpose: rapid iteration.
- Testing (staging/QA):
  - Config: production-like settings with test data, feature toggles exercised.
  - Purpose: automated tests and manual QA.
- Production:
  - Config: strict secrets, monitoring, scaling, backups, high availability.
  - Purpose: serve users with reliability and security.

Separation practices:

- Use environment variables for configuration (12-factor): do not hardcode secrets.
- Keep separate Docker Compose files: `docker-compose.dev.yml`, `docker-compose.prod.yml`.
- Use different databases or schemas for testing and production.

## 7. Health Monitoring

Health checks used in Sundowns:

Health checks used in Sundowns:

- `/health/` — lightweight root health check (optional). Returns `200 OK` with a small JSON payload like `{"status": "ok"}`. Useful for external load-balancer or uptime probes that do not need database verification.
- `/common/health/` — primary application health check. Performs Django setup and a quick DB verification; recommended for container or orchestration health probes.

Example probe (for load balancer / docker healthcheck):

```bash
# Container health check (recommended to use the application probe):
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8000/common/health/ || exit 1

# Lightweight external probe (optional):
curl -f https://example.com/health/
```

Why it's necessary:

- Quick indication of service availability and degraded downstream dependencies.
- Enables orchestrators and load balancers to remove unhealthy hosts automatically.

## 8. CI/CD Pipeline

Overview:

- We use GitHub Actions to run tests, build images, push images to a registry (Docker Hub or AWS ECR), and optionally deploy to EC2.

Typical pipeline stages:

1. Pull request: run linting, unit tests, and static analysis.
2. Merge to `main`/`master`: build production image, push to registry, trigger deploy workflow.
3. Deploy job: SSH into EC2 or call orchestration to pull and restart services.

Example simplified workflow steps:

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: docker run --rm sundowns:ci python manage.py test

  build-and-push:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v3
      - name: Build and push image
        run: |
          docker build -t ${{ secrets.REGISTRY }}/sundowns:${{ github.sha }} .
          docker push ${{ secrets.REGISTRY }}/sundowns:${{ github.sha }}

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to EC2
        run: ssh ubuntu@ec2-host 'cd /srv/sundowns && docker-compose -f docker-compose.prod.yml pull && docker-compose -f docker-compose.prod.yml up -d'
```

Security notes:

- Keep secrets in GitHub Secrets (registry creds, SSH keys).
- Use ephemeral deploy keys or GitHub Actions OIDC where possible instead of long-lived keys.

## 9. AWS EC2 Deployment

High-level steps:

1. Provision EC2 instance with required sizing.
2. Configure Security Group: allow port 22 (admin), 80/443 (http/https), and any internal ports required.
3. Install Docker and Docker Compose.
4. Clone repository and pull images or build on host.
5. Run `docker-compose -f docker-compose.prod.yml up -d --build`.

Commands (example):

```bash
# On the EC2 host
sudo apt update && sudo apt install -y docker.io docker-compose
sudo usermod -aG docker $USER
git clone git@github.com:your-org/sundowns.git
cd sundowns
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d --build
```

Operating model:

- Use a single EC2 instance for small deployments; for larger scale, use an autoscaling group behind a load balancer and a managed database (RDS).
- Use systemd or a watch script to ensure containers are restarted on host reboot.

## 10. HTTPS Deployment

Principles:

- Terminate TLS at Nginx.
- Redirect HTTP to HTTPS.
- Use modern TLS configuration and HSTS.

Obtaining certificates (Let\'s Encrypt example):

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d example.com -d www.example.com
```

TLS hardening checklist:

- Use only TLS 1.2 and TLS 1.3.
- Prefer ECDHE ciphers and AEAD suites (e.g., ECDHE-ECDSA-AES128-GCM-SHA256, TLS_AES_128_GCM_SHA256).
- Enable HSTS: `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`.
- Disable SSLv2/SSLv3 and weak ciphers.
- Enable OCSP stapling where possible.
- Use strong Diffie-Hellman parameters (if using DHE).

Example Nginx TLS settings snippet:

```nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_prefer_server_ciphers on;
ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:...';
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
ssl_session_timeout 1d;
ssl_session_cache shared:SSL:50m;
ssl_stapling on;
ssl_stapling_verify on;
```

## 11. Backups

Postgres backups:

- Use `pg_dump` for logical backups and database snapshots for point-in-time recovery when paired with WAL archiving.
- Automated backups can be uploaded to S3.

Backup example (logical backup with gzip):

```bash
PGHOST=localhost PGUSER=postgres PGDATABASE=sundowns
pg_dump -Fc -f /backups/sundowns_$(date +%F).dump
gzip /backups/sundowns_$(date +%F).dump
aws s3 cp /backups/sundowns_$(date +%F).dump.gz s3://my-bucket/sundowns/
```

Redis backups:

- Use RDB/AOF snapshots, and copy `dump.rdb` or `appendonly.aof` to durable storage.

Backup scheduling:

- Run backups daily and keep a 30–90 day retention depending on data use.
- Test restore procedures regularly in a staging environment.

## 12. Logging

Strategy:

- Aggregate application logs and system logs centrally.
- Ship container logs to a logging backend (CloudWatch, ELK, or a hosted logging provider).

What to collect:

- Gunicorn stdout/stderr (app logs)
- Nginx access and error logs
- System logs and Docker daemon logs
- Celery worker logs

Example: send Docker logs to CloudWatch via `awslogs` or run `fluent-bit` as a sidecar to send logs to a central store.

Log best practices:

- Structured JSON logs for easy querying.
- Use correlation IDs passed through HTTP headers to connect requests across services.
- Keep logs for an appropriate retention (30–90 days) and configure lifecycle policies.

## 13. Current Production Flow

Typical deployment flow used for Sundowns production:

1. Developer opens PR → automated tests run in GitHub Actions.
2. Merge to `main` triggers image build and push to registry.
3. Deploy job SSHes to EC2 and runs `docker-compose -f docker-compose.prod.yml pull` and `up -d`.
4. Load balancer health checks `/health/` and rotates traffic only to healthy hosts.
5. Centralized logs and alerts monitor errors and performance.

Flow diagram (simplified):

GitHub Actions -> Registry (ECR/DockerHub) -> EC2 Host -> Docker Compose -> Nginx -> Gunicorn -> Postgres/Redis

## 14. Lessons Learned

- Use production-like images early in CI to catch runtime issues caused by dev-only dependencies.
- Automate rollbacks: keep the previous image tag available to revert quickly.
- Keep health checks lightweight and deterministic — avoid expensive DB queries.
- Logging and structured logs are essential for debugging production issues quickly.
- Encrypt and rotate keys: never keep long-lived private keys on instances.
- Test restore procedures for backups — a backup is only valuable if it can be restored.

Operational examples encountered during rollout:

- Issue: failing requests due to missing `X-Forwarded-Proto` — fix: ensure Nginx sets forwarding headers and Django's `SECURE_PROXY_SSL_HEADER` is configured.
- Issue: long cold starts on workers — fix: pre-warm caches in staging and tune Gunicorn worker count.

## 15. Future Improvements

- Move database to RDS for managed backups and automated multi-AZ failover.
- Use an autoscaling group + Application Load Balancer for zero-downtime deploys.
- Adopt OIDC or ephemeral credentials for GitHub Actions to EC2 deployments.
- Migrate logs/metrics to a SaaS observability solution for faster triage.
- Introduce feature flags for safer rollouts and A/B experiments.

---

Appendix — Useful commands summary

```bash
# Build prod images locally
docker build -t sundowns:prod -f Dockerfile .

# Start production-style stack
docker-compose -f docker-compose.prod.yml up -d --build

# Check health endpoint
curl -f https://example.com/health/ || echo "unhealthy"

# Create DB backup
pg_dump -Fc -f /backups/sundowns_$(date +%F).dump
```
