# Sundowns WPA System Architecture

## Overview

Sundowns WPA is a Django-based supporter membership and engagement platform designed for football supporter communities.

The platform manages:

* Users
* Branches
* Memberships
* Payments
* Matches
* Tickets
* Transport
* Loyalty Points
* Rewards
* Promotions
* Notifications
* Analytics

The system follows a modular monolith architecture with clear separation between frontend template routes and DRF API routes.

## Architecture Decision Records

- [ADR-005 — Platform Engagement Engine](architecture/adr-005-platform-engagement-engine.md)

---

# Core Technology Stack

* Django
* Django REST Framework
* PostgreSQL
* Docker
* Docker Compose
* Redis
* Celery Foundations
* Tailwind CSS
* JWT Authentication
* Django Template Frontend

---

# High-Level Architecture

```text
Browser
   |
   v
Django Application
   |
   |----------------------------
   | Frontend Template Routes
   | DRF API Routes
   | Business Logic
   | Services Layer
   |----------------------------
   |
   v
PostgreSQL Database

Redis
   |
   v
Future Celery Workers
```

---

# Routing Architecture

Frontend and API routes are intentionally separated.

```text
frontend_urls.py
    ↓
Template Pages

urls.py
    ↓
API Endpoints
```

Examples:

```text
matches/frontend_urls.py
    /matches/

matches/urls.py
    /api/matches/
```

```text
ticketing/frontend_urls.py
    /tickets/

ticketing/urls.py
    /api/tickets/
```

This separation improves:

* Maintainability
* Testing
* Route clarity
* Future frontend flexibility

---

# Domain Architecture

## Authentication

Responsibilities:

* Registration
* Login
* JWT Authentication
* Role-Based Access
* Permissions

Roles:

```text
Admin
Member
```

---

## Users

Custom user model.

Important fields:

* username
* email
* role
* branch

Business rule:

```text
Every supporter belongs to a branch.
```

---

## Branches

Represents supporter communities.

Relationships:

```text
Branch
    ↓
Users
Membership Activity
Transport Activity
Future Campaign Targeting
```

---

## Membership

Controls supporter eligibility.

### Membership Types

#### Basic

```text
R50
Promotional Giveaways
30% Merchandise Discount
```

#### Premium

```text
R100
Transport Eligibility
60% Merchandise Discount
```

#### Golden

```text
R150
Expanded Transport Eligibility
70% Merchandise Discount
VIP Benefits
```

### Membership Flow

```text
Register
    ↓
Inactive Membership
    ↓
Payment Successful
    ↓
Membership Activated
```

Ticket booking requires:

```text
membership.status == active
```

---

## Payments

Responsible for membership activation.

Flow:

```text
Membership Payment
    ↓
Payment Successful
    ↓
Membership Activated
```

Future:

```text
Reward Payments
Merchandise Payments
Campaign Payments
```

---

## Matches

Stores fixture information.

Supporters can:

* View Fixtures
* View Match Details
* Book Tickets

---

## Ticketing

Handles:

* Ticket Booking
* Duplicate Prevention
* QR Generation
* QR Verification
* Loyalty Point Awards
* Transport Prompt

### Ticket Booking Flow

```text
Book Ticket
    ↓
Membership Validation
    ↓
Duplicate Check
    ↓
Ticket Created
    ↓
Transport Prompt
```

---

## Transport

Transport booking linked to:

* Branches
* Matches
* Tickets

Rules:

```text
Capacity Cannot Be Exceeded

Ticket Match
    =
Transport Match

Invalid Transport Booking
    Prevented
```

---

# Loyalty Domain

## Points

Points are awarded for supporter activities.

Examples:

```text
Membership Payments
Ticket Purchases
Future Campaign Activities
Future Attendance Verification
```

Points are stored as:

```text
PointsTransaction
```

The ledger is the source of truth.

---

## Tiers

Supporters progress through loyalty tiers.

### Tier Thresholds

```text
Bronze
0+

Silver
100+

Gold
500+

Platinum
1000+
```

### Tier Benefits

Used for:

* Reward Eligibility
* Future Campaign Eligibility
* Future VIP Experiences

---

## Rewards

Supporters redeem rewards using points.

Reward fields include:

```text
Points Cost
Minimum Tier
Available Quantity
Active Status
```

---

## Reward Redemption Workflow

```text
Pending
    ↓
Approved
    ↓
Ready For Collection
    ↓
Collected
    ↓
Completed
```

Alternative outcomes:

```text
Rejected
Cancelled
```

---

## Promotions

Promotions modify loyalty earning behavior.

Examples:

```text
Double Points Weekend
Membership Bonus
Match Attendance Multiplier
```

Promotions support:

```text
Event Type
Multiplier
Start Date
End Date
```

---

# Notifications Domain

Notifications provide supporter engagement feedback.

Current notification types:

```text
points_earned
tier_upgrade
reward_redeemed
```

Future notification types:

```text
campaign_invitation
competition_entry
winner_announced
branch_drive
membership_expiry
```

Architecture:

```text
Business Event
    ↓
Notification Service
    ↓
Notification Record
    ↓
Notification Centre
```

---

# Analytics Domain

Provides operational and loyalty insights.

Current metrics:

```text
Top Supporters
Tier Distribution
Reward Statistics
Supporter Activity
```

Future metrics:

```text
Campaign Analytics
Branch Performance
Attendance Analytics
Sponsor Analytics
```

Architecture:

```text
Platform Activity
    ↓
Analytics Services
    ↓
Aggregated Metrics
    ↓
Admin Dashboard
```

---

# User Journey

```text
Register
    ↓
Select Branch
    ↓
Membership Created
    ↓
Membership Payment
    ↓
Membership Activated
    ↓
Book Ticket
    ↓
Earn Points
    ↓
Progress Through Tiers
    ↓
Redeem Rewards
    ↓
Receive Notifications
```

---

# Admin Journey

```text
Admin Login
    ↓
Admin Dashboard
    ↓
View Analytics
    ↓
Manage Memberships
    ↓
Manage Rewards
    ↓
Approve Redemptions
    ↓
Verify QR Tickets
```

---

# Data Flow: Membership Activation

```text
Payment
    ↓
Successful
    ↓
Membership Activated
```

---

# Data Flow: Ticket Booking

```text
Book Ticket
    ↓
Membership Validation
    ↓
Duplicate Check
    ↓
Ticket Created
```

---

# Data Flow: Reward Redemption

```text
Redeem Reward
    ↓
Tier Validation
    ↓
Points Validation
    ↓
Stock Validation
    ↓
Points Deducted
    ↓
Redemption Created
    ↓
Notification Created
```

---

# Data Flow: Tier Upgrade

```text
Points Earned
    ↓
Tier Recalculated
    ↓
Tier Upgrade Detected
    ↓
Notification Created
```

---

# Testing Architecture

Tests execute inside Docker.

```text
docker compose exec web python manage.py test --settings=sundowns_app.settings.test
```

Coverage includes:

* Registration
* Branch Assignment
* JWT Authentication
* Membership Activation
* Ticket Booking
* Duplicate Prevention
* Transport Validation
* QR Verification
* Loyalty Points
* Tier Calculation
* Reward Redemption
* Notifications
* Analytics

---

# Current Navigation Structure

```text
Dashboard

Supporter
    Membership
    Branches

Match Day
    Matches
    Tickets
    Transport

Loyalty
    Points
    Rewards

Engagement
    Notifications

Account
    Settings
```

---

# Future Domains

Planned but not yet implemented.

## Campaigns & Supporter Engagement

Purpose:

```text
Competitions
Sponsor Activations
Branch Recruitment Drives
Attendance Challenges
Membership Drives
```

Campaigns will use audience targeting.

Examples:

```text
All Supporters

Specific Branches

Specific Tiers

Specific Membership Types
```

Competitions are considered a type of Campaign.

---

# Deployment Architecture Target

```text
Browser
   |
   v
Nginx
   |
   v
Gunicorn
   |
   v
Django
   |
   |---- PostgreSQL
   |
   |---- Redis
   |
   |---- Celery Worker
```

Future AWS path:

```text
EC2 + Docker Compose
        ↓
ECS / Fargate (if required)
```

---

# Operational Roadmap

Future production maturity work:

```text
Monitoring
Logging
Alerting
Backups
Disaster Recovery
Incident Response
Runbooks
Performance Monitoring
```

---

# Current Architecture Status

Implemented:

```text
Authentication
Users
Branches
Memberships
Payments
Matches
Ticketing
Transport
Points
Rewards
Promotions
Notifications
Analytics
```

Planned:

```text
Campaigns
Competitions
Sponsor Activations
Branch Challenges
Merchandise
Advanced Loyalty Features
```
