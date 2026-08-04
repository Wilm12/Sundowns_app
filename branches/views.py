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
from supporters.models import StudentVerification, StudentVerificationStatus
from supporters.services.verify_student import VerifyStudentService
from journeys.services.collect_ticket import CollectTicketService
from matches.models import Match
from .models import Branch, BranchRole, CommitteeAction, CommitteePosition
from authentication.permissions import IsAdminOrReadOnly
from .serializers import BranchSerializer
from .services.committee import CommitteeService
from .services.authorization import is_branch_admin
from .services.promote_branch_admin import PromoteBranchAdminService, BranchAdminAlreadyAssigned, UserNotInBranch
from .services.remove_branch_admin import RemoveBranchAdminService, LastBranchAdminRemovalError
from .forms import PromoteBranchAdminForm, CommitteePositionManagementForm, RemoveBranchAdminForm
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

    if request.method == "POST":
        if "promote" in request.POST:
            form = PromoteBranchAdminForm(request.POST, branch=branch)
            if form.is_valid():
                try:
                    PromoteBranchAdminService.promote(branch, form.cleaned_data["supporter"], request.user)
                except (BranchAdminAlreadyAssigned, UserNotInBranch) as exc:
                    messages.error(request, str(exc))
                else:
                    messages.success(request, "Supporter promoted to branch admin.")
        elif "committee_action" in request.POST:
            form = CommitteePositionManagementForm(request.POST, branch=branch)
            if form.is_valid():
                member = form.cleaned_data["member"]
                role = BranchRole.objects.filter(branch=branch, user=member, role=BranchRole.Role.BRANCH_ADMIN, is_active=True).first()
                if not role:
                    messages.error(request, "Only active branch admins can hold leadership positions.")
                else:
                    action = form.cleaned_data["action"]
                    position = form.cleaned_data["position"]
                    existing_position = CommitteePosition.objects.filter(branch=branch, branch_role=role).first()
                    if action == "remove":
                        if existing_position:
                            existing_position.delete()
                            CommitteeService.log_activity(branch, request.user, CommitteeAction.ADMIN_REMOVED, target_user=member, metadata={"position": existing_position.position})
                            messages.success(request, "Leadership position removed.")
                        else:
                            messages.error(request, "No leadership position was assigned.")
                    else:
                        if existing_position and action == "change":
                            existing_position.position = position
                            existing_position.created_by = request.user
                            existing_position.save(update_fields=["position", "created_by"])
                            CommitteeService.log_activity(branch, request.user, CommitteeAction.ADMIN_PROMOTED, target_user=member, metadata={"position": position})
                            messages.success(request, "Leadership position updated.")
                        elif not existing_position and action == "assign" and position:
                            CommitteePosition.objects.create(branch=branch, branch_role=role, position=position, created_by=request.user)
                            CommitteeService.log_activity(branch, request.user, CommitteeAction.ADMIN_PROMOTED, target_user=member, metadata={"position": position})
                            messages.success(request, "Leadership position assigned.")
                        else:
                            messages.error(request, "Select a position to assign or change.")
        elif "remove_admin" in request.POST:
            form = RemoveBranchAdminForm(request.POST, branch=branch)
            if form.is_valid():
                target_user = form.cleaned_data["user"]
                try:
                    RemoveBranchAdminService.remove(branch, target_user, request.user)
                except LastBranchAdminRemovalError as exc:
                    messages.error(request, str(exc))
                else:
                    messages.success(request, "Branch admin removed.")

        return redirect("branch_committee", branch_id=branch.pk)

    committee_members = CommitteeService.list_committee_members(branch)
    stats = CommitteeService.get_committee_stats(branch)
    activities = branch.committee_activities.select_related("actor", "target_user")[:10]
    leadership_positions = CommitteeService.get_leadership_positions(branch)
    pending_verifications = (
        StudentVerification.objects.filter(
            user__branch=branch,
            status=StudentVerificationStatus.PENDING,
        )
        .select_related("user")
        .order_by("created_at")
    )

    return render(request, "branches/committee.html", {
        "branch": branch,
        "committee_members": committee_members,
        "stats": stats,
        "activities": activities,
        "leadership_positions": leadership_positions,
        "promote_form": PromoteBranchAdminForm(branch=branch),
        "position_form": CommitteePositionManagementForm(branch=branch),
        "remove_form": RemoveBranchAdminForm(branch=branch),
        "pending_verifications": pending_verifications,
    })


@login_required
def supporter_verification_view(request, branch_id, supporter_id):
    """Allow branch admins to verify a supporter and continue gate redemption."""

    branch = get_object_or_404(Branch, id=branch_id)
    supporter = get_object_or_404(User, id=supporter_id)
    if not is_branch_admin(request.user, branch):
        return render(request, "403.html", status=403)

    next_path = request.GET.get("next")
    collection_code = request.GET.get("code", "")
    match_id = request.GET.get("match_id")

    if request.method == "POST":
        verification = (
            StudentVerification.objects.filter(
                user=supporter,
                status=StudentVerificationStatus.PENDING,
            )
            .order_by("-created_at")
            .first()
        )
        if verification is None:
            messages.error(request, "No pending verification record was found for this supporter.")
        else:
            VerifyStudentService.verify(verification, request.user)
            if next_path == "gate-redemption" and collection_code and match_id:
                try:
                    match = get_object_or_404(Match, pk=match_id)
                    CollectTicketService.collect(collection_code, request.user, branch=branch, match=match)
                except Exception as exc:
                    messages.error(request, f"Verification succeeded but redemption failed: {exc}")
                else:
                    messages.success(request, "Supporter verified and ticket redeemed successfully.")
                return redirect("match_operations_console", branch_id=branch.pk, match_id=match_id)
            messages.success(request, "Supporter verification completed.")
        return redirect("match_operations_console", branch_id=branch.pk, match_id=match_id) if next_path == "gate-redemption" and match_id else redirect("branch_committee", branch_id=branch.pk)

    return render(request, "branches/supporter_verification.html", {
        "branch": branch,
        "supporter": supporter,
        "next_path": next_path,
        "collection_code": collection_code,
        "match_id": match_id,
    })

