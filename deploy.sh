#!/bin/bash

set -e

echo "Pulling latest code..."
git pull origin master

echo "Building containers..."
docker compose \
  --env-file .env.prod \
  -f docker-compose.prod.yml \
  up -d --build

echo "Running migrations..."
docker compose \
  --env-file .env.prod \
  -f docker-compose.prod.yml \
  exec web python manage.py migrate

echo "Collecting static files..."
docker compose \
  --env-file .env.prod \
  -f docker-compose.prod.yml \
  exec web python manage.py collectstatic --noinput

echo "Deployment complete."
