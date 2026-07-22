# Architecture V2

## Overview

The platform should evolve from a membership-centric product into a branch operations platform.

This architecture treats match-day operations as the primary organizing principle.

## Architectural Direction

The system should be built around the following themes:

- branch operations
- season-based planning and execution
- supporter identity
- event participation
- verification and eligibility
- logistical workflows
- reporting and branch administration

## Core Design Principle

Operational capabilities should be modeled as connected workflows rather than isolated modules.

## Proposed Architectural Shape

### Foundation Domains

- Branch Operations
- Season
- Supporter Identity
- Branch
- Member Profile
- Eligibility
- Student Verification
- Roles

### Operational Modules

- Supporters
- Verification
- Events
- Journeys
- Attendance
- Verification Window
- Reports
- Competitions
- Communications
- Reporting
- Administration
- Match Booking
- Transport Booking
- Complimentary Ticket Allocation
- Ticket Collection
- Bus Boarding

### Commercial Modules

Commercial functionality should remain secondary and be introduced later.

- Membership Payments
- Loyalty
- Rewards
- Sponsors
- Merchandise Discounts
- Competitions

## Architectural Intent

The architecture should support:

- a shared supporter record across multiple branches and events
- branch-specific operating rules
- season-based orchestration of participation, verification, attendance, and reporting
- consistent lifecycle tracking for one supporter across many events
- a strong Branch Operations foundation that can accommodate administration, communications, reporting, and supporter journeys
- future expansion without reworking the whole platform

## Related Documents

- [DOMAIN_EVENTS.md](DOMAIN_EVENTS.md)
- [CONTEXT_MAP.md](CONTEXT_MAP.md)
- [UBIQUITOUS_LANGUAGE.md](UBIQUITOUS_LANGUAGE.md)
