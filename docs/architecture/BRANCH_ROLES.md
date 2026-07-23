# Branch Roles

**Sprint:** B3 – Operational Roles

**Status:** Architecture

---

# Purpose

The Branch Roles model defines the operational responsibilities within a supporters' branch.

Roles represent business responsibilities, not Django permissions.

The goal is to mirror how student supporters' branches operate in the real world.

---

# Design Principles

## Roles represent responsibilities

A role answers:

> "What operational responsibility does this supporter have?"

It does not answer:

> "What database permissions do they have?"

---

## A supporter may hold multiple roles

Example:

William

↓

UP Tuks

↓

- Branch President
- Student Verifier

---

## Roles belong to a Branch

Roles are contextual.

A supporter could be:

Transport Coordinator

at

UP Tuks

while being an ordinary supporter elsewhere.

---

## Roles are operational

Operational roles control workflows.

Examples:

- Opening journeys
- Verifying students
- Allocating transport
- Allocating complimentary tickets

---

# Role Catalogue

## Branch President

Purpose

Leads the branch.

Responsibilities

- Overall branch management
- Assign operational roles
- Approve policies
- View branch reports

Future capabilities

- Open season
- Close season
- Suspend branch operations

---

## Secretary

Purpose

Administrative management.

Responsibilities

- Manage supporter records
- Maintain communications
- Publish announcements
- Organise meetings

---

## Student Verifier

Purpose

Validate student eligibility.

Responsibilities

- Review verification requests
- Approve student verification
- Reject invalid submissions

Future

Publishes:

StudentVerified

StudentVerificationRejected

---

## Journey Coordinator

Purpose

Own supporter journeys.

Responsibilities

- Open journeys
- Close journeys
- Manage bookings
- Monitor participation

---

## Transport Coordinator

Purpose

Manage supporter transport.

Responsibilities

- Allocate buses
- Assign supporters
- Monitor boarding
- Confirm departures

---

## Ticket Distributor

Purpose

Manage complimentary tickets.

Responsibilities

- Allocate tickets
- Record ticket collection
- Handle uncollected tickets

---

## Communications Officer

Purpose

Manage branch communications.

Responsibilities

- Publish announcements
- Notify supporters
- Schedule reminders

---

# Future Roles

Possible future additions:

- Merchandise Coordinator
- Sponsorship Coordinator
- Competition Manager
- Treasurer

These are intentionally excluded from Sprint B3.

---

# Operational Ownership

## Branch President owns

- Branch administration
- Policies
- Role assignment

---

## Journey Coordinator owns

- Journey lifecycle

---

## Transport Coordinator owns

- Bus allocation
- Boarding operations

---

## Ticket Distributor owns

- Ticket allocation
- Ticket collection

---

## Student Verifier owns

- Student verification

---

## Communications Officer owns

- Announcements
- Notifications

---

# Domain Events

The Branch Context publishes:

## BranchRoleAssigned

Publisher

Branch Context

Consumers

Communications

Audit

Reporting

Payload

- branch_id
- supporter_id
- role
- assigned_by
- timestamp

---

## BranchRoleRemoved

Publisher

Branch Context

Consumers

Communications

Audit

Reporting

Payload

- branch_id
- supporter_id
- role
- removed_by
- timestamp

---

# Application Services

The following application services will eventually exist.

AssignBranchRoleService

Responsibilities

- Validate assignment
- Prevent duplicates
- Publish BranchRoleAssigned

---

RemoveBranchRoleService

Responsibilities

- Remove assignment
- Publish BranchRoleRemoved

---

ListBranchRolesService

Responsibilities

- Return operational structure
- Support reporting

---

# Architectural Rules

Operational roles are not Django Groups.

Operational roles are not Django Permissions.

Django authentication remains responsible for authentication.

Branch Roles remain responsible for business operations.

Permission checks should eventually become:

"Does this supporter currently hold the required operational role?"

rather than

"Is this user staff?"

---

# Future Integration

Supporter Context

Consumes role assignments.

---

Journey Context

Uses Journey Coordinator.

---

Transport Context

Uses Transport Coordinator.

---

Ticketing Context

Uses Ticket Distributor.

---

Communications Context

Uses Communications Officer.

---

Reporting Context

Aggregates role activity.

---

# Definition of Done

Sprint B3 is complete when:

- The operational role catalogue is defined.
- Responsibilities are documented.
- Ownership boundaries are clear.
- Domain events are identified.
- Application services are defined.
- Future implementation can begin without ambiguity.
