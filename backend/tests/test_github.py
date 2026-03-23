from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.integrations.models import GitActivity, IntegrationConfig
from tests.factories import ProjectFactory


@pytest.mark.django_db
class TestGitActivityAPI:
    def test_list_empty(self, api_client, user):
        response = api_client.get("/api/v1/integrations/git-activities/")
        assert response.status_code == 200
        assert response.data["count"] == 0

    def test_list_activities(self, api_client, user, project):
        GitActivity.objects.create(
            project=project,
            event_type="commit",
            author="dev@example.com",
            title="feat: add login",
            external_id="abc123",
            event_date=timezone.now(),
        )
        GitActivity.objects.create(
            project=project,
            event_type="pr_opened",
            author="dev@example.com",
            title="PR: Login feature",
            external_id="pr-1",
            event_date=timezone.now(),
        )

        response = api_client.get("/api/v1/integrations/git-activities/")
        assert response.status_code == 200
        assert response.data["count"] == 2

    def test_filter_by_project(self, api_client, user, project):
        other_project = ProjectFactory(owner=user)
        GitActivity.objects.create(
            project=project,
            event_type="commit",
            author="dev@example.com",
            title="In my project",
            external_id="abc",
            event_date=timezone.now(),
        )
        GitActivity.objects.create(
            project=other_project,
            event_type="commit",
            author="dev@example.com",
            title="In other project",
            external_id="def",
            event_date=timezone.now(),
        )

        response = api_client.get(f"/api/v1/integrations/git-activities/?project={project.id}")
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["title"] == "In my project"

    def test_activities_ordered_by_date(self, api_client, user, project):
        now = timezone.now()
        GitActivity.objects.create(
            project=project,
            event_type="commit",
            author="dev",
            title="Older commit",
            external_id="old",
            event_date=now - timezone.timedelta(hours=2),
        )
        GitActivity.objects.create(
            project=project,
            event_type="commit",
            author="dev",
            title="Newer commit",
            external_id="new",
            event_date=now,
        )

        response = api_client.get("/api/v1/integrations/git-activities/")
        assert response.status_code == 200
        assert response.data["results"][0]["title"] == "Newer commit"


@pytest.mark.django_db
class TestGitHubClient:
    def test_github_client_init(self):
        from apps.integrations.git.client import GitHubClient

        client = GitHubClient(token="test-token")
        assert client.access_token == "test-token"
        assert "Bearer test-token" in client.client.headers["Authorization"]
        client.close()

    def test_github_client_context_manager(self):
        from apps.integrations.git.client import GitHubClient

        with GitHubClient(token="test") as client:
            assert client.access_token == "test"


@pytest.mark.django_db
class TestGitHubSyncDispatch:
    @patch("apps.integrations.git.tasks.poll_github_updates.delay")
    def test_sync_dispatches_github_task(self, mock_task, api_client, user):
        integration = IntegrationConfig.objects.create(
            user=user,
            integration_type="github",
            is_enabled=True,
            credentials={"token": "ghp_test"},
            sync_status=IntegrationConfig.SyncStatus.IDLE,
        )

        response = api_client.post(f"/api/v1/integrations/configs/{integration.id}/sync/")
        assert response.status_code == 202
        integration.refresh_from_db()
        assert integration.sync_status == "syncing"
        mock_task.assert_called_once_with(integration.id)
