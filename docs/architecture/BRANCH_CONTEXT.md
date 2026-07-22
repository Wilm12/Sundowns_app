# Branch Context

## 1. Purpose

The Branch Context is the operational home for branch-level administration, configuration, and policy. Its purpose is to define how a branch operates as a first-class business unit within the platform, while remaining independent from ticketing, transport, payments, and other downstream workflows.

In this architecture, a branch is not just a label attached to a user or a transport option. It is an operational domain with its own identity, rules, administrators, and business policies.

---

## 2. Responsibilities

The Branch Context is responsible for:

- defining the identity of a branch
- maintaining branch-level operational policies
- managing branch administrators and contact information
- representing the branch’s operational status
- publishing branch lifecycle events for the wider platform
- providing branch-level configuration needed by other contexts

The context should not own:

- ticketing logic
- transport booking rules
- payment processing
- match-specific journey execution

Those concerns belong to other contexts and should consume branch policies rather than depend on branch internals in a tightly coupled way.

---

## 3. Aggregate Root

The aggregate root of this context is:

- Branch

The Branch aggregate is the authoritative boundary for branch-level rules and configuration. It protects the consistency of branch identity, policies, and administration.

The Branch aggregate should remain intentionally simple in Sprint B. It should own the core concerns that matter now:

- identity
- policies
- administrators
- contact information
- operational status
- branch-related events

---

## 4. Entities

The initial entity model should be lightweight and pragmatic.

### Branch
The primary aggregate root.

Responsibilities:
- represent a branch as an operational unit
- hold its core identity and configuration
- enforce branch-level policy consistency
- publish branch lifecycle events

### BranchAdministrator
A supporting entity that represents a user who is authorized to operate the branch.

Responsibilities:
- link a user to a branch in an administrative capacity
- reflect branch-level operational authority
- support future role-based administration without overcomplicating the initial model

### BranchPolicy
A supporting entity that captures the configurable rules that make a branch behave differently from others.

Responsibilities:
- hold branch-specific operating rules
- define verification requirements, booking windows, capacity rules, and other policy decisions
- allow policies to evolve independently from the branch identity itself

---

## 5. Value Objects

Value objects should be introduced where they add clarity without unnecessary complexity.

### ContactDetails
A value object representing the branch’s contact information.

Example fields:
- email
- phone
- address

Purpose:
- keep contact information structured and consistent
- avoid scattering contact fields across the aggregate

### BranchCode
A value object representing a stable, business-facing identifier for the branch.

Purpose:
- support internal references and external integrations
- keep branch identity distinct from database identity

### BranchStatus
A value object representing the operational state of the branch.

Possible values:
- Active
- Inactive
- Suspended

Purpose:
- make branch state explicit and constrained
- avoid raw string state management in the aggregate

---

## 6. Domain Events

Domain events should be used to inform the wider platform when branch state changes.

### BranchCreated
Published when a new branch is created.

Purpose:
- notify downstream contexts that a branch now exists

### BranchPoliciesUpdated
Published when branch policies change.

Purpose:
- allow communications, journeys, verification, and reporting to react to policy change

### SupporterJoinedBranch
Published when a supporter is linked to a branch.

Purpose:
- signal branch participation and enable branch-level workflows

### BranchSeasonOpened
Published when the branch becomes operational for a season.

Purpose:
- notify downstream contexts that branch operations are active for a given season

### BranchSeasonClosed
Published when a branch is no longer operational for a season.

Purpose:
- signal the end of seasonal participation for the branch

---

## 7. Application Services

Application services should orchestrate use cases and keep the presentation layer thin.

### CreateBranchService
Responsibilities:
- create a new Branch aggregate
- validate incoming branch data
- publish BranchCreated

### UpdateBranchPoliciesService
Responsibilities:
- update branch policies in a coordinated way
- enforce policy consistency rules
- publish BranchPoliciesUpdated

### RegisterBranchAdministratorService
Responsibilities:
- assign administrative responsibility to a user
- ensure the branch can be operated safely
- preserve branch-level authorization rules

### OpenBranchSeasonService
Responsibilities:
- activate branch operation for a season
- validate readiness
- publish BranchSeasonOpened

### CloseBranchSeasonService
Responsibilities:
- close branch operation for a season
- publish BranchSeasonClosed

---

## 8. Invariants

The Branch aggregate should protect the following invariants:

- a branch must have a unique identity
- a branch must have valid operational status
- branch policies must remain coherent with the branch’s operational purpose
- administrators must be associated with a valid branch
- a branch cannot be in contradictory states such as active and suspended at the same time
- branch-level rules should be applied consistently across the platform

These invariants should be enforced inside the aggregate or through domain services, not through controllers or serializers.

---

## 9. Future Expansion

This context should remain simple now and grow only when the business actually needs it.

Future expansion may include:

- Season as a first-class aggregate when seasonal administration becomes a real operational concern
- branch participation history when transfers, alumni, and historical reporting become important
- richer policy modeling such as attendance thresholds, capacity rules, and verification requirements
- branch-specific dashboards and reporting read models
- more sophisticated administrative roles and delegation models

The guiding principle for the future is: introduce complexity only when the business requires it.
