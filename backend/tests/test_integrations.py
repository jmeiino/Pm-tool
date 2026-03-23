import pytest

from apps.integrations.jira.mappers import (
    jira_issue_to_local,
    jira_priority_to_local,
    jira_status_to_local,
    local_issue_to_jira,
)
from tests.factories import IssueFactory, ProjectFactory


@pytest.mark.django_db
class TestJiraMappers:
    def test_jira_priority_to_local(self):
        assert jira_priority_to_local("Highest") == "highest"
        assert jira_priority_to_local("Medium") == "medium"
        assert jira_priority_to_local("Unknown") == "medium"
        assert jira_priority_to_local(None) == "medium"

    def test_jira_status_to_local(self):
        assert jira_status_to_local("To Do") == "to_do"
        assert jira_status_to_local("In Progress") == "in_progress"
        assert jira_status_to_local("Done") == "done"
        assert jira_status_to_local(None) == "to_do"

    def test_jira_issue_to_local(self, user):
        project = ProjectFactory(owner=user)
        jira_data = {
            "id": "12345",
            "key": "TEST-1",
            "fields": {
                "summary": "Test Issue",
                "description": "A test issue",
                "issuetype": {"name": "Task"},
                "status": {"name": "To Do"},
                "priority": {"name": "High"},
                "duedate": "2024-12-31",
                "updated": "2024-01-01T00:00:00.000+0000",
            },
        }

        result = jira_issue_to_local(jira_data, project)
        assert result["project"] == project
        assert result["title"] == "Test Issue"
        assert result["priority"] == "high"
        assert result["status"] == "to_do"
        assert result["jira_issue_id"] == "12345"
        assert result["jira_issue_key"] == "TEST-1"

    def test_local_issue_to_jira(self, user):
        project = ProjectFactory(owner=user)
        issue = IssueFactory(
            project=project,
            title="Local Issue",
            priority="high",
            issue_type="story",
        )

        result = local_issue_to_jira(issue)
        assert result["summary"] == "Local Issue"
        assert result["priority"]["name"] == "High"
        assert result["issuetype"]["name"] == "Story"


@pytest.mark.django_db
class TestIntegrationConfigAPI:
    def test_create_integration(self, api_client, user):
        response = api_client.post(
            "/api/v1/integrations/configs/",
            {
                "integration_type": "jira",
                "credentials": {"url": "https://test.atlassian.net", "email": "test@test.de", "api_token": "secret"},
                "is_enabled": True,
            },
            format="json",
        )
        assert response.status_code == 201
        assert response.data["integration_type"] == "jira"

    def test_list_integrations(self, api_client, user):
        response = api_client.get("/api/v1/integrations/configs/")
        assert response.status_code == 200

    def test_sync_disabled_integration(self, api_client, user):
        from apps.integrations.models import IntegrationConfig

        integration = IntegrationConfig.objects.create(
            user=user,
            integration_type="jira",
            is_enabled=False,
            credentials={},
        )
        response = api_client.post(f"/api/v1/integrations/configs/{integration.id}/sync/")
        assert response.status_code == 400

    def test_sync_already_syncing(self, api_client, user):
        from apps.integrations.models import IntegrationConfig

        integration = IntegrationConfig.objects.create(
            user=user,
            integration_type="jira",
            is_enabled=True,
            sync_status=IntegrationConfig.SyncStatus.SYNCING,
            credentials={},
        )
        response = api_client.post(f"/api/v1/integrations/configs/{integration.id}/sync/")
        assert response.status_code == 409


@pytest.mark.django_db
class TestNotificationAPI:
    def test_list_notifications(self, api_client, user):
        from apps.notifications.models import Notification

        Notification.objects.create(
            user=user,
            title="Test",
            message="Test notification",
            notification_type="general",
        )

        response = api_client.get("/api/v1/notifications/")
        assert response.status_code == 200
        assert response.data["count"] == 1

    def test_mark_notification_read(self, api_client, user):
        from apps.notifications.models import Notification

        notification = Notification.objects.create(
            user=user,
            title="Test",
            message="Test",
            notification_type="general",
            is_read=False,
        )

        response = api_client.post(f"/api/v1/notifications/{notification.id}/mark-read/")
        assert response.status_code == 200

        notification.refresh_from_db()
        assert notification.is_read is True

    def test_mark_all_read(self, api_client, user):
        from apps.notifications.models import Notification

        Notification.objects.create(user=user, title="T1", message="M1", notification_type="general")
        Notification.objects.create(user=user, title="T2", message="M2", notification_type="general")

        response = api_client.post("/api/v1/notifications/mark-all-read/")
        assert response.status_code == 200

        assert Notification.objects.filter(user=user, is_read=False).count() == 0
