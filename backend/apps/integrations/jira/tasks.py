import logging

from django.utils import timezone

from config.celery import app

logger = logging.getLogger(__name__)


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def poll_jira_updates(self, integration_id: int):
    """Periodischer Task: Neue Änderungen aus Jira abrufen."""
    from apps.integrations.models import IntegrationConfig
    from apps.notifications.services import NotificationService

    from .sync import JiraSyncService

    try:
        integration = IntegrationConfig.objects.get(id=integration_id)
    except IntegrationConfig.DoesNotExist:
        logger.error("Integration %s nicht gefunden", integration_id)
        return

    try:
        sync_service = JiraSyncService(integration)
        sync_log = sync_service.sync_inbound()

        integration.last_synced_at = timezone.now()
        integration.sync_status = IntegrationConfig.SyncStatus.IDLE
        integration.save(update_fields=["last_synced_at", "sync_status", "updated_at"])

        logger.info(
            "Jira-Sync abgeschlossen: %d erstellt, %d aktualisiert",
            sync_log.records_created,
            sync_log.records_updated,
        )
    except Exception as exc:
        integration.sync_status = IntegrationConfig.SyncStatus.ERROR
        integration.save(update_fields=["sync_status", "updated_at"])

        NotificationService.create_notification(
            user=integration.user,
            title="Jira-Sync fehlgeschlagen",
            message=str(exc),
            notification_type="sync_error",
            severity="warning",
        )
        raise self.retry(exc=exc)


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def sync_project_to_jira(self, integration_id: int, project_id: int):
    """Einzelnes Projekt nach Jira synchronisieren."""
    from apps.integrations.models import IntegrationConfig
    from apps.notifications.services import NotificationService

    from .sync import JiraSyncService

    try:
        integration = IntegrationConfig.objects.get(id=integration_id)
    except IntegrationConfig.DoesNotExist:
        logger.error("Integration %s nicht gefunden", integration_id)
        return

    try:
        sync_service = JiraSyncService(integration)
        sync_log = sync_service.sync_outbound()
        conflicts = sync_service.detect_conflicts()

        if conflicts:
            NotificationService.create_notification(
                user=integration.user,
                title="Sync-Konflikte erkannt",
                message=f"{len(conflicts)} Konflikte bei der Jira-Synchronisierung.",
                notification_type="sync_error",
                severity="warning",
            )

        logger.info(
            "Outbound Jira-Sync abgeschlossen: %d erstellt, %d aktualisiert, %d Konflikte",
            sync_log.records_created,
            sync_log.records_updated,
            len(conflicts),
        )
    except Exception as exc:
        integration.sync_status = IntegrationConfig.SyncStatus.ERROR
        integration.save(update_fields=["sync_status", "updated_at"])
        raise self.retry(exc=exc)


@app.task(bind=True)
def poll_all_jira_integrations(self):
    """Alle aktiven Jira-Integrationen synchronisieren."""
    from apps.integrations.models import IntegrationConfig

    integrations = IntegrationConfig.objects.filter(
        integration_type=IntegrationConfig.IntegrationType.JIRA,
        is_enabled=True,
    )
    for integration in integrations:
        poll_jira_updates.delay(integration.id)
