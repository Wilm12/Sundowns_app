# ADR-00X: Product Pivot from Membership Platform to Branch Operations Platform

## Status

Proposed

## Context

The original product direction focused on supporter membership and related commercial features. However, the operational realities of student supporters' branches indicate a more fundamental need: a platform that supports branch-led match-day operations.

The current manual processes around supporter registration, verification, match booking, transport coordination, ticket allocation, attendance tracking, and reporting create friction for branches and supporters alike.

## Decision

The platform will pivot from being primarily a membership platform to becoming an operating platform for student supporters' branches.

Membership management remains important, but it becomes one capability within a broader domain rather than the central product concept.

## Consequences

### Positive

- Stronger alignment with real branch operational needs
- Better foundation for future expansion into other supporter branch types
- Clearer domain boundaries around event participation and branch operations
- Improved ability to build an auditable operating workflow for matches

### Trade-offs

- The initial architecture must shift away from membership-first thinking
- Some existing models and assumptions will need to be re-evaluated
- The platform will need a more explicit operational workflow model

## Architectural Implication

The product should be organized around supporter participation in branch-led events rather than around membership alone.

This pivot creates a stronger foundation for future multi-branch, multi-event, and commercial expansion.
