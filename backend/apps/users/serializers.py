from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "timezone",
            "daily_capacity_hours",
            "preferences",
            "is_staff",
            "is_active",
        ]
        read_only_fields = ["id", "username", "is_staff", "is_active"]
