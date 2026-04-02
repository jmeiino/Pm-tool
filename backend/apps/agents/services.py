"""Service fuer die Kommunikation mit Paperclip (neu) oder Agent-Agency (Legacy)."""

import logging

import httpx

from .models import AgentCompanyConfig, AgentTask

logger = logging.getLogger(__name__)

# ─── Priority-Mapping: PM-Tool (1-5) → Paperclip (low/medium/high/urgent) ────

PRIORITY_TO_PAPERCLIP = {
    1: "urgent",
    2: "high",
    3: "medium",
    4: "low",
    5: "low",
}

# ─── Task-Type → Paperclip Agent-ID Mapping ─────────────────────────────────

DEFAULT_AGENT_MAPPING = {
    "software": "94b76903-93a3-4dd1-aabf-9ca5ef4b281b",  # Coder
    "code": "94b76903-93a3-4dd1-aabf-9ca5ef4b281b",       # Coder
    "content": "310c6598-b798-4ef3-bdc2-67e0d275aa5b",     # Writer
    "research": "5f88d00d-c755-4341-ba98-06cb5ec657b9",    # Researcher
}

PAPERCLIP_ROLE_MAP = {
    "94b76903-93a3-4dd1-aabf-9ca5ef4b281b": "coder",
    "310c6598-b798-4ef3-bdc2-67e0d275aa5b": "writer",
    "5f88d00d-c755-4341-ba98-06cb5ec657b9": "researcher",
}


class AgentBridgeService:
    """HTTP-Client fuer Paperclip (Standard) oder Agent-Agency (Legacy).

    Wenn ``company.use_paperclip`` aktiviert ist, werden alle Aufrufe ueber
    die Paperclip-API geroutet.  Andernfalls wird die alte direkte
    Agent-Agency-API genutzt (Fallback/Legacy-Modus).
    """

    def __init__(self, company: AgentCompanyConfig):
        self.company = company
        self._use_paperclip = company.use_paperclip and bool(company.paperclip_company_id)

        if self._use_paperclip:
            self.client = httpx.Client(
                base_url=company.paperclip_base_url.rstrip("/"),
                headers={
                    "Authorization": f"Bearer {company.paperclip_api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        else:
            self.client = httpx.Client(
                base_url=company.base_url.rstrip("/"),
                headers={
                    "Authorization": f"Bearer {company.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )

    # ─── Haupt-Methoden ──────────────────────────────────────────────────

    def delegate_task(self, task: AgentTask, instructions: str = "") -> dict:
        """Aufgabe delegieren — ueber Paperclip oder direkt an Agent-Agency."""
        if self._use_paperclip:
            return self._paperclip_delegate(task, instructions)
        return self._legacy_delegate(task, instructions)

    def cancel_task(self, external_task_id: str) -> dict:
        """Aufgabe abbrechen."""
        if self._use_paperclip:
            return self._paperclip_cancel(external_task_id)
        return self._legacy_cancel(external_task_id)

    def send_reply(self, external_task_id: str, content: str, decision_option: str = "") -> dict:
        """User-Antwort an Agent senden."""
        if self._use_paperclip:
            return self._paperclip_reply(external_task_id, content, decision_option)
        return self._legacy_reply(external_task_id, content, decision_option)

    def get_company_status(self) -> dict:
        """Firmenstatus abrufen (Agent-Auslastung, aktive Tasks)."""
        if self._use_paperclip:
            return self._paperclip_company_status()
        return self._legacy_company_status()

    def sync_agent_profiles(self) -> list:
        """Agent-Profile synchronisieren und in DB speichern."""
        if self._use_paperclip:
            return self._paperclip_sync_profiles()
        return self._legacy_sync_profiles()

    # ─── Paperclip-Implementierungen ─────────────────────────────────────

    def _paperclip_delegate(self, task: AgentTask, instructions: str = "") -> dict:
        """Issue in Paperclip erstellen und optional Agent wecken."""
        company_id = self.company.paperclip_company_id
        agent_mapping = self.company.settings.get("agent_mapping", DEFAULT_AGENT_MAPPING)

        # Priority-Mapping
        paperclip_priority = PRIORITY_TO_PAPERCLIP.get(task.priority, "medium")

        # Agent-ID anhand des Task-Typs bestimmen
        agent_id = agent_mapping.get(task.task_type)

        # Beschreibung mit Kontext aufbauen
        description_parts = [task.issue.description or ""]
        if instructions:
            description_parts.append(f"\n\n---\n**Anweisungen:** {instructions}")

        # Callback-URL und PM-Tool-Kontext in die Beschreibung einbetten,
        # damit Agent-Agency diese Informationen aus dem Issue lesen kann
        callback_url = f"{self._pm_base_url()}/api/v1/agents/webhooks/event/"
        context_block = (
            f"\n\n---\n"
            f"<!-- pm-tool-context\n"
            f"external_id: {task.external_task_id}\n"
            f"project_key: {task.issue.project.key}\n"
            f"issue_key: {task.issue.key}\n"
            f"issue_type: {task.issue.issue_type}\n"
            f"callback_url: {callback_url}\n"
            f"-->"
        )
        description_parts.append(context_block)

        payload = {
            "title": task.issue.title,
            "description": "\n".join(description_parts),
            "status": "todo",
            "priority": paperclip_priority,
            "labels": ["ai-agent"],
        }

        if agent_id:
            payload["assigneeAgentId"] = agent_id

        try:
            response = self.client.post(
                f"/api/companies/{company_id}/issues",
                json=payload,
            )
            response.raise_for_status()
            issue_data = response.json()
            logger.info(
                "Paperclip-Issue erstellt: %s fuer Task %s",
                issue_data.get("id", "?"),
                task.external_task_id,
            )

            # Paperclip-Issue-ID im Task speichern fuer spaetere Referenz
            task.deliverables = task.deliverables or []
            task.deliverables.append({"paperclip_issue_id": issue_data.get("id")})
            task.save(update_fields=["deliverables", "updated_at"])

            # Agent wecken, falls zugewiesen
            wakeup_agent_id = agent_id or issue_data.get("assigneeAgentId")
            if wakeup_agent_id and issue_data.get("id"):
                self._paperclip_wakeup(wakeup_agent_id, issue_data["id"])

            return issue_data

        except httpx.HTTPError as e:
            logger.error("Fehler beim Erstellen des Paperclip-Issues: %s", e)
            raise

    def _paperclip_wakeup(self, agent_id: str, issue_id: str) -> dict | None:
        """Agent in Paperclip wecken."""
        try:
            response = self.client.post(
                f"/api/agents/{agent_id}/wakeup",
                json={
                    "reason": "issue_assigned",
                    "payload": {"issueId": issue_id},
                },
            )
            response.raise_for_status()
            logger.info("Paperclip-Agent %s geweckt fuer Issue %s", agent_id, issue_id)
            return response.json()
        except httpx.HTTPError as e:
            logger.warning("Agent-Wakeup fehlgeschlagen (nicht kritisch): %s", e)
            return None

    def _paperclip_cancel(self, external_task_id: str) -> dict:
        """Issue in Paperclip als cancelled kommentieren.

        Paperclip hat keinen dedizierten Cancel-Endpoint.  Wir senden
        einen Kommentar und versuchen den Status zu aendern.
        """
        issue_id = self._get_paperclip_issue_id(external_task_id)
        if not issue_id:
            logger.warning(
                "Keine Paperclip-Issue-ID fuer Task %s gefunden, "
                "lokaler Cancel ohne Paperclip-Benachrichtigung",
                external_task_id,
            )
            return {"status": "local_only"}

        try:
            response = self.client.post(
                f"/api/issues/{issue_id}/comments",
                json={"body": "[PM-Tool] Aufgabe wurde abgebrochen."},
            )
            response.raise_for_status()
            logger.info("Paperclip-Issue %s als abgebrochen kommentiert", issue_id)
            return response.json()
        except httpx.HTTPError as e:
            logger.error("Fehler beim Abbrechen in Paperclip: %s", e)
            raise

    def _paperclip_reply(
        self, external_task_id: str, content: str, decision_option: str = ""
    ) -> dict:
        """Kommentar auf Paperclip-Issue als Reply senden."""
        issue_id = self._get_paperclip_issue_id(external_task_id)
        if not issue_id:
            logger.warning(
                "Keine Paperclip-Issue-ID fuer Task %s — Reply nicht gesendet",
                external_task_id,
            )
            return {"status": "local_only"}

        body = content
        if decision_option:
            body = f"[Entscheidung: {decision_option}]\n\n{content}"

        try:
            response = self.client.post(
                f"/api/issues/{issue_id}/comments",
                json={"body": body},
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error("Fehler beim Senden des Paperclip-Kommentars: %s", e)
            raise

    def _paperclip_company_status(self) -> dict:
        """Agent-Liste und Status ueber Paperclip abrufen."""
        company_id = self.company.paperclip_company_id
        try:
            response = self.client.get(f"/api/companies/{company_id}/agents")
            response.raise_for_status()
            agents_data = response.json()
            # Paperclip gibt eine Liste von Agents zurueck
            agents = agents_data if isinstance(agents_data, list) else agents_data.get("agents", [])
            return {
                "agents": agents,
                "active_tasks": sum(1 for a in agents if a.get("status") == "working"),
            }
        except httpx.HTTPError as e:
            logger.error("Fehler beim Abrufen des Paperclip-Status: %s", e)
            return {"agents": [], "active_tasks": 0}

    def _paperclip_sync_profiles(self) -> list:
        """Agent-Profile aus Paperclip synchronisieren."""
        from .models import AgentProfile

        company_id = self.company.paperclip_company_id
        try:
            response = self.client.get(f"/api/companies/{company_id}/agents")
            response.raise_for_status()
            agents_data = response.json()
            agents_list = (
                agents_data if isinstance(agents_data, list) else agents_data.get("agents", [])
            )
        except httpx.HTTPError as e:
            logger.error("Fehler beim Laden der Agent-Profile aus Paperclip: %s", e)
            return []

        valid_roles = {c.value for c in AgentProfile.Role}
        synced = []
        for agent in agents_list:
            # Rolle anhand der Agent-ID oder des Paperclip-Feldes bestimmen
            agent_id = agent.get("id", "")
            role = PAPERCLIP_ROLE_MAP.get(agent_id, agent.get("role", "specialist"))
            if role not in valid_roles:
                role = "specialist"

            profile, _created = AgentProfile.objects.update_or_create(
                external_id=agent_id,
                defaults={
                    "company": self.company,
                    "name": agent.get("name", agent.get("displayName", "Unknown")),
                    "role": role,
                    "status": agent.get("status", "idle"),
                    "capabilities": agent.get("capabilities", []),
                },
            )
            synced.append(profile)
        return synced

    # ─── Paperclip-Hilfsmethoden ─────────────────────────────────────────

    def _get_paperclip_issue_id(self, external_task_id: str) -> str | None:
        """Paperclip-Issue-ID aus den Task-Deliverables lesen."""
        try:
            task = AgentTask.objects.get(external_task_id=external_task_id)
            for d in (task.deliverables or []):
                if isinstance(d, dict) and d.get("paperclip_issue_id"):
                    return d["paperclip_issue_id"]
        except AgentTask.DoesNotExist:
            pass
        return None

    # ─── Legacy-Implementierungen (Agent-Agency direkt) ──────────────────

    def _legacy_delegate(self, task: AgentTask, instructions: str = "") -> dict:
        """Aufgabe direkt an Agent-Agency senden (alter Pfad)."""
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
            logger.error("Fehler beim Delegieren der Aufgabe (Legacy): %s", e)
            raise

    def _legacy_cancel(self, external_task_id: str) -> dict:
        """Aufgabe in Agent-Agency abbrechen (alter Pfad)."""
        try:
            response = self.client.post(f"/api/v1/tasks/{external_task_id}/cancel/")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error("Fehler beim Abbrechen der Aufgabe (Legacy): %s", e)
            raise

    def _legacy_reply(
        self, external_task_id: str, content: str, decision_option: str = ""
    ) -> dict:
        """User-Antwort direkt an Agent-Agency senden (alter Pfad)."""
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
            logger.error("Fehler beim Senden der Antwort (Legacy): %s", e)
            raise

    def _legacy_company_status(self) -> dict:
        """Firmenstatus direkt von Agent-Agency abrufen (alter Pfad)."""
        try:
            response = self.client.get("/api/v1/status/")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error("Fehler beim Abrufen des Firmenstatus (Legacy): %s", e)
            return {"agents": [], "active_tasks": 0}

    def _legacy_sync_profiles(self) -> list:
        """Agent-Profile direkt von Agent-Agency laden (alter Pfad)."""
        from .models import AgentProfile

        try:
            response = self.client.get("/api/v1/agents/")
            response.raise_for_status()
            agents_data = response.json().get("agents", [])
        except httpx.HTTPError as e:
            logger.error("Fehler beim Laden der Agent-Profile (Legacy): %s", e)
            return []

        valid_roles = {c.value for c in AgentProfile.Role}
        synced = []
        for agent in agents_data:
            role = agent.get("role", "specialist")
            if role not in valid_roles:
                role = "specialist"
            profile, _created = AgentProfile.objects.update_or_create(
                external_id=agent["id"],
                defaults={
                    "company": self.company,
                    "name": agent.get("name", "Unknown"),
                    "role": role,
                    "status": agent.get("status", "idle"),
                    "capabilities": agent.get("capabilities", []),
                },
            )
            synced.append(profile)
        return synced

    # ─── Gemeinsame Hilfsmethoden ────────────────────────────────────────

    def _pm_base_url(self) -> str:
        """PM-Tool Base-URL aus Settings."""
        from django.conf import settings

        return getattr(settings, "PM_TOOL_BASE_URL", "http://localhost:4107")

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
