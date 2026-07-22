# Context Map

## Purpose

The Context Map captures the major bounded contexts in the platform and how they relate to one another.

It is intended to show the architectural shape of the system without replacing the domain model.

## Core Contexts

### Branch Operations
The umbrella domain that coordinates branch administration, supporter participation, and match-day execution.

### Supporter Management
Responsible for supporter identity, supporter profiles, affiliations, and basic relationship management.

### Verification
Responsible for student identity checks, eligibility assessment, and verification windows.

### Journey Management
Responsible for the lifecycle of supporter participation in a match or event, including journey opening, booking, transport, ticketing, boarding, and completion.

### Communications
Responsible for announcements, reminders, confirmations, and other supporter-facing messaging.

### Reporting
Responsible for seasonal reporting, attendance analysis, branch insights, and operational metrics.

### Administration
Responsible for branch-level oversight, roles, permissions, and operational governance.

## High-Level Relationships

```text
                    Branch Operations
                           │
      ┌────────────────────┼────────────────────┐
      │                    │                    │
 Supporter Management   Journey Management   Communications
      │                    │                    │
   Verification        Transport / Ticket      Announcements
      │                    │
   Reporting            Attendance
```

## Architectural Intent

- Branch Operations is the umbrella domain.
- Supporter Management and Verification provide the identity and eligibility foundation.
- Journey Management orchestrates the operational workflow around matches and participation.
- Communications and Reporting are cross-cutting capabilities that depend on the operational state of the platform.
- Administration provides governance over how the system is used by branches.
