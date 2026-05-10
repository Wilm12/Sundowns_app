from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from branches.models import Branch
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta

from users.models import User
from membership.models import Membership
from ticketing.models import Ticket
from transport.models import TransportBooking

@login_required
def dashboard_view(request):
    from membership.models import Membership
    from ticketing.models import Ticket
    from transport.models import TransportBooking
    from matches.models import Match

    membership = Membership.objects.filter(
        user=request.user
    ).order_by("-start_date").first()

    tickets_count = Ticket.objects.filter(
        user=request.user
    ).count()

    transport_bookings_count = TransportBooking.objects.filter(
        ticket__user=request.user
    ).count()

    upcoming_matches_count = Match.objects.count()

    return render(request, "dashboard.html", {
        "membership": membership,
        "tickets_count": tickets_count,
        "transport_bookings_count": transport_bookings_count,
        "upcoming_matches_count": upcoming_matches_count,
    })


def home_view(request):
    return render(request, "home.html")

@login_required
def admin_dashboard_view(request):
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