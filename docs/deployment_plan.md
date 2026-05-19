# Deployment Plan

## Production Docker Compose

The production deployment for Sundowns uses `docker-compose.prod.yml` with a minimal three-service stack:

- `db`: PostgreSQL database
- `web`: Django application served by Gunicorn
- `nginx`: reverse proxy and static/media file delivery

### Production startup

```bash
docker compose -f docker-compose.prod.yml up -d
```

### Required environment file

Ensure `.env.prod` includes the production database credentials and any other environment settings used by Django.

### Production service details

- `db` reads PostgreSQL connection settings from `.env.prod`
- `web` runs Gunicorn on port `8000`
- `nginx` listens on port `80` and forwards traffic to `web`
- Static files are mounted from `./staticfiles`
- Media files are mounted from `./media`

### Notes

- The file uses consistent 2-space indentation.
- The compose file should include a top-level `version` declaration for compatibility with Docker Compose tooling.
