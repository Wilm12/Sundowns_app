"""Branch serializers for API representation of branch data."""

from rest_framework import serializers
from .models import Branch, BranchPolicy, BranchRole


class BranchSerializer(serializers.ModelSerializer):
    """Serializer for branch data used by branch API endpoints."""

    class Meta:
        model = Branch
        fields = [
            'id',
            'name',
            'branch_code',
            'location',
            'description',
            'university',
            'meeting_point',
            'ticket_collection_point',
            'social_media_links',
            'contact_email',
            'contact_phone',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BranchPolicySerializer(serializers.ModelSerializer):
    """Serializer for branch policy data used by branch-related API endpoints."""

    class Meta:
        model = BranchPolicy
        fields = [
            'branch',
            'student_verification_required',
            'booking_deadline_hours',
            'maximum_bus_capacity',
            'attendance_threshold',
            'allow_guest_supporters',
            'announcement_requires_approval',
            'updated_at',
        ]
        read_only_fields = ['branch', 'updated_at']


class BranchRoleSerializer(serializers.ModelSerializer):
    """Serializer for operational branch role data."""

    class Meta:
        model = BranchRole
        fields = [
            'id',
            'branch',
            'user',
            'role',
            'assigned_at',
            'assigned_by',
            'is_active',
        ]
        read_only_fields = ['id', 'assigned_at']

