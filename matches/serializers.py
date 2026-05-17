"""Serializer for exposing match details in API responses."""

from rest_framework import serializers
from .models import Match


class MatchSerializer(serializers.ModelSerializer):
    """Serializer for match resource representation."""
    class Meta:
        model = Match
        fields = ['id', 'opponent', 'location', 'date']
