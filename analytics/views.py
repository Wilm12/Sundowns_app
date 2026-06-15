from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect

from .services import (
    get_analytics_loyalty_metrics,
    get_analytics_reward_metrics,
    get_analytics_membership_metrics,
)


@login_required
def analytics_dashboard_view(request):
    """Render the admin analytics dashboard at /analytics/."""
    if request.user.role != 'admin':
        messages.error(request, 'Only admins can access analytics.')
        return redirect('dashboard')

    context = {
        **get_analytics_loyalty_metrics(),
        **get_analytics_reward_metrics(),
        **get_analytics_membership_metrics(),
    }
    return render(request, 'analytics/dashboard.html', context)
