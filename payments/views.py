from rest_framework import generics, permissions
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from membership.models import Membership
from .models import Payment

from authentication.permissions import IsAdminRole
from .models import Payment
from .serializers import PaymentSerializer


class PaymentListCreateView(generics.ListCreateAPIView):
    queryset = Payment.objects.all().order_by('-created_at')
    serializer_class = PaymentSerializer
    permission_classes = [IsAdminRole]


class PaymentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAdminRole]


class MyPaymentsView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(
            user=self.request.user
        ).order_by('-created_at')

@login_required
def payment_page(request):
    membership = Membership.objects.filter(
        user=request.user
    ).order_by("-start_date").first()

    payments = Payment.objects.filter(
        membership=membership
    ).order_by("-created_at") if membership else []

    expected_amount = membership.expected_price() if membership else None

    return render(request, "payments/payments.html", {
        "membership": membership,
        "payments": payments,
        "expected_amount": expected_amount,
    })


@login_required
def create_membership_payment_page(request):
    membership = Membership.objects.filter(
        user=request.user
    ).order_by("-start_date").first()

    if not membership:
        messages.error(request, "No membership found.")
        return redirect("payment_page")

    Payment.objects.create(
        user=request.user,
        membership=membership,
        amount=membership.expected_price(),
        status="success",
    )

    messages.success(request, "Payment successful. Membership activated.")
    return redirect("payment_page")
