"""Reusable points service layer for awarding points."""

from .models import PointsTransaction
from .rules import PointEvent, POINT_RULES


def award_points(user, *, event, description, reference_id=None):
    """Award points to a user's points account for a specific event.

    Args:
        user: The user receiving points.
        event: A PointEvent enum member or corresponding string value.
        description: Human-readable description of why points were awarded.
        reference_id: Optional external reference identifier.

    Returns:
        PointsTransaction: The newly created transaction record.

    Raises:
        ValueError: If the event is invalid or the user has no points account.
        TypeError: If event is not a PointEvent or string.
    """
    if isinstance(event, str):
        try:
            event = PointEvent(event)
        except ValueError:
            valid_events = ', '.join(e.value for e in PointEvent)
            raise ValueError(
                f"Invalid point event: {event!r}. Valid events are: {valid_events}"
            )
    elif not isinstance(event, PointEvent):
        raise TypeError('event must be a PointEvent or string')

    account = getattr(user, 'points_account', None)
    if account is None:
        raise ValueError('User must have a points account before awarding points')

    points = POINT_RULES[event]

    return PointsTransaction.objects.create(
        account=account,
        transaction_type=event.value,
        points=points,
        description=description,
        reference_id=reference_id,
    )
