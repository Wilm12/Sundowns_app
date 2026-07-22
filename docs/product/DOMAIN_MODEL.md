# Domain Model

## Core Intent

The domain model should reflect branch operations as the primary domain concept, with supporter participation workflows organized within that broader operational context.

## Core Concepts

### Branch Operations
The overarching domain that covers everyday branch administration and match-day execution.

### Supporter
A person who participates in branch activities and match-day operations.

### Branch
A supporter branch that runs operations, manages participants, and coordinates activities.

### Supporter Profile
A persistent profile containing identity and participation-related information for a supporter.

### Affiliation
A supporter may be affiliated with one or more branches or supporter groups.

### Eligibility
A policy-driven assessment of whether a supporter is permitted to participate in a given operation or event.

### Verification
The process of confirming a supporter’s student or branch eligibility status.

### Event
A match or branch activity that creates an operational workflow.

### Season
A defined period of time within which branch operations, supporter participation, verification, reporting, and competitions are organized.

### Match Participation
The lifecycle of a supporter’s engagement with a specific event.

## Domain Relationships

- A Branch runs Branch Operations across many activities and events.
- A Season contains the operational cadence for a defined period of time.
- A Supporter may belong to one or more Branches.
- A Branch may coordinate many Events within a Season.
- A Supporter may participate in many Events across one or more Seasons.
- Each participation may have a distinct Eligibility state.
- Each participation may advance through operational stages such as booking, verification, transport, boarding, and attendance.

## Modeling Guidance

- Branch Operations should be treated as the primary domain concept.
- Season should be treated as the organizing period for branch operations and participation workflows.
- Supporter Journey should be treated as a major workflow within Branch Operations rather than the entire domain.
- Membership should be treated as an attribute or affiliation state rather than the primary domain concept.
- Eligibility should be modeled as a policy-driven assessment rather than a static flag.
- Operational workflows should be modeled around participation in a specific event rather than around isolated modules such as transport or ticketing.

## Domain Events

The domain should be modeled around explicit events that represent important state transitions across branch operations.

Representative events include:

- SupporterRegistered
- StudentVerified
- JourneyOpened
- JourneyBooked
- TransportAssigned
- BusBoarded
- TicketCollected
- AttendanceRecorded
- JourneyCompleted
