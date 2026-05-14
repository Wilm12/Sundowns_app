# Testing Environment

## Django Test Setup

### Running Tests

Execute tests inside the Docker container:

```bash
docker compose exec web python manage.py test --settings=sundowns_app.settings.test
```

---

## Testing Architecture

The project uses:

- Django TestCase
- DRF APITestCase
- PostgreSQL test database
- Docker-based test execution

Tests are executed inside the Docker web container to ensure environment consistency with development and staging.

---

## Frontend vs API Testing

The project separates:

- frontend/template routes (`frontend_urls.py`)
- API/DRF routes (`urls.py`)

Tests must target the correct route type depending on whether the feature is frontend-rendered or API-based.

---

## Current Test Coverage

Implemented automated tests:

- Registration with required branch
- JWT login/token authentication
- Successful payment activates membership
- Inactive membership cannot book tickets
- Successful ticket booking redirects to transport prompt
- Transport prompt redirect logic
- QR verification success flow
- QR verification permission protection
- Duplicate ticket prevention
- Transport capacity enforcement
- Transport-match consistency validation

---

## Test Settings Configuration

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

---

## Expected Test Results

Upon successful configuration:

```text
Test suite should complete successfully with all tests passing.

OK
```

---

## Dependencies

Ensure all required packages are installed in `requirements.txt`:

```text
qrcode[pil]
# ... other dependencies
```

If missing, install them:

```bash
docker compose run --rm web pip install "qrcode[pil]"
docker compose build web
docker compose up -d
```

---

## Common Issues

- **Database Connection Errors**  
  Verify `HOST = "db"` in test settings (not `localhost`)

- **Missing Python Modules**  
  Install via pip and add to `requirements.txt`

- **Security Warnings**  
  Use secret keys with sufficient length (32+ characters)

---

## Registration Test Rule

Registration requires a branch.

Any registration test must:

- create a `Branch` object
- include the branch ID in the payload
- assert that the created user belongs to that branch

---

## Login Test

The login test verifies that a registered user can authenticate and receive JWT access and refresh tokens.

---

## Ticket Booking Membership Rule

Ticket booking requires an active membership.

Tests must verify that users with inactive memberships cannot successfully create tickets.

---

## Ticket Booking Flow

1. User must have an active membership.
2. Ticket is created after successful booking.
3. User is redirected to a transport prompt page.
4. Choosing `"Yes"` redirects to transport options for the selected match.
5. Choosing `"No"` redirects to the user's tickets page.

---

## QR Ticket Verification

QR ticket verification is restricted to admin users.

Verification flow:

1. Member books a ticket.
2. Ticket is created with status `"booked"`.
3. Admin submits the QR code to the verification endpoint.
4. Ticket status changes from `"booked"` to `"used"`.

Test coverage verifies:

- Admin users can verify valid QR codes.
- Verified tickets are updated to `"used"`.
- Verification endpoint returns HTTP 200 on success.
- Non-admin users are blocked from verification.

---

## Duplicate Ticket Booking

A user cannot book more than one ticket for the same match.

Test coverage verifies:

- First ticket exists for the user and match.
- Second booking attempt is blocked.
- Ticket count remains `1`.

---

## Transport Capacity Rule

Transport bookings cannot exceed available seats.

Test coverage verifies:

- A transport option with full capacity blocks additional bookings.
- No extra `TransportBooking` is created.
- Available seats remain `0`.

---

## Transport Match Consistency

Transport bookings must belong to the same match as the ticket.

Test coverage verifies:

- Tickets cannot book transport assigned to a different match.
- Invalid transport bookings are blocked.
- No `TransportBooking` record is created for mismatched matches.

---

## CI/CD Readiness

The current automated test suite is designed to run inside Docker and is suitable for future CI/CD integration using GitHub Actions or other pipeline tools.
