# ADR: Immediate Ticket Issuance After Booking

Date: 2026-08-13
Status: Accepted
Authors: GitHub Copilot (assistant), developer

Context
-------
Previously journeys could be left in an inconsistent state where a
`collection_code` existed while the journey remained in `BOOKED` status.
This caused dashboard and operational discrepancies: metrics for allocated,
booked, pending and attended could diverge between consoles and reality.
Some historical flows also mixed payment/allocation semantics with booking,
leading to accidental coupling of booking and activation.

Decision
--------
- Generate collection codes at booking time.
- Any journey that has a `collection_code` MUST be in `JourneyStatus.TICKET_READY`.
- `BOOKED` journeys MUST NOT have a `collection_code`.
- Verification is required for redemption (gate collection), not for booking.
- Successful verification (branch admin verification flow) will automatically
  redeem the ticket and transition the journey to `JourneyStatus.MATCH_ATTENDED`.

Rationale
--------
- A collection code represents a physical/serial ticket that has been
  issued and is awaiting redemption; therefore the journey state should
  reflect that (TICKET_READY).
- Keeping `BOOKED` free of collection codes prevents ambiguous states and
  simplifies metric calculations:
  - Booked = journeys with status `BOOKED` and no issued ticket
  - Allocated = journeys where a ticket has been issued (includes TICKET_READY)
  - Pending = journeys with status `TICKET_READY` (tickets issued, awaiting redemption)
  - Attended = journeys with status `MATCH_ATTENDED`
- This separation decouples booking from supporter activation and from
  payment/allocation flows, preventing accidental re-introduction of prior
  gating behavior.

Consequences
-----------
- Implementation must ensure any code path that assigns `collection_code`
  also updates `journey.status = JourneyStatus.TICKET_READY` and persists the change.
  See: [journeys/services/book_journey.py](journeys/services/book_journey.py#L1-L200)
- Allocation code that attaches `Ticket` records should accept `TICKET_READY`
  journeys (it may be idempotent or attach missing ticket records).
  See: [journeys/services/allocate_ticket.py](journeys/services/allocate_ticket.py#L1-L200)
- Collect/redemption code must require active verification and move
  `TICKET_READY` -> `MATCH_ATTENDED` upon successful redemption
  (this is already implemented in `journeys/services/collect_ticket.py`).
- Tests and dashboards must compute `pending_count` as
  `journeys.filter(status=JourneyStatus.TICKET_READY).count()` so Match
  Operations and Branch Admin Dashboard remain consistent.

Notes
-----
- This ADR codifies a core business rule. Any future change that touches
  booking, allocation, verification, or redemption must reference this ADR
  and either comply or explicitly document compensating changes.

References
---------
- Code changes made (local workspace):
  - `journeys/services/book_journey.py`
  - `journeys/services/allocate_ticket.py`
  - `journeys/services/collect_ticket.py`
  - `branches/services/branch_admin_dashboard.py`
  - `journeys/services/match_operations.py`

--
Generated during maintenance to ensure bookkeeping and operational metrics remain consistent.
