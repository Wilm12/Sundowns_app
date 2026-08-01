from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class JourneyOpened:
    journey_id: int
    supporter_id: int
    branch_id: int
    match_id: int
    timestamp: Optional[datetime] = None
    correlation_id: Optional[UUID] = None


@dataclass(frozen=True)
class JourneyBooked:
    journey_id: int
    supporter_id: int
    branch_id: int
    match_id: int
    timestamp: Optional[datetime] = None
    correlation_id: Optional[UUID] = None


@dataclass(frozen=True)
class TicketAllocated:
    journey_id: int
    supporter_id: int
    branch_id: int
    match_id: int
    ticket_id: int
    collection_code: UUID
    allocated_by: Optional[int] = None
    timestamp: Optional[datetime] = None
    correlation_id: Optional[UUID] = None
