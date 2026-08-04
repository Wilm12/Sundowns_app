# Migrations

Guidelines for managing database migrations and schema changes safely.

Symptoms:
- relation does not exist
- dashboard returns 500

Diagnosis:
showmigrations

Resolution:
python manage.py migrate

Verification:
showmigrations
