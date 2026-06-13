"""Promotion service helpers."""

from django.utils import timezone
from .models import Promotion
from points.rules import PointEvent


def get_points_multiplier(event):
    """Return the multiplier for a given PointEvent.

    Args:
        event: PointEvent enum member or string matching its value.

    Returns:
        int: multiplier (defaults to 1 if no active promotion applies).
    """
    # normalize event to string value
    if hasattr(event, 'value'):
        event_value = event.value
    else:
        event_value = str(event)

    now = timezone.now()

    promotions = Promotion.objects.filter(
        event_type=event_value,
        is_active=True,
    )

    for promo in promotions:
        if promo.start_date and promo.end_date:
            if promo.start_date <= now <= promo.end_date:
                return promo.multiplier
        else:
            # if no dates set, treat as always-on when active
            return promo.multiplier

    return 1
