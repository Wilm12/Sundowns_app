# Sprint B — Branch Context

**Status:** Architecture & Domain Design

**Objective:** Establish the Branch bounded context as the operational owner of branch administration and configuration within the Branch Operations platform.

---

# Purpose

The Branch Context is responsible for managing how a supporters' branch operates.

It does not manage supporter journeys, transport, tickets, attendance, or payments.

Instead, it defines the operational environment in which those workflows occur.

---

# Vision

A Branch represents an organised supporters' community.

It owns:

- its identity
- its administrators
- its operational policies
- its communication preferences
- its configuration

Every other operational workflow occurs within a Branch.

---

# Aggregate Root

## Branch

The Branch Aggregate Root protects all branch-level business rules.

Other bounded contexts may reference a Branch but may not modify its internal state directly.

---

# Responsibilities

The Branch Context owns:

- Branch Identity
- Branch Administration
- Branch Roles
- Branch Policies
- Branch Contact Information
- Branch Operational Status
- Branch Configuration

It does NOT own:

- Supporters
- Journeys
- Ticket Allocation
- Transport
- Attendance
- Payments
- Rewards

Those belong to their own bounded contexts.

---

# Branch Entity

Current

```text
Branch
-------
id
name
location
created_at
```

Future

```text
Branch
-------
id
name
code
location
contact_email
contact_phone
status
created_at
updated_at
```

---

# Branch Status

Initially, a simple enum is sufficient.

```text
ACTIVE

INACTIVE

SUSPENDED
```

No historical snapshots will be implemented during Sprint B.

---

# Branch Policies

Branch Policies are business configuration owned by the Branch.

Examples:

- Student verification required
- Journey booking deadline
- Maximum transport capacity
- Complimentary ticket allocation strategy
- Announcement approval required
- Attendance requirement
- Supported university

These policies should eventually be configurable without code changes.

Initially they may simply exist as fields or a configuration object.

---

# Branch Roles

Branch Roles are operational responsibilities.

They are NOT Django permissions.

Initial roles:

- Branch President
- Secretary
- Transport Coordinator
- Ticket Distributor
- Student Verifier
- Event Coordinator

These roles describe business responsibilities.

Permission enforcement can be layered later.

---

# Value Objects

## ContactDetails

Represents official branch contact information.

Contains:

- email
- phone
- meeting location

This value object has no identity.

---

# Application Services

Sprint B defines—not implements—the following services.

## CreateBranchService

Creates a new branch.

---

## UpdateBranchPolicyService

Updates operational policies.

---

## AssignBranchAdministratorService

Assigns branch administrators.

---

## UpdateBranchContactService

Maintains branch contact information.

---

## ChangeBranchStatusService

Activates, suspends or deactivates a branch.

---

# Domain Events

The Branch Context publishes events.

## BranchCreated

Publisher:

Branch Context

Consumers:

Communications

Reporting

Analytics

---

## BranchAdministratorAssigned

Publisher:

Branch Context

Consumers:

Communications

Audit

---

## BranchPolicyUpdated

Publisher:

Branch Context

Consumers:

Journey Context

Transport Context

Ticketing Context

---

## BranchActivated

Publisher:

Branch Context

Consumers:

Communications

Reporting

---

## BranchSuspended

Publisher:

Branch Context

Consumers:

Journey Context

Communications

Reporting

---

# Invariants

The Branch Aggregate protects the following rules.

## Identity

Every branch has a unique name.

---

## Administration

Every active branch must have at least one administrator.

---

## Status

A branch cannot be simultaneously Active and Suspended.

---

## Policies

Operational policies may only be modified through Branch application services.

---

## Ownership

Only the Branch Context may modify Branch state.

Other bounded contexts may reference Branch but never update it directly.

---

# Integration with Other Contexts

## Supporter Context

Supporters belong to a Branch.

Supporter Context references Branch.

Branch does not manage Supporters.

---

## Journey Context

Journeys occur within a Branch.

Journey references Branch.

Branch does not orchestrate Journeys.

---

## Communications Context

Announcements belong to Branch.

Communication consumes Branch events.

---

## Reporting Context

Reports aggregate Branch operational data.

Reporting consumes Branch events.

---

# Folder Structure (Target)

```text
branches/

    models.py

    services/

        create_branch.py

        update_policy.py

        assign_admin.py

        change_status.py

    events.py

    handlers.py

    repositories.py

    policies.py

    tests/
```

Not all files will be created during Sprint B.

This is the architectural target.

---

# Definition of Done

Sprint B is complete when:

✓ Branch is clearly established as an Aggregate Root.

✓ Branch responsibilities are documented.

✓ Operational ownership boundaries are defined.

✓ Domain events are identified.

✓ Application services are defined.

✓ Branch policies are identified.

✓ Future implementation can proceed without ambiguity.
