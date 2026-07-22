"""Branch serializers for API representation of branch data."""

from rest_framework import serializers
from .models import Branch


class BranchSerializer(serializers.ModelSerializer):
    """Serializer for branch data used by branch API endpoints."""

    class Meta:
        model = Branch
        fields = [
            'id',
            'name',
            'branch_code',
            'location',
            'contact_email',
            'contact_phone',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

