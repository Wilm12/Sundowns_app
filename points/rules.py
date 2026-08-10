"""Point awarding rules for the BranchRoute Points System."""

from enum import Enum


class PointEvent(Enum):
    """Supported point-awarding events."""
    MEMBERSHIP_PAYMENT = 'membership_payment'
    TICKET_BOOKING = 'ticket_booking'
    TRANSPORT_BOOKING = 'transport_booking'


POINT_RULES = {
    PointEvent.MEMBERSHIP_PAYMENT: 50,
    PointEvent.TICKET_BOOKING: 10,
    PointEvent.TRANSPORT_BOOKING: 5,
}
