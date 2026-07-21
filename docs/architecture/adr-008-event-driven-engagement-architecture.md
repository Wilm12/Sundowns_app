# ADR-008: Event-Driven Engagement Architecture

- **Status:** Accepted
- **Date:** 2026-07-17
- **Decision Makers:** Platform Engineering Team

---

# Context

The Sundowns WPA platform initially handled supporter engagement directly inside business domains.

For example:

- Membership activation awarded supporter points.
- Membership activation would eventually unlock promotions.
- Membership activation would eventually create timeline entries.
- Membership activation would eventually award badges.

As supporter engagement expands, embedding all of this logic inside the Payments or Membership domains would violate the Single Responsibility Principle and create tight coupling between unrelated business domains.

The platform requires a scalable mechanism where business events can trigger multiple independent workflows without modifying the originating domain.

---

# Decision

The platform adopts an **event-driven engagement architecture**.

Business domains publish **domain events** whenever significant supporter activities occur.

The Engagement Engine is responsible for consuming those events and orchestrating supporter engagement workflows.

The originating domain **never directly invokes** badge, promotion, analytics, or timeline services.

Instead, it simply publishes a business event.

---

# Event Flow

```text
Payment Successful
        │
        ▼
Membership Activated
        │
        ▼
Publish MEMBERSHIP_ACTIVATED Event
        │
        ▼
Engagement Dispatcher
        │
        ▼
Membership Activated Handler
        │
        ├──────────────► Badge Service
        │
        ├──────────────► Promotion Service
        │
        ├──────────────► Timeline Service
        │
        └──────────────► Analytics Service
```

---

# Architecture

```
engagement/

dispatcher.py
registry.py
handlers.py
events.py
envelope.py
exceptions.py

services/

    badge_service.py

    promotion_service.py

    timeline_service.py

    analytics_service.py
```

---

# Responsibilities

## Business Domains

Business domains own business state.

Example:

### Payments

Responsible for:

- Recording payment
- Activating membership
- Publishing `MEMBERSHIP_ACTIVATED`

Not responsible for:

- Badges
- Promotions
- Timeline
- Analytics

---

## Engagement Dispatcher

Responsible for:

- Publishing events
- Routing events
- Correlation IDs
- Event logging
- Handler lookup

Not responsible for business logic.

---

## Event Handlers

Responsible for orchestration.

Example:

`membership_activated_handler`

Coordinates:

- Points
- Badge
- Promotions
- Timeline
- Analytics

Handlers contain orchestration only.

Business rules belong inside individual services.

---

## Engagement Services

Each service owns one business capability.

| Service | Responsibility |
|----------|----------------|
| Badge Service | Award supporter badges |
| Promotion Service | Unlock supporter promotions |
| Timeline Service | Record supporter activity history |
| Analytics Service | Record engagement analytics |

Services must remain independent and must not call each other directly.

---

# Design Principles

## 1. Publish Events, Not Actions

Business domains publish:

```
Membership Activated
```

Not:

```
Award Welcome Badge
```

This keeps domains independent of engagement implementation.

---

## 2. Loose Coupling

Payments has no knowledge of:

- badges
- promotions
- timeline
- analytics

New engagement services can subscribe to existing events without changing Payments.

---

## 3. Single Responsibility

Each engagement service owns exactly one concern.

Example:

```
Badge Service
    ↓
Badges

Promotion Service
    ↓
Promotions

Timeline Service
    ↓
Timeline

Analytics Service
    ↓
Analytics
```

---

## 4. Extensibility

Future capabilities can subscribe to existing events.

Example:

```
Membership Activated

        │

        ├── Loyalty Service

        ├── Marketing Service

        ├── Notification Service

        ├── Recommendation Engine

        └── AI Personalisation
```

No modifications are required to Payments.

---

## 5. Observability

Every published event carries:

- Event Type
- Correlation ID
- Timestamp
- Payload

This enables complete traceability across the engagement pipeline.

---

# Current Event Catalogue

| Event | Publisher |
|--------|-----------|
| MEMBERSHIP_ACTIVATED | Payments |
| TICKET_BOOKED *(planned)* | Ticketing |
| TRANSPORT_BOOKED *(planned)* | Transport |
| MATCH_CHECKED_IN *(planned)* | Ticket Verification |
| REWARD_REDEEMED *(planned)* | Rewards |
| BRANCH_CHANGED *(planned)* | Membership |

---

# Benefits

- Clear separation of concerns.
- Business domains remain clean.
- Engagement logic is centralized.
- Easy to introduce new supporter experiences.
- Easier automated testing.
- Improved auditability.
- Future-ready for asynchronous messaging.
- Reduced coupling between business domains.

---

# Trade-offs

- More architectural components.
- Requires good logging.
- Requires careful event versioning as the platform grows.
- Future asynchronous execution will require idempotent handlers.

These trade-offs are acceptable considering the expected growth of the platform.

---

# Future Evolution

The current dispatcher executes handlers synchronously inside Django.

The architecture intentionally allows migration to asynchronous event processing without changing business domains.

Current:

```
Payment
    │
Dispatcher
    │
Handler
    │
Services
```

Future:

```
Payment
    │
Kafka / RabbitMQ / Amazon SQS
    │
Worker
    │
Handler
    │
Services
```

Only the dispatcher implementation changes.

Business domains continue publishing the same events.

---

# Implementation Status

## Completed

- Event Dispatcher
- Event Registry
- Event Envelope
- Domain Events
- Membership Activation Event
- Membership Activated Handler
- Badge Service (placeholder)
- Promotion Service (placeholder)
- Timeline Service (placeholder)
- Analytics Service (placeholder)
- Payment-driven event publishing
- Correlation ID logging
- CI validation

## Planned (Sprint 4)

- EngagementTimeline model
- UserBadge model
- Promotion unlock persistence
- Analytics persistence
- Supporter activity feed

---

# Decision Summary

The Sundowns WPA platform adopts an **event-driven engagement architecture** in which business domains publish domain events and the Engagement Engine orchestrates supporter engagement through dedicated handlers and independent services.

This architecture separates business state changes from engagement workflows, improving maintainability, extensibility, observability, and readiness for future asynchronous event processing.
