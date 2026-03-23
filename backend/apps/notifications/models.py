from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class Notification(TimeStampedModel):
    class NotificationType(models.TextChoices):
        DEADLINE_WARNING = "deadline_warning", "Fristwarnung"
        SYNC_ERROR = "sync_error", "Synchronisierungsfehler"
        AI_SUGGESTION = "ai_suggestion", "KI-Vorschlag"
        STATUS_CHANGE = "status_change", "Statusänderung"
        GENERAL = "general", "Allgemein"

    class Severity(models.TextChoices):
        INFO = "info", "Information"
        WARNING = "warning", "Warnung"
        URGENT = "urgent", "Dringend"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="Benutzer",
    )
    title = models.CharField(max_length=255, verbose_name="Titel")
    message = models.TextField(verbose_name="Nachricht")
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        verbose_name="Typ",
    )
    severity = models.CharField(
        max_length=10,
        choices=Severity.choices,
        default=Severity.INFO,
        verbose_name="Schweregrad",
    )
    is_read = models.BooleanField(default=False, verbose_name="Gelesen")
    action_url = models.CharField(max_length=500, blank=True, verbose_name="Aktions-URL")
    metadata = models.JSONField(default=dict, blank=True, verbose_name="Metadaten")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Benachrichtigung"
        verbose_name_plural = "Benachrichtigungen"

    def __str__(self):
        return f"{self.title} ({self.get_notification_type_display()})"
