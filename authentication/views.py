"""Views for authentication workflows and user token management.

This module contains class-based and function-based views for registration,
login, session management, and role-restricted access checks.
"""

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from branches.models import Branch
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from .serializers import RegisterSerializer
from .permissions import IsAdminRole, IsMemberRole
from .serializers import RegisterSerializer, MeSerializer, EmailTokenObtainPairSerializer


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
            return redirect("membership_page")

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
                return redirect("membership_page")

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