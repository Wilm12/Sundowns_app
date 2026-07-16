# ADR-007 — Dispatcher Separation

**Status:** Accepted

**Date:** 2026-07-16

**Decision Type:** Architecture

## Context

The Engagement Engine needs to dispatch events to handlers with a clean, focused interface.

The initial implementation contained dispatcher logic in `services.py`, conflating:
- Infrastructure concerns (event routing)
- Business concerns (engagement services)
- Import clarity (ambiguous what "services" contained)

## Decision

Rename `services.py` to `dispatcher.py` to explicitly indicate its responsibility: dispatching events to registered handlers.

### Structure

```
engagement/
├── dispatcher.py       ← publish(envelope) function
├── registry.py         ← EVENT_HANDLERS mapping
├── handlers.py         ← Event orchestration
├── events.py           ← Event enum definitions
├── envelope.py         ← Event container
├── exceptions.py       ← Domain exceptions
└── services/           ← Business services
    ├── badge_service.py
    ├── promotion_service.py
    ├── timeline_service.py
    └── analytics_service.py
```

## Rationale

1. **Explicit Intent** — `dispatcher.py` name clearly indicates purpose
2. **Semantic Clarity** — `services/` folder contains engagement services, not infrastructure
3. **Import Readability** — `from engagement.dispatcher import publish` is self-documenting
4. **Consistency** — Infrastructure files grouped at root; business logic in services folder

## Consequences

- All imports use `from engagement.dispatcher import publish`
- Infrastructure becomes a distinct layer
- Business services are clearly isolated in `services/` folder
- Easier for new developers to understand system organization
