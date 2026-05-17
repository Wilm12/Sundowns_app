"""Serializer for user profile data and branch metadata."""

from rest_framework import serializers
from .models import User


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer exposing the authenticated user's profile and branch name."""
    branch_name = serializers.CharField(source='branch.name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'role',
            'branch',
            'branch_name',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'role',
            'created_at',
        ]
