# Observability & SRE Roadmap

**Project:** Sundowns WPA  
**Status:** Active  
**Scope:** Monitoring, observability, operational engineering, and reliability engineering

## 1. Purpose

This roadmap defines the progression from basic infrastructure monitoring toward production-grade observability, operational maturity, SRE practices, and controlled failure testing.

The objective is to establish the ability to:

> **detect -> understand -> respond -> recover -> measure -> improve**

## 2. Phase 3: Monitoring & Observability

| ID | Area | Status |
| --- | --- | --- |
| 3.1 | Infrastructure Monitoring | Completed |
| 3.2 | Application Monitoring | Completed |
| 3.3 | PostgreSQL Monitoring | Completed |
| 3.4 | Redis Monitoring | Next |
| 3.5 | Nginx Monitoring | Planned |
| 3.6 | Container Monitoring | Planned |
| 3.7 | External Monitoring | Planned |
| 3.8 | Centralized Logging | Planned |
| 3.9 | Synthetic Monitoring | Planned |
| 3.10 | Business Observability | Planned |

### 3.1 Infrastructure Monitoring

**Status: Completed**

Monitor the infrastructure supporting Sundowns WPA:

- CPU
- Memory
- Disk and filesystem
- Network
- Host availability

### 3.2 Application Monitoring

**Status: Completed**

Monitor Django runtime behaviour, including:

- Request rate
- Response time
- Errors and exceptions
- Database queries
- Cache behaviour

A Grafana application dashboard has been established.

### 3.3 PostgreSQL Monitoring

**Status: Completed**

Monitor:

- Connections
- Transactions
- Locks and deadlocks
- Cache performance
- Database health
- Query behaviour

A PostgreSQL dashboard has been established.

### 3.4 Redis Monitoring

**Status: Next**

Introduce Redis-specific observability using `redis-exporter`.

Monitor:

- Memory usage
- Connected clients
- Cache hits and misses
- Evictions
- Redis availability
- Command activity

The objective is to understand Redis as an operational dependency, not simply confirm that its container is running.

### 3.5 Nginx Monitoring

Introduce Nginx-specific monitoring for:

- Requests and connections
- Latency
- HTTP 4xx and 5xx responses
- Upstream behaviour

### 3.6 Container Monitoring

Introduce container-level monitoring using cAdvisor for:

- Container CPU and memory
- Container restarts
- Filesystem usage
- Network activity

This provides visibility between host-level infrastructure metrics and individual application services.

### 3.7 External Monitoring

Introduce black-box monitoring for:

- Website availability
- DNS
- TLS/SSL
- TCP connectivity
- External latency

This represents the platform from the perspective of an external user rather than the server itself.

### 3.8 Centralized Logging

Introduce centralized log collection using Loki and Promtail. Collect logs from:

- Django
- Gunicorn
- Nginx
- PostgreSQL
- Redis
- Docker
- Linux/system services

The goal is to correlate metrics and logs during incidents.

### 3.9 Synthetic Monitoring

Create synthetic business transactions that periodically test critical workflows:

```text
login
registration
payment
ticket booking
membership renewal
```

This detects situations where infrastructure appears healthy but an important user journey is broken.

### 3.10 Business Observability

Move from technical monitoring to monitoring the health of the supporter platform.

#### Supporters

- Total supporters
- Active and inactive supporters
- New supporters per day

#### Branches

- Active branches
- Branch growth
- Attendance
- Participation

#### Memberships

- Active memberships
- Renewals
- Expirations
- Conversion rates

#### Tickets

- Tickets sold
- Booking success rate
- Booking failures
- Occupancy

#### Payments

- Payment success and failure rates
- Revenue per day

#### Matches

- Attendance
- Transport utilisation
- Supporter participation

This should eventually become an **Sundowns WPA Executive/Business Dashboard**.

## 3. Phase 4: Operational Engineering

| ID | Area | Status |
| --- | --- | --- |
| 4.1 | Incident Management | Planned |
| 4.2 | Disaster Recovery | Planned |
| 4.3 | Backup Verification | Planned |
| 4.4 | Capacity Planning | Planned |
| 4.5 | SLOs & Error Budgets | Planned |
| 4.6 | Chaos Engineering | Planned |

### 4.1 Incident Management

Establish:

- Severity levels
- Incident procedures
- Runbooks
- Escalation procedures
- Incident documentation
- Postmortems

Existing intentional failure exercises will feed directly into this section.

### 4.2 Disaster Recovery

Test recovery from:

```text
PostgreSQL loss
Redis loss
Nginx loss
Django/application failure
EC2 failure
SSL expiry
DNS failure
```

For each scenario, document:

```text
failure
-> detection
-> diagnosis
-> recovery
-> validation
-> documentation
```

### 4.3 Backup Verification

Move beyond simply creating backups. Test:

```text
backup
-> restore
-> validation
-> application verification
```

The objective is to prove that backups are recoverable.

### 4.4 Capacity Planning

Track and forecast:

- CPU growth
- Memory requirements
- Storage growth
- Database growth
- Traffic growth
- Container resource consumption

The objective is to identify scaling requirements before capacity becomes an incident.

### 4.5 SLOs & Error Budgets

Define service reliability objectives for availability, latency, and errors.

Initial areas include:

- **Availability:** target 99.9%
- **Latency:** for example, 95th percentile response time
- **Errors:** acceptable application error rates

These objectives establish an error budget and support operational decisions based on measurable reliability. SLA, SLO, and SLI concepts will be documented here and connected to monitoring data.

### 4.6 Chaos Engineering

Deliberately introduce controlled failures.

#### Infrastructure

```text
stop Nginx
stop PostgreSQL
stop Redis
kill Django
stop Prometheus
stop Grafana
```

#### Network

```text
block Redis
block PostgreSQL
introduce latency
drop packets
```

#### DNS/TLS

```text
break DuckDNS
break DNS resolution
simulate certificate expiry
```

#### Data and host

```text
simulate PostgreSQL failure
restore backup
verify recovery
terminate EC2
recover platform
```

Every experiment follows:

```text
BREAK
  ↓
DETECT
  ↓
ALERT
  ↓
DIAGNOSE
  ↓
RECOVER
  ↓
VALIDATE
  ↓
DOCUMENT
  ↓
POSTMORTEM
```

## 4. Execution Strategy

The roadmap is an engineering progression rather than a simple numerical checklist:

```text
3.1 -> 3.2 -> 3.3 -> 3.4 -> 3.5 -> 3.6 -> 3.7 -> 3.8
                                      |
                                    4.1 -> 4.2
                                      |
                                  3.9 -> 3.10
                                      |
                                  4.5 -> 4.6
```

Chaos engineering and reliability objectives become more valuable once the platform has enough observability and operational process to detect and understand failures.

## 5. Current Position

### Completed

```text
3.1 Infrastructure Monitoring
3.2 Application Monitoring
3.3 PostgreSQL Monitoring
```

### Next

```text
3.4 Redis Monitoring
```

### Later

```text
3.5 Nginx Monitoring
3.6 Container Monitoring
3.7 External Monitoring
3.8 Centralized Logging
4.1 Incident Management
4.2 Disaster Recovery
3.9 Synthetic Monitoring
3.10 Business Observability
4.5 SLOs & Error Budgets
4.6 Chaos Engineering
```

This document is the baseline roadmap for observability and SRE work so the execution order remains stable when project work resumes.
