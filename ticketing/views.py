from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404, render

from matches.models import Match
from membership.models import Membership
from .models import Ticket

from authentication.permissions import IsAdminRole
from .models import Ticket
from .serializers import TicketSerializer, TicketVerifySerializer

@login_required
def my_tickets_page(request):
    tickets = Ticket.objects.filter(
        user=request.user
    ).order_by("-created_at")

    return render(
        request,
        "ticketing/my_tickets.html",
        {"tickets": tickets}
    )
class TicketVerifyView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request):
        serializer = TicketVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ticket = serializer.validated_data['ticket']
        ticket.status = 'used'
        ticket.save()

        return Response(
            {
                'message': 'Ticket verified successfully.',
                'ticket': TicketSerializer(ticket).data,
            },
            status=status.HTTP_200_OK
        )


class TicketListCreateView(generics.ListCreateAPIView):
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Ticket.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TicketDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Ticket.objects.filter(user=self.request.user)


class MyTicketsView(generics.ListAPIView):
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Ticket.objects.filter(user=self.request.user).order_by('-created_at')

@login_required
def book_ticket_page(request, match_id):
    match = get_object_or_404(Match, id=match_id)

    has_active_membership = Membership.objects.filter(
        user=request.user,
        status="active"
    ).exists()

    if not has_active_membership:
        messages.error(request, "You need an active membership to book a ticket.")
        return redirect("match_list_page")

    existing_ticket = Ticket.objects.filter(
        user=request.user,
        match=match
    ).first()

    if existing_ticket:
        messages.error(request, "You already have a ticket for this match.")
        return redirect("match_list_page")

    Ticket.objects.create(
        user=request.user,
        match=match,
        status="booked"
    )

    messages.success(request, "Ticket booked successfully.")
    return redirect("match_list_page")