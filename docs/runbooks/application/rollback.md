# Rollback Runbook

## Purpose

This document defines the rollback procedures for the BranchRoute production environment.

Rollback procedures are used when:

* A deployment introduces critical bugs.
* A migration causes unexpected behaviour.
* A release breaks core platform functionality.
* Production services become unstable after deployment.

---

# Rollback Levels

The platform supports three rollback levels:

1. Application Rollback
2. Deployment Rollback
3. Disaster Recovery Rollback

---

# Level 1 — Application Rollback

## When to Use

Use when:

* A code deployment introduced a bug.
* Database schema remains compatible.
* No database recovery is required.

Examples:

* Broken dashboard page
* Broken rewards page
* Notification UI issue
* Incorrect business logic

---

## Procedure

### Step 1

Identify previous stable commit:

```bash
git log --oneline
```

### Step 2

Checkout previous version:

```bash
git checkout <stable_commit_hash>
```

### Step 3

Deploy:

```bash
./deploy.sh
```

### Step 4

Verify:

* Homepage loads
* Login works
* Dashboard works
* Rewards page works
* Notifications page works

---

## Expected Recovery Time

15–30 minutes

---

# Level 2 — Deployment Rollback

## When to Use

Use when:

* Application rollback alone is insufficient.
* New migrations were applied.
* Current code is incompatible with production operations.

Examples:

* Sprint deployment causes production instability.
* New feature breaks critical workflows.
* Reward redemption workflow fails.

---

## Procedure

### Step 1

Review migration status:

```bash
docker compose exec web python manage.py showmigrations
```

### Step 2

Identify last known stable release.

### Step 3

Checkout stable commit:

```bash
git checkout <stable_commit_hash>
```

### Step 4

Deploy:

```bash
./deploy.sh
```

### Step 5

Verify:

```bash
docker compose exec web python manage.py check
```

Verify platform functionality.

---

## Important

Avoid rolling back database migrations unless absolutely necessary.

The preferred approach is:

* Roll back application code.
* Keep database schema.
* Deploy a hotfix.

---

## Expected Recovery Time

30–60 minutes

---

# Level 3 — Disaster Recovery Rollback

## When to Use

Use when:

* Production database becomes corrupted.
* Critical data loss occurs.
* Infrastructure failure occurs.
* EC2 instance is lost.

Examples:

* Failed migration damages data.
* PostgreSQL corruption.
* Accidental data deletion.
* AWS infrastructure failure.

---

## Procedure

### Step 1

Provision replacement infrastructure.

### Step 2

Clone repository:

```bash
git clone <repository>
```

### Step 3

Restore production environment variables.

Required:

```text
.env.prod
```

### Step 4

Deploy application:

```bash
./deploy.sh
```

### Step 5

Restore database backup:

```bash
cat backup.sql | docker compose exec -T db psql -U postgres sundowns_prod
```

### Step 6

Verify migrations:

```bash
docker compose exec web python manage.py showmigrations
```

All migrations should show:

```text
[X]
```

### Step 7

Perform smoke testing:

* Login
* Memberships
* Ticket booking
* Rewards
* Notifications
* Analytics

---

## Expected Recovery Time

1–2 hours

---

# Post-Rollback Verification Checklist

After any rollback:

## Infrastructure

* EC2 healthy
* Docker containers running
* PostgreSQL running
* Redis running
* Nginx running

```bash
docker compose ps
```

---

## Application

Verify:

* Homepage
* Login
* Dashboard
* Memberships
* Ticketing
* Rewards
* Notifications
* Analytics

---

## Database

Verify:

```bash
docker compose exec web python manage.py showmigrations
```

Verify:

```bash
docker compose exec db psql -U postgres sundowns_prod
```

Then:

```sql
\dt
```

Expected:

* users_user
* membership_membership
* ticketing_ticket
* points_*
* rewards_*
* notifications_*
* promotions_*

---

# Current Rollback Capability

Current platform status:

✅ Code rollback supported

✅ Docker deployment rollback supported

✅ Database backup and restore supported

⚠ Automated backup storage not yet implemented

⚠ Automated rollback not yet implemented

⚠ Blue/Green deployments not yet implemented

---

# Future Improvements

Planned:

* Automated PostgreSQL backups
* AWS S3 backup storage
* Backup retention policies
* Prometheus monitoring
* Grafana dashboards
* Blue/Green deployment strategy
* Canary deployments
* Automated rollback triggers

