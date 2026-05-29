
````md
# CI/CD Pipeline

## Purpose

This document explains the CI/CD flow for the Sundowns WPA Platform.

The goal of the pipeline is to reduce manual deployment work and make production updates more repeatable, visible, and reliable.

Before CI/CD, deployment required manual steps:

```text
Commit code
→ Push to GitHub
→ SSH into EC2
→ git pull
→ rebuild containers
→ restart services
→ check health manually
````

After CI/CD, the deployment flow becomes:

```text
Push to master
→ GitHub Actions starts
→ SSH into EC2
→ pull latest code
→ rebuild Docker containers
→ restart production stack
→ verify containers
```

---

## Current CI/CD Status

The project currently has:

```text
CI  ✅
CD  ✅
```

CI validates the project before deployment.

CD deploys the latest code to the EC2 server automatically.

---

## CI: Continuous Integration

Continuous Integration checks whether the application is safe to merge and deploy.

The CI workflow validates:

* Python dependencies
* Django system checks
* database migrations
* automated tests
* Docker image build

This helps catch problems before they reach the production server.

Typical CI flow:

```text
Developer pushes code
→ GitHub Actions runs tests
→ Docker image build is validated
→ workflow passes or fails
```

---

## CD: Continuous Deployment

Continuous Deployment updates the live EC2 server after code is pushed to the deployment branch.

The CD workflow uses GitHub Actions to connect to the EC2 server through SSH.

Deployment flow:

```text
GitHub Actions
→ SSH into EC2
→ cd ~/Sundowns_app
→ verify .env.prod exists
→ git pull origin master
→ docker compose up -d --build
→ docker ps
```

---

## GitHub Secrets

The deployment workflow uses GitHub repository secrets.

These secrets are not stored in source code.

Required secrets:

| Secret Name   | Purpose                                         |
| ------------- | ----------------------------------------------- |
| `EC2_HOST`    | Public hostname or IP address of the EC2 server |
| `EC2_USER`    | Linux user used for SSH deployment              |
| `EC2_SSH_KEY` | Private SSH key used by GitHub Actions          |

Example:

```text
EC2_HOST=sundownswpa.duckdns.org
EC2_USER=root
EC2_SSH_KEY=private deployment key
```

The private key is stored only in GitHub Secrets and is never committed to Git.

---

## Deployment SSH Key

A dedicated SSH key was created for GitHub Actions.

On EC2:

```bash
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/github_actions
```

This created:

```text
~/.ssh/github_actions      # private key
~/.ssh/github_actions.pub  # public key
```

The public key was added to:

```text
~/.ssh/authorized_keys
```

The private key was stored in GitHub Actions Secrets as:

```text
EC2_SSH_KEY
```

This allows GitHub Actions to SSH into EC2 during deployment.

---

## Deployment Workflow

The deployment workflow lives in:

```text
.github/workflows/deploy.yml
```

Example deployment workflow:

```yaml
name: Deploy to EC2

on:
  push:
    branches:
      - master

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Deploy over SSH
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ${{ secrets.EC2_USER }}
          key: ${{ secrets.EC2_SSH_KEY }}
          script: |
            cd ~/Sundowns_app

            test -f .env.prod || { echo ".env.prod missing"; exit 1; }

            git pull origin master

            docker compose \
              -f docker-compose.yml \
              -f docker-compose.prod.yml \
              up -d --build

            docker ps
```

---

## Environment Protection

The production environment file is intentionally not committed to Git:

```text
.env.prod
```

Instead, Git tracks only:

```text
.env.prod.example
```

This prevents secrets from being overwritten or exposed during deployment.

The deploy script includes this guard:

```bash
test -f .env.prod || { echo ".env.prod missing"; exit 1; }
```

This prevents deployment from continuing if the server environment file is missing.

This is important because the application requires `.env.prod` for:

* Django secret key
* database credentials
* allowed hosts
* Redis connection
* HTTPS settings

---

## Security Group Issue Encountered

Initial deployment failed with:

```text
dial tcp 50.16.120.223:22: i/o timeout
```

Root cause:

```text
GitHub Actions runners could not reach EC2 port 22.
```

The EC2 security group originally allowed SSH only from the local laptop IP.

GitHub Actions runs from GitHub-managed IP addresses, so the SSH request came from a different source.

Temporary fix:

```text
Allow SSH port 22 from 0.0.0.0/0
```

This allowed GitHub Actions to connect and complete deployment.

Long-term improvement:

* create a dedicated deploy user
* restrict SSH access
* use AWS Systems Manager Session Manager
* use a self-hosted GitHub Actions runner
* use GitHub OIDC with AWS deployment tooling

---

## Deployment Verification

After a successful deployment, verify the server state:

```bash
cd ~/Sundowns_app
git log --oneline -3
docker ps
```

Expected containers:

```text
nginx   healthy
web     healthy
db      running
redis   running
```

Health endpoint:

```text
https://sundownswpa.duckdns.org/common/health/
```

Expected response:

```text
healthy
```

or:

```json
{
  "status": "healthy",
  "database": "connected"
}
```

depending on whether the request is handled by Nginx or Django.

---

## Current Production Flow

```text
Developer
→ git push origin master
→ GitHub Actions
→ SSH to EC2
→ git pull origin master
→ Docker Compose rebuild
→ Nginx + Gunicorn + Django restart
→ PostgreSQL and Redis remain running
→ Public HTTPS app updated
```

---

## What This Solves

The CI/CD pipeline solves several manual deployment problems:

* forgetting to pull latest code on EC2
* stale containers running old code
* manual restart mistakes
* inconsistent deployment commands
* lack of deployment visibility
* repeated SSH deployment work

It also creates a visible deployment history in GitHub Actions.

---

## Current Limitations

The current CD setup is functional but still simple.

Limitations:

* deploys directly from GitHub Actions to EC2 over SSH
* uses root user for deployment
* SSH access was temporarily opened broadly for GitHub Actions
* no automatic rollback yet
* no blue/green deployment
* no separate staging deployment job yet
* no image registry promotion flow yet

---

## Future Improvements

Recommended next improvements:

1. Create a non-root `deploy` user
2. Restrict SSH access
3. Add post-deployment health check
4. Fail deployment if health check fails
5. Add rollback strategy
6. Use Docker image registry
7. Add separate staging and production jobs
8. Add GitHub Environments with manual approval
9. Use AWS SSM or OIDC-based deployment
10. Add Slack/email deployment notifications

---

## Lessons Learned

* CI and CD are different stages.
* Passing tests does not automatically mean production is updated.
* A real CD pipeline must update the target runtime environment.
* Server-only `.env.prod` files must be protected from Git.
* GitHub Actions runners need network access to the deployment target.
* SSH keys should be dedicated to deployment, not reused from personal access.
* Deployment automation reduces manual mistakes.
* Health checks are essential after deployment.
* Production deployment is a coordination problem across Git, CI/CD, Docker, Linux, networking, secrets, and application runtime.

````

Then commit:

```bash
git add docs/ci-cd.md
git commit -m "Document CI/CD deployment flow"
git push origin master
````

