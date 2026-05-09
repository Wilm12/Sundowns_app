from django.contrib.auth.decorators import login_required
from django.shortcuts import render


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
