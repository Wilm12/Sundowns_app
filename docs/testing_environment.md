# Testing Environment

## Django Test Setup

### Running Tests

Execute tests inside the Docker container:
```bash
docker compose exec web python manage.py test --settings=sundowns_app.settings.test
```

### Test Settings Configuration

Ensure your test settings file uses Docker service names for database connectivity:

```python
# sundowns_app/settings/test.py

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'sundowns_test_db',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'db',  # Use Docker service name, not 'localhost'
        'PORT': '5432',
    }
}

# Use secure secret key (at least 32 characters)
SECRET_KEY = "test-secret-key-for-sundowns-project-at-least-32-chars"
```

### Expected Test Results

Upon successful configuration:
```
Ran 3 tests in 0.087s

OK
```

## Dependencies

Ensure all required packages are installed in `requirements.txt`:

```
qrcode[pil]
# ... other dependencies
```

If missing, install them:
```bash
docker compose run --rm web pip install "qrcode[pil]"
docker compose build web
docker compose up -d
```

## Common Issues

- **Database Connection Errors**: Verify `HOST = "db"` in test settings (not `localhost`)
- **Missing Python Modules**: Install via pip and add to `requirements.txt`
- **Security Warnings**: Use secret keys with sufficient length (32+ characters)
