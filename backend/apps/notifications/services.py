import logging
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Notification

logger = logging.getLogger(__name__)
User = get_user_model()


class NotificationService:
    """Service-Klasse fuer das Erstellen und Verwalten von Benachrichtigungen."""

    @staticmethod
    def create_notification(
        user,
        title: str,
        message: str,
        notification_type: str = Notification.NotificationType.GENERAL,
        severity: str = Notification.Severity.INFO,
        action_url: str = "",
        metadata: dict | None = None,
    ) -> Notification:
        """Erstellt eine neue Benachrichtigung fuer einen Benutzer."""
        return Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            severity=severity,
            action_url=action_url,
            metadata=metadata or {},
        )

    @staticmethod
    def create_deadline_warnings(days_ahead: int = 2) -> int:
        """Erstellt Fristwarnungen fuer Aufgaben, deren Deadline bald erreicht wird.

        Args:
            days_ahead: Anzahl der Tage im Voraus, fuer die Warnungen erstellt werden.

        Returns:
            Anzahl der erstellten Benachrichtigungen.
        """
        from apps.todos.models import PersonalTodo

        now = timezone.now()
        warning_threshold = now + timedelta(days=days_ahead)

        upcoming_todos = PersonalTodo.objects.filter(
            due_date__lte=warning_threshold,
            due_date__gt=now,
            status__in=["open", "in_progress"],
        ).select_related("user")

        created_count = 0
        for todo in upcoming_todos:
            # Pruefen ob bereits eine Warnung fuer diese Aufgabe existiert
            already_warned = Notification.objects.filter(
                user=todo.user,
                notification_type=Notification.NotificationType.DEADLINE_WARNING,
                metadata__todo_id=todo.id,
                created_at__gte=now - timedelta(days=1),
            ).exists()

            if not already_warned:
                days_remaining = (todo.due_date - now.date()).days if hasattr(todo.due_date, "year") else (todo.due_date - now).days
                severity = (
                    Notification.Severity.URGENT
                    if days_remaining <= 1
                    else Notification.Severity.WARNING
                )
                NotificationService.create_notification(
                    user=todo.user,
                    title=f"Fristwarnung: {todo.title}",
                    message=f"Die Aufgabe \"{todo.title}\" ist in {days_remaining} Tag(en) faellig.",
                    notification_type=Notification.NotificationType.DEADLINE_WARNING,
                    severity=severity,
                    metadata={"todo_id": todo.id},
                )
                created_count += 1

        logger.info("%d Fristwarnungen erstellt.", created_count)
        return created_count
