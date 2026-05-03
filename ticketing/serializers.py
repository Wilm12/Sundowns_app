from rest_framework import serializers

from membership.models import Membership
from .models import Ticket


class TicketSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    opponent = serializers.CharField(source='match.opponent', read_only=True)
    match_date = serializers.DateTimeField(source='match.date', read_only=True)
    match_location = serializers.CharField(source='match.location', read_only=True)

    class Meta:
        model = Ticket
        fields = [
            'id',
            'user',
            'username',
            'email',
            'match',
            'opponent',
            'match_date',
            'match_location',
            'qr_code',
            'status',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'user',
            'username',
            'email',
            'opponent',
            'match_date',
            'match_location',
            'qr_code',
            'created_at',
        ]

    def validate(self, attrs):
        request = self.context.get('request')
        user = request.user if request and request.user.is_authenticated else None
        match = attrs.get('match')

        if user and not Membership.objects.filter(user=user, status='active').exists():
            raise serializers.ValidationError({
                'user': 'User must have an active membership to book a ticket.'
            })

        if user and match and Ticket.objects.filter(user=user, match=match).exists():
            raise serializers.ValidationError({
                'ticket': 'User already has a ticket for this match.'
            })

        return attrs


class TicketVerifySerializer(serializers.Serializer):
    qr_code = serializers.UUIDField()

    def validate(self, attrs):
        qr_code = attrs.get('qr_code')

        try:
            ticket = Ticket.objects.get(qr_code=qr_code)
        except Ticket.DoesNotExist:
            raise serializers.ValidationError({
                'qr_code': 'Invalid ticket QR code.'
            })

        if ticket.status != 'booked':
            raise serializers.ValidationError({
                'ticket': f'Ticket cannot be verified because it is {ticket.status}.'
            })

        attrs['ticket'] = ticket
        return attrs