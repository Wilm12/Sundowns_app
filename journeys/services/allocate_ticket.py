import random
from datetime import datetime
from uuid import uuid4

from django.utils import timezone

from engagement.dispatcher import publish
from engagement.envelope import EngagementEventEnvelope
from engagement.events import EngagementEvent

from ticketing.models import Ticket

from ..events import TicketAllocated
from ..models import Journey, JourneyStatus


class InvalidJourneyState(Exception):
    """Raised when the journey is not in a state that can receive a ticket."""


class JourneyAlreadyHasTicket(Exception):
    """Raised when the journey already has an associated ticket."""


class TicketAllocationFailed(Exception):
    """Raised when ticket allocation cannot be completed."""


class AllocateTicketService:
    """Allocate a complimentary ticket to a booked journey."""

    @staticmethod
    def allocate(journey, allocated_by=None):
        if not isinstance(journey, Journey):
            raise TicketAllocationFailed("Journey is invalid.")

        if journey.status != JourneyStatus.BOOKED:
            raise InvalidJourneyState("Only BOOKED journeys may receive a ticket.")

        if journey.ticket_id is not None:
            raise JourneyAlreadyHasTicket("Journey already has a ticket.")

        ticket = Ticket.objects.create(
            user=journey.supporter,
            match=journey.match,
            status="booked",
        )

        collection_code = AllocateTicketService._generate_collection_code(journey)

        journey.ticket = ticket
        journey.ticket_allocated_at = timezone.now()
        journey.collection_code = collection_code
        journey.status = JourneyStatus.TICKET_READY
        journey.save(update_fields=["ticket", "ticket_allocated_at", "collection_code", "status", "updated_at"])

        event = TicketAllocated(
            journey_id=journey.pk,
            supporter_id=journey.supporter_id,
            branch_id=journey.branch_id,
            match_id=journey.match_id,
            ticket_id=ticket.pk,
            collection_code=journey.collection_code,
            allocated_by=allocated_by.pk if allocated_by else None,
            timestamp=timezone.now(),
            correlation_id=uuid4(),
        )
        envelope = EngagementEventEnvelope(
            event=EngagementEvent.TICKET_ALLOCATED,
            user=journey.supporter,
            payload={
                "journey_id": journey.pk,
                "supporter_id": journey.supporter_id,
                "branch_id": journey.branch_id,
                "match_id": journey.match_id,
                "ticket_id": ticket.pk,
                "collection_code": str(journey.collection_code),
                "allocated_by": allocated_by.pk if allocated_by else None,
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
