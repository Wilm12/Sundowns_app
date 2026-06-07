# Application Incident Log

Track application incidents, errors, and post-incident analysis in this section.

## 2026-06-07 - Web Container Stopped During Incident Response Exercise

### Type

Simulated Incident / Game Day Exercise

### Detection

The web container was intentionally stopped to practice incident response.

Command used:

```bash
docker stop sundowns_app-web-1
```

The incident was detected by checking container status and application availability.

### Symptoms

- Web container stopped running
- Application became unavailable
- Health endpoint could not return the expected healthy response
- Nginx remained running but could not successfully serve the application

### Impact

This was a controlled exercise.

Potential user impact if this occurred unexpectedly:

- Application unavailable
- Login unavailable
- Dashboard unavailable
- Membership workflows unavailable
- Ticket booking unavailable
- Transport booking unavailable
- Payments unavailable

### Root Cause

The web container was intentionally stopped as part of an incident response simulation.

### Resolution

The intended recovery was to restart the production web service.

During recovery, an incorrect compose command was later used, causing a separate real incident.

### Verification

Verification steps included:

```bash
docker ps

curl https://sundownswpa.duckdns.org/common/health/
```

Expected:

```json
{
  "status": "healthy",
  "database": "connected"
}
```

### Lessons Learned

- A stopped web container makes the application unavailable even when other services remain running.
- Incident response should begin with checking container status.
- Recovery commands must be environment-specific.
- Simulated incidents are valuable because they expose weaknesses in operational procedures.
- Recovery actions themselves can introduce incidents.

### Runbook Updates

Application → Deployment Runbook

---

## 2026-06-07 - 502 Bad Gateway During Recovery

### Type

Real Incident

### Detection

While performing a recovery exercise after intentionally stopping the web container, the application health endpoint returned 502 Bad Gateway.

### Symptoms

- Users received a 502 Bad Gateway page from Nginx
- Health endpoint failed
- Web container appeared to be running
- Nginx container remained healthy

### Impact

Entire application unavailable.

Affected:

- Authentication
- Memberships
- Payments
- Matches
- Ticketing
- Transport
- Dashboard

### Root Cause

The web service was restarted using:

```bash
docker compose up -d web
```

instead of the production compose configuration.

This started the application using the incorrect compose configuration and caused Nginx upstream failures.

### Resolution

The production stack was restarted using:

```bash
docker compose --env-file .env.prod \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  up -d --build
```

### Verification

- docker ps
- Health endpoint returned healthy
- Application pages loaded successfully

### Lessons Learned

- A running container does not guarantee a healthy user experience.
- Production recovery procedures must be documented.
- Development and production compose commands must not be mixed.
- Recovery exercises can expose weaknesses in operational procedures.

### Runbook Updates

Application → Deployment Runbook

docker stop sundowns_app-web-1