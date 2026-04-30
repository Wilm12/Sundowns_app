from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    membership_tier = serializers.CharField(source='membership.tier', read_only=True)
    expected_amount = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            'id',
            'user',
            'username',
            'email',
            'membership',
            'membership_tier',
            'amount',
            'expected_amount',
            'status',
            'reference',
            'paid_at',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'username',
            'email',
            'membership_tier',
            'expected_amount',
            'created_at',
        ]

    def get_expected_amount(self, obj):
        return obj.membership.expected_price()

def validate(self, attrs):
    membership = attrs.get('membership')
    amount = attrs.get('amount')
    user = attrs.get('user')

    if membership and amount:
        expected = membership.expected_price()
        if amount != expected:
            raise serializers.ValidationError({
                'amount': f'Amount must be {expected} for {membership.tier} membership.'
            })

    if user and membership and membership.user_id != user.id:
        raise serializers.ValidationError({
            'user': 'Payment user must match the membership user.'
        })

    return attrs
