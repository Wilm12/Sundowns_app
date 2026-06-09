"""Serializer for membership details and computed membership pricing."""

from rest_framework import serializers
from .models import Membership


class MembershipSerializer(serializers.ModelSerializer):
    """Serializer exposing membership and related user data."""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    expected_price = serializers.SerializerMethodField()
    merchandise_discount = serializers.SerializerMethodField()
    transport_eligibility = serializers.SerializerMethodField()
    promotion_categories = serializers.SerializerMethodField()

    class Meta:
        model = Membership
        fields = [
            'id',
            'user',
            'username',
            'email',
            'tier',
            'status',
            'start_date',
            'expiry_date',
            'expected_price',
            'merchandise_discount',
            'transport_eligibility',
            'promotion_categories',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'username',
            'email',
            'expected_price',
            'merchandise_discount',
            'transport_eligibility',
            'promotion_categories',
            'created_at',
        ]

    def get_expected_price(self, obj):
        """Return the computed price for the membership tier."""
        return obj.expected_price()

    def get_merchandise_discount(self, obj):
        """Return the merchandise discount percentage used for dashboards and pricing."""
        return obj.get_merchandise_discount()

    def get_transport_eligibility(self, obj):
        """Return the transport eligibility category used for dashboards and booking flow."""
        return obj.get_transport_eligibility()

    def get_promotion_categories(self, obj):
        """Return promotion category access for the membership tier."""
        return obj.get_promotion_categories()
