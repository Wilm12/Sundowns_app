import random
from datetime import datetime
from uuid import uuid4

from django.utils import timezone

from engagement.dispatcher import publish
from engagement.envelope import EngagementEventEnvelope
from engagement.events import EngagementEvent

from ..events import JourneyBooked
from ..models import Journey, JourneyStatus
from .open_journey import JourneyAlreadyExists


class InvalidJourneyTransition(Exception):
    """Raised when a journey cannot transition to the requested state."""


class BookJourneyService:
    """Transition an open journey to a booked state."""

    @staticmethod
    def book_journey(journey):
        if journey.status != JourneyStatus.OPEN:
            raise InvalidJourneyTransition("Journey must be OPEN to be booked.")

        existing_active_journey = Journey.objects.filter(
            supporter=journey.supporter,
            branch=journey.branch,
            match=journey.match,
            status__in=[JourneyStatus.OPEN, JourneyStatus.BOOKED],
        ).exclude(pk=journey.pk).exists()
        if existing_active_journey:
            raise JourneyAlreadyExists("An active journey already exists for the same supporter/branch/match.")

        collection_code = BookJourneyService._generate_collection_code(journey)
        journey.collection_code = collection_code
        # When a collection code is generated during booking the journey
        # immediately becomes TICKET_READY (ticket issued and awaiting
        # redemption). BOOKED must not have a collection code.
        journey.status = JourneyStatus.TICKET_READY
        journey.save(update_fields=["collection_code", "status", "updated_at"])

        event = JourneyBooked(
            journey_id=journey.pk,
            supporter_id=journey.supporter_id,
            branch_id=journey.branch_id,
            match_id=journey.match_id,
            timestamp=timezone.now(),
            correlation_id=uuid4(),
        )
        envelope = EngagementEventEnvelope(
            event=EngagementEvent.JOURNEY_BOOKED,
            user=journey.supporter,
            payload={
                "journey_id": journey.pk,
                "supporter_id": journey.supporter_id,
                "branch_id": journey.branch_id,
                "match_id": journey.match_id,
                "timestamp": datetime.now(),
            },
            correlation_id=event.correlation_id,
        )
        publish(envelope)
        return journey

    @staticmethod
    def _generate_collection_code(journey):
        while True:
            code = f"{random.randint(1000, 9999)}"
            if not Journey.objects.filter(branch=journey.branch, match=journey.match, collection_code=code).exists():
                return code
