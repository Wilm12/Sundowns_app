"""Views for points system.

This module contains views for supporter-facing points pages.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from .models import PointsAccount, PointsTransaction
from . import tiers as tier_helpers
from .rules import POINT_RULES
from promotions.models import Promotion


@login_required
def points_dashboard(request):
    """Render the supporter-facing points dashboard."""
    account = getattr(request.user, 'points_account', None)
    if account is None:
        account = PointsAccount.objects.filter(user=request.user).first()

    transactions = []
    if account is not None:
        transactions = PointsTransaction.objects.filter(account=account).order_by('-created_at')
    # Tier info for user
    user_points = account.balance if account is not None else 0
    current_tier = tier_helpers.get_tier_from_points(user_points)
    next_tier = tier_helpers.get_next_tier(user_points)
    points_until_next = tier_helpers.points_until_next_tier(user_points)

    now = timezone.now()
    promotions = Promotion.objects.filter(
        is_active=True,
        start_date__lte=now,
        end_date__gte=now,
    ).order_by('end_date')

    earning_guide = []
    for event, value in POINT_RULES.items():
        label = event.name.replace('_', ' ').title() if hasattr(event, 'name') else str(event)
        earning_guide.append({
            'event': label,
            'points': value,
        })

    # TODO: if PointsTransaction stores promotion metadata, annotate bonus promotion info here.
    # Example metadata could include promotion_id or promotion_multiplier fields.

    return render(request, 'points/dashboard.html', {
        'account': account,
        'transactions': transactions,
        'current_tier': current_tier,
        'current_points': user_points,
        'next_tier': next_tier,
        'points_until_next': points_until_next,
        'promotions': promotions,
        'earning_guide': earning_guide,
    })


@login_required
def tiers_page(request):
    thresholds = [
        {
            'tier': tier.capitalize(),
            'threshold': tier_helpers.TIER_THRESHOLDS[tier],
        }
        for tier in tier_helpers.TIER_ORDER
    ]
    return render(request, 'points/tiers.html', {
        'thresholds': thresholds,
    })
