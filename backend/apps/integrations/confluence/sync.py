import logging

from django.utils import timezone

from apps.integrations.models import ConfluencePage, IntegrationConfig, SyncLog

from .client import ConfluenceClient

logger = logging.getLogger(__name__)


class ConfluenceSyncService:
    """Service für die Synchronisierung mit Confluence."""

    def __init__(self, integration: IntegrationConfig):
        self.integration = integration
        creds = integration.credentials
        self.client = ConfluenceClient(
            url=creds.get("url", ""),
            email=creds.get("email", ""),
            api_token=creds.get("api_token", ""),
        )

    def sync_pages(self, space_key: str) -> dict:
        """Seiten eines Space synchronisieren."""
        pages = self.client.get_pages(space_key)
        stats = {"created": 0, "updated": 0}

        for page_data in pages:
            page_id = str(page_data.get("id", ""))
            title = page_data.get("title", "")
            content = ""
            if page_data.get("body", {}).get("storage", {}).get("value"):
                content = page_data["body"]["storage"]["value"]

            last_update = page_data.get("version", {}).get("when", timezone.now().isoformat())

            page, created = ConfluencePage.objects.update_or_create(
                confluence_page_id=page_id,
                defaults={
                    "space_key": space_key,
                    "title": title,
                    "content_text": content,
                    "last_confluence_update": last_update,
                },
            )

            if created:
                stats["created"] += 1
            else:
                stats["updated"] += 1

        return stats

    def sync_inbound(self) -> SyncLog:
        """Eingehender Sync: Confluence -> lokal."""
        sync_log = SyncLog.objects.create(
            integration=self.integration,
            direction=SyncLog.Direction.INBOUND,
            status=SyncLog.Status.STARTED,
            started_at=timezone.now(),
        )

        total_created = 0
        total_updated = 0
        errors = []

        try:
            spaces = self.integration.settings.get("spaces", [])
            for space_key in spaces:
                try:
                    stats = self.sync_pages(space_key)
                    total_created += stats["created"]
                    total_updated += stats["updated"]
                except Exception as e:
                    errors.append(f"Fehler bei Space {space_key}: {str(e)}")

            sync_log.status = SyncLog.Status.COMPLETED
        except Exception as e:
            sync_log.status = SyncLog.Status.FAILED
            errors.append(str(e))

        sync_log.records_processed = total_created + total_updated
        sync_log.records_created = total_created
        sync_log.records_updated = total_updated
        sync_log.errors = errors
        sync_log.completed_at = timezone.now()
        sync_log.save()

        return sync_log
