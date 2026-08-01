from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from engagement.dispatcher import publish
from engagement.envelope import EngagementEventEnvelope


@dataclass(frozen=True)
class BranchRoleAssigned:
    branch_id: int
    supporter_id: int
    role: str
    assigned_by: Optional[int]
    assigned_at: datetime
    correlation_id: Optional[UUID] = None


@dataclass(frozen=True)
class BranchRoleRemoved:
    branch_id: int
    supporter_id: int
    role: str
    removed_by: Optional[int]
    removed_at: datetime
    correlation_id: Optional[UUID] = None


def dispatch_event(event, user, payload, correlation_id=None):
    envelope = EngagementEventEnvelope(
        event=event,
        user=user,
        payload=payload,
        correlation_id=correlation_id or uuid4(),
    )
    publish(envelope)
    return envelope
