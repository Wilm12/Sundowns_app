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
    collection_code: str
    allocated_by: Optional[int] = None
    timestamp: Optional[datetime] = None
    correlation_id: Optional[UUID] = None


@dataclass(frozen=True)
class TicketCollected:
    journey_id: int
    supporter_id: int
    branch_id: int
    match_id: int
    ticket_id: int
    collected_by: Optional[int] = None
    collected_at: Optional[datetime] = None
    correlation_id: Optional[UUID] = None


@dataclass(frozen=True)
class AttendanceRecorded:
    journey_id: int
    supporter_id: int
    branch_id: int
    match_id: int
    attended_by: Optional[int] = None
    attended_at: Optional[datetime] = None
    correlation_id: Optional[UUID] = None
