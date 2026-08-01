from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class SupporterRegistered:
    supporter_id: int
    email: str
    registered_at: datetime
    correlation_id: Optional[UUID] = None


@dataclass(frozen=True)
class StudentVerificationRequested:
    supporter_id: int
    requested_at: datetime
    correlation_id: Optional[UUID] = None


@dataclass(frozen=True)
class StudentVerified:
    supporter_id: int
    verified_at: datetime
    correlation_id: Optional[UUID] = None


@dataclass(frozen=True)
class StudentVerificationRejected:
    supporter_id: int
    rejected_at: datetime
    correlation_id: Optional[UUID] = None


@dataclass(frozen=True)
class EligibilityGranted:
    supporter_id: int
    granted_at: datetime
    correlation_id: Optional[UUID] = None


@dataclass(frozen=True)
class EligibilityRevoked:
    supporter_id: int
    revoked_at: datetime
    correlation_id: Optional[UUID] = None
