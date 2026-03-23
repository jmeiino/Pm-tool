from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.integrations.models import CalendarEvent, IntegrationConfig


@pytest.mark.django_db
class TestGraphClient:
    @patch("apps.integrations.microsoft.graph_client.msal.ConfidentialClientApplication")
    def test_graph_client_set_token(self, mock_msal):
        from apps.integrations.microsoft.graph_client import GraphClient

        client = GraphClient(
            client_id="test-id",
            client_secret="test-secret",
            tenant_id="test-tenant",
            redirect_uri="http://localhost/callback",
        )
        client.set_token("test-access-token")
        assert client._access_token == "test-access-token"

    @patch("apps.integrations.microsoft.graph_client.msal.ConfidentialClientApplication")
    def test_graph_client_request_without_token(self, mock_msal):
        from apps.integrations.microsoft.graph_client import GraphClient

        client = GraphClient(
            client_id="test-id",
            client_secret="test-secret",
            tenant_id="test-tenant",
            redirect_uri="http://localhost/callback",
        )
        with pytest.raises(ValueError, match="Kein Access-Token"):
            client._request("GET", "/me")


@pytest.mark.django_db
class TestMicrosoftSyncService:
    @patch("apps.integrations.microsoft.graph_client.msal.ConfidentialClientApplication")
    @patch("apps.integrations.microsoft.graph_client.GraphClient.get_calendar_events")
    def test_sync_calendar_creates_events(self, mock_events, mock_msal, user):
        integration = IntegrationConfig.objects.create(
            user=user,
            integration_type="microsoft_calendar",
            is_enabled=True,
            credentials={"access_token": "test-token"},
        )

        mock_events.return_value = [
            {
                "id": "ms-event-1",
                "subject": "Team Meeting",
                "start": {"dateTime": "2025-01-15T10:00:00"},
                "end": {"dateTime": "2025-01-15T11:00:00"},
                "isAllDay": False,
                "location": {"displayName": "Raum 1"},
                "attendees": [
                    {"emailAddress": {"address": "alice@example.com"}},
                    {"emailAddress": {"address": "bob@example.com"}},
                ],
                "organizer": {"emailAddress": {"address": "boss@example.com"}},
                "importance": "normal",
            },
            {
                "id": "ms-event-2",
                "subject": "Standup",
                "start": {"dateTime": "2025-01-15T09:00:00"},
                "end": {"dateTime": "2025-01-15T09:15:00"},
                "isAllDay": False,
                "location": {"displayName": ""},
                "attendees": [],
                "organizer": {"emailAddress": {"address": "boss@example.com"}},
                "importance": "high",
            },
        ]

        from apps.integrations.microsoft.sync import MicrosoftSyncService

        service = MicrosoftSyncService(integration)
        stats = service.sync_calendar("2025-01-15T00:00:00Z", "2025-01-16T00:00:00Z")

        assert stats["created"] == 2
        assert stats["updated"] == 0
        assert CalendarEvent.objects.filter(user=user).count() == 2

        event = CalendarEvent.objects.get(external_id="ms-event-1")
        assert event.title == "Team Meeting"
        assert event.location == "Raum 1"
        assert len(event.attendees) == 2

    @patch("apps.integrations.microsoft.graph_client.msal.ConfidentialClientApplication")
    @patch("apps.integrations.microsoft.graph_client.GraphClient.get_calendar_events")
    def test_sync_calendar_updates_existing(self, mock_events, mock_msal, user):
        integration = IntegrationConfig.objects.create(
            user=user,
            integration_type="microsoft_calendar",
            is_enabled=True,
            credentials={"access_token": "test-token"},
        )

        CalendarEvent.objects.create(
            user=user,
            external_id="ms-event-1",
            title="Old Title",
            start_time=timezone.now(),
            end_time=timezone.now() + timezone.timedelta(hours=1),
        )

        mock_events.return_value = [
            {
                "id": "ms-event-1",
                "subject": "New Title",
                "start": {"dateTime": "2025-01-15T10:00:00"},
                "end": {"dateTime": "2025-01-15T11:00:00"},
                "isAllDay": False,
                "location": {"displayName": ""},
                "attendees": [],
                "organizer": {"emailAddress": {"address": ""}},
                "importance": "normal",
            },
        ]

        from apps.integrations.microsoft.sync import MicrosoftSyncService

        service = MicrosoftSyncService(integration)
        stats = service.sync_calendar("2025-01-15T00:00:00Z", "2025-01-16T00:00:00Z")

        assert stats["created"] == 0
        assert stats["updated"] == 1

        event = CalendarEvent.objects.get(external_id="ms-event-1")
        assert event.title == "New Title"

    @patch("apps.integrations.microsoft.graph_client.msal.ConfidentialClientApplication")
    @patch("apps.integrations.microsoft.graph_client.GraphClient.get_calendar_events")
    def test_sync_inbound_creates_sync_log(self, mock_events, mock_msal, user):
        integration = IntegrationConfig.objects.create(
            user=user,
            integration_type="microsoft_calendar",
            is_enabled=True,
            credentials={"access_token": "test-token"},
        )
        mock_events.return_value = []

        from apps.integrations.microsoft.sync import MicrosoftSyncService
        from apps.integrations.models import SyncLog

        service = MicrosoftSyncService(integration)
        sync_log = service.sync_inbound()

        assert sync_log.status == SyncLog.Status.COMPLETED
        assert sync_log.direction == SyncLog.Direction.INBOUND
        assert SyncLog.objects.filter(integration=integration).count() == 1
