import logging

from django.utils import timezone

from config.celery import app

logger = logging.getLogger(__name__)


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def poll_confluence_updates(self, integration_id: int):
    """Periodischer Task: Neue Änderungen aus Confluence abrufen."""
    from apps.integrations.models import IntegrationConfig
    from apps.notifications.services import NotificationService

    from .sync import ConfluenceSyncService

    try:
        integration = IntegrationConfig.objects.get(id=integration_id)
    except IntegrationConfig.DoesNotExist:
        logger.error("Integration %s nicht gefunden", integration_id)
        return

    try:
        sync_service = ConfluenceSyncService(integration)
        sync_service.sync_inbound()

        integration.last_synced_at = timezone.now()
        integration.sync_status = IntegrationConfig.SyncStatus.IDLE
        integration.save(update_fields=["last_synced_at", "sync_status", "updated_at"])
    except Exception as exc:
        integration.sync_status = IntegrationConfig.SyncStatus.ERROR
        integration.save(update_fields=["sync_status", "updated_at"])

        NotificationService.create_notification(
            user=integration.user,
            title="Confluence-Sync fehlgeschlagen",
            message=str(exc),
            notification_type="sync_error",
            severity="warning",
        )
        raise self.retry(exc=exc)


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def analyze_confluence_page_task(self, page_id: int):
    """KI-Analyse einer Confluence-Seite."""
    from apps.ai.services import AIService
    from apps.integrations.models import ConfluencePage

    try:
        page = ConfluencePage.objects.get(id=page_id)
    except ConfluencePage.DoesNotExist:
        logger.error("Confluence-Seite %s nicht gefunden", page_id)
        return

    try:
        service = AIService()
        result = service.analyze_confluence_page(page.content_text)

        page.ai_summary = result.get("summary", "")
        page.ai_action_items = result.get("action_items", [])
        page.ai_decisions = result.get("decisions", [])
        page.ai_risks = result.get("risks", [])
        page.ai_processed_at = timezone.now()
        page.save()

        logger.info("Confluence-Seite %s analysiert", page.title)
    except Exception as exc:
        logger.exception("KI-Analyse fehlgeschlagen für Seite %s", page_id)
        raise self.retry(exc=exc)
