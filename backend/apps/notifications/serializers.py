from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    notification_type_display = serializers.CharField(
        source="get_notification_type_display", read_only=True
    )
    severity_display = serializers.CharField(
        source="get_severity_display", read_only=True
    )

    class Meta:
        model = Notification
        fields = [
            "id", "user", "title", "message", "notification_type",
            "notification_type_display", "severity", "severity_display",
            "is_read", "action_url", "metadata", "created_at", "updated_at",
        ]
        read_only_fields = ["user", "created_at", "updated_at"]
