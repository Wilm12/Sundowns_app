# Deployment Runbook

Known recovery pitfalls and production deployment guidance for the application.

# Known Recovery Pitfalls

## Pitfall 1: Starting Production With Development Compose Commands

Symptoms:

- 502 Bad Gateway
- Health endpoint unavailable
- Web container running but application inaccessible

Cause:

Using:

```bash
docker compose up -d web
```

instead of the production compose configuration.

Recovery:

Restart the stack using:

```bash
docker compose --env-file .env.prod \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  up -d --build
```

Prevention:

Always use production compose files for production operations.
