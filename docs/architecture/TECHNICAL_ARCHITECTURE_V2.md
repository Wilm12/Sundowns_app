# Technical Architecture V2

## Purpose

This document translates the product architecture into a technical architecture that future implementation work should follow.

It defines a layered structure, bounded contexts, aggregate roots, domain events, application services, dependency rules, target folder structure, and coding conventions.

---

## 1. Overall Architecture

The platform should follow a layered architecture with clear responsibilities and a dependency direction that preserves business logic ownership.

```text
Presentation Layer

↓

Application Layer

↓

Domain Layer

↓

Infrastructure Layer
```

### Presentation Layer

Responsibilities:
- expose user-facing entry points such as web views, APIs, and admin interfaces
- collect input and delegate to application services
- format responses for clients

Rules:
- should remain thin
- should not contain business logic
- should not own domain invariants

### Application Layer

Responsibilities:
- orchestrate use cases
- coordinate domain services and repositories
- manage transactions and workflows
- invoke domain logic and domain events

Rules:
- contains use-case orchestration, not business rules
- should be the main integration point for controllers, handlers, and external workflows

### Domain Layer

Responsibilities:
- define business concepts, policies, invariants, and aggregate behavior
- own domain rules and state transitions
- define domain events and interfaces for infrastructure concerns

Rules:
- must not depend on web frameworks, views, or transport-specific concerns
- should express business intent clearly
- should remain the authoritative home of business logic

### Infrastructure Layer

Responsibilities:
- implement persistence, messaging, external integrations, and other technical concerns
- provide repositories, event publishers, email gateways, storage adapters, and similar capabilities

Rules:
- depends on the domain layer
- should not dictate business rules
- should be replaceable without changing domain behavior

---

## 2. Bounded Contexts

The system should be organized into bounded contexts so that each area has a clear responsibility boundary and its own domain language.

### Branch Context

Purpose:
- manage branch-level administration, operational configuration, branch roles, and operating policies

Responsibilities:
- define branch operating rules
- manage branch administrators and branch-level settings
- coordinate branch-specific workflows
- own branch-level policies and operational configuration

Owned aggregates:
- Branch

Published events:
- BranchCreated
- BranchPoliciesUpdated
- SupporterJoinedBranch
- BranchSeasonOpened
- BranchSeasonClosed

Consumed events:
- SupporterRegistered
- StudentVerified

### Supporter Context

Purpose:
- maintain supporter identity and profile information

Responsibilities:
- register supporters
- maintain supporter profile data
- manage supporter affiliations to branches
- support verification readiness

Owned aggregates:
- Supporter
- SupporterProfile

Published events:
- SupporterRegistered
- SupporterProfileUpdated

Consumed events:
- BranchCreated
- SeasonOpened

### Verification Context

Purpose:
- determine whether a supporter is eligible to participate in branch operations

Responsibilities:
- evaluate student verification status
- assess eligibility against seasonal rules
- manage verification windows and approval state

Owned aggregates:
- VerificationRequest
- EligibilityAssessment

Published events:
- StudentVerified
- VerificationExpired
- EligibilityRevoked

Consumed events:
- SupporterRegistered
- SeasonOpened

### Journey Context

Purpose:
- manage a supporter’s participation lifecycle within a specific match or event

Responsibilities:
- open journeys
- manage booking and participation states
- coordinate match, transport, ticket, boarding, and attendance stages
- close journeys after completion

Owned aggregates:
- Journey
- JourneyBooking
- JourneyAttendance

Published events:
- JourneyOpened
- JourneyBooked
- TransportAssigned
- BusBoarded
- TicketCollected
- AttendanceRecorded
- JourneyCompleted

Consumed events:
- StudentVerified
- TransportAssigned
- TicketCollected
- BusBoarded

### Communication Context

Purpose:
- deliver announcements, reminders, confirmations, and operational messaging

Responsibilities:
- send communications based on journey and seasonal state
- manage communication templates and recipients
- track communication outcomes where relevant

Owned aggregates:
- Announcement
- CommunicationChannel

Published events:
- AnnouncementSent
- ReminderTriggered

Consumed events:
- JourneyOpened
- JourneyBooked
- JourneyCompleted
- AttendanceRecorded

### Reporting Context

Purpose:
- provide branch-level insights and seasonal reporting

Responsibilities:
- aggregate attendance and operational data
- produce seasonal reports and branch summaries
- support performance and trend analysis

Owned aggregates:
- ReportDefinition
- SeasonalReport

Published events:
- ReportGenerated

Consumed events:
- AttendanceRecorded
- JourneyCompleted
- VerificationExpired

### Commercial Context (Future)

Purpose:
- support commercial capabilities such as memberships, loyalty, rewards, and merchandise discounts

Responsibilities:
- manage membership products and commercial entitlements
- integrate with rewards and loyalty workflows
- support sponsor-linked campaigns where applicable

Owned aggregates:
- MembershipProduct
- LoyaltyProgram

Published events:
- MembershipActivated
- RewardIssued

Consumed events:
- SupporterRegistered
- StudentVerified
- JourneyCompleted

---

## 3. Context Map

The bounded contexts should interact through explicit relationships and well-defined events.

```text
Supporter
   │
   ▼
Verification
   │
   ▼
Journey
   │
   ├──────────────► Communication
   │
   └──────────────► Reporting
```

### Interaction Notes

- Supporter Context is the foundation for identity.
- Verification Context depends on supporter identity and produces eligibility outcomes.
- Journey Context consumes verification outcomes and drives the operational lifecycle.
- Communication Context reacts to journey milestones and branch communications needs.
- Reporting Context observes completed workflows and produces operational insight.
- Commercial Context should be introduced later and should depend on the operational state produced by the core contexts.

---

## 4. Aggregate Roots

The following aggregate roots should form the core consistency boundaries of the platform.

### Branch

Why it is an aggregate root:
- it represents the primary operational unit and owns branch identity, policies, administrators, contact information, and operational configuration

Invariants it protects:
- branch identity is unique
- branch policies remain coherent with the branch’s operational role
- administrators and contact details remain consistent
- branch operational status is valid for the current season context

For Sprint B, the branch aggregate should stay intentionally simple. It should own:
- Identity
- Policies
- Administrators
- Contact Information
- Operational Status
- Events

Season should not be treated as a child of Branch in the first slice. Branch participates in a Season as a separate concern that can be introduced later.

### Supporter

Why it is an aggregate root:
- it owns the identity and profile lifecycle of a person participating in branch operations

Invariants it protects:
- a supporter should have a single canonical identity within the platform
- affiliation and profile changes must remain coherent

### Journey

Why it is an aggregate root:
- it governs the full lifecycle of a supporter’s participation in a specific event

Invariants it protects:
- a journey must progress through valid states
- booking, transportation, ticketing, boarding, and attendance must remain consistent with the journey lifecycle

### Season

Why it is an aggregate root:
- it defines the operational window for journeys, attendance, verification, and reporting

Invariants it protects:
- seasonal boundaries must remain coherent
- seasonal rules and windows should apply consistently to all related workflow entities

### VerificationRequest

Why it is an aggregate root:
- it owns the lifecycle of student verification and eligibility assessment

Invariants it protects:
- verification cannot be in contradictory states
- eligibility outcomes must be tied to a valid verification process

---

## 5. Domain Events

Domain events should be used for cross-context communication and for preserving business history.

### Event Template

- Event name
- Publisher
- Subscribers
- Payload
- Purpose

### Example Events

#### SupporterRegistered

Publisher:
- Supporter Context

Subscribers:
- Verification Context
- Journey Context

Payload:
- supporter_id
- branch_id
- profile_snapshot

Purpose:
- notify downstream contexts that a supporter exists and is ready for further processing

#### SupporterJoinedBranch

Publisher:
- Branch Context

Subscribers:
- Communication Context
- Reporting Context

Payload:
- supporter_id
- branch_id
- joined_at

Purpose:
- signal that a supporter now participates in a branch and can be considered for branch-level workflows

#### StudentVerified

Publisher:
- Verification Context

Subscribers:
- Journey Context
- Reporting Context

Payload:
- supporter_id
- season_id
- eligibility_status
- verified_at

Purpose:
- mark a supporter as eligible for operational participation

#### JourneyOpened

Publisher:
- Journey Context

Subscribers:
- Communication Context
- Reporting Context

Payload:
- journey_id
- supporter_id
- event_id
- opened_at

Purpose:
- signal that a journey has started and operational processing can begin

#### JourneyBooked

Publisher:
- Journey Context

Subscribers:
- Communication Context
- Reporting Context

Payload:
- journey_id
- booking_state
- booked_at

Purpose:
- indicate that the supporter has successfully booked their participation

#### TransportAssigned

Publisher:
- Journey Context

Subscribers:
- Communication Context

Payload:
- journey_id
- transport_id
- assigned_at

Purpose:
- notify the operational team and supporter about transport allocation

#### BusBoarded

Publisher:
- Journey Context

Subscribers:
- Reporting Context

Payload:
- journey_id
- boarded_at

Purpose:
- mark that the supporter has completed the boarding stage

#### TicketCollected

Publisher:
- Journey Context

Subscribers:
- Reporting Context

Payload:
- journey_id
- ticket_reference
- collected_at

Purpose:
- record ticket handoff or collection

#### AttendanceRecorded

Publisher:
- Journey Context

Subscribers:
- Reporting Context
- Communication Context

Payload:
- journey_id
- attendance_status
- recorded_at

Purpose:
- capture match-day attendance and update reports

#### JourneyCompleted

Publisher:
- Journey Context

Subscribers:
- Reporting Context
- Commercial Context (future)

Payload:
- journey_id
- completed_at
- outcome

Purpose:
- finalize the lifecycle of the journey and support downstream analytics and commercial flows

---

## 6. Application Services

Application services should orchestrate use cases and coordinate domain behavior without embedding business rules into controllers or views.

### RegisterSupporterService

Responsibilities:
- create a supporter profile and initialize the supporter lifecycle
- publish the relevant domain events

### VerifyStudentService

Responsibilities:
- evaluate verification input and determine eligibility
- update the verification state for a supporter

### OpenJourneyService

Responsibilities:
- create a journey for a supporter within an event or season
- initialize the journey state machine

### BookJourneyService

Responsibilities:
- process journey booking decisions
- coordinate booking-related invariants and publish relevant events

### AllocateTransportService

Responsibilities:
- assign transport to a booked journey
- publish transport-related domain events

### AllocateTicketService

Responsibilities:
- allocate or issue ticket entitlement for a journey
- publish the ticket allocation state change

### RecordAttendanceService

Responsibilities:
- record attendance for a completed journey
- publish attendance-related events

### CloseJourneyService

Responsibilities:
- finalize a journey after attendance and closure rules are satisfied
- publish completion events

---

## 7. Dependency Rules

The architecture should enforce clear dependency boundaries.

### Core Rules

- Domain layer never depends on Django views, serializers, or transport concerns.
- Views and API handlers call application services.
- Application services coordinate domain objects and repositories.
- Bounded contexts communicate through domain events.
- No cross-context model imports.
- Infrastructure depends on the domain, never the reverse.
- Repositories implement interfaces defined by the domain.
- Event publishers and handlers should be implemented in the infrastructure or application layer, but the domain should define the event contracts.

### Cross-Context Rule

- Cross-context interaction must occur through events or explicit application-service contracts.
- Contexts should not directly mutate each other’s entities.

---

## 8. Folder Structure

The project structure should be organized by bounded context so that ownership is clear and evolution is manageable.

```text
branch/
  models.py
  services/
  events.py
  handlers.py
  repositories.py
  tests/

supporter/
  models.py
  services/
  events.py
  handlers.py
  repositories.py
  tests/

verification/
  models.py
  services/
  events.py
  handlers.py
  repositories.py
  tests/

journey/
  models.py
  services/
  events.py
  handlers.py
  repositories.py
  tests/

communication/
  models.py
  services/
  events.py
  handlers.py
  repositories.py
  tests/

reporting/
  models.py
  services/
  events.py
  handlers.py
  repositories.py
  tests/

commercial/
  models.py
  services/
  events.py
  handlers.py
  repositories.py
  tests/
```

### Notes

- This is a target structure and should not be interpreted as a requirement to implement every context immediately.
- Each context should be organized around its own domain concepts and responsibilities.

---

## 9. Coding Conventions

The implementation should follow a consistent set of conventions so the system remains understandable over time.

### General Conventions

- Thin views and controllers
- Fat application services where orchestration is needed
- Business rules belong in the domain layer
- Events should be used for cross-context communication
- One aggregate should own one invariant group
- Use consistent ubiquitous language across code, docs, and product discussions

### Domain Conventions

- Prefer explicit value objects for concepts such as eligibility and verification status
- Keep state transitions explicit and named
- Avoid leaking infrastructure concerns into domain objects
- Define invariants near the aggregate that protects them

### Application Conventions

- Application services should be named for use cases rather than technical actions
- Use repositories to hide persistence details from the domain
- Keep transaction boundaries clear and intentional

### Infrastructure Conventions

- Repositories should implement domain-defined interfaces
- Event publishing should be explicit and observable
- Adapters should isolate external systems from core business code

---

### Sprint B implementation focus

The first implementation slice should stay intentionally narrow and focus on ownership rather than introducing premature abstractions.

Priority outcomes:
- introduce branch policies as a first-class concern
- give the branch aggregate responsibility for operational configuration and branch-level rules
- support branch administrators and contact information without introducing additional child aggregates
- publish simple branch lifecycle events such as BranchCreated, SupporterJoinedBranch, and BranchPoliciesUpdated
- keep the model easy to evolve toward Season, verification, and journey workflows later

Suggested backlog order:
1. Branch Policies
2. Operational Roles
3. Branch Events
4. Branch Dashboard Read Model
5. Branch Services

## Summary

This architecture establishes a platform that is:

- centered on branch operations
- organized into clear bounded contexts
- driven by domain events
- protected by aggregate invariants
- extensible toward future commercial capabilities
