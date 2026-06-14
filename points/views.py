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
from rewards.models import RewardRedemption


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
    # progress percentage between current tier and next
    progress_percent = 0
    current_threshold = tier_helpers.TIER_THRESHOLDS.get(current_tier, 0)
    next_threshold = None
    next_tier_key = tier_helpers.get_next_tier(user_points)
    if next_tier_key:
        next_threshold = tier_helpers.TIER_THRESHOLDS.get(next_tier_key)
    if next_threshold and next_threshold > current_threshold:
        span = next_threshold - current_threshold
        gained = (user_points or 0) - current_threshold
        progress_percent = int(round(max(0, min(1.0, gained / float(span))) * 100))

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
        'progress_percent': progress_percent,
        'rewards_redeemed_count': RewardRedemption.objects.filter(user=request.user, status__in=[RewardRedemption.Status.APPROVED, RewardRedemption.Status.FULFILLED]).count(),
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
