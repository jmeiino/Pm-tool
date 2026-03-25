"""Service für die Kommunikation mit dem Agent-Microservice."""

import logging

import httpx

from .models import AgentCompanyConfig, AgentTask

logger = logging.getLogger(__name__)


class AgentBridgeService:
    """HTTP-Client für den Agent-Service."""

    def __init__(self, company: AgentCompanyConfig):
        self.company = company
        self.client = httpx.Client(
            base_url=company.base_url.rstrip("/"),
            headers={
                "Authorization": f"Bearer {company.api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    def delegate_task(self, task: AgentTask, instructions: str = "") -> dict:
        """Aufgabe an die agentische Firma senden."""
        payload = {
            "external_id": task.external_task_id,
            "title": task.issue.title,
            "description": task.issue.description or "",
            "priority": task.priority,
            "type": task.task_type or "general",
            "context": {
                "project_key": task.issue.project.key,
                "issue_key": task.issue.key,
                "issue_type": task.issue.issue_type,
                "instructions": instructions,
            },
            "callback_url": f"{self._pm_base_url()}/api/v1/agents/webhooks/event/",
        }

        try:
            response = self.client.post("/api/v1/tasks/", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error("Fehler beim Delegieren der Aufgabe: %s", e)
            raise

    def cancel_task(self, external_task_id: str) -> dict:
        """Aufgabe im Agent-Service abbrechen."""
        try:
            response = self.client.post(f"/api/v1/tasks/{external_task_id}/cancel/")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error("Fehler beim Abbrechen der Aufgabe: %s", e)
            raise

    def send_reply(self, external_task_id: str, content: str, decision_option: str = "") -> dict:
        """User-Antwort an Agent senden."""
        payload = {"content": content}
        if decision_option:
            payload["decision_option"] = decision_option

        try:
            response = self.client.post(
                f"/api/v1/tasks/{external_task_id}/reply/",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error("Fehler beim Senden der Antwort: %s", e)
            raise

    def get_company_status(self) -> dict:
        """Firmenstatus abrufen (Agent-Auslastung, aktive Tasks)."""
        try:
            response = self.client.get("/api/v1/status/")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error("Fehler beim Abrufen des Firmenstatus: %s", e)
            return {"agents": [], "active_tasks": 0}

    def sync_agent_profiles(self) -> list[dict]:
        """Agent-Profile vom Service synchronisieren."""
        try:
            response = self.client.get("/api/v1/agents/")
            response.raise_for_status()
            return response.json().get("agents", [])
        except httpx.HTTPError as e:
            logger.error("Fehler beim Laden der Agent-Profile: %s", e)
            return []

    def _pm_base_url(self) -> str:
        """PM-Tool Base-URL aus Settings."""
        from django.conf import settings

        return getattr(settings, "PM_TOOL_BASE_URL", "http://localhost:8000")

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
