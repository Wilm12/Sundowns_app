from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from branches.models import Branch
from journeys.models import Journey
from journeys.services.allocate_ticket import AllocateTicketService
from journeys.services.collect_ticket import CollectTicketService
from journeys.services.match_operations import MatchOperationsService
from journeys.services.record_attendance import RecordAttendanceService
from matches.models import Match


@login_required
def match_operations_console(request, branch_id, match_id):
    branch = get_object_or_404(Branch, pk=branch_id)
    match = get_object_or_404(Match, pk=match_id)

    has_admin_access = branch.branch_roles.filter(
        user=request.user,
        role='BRANCH_ADMIN',
        is_active=True,
    ).exists()
    if not has_admin_access:
        raise PermissionDenied

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "allocate":
            journey_id = request.POST.get("journey_id")
            journey = get_object_or_404(Journey, pk=journey_id, branch=branch, match=match)
            AllocateTicketService.allocate(journey, allocated_by=request.user)
            messages.success(request, "Ticket allocated successfully.")
        elif action == "redeem":
            collection_code = request.POST.get("collection_code", "") or request.POST.get("code", "")
            try:
                CollectTicketService.collect(collection_code, request.user, branch=branch, match=match)
            except Exception as exc:
                messages.error(request, str(exc))
            else:
                messages.success(request, "Ticket redeemed successfully.")
        elif action == "attend":
            journey_id = request.POST.get("journey_id")
            journey = get_object_or_404(Journey, pk=journey_id, branch=branch, match=match)
            RecordAttendanceService.record(journey, request.user)
            messages.success(request, "Attendance recorded successfully.")

        return redirect("match_operations_console", branch_id=branch.pk, match_id=match.pk)

    search_query = request.GET.get("q", "")
    console = MatchOperationsService.get_console(branch, match, search_query=search_query)

    return render(request, "branches/match_operations_console.html", {
        "branch": branch,
        "match": match,
        "console": console,
    })
