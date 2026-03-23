from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    """ViewSet für Benachrichtigungen."""

    serializer_class = NotificationSerializer
    filterset_fields = ["notification_type", "severity", "is_read"]
    ordering_fields = ["created_at", "severity"]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read(self, request, pk=None):
        """Markiert eine einzelne Benachrichtigung als gelesen."""
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response(NotificationSerializer(notification).data)

    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request):
        """Markiert alle Benachrichtigungen des Benutzers als gelesen."""
        count = self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({"marked_read": count})
