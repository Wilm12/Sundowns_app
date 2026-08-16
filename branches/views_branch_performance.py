from django.shortcuts import render
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from branches.models import BranchRole, Branch
from branches.services.authorization import is_branch_admin
from analytics.services import BranchAnalyticsService
from matches.models import Match


@login_required
def branch_performance_view(request, branch_id=None):
    """Render branch performance analytics for the authenticated branch admin."""
    branch = request.user.branch

    if branch is None:
        branch_role = BranchRole.objects.filter(
            user=request.user,
            role=BranchRole.Role.BRANCH_ADMIN,
            is_active=True,
        ).select_related("branch").first()
        branch = branch_role.branch if branch_role else None

    # If branch_id is provided in URL, override with that
    if branch_id:
        branch = Branch.objects.filter(pk=branch_id).first()

    if not is_branch_admin(request.user, branch):
        return HttpResponseForbidden()

    # Get the current match (operational or branch-related)
    operational_match = getattr(branch, "operational_match", None)

    if not operational_match:
        from journeys.models import Journey, JourneyStatus
        from django.utils import timezone

        operational_match = (
            Match.objects.filter(
                journeys__branch=branch,
                journeys__status__in=[
                    JourneyStatus.BOOKED,
                    JourneyStatus.TICKET_READY,
                ],
            )
            .order_by("date")
            .distinct()
            .first()
        )

    if not operational_match:
        branch_match = (
            Match.objects.filter(journeys__branch=branch)
            .order_by("-date")
            .distinct()
            .first()
        )
        operational_match = branch_match

    if not operational_match:
        upcoming_match = Match.objects.filter(
            date__gte=timezone.now()
        ).order_by("date").first()
        operational_match = upcoming_match

    if operational_match is None:
        operational_match = Match.objects.order_by("date").first()

    # Get branch analytics for current match
    current_match_analytics = {}
    if operational_match:
        current_match_analytics = BranchAnalyticsService.get_branch_match_metrics(
            branch, operational_match
        )

    # Get historical performance
    historical_performance = BranchAnalyticsService.get_branch_performance(branch)[:10]

    context = {
        "branch": branch,
        "current_match": operational_match,
        "current_match_analytics": current_match_analytics,
        "historical_performance": historical_performance,
    }

    return render(
        request,
        "branches/branch_performance.html",
        context,
    )
