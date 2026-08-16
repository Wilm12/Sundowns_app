"""Views for branch administration, listing, and detail pages.

This module provides both API endpoints and page views for branch data,
including admin-restricted operations and member dashboard navigation.
"""

from django.db import transaction
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from users.models import User
from transport.models import Transport
from supporters.models import StudentVerification, StudentVerificationStatus
from supporters.services.verify_student import VerifyStudentService
from journeys.services.collect_ticket import CollectTicketService
from analytics.services import AnalyticsSnapshotService
from matches.models import Match
from .models import Branch, BranchRole, CommitteeAction, CommitteePosition, MatchAllocation
from authentication.permissions import IsAdminOrReadOnly
from .serializers import BranchSerializer
from .services.committee import CommitteeService
from .services.authorization import is_branch_admin
from .services.promote_branch_admin import PromoteBranchAdminService, BranchAdminAlreadyAssigned, UserNotInBranch
from .services.remove_branch_admin import RemoveBranchAdminService, LastBranchAdminRemovalError
from .forms import PromoteBranchAdminForm, CommitteePositionManagementForm, RemoveBranchAdminForm, MatchAllocationForm
from django.contrib import messages
from .forms import MatchForm
from django.utils import timezone

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
    """Render the branch operations dashboard for branch admins."""

    branch = get_object_or_404(Branch, id=branch_id)
    if not is_branch_admin(request.user, branch):
        return render(request, "403.html", status=403)

    if request.method == "POST":
        if "match_submit" in request.POST:
            form = MatchForm(request.POST)
            allocation_form = MatchAllocationForm(request.POST, branch=branch)
            if form.is_valid() and allocation_form.is_valid():
                published = form.cleaned_data.get("published", False)
                with transaction.atomic():
                    match = form.save(commit=False)
                    match.published = published
                    match.save()
                    allocation_values = allocation_form.get_allocation_values()
                    for target_branch in Branch.objects.filter(pk__in=allocation_values.keys()).order_by("name"):
                        value = allocation_values.get(target_branch.pk, 0) or 0
                        MatchAllocation.objects.update_or_create(
                            branch=target_branch,
                            match=match,
                            defaults={"allocated_tickets": value, "updated_by": request.user},
                        )
                    if published:
                        previous_operational = branch.operational_match
                        if previous_operational and previous_operational.pk != match.pk:
                            previous_operational.published = False
                            previous_operational.save(update_fields=["published"])
                        branch.operational_match = match
                        branch.save(update_fields=["operational_match"])
                        messages.success(request, "Match created and published as the branch operational match.")
                    else:
                        if branch.operational_match_id == match.pk:
                            branch.operational_match = None
                            branch.save(update_fields=["operational_match"])
                        match.published = False
                        match.save(update_fields=["published"])
                        messages.success(request, "Match saved successfully.")
                return redirect("branch_committee", branch_id=branch.pk)
            messages.error(request, "Please correct the match form and allocation values and try again.")
        elif "promote" in request.POST:
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
    branch_matches = Match.objects.filter(published=True).order_by("date")

    supporter_email_query = request.GET.get("supporter_email", "").strip()
    supporter_search_results = []
    if supporter_email_query:
        supporter_search_results = (
            User.objects.filter(branch=branch, email__icontains=supporter_email_query)
            .exclude(
                branch_roles__branch=branch,
                branch_roles__role=BranchRole.Role.BRANCH_ADMIN,
                branch_roles__is_active=True,
            )
            .order_by("email")
            .distinct()[:10]
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
        "match_form": MatchForm(),
        "match_allocation_form": MatchAllocationForm(branch=branch),
        "branch_matches": branch_matches,
        "supporter_email_query": supporter_email_query,
        "supporter_search_results": supporter_search_results,
    })


@login_required
def match_management_view(request, branch_id):
    """Render a simple match management UI for branch admins.

    Allows creating matches scoped to the branch and publishing a match
    as the branch's operational match.
    """

    branch = get_object_or_404(Branch, id=branch_id)
    if not is_branch_admin(request.user, branch):
        return render(request, "403.html", status=403)

    if request.method == "POST":
        form = MatchForm(request.POST)
        allocation_form = MatchAllocationForm(request.POST, branch=branch)
        if form.is_valid() and allocation_form.is_valid():
            with transaction.atomic():
                match = form.save(commit=False)
                match.save()
                allocation_values = allocation_form.get_allocation_values()
                for target_branch in Branch.objects.filter(pk__in=allocation_values.keys()).order_by("name"):
                    value = allocation_values.get(target_branch.pk, 0) or 0
                    MatchAllocation.objects.update_or_create(
                        branch=target_branch,
                        match=match,
                        defaults={"allocated_tickets": value, "updated_by": request.user},
                    )
                if request.POST.get("publish"):
                    previous_operational = branch.operational_match
                    if previous_operational and previous_operational.pk != match.pk:
                        previous_operational.published = False
                        previous_operational.save(update_fields=["published"])
                    branch.operational_match = match
                    match.published = True
                    match.save(update_fields=["published"])
                    branch.save(update_fields=["operational_match"])
                    messages.success(request, "Match published as operational match.")
                else:
                    messages.success(request, "Match created successfully.")
            return redirect("branch_matches_manage", branch_id=branch.pk)
        messages.error(request, "Please correct the match form and allocation values and try again.")

    matches = Match.objects.filter(journeys__branch=branch).distinct().order_by("date")[:25]
    if not matches.exists():
        matches = Match.objects.order_by("date")[:25]
    form = MatchForm()
    allocation_form = MatchAllocationForm(branch=branch)

    return render(request, "branches/match_management.html", {
        "branch": branch,
        "matches": matches,
        "form": form,
        "match_allocation_form": allocation_form,
    })


@login_required
def match_edit_view(request, branch_id, match_id):
    """Edit an existing match for the branch while preserving the current admin workflow."""
    branch = get_object_or_404(Branch, id=branch_id)
    if not is_branch_admin(request.user, branch):
        return HttpResponseForbidden()

    match = get_object_or_404(Match, id=match_id)

    if request.method == "POST":
        form = MatchForm(request.POST, instance=match)
        allocation_form = MatchAllocationForm(request.POST, branch=branch, match=match)
        if form.is_valid() and allocation_form.is_valid():
            with transaction.atomic():
                form.save()
                allocation_values = allocation_form.get_allocation_values()
                matching_branches = Branch.objects.filter(pk__in=allocation_values.keys()).order_by("name")
                for target_branch in matching_branches:
                    value = allocation_values.get(target_branch.pk, 0) or 0
                    MatchAllocation.objects.update_or_create(
                        branch=target_branch,
                        match=match,
                        defaults={"allocated_tickets": value, "updated_by": request.user},
                    )
                MatchAllocation.objects.filter(match=match).exclude(branch__in=matching_branches).delete()
            messages.success(request, "Match updated successfully.")
            return redirect("branch_committee", branch_id=branch.pk)
        messages.error(request, "Please correct the match form and allocation values and try again.")
    else:
        form = MatchForm(instance=match)
        allocation_form = MatchAllocationForm(branch=branch, match=match)

    return render(request, "branches/edit_match.html", {
        "branch": branch,
        "match": match,
        "form": form,
        "allocation_form": allocation_form,
    })


@login_required
def match_publish_view(request, branch_id, match_id):
    branch = get_object_or_404(Branch, id=branch_id)
    if not is_branch_admin(request.user, branch):
        return render(request, "403.html", status=403)

    match = get_object_or_404(Match, id=match_id)
    # Toggle publish if already published; closing an active match finalizes the snapshot.
    if branch.operational_match_id == match.id:
        AnalyticsSnapshotService.generate_for_match(match)
        branch.operational_match = None
        branch.save(update_fields=["operational_match"])
        messages.success(request, "Operational match cleared and analytics finalized.")
    else:
        branch.operational_match = match
        branch.save(update_fields=["operational_match"])
        messages.success(request, "Match published as operational match.")

    return redirect("branch_matches_manage", branch_id=branch.pk)


@login_required
def supporter_verification_view(request, branch_id, supporter_id):
    """Allow branch admins to verify a supporter and continue ticket collection."""

    branch = get_object_or_404(Branch, id=branch_id)
    supporter = get_object_or_404(User, id=supporter_id)
    if not is_branch_admin(request.user, branch):
        return render(request, "403.html", status=403)

    next_path = request.POST.get("next") or request.GET.get("next")
    collection_code = request.POST.get("code", "") or request.GET.get("code", "")
    match_id = request.POST.get("match_id") or request.GET.get("match_id")

    if request.method == "POST":
        verification = (
            StudentVerification.objects.filter(
                user=supporter,
            )
            .order_by("-created_at")
            .first()
        )

        if verification is None:
            verification = StudentVerification.objects.create(
                user=supporter,
                student_number=f"auto-{supporter.pk}",
                university="BranchRoute",
                status=StudentVerificationStatus.PENDING,
            )

        if verification.status == StudentVerificationStatus.VERIFIED:
            should_redemption_run = bool(collection_code and match_id)
        else:
            VerifyStudentService.verify(verification, request.user)
            should_redemption_run = bool(collection_code and match_id)

        if should_redemption_run:
            try:
                match = get_object_or_404(Match, pk=match_id)
                CollectTicketService.collect(collection_code, request.user, branch=branch, match=match)
            except Exception as exc:
                messages.error(request, f"Verification succeeded but redemption failed: {exc}")
            else:
                messages.success(request, "Supporter verified and ticket redeemed successfully.")
            return redirect("match_operations_console", branch_id=branch.pk, match_id=match_id)

        messages.success(request, "Supporter verification completed.")
        return redirect("branch_committee", branch_id=branch.pk)

    return render(request, "branches/supporter_verification.html", {
        "branch": branch,
        "supporter": supporter,
        "next_path": next_path,
        "collection_code": collection_code,
        "match_id": match_id,
    })

