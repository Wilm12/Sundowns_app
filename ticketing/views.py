from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from authentication.permissions import IsAdminRole
from .models import Ticket
from .serializers import TicketSerializer, TicketVerifySerializer


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