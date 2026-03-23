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
        """Alle Projekte aus Jira abrufen mit Paginierung."""
        try:
            return self.jira.projects()
        except Exception:
            logger.exception("Fehler beim Abrufen der Jira-Projekte")
            raise

    def get_issues(self, project_key: str, updated_since: str | None = None) -> list[dict]:
        """Issues eines Projekts per JQL abrufen mit Paginierung."""
        jql = f"project = {project_key}"
        if updated_since:
            jql += f' AND updated >= "{updated_since}"'
        jql += " ORDER BY updated DESC"

        all_issues = []
        start_at = 0
        max_results = 100

        while True:
            try:
                result = self.jira.jql(jql, start=start_at, limit=max_results)
                issues = result.get("issues", [])
                all_issues.extend(issues)

                if len(issues) < max_results:
                    break
                start_at += max_results
            except Exception:
                logger.exception("Fehler beim Abrufen der Jira-Issues für %s", project_key)
                raise

        return all_issues

    def get_sprints(self, board_id: int) -> list[dict]:
        """Sprints eines Boards abrufen."""
        try:
            return self.jira.get_all_sprint(board_id)
        except Exception as e:
            if "does not support sprints" in str(e).lower():
                logger.info("Board %s unterstützt keine Sprints", board_id)
                return []
            logger.exception("Fehler beim Abrufen der Sprints für Board %s", board_id)
            raise

    def create_issue(self, project_key: str, fields: dict) -> dict:
        """Neues Issue in Jira erstellen."""
        fields["project"] = {"key": project_key}
        try:
            return self.jira.issue_create(fields=fields)
        except Exception:
            logger.exception("Fehler beim Erstellen eines Jira-Issues")
            raise

    def update_issue(self, issue_key: str, fields: dict) -> dict:
        """Bestehendes Issue in Jira aktualisieren."""
        try:
            return self.jira.issue_update(issue_key, fields=fields)
        except Exception:
            logger.exception("Fehler beim Aktualisieren von Jira-Issue %s", issue_key)
            raise

    def add_comment(self, issue_key: str, body: str) -> dict:
        """Kommentar zu einem Issue hinzufügen."""
        try:
            return self.jira.issue_add_comment(issue_key, body)
        except Exception:
            logger.exception("Fehler beim Hinzufügen eines Kommentars zu %s", issue_key)
            raise
