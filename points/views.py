"""Views for points system.

This module contains views for supporter-facing points pages.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import PointsAccount, PointsTransaction


@login_required
def points_dashboard(request):
    """Render the supporter-facing points dashboard."""
    account = getattr(request.user, 'points_account', None)
    if account is None:
        account = PointsAccount.objects.filter(user=request.user).first()

    transactions = []
    if account is not None:
        transactions = PointsTransaction.objects.filter(account=account).order_by('-created_at')

    return render(request, 'points/dashboard.html', {
        'account': account,
        'transactions': transactions,
    })
