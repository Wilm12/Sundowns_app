"""Membership API and page views for managing membership lifecycle."""

from rest_framework import generics, permissions

from authentication.permissions import IsAdminRole
from .models import Membership
from .serializers import MembershipSerializer
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from .tier_rules import TIER_RULES, get_all_tiers


class MembershipListCreateView(generics.ListCreateAPIView):
    """Admin API endpoint for listing and creating memberships."""

    queryset = Membership.objects.all().order_by('-created_at')
    serializer_class = MembershipSerializer
    permission_classes = [IsAdminRole]


class MembershipDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Admin API endpoint for retrieving, updating, and deleting memberships."""
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer
    permission_classes = [IsAdminRole]


class MyMembershipsView(generics.ListAPIView):
    """API endpoint returning memberships for the current authenticated user."""

    serializer_class = MembershipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Membership.objects.filter(
            user=self.request.user
        ).order_by('-created_at')


@login_required
def membership_page(request):
    """Render the membership summary page for the authenticated user."""
    membership = Membership.objects.filter(
        user=request.user
    ).order_by('-created_at').first()

    if request.method == 'POST':
        selected_tier = request.POST.get('tier')

        if selected_tier not in TIER_RULES:
            return redirect('membership_page')

        if membership and membership.tier == selected_tier:
            return redirect('membership_page')

        if not membership:
            membership = Membership.objects.create(
                user=request.user,
                tier=selected_tier,
                status='pending',
                start_date=timezone.now().date(),
            )
        else:
            membership.tier = selected_tier
            membership.status = 'pending'
            membership.start_date = timezone.now().date()
            membership.expiry_date = None
            membership.save()

        return redirect('payment_page')

    return render(request, 'membership/membership.html', {
        'membership': membership,
        'tier_rules': get_all_tiers(),
    })
