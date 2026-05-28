# AWS EC2 Deployment Plan

## Target Architecture

```text
User Browser
→ Public IP / Domain
→ EC2 Security Group
→ Nginx container
→ Gunicorn web container
→ Django App
→ PostgreSQL container
→ Redis container
