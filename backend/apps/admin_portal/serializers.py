from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class AdminUserSerializer(serializers.ModelSerializer):
    """Serializer fuer die Admin-Benutzerverwaltung."""

    full_name = serializers.SerializerMethodField()
    project_count = serializers.SerializerMethodField()
    integration_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "is_staff",
            "is_active",
            "timezone",
            "daily_capacity_hours",
            "date_joined",
            "last_login",
            "project_count",
            "integration_count",
        ]
        read_only_fields = ["id", "date_joined", "last_login", "full_name"]

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username

    def get_project_count(self, obj):
        return obj.owned_projects.count() if hasattr(obj, "owned_projects") else 0

    def get_integration_count(self, obj):
        return obj.integration_configs.count() if hasattr(obj, "integration_configs") else 0


class AdminUserCreateSerializer(serializers.ModelSerializer):
    """Serializer zum Erstellen neuer Benutzer."""

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
            "is_staff",
            "is_active",
            "timezone",
            "daily_capacity_hours",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
