"""Views for points system.

This module contains views for supporter-facing points pages.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import PointsAccount, PointsTransaction
from . import tiers as tier_helpers


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

    return render(request, 'points/dashboard.html', {
        'account': account,
        'transactions': transactions,
        'current_tier': current_tier,
        'next_tier': next_tier,
        'points_until_next': points_until_next,
    })
