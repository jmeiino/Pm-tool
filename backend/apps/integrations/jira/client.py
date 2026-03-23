import logging

from atlassian import Jira

logger = logging.getLogger(__name__)


class JiraClient:
    """Client für die Kommunikation mit der Jira REST API."""

    def __init__(self, url: str, email: str, api_token: str):
        self.url = url
        self.email = email
        self.jira = Jira(
            url=url,
            username=email,
            password=api_token,
            cloud=True,
        )

    def get_projects(self) -> list[dict]:
        """Alle Projekte aus Jira abrufen."""
        # TODO: Paginierung implementieren
        # TODO: Fehlerbehandlung und Retry-Logik ergänzen
        return self.jira.projects()

    def get_issues(self, project_key: str) -> list[dict]:
        """Issues eines Projekts per JQL abrufen."""
        # TODO: Paginierung für große Projekte implementieren
        # TODO: Felder konfigurierbar machen
        jql = f"project = {project_key} ORDER BY updated DESC"
        return self.jira.jql(jql).get("issues", [])

    def get_sprints(self, board_id: int) -> list[dict]:
        """Sprints eines Boards abrufen."""
        # TODO: Agile-API-Endpunkt verwenden
        # TODO: Paginierung implementieren
        return self.jira.get_all_sprint(board_id)

    def create_issue(self, data: dict) -> dict:
        """Neues Issue in Jira erstellen."""
        # TODO: Feld-Mapping von internem Format zu Jira-Format
        # TODO: Validierung der Pflichtfelder
        return self.jira.issue_create(fields=data)

    def update_issue(self, issue_key: str, data: dict) -> dict:
        """Bestehendes Issue in Jira aktualisieren."""
        # TODO: Feld-Mapping implementieren
        # TODO: Konflikterkennung (optimistic locking)
        return self.jira.issue_update(issue_key, fields=data)

    def add_comment(self, issue_key: str, body: str) -> dict:
        """Kommentar zu einem Issue hinzufügen."""
        # TODO: Rich-Text / ADF-Format unterstützen
        return self.jira.issue_add_comment(issue_key, body)
