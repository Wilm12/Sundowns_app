from rest_framework import generics, permissions

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