# Points System

## Events

- Membership Payment = +50
- Ticket Booking = +10
- Transport Booking = +5

## Architecture

User
 └── PointsAccount
       └── PointsTransaction

## Rules

Points are awarded only on business-event transitions.

- Membership:
    - not successful -> successful
- Ticket:
    - not booked -> booked
- Transport:
    - not booked -> booked

## Duplicate Prevention

Status transition detection prevents duplicate awards.

## Backfill

Legacy users can be provisioned using:

```bash
python manage.py backfill_points_accounts
```
