import pytest

from tests.factories import CommentFactory, IssueFactory, ProjectFactory, SprintFactory


@pytest.mark.django_db
class TestProjectAPI:
    def test_create_project(self, api_client, user):
        response = api_client.post(
            "/api/v1/projects/",
            {
                "name": "Test Projekt",
                "key": "TST",
                "description": "Ein Testprojekt",
            },
        )
        assert response.status_code == 201
        assert response.data["name"] == "Test Projekt"
        assert response.data["key"] == "TST"

    def test_list_projects(self, api_client, project):
        response = api_client.get("/api/v1/projects/")
        assert response.status_code == 200
        assert response.data["count"] >= 1
        assert any(p["id"] == project.id for p in response.data["results"])

    def test_project_detail(self, api_client, project):
        response = api_client.get(f"/api/v1/projects/{project.id}/")
        assert response.status_code == 200
        assert response.data["name"] == project.name

    def test_project_stats(self, api_client, project):
        IssueFactory(project=project, status="to_do")
        IssueFactory(project=project, status="done")
        IssueFactory(project=project, status="in_progress")

        response = api_client.get(f"/api/v1/projects/{project.id}/stats/")
        assert response.status_code == 200
        assert response.data["total"] == 3
        assert response.data["by_status"]["to_do"] == 1
        assert response.data["by_status"]["done"] == 1

    def test_project_stats_with_sprint(self, api_client, project):
        sprint = SprintFactory(project=project, status="active")
        IssueFactory(project=project, sprint=sprint, status="done")
        IssueFactory(project=project, sprint=sprint, status="to_do")

        response = api_client.get(f"/api/v1/projects/{project.id}/stats/")
        assert response.status_code == 200
        assert "sprint_info" in response.data
        assert response.data["sprint_info"]["total_issues"] == 2
        assert response.data["sprint_info"]["done_issues"] == 1

    def test_filter_projects_by_status(self, api_client, user):
        ProjectFactory(owner=user, status="active")
        ProjectFactory(owner=user, status="paused")

        response = api_client.get("/api/v1/projects/?status=active")
        assert response.status_code == 200
        for p in response.data["results"]:
            assert p["status"] == "active"


@pytest.mark.django_db
class TestIssueAPI:
    def test_create_issue_auto_key(self, api_client, project):
        response = api_client.post(
            "/api/v1/issues/",
            {
                "project": project.id,
                "title": "Test Issue",
                "issue_type": "task",
                "priority": "medium",
            },
        )
        assert response.status_code == 201
        assert response.data["key"].startswith(project.key)

    def test_create_multiple_issues_sequential_keys(self, api_client, project):
        r1 = api_client.post(
            "/api/v1/issues/",
            {
                "project": project.id,
                "title": "Issue 1",
            },
        )
        r2 = api_client.post(
            "/api/v1/issues/",
            {
                "project": project.id,
                "title": "Issue 2",
            },
        )
        assert r1.status_code == 201
        assert r2.status_code == 201
        # Keys should be different
        assert r1.data["key"] != r2.data["key"]

    def test_list_issues(self, api_client, project):
        IssueFactory(project=project)
        IssueFactory(project=project)

        response = api_client.get(f"/api/v1/issues/?project={project.id}")
        assert response.status_code == 200
        assert response.data["count"] == 2

    def test_issue_detail(self, api_client, project):
        issue = IssueFactory(project=project)

        response = api_client.get(f"/api/v1/issues/{issue.id}/")
        assert response.status_code == 200
        assert response.data["title"] == issue.title
        assert "comments" in response.data
        assert "subtasks" in response.data

    def test_filter_issues_by_status(self, api_client, project):
        IssueFactory(project=project, status="to_do")
        IssueFactory(project=project, status="done")

        response = api_client.get(f"/api/v1/issues/?status=to_do&project={project.id}")
        assert response.status_code == 200
        for issue in response.data["results"]:
            assert issue["status"] == "to_do"

    def test_issue_transition(self, api_client, project):
        issue = IssueFactory(project=project, status="to_do")

        response = api_client.post(
            f"/api/v1/issues/{issue.id}/transition/",
            {"status": "in_progress"},
        )
        assert response.status_code == 200
        assert response.data["status"] == "in_progress"

    def test_issue_transition_missing_status(self, api_client, project):
        issue = IssueFactory(project=project)

        response = api_client.post(f"/api/v1/issues/{issue.id}/transition/", {})
        assert response.status_code == 400


@pytest.mark.django_db
class TestCommentAPI:
    def test_create_comment(self, api_client, project, user):
        issue = IssueFactory(project=project)

        response = api_client.post(
            f"/api/v1/issues/{issue.id}/comments/",
            {"body": "Test Kommentar"},
        )
        assert response.status_code == 201
        assert response.data["body"] == "Test Kommentar"
        assert response.data["author"] == user.id

    def test_list_comments(self, api_client, project, user):
        issue = IssueFactory(project=project)
        CommentFactory(issue=issue, author=user)
        CommentFactory(issue=issue, author=user)

        response = api_client.get(f"/api/v1/issues/{issue.id}/comments/")
        assert response.status_code == 200
        assert response.data["count"] == 2


@pytest.mark.django_db
class TestLabelAPI:
    def test_create_label(self, api_client):
        response = api_client.post(
            "/api/v1/labels/",
            {
                "name": "Feature",
                "color": "#22C55E",
            },
        )
        assert response.status_code == 201
        assert response.data["name"] == "Feature"
