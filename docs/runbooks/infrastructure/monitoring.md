# Monitoring Runbook

## Purpose

This document describes the monitoring stack for BranchRoute.

The monitoring stack provides:

* Infrastructure visibility
* Resource utilisation monitoring
* Performance monitoring
* Early warning of system failures
* Operational troubleshooting support

---

# Monitoring Architecture

```text
EC2 Instance
    |
    |-- Node Exporter
    |
    |-- Prometheus
    |
    |-- Grafana
```

Data Flow:

```text
Node Exporter
      ↓
 Prometheus
      ↓
   Grafana
```

---

# Monitoring Components

## Node Exporter

Purpose:

Collects operating system and infrastructure metrics.

Metrics include:

* CPU usage
* Memory usage
* Disk usage
* Disk I/O
* Network traffic
* System load
* Filesystem statistics

Container:

```text
node-exporter
```

Port:

```text
9100
```

---

## Prometheus

Purpose:

Collects and stores monitoring metrics.

Container:

```text
prometheus
```

Port:

```text
9090
```

Configuration:

```text
monitoring/prometheus/prometheus.yml
```

Current scrape targets:

```text
prometheus:9090
node-exporter:9100
```

URL:

```text
http://SERVER_IP:9090
```

Verification:

Status → Targets

Expected:

```text
prometheus = UP
node-exporter = UP
```

---

## Grafana

Purpose:

Visualisation and dashboarding.

Container:

```text
grafana
```

Port:

```text
3000
```

URL:

```text
http://SERVER_IP:3000
```

Default login:

```text
admin
```

Password:

Stored securely by administrator.

---

# Data Sources

## Prometheus

Datasource Type:

```text
Prometheus
```

Datasource URL:

```text
http://prometheus:9090
```

Verification:

```text
Save & Test
```

Expected:

```text
Successfully queried Prometheus
```

---

# Installed Dashboards

## Node Exporter Full

Dashboard ID:

```text
1860
```

Purpose:

Infrastructure overview dashboard.

Provides:

* CPU utilisation
* Memory utilisation
* Disk utilisation
* Network traffic
* Filesystem usage
* Load averages

---

# Open Ports

## Prometheus

```text
9090
```

Current Use:

Monitoring administration

Security Group:

Enabled

Future State:

Restrict public access.

---

## Grafana

```text
3000
```

Current Use:

Monitoring administration

Security Group:

Enabled

Future State:

Serve through Nginx with HTTPS.

---

# Operational Checks

## Verify Containers

```bash
docker compose ps
```

Expected:

```text
prometheus
grafana
node-exporter
```

Status:

```text
Up
```

---

## Verify Prometheus

```bash
curl http://localhost:9090/-/healthy
```

Expected:

```text
Prometheus is Healthy
```

---

## Verify Node Exporter

```bash
curl http://localhost:9100/metrics
```

Expected:

Large metrics output.

---

## Verify Grafana

Open:

```text
http://SERVER_IP:3000
```

Expected:

Grafana login page.

---

# Future Monitoring Roadmap

## Phase 1 (Completed)

* Node Exporter
* Prometheus
* Grafana
* Infrastructure dashboards

---

## Phase 2

* Django Prometheus instrumentation
* Application metrics
* Request latency monitoring
* Error monitoring
* Database metrics

---

## Phase 3

* Alerting
* Email notifications
* Incident thresholds
* Service health monitoring

---

## Phase 4

* Business metrics
* Membership growth dashboards
* Ticket booking metrics
* Branch engagement metrics
* Loyalty and rewards metrics
* Campaign performance metrics

---

# Last Updated

Sprint 16 – Monitoring Foundation

