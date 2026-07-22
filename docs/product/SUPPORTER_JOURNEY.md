# Supporter Journey

## Purpose

Supporter Journey is a major workflow within the broader Branch Operations domain. It captures how a supporter progresses through branch-led match-day operations.

## Relationship to Season

A Season provides the temporal container for journeys and related branch activities. Many journeys, attendance records, verification windows, reports, and competitions are organized around a season rather than a continuous operating model.

## Journey Stages

1. Register
2. Create or update supporter profile
3. Complete student verification
4. Become eligible for branch operations
5. Book match participation
6. Book transport
7. Receive booking confirmation
8. Prepare for match-day logistics
9. Board bus or access transport
10. Collect ticket or confirmation material
11. Attend match
12. Record attendance
13. Complete the journey

## Design Intent

The journey should be understood as one operational progression within Branch Operations rather than as the complete domain.

Each stage may be handled by a different capability or bounded context, but the overall experience should feel coherent to the supporter.

## Key Architectural Principle

The journey should connect identity, eligibility, booking, logistics, and attendance into a single continuous story for the supporter while remaining a part of the broader Branch Operations domain.
