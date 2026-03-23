import pytest
from django.utils import timezone

from apps.integrations.models import CalendarEvent, IntegrationConfig
from tests.factories import UserFactory


@pytest.mark.django_db
class TestCalendarEventAPI:
    def test_list_empty(self, api_client, user):
        response = api_client.get("/api/v1/integrations/calendar-events/")
        assert response.status_code == 200
        assert response.data["count"] == 0

    def test_list_returns_own_events(self, api_client, user):
        now = timezone.now()
        CalendarEvent.objects.create(
            user=user,
            external_id="evt-1",
            title="Standup",
            start_time=now,
            end_time=now + timezone.timedelta(minutes=30),
        )
        # Another user's event should not appear
        other = UserFactory()
        CalendarEvent.objects.create(
            user=other,
            external_id="evt-2",
            title="Other Meeting",
            start_time=now,
            end_time=now + timezone.timedelta(minutes=60),
        )

        response = api_client.get("/api/v1/integrations/calendar-events/")
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["title"] == "Standup"

    def test_filter_by_date_range(self, api_client, user):
        now = timezone.now()
        CalendarEvent.objects.create(
            user=user,
            external_id="evt-past",
            title="Past Event",
            start_time=now - timezone.timedelta(days=10),
            end_time=now - timezone.timedelta(days=10, hours=-1),
        )
        CalendarEvent.objects.create(
            user=user,
            external_id="evt-future",
            title="Future Event",
            start_time=now + timezone.timedelta(days=1),
            end_time=now + timezone.timedelta(days=1, hours=1),
        )

        start = now.isoformat()
        end = (now + timezone.timedelta(days=7)).isoformat()
        response = api_client.get(
            f"/api/v1/integrations/calendar-events/?start={start}&end={end}"
        )
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["title"] == "Future Event"


@pytest.mark.django_db
class TestMicrosoftSyncDispatch:
    def test_sync_dispatches_microsoft_task(self, api_client, user):
        integration = IntegrationConfig.objects.create(
            user=user,
            integration_type="microsoft_calendar",
            is_enabled=True,
            credentials={"access_token": "test"},
            sync_status=IntegrationConfig.SyncStatus.IDLE,
        )
        with pytest.raises(Exception):
            # Task will fail because no real MS credentials, but the dispatch path is exercised
            pass

        response = api_client.post(
            f"/api/v1/integrations/configs/{integration.id}/sync/"
        )
        assert response.status_code == 202
        integration.refresh_from_db()
        assert integration.sync_status == "syncing"
