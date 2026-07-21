"""Serializers for authentication, registration, and JWT token handling.

This module validates registration data, enforces password policy, and issues
user profile responses for authenticated sessions.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for new user registration.

    Validates password confirmation, email uniqueness, and creates a new user
    with hashed credentials.
    """

    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'branch', 'password', 'password_confirm']

    def validate_email(self, value):
        """Validate that the submitted email address is unique."""

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, attrs):
        """Validate password confirmation and enforce Django password rules."""

        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Passwords do not match."})

        validate_password(attrs['password'])
        return attrs

    def create(self, validated_data):
        """Create a new user instance after removing confirmation data."""

        validated_data.pop('password_confirm')
        email = validated_data.get('email')
        validated_data['username'] = email.lower()
        return User.objects.create_user(**validated_data)


class MeSerializer(serializers.ModelSerializer):
    """Serializer exposing authenticated user profile data."""

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'branch']


class EmailTokenObtainPairSerializer(serializers.Serializer):
    """Serializer for validating credentials and issuing JWT refresh/access tokens."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Validate credentials and return authenticated JWT data."""

        email = attrs.get('email')
        password = attrs.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password.")

        if not user.check_password(password):
            raise serializers.ValidationError("Invalid email or password.")

        if not user.is_active:
            raise serializers.ValidationError("This account is inactive.")

        refresh = RefreshToken.for_user(user)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'branch': user.branch.id if user.branch else None,
            }
        }
