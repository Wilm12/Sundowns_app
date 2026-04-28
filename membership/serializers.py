from rest_framework import serializers
from .models import Membership


class MembershipSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    expected_price = serializers.SerializerMethodField()

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
            'created_at',
        ]
        read_only_fields = [
            'id',
            'username',
            'email',
            'expected_price',
            'created_at',
        ]

    def get_expected_price(self, obj):
        return obj.expected_price()
