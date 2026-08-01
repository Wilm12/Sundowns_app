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

- Member
- Branch Admin

---

## Roles belong to a Branch

Roles are contextual.

A supporter could be:

Branch Admin

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

## Member

Purpose

Represents an ordinary branch supporter.

Responsibilities

- Participate in branch journeys and events
- Access branch communications
- Receive branch updates

---

## Branch Admin

Purpose

Represents the operational branch lead for day-to-day administration.

Responsibilities

- Approve supporter verification
- Collect tickets for branch journeys
- Record attendance for collected tickets
- Access the branch operations dashboard
- Manage branch role assignments within the branch

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

## Branch Admin owns

- Branch administration
- Policies
- Role assignment
- Verification approval
- Ticket collection
- Attendance recording

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

Consumes branch admin assignments.

---

Journey Context

Uses branch admin authorization for ticket collection and attendance recording.

---

Reporting Context

Aggregates branch admin activity.

---

# Definition of Done

Sprint B3 is complete when:

- The operational role catalogue is defined.
- Responsibilities are documented.
- Ownership boundaries are clear.
- Domain events are identified.
- Application services are defined.
- Future implementation can begin without ambiguity.
