# Supporter Context

## Purpose

The Supporter Context is the authoritative bounded context for supporter identity, profile, verification, eligibility, and lifecycle management.

It owns the canonical identity of a person participating in branch operations. Other contexts may reference that identity, but they do not own or mutate it directly.

## Core Principle

The platform manages known supporters, not anonymous participants.

Every journey, attendance record, transport booking, ticket allocation, and report should ultimately reference a Supporter.

## Aggregate Root

### Supporter

The Supporter aggregate owns:
- supporter identity
- supporter profile details
- verification state
- eligibility state
- lifecycle state

It is the boundary for supporter-related invariants.

## Responsibilities

The Supporter Context owns:
- Supporter identity
- Supporter profile
- Student verification
- Eligibility evaluation
- Verification renewal
- Supporter lifecycle

It does not own:
- journeys
- transport
- ticket allocation
- attendance
- payments
- branch policies
- branch roles

## Domain Model

### Supporter

Suggested fields:
- id
- first_name
- last_name
- email
- phone_number
- student_number
- university
- status
- created_at
- updated_at

### StudentVerification

Suggested fields:
- supporter
- verification_status
- verified_at
- expires_at
- verified_by
- evidence_reference

### Eligibility

Suggested fields:
- supporter
- is_eligible
- reason
- evaluated_at

## Status Values

Supporter status should reflect operational state:
- ACTIVE
- PENDING_VERIFICATION
- VERIFIED
- INACTIVE
- SUSPENDED

## Invariants

- Email is unique.
- A supporter represents one real person.
- Only one active verification record per supporter.
- Eligibility may only be changed through Supporter application services.
- Only the Supporter Context may modify supporter identity and verification state.

## Application Services

- RegisterSupporterService
- UpdateSupporterProfileService
- VerifyStudentService
- RejectStudentVerificationService
- EvaluateEligibilityService
- RenewVerificationService

## Domain Events

- SupporterRegistered
- StudentVerificationRequested
- StudentVerified
- StudentVerificationRejected
- EligibilityGranted
- EligibilityRevoked

## Context Boundaries

### Branch Context
- Branch references Supporter.
- Supporter does not manage branch policies.

### Journey Context
- Journeys are created for supporters.
- Journey consumes eligibility events.

### Communications Context
- Communications targets supporters.
- Communications consumes supporter events.

### Reporting Context
- Reporting aggregates supporter participation and verification statistics.
