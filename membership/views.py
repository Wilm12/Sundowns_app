from rest_framework import generics, permissions

from authentication.permissions import IsAdminRole
from .models import Membership
from .serializers import MembershipSerializer
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Membership


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

@login_required
def membership_page(request):
    membership = Membership.objects.filter(
        user=request.user
    ).order_by('-start_date').first()

    return render(request, 'membership/membership.html', {
        'membership': membership,
    })
