# Agent-Agency — Paperclip-Integration

## Übersicht

Agent-Agency wird als **HTTP-Adapter-Agent** bei Paperclip registriert. Paperclip sendet periodische Heartbeats an Agent-Agency, sobald eine Aufgabe zugewiesen wurde. Agent-Agency empfängt den Heartbeat, holt sich die Issue-Details über die Paperclip-API, führt die Aufgabe über die bestehende Workflow-Engine aus und meldet das Ergebnis zurück.

**Kommunikationsfluss:**

```
Paperclip Board                       Agent-Agency
     |                                      |
     |  POST /api/v1/heartbeat/             |
     |  { runId, agentId, context }  -----> |
     |                                      |  GET  /api/agents/me
     |                                      |  GET  /api/issues/{taskId}
     |                                      |  POST /api/issues/{taskId}/checkout
     |                                      |
     |                                      |  [Interne Verarbeitung]
     |                                      |  classify -> execute -> QA -> deliver
     |                                      |
     |                                      |  PATCH /api/issues/{taskId}
     |  <-- 200 OK mit Ergebnis ----------- |
     |                                      |
```

---

## 1. Konfiguration erweitern

### 1.1 Neue Settings in `app/config.py`

Folgende Felder werden der bestehenden `Settings`-Klasse hinzugefügt:

```python
# app/config.py — Ergänzungen am Ende der Settings-Klasse

class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    # ... bestehende Felder ...

    # === Paperclip-Integration ===
    paperclip_enabled: bool = False
    paperclip_api_url: str = ""          # z.B. "http://paperclip:3100"
    paperclip_api_key: str = ""          # Bearer-Token für Paperclip-API
    paperclip_agent_id: str = ""         # Agent-ID in Paperclip
    paperclip_timeout_seconds: int = 300 # Maximale Ausführungszeit pro Heartbeat
```

### 1.2 Umgebungsvariablen (`.env`)

```env
# Paperclip-Integration
PAPERCLIP_ENABLED=true
PAPERCLIP_API_URL=http://paperclip:3100
PAPERCLIP_API_KEY=pk_live_xxxxxxxxxxxxxxxxxxxx
PAPERCLIP_AGENT_ID=agent_01HXXXXXXXXXXXXXXX
PAPERCLIP_TIMEOUT_SECONDS=300
```

---

## 2. Neuer Endpoint: `POST /api/v1/heartbeat/`

### 2.1 Request-Format von Paperclip

Paperclip sendet bei jedem Heartbeat folgenden JSON-Body:

```json
{
  "runId": "run_01HXXXXXXXXX",
  "agentId": "agent_01HXXXXXXXXX",
  "companyId": "company_01HXXXXXXXXX",
  "context": {
    "taskId": "issue-uuid-hier",
    "wakeReason": "assignment",
    "commentId": null
  }
}
```

| Feld                   | Beschreibung                                                  |
| ---------------------- | ------------------------------------------------------------- |
| `runId`                | Eindeutige ID dieses Heartbeat-Durchlaufs                     |
| `agentId`              | Paperclip-Agent-ID (muss mit `PAPERCLIP_AGENT_ID` stimmen)    |
| `companyId`            | Unternehmen in Paperclip                                      |
| `context.taskId`       | Issue-UUID die bearbeitet werden soll                          |
| `context.wakeReason`   | Grund: `assignment`, `schedule` oder `mention`                 |
| `context.commentId`    | Optional: Kommentar-ID bei `mention`-Trigger                   |

### 2.2 Response-Format

```json
{
  "status": "completed",
  "runId": "run_01HXXXXXXXXX",
  "taskId": "issue-uuid-hier",
  "internalTaskId": "uuid-der-internen-aufgabe",
  "summary": "Zusammenfassung des Ergebnisses",
  "executionTimeMs": 12345
}
```

---

## 3. Pydantic-Schemas

### 3.1 Ergänzungen in `app/api/schemas.py`

```python
# app/api/schemas.py — Paperclip-Schemas am Ende der Datei

# === Paperclip Heartbeat ===


class PaperclipHeartbeatContext(BaseModel):
    """Kontext eines Paperclip-Heartbeats."""
    taskId: str = Field(..., description="Issue-UUID in Paperclip")
    wakeReason: str = Field(
        ...,
        description="Grund des Heartbeats: assignment, schedule, mention",
    )
    commentId: str | None = Field(
        None,
        description="Kommentar-ID bei mention-Trigger",
    )


class PaperclipHeartbeatRequest(BaseModel):
    """Eingehender Heartbeat von Paperclip."""
    runId: str = Field(..., description="Eindeutige Run-ID dieses Heartbeats")
    agentId: str = Field(..., description="Paperclip-Agent-ID")
    companyId: str = Field(..., description="Paperclip-Unternehmens-ID")
    context: PaperclipHeartbeatContext


class PaperclipHeartbeatResponse(BaseModel):
    """Antwort auf einen Paperclip-Heartbeat."""
    status: str = Field(..., description="completed | failed | accepted")
    runId: str
    taskId: str
    internalTaskId: str | None = None
    summary: str = ""
    error: str | None = None
    executionTimeMs: int = 0
```

---

## 4. Paperclip-API-Client

### 4.1 Neue Datei: `app/integrations/paperclip_client.py`

Dieser Client kapselt alle Aufrufe an die Paperclip-API:

```python
"""Paperclip-API-Client — Kommunikation mit dem Paperclip-Board."""

from typing import Any

import httpx
import structlog

from app.config import settings

logger = structlog.get_logger()

# Timeout für ausgehende Requests an Paperclip
_TIMEOUT = httpx.Timeout(30.0, connect=10.0)


class PaperclipAPIError(Exception):
    """Fehler bei der Kommunikation mit der Paperclip-API."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class PaperclipClient:
    """HTTP-Client für die Paperclip-API.

    Alle Requests enthalten den Bearer-Token und die Run-ID als Header.
    """

    def __init__(self, run_id: str | None = None):
        self.base_url = settings.paperclip_api_url.rstrip("/")
        self.api_key = settings.paperclip_api_key
        self.run_id = run_id

    def _headers(self) -> dict[str, str]:
        """Standard-Header für alle Paperclip-API-Aufrufe."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.run_id:
            headers["X-Paperclip-Run-Id"] = self.run_id
        return headers

    async def get_agent_info(self) -> dict[str, Any]:
        """GET /api/agents/me — Eigene Agent-Informationen abrufen."""
        url = f"{self.base_url}/api/agents/me"
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(url, headers=self._headers())

        if response.status_code != 200:
            raise PaperclipAPIError(
                f"Agent-Info abrufen fehlgeschlagen: {response.status_code} {response.text}",
                status_code=response.status_code,
            )

        data = response.json()
        logger.info(
            "Paperclip Agent-Info abgerufen",
            agent_name=data.get("name"),
            agent_role=data.get("role"),
        )
        return data

    async def get_issue(self, task_id: str) -> dict[str, Any]:
        """GET /api/issues/{taskId} — Issue-Details abrufen."""
        url = f"{self.base_url}/api/issues/{task_id}"
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(url, headers=self._headers())

        if response.status_code == 404:
            raise PaperclipAPIError(
                f"Issue {task_id} nicht gefunden",
                status_code=404,
            )
        if response.status_code != 200:
            raise PaperclipAPIError(
                f"Issue abrufen fehlgeschlagen: {response.status_code} {response.text}",
                status_code=response.status_code,
            )

        data = response.json()
        logger.info(
            "Paperclip Issue abgerufen",
            task_id=task_id,
            title=data.get("title"),
            status=data.get("status"),
        )
        return data

    async def checkout_issue(self, task_id: str) -> dict[str, Any]:
        """POST /api/issues/{taskId}/checkout — Issue zur Bearbeitung reservieren."""
        url = f"{self.base_url}/api/issues/{task_id}/checkout"
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(url, headers=self._headers())

        if response.status_code not in (200, 201):
            raise PaperclipAPIError(
                f"Issue-Checkout fehlgeschlagen: {response.status_code} {response.text}",
                status_code=response.status_code,
            )

        data = response.json()
        logger.info("Paperclip Issue ausgecheckt", task_id=task_id)
        return data

    async def update_issue(
        self,
        task_id: str,
        *,
        status: str | None = None,
        comment: str | None = None,
        result_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """PATCH /api/issues/{taskId} — Issue mit Ergebnis aktualisieren."""
        url = f"{self.base_url}/api/issues/{task_id}"

        payload: dict[str, Any] = {}
        if status:
            payload["status"] = status
        if comment:
            payload["comment"] = comment
        if result_data:
            payload["result"] = result_data

        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.patch(
                url,
                json=payload,
                headers=self._headers(),
            )

        if response.status_code not in (200, 204):
            raise PaperclipAPIError(
                f"Issue-Update fehlgeschlagen: {response.status_code} {response.text}",
                status_code=response.status_code,
            )

        data = response.json() if response.content else {}
        logger.info(
            "Paperclip Issue aktualisiert",
            task_id=task_id,
            status=status,
            has_comment=bool(comment),
        )
        return data

    async def add_comment(self, task_id: str, body: str) -> dict[str, Any]:
        """POST /api/issues/{taskId}/comments — Kommentar hinzufuegen."""
        url = f"{self.base_url}/api/issues/{task_id}/comments"
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                url,
                json={"body": body},
                headers=self._headers(),
            )

        if response.status_code not in (200, 201):
            raise PaperclipAPIError(
                f"Kommentar fehlgeschlagen: {response.status_code} {response.text}",
                status_code=response.status_code,
            )

        return response.json()
```

---

## 5. Heartbeat-Endpoint — Vollstaendige Implementierung

### 5.1 Neue Datei: `app/api/routes/heartbeat.py`

```python
"""Paperclip-Heartbeat-Endpoint — Empfängt Heartbeats und verarbeitet Aufgaben."""

import time
import uuid

import structlog
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    PaperclipHeartbeatRequest,
    PaperclipHeartbeatResponse,
    TaskCreate,
)
from app.config import settings
from app.integrations.paperclip_client import PaperclipClient, PaperclipAPIError
from app.models.task import Task, TaskStatus

logger = structlog.get_logger()

router = APIRouter()


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _map_issue_to_task_type(issue: dict) -> str:
    """Paperclip-Issue-Labels auf Agent-Agency-Aufgabentypen mappen.

    Paperclip-Issues können Labels wie 'bug', 'feature', 'docs' tragen.
    Diese werden auf die internen Typen 'code', 'content', 'research'
    abgebildet.
    """
    labels = {label.lower() for label in issue.get("labels", [])}
    issue_type = issue.get("type", "").lower()

    # Code-Aufgaben
    if labels & {"bug", "feature", "refactor", "tech-debt"} or issue_type in ("bug", "feature"):
        return "code"

    # Content/Dokumentation
    if labels & {"docs", "documentation", "content", "copy"} or issue_type == "docs":
        return "content"

    # Research/Analyse
    if labels & {"research", "spike", "investigation", "analysis"} or issue_type == "research":
        return "research"

    # Fallback: Lässt den Orchestrator entscheiden
    return "general"


def _build_description(issue: dict, wake_reason: str) -> str:
    """Ausführliche Aufgabenbeschreibung aus Paperclip-Issue erstellen."""
    parts = []

    # Hauptbeschreibung
    body = issue.get("body") or issue.get("description") or ""
    if body:
        parts.append(body)

    # Akzeptanzkriterien
    acceptance = issue.get("acceptanceCriteria")
    if acceptance:
        parts.append(f"\n\n[Akzeptanzkriterien]:\n{acceptance}")

    # Labels als Kontext
    labels = issue.get("labels", [])
    if labels:
        parts.append(f"\n\n[Labels]: {', '.join(labels)}")

    # Priorität
    priority = issue.get("priority")
    if priority:
        parts.append(f"\n[Priorität]: {priority}")

    # Auslöser
    parts.append(f"\n[Auslöser]: {wake_reason}")

    return "\n".join(parts) if parts else "Keine Beschreibung vorhanden."


# ---------------------------------------------------------------------------
# Heartbeat-Protokoll (7 Schritte)
# ---------------------------------------------------------------------------

@router.post("/heartbeat/", response_model=PaperclipHeartbeatResponse)
async def receive_heartbeat(heartbeat: PaperclipHeartbeatRequest):
    """Empfängt einen Heartbeat von Paperclip und verarbeitet die zugewiesene Aufgabe.

    Das Heartbeat-Protokoll durchläuft 7 Schritte:

    1. Validierung — Prüfe ob Paperclip aktiviert und Agent-ID korrekt
    2. Agent-Info — Hole eigene Agent-Informationen von Paperclip
    3. Issue laden — Hole Issue-Details über Paperclip-API
    4. Checkout — Reserviere die Issue zur Bearbeitung
    5. Mapping — Übersetze Paperclip-Issue in Agent-Agency-Task
    6. Ausführung — Verarbeite über die bestehende Workflow-Engine
    7. Rückmeldung — Aktualisiere Issue in Paperclip mit Ergebnis
    """
    start_time = time.time()
    run_id = heartbeat.runId
    task_id = heartbeat.context.taskId
    wake_reason = heartbeat.context.wakeReason

    logger.info(
        "Paperclip Heartbeat empfangen",
        run_id=run_id,
        agent_id=heartbeat.agentId,
        task_id=task_id,
        wake_reason=wake_reason,
    )

    # -----------------------------------------------------------------------
    # Schritt 1: Validierung
    # -----------------------------------------------------------------------
    if not settings.paperclip_enabled:
        raise HTTPException(
            status_code=503,
            detail="Paperclip-Integration ist nicht aktiviert",
        )

    if heartbeat.agentId != settings.paperclip_agent_id:
        logger.warning(
            "Agent-ID stimmt nicht überein",
            expected=settings.paperclip_agent_id,
            received=heartbeat.agentId,
        )
        raise HTTPException(
            status_code=403,
            detail="Agent-ID stimmt nicht mit der konfigurierten ID überein",
        )

    client = PaperclipClient(run_id=run_id)

    try:
        # -------------------------------------------------------------------
        # Schritt 2: Agent-Info abrufen
        # -------------------------------------------------------------------
        agent_info = await client.get_agent_info()
        logger.info(
            "Schritt 2 abgeschlossen: Agent-Info",
            agent_name=agent_info.get("name"),
            agent_role=agent_info.get("role"),
        )

        # -------------------------------------------------------------------
        # Schritt 3: Issue-Details laden
        # -------------------------------------------------------------------
        issue = await client.get_issue(task_id)
        logger.info(
            "Schritt 3 abgeschlossen: Issue geladen",
            task_id=task_id,
            title=issue.get("title"),
            status=issue.get("status"),
        )

        # Prüfe ob Issue bearbeitbar ist
        issue_status = issue.get("status", "").lower()
        if issue_status in ("done", "closed", "cancelled"):
            return PaperclipHeartbeatResponse(
                status="completed",
                runId=run_id,
                taskId=task_id,
                summary=f"Issue bereits im Endzustand: {issue_status}",
            )

        # -------------------------------------------------------------------
        # Schritt 4: Issue zur Bearbeitung auschecken
        # -------------------------------------------------------------------
        await client.checkout_issue(task_id)
        logger.info("Schritt 4 abgeschlossen: Issue ausgecheckt", task_id=task_id)

        # -------------------------------------------------------------------
        # Schritt 5: Paperclip-Issue auf Agent-Agency-Task mappen
        # -------------------------------------------------------------------
        title = issue.get("title", "Unbenannte Aufgabe")
        description = _build_description(issue, wake_reason)
        task_type = _map_issue_to_task_type(issue)

        # Kontext-Daten für die interne Verarbeitung
        context = {
            "source": "paperclip",
            "paperclip_run_id": run_id,
            "paperclip_issue_id": task_id,
            "paperclip_company_id": heartbeat.companyId,
            "paperclip_agent_id": heartbeat.agentId,
            "wake_reason": wake_reason,
            "issue_labels": issue.get("labels", []),
            "issue_priority": issue.get("priority"),
            "issue_type": issue.get("type"),
            "mapped_task_type": task_type,
        }

        # Kommentar-Kontext bei mention-Trigger
        if wake_reason == "mention" and heartbeat.context.commentId:
            context["trigger_comment_id"] = heartbeat.context.commentId

        logger.info(
            "Schritt 5 abgeschlossen: Mapping",
            title=title,
            task_type=task_type,
            context_keys=list(context.keys()),
        )

        # -------------------------------------------------------------------
        # Schritt 6: Aufgabe intern verarbeiten
        # -------------------------------------------------------------------
        internal_task_id = await _execute_via_workflow_engine(
            title=title,
            description=description,
            context=context,
        )

        # Warte auf Ergebnis (die Workflow-Engine arbeitet synchron im Celery-Worker,
        # aber hier rufen wir sie direkt auf für den synchronen Heartbeat-Modus)
        execution_time_ms = int((time.time() - start_time) * 1000)

        # Lade das Ergebnis der internen Aufgabe
        task_result = await _get_task_result(internal_task_id)

        logger.info(
            "Schritt 6 abgeschlossen: Ausführung",
            internal_task_id=internal_task_id,
            status=task_result["status"],
            execution_time_ms=execution_time_ms,
        )

        # -------------------------------------------------------------------
        # Schritt 7: Ergebnis an Paperclip zurückmelden
        # -------------------------------------------------------------------
        summary = task_result.get("summary", "Aufgabe verarbeitet")
        deliverables = task_result.get("deliverables", [])

        # Kommentar mit Ergebnis zusammenstellen
        comment_parts = [f"## Ergebnis von Agent-Agency\n"]
        comment_parts.append(f"**Status:** {task_result['status']}")
        comment_parts.append(f"**Ausführungszeit:** {execution_time_ms}ms")
        comment_parts.append(f"**Interne Task-ID:** `{internal_task_id}`\n")

        if summary:
            comment_parts.append(f"### Zusammenfassung\n{summary}\n")

        if deliverables:
            comment_parts.append("### Ergebnisse\n")
            for i, deliverable in enumerate(deliverables, 1):
                d_type = deliverable.get("type", "unbekannt")
                d_content = deliverable.get("content", "")
                if d_type == "code":
                    lang = deliverable.get("metadata", {}).get("language", "")
                    comment_parts.append(f"**Ergebnis {i}** ({d_type}):\n```{lang}\n{d_content}\n```\n")
                else:
                    comment_parts.append(f"**Ergebnis {i}** ({d_type}):\n{d_content}\n")

        if task_result.get("error"):
            comment_parts.append(f"### Fehler\n{task_result['error']}")

        comment_body = "\n".join(comment_parts)

        # Issue in Paperclip aktualisieren
        result_status = "done" if task_result["status"] == "completed" else "review"
        await client.update_issue(
            task_id,
            status=result_status,
            comment=comment_body,
            result_data={
                "internalTaskId": internal_task_id,
                "summary": summary,
                "deliverables": deliverables,
                "executionTimeMs": execution_time_ms,
            },
        )

        logger.info(
            "Schritt 7 abgeschlossen: Rückmeldung an Paperclip",
            task_id=task_id,
            paperclip_status=result_status,
        )

        return PaperclipHeartbeatResponse(
            status="completed" if task_result["status"] == "completed" else "failed",
            runId=run_id,
            taskId=task_id,
            internalTaskId=internal_task_id,
            summary=summary,
            error=task_result.get("error"),
            executionTimeMs=execution_time_ms,
        )

    except PaperclipAPIError as e:
        logger.error(
            "Paperclip-API-Fehler",
            run_id=run_id,
            task_id=task_id,
            error=str(e),
            status_code=e.status_code,
        )

        # Versuche Fehler an Paperclip zu melden
        try:
            await client.update_issue(
                task_id,
                comment=f"## Fehler bei der Verarbeitung\n\n{str(e)}",
            )
        except Exception:
            pass

        return PaperclipHeartbeatResponse(
            status="failed",
            runId=run_id,
            taskId=task_id,
            error=str(e),
            executionTimeMs=int((time.time() - start_time) * 1000),
        )

    except Exception as e:
        logger.exception(
            "Unerwarteter Fehler bei Heartbeat-Verarbeitung",
            run_id=run_id,
            task_id=task_id,
        )

        # Versuche Fehler an Paperclip zu melden
        try:
            await client.update_issue(
                task_id,
                comment=f"## Interner Fehler\n\nAgent-Agency konnte die Aufgabe nicht verarbeiten: {str(e)}",
            )
        except Exception:
            pass

        return PaperclipHeartbeatResponse(
            status="failed",
            runId=run_id,
            taskId=task_id,
            error="Interner Verarbeitungsfehler",
            executionTimeMs=int((time.time() - start_time) * 1000),
        )


# ---------------------------------------------------------------------------
# Interne Ausführung über die bestehende Workflow-Engine
# ---------------------------------------------------------------------------

async def _execute_via_workflow_engine(
    title: str,
    description: str,
    context: dict,
) -> str:
    """Erstellt eine interne Aufgabe und verarbeitet sie synchron.

    Im Heartbeat-Modus wird die Aufgabe NICHT über Celery enqueued,
    sondern direkt über _process_task() ausgeführt, da Paperclip
    eine synchrone Antwort erwartet.

    Returns:
        Die interne Task-ID als String.
    """
    from app.orchestration.workflow_engine import _process_task, _get_worker_session

    async with _get_worker_session()() as db:
        task = Task(
            external_id=f"paperclip-{context.get('paperclip_issue_id', 'unknown')}",
            title=title,
            description=description,
            context=context,
            status=TaskStatus.ACCEPTED.value,
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)
        task_id = str(task.id)

    logger.info("Interne Aufgabe erstellt", task_id=task_id, title=title)

    # Direkte synchrone Ausführung (nicht über Celery)
    await _process_task(task_id)

    return task_id


async def _get_task_result(task_id: str) -> dict:
    """Lade das Ergebnis einer verarbeiteten Aufgabe aus der Datenbank."""
    from app.orchestration.workflow_engine import _get_worker_session

    async with _get_worker_session()() as db:
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            return {
                "status": "failed",
                "error": f"Interne Aufgabe {task_id} nicht gefunden",
                "summary": "",
                "deliverables": [],
            }

        return {
            "status": task.status,
            "error": task.error,
            "summary": task.title,
            "deliverables": task.deliverables or [],
            "token_usage": task.token_usage,
        }
```

---

## 6. Heartbeat-Protokoll — Detaillierte Schrittbeschreibung

### Schritt 1: Validierung

```python
# Prüfe ob die Integration aktiviert ist
if not settings.paperclip_enabled:
    raise HTTPException(status_code=503, detail="Paperclip-Integration ist nicht aktiviert")

# Prüfe ob die Agent-ID übereinstimmt
if heartbeat.agentId != settings.paperclip_agent_id:
    raise HTTPException(status_code=403, detail="Agent-ID stimmt nicht überein")
```

Dieser Schritt stellt sicher, dass:
- Die Paperclip-Integration explizit aktiviert wurde (`PAPERCLIP_ENABLED=true`)
- Nur Heartbeats für den korrekt konfigurierten Agent akzeptiert werden
- Unautorisierte Aufrufe sofort abgewiesen werden

### Schritt 2: Agent-Info abrufen

```python
client = PaperclipClient(run_id=heartbeat.runId)
agent_info = await client.get_agent_info()
# GET http://paperclip:3100/api/agents/me
# Header: Authorization: Bearer {PAPERCLIP_API_KEY}
# Header: X-Paperclip-Run-Id: {runId}
```

Die Agent-Info enthält Name, Rolle und Konfiguration des Agents in Paperclip. Dies ist nützlich, um das Verhalten dynamisch anzupassen (z.B. andere Executor-Strategie je nach Rolle).

### Schritt 3: Issue-Details laden

```python
issue = await client.get_issue(heartbeat.context.taskId)
# GET http://paperclip:3100/api/issues/{taskId}
```

Antwort-Beispiel:
```json
{
  "id": "issue-uuid",
  "title": "Login-Seite responsiv machen",
  "body": "Die Login-Seite bricht auf Mobilgeräten um...",
  "status": "todo",
  "priority": "high",
  "labels": ["bug", "frontend"],
  "type": "bug",
  "acceptanceCriteria": "- Kein Umbruch unter 375px\n- Tests bestehen"
}
```

### Schritt 4: Issue auschecken

```python
await client.checkout_issue(heartbeat.context.taskId)
# POST http://paperclip:3100/api/issues/{taskId}/checkout
```

Durch den Checkout wird die Issue in Paperclip als "in Bearbeitung" markiert. Andere Agents können sie nicht mehr beanspruchen. Bei Fehler (z.B. bereits ausgecheckt) wird eine `PaperclipAPIError` geworfen.

### Schritt 5: Mapping Paperclip-Issue auf Agent-Agency-Task

```python
# Typ-Mapping basierend auf Labels und Issue-Typ
task_type = _map_issue_to_task_type(issue)

# Beschreibung zusammenbauen
description = _build_description(issue, wake_reason)

# Kontext mit allen Paperclip-Metadaten anreichern
context = {
    "source": "paperclip",
    "paperclip_run_id": run_id,
    "paperclip_issue_id": task_id,
    # ... weitere Felder
}
```

Das Mapping-Schema:

| Paperclip-Labels                | Agent-Agency-Typ | Executor    |
| ------------------------------- | ---------------- | ----------- |
| `bug`, `feature`, `refactor`    | `code`           | `coder`     |
| `docs`, `documentation`         | `content`        | `writer`    |
| `research`, `spike`, `analysis` | `research`       | `researcher`|
| (alles andere)                  | `general`        | Orchestrator entscheidet |

### Schritt 6: Ausführung über Workflow-Engine

```python
internal_task_id = await _execute_via_workflow_engine(
    title=title,
    description=description,
    context=context,
)
```

Intern wird die bestehende Pipeline genutzt:
1. Task wird in der Datenbank erstellt (`TaskStatus.ACCEPTED`)
2. `_process_task()` wird **direkt** aufgerufen (nicht über Celery), da Paperclip eine synchrone Antwort erwartet
3. Die Pipeline durchläuft: Classify -> Execute -> QA -> Deliver
4. Das Ergebnis wird aus der Datenbank geladen

**Wichtig:** Im Heartbeat-Modus wird Celery umgangen. Die Aufgabe wird im Request-Thread verarbeitet. Der `PAPERCLIP_TIMEOUT_SECONDS`-Wert sollte den Paperclip-Heartbeat-Timeout (`timeoutSec` in der Adapter-Config) nicht überschreiten.

### Schritt 7: Rückmeldung an Paperclip

```python
# Issue-Status in Paperclip setzen
await client.update_issue(
    task_id,
    status="done",               # oder "review" bei Fehlern
    comment=comment_body,         # Markdown-Ergebnis als Kommentar
    result_data={                 # Strukturierte Daten
        "internalTaskId": internal_task_id,
        "summary": summary,
        "deliverables": deliverables,
        "executionTimeMs": execution_time_ms,
    },
)
# PATCH http://paperclip:3100/api/issues/{taskId}
```

Das Ergebnis wird in zwei Formen zurückgemeldet:
- **Kommentar:** Menschenlesbarer Markdown-Text mit Zusammenfassung, Code-Blöcken und Fehlermeldungen
- **Strukturierte Daten:** JSON-Objekt im `result`-Feld für maschinelle Weiterverarbeitung

---

## 7. Router in der App registrieren

### 7.1 Ergänzung in `app/main.py`

```python
# app/main.py — Import ergänzen

from app.api.routes import (
    agent_messages, agents, api_keys, attachments, audit, costs, events,
    heartbeat,  # <-- NEU
    pipelines, plugins, skills, tasks, teams, webhooks, workspaces,
)

# ... nach den bestehenden Router-Registrierungen ...

# Paperclip-Heartbeat (kein API-Key-Schutz — Paperclip authentifiziert sich selbst)
app.include_router(
    heartbeat.router,
    prefix="/api/v1",
    tags=["paperclip"],
)
```

**Hinweis:** Der Heartbeat-Endpoint nutzt **nicht** die `require_api_key`-Dependency, da Paperclip sich über die Agent-ID und den konfigurierten API-Key selbst authentifiziert (Schritt 1 der Validierung). Alternativ kann ein separater Paperclip-spezifischer Auth-Mechanismus implementiert werden:

```python
# Optional: Eigene Authentifizierung für den Heartbeat-Endpoint
from fastapi import Header

async def verify_paperclip_origin(
    x_paperclip_signature: str | None = Header(None),
) -> None:
    """Prüft die Herkunft eines Paperclip-Heartbeats via HMAC-Signatur."""
    if not x_paperclip_signature:
        raise HTTPException(status_code=401, detail="Paperclip-Signatur fehlt")
    # HMAC-Validierung hier implementieren
```

---

## 8. Docker-Compose-Anpassung

### 8.1 Umgebungsvariablen für API- und Worker-Service

In der `docker-compose.yml` muessen die neuen Umgebungsvariablen ergänzt werden:

```yaml
services:
  api:
    build: .
    ports: ["4108:8000"]
    env_file: .env
    environment:
      DATABASE_URL: postgresql+asyncpg://agent:${DB_PASSWORD:-changeme}@db:5432/agentic_company
      REDIS_URL: redis://redis:6379/0
      SEARXNG_URL: http://searxng:8080
      # === Paperclip-Integration ===
      PAPERCLIP_ENABLED: ${PAPERCLIP_ENABLED:-false}
      PAPERCLIP_API_URL: ${PAPERCLIP_API_URL:-}
      PAPERCLIP_API_KEY: ${PAPERCLIP_API_KEY:-}
      PAPERCLIP_AGENT_ID: ${PAPERCLIP_AGENT_ID:-}
      PAPERCLIP_TIMEOUT_SECONDS: ${PAPERCLIP_TIMEOUT_SECONDS:-300}
    # ... Rest bleibt gleich

  worker:
    build: .
    command: celery -A app.worker worker -l info -c 4
    env_file: .env
    environment:
      DATABASE_URL: postgresql+asyncpg://agent:${DB_PASSWORD:-changeme}@db:5432/agentic_company
      REDIS_URL: redis://redis:6379/0
      SEARXNG_URL: http://searxng:8080
      # === Paperclip-Integration ===
      PAPERCLIP_ENABLED: ${PAPERCLIP_ENABLED:-false}
      PAPERCLIP_API_URL: ${PAPERCLIP_API_URL:-}
      PAPERCLIP_API_KEY: ${PAPERCLIP_API_KEY:-}
      PAPERCLIP_AGENT_ID: ${PAPERCLIP_AGENT_ID:-}
      PAPERCLIP_TIMEOUT_SECONDS: ${PAPERCLIP_TIMEOUT_SECONDS:-300}
    # ... Rest bleibt gleich
```

### 8.2 Netzwerk-Konfiguration

Falls Paperclip im gleichen Docker-Netzwerk läuft:

```yaml
networks:
  agentic-network:
    driver: bridge
  # Falls Paperclip ein eigenes Netzwerk hat:
  paperclip-network:
    external: true
    name: paperclip_default

services:
  api:
    networks:
      - agentic-network
      - paperclip-network  # Zugriff auf Paperclip-API
```

### 8.3 `.env`-Beispielkonfiguration

```env
# === Paperclip-Integration ===
PAPERCLIP_ENABLED=true
PAPERCLIP_API_URL=http://paperclip:3100
PAPERCLIP_API_KEY=pk_live_xxxxxxxxxxxxxxxxxxxx
PAPERCLIP_AGENT_ID=agent_01HXXXXXXXXXXXXXXX
PAPERCLIP_TIMEOUT_SECONDS=300
```

---

## 9. Registrierung bei Paperclip

Agent-Agency wird als HTTP-Adapter-Agent im Paperclip-Board registriert:

```bash
curl -X POST http://localhost:3100/api/companies/{companyId}/agents \
  -H "Authorization: Bearer $BOARD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Coder",
    "role": "engineer",
    "adapterType": "http",
    "adapterConfig": {
      "url": "http://agent-agency:4108/api/v1/heartbeat/",
      "timeoutSec": 300
    }
  }'
```

**Parameter:**

| Feld                     | Wert                                              | Beschreibung                             |
| ------------------------ | ------------------------------------------------- | ---------------------------------------- |
| `name`                   | `"Coder"`                                         | Anzeigename im Paperclip-Board           |
| `role`                   | `"engineer"`                                      | Rolle: `engineer`, `writer`, `researcher`|
| `adapterType`            | `"http"`                                          | HTTP-Adapter (im Gegensatz zu WebSocket) |
| `adapterConfig.url`      | `"http://agent-agency:4108/api/v1/heartbeat/"`    | Heartbeat-URL                            |
| `adapterConfig.timeoutSec` | `300`                                           | Timeout — muss zu `PAPERCLIP_TIMEOUT_SECONDS` passen |

### Mehrere Agents registrieren

Für verschiedene Rollen können mehrere Agents registriert werden:

```bash
# Coder-Agent
curl -X POST http://localhost:3100/api/companies/{companyId}/agents \
  -H "Authorization: Bearer $BOARD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Agent-Agency Coder",
    "role": "engineer",
    "adapterType": "http",
    "adapterConfig": {
      "url": "http://agent-agency:4108/api/v1/heartbeat/",
      "timeoutSec": 300
    }
  }'

# Writer-Agent
curl -X POST http://localhost:3100/api/companies/{companyId}/agents \
  -H "Authorization: Bearer $BOARD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Agent-Agency Writer",
    "role": "writer",
    "adapterType": "http",
    "adapterConfig": {
      "url": "http://agent-agency:4108/api/v1/heartbeat/",
      "timeoutSec": 300
    }
  }'

# Researcher-Agent
curl -X POST http://localhost:3100/api/companies/{companyId}/agents \
  -H "Authorization: Bearer $BOARD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Agent-Agency Researcher",
    "role": "researcher",
    "adapterType": "http",
    "adapterConfig": {
      "url": "http://agent-agency:4108/api/v1/heartbeat/",
      "timeoutSec": 180
    }
  }'
```

Die `agentId` aus der Paperclip-Antwort muss als `PAPERCLIP_AGENT_ID` konfiguriert werden. Bei mehreren Agents kann ein einzelner Agent-Agency-Service alle Heartbeats empfangen — die Agent-ID-Prüfung in Schritt 1 kann dann auf eine Liste erweitert werden.

---

## 10. Test-Szenario

### 10.1 Manueller Heartbeat-Test

```bash
# Heartbeat simulieren (Paperclip ist nicht nötig)
curl -X POST http://localhost:4108/api/v1/heartbeat/ \
  -H "Content-Type: application/json" \
  -d '{
    "runId": "test-run-001",
    "agentId": "agent_01HXXXXXXXXXXXXXXX",
    "companyId": "company_01HXXXXXXXXX",
    "context": {
      "taskId": "issue-uuid-hier",
      "wakeReason": "assignment",
      "commentId": null
    }
  }'
```

### 10.2 Unit-Test

```python
# tests/test_heartbeat.py

import pytest
from unittest.mock import AsyncMock, patch

from httpx import AsyncClient


@pytest.fixture
def paperclip_settings(monkeypatch):
    """Paperclip-Einstellungen für Tests aktivieren."""
    monkeypatch.setattr("app.config.settings.paperclip_enabled", True)
    monkeypatch.setattr("app.config.settings.paperclip_api_url", "http://paperclip-test:3100")
    monkeypatch.setattr("app.config.settings.paperclip_api_key", "test-key")
    monkeypatch.setattr("app.config.settings.paperclip_agent_id", "test-agent-id")


async def test_heartbeat_disabled(client: AsyncClient):
    """Heartbeat wird abgelehnt wenn Paperclip deaktiviert."""
    response = await client.post("/api/v1/heartbeat/", json={
        "runId": "run-1",
        "agentId": "agent-1",
        "companyId": "company-1",
        "context": {"taskId": "task-1", "wakeReason": "assignment"},
    })
    assert response.status_code == 503


async def test_heartbeat_wrong_agent_id(client: AsyncClient, paperclip_settings):
    """Heartbeat mit falscher Agent-ID wird abgelehnt."""
    response = await client.post("/api/v1/heartbeat/", json={
        "runId": "run-1",
        "agentId": "wrong-agent-id",
        "companyId": "company-1",
        "context": {"taskId": "task-1", "wakeReason": "assignment"},
    })
    assert response.status_code == 403


async def test_heartbeat_success(client: AsyncClient, paperclip_settings):
    """Erfolgreicher Heartbeat-Durchlauf mit Mock-Paperclip."""
    mock_issue = {
        "id": "task-1",
        "title": "Button reparieren",
        "body": "Der Submit-Button funktioniert nicht auf Mobile",
        "status": "todo",
        "labels": ["bug", "frontend"],
        "type": "bug",
        "priority": "high",
    }

    with patch("app.api.routes.heartbeat.PaperclipClient") as MockClient:
        instance = MockClient.return_value
        instance.get_agent_info = AsyncMock(return_value={"name": "Coder", "role": "engineer"})
        instance.get_issue = AsyncMock(return_value=mock_issue)
        instance.checkout_issue = AsyncMock(return_value={})
        instance.update_issue = AsyncMock(return_value={})

        with patch("app.api.routes.heartbeat._execute_via_workflow_engine") as mock_exec:
            mock_exec.return_value = "internal-task-uuid"

            with patch("app.api.routes.heartbeat._get_task_result") as mock_result:
                mock_result.return_value = {
                    "status": "completed",
                    "summary": "Button repariert",
                    "deliverables": [{"type": "code", "content": "fix.patch"}],
                    "error": None,
                }

                response = await client.post("/api/v1/heartbeat/", json={
                    "runId": "run-1",
                    "agentId": "test-agent-id",
                    "companyId": "company-1",
                    "context": {"taskId": "task-1", "wakeReason": "assignment"},
                })

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "completed"
                assert data["runId"] == "run-1"
                assert data["internalTaskId"] == "internal-task-uuid"
```

---

## 11. Sequenzdiagramm

```
Paperclip                 Agent-Agency              Workflow-Engine          Paperclip-API
   |                           |                          |                      |
   | POST /heartbeat/          |                          |                      |
   |-------------------------->|                          |                      |
   |                           |                          |                      |
   |                           | 1. Validierung           |                      |
   |                           |---+                      |                      |
   |                           |   |                      |                      |
   |                           |<--+                      |                      |
   |                           |                          |                      |
   |                           | 2. GET /api/agents/me    |                      |
   |                           |--------------------------------------------->   |
   |                           |   <-- Agent-Info --------|-------------------   |
   |                           |                          |                      |
   |                           | 3. GET /api/issues/{id}  |                      |
   |                           |--------------------------------------------->   |
   |                           |   <-- Issue-Details -----|-------------------   |
   |                           |                          |                      |
   |                           | 4. POST /issues/{id}/checkout                   |
   |                           |--------------------------------------------->   |
   |                           |   <-- OK ----------------|-------------------   |
   |                           |                          |                      |
   |                           | 5. Mapping               |                      |
   |                           |---+                      |                      |
   |                           |   |                      |                      |
   |                           |<--+                      |                      |
   |                           |                          |                      |
   |                           | 6. _process_task()       |                      |
   |                           |------------------------->|                      |
   |                           |                          | classify             |
   |                           |                          | execute              |
   |                           |                          | QA review            |
   |                           |   <-- Ergebnis ---------|                      |
   |                           |                          |                      |
   |                           | 7. PATCH /api/issues/{id}|                      |
   |                           |--------------------------------------------->   |
   |                           |   <-- OK ----------------|-------------------   |
   |                           |                          |                      |
   |   <-- 200 Ergebnis -------|                          |                      |
   |                           |                          |                      |
```

---

## 12. Fehlerbehandlung und Edge Cases

### Timeout-Verhalten

Paperclip wartet maximal `timeoutSec` Sekunden (konfiguriert bei der Agent-Registrierung). Falls Agent-Agency nicht rechtzeitig antwortet:
- Paperclip markiert den Run als "timed out"
- Die interne Aufgabe läuft ggf. weiter
- Beim nächsten Heartbeat kann geprüft werden, ob die Aufgabe inzwischen abgeschlossen ist

### Idempotenz

Derselbe Heartbeat kann mehrfach eintreffen (z.B. bei Netzwerk-Retries). Die `runId` sollte als Idempotenz-Key verwendet werden:

```python
# Prüfung auf Duplikate (optional, in Schritt 1)
from app.models.task import Task

async with _get_worker_session()() as db:
    existing = await db.execute(
        select(Task).where(
            Task.context["paperclip_run_id"].astext == heartbeat.runId
        )
    )
    if existing.scalar_one_or_none():
        return PaperclipHeartbeatResponse(
            status="completed",
            runId=run_id,
            taskId=task_id,
            summary="Heartbeat bereits verarbeitet (Duplikat)",
        )
```

### Fehlerhafte Issues

Falls eine Issue nicht verarbeitet werden kann (z.B. leere Beschreibung), wird ein informativer Kommentar an Paperclip gesendet statt die Aufgabe stillschweigend zu verwerfen.

---

## 13. Zusammenfassung der neuen/geänderten Dateien

| Datei                                      | Aktion   | Beschreibung                                |
| ------------------------------------------ | -------- | ------------------------------------------- |
| `app/config.py`                            | Ändern   | 5 neue Paperclip-Settings                   |
| `app/api/schemas.py`                       | Ändern   | 3 neue Pydantic-Modelle für Heartbeat       |
| `app/integrations/paperclip_client.py`     | Neu      | HTTP-Client für Paperclip-API               |
| `app/api/routes/heartbeat.py`              | Neu      | Heartbeat-Endpoint mit 7-Schritt-Protokoll  |
| `app/main.py`                              | Ändern   | Router-Registrierung für Heartbeat          |
| `docker-compose.yml`                       | Ändern   | Paperclip-Umgebungsvariablen                |
| `.env`                                     | Ändern   | Paperclip-Konfigurationswerte               |
| `tests/test_heartbeat.py`                  | Neu      | Unit-Tests für den Heartbeat-Endpoint       |
