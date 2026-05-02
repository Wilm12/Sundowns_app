from rest_framework import serializers
from .models import Transport, TransportBooking, TransportSettlement


class TransportSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    opponent = serializers.CharField(source='match.opponent', read_only=True)
    available_seats = serializers.SerializerMethodField()

    class Meta:
        model = Transport
        fields = [
            'id',
            'branch',
            'branch_name',
            'match',
            'opponent',
            'owner_id',
            'capacity',
            'available_seats',
            'status',
            'created_at',
        ]

    def get_available_seats(self, obj):
        return obj.available_seats()


class TransportBookingSerializer(serializers.ModelSerializer):
    ticket_qr = serializers.UUIDField(source='ticket.qr_code', read_only=True)

    class Meta:
        model = TransportBooking
        fields = [
            'id',
            'ticket',
            'ticket_qr',
            'transport',
            'status',
            'verified_at',
            'created_at',
        ]

    def validate(self, attrs):
        ticket = attrs.get('ticket')
        transport = attrs.get('transport')

        if ticket and ticket.status != 'booked':
            raise serializers.ValidationError({
                'ticket': 'Only booked tickets can be used for transport booking.'
            })

        if ticket and transport and transport.match and ticket.match_id != transport.match_id:
            raise serializers.ValidationError({
                'transport': 'Transport must be for the same match as the ticket.'
            })

        if transport and transport.status != 'active':
            raise serializers.ValidationError({
                'transport': 'Transport is not active.'
            })

        if transport and transport.available_seats() <= 0:
            raise serializers.ValidationError({
                'transport': 'No seats available.'
            })

        return attrs


class TransportSettlementSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransportSettlement
        fields = [
            'id',
            'transport',
            'owner_id',
            'amount',
            'status',
            'payment_date',
            'created_at',
        ]
