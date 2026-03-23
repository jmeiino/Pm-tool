import logging

from django.utils import timezone

from config.celery import app

logger = logging.getLogger(__name__)


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def poll_microsoft_calendar(self, integration_id: int):
    """Periodischer Task: Kalender-Termine aus Microsoft 365 abrufen."""
    from apps.integrations.models import IntegrationConfig
    from apps.notifications.services import NotificationService

    from .sync import MicrosoftSyncService

    try:
        integration = IntegrationConfig.objects.get(id=integration_id)
    except IntegrationConfig.DoesNotExist:
        logger.error("Integration %s nicht gefunden", integration_id)
        return

    try:
        sync_service = MicrosoftSyncService(integration)
        sync_service.sync_inbound()

        integration.last_synced_at = timezone.now()
        integration.sync_status = IntegrationConfig.SyncStatus.IDLE
        integration.save(update_fields=["last_synced_at", "sync_status", "updated_at"])
    except Exception as exc:
        integration.sync_status = IntegrationConfig.SyncStatus.ERROR
        integration.save(update_fields=["sync_status", "updated_at"])

        NotificationService.create_notification(
            user=integration.user,
            title="Microsoft-Sync fehlgeschlagen",
            message=str(exc),
            notification_type="sync_error",
            severity="warning",
        )
        raise self.retry(exc=exc)
