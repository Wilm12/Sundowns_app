# ADR-006 — Engagement Engine Implementation

**Status:** Accepted

**Date:** 2026-07-16

**Decision Type:** Architecture

## Context

The Engagement Engine architecture requires a clear separation between event coordination infrastructure and business service implementations.

The initial implementation blended dispatcher logic with business services, making it difficult to:
- Test event handlers independently
- Scale services without affecting infrastructure
- Add new engagement services
- Maintain clear architectural boundaries

## Decision

Implement the Engagement Engine with explicit separation between:

### Infrastructure Layer
- `dispatcher.py` — Event routing to handlers
- `registry.py` — Event-to-handler mapping
- `handlers.py` — Event orchestration (thin layer)

### Business Services Layer
- `services/` — Independent engagement services
  - `badge_service.py`
  - `promotion_service.py`
  - `timeline_service.py`
  - `analytics_service.py`

## Rationale

1. **Single Responsibility** — Infrastructure owns routing; services own engagement logic
2. **Testability** — Services can be tested independently with mocked dependencies
3. **Scalability** — New services can be added without modifying infrastructure
4. **Clarity** — Clear separation enables developers to understand system boundaries
5. **Maintainability** — Changes to business logic don't affect event routing

## Consequences

- Handlers remain thin orchestrators (5-10 lines each)
- Services are independently deployable and testable
- Changes to engagement workflows only affect relevant services
- Infrastructure code is stable and rarely modified

## Alternative Rejected

Embedding all logic in handlers — would create God objects and tight coupling.
