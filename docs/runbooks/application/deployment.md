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


# Sundowns WPA Production Runbook

## Standard Deployment

### 1. Connect to Production

```bash
ssh ubuntu@<server>
cd ~/Sundowns_app
```

### 2. Optional Database Backup

For significant releases:

```bash
docker compose \
  --env-file .env.prod \
  -f docker-compose.prod.yml \
  exec db pg_dump -U postgres sundowns_prod > backup_$(date +%F).sql
```

### 3. Deploy

```bash
./deploy.sh
```

The deployment script performs:

* Pull latest code (if included)
* Rebuild containers
* Start/update services
* Apply migrations
* Collect static files

### 4. Verify

Open:

```text
https://sundownswpa.duckdns.org
https://sundownswpa.duckdns.org/dashboard/
https://sundownswpa.duckdns.org/rewards/
https://sundownswpa.duckdns.org/notifications/
https://sundownswpa.duckdns.org/analytics/
```

### 5. Check Logs

```bash
docker compose logs web --tail=100
docker compose logs nginx --tail=100
```

---

# Incident Response

## Application Error

Check:

```bash
docker compose logs web --tail=200
```

## Database Error

Check:

```bash
docker compose logs db --tail=200
```

Verify migrations:

```bash
docker compose exec web python manage.py showmigrations
```

## Service Down

Check:

```bash
docker compose ps
```

Restart:

```bash
docker compose restart
```

---

# Rollback Procedure

## Code Rollback

```bash
git log --oneline
git checkout <previous_commit>
./deploy.sh
```

## Database Recovery

Restore from backup if required.

---

# Monitoring Checks

Verify:

* Homepage loads
* Login works
* Dashboard loads
* Rewards loads
* Notifications loads
* Analytics loads

Review:

```bash
docker stats
```

and later:

* Prometheus dashboards
* Grafana dashboards
* Alert notifications

