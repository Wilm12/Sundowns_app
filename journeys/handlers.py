import logging

logger = logging.getLogger(__name__)


def journey_opened_handler(envelope):
    payload = envelope.payload or {}
    logger.info(
        "JourneyOpened | supporter=%s | match=%s | branch=%s",
        payload.get("supporter_id"),
        payload.get("match_id"),
        payload.get("branch_id"),
    )


def journey_booked_handler(envelope):
    payload = envelope.payload or {}
    logger.info(
        "JourneyBooked | supporter=%s | match=%s | branch=%s",
        payload.get("supporter_id"),
        payload.get("match_id"),
        payload.get("branch_id"),
    )


def ticket_allocated_handler(envelope):
    payload = envelope.payload or {}
    logger.info(
        "TicketAllocated | journey=%s | supporter=%s | ticket=%s",
        payload.get("journey_id"),
        payload.get("supporter_id"),
        payload.get("ticket_id"),
    )
