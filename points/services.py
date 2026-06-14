"""Reusable points service layer for awarding points."""

from django.db import transaction

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

    # apply promotion multiplier when present
    base_points = POINT_RULES[event]
    try:
        # import here to avoid circular import at module load
        from promotions.services import get_points_multiplier
    except Exception:
        # if promotions app not available, fall back to multiplier 1
        def get_points_multiplier(_):
            return 1

    multiplier = get_points_multiplier(event)
    points = base_points * multiplier

    if reference_id is not None:
        with transaction.atomic():
            transaction_obj, created = PointsTransaction.objects.get_or_create(
                account=account,
                reference_id=reference_id,
                defaults={
                    'transaction_type': event.value,
                    'points': points,
                    'description': description,
                }
            )

        if not created:
            if (
                transaction_obj.transaction_type != event.value
                or transaction_obj.points != points
                or transaction_obj.description != description
            ):
                raise ValueError(
                    'Existing points transaction conflicts with requested award details.'
                )

        return transaction_obj

    return PointsTransaction.objects.create(
        account=account,
        transaction_type=event.value,
        points=points,
        description=description,
        reference_id=reference_id,
    )


def get_tier_distribution():
    """Return counts of users per tier key for admin analytics.

    Keeps the implementation simple and database-driven. Returns a dict with
    keys matching `TIER_ORDER` from `points.tiers`.
    """
    from collections import Counter
    from .models import PointsAccount
    from . import tiers as tier_helpers

    accounts = PointsAccount.objects.select_related('user').all()
    counters = Counter()
    for acct in accounts:
        tier = tier_helpers.get_tier_from_points(acct.balance)
        counters[tier] += 1

    return {k: counters.get(k, 0) for k in tier_helpers.TIER_ORDER}
