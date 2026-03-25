"""Tests für den Import-Wizard: GitHub-Mapper, Preview- und Confirm-Endpoints."""

from unittest.mock import MagicMock, patch

import pytest

from apps.integrations.git.mappers import (
    github_issue_to_local,
    github_labels_to_issue_type,
    github_labels_to_priority,
)
from apps.integrations.models import IntegrationConfig
from apps.projects.models import Issue, Project
from tests.factories import IntegrationConfigFactory, ProjectFactory


# ─── GitHub Mapper Tests ─────────────────────────────────────────────────────


@pytest.mark.django_db
class TestGitHubMappers:
    def test_github_labels_to_issue_type_bug(self):
        labels = [{"name": "bug"}]
        assert github_labels_to_issue_type(labels) == "bug"

    def test_github_labels_to_issue_type_enhancement(self):
        labels = [{"name": "enhancement"}]
        assert github_labels_to_issue_type(labels) == "story"

    def test_github_labels_to_issue_type_default(self):
        labels = [{"name": "documentation"}]
        assert github_labels_to_issue_type(labels) == "task"

    def test_github_labels_to_issue_type_empty(self):
        assert github_labels_to_issue_type([]) == "task"

    def test_github_labels_to_priority_high(self):
        labels = [{"name": "priority: high"}]
        assert github_labels_to_priority(labels) == "high"

    def test_github_labels_to_priority_default(self):
        labels = [{"name": "help wanted"}]
        assert github_labels_to_priority(labels) == "medium"

    def test_github_issue_to_local(self, user):
        project = ProjectFactory(owner=user)
        gh_issue = {
            "id": 99001,
            "number": 42,
            "title": "Fix login bug",
            "body": "The login page crashes on mobile.",
            "state": "open",
            "labels": [{"name": "bug"}, {"name": "priority: high"}],
        }

        result = github_issue_to_local(gh_issue, project, "user/repo")
        assert result["project"] == project
        assert result["title"] == "Fix login bug"
        assert result["description"] == "The login page crashes on mobile."
        assert result["issue_type"] == "bug"
        assert result["priority"] == "high"
        assert result["status"] == "to_do"
        assert result["github_issue_id"] == 99001
        assert result["github_issue_number"] == 42
        assert result["github_repo_full_name"] == "user/repo"

    def test_github_issue_to_local_closed(self, user):
        project = ProjectFactory(owner=user)
        gh_issue = {
            "id": 99002,
            "number": 43,
            "title": "Done task",
            "body": None,
            "state": "closed",
            "labels": [],
        }

        result = github_issue_to_local(gh_issue, project, "user/repo")
        assert result["status"] == "done"
        assert result["description"] == ""
        assert result["issue_type"] == "task"


# ─── Import Preview: No Integration ──────────────────────────────────────────


@pytest.mark.django_db
class TestImportPreviewNoIntegration:
    """Preview-Endpoints geben 404 zurück, wenn keine Integration konfiguriert ist."""

    def test_jira_preview_no_integration(self, api_client):
        response = api_client.get("/api/v1/integrations/import/jira/preview/")
        assert response.status_code == 404

    def test_github_preview_no_integration(self, api_client):
        response = api_client.get("/api/v1/integrations/import/github/preview/")
        assert response.status_code == 404

    def test_confluence_preview_no_integration(self, api_client):
        response = api_client.get("/api/v1/integrations/import/confluence/preview/")
        assert response.status_code == 404


# ─── Import Confirm: No Integration ──────────────────────────────────────────


@pytest.mark.django_db
class TestImportConfirmNoIntegration:
    """Confirm-Endpoints geben 404 zurück, wenn keine Integration konfiguriert ist."""

    def test_jira_confirm_no_integration(self, api_client):
        response = api_client.post(
            "/api/v1/integrations/import/jira/confirm/",
            {"projects": []},
            format="json",
        )
        assert response.status_code == 404

    def test_github_confirm_no_integration(self, api_client):
        response = api_client.post(
            "/api/v1/integrations/import/github/confirm/",
            {"repos": []},
            format="json",
        )
        assert response.status_code == 404

    def test_confluence_confirm_no_integration(self, api_client):
        response = api_client.post(
            "/api/v1/integrations/import/confluence/confirm/",
            {"pages": []},
            format="json",
        )
        assert response.status_code == 404


# ─── Jira Import Tests ───────────────────────────────────────────────────────


@pytest.mark.django_db
class TestJiraImport:
    @pytest.fixture
    def jira_integration(self, user):
        return IntegrationConfigFactory(
            user=user,
            integration_type="jira",
            is_enabled=True,
            credentials={
                "url": "https://test.atlassian.net",
                "email": "test@test.de",
                "api_token": "secret",
            },
        )

    @patch("apps.integrations.jira.client.JiraClient")
    def test_jira_preview_projects(self, MockJiraClient, api_client, jira_integration):
        """Preview ohne project_key liefert nur Projekte (Lazy Loading)."""
        mock_client = MagicMock()
        MockJiraClient.return_value = mock_client
        mock_client.get_projects.return_value = [
            {"id": "10001", "key": "PROJ", "name": "Test Project"},
        ]

        response = api_client.get("/api/v1/integrations/import/jira/preview/")
        assert response.status_code == 200
        data = response.data
        assert len(data["projects"]) == 1
        assert data["projects"][0]["key"] == "PROJ"
        assert data["projects"][0]["issues"] == []  # Issues noch nicht geladen

    @patch("apps.integrations.jira.client.JiraClient")
    def test_jira_preview_issues_lazy(self, MockJiraClient, api_client, jira_integration):
        """Preview mit project_key lädt Issues lazy nach."""
        mock_client = MagicMock()
        MockJiraClient.return_value = mock_client
        mock_client.get_issues.return_value = [
            {
                "id": "20001",
                "key": "PROJ-1",
                "fields": {
                    "summary": "Task eins",
                    "status": {"name": "To Do"},
                    "assignee": {"displayName": "Max Mustermann"},
                    "sprint": {"name": "Sprint 1"},
                    "issuetype": {"name": "Task"},
                    "priority": {"name": "High"},
                },
            },
        ]

        response = api_client.get("/api/v1/integrations/import/jira/preview/?project_key=PROJ")
        assert response.status_code == 200
        data = response.data
        assert len(data["projects"][0]["issues"]) == 1
        assert data["projects"][0]["issues"][0]["summary"] == "Task eins"
        assert "Max Mustermann" in data["available_assignees"]
        assert "To Do" in data["available_statuses"]
        assert "Sprint 1" in data["available_sprints"]

    def test_jira_confirm_creates_project(self, api_client, user, jira_integration):
        """Confirm erstellt Projekt ohne Issues (kein Client-Call nötig)."""
        response = api_client.post(
            "/api/v1/integrations/import/jira/confirm/",
            {
                "projects": [
                    {
                        "jira_project_id": "10001",
                        "jira_project_key": "PROJ",
                        "name": "Test Project",
                        "issue_ids": [],
                    }
                ]
            },
            format="json",
        )
        assert response.status_code == 201
        assert response.data["created"] == 1

        project = Project.objects.get(jira_project_id="10001")
        assert project.name == "Test Project"
        assert project.jira_project_key == "PROJ"
        assert project.source == "jira"
        assert project.owner == user

    @patch("apps.integrations.jira.mappers.jira_issue_to_local")
    @patch("apps.integrations.jira.client.JiraClient")
    def test_jira_confirm_with_issues(
        self, MockJiraClient, mock_mapper, api_client, user, jira_integration
    ):
        mock_client = MagicMock()
        MockJiraClient.return_value = mock_client
        mock_client.get_issues.return_value = [
            {"id": "20001", "key": "PROJ-1", "fields": {"summary": "Issue 1"}},
            {"id": "20002", "key": "PROJ-2", "fields": {"summary": "Issue 2"}},
        ]

        # Simuliere den Mapper
        def fake_mapper(jira_data, project):
            fields = jira_data.get("fields", {})
            return {
                "project": project,
                "title": fields.get("summary", ""),
                "description": "",
                "issue_type": "task",
                "status": "to_do",
                "priority": "medium",
                "story_points": None,
                "due_date": None,
                "jira_issue_id": jira_data["id"],
                "jira_issue_key": jira_data["key"],
                "jira_updated_at": None,
            }

        mock_mapper.side_effect = fake_mapper

        response = api_client.post(
            "/api/v1/integrations/import/jira/confirm/",
            {
                "projects": [
                    {
                        "jira_project_id": "10001",
                        "jira_project_key": "PROJ",
                        "name": "Test Project",
                        "issue_ids": ["20001"],  # Nur Issue 1 importieren
                    }
                ]
            },
            format="json",
        )
        assert response.status_code == 201
        # 1 Projekt + 1 Issue = 2 erstellt
        assert response.data["created"] == 2
        assert Issue.objects.filter(jira_issue_id="20001").exists()
        assert not Issue.objects.filter(jira_issue_id="20002").exists()


# ─── GitHub Import Tests ──────────────────────────────────────────────────────


@pytest.mark.django_db
class TestGitHubImport:
    @pytest.fixture
    def github_integration(self, user):
        return IntegrationConfigFactory(
            user=user,
            integration_type="github",
            is_enabled=True,
            credentials={"token": "ghp_testtoken"},
        )

    @patch("apps.integrations.git.client.GitHubClient")
    def test_github_preview(self, MockGitHubClient, api_client, github_integration):
        mock_client = MagicMock()
        MockGitHubClient.return_value = mock_client
        mock_client.get_authenticated_user.return_value = {"login": "testuser"}
        mock_client.get_repos.return_value = [
            {
                "full_name": "testuser/my-repo",
                "description": "My test repo",
                "language": "Python",
                "stargazers_count": 5,
                "open_issues_count": 2,
            },
        ]
        mock_client.get_issues.return_value = [
            {
                "id": 30001,
                "number": 1,
                "title": "Fix bug",
                "state": "open",
                "assignee": {"login": "testuser"},
                "user": {"login": "testuser"},
                "labels": [{"name": "bug"}],
            },
        ]

        response = api_client.get("/api/v1/integrations/import/github/preview/")
        assert response.status_code == 200
        data = response.data
        assert data["github_username"] == "testuser"
        assert len(data["repos"]) == 1
        assert data["repos"][0]["full_name"] == "testuser/my-repo"
        assert len(data["repos"][0]["issues"]) == 1

    @patch("apps.integrations.git.client.GitHubClient")
    def test_github_preview_mine_only(self, MockGitHubClient, api_client, github_integration):
        mock_client = MagicMock()
        MockGitHubClient.return_value = mock_client
        mock_client.get_authenticated_user.return_value = {"login": "testuser"}
        mock_client.get_repos.return_value = [
            {
                "full_name": "testuser/repo",
                "description": "",
                "language": "Python",
                "stargazers_count": 0,
                "open_issues_count": 2,
            },
        ]
        mock_client.get_issues.return_value = [
            {
                "id": 30001,
                "number": 1,
                "title": "My issue",
                "state": "open",
                "assignee": {"login": "testuser"},
                "user": {"login": "testuser"},
                "labels": [],
            },
            {
                "id": 30002,
                "number": 2,
                "title": "Other issue",
                "state": "open",
                "assignee": {"login": "otheruser"},
                "user": {"login": "otheruser"},
                "labels": [],
            },
        ]

        response = api_client.get(
            "/api/v1/integrations/import/github/preview/?mine_only=true"
        )
        assert response.status_code == 200
        # Nur Issue 1 sollte angezeigt werden (mine_only Filter)
        issues = response.data["repos"][0]["issues"]
        assert len(issues) == 1
        assert issues[0]["title"] == "My issue"

    @patch("apps.integrations.git.client.GitHubClient")
    def test_github_confirm_new_project(self, MockGitHubClient, api_client, user, github_integration):
        mock_client = MagicMock()
        MockGitHubClient.return_value = mock_client
        mock_client.get_issues.return_value = [
            {
                "id": 30001,
                "number": 1,
                "title": "Fix bug",
                "body": "Bug description",
                "state": "open",
                "labels": [{"name": "bug"}],
            },
        ]

        response = api_client.post(
            "/api/v1/integrations/import/github/confirm/",
            {
                "repos": [
                    {
                        "full_name": "testuser/my-repo",
                        "create_new_project": True,
                        "project_name": "My Repo",
                        "selected_issue_ids": [30001],
                    }
                ]
            },
            format="json",
        )
        assert response.status_code == 201
        assert response.data["created"] >= 2  # 1 Projekt + 1 Issue

        project = Project.objects.get(github_repo_full_name="testuser/my-repo")
        assert project.name == "My Repo"
        assert project.source == "github"
        assert project.owner == user

        issue = Issue.objects.get(github_issue_id=30001)
        assert issue.title == "Fix bug"
        assert issue.project == project

    @patch("apps.integrations.git.client.GitHubClient")
    def test_github_confirm_existing_project(
        self, MockGitHubClient, api_client, user, project, github_integration
    ):
        mock_client = MagicMock()
        MockGitHubClient.return_value = mock_client
        mock_client.get_issues.return_value = []

        response = api_client.post(
            "/api/v1/integrations/import/github/confirm/",
            {
                "repos": [
                    {
                        "full_name": "testuser/other-repo",
                        "create_new_project": False,
                        "target_project_id": project.id,
                        "selected_issue_ids": [],
                    }
                ]
            },
            format="json",
        )
        assert response.status_code == 201

        project.refresh_from_db()
        assert project.github_repo_full_name == "testuser/other-repo"

    @patch("apps.integrations.git.client.GitHubClient")
    def test_github_confirm_updates_integration_settings(
        self, MockGitHubClient, api_client, user, github_integration
    ):
        mock_client = MagicMock()
        MockGitHubClient.return_value = mock_client
        mock_client.get_issues.return_value = []

        api_client.post(
            "/api/v1/integrations/import/github/confirm/",
            {
                "repos": [
                    {
                        "full_name": "testuser/new-repo",
                        "create_new_project": True,
                        "project_name": "New Repo",
                        "selected_issue_ids": [],
                    }
                ]
            },
            format="json",
        )

        github_integration.refresh_from_db()
        repos = github_integration.settings.get("repos", [])
        assert len(repos) == 1
        assert repos[0]["owner"] == "testuser"
        assert repos[0]["repo"] == "new-repo"


# ─── Confluence Import Tests ─────────────────────────────────────────────────


@pytest.mark.django_db
class TestConfluenceImport:
    @pytest.fixture
    def confluence_integration(self, user):
        return IntegrationConfigFactory(
            user=user,
            integration_type="confluence",
            is_enabled=True,
            credentials={
                "url": "https://test.atlassian.net/wiki",
                "email": "test@test.de",
                "api_token": "secret",
            },
        )

    @patch("apps.integrations.confluence.client.ConfluenceClient")
    def test_confluence_preview_spaces(
        self, MockConfluenceClient, api_client, confluence_integration
    ):
        mock_client = MagicMock()
        MockConfluenceClient.return_value = mock_client
        mock_client.get_spaces.return_value = [
            {
                "key": "DEV",
                "name": "Development",
                "description": {"plain": {"value": "Dev space"}},
            },
            {
                "key": "HR",
                "name": "Human Resources",
                "description": {"plain": {"value": ""}},
            },
        ]

        response = api_client.get("/api/v1/integrations/import/confluence/preview/")
        assert response.status_code == 200
        data = response.data
        assert len(data["spaces"]) == 2
        assert data["spaces"][0]["key"] == "DEV"
        assert data["spaces"][0]["name"] == "Development"

    @patch("apps.integrations.confluence.client.ConfluenceClient")
    def test_confluence_preview_pages_by_space(
        self, MockConfluenceClient, api_client, confluence_integration
    ):
        mock_client = MagicMock()
        MockConfluenceClient.return_value = mock_client
        mock_client.get_pages.return_value = [
            {
                "id": "12345",
                "title": "Meeting Notes",
                "version": {
                    "by": {"displayName": "Test User", "email": "test@test.de"},
                    "when": "2024-01-15T10:00:00Z",
                },
                "history": {"createdBy": {"email": "test@test.de"}},
            },
        ]

        response = api_client.get(
            "/api/v1/integrations/import/confluence/preview/?space_key=DEV"
        )
        assert response.status_code == 200
        data = response.data
        assert len(data["pages"]) == 1
        assert data["pages"][0]["title"] == "Meeting Notes"
        assert data["pages"][0]["confluence_page_id"] == "12345"

    @patch("apps.integrations.confluence.client.ConfluenceClient")
    def test_confluence_preview_my_pages_only(
        self, MockConfluenceClient, api_client, confluence_integration
    ):
        mock_client = MagicMock()
        MockConfluenceClient.return_value = mock_client
        mock_client.get_pages.return_value = [
            {
                "id": "12345",
                "title": "My Page",
                "version": {
                    "by": {"displayName": "Test User", "email": "test@test.de"},
                    "when": "2024-01-15T10:00:00Z",
                },
                "history": {"createdBy": {"email": "test@test.de"}},
            },
            {
                "id": "12346",
                "title": "Other Page",
                "version": {
                    "by": {"displayName": "Other User", "email": "other@other.de"},
                    "when": "2024-01-15T10:00:00Z",
                },
                "history": {"createdBy": {"email": "other@other.de"}},
            },
        ]

        response = api_client.get(
            "/api/v1/integrations/import/confluence/preview/?space_key=DEV&my_pages_only=true"
        )
        assert response.status_code == 200
        # Nur die eigene Seite sollte angezeigt werden
        assert len(response.data["pages"]) == 1
        assert response.data["pages"][0]["title"] == "My Page"

    @patch("apps.integrations.confluence.client.ConfluenceClient")
    def test_confluence_confirm_creates_pages(
        self, MockConfluenceClient, api_client, user, confluence_integration
    ):
        mock_client = MagicMock()
        MockConfluenceClient.return_value = mock_client
        mock_client.get_page_content.return_value = {
            "plain_text": "Page content here",
            "version": {"when": "2024-01-15T10:00:00Z"},
        }

        response = api_client.post(
            "/api/v1/integrations/import/confluence/confirm/",
            {
                "pages": [
                    {
                        "confluence_page_id": "12345",
                        "space_key": "DEV",
                        "title": "Meeting Notes",
                        "analyze": False,
                    }
                ]
            },
            format="json",
        )
        assert response.status_code == 201
        assert response.data["created"] == 1

        from apps.integrations.models import ConfluencePage

        page = ConfluencePage.objects.get(confluence_page_id="12345")
        assert page.title == "Meeting Notes"
        assert page.space_key == "DEV"


# ─── GitHub Sync Issue Update Tests ───────────────────────────────────────────


@pytest.mark.django_db
class TestGitHubSyncIssues:
    """Tests für laufende GitHub Issue Synchronisation."""

    @patch("apps.integrations.git.sync.GitHubClient")
    def test_sync_issues_updates_existing(self, MockGitHubClient, user):
        """sync_issues aktualisiert nur bereits importierte Issues."""
        project = ProjectFactory(owner=user, github_repo_full_name="testuser/repo")
        # Erstelle ein bereits importiertes Issue
        Issue.objects.create(
            project=project,
            title="Old Title",
            key=f"{project.key}-1",
            github_issue_id=30001,
            github_issue_number=1,
            github_repo_full_name="testuser/repo",
            status="to_do",
        )

        mock_client = MagicMock()
        MockGitHubClient.return_value = mock_client
        mock_client.get_issues.return_value = [
            {
                "id": 30001,
                "number": 1,
                "title": "Updated Title",
                "body": "Updated body",
                "state": "closed",
                "labels": [{"name": "bug"}],
            },
            {
                "id": 30002,
                "number": 2,
                "title": "New Issue (should be ignored)",
                "body": "",
                "state": "open",
                "labels": [],
            },
        ]

        integration = IntegrationConfigFactory(
            user=user,
            integration_type="github",
            is_enabled=True,
            credentials={"token": "ghp_test"},
            settings={"repos": [{"owner": "testuser", "repo": "repo", "project_id": project.id}]},
        )

        from apps.integrations.git.sync import GitHubSyncService

        service = GitHubSyncService(integration)
        created, updated = service.sync_issues(project, "testuser", "repo")

        assert created == 0
        assert updated == 1

        issue = Issue.objects.get(github_issue_id=30001)
        assert issue.title == "Updated Title"
        assert issue.status == "done"

        # Issue 30002 sollte NICHT importiert worden sein
        assert not Issue.objects.filter(github_issue_id=30002).exists()

    @patch("apps.integrations.git.sync.GitHubClient")
    def test_sync_issues_skips_without_imported(self, MockGitHubClient, user):
        """sync_issues überspringt Projekte ohne importierte GitHub Issues."""
        project = ProjectFactory(owner=user)

        mock_client = MagicMock()
        MockGitHubClient.return_value = mock_client

        integration = IntegrationConfigFactory(
            user=user,
            integration_type="github",
            is_enabled=True,
            credentials={"token": "ghp_test"},
        )

        from apps.integrations.git.sync import GitHubSyncService

        service = GitHubSyncService(integration)
        created, updated = service.sync_issues(project, "testuser", "repo")

        assert created == 0
        assert updated == 0
        mock_client.get_issues.assert_not_called()


# ─── Model Tests ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestProjectModelGitHubFields:
    def test_project_source_default(self, user):
        project = ProjectFactory(owner=user)
        assert project.source == "manual"

    def test_project_github_fields(self, user):
        project = ProjectFactory(
            owner=user,
            source=Project.Source.GITHUB,
            github_repo_full_name="user/repo",
        )
        assert project.source == "github"
        assert project.github_repo_full_name == "user/repo"

    def test_issue_github_fields(self, user):
        project = ProjectFactory(owner=user)
        issue = Issue.objects.create(
            project=project,
            title="GitHub Issue",
            key=f"{project.key}-1",
            github_issue_id=12345,
            github_issue_number=42,
            github_repo_full_name="user/repo",
        )
        assert issue.github_issue_id == 12345
        assert issue.github_issue_number == 42
        assert issue.github_repo_full_name == "user/repo"
