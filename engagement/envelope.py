"""Event envelope for the Engagement Engine.

This module defines an immutable envelope that wraps platform events as
they travel through the Engagement Engine. The envelope contains the
event, the associated user, an optional payload, a UTC timestamp and a
correlation id for tracing.
"""

from dataclasses import dataclass, field
from datetime import datetime
import uuid
from typing import Any, Dict

from engagement.events import EngagementEvent


@dataclass(frozen=True)
class EngagementEventEnvelope:
    """Immutable container for an engagement event.

    Attributes:
        event: The engagement event (an `EngagementEvent` enum member).
        user: The user associated with the event. Kept as `Any` for now.
        payload: Arbitrary payload data for the event.
        timestamp: UTC timestamp when the envelope was created.
        correlation_id: UUID used to correlate related events/actions.
    """

    event: EngagementEvent
    user: Any
    payload: Dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: uuid.UUID = field(default_factory=uuid.uuid4)
