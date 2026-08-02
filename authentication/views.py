"""Views for authentication workflows and user token management.

This module contains class-based and function-based views for registration,
login, session management, and role-restricted access checks.
"""

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from branches.models import Branch
from branches.services.authorization import is_branch_admin
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.utils.http import url_has_allowed_host_and_scheme
from .serializers import RegisterSerializer
from .permissions import IsAdminRole, IsMemberRole
from .serializers import RegisterSerializer, MeSerializer, EmailTokenObtainPairSerializer


def _get_post_login_redirect(request, user):
    next_url = request.POST.get("next") or request.GET.get("next")

    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return redirect(next_url)

    if user.is_superuser:
        return redirect("/admin/")

    if is_branch_admin(user):
        return redirect("branch_admin_dashboard")

    return redirect("membership_page")


class RegisterView(generics.CreateAPIView):
    """API view for creating new user accounts.

    Allows unauthenticated access for account creation while enforcing serializer
    validation for passwords, email uniqueness, and branch assignment.
    """

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class LoginView(APIView):
    """API view for issuing JWT tokens after user authentication."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = EmailTokenObtainPairSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class MeView(APIView):
    """API view returning the authenticated user's profile data."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = MeSerializer(request.user)
        return Response(serializer.data)


class AdminOnlyView(APIView):
    """API view accessible only to admin users."""

    permission_classes = [IsAdminRole]

    def get(self, request):
        return Response({"message": "Welcome, admin."})


class MemberOnlyView(APIView):
    """API view accessible only to member users."""

    permission_classes = [IsMemberRole]

    def get(self, request):
        return Response({"message": "Welcome, member."})


def login_page(request):
    """Render and process the authentication login page."""
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(
            request,
            email=email,
            password=password
        )

        if user is not None:
            login(request, user)
            return _get_post_login_redirect(request, user)

        messages.error(request, "Invalid email or password.")

    return render(request, "authentication/login.html")


def logout_page(request):
    """Log out the current user and redirect to the home page."""

    logout(request)
    return redirect("home")


def register_page(request):
    """Render and process the user registration page."""

    branches = Branch.objects.all().order_by("name")

    if request.method == "POST":
        serializer = RegisterSerializer(data=request.POST)

        if serializer.is_valid():
            user = serializer.save()
            authenticated_user = authenticate(
                request,
                email=user.email,
                password=request.POST.get("password"),
            )

            if authenticated_user is not None:
                login(request, authenticated_user)
                return _get_post_login_redirect(request, authenticated_user)

            messages.success(
                request,
                "Account created successfully. You can now log in."
            )
            return redirect("login_page")

        for field, errors in serializer.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")

    return render(request, "authentication/register.html", {
        "branches": branches,
    })