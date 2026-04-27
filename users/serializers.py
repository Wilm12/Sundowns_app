from rest_framework import serializers
from .models import User


class UserProfileSerializer(serializers.ModelSerializer):
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
