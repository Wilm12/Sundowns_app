from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from .serializers import RegisterSerializer
from .permissions import IsAdminRole, IsMemberRole
from .serializers import RegisterSerializer, MeSerializer, EmailTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = EmailTokenObtainPairSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = MeSerializer(request.user)
        return Response(serializer.data)


class AdminOnlyView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        return Response({"message": "Welcome, admin."})


class MemberOnlyView(APIView):
    permission_classes = [IsMemberRole]

    def get(self, request):
        return Response({"message": "Welcome, member."})

def login_page(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect("home")

        messages.error(request, "Invalid username or password.")

    return render(request, "authentication/login.html")


def logout_page(request):
    logout(request)
    return redirect("home")

def register_page(request):
    if request.method == "POST":
        serializer = RegisterSerializer(data=request.POST)

        if serializer.is_valid():
            serializer.save()
            messages.success(request, "Account created successfully. You can now log in.")
            return redirect("login_page")

        for field, errors in serializer.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")

    return render(request, "authentication/register.html")