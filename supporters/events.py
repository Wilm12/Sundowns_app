from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class StudentVerificationRequested:
    supporter_id: int
    verification_id: int
    branch_id: Optional[int] = None
    acted_by: Optional[int] = None
    timestamp: Optional[datetime] = None
    correlation_id: Optional[UUID] = None


@dataclass(frozen=True)
class StudentVerified:
    supporter_id: int
    verification_id: int
    branch_id: Optional[int] = None
    verified_by: Optional[int] = None
    expires_at: Optional[datetime] = None
    correlation_id: Optional[UUID] = None


@dataclass(frozen=True)
class StudentVerificationRejected:
    supporter_id: int
    verification_id: int
    branch_id: Optional[int] = None
    acted_by: Optional[int] = None
    timestamp: Optional[datetime] = None
    correlation_id: Optional[UUID] = None
