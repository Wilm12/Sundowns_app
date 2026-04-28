from rest_framework import generics, permissions

from authentication.permissions import IsAdminRole
from .models import Membership
from .serializers import MembershipSerializer


class MembershipListCreateView(generics.ListCreateAPIView):
    queryset = Membership.objects.all().order_by('-created_at')
    serializer_class = MembershipSerializer
    permission_classes = [IsAdminRole]


class MembershipDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer
    permission_classes = [IsAdminRole]


class MyMembershipsView(generics.ListAPIView):
    serializer_class = MembershipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Membership.objects.filter(
            user=self.request.user
        ).order_by('-created_at')
