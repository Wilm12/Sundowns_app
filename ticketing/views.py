"""Ticketing views for booking, verification, and ticket listing."""

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404, render

from matches.models import Match
from membership.models import Membership
from branches.models import BranchPolicy
from supporters.models import EligibilityReason, SupporterEligibility
from journeys.services.allocate_ticket import AllocateTicketService
from journeys.services.book_journey import BookJourneyService
from journeys.services.open_journey import OpenJourneyService
from .models import Ticket

from authentication.permissions import IsAdminRole
from .serializers import TicketSerializer, TicketVerifySerializer


def _book_complimentary_ticket_for_user(user, match):
    """Create a Journey and allocate a complimentary ticket through the Journey lifecycle."""
    branch = user.branch
    if branch is None:
        raise ValueError("User must be assigned to a branch before booking a ticket.")

    BranchPolicy.objects.get_or_create(branch=branch)
    eligibility, _ = SupporterEligibility.objects.get_or_create(
        supporter=user,
        defaults={
            "is_eligible": True,
            "reason": EligibilityReason.MANUAL_OVERRIDE,
        },
    )
    if not eligibility.is_eligible:
        raise ValueError("Supporter is not currently eligible to start a journey.")

    journey = OpenJourneyService.open_journey(supporter=user, branch=branch, match=match)
    journey = BookJourneyService.book_journey(journey)
    journey = AllocateTicketService.allocate(journey)
    return journey.ticket


@login_required
def my_tickets_page(request):
    """Render the current user's ticket history page."""

    tickets = Ticket.objects.filter(
        user=request.user
    ).order_by("-created_at")

    return render(
        request,
        "ticketing/my_tickets.html",
        {"tickets": tickets}
    )


class TicketVerifyView(APIView):
    """Admin-only API view for verifying a ticket QR code."""

    permission_classes = [IsAdminRole]

    def post(self, request):
        serializer = TicketVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ticket = serializer.validated_data["ticket"]
        ticket.status = "used"
        ticket.save()

        return Response(
            {
                "message": "Ticket verified successfully.",
                "ticket": TicketSerializer(ticket).data,
            },
            status=status.HTTP_200_OK
        )


class TicketListCreateView(generics.ListCreateAPIView):
    """API endpoint for listing and booking tickets for the authenticated user."""

    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Ticket.objects.filter(
            user=self.request.user
        ).order_by("-created_at")

    def perform_create(self, serializer):
        match = serializer.validated_data["match"]
        ticket = _book_complimentary_ticket_for_user(self.request.user, match)
        serializer.instance = ticket


class TicketDetailView(generics.RetrieveUpdateDestroyAPIView):
    """API endpoint for ticket detail, update, and delete operations."""

    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Ticket.objects.filter(user=self.request.user)


class MyTicketsView(generics.ListAPIView):
    """API endpoint listing the authenticated user's tickets."""

    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Ticket.objects.filter(
            user=self.request.user
        ).order_by("-created_at")


@login_required
def book_ticket_page(request, match_id):
    """Book a ticket for a match if the user has an active membership."""

    match = get_object_or_404(Match, id=match_id)

    has_active_membership = Membership.objects.filter(
        user=request.user,
        status="active"
    ).exists()

    if not has_active_membership:
        messages.error(
            request,
            "You need an active membership to book tickets. Please complete payment to activate your membership."
        )
        return redirect("/payments/")

    existing_ticket = Ticket.objects.filter(
        user=request.user,
        match=match
    ).first()

    if existing_ticket:
        messages.error(request, "You already have a ticket for this match.")
        return redirect("/matches/")

    ticket = _book_complimentary_ticket_for_user(request.user, match)

    messages.success(request, "Ticket booked successfully.")
    return redirect("transport_prompt_page", ticket_id=ticket.id)


@login_required
def transport_prompt_page(request, ticket_id):
    """Prompt the user to select transport after booking a ticket."""
    ticket = get_object_or_404(
        Ticket,
        id=ticket_id,
        user=request.user
    )

    if request.method == "POST":
        choice = request.POST.get("transport_choice")

        if choice == "yes":
            return redirect("/transport/")

        if choice == "no":
            return redirect("my_tickets_page")

    return render(
        request,
        "ticketing/transport_prompt.html",
        {"ticket": ticket}
    )


@login_required
def verify_ticket_page(request):
    """Render the ticket verification page and process admin ticket verification."""

    if request.user.role != "admin":
        messages.error(request, "Only admins can verify tickets.")
        return redirect("dashboard")

    if request.method == "POST":
        qr_code = request.POST.get("qr_code")

        ticket = Ticket.objects.filter(qr_code=qr_code).first()

        if not ticket:
            messages.error(request, "Invalid ticket QR code.")
            return redirect("verify_ticket_page")

        if ticket.status != "booked":
            messages.error(
                request,
                f"Ticket cannot be verified because it is {ticket.status}."
            )
            return redirect("verify_ticket_page")

        ticket.status = "used"
        ticket.save()

        messages.success(request, "Ticket verified successfully.")
        return redirect("verify_ticket_page")

    return render(request, "ticketing/verify_ticket.html")
