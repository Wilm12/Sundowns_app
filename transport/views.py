from rest_framework import generics, permissions
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from ticketing.models import Ticket
from .models import Transport, TransportBooking

from authentication.permissions import IsAdminRole, IsAdminOrReadOnly
from .models import Transport, TransportBooking, TransportSettlement
from .serializers import (
    TransportSerializer,
    TransportBookingSerializer,
    TransportSettlementSerializer,
)


class TransportListCreateView(generics.ListCreateAPIView):
    queryset = Transport.objects.all().order_by('-created_at')
    serializer_class = TransportSerializer
    permission_classes = [IsAdminOrReadOnly]


class TransportDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Transport.objects.all()
    serializer_class = TransportSerializer
    permission_classes = [IsAdminOrReadOnly]


class TransportBookingListCreateView(generics.ListCreateAPIView):
    serializer_class = TransportBookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TransportBooking.objects.filter(
            ticket__user=self.request.user
        ).order_by('-created_at')


class TransportBookingDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TransportBookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TransportBooking.objects.filter(
            ticket__user=self.request.user
        )


class MyTransportBookingsView(generics.ListAPIView):
    serializer_class = TransportBookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TransportBooking.objects.filter(
            ticket__user=self.request.user
        ).order_by('-created_at')


class TransportSettlementListCreateView(generics.ListCreateAPIView):
    queryset = TransportSettlement.objects.all().order_by('-created_at')
    serializer_class = TransportSettlementSerializer
    permission_classes = [IsAdminRole]


class TransportSettlementDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TransportSettlement.objects.all()
    serializer_class = TransportSettlementSerializer
    permission_classes = [IsAdminRole]

@login_required
def transport_list_page(request):
    tickets = Ticket.objects.filter(
        user=request.user,
        status='booked'
    ).select_related('match')

    transports = Transport.objects.filter(
        status='active'
    ).select_related('branch', 'match').order_by('-created_at')

    return render(request, 'transport/list.html', {
        'tickets': tickets,
        'transports': transports,
    })


@login_required
def book_transport_page(request, transport_id, ticket_id):
    transport = get_object_or_404(Transport, id=transport_id)
    ticket = get_object_or_404(Ticket, id=ticket_id, user=request.user)

    if ticket.status != 'booked':
        messages.error(request, 'Only booked tickets can be used for transport booking.')
        return redirect('transport_list_page')

    if transport.match and ticket.match_id != transport.match_id:
        messages.error(request, 'Transport must be for the same match as your ticket.')
        return redirect('transport_list_page')

    if transport.status != 'active':
        messages.error(request, 'This transport is not active.')
        return redirect('transport_list_page')

    if transport.available_seats() <= 0:
        messages.error(request, 'No seats available for this transport.')
        return redirect('transport_list_page')

    existing_booking = TransportBooking.objects.filter(ticket=ticket).first()

    if existing_booking:
        messages.error(request, 'This ticket already has a transport booking.')
        return redirect('my_transport_bookings_page')

    TransportBooking.objects.create(
        ticket=ticket,
        transport=transport,
        status='booked'
    )

    messages.success(request, 'Transport booked successfully.')
    return redirect('my_transport_bookings_page')


@login_required
def my_transport_bookings_page(request):
    bookings = TransportBooking.objects.filter(
        ticket__user=request.user
    ).select_related('ticket', 'ticket__match', 'transport', 'transport__branch')

    return render(request, 'transport/my_bookings.html', {
        'bookings': bookings,
    })