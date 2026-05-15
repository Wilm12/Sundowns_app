# Sundowns WPA System Architecture

## Overview

Sundowns WPA is a Django-based membership platform for supporters. The system manages users, branches, memberships, payments, match tickets, QR verification, and transport bookings.

The project follows a modular monolith architecture with clear separation between frontend template routes and DRF API routes.

---

## Core Stack

- Django
- Django REST Framework
- PostgreSQL
- Docker
- Docker Compose
- Redis
- Celery foundations
- Tailwind CSS
- JWT authentication
- Django template frontend

---

## High-Level Architecture

```text
Browser
  |
  | HTTP requests
  v
Django Application
  |
  |----------------------------
  | Frontend Template Routes
  | DRF API Routes
  | Business Logic
  |----------------------------
  |
  v
PostgreSQL Database

Redis + Celery
  |
  v
Future background tasks
Routing Architecture

The project separates frontend routes from API routes.

frontend_urls.py  -> Django template pages
urls.py           -> DRF/API endpoints

Example:

matches/frontend_urls.py  -> /matches/
matches/urls.py           -> /api/matches/

ticketing/frontend_urls.py -> /tickets/
ticketing/urls.py          -> /api/tickets/

This prevents route conflicts and makes testing clearer.

Main Modules
Authentication

Handles:

user registration
login
JWT authentication
role-based access
admin/member permissions
Users

Contains the custom user model.

Important user fields:

username
email
role
branch
branch change tracking

Business rule:

Every user must belong to a branch.
Branches

Branches represent supporter groups.

Branches connect to:

users
memberships indirectly
transport
dashboard identity
Membership

Membership controls access to ticket booking.

Flow:

Register
→ Membership created inactive
→ Payment completed
→ Membership activated

Ticket booking requires:

membership.status == active
Payments

Payments activate memberships.

Flow:

User pays membership fee
→ Payment status becomes successful
→ Membership status becomes active
Matches

Matches represent upcoming fixtures.

Users can:

view matches
view match details
book tickets for matches
Ticketing

Ticketing handles:

ticket booking
duplicate prevention
QR code generation
QR verification
transport prompt after booking

Ticket booking flow:

Book Ticket
→ Ticket created
→ Transport prompt
→ Yes: transport page
→ No: my tickets page
Transport

Transport is linked to:

branches
matches
tickets

Rules:

transport capacity cannot be exceeded
ticket match must match transport match
one ticket cannot book invalid transport
User Journey
User registers
→ selects branch
→ membership created inactive
→ user pays membership fee
→ membership becomes active
→ user books match ticket
→ QR ticket generated
→ user chooses whether transport is needed
→ user books transport
→ admin verifies QR ticket
Admin Journey
Admin logs in
→ opens admin dashboard
→ views platform statistics
→ verifies QR ticket
→ ticket status changes from booked to used
Data Flow: Ticket Booking
User clicks Book Ticket
  |
  v
Django checks active membership
  |
  v
Django checks duplicate ticket
  |
  v
Ticket is created
  |
  v
User is redirected to transport prompt
Data Flow: Payment Activation
User clicks Pay Membership
  |
  v
Payment record is created
  |
  v
Payment status = successful
  |
  v
Membership status becomes active
Data Flow: QR Verification
Admin submits QR code
  |
  v
System finds ticket by QR
  |
  v
System checks ticket status
  |
  v
Ticket status changes from booked to used
Testing Architecture

Tests run inside Docker:

docker compose exec web python manage.py test --settings=sundowns_app.settings.test

Current tested areas:

registration with branch
JWT login
payment activation
inactive membership ticket restriction
duplicate ticket prevention
ticket booking redirect
transport prompt
QR verification
QR permission protection
transport capacity
transport match consistency
Deployment Architecture Target

Planned production path:

Browser
  |
  v
Nginx
  |
  v
Gunicorn
  |
  v
Django App
  |
  |---- PostgreSQL
  |---- Redis
  |---- Celery Worker

Future AWS path:

EC2 + Docker Compose initially
→ ECS/Fargate later if needed
Current Architecture Status

The project currently has:

modular Django apps
frontend/API route separation
Docker-based development
Docker-based testing
PostgreSQL database
Redis/Celery foundations
working frontend flows
tested business rules
deployment preparation in progress