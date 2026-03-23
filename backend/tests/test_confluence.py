from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.integrations.models import ConfluencePage


@pytest.fixture
def confluence_page():
    return ConfluencePage.objects.create(
        confluence_page_id="12345",
        space_key="DEV",
        title="Architektur-Entscheidung",
        content_text="Wir verwenden Django + Next.js.",
        last_confluence_update=timezone.now(),
    )


@pytest.mark.django_db
class TestConfluencePageAPI:
    def test_list_pages(self, api_client, user, confluence_page):
        response = api_client.get("/api/v1/integrations/confluence-pages/")
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["title"] == "Architektur-Entscheidung"

    def test_retrieve_page(self, api_client, user, confluence_page):
        response = api_client.get(f"/api/v1/integrations/confluence-pages/{confluence_page.id}/")
        assert response.status_code == 200
        assert response.data["space_key"] == "DEV"

    def test_filter_by_space(self, api_client, user, confluence_page):
        ConfluencePage.objects.create(
            confluence_page_id="99999",
            space_key="TEAM",
            title="Team-Seite",
            content_text="Team-Inhalt",
            last_confluence_update=timezone.now(),
        )
        response = api_client.get("/api/v1/integrations/confluence-pages/?space_key=DEV")
        assert response.status_code == 200
        assert response.data["count"] == 1

    def test_search_pages(self, api_client, user, confluence_page):
        response = api_client.get("/api/v1/integrations/confluence-pages/?search=Architektur")
        assert response.status_code == 200
        assert response.data["count"] == 1

    @patch("apps.integrations.confluence.tasks.analyze_confluence_page_task.delay")
    def test_analyze_page(self, mock_task, api_client, user, confluence_page):
        response = api_client.post(f"/api/v1/integrations/confluence-pages/{confluence_page.id}/analyze/")
        assert response.status_code == 202
        assert "page_id" in response.data
        mock_task.assert_called_once_with(confluence_page.id)

    def test_create_todos_without_analysis(self, api_client, user, confluence_page):
        response = api_client.post(f"/api/v1/integrations/confluence-pages/{confluence_page.id}/create-todos/")
        assert response.status_code == 400

    def test_create_todos_with_action_items(self, api_client, user, confluence_page):
        confluence_page.ai_action_items = [
            "Frontend implementieren",
            "API testen",
        ]
        confluence_page.save()

        response = api_client.post(f"/api/v1/integrations/confluence-pages/{confluence_page.id}/create-todos/")
        assert response.status_code == 201
        assert response.data["count"] == 2

        from apps.todos.models import PersonalTodo

        todos = PersonalTodo.objects.filter(user=user)
        assert todos.count() == 2
        assert todos.filter(title="Frontend implementieren").exists()


@pytest.mark.django_db
class TestConfluenceClientHelpers:
    def test_html_to_text(self):
        from apps.integrations.confluence.client import ConfluenceClient

        html = "<p>Hallo <b>Welt</b></p><br/><p>Test</p>"
        result = ConfluenceClient._html_to_text(html)
        assert "Hallo Welt" in result
        assert "Test" in result
        assert "<" not in result
