from datetime import datetime
from uuid import UUID, uuid4

from django.utils import timezone

from engagement.dispatcher import publish
from engagement.envelope import EngagementEventEnvelope
from engagement.events import EngagementEvent

from branches.models import BranchRole

from ..events import TicketCollected
from ..models import Journey, JourneyStatus


class InvalidCollectionCode(Exception):
    """Raised when a collection code does not resolve to a journey."""


class TicketAlreadyCollected(Exception):
    """Raised when a ticket has already been collected."""


class CollectorNotAuthorized(Exception):
    """Raised when a collector does not have distributor privileges for the branch."""


class InvalidJourneyState(Exception):
    """Raised when a journey is not in a state that can be collected."""


class CollectTicketService:
    """Collect a ticket from a booked journey using its collection code."""

    @staticmethod
    def collect(collection_code, collector):
        try:
            journey = Journey.objects.get(collection_code=UUID(str(collection_code)))
        except (Journey.DoesNotExist, ValueError, TypeError):
            raise InvalidCollectionCode("Collection code does not match an existing journey.")

        if journey.status == JourneyStatus.TICKET_COLLECTED:
            raise TicketAlreadyCollected("Ticket has already been collected.")

        if journey.status != JourneyStatus.TICKET_READY:
            raise InvalidJourneyState("Only TICKET_READY journeys may be collected.")

        has_distributor_role = BranchRole.objects.filter(
            branch=journey.branch,
            user=collector,
            role=BranchRole.Role.TICKET_DISTRIBUTOR,
            is_active=True,
        ).exists()
        if not has_distributor_role:
            raise CollectorNotAuthorized("Collector is not authorized to distribute tickets for this branch.")

        journey.ticket_collected_at = timezone.now()
        journey.ticket_collected_by = collector
        journey.status = JourneyStatus.TICKET_COLLECTED
        journey.save(update_fields=["ticket_collected_at", "ticket_collected_by", "status", "updated_at"])

        event = TicketCollected(
            journey_id=journey.pk,
            supporter_id=journey.supporter_id,
            branch_id=journey.branch_id,
            match_id=journey.match_id,
            ticket_id=journey.ticket_id,
            collected_by=collector.pk,
            collected_at=journey.ticket_collected_at,
            correlation_id=uuid4(),
        )
        envelope = EngagementEventEnvelope(
            event=EngagementEvent.TICKET_COLLECTED,
            user=journey.supporter,
            payload={
                "journey_id": journey.pk,
                "supporter_id": journey.supporter_id,
                "branch_id": journey.branch_id,
                "match_id": journey.match_id,
                "ticket_id": journey.ticket_id,
                "collected_by": collector.pk,
                "collected_at": datetime.now(),
            },
            correlation_id=event.correlation_id,
        )
        publish(envelope)
        return journey
