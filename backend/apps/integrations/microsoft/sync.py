import logging

from django.conf import settings
from django.utils import timezone
from dateutil import parser as dateparser

from apps.integrations.models import CalendarEvent, IntegrationConfig, SyncLog

from .graph_client import GraphClient

logger = logging.getLogger(__name__)


class MicrosoftSyncService:
    """Service für die Synchronisierung mit Microsoft 365."""

    def __init__(self, integration: IntegrationConfig):
        self.integration = integration
        creds = integration.credentials
        self.client = GraphClient(
            client_id=settings.MS_CLIENT_ID,
            client_secret=settings.MS_CLIENT_SECRET,
            tenant_id=settings.MS_TENANT_ID,
            redirect_uri=settings.MS_REDIRECT_URI,
        )
        self.client.set_token(creds.get("access_token", ""))

    def sync_calendar(self, start_date: str, end_date: str) -> dict:
        """Kalender-Termine synchronisieren."""
        events = self.client.get_calendar_events(start_date, end_date)
        stats = {"created": 0, "updated": 0}

        for event_data in events:
            external_id = event_data.get("id", "")
            if not external_id:
                continue

            start = event_data.get("start", {})
            end = event_data.get("end", {})
            is_all_day = event_data.get("isAllDay", False)

            start_time = dateparser.isoparse(
                start.get("dateTime", "") + "Z" if not start.get("dateTime", "").endswith("Z") else start.get("dateTime", "")
            ) if start.get("dateTime") else timezone.now()

            end_time = dateparser.isoparse(
                end.get("dateTime", "") + "Z" if not end.get("dateTime", "").endswith("Z") else end.get("dateTime", "")
            ) if end.get("dateTime") else start_time

            attendees = [
                a.get("emailAddress", {}).get("address", "")
                for a in event_data.get("attendees", [])
            ]

            _, created = CalendarEvent.objects.update_or_create(
                user=self.integration.user,
                external_id=external_id,
                defaults={
                    "title": event_data.get("subject", ""),
                    "start_time": start_time,
                    "end_time": end_time,
                    "is_all_day": is_all_day,
                    "location": event_data.get("location", {}).get("displayName", ""),
                    "attendees": attendees,
                    "metadata": {
                        "organizer": event_data.get("organizer", {}).get("emailAddress", {}).get("address", ""),
                        "importance": event_data.get("importance", ""),
                    },
                },
            )

            if created:
                stats["created"] += 1
            else:
                stats["updated"] += 1

        return stats

    def sync_inbound(self) -> SyncLog:
        """Eingehender Sync: Microsoft -> lokal."""
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
            # Sync next 30 days of calendar
            now = timezone.now()
            start = now.isoformat()
            end = (now + timezone.timedelta(days=30)).isoformat()

            stats = self.sync_calendar(start, end)
            total_created += stats["created"]
            total_updated += stats["updated"]

            sync_log.status = SyncLog.Status.COMPLETED
        except Exception as e:
            sync_log.status = SyncLog.Status.FAILED
            errors.append(str(e))
            logger.exception("Microsoft-Sync fehlgeschlagen")

        sync_log.records_processed = total_created + total_updated
        sync_log.records_created = total_created
        sync_log.records_updated = total_updated
        sync_log.errors = errors
        sync_log.completed_at = timezone.now()
        sync_log.save()

        return sync_log
