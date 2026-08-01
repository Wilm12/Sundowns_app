"""Views for branch administration, listing, and detail pages.

This module provides both API endpoints and page views for branch data,
including admin-restricted operations and member dashboard navigation.
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from users.models import User
from transport.models import Transport
from .models import Branch
from authentication.permissions import IsAdminOrReadOnly
from .serializers import BranchSerializer
from .services.committee import CommitteeService
from .services.authorization import is_branch_admin
from django.contrib import messages

@login_required
def my_branch_page(request):
    """Redirect the logged in user to their assigned branch detail page."""

    if not request.user.branch:
        messages.error(request, "You are not assigned to a branch.")
        return redirect("dashboard")

    return redirect("branch_detail_page", branch_id=request.user.branch.id)


class BranchViewSet(viewsets.ModelViewSet):
    """API viewset for branch CRUD operations."""

    queryset = Branch.objects.all().order_by('name')
    serializer_class = BranchSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]


@login_required
def branch_list_page(request):
    """Render the branch listing page for authenticated users."""

    branches = Branch.objects.all().order_by("name")

    return render(request, "branches/list.html", {
        "branches": branches,
    })


@login_required
def branch_detail_page(request, branch_id):
    """Render the branch detail page, including members and active transport."""

    branch = get_object_or_404(Branch, id=branch_id)

    members = User.objects.filter(
        branch=branch
    ).order_by("username")

    transport = Transport.objects.filter(
        branch=branch,
        status="active"
    )

    return render(request, "branches/detail.html", {
        "branch": branch,
        "members": members,
        "transport": transport,
    })


@login_required
def committee_management_view(request, branch_id):
    """Render a lightweight committee management dashboard for branch admins."""

    branch = get_object_or_404(Branch, id=branch_id)
    if not is_branch_admin(request.user, branch):
        return render(request, "403.html", status=403)

    committee_members = CommitteeService.list_committee_members(branch)
    stats = CommitteeService.get_committee_stats(branch)
    activities = branch.committee_activities.select_related("actor", "target_user")[:10]

    return render(request, "branches/committee.html", {
        "branch": branch,
        "committee_members": committee_members,
        "stats": stats,
        "activities": activities,
    })

