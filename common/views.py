"""Common views for dashboard, settings, and shared user workflows."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from branches.models import Branch
from branches.services.authorization import is_branch_admin
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm

from users.models import User
from membership.models import Membership
from ticketing.models import Ticket
from transport.models import TransportBooking
from supporters.models import StudentVerification, StudentVerificationStatus, SupporterEligibility

from django.http import JsonResponse
from django.db import connection

@login_required
def dashboard_view(request):
    """Render the user dashboard with membership, ticket, transport, and match counts."""

    from membership.models import Membership
    from ticketing.models import Ticket
    from transport.models import TransportBooking
    from matches.models import Match

    if is_branch_admin(request.user):
        return redirect("branch_admin_dashboard")

    membership = Membership.objects.filter(
        user=request.user
    ).order_by("-start_date").first()

    tickets_count = Ticket.objects.filter(
        user=request.user
    ).count()

    transport_bookings_count = TransportBooking.objects.filter(
        ticket__user=request.user
    ).count()

    upcoming_matches_count = Match.objects.filter(published=True).count()

    from notifications.models import Notification
    latest_notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')[:5]

    verification = (
        StudentVerification.objects.filter(user=request.user)
        .order_by('-created_at')
        .first()
    )
    eligibility = (
        SupporterEligibility.objects.filter(supporter=request.user)
        .order_by('-updated_at')
        .first()
    )

    # A supporter is only 'Active' after a successful verification approval.
    if verification and verification.status in {
        StudentVerificationStatus.APPROVED,
        StudentVerificationStatus.VERIFIED,
    } and (verification.expires_at is None or verification.expires_at > timezone.now()):
        supporter_status = "Active"
        supporter_status_detail = "Verified and eligible for booking and redemption."
    elif verification and verification.status == StudentVerificationStatus.REJECTED:
        supporter_status = "Inactive"
        supporter_status_detail = "Verification was rejected."
    elif verification and verification.status == StudentVerificationStatus.PENDING:
        supporter_status = "Pending"
        supporter_status_detail = "Awaiting branch verification."
    else:
        # Booking should not affect activation; eligibility alone does not make the supporter Active.
        supporter_status = "Inactive"
        if eligibility and eligibility.is_eligible:
            supporter_status_detail = "Eligible but unverified; complete branch verification to activate."
        else:
            supporter_status_detail = "Verification is still required."

    display_name = (
        request.user.first_name
        or request.user.username
        or request.user.email
        or "there"
    )

    return render(request, "dashboard.html", {
        "membership": membership,
        "tickets_count": tickets_count,
        "transport_bookings_count": transport_bookings_count,
        "upcoming_matches_count": upcoming_matches_count,
        "latest_notifications": latest_notifications,
        "display_name": display_name,
        "supporter_status": supporter_status,
        "supporter_status_detail": supporter_status_detail,
    })


def home_view(request):
    """Render the public home page."""

    return render(request, "home.html")


@login_required
def admin_dashboard_view(request):
    """Render the admin dashboard, restricting access to admin users only."""

    if request.user.role != "admin":
        messages.error(request, "Only admins can access the admin dashboard.")
        return redirect("dashboard")

    total_users = User.objects.count()

    active_memberships = Membership.objects.filter(
        status="active"
    ).count()

    total_tickets = Ticket.objects.count()

    verified_tickets = Ticket.objects.filter(
        status="used"
    ).count()

    total_transport_bookings = TransportBooking.objects.count()

    return render(request, "admin_dashboard.html", {
        "total_users": total_users,
        "active_memberships": active_memberships,
        "total_tickets": total_tickets,
        "verified_tickets": verified_tickets,
        "total_transport_bookings": total_transport_bookings,
    })


@login_required
def user_settings_view(request):
    """Render and process the user settings page, including branch changes."""

    branches = Branch.objects.all().order_by("name")

    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        new_branch_id = request.POST.get("branch")

        request.user.username = username
        request.user.email = email

        current_branch_id = request.user.branch_id

        if new_branch_id and str(current_branch_id) != str(new_branch_id):
            today = timezone.now().date()

            if not request.user.branch_change_window_start:
                request.user.branch_change_window_start = today
                request.user.branch_change_count = 0

            window_end = request.user.branch_change_window_start + timedelta(days=365)

            if today > window_end:
                request.user.branch_change_window_start = today
                request.user.branch_change_count = 0

            if request.user.branch_change_count >= 2:
                messages.error(
                    request,
                    "You can only change your branch twice within a 12-month period."
                )
                return redirect("user_settings")

            request.user.branch_id = new_branch_id
            request.user.branch_change_count += 1

        request.user.save()

        messages.success(request, "Settings updated successfully.")
        return redirect("user_settings")

    return render(request, "settings.html", {
        "branches": branches,
    })


@login_required
def change_password_view(request):
    """Process a password change request and update the user session."""

    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)

        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)

            messages.success(request, "Password changed successfully.")
            return redirect("user_settings")

        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, error)

    return redirect("user_settings")

def health_check(request):
    """
    Basic health check endpoint for deployment and container monitoring.
    Verifies that the Django app can respond and connect to the database.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")

        return JsonResponse({
            "status": "healthy",
            "database": "connected",
        })

    except Exception:
        return JsonResponse({
            "status": "unhealthy",
            "database": "disconnected",
        }, status=500)