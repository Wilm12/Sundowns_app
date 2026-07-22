# Domain Events

## Purpose

Domain events formalize the event-driven nature of the platform and provide a shared language for cross-context communication.

## Core Event Types

- SupporterRegistered
- StudentVerified
- JourneyOpened
- JourneyBooked
- TransportAssigned
- BusBoarded
- TicketCollected
- AttendanceRecorded
- JourneyCompleted

## Event Design Principles

- Events represent meaningful business transitions rather than internal implementation steps.
- Events should be immutable and observable by downstream capabilities.
- Events should support communication between bounded contexts such as verification, bookings, logistics, attendance, and reporting.
- Events should help preserve auditability and operational traceability.
