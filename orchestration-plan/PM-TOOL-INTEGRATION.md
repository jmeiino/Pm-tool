# PM-Tool — Paperclip-Integration

## Übersicht

PM-Tool (Django/Next.js) dient als "Board" für Paperclip (Agent-Agency). Menschen erstellen Aufgaben im PM-Tool, Paperclip delegiert sie an AI-Agents, und die Ergebnisse fließen über Webhooks und SSE zurück ins PM-Tool. Beide Systeme kommunizieren bidirektional über REST-APIs und HMAC-signierte Webhooks.

### Architektur-Diagramm

```
┌─────────────────────────────────┐          ┌─────────────────────────────────┐
│          PM-Tool                │          │         Paperclip               │
│  (Django + Next.js + Celery)    │          │  (FastAPI + Celery + SQLAlchemy)│
│                                 │          │                                 │
│  Issue erstellt / Jira-Sync     │          │  Orchestrator → Executor → QA   │
│         │                       │          │         ▲                       │
│         ▼                       │          │         │                       │
│  AgentBridgeService             │──POST───▶│  POST /api/v1/tasks/            │
│  (httpx-Client)                 │          │  (TaskCreate Schema)            │
│                                 │          │         │                       │
│                                 │          │         ▼                       │
│  POST /api/v1/agents/           │◀─WEBHOOK─│  pm_tool_callback.py            │
│    webhooks/event/              │          │  (HMAC-SHA256 signiert)         │
│  (webhook_handler.py)           │          │                                 │
│         │                       │          │                                 │
│         ▼                       │          │                                 │
│  AgentTask / AgentMessage       │          │  Task / TaskMessage             │
│  Status-Update + SSE-Stream     │          │  Deliverables + Events          │
└─────────────────────────────────┘          └─────────────────────────────────┘
```

### Bestehende Infrastruktur

**PM-Tool** (C:\Projekte\Pm-tool):
- `backend/apps/agents/models.py` — AgentCompanyConfig, AgentProfile, AgentTask, AgentMessage
- `backend/apps/agents/services.py` — AgentBridgeService (httpx-Client)
- `backend/apps/agents/webhook_handler.py` — Empfängt HMAC-signierte Events
- `backend/apps/agents/views.py` — ViewSets, Webhook-Endpoint, SSE-Stream
- `backend/apps/agents/urls.py` — Router-Konfiguration
- `backend/apps/agents/serializers.py` — DRF-Serializers für Tasks/Messages

**Paperclip** (C:\Projekte\Agent-Agency):
- `app/api/routes/tasks.py` — Task-CRUD (create, get, list, reply, cancel, approve, reject)
- `app/api/schemas.py` — TaskCreate, TaskResponse, TaskReply
- `app/callbacks/pm_tool_callback.py` — Webhook-Versand mit HMAC-SHA256
- `app/api/routes/webhooks.py` — Webhook-Ereignistypen-Info
- `app/config.py` — webhook_secret, Ports, Redis-URL

---

## Richtung 1: PM-Tool → Paperclip (Aufgabe erstellen)

### Trigger-Szenarien

| Auslöser | Verhalten |
|----------|-----------|
| Manuell: User klickt "An AI-Agent delegieren" | Sofortige Delegation via `AgentTaskViewSet.delegate()` |
| Automatisch: Issue mit Label `ai-agent` erstellt | Django post_save Signal auf Issue → Celery-Task |
| Jira-Sync: Issue aus Jira mit AI-Label importiert | Vorhandener Jira-Sync-Hook prüft Label → Celery-Task |

### Bestehender Client: AgentBridgeService

Der `AgentBridgeService` in `backend/apps/agents/services.py` ist bereits vollständig implementiert:

```python
class AgentBridgeService:
    """HTTP-Client für den Agent-Service."""

    def __init__(self, company: AgentCompanyConfig):
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
        response = self.client.post("/api/v1/tasks/", json=payload)
        response.raise_for_status()
        return response.json()

    def cancel_task(self, external_task_id: str) -> dict: ...
    def send_reply(self, external_task_id: str, content: str, decision_option: str = "") -> dict: ...
    def get_company_status(self) -> dict: ...
    def sync_agent_profiles(self) -> list[dict]: ...
```

### Paperclip-API: TaskCreate Schema

Der Paperclip-Endpunkt `POST /api/v1/tasks/` erwartet:

```json
{
  "external_id": "pm-PROJ-42-a1b2c3d4",
  "title": "Login-Seite implementieren",
  "description": "Erstelle eine responsive Login-Seite mit E-Mail/Passwort-Authentifizierung...",
  "context": {
    "project_key": "PROJ",
    "issue_key": "PROJ-42",
    "issue_type": "task",
    "instructions": "Verwende React + Tailwind CSS"
  },
  "callback_url": "https://pm-tool.example.com/api/v1/agents/webhooks/event/"
}
```

**Validierung (Paperclip-seitig):**
- `external_id`: 1–255 Zeichen (Pflichtfeld)
- `title`: 1–500 Zeichen (Pflichtfeld)
- `description`: 1–50.000 Zeichen (Pflichtfeld)
- `context`: JSON-Objekt, max. 100.000 Bytes serialisiert
- `callback_url`: Optional, aber erforderlich für Rückmeldungen
- `reply_url`: Optional, für User-Antworten bei Rückfragen

### Bestehende Delegation (Views)

Die `delegate`-Action in `AgentTaskViewSet` führt die vollständige Kette durch:

1. Validierung via `DelegateTaskSerializer` (issue_id, priority 1–5, task_type, instructions)
2. Erstellt lokalen `AgentTask` mit `external_task_id = f"pm-{issue.key}-{uuid.uuid4().hex[:8]}"`
3. Erstellt System-Nachricht "Aufgabe ... an die agentische Firma delegiert."
4. Ruft `AgentBridgeService.delegate_task()` auf
5. Setzt Status auf `ASSIGNED` bei Erfolg, erstellt Error-Message bei Fehler

### Celery-Task für automatische Delegation

Für die automatische Delegation muss ein neuer Celery-Task erstellt werden:

**Datei: `backend/apps/agents/tasks.py`** (neu)

```python
"""Celery-Tasks für die Paperclip-Integration."""
import logging
import uuid

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_to_paperclip_task(self, issue_id: int, user_id: int, instructions: str = ""):
    """Issue asynchron an Paperclip delegieren."""
    from apps.agents.models import AgentCompanyConfig, AgentMessage, AgentTask
    from apps.agents.services import AgentBridgeService
    from apps.projects.models import Issue
    from django.contrib.auth import get_user_model

    User = get_user_model()

    try:
        issue = Issue.objects.select_related("project").get(id=issue_id)
        user = User.objects.get(id=user_id)
    except (Issue.DoesNotExist, User.DoesNotExist) as e:
        logger.error("Issue oder User nicht gefunden: %s", e)
        return {"status": "error", "reason": str(e)}

    company = AgentCompanyConfig.objects.filter(
        user=user, is_enabled=True
    ).first()
    if not company:
        logger.warning("Keine aktive Agent-Company für User %s", user.username)
        return {"status": "error", "reason": "Keine Agent-Company konfiguriert"}

    # Prüfen ob bereits ein aktiver Task für dieses Issue existiert
    existing = AgentTask.objects.filter(
        issue=issue,
        status__in=["pending", "assigned", "in_progress", "review", "needs_input"],
    ).exists()
    if existing:
        logger.info("Issue %s hat bereits einen aktiven Agent-Task", issue.key)
        return {"status": "skipped", "reason": "Aktiver Task existiert bereits"}

    task = AgentTask.objects.create(
        issue=issue,
        company=company,
        external_task_id=f"pm-{issue.key}-{uuid.uuid4().hex[:8]}",
        priority=3,
        task_type=_infer_task_type(issue),
    )

    AgentMessage.objects.create(
        task=task,
        message_type=AgentMessage.MessageType.SYSTEM,
        content=f"Aufgabe '{issue.title}' automatisch an Paperclip delegiert.",
    )

    try:
        with AgentBridgeService(company) as bridge:
            result = bridge.delegate_task(task, instructions=instructions)
        task.status = AgentTask.Status.ASSIGNED
        task.save(update_fields=["status", "updated_at"])
        logger.info("Issue %s erfolgreich an Paperclip delegiert", issue.key)
        return {"status": "ok", "task_id": task.id}
    except Exception as exc:
        AgentMessage.objects.create(
            task=task,
            message_type=AgentMessage.MessageType.ERROR,
            content=f"Verbindungsfehler: {str(exc)}",
        )
        logger.error("Delegation fehlgeschlagen: %s", exc)
        raise self.retry(exc=exc)


def _infer_task_type(issue) -> str:
    """Task-Typ anhand des Issue-Typs ableiten."""
    mapping = {
        "bug": "software",
        "feature": "software",
        "story": "software",
        "task": "general",
        "documentation": "content",
        "research": "research",
        "design": "design",
    }
    return mapping.get(issue.issue_type, "general")
```

### Django Signal für automatische Delegation

**Datei: `backend/apps/agents/signals.py`** (neu)

```python
"""Signals für automatische Paperclip-Delegation."""
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.projects.models import Issue

logger = logging.getLogger(__name__)

AI_DELEGATION_LABELS = {"ai-agent", "paperclip", "auto-delegate"}


@receiver(post_save, sender=Issue)
def auto_delegate_to_paperclip(sender, instance, created, **kwargs):
    """Bei neuen Issues mit AI-Label automatisch an Paperclip delegieren."""
    if not created:
        return

    # Prüfen ob Issue AI-Labels hat
    issue_labels = set(instance.labels or [])
    if not issue_labels & AI_DELEGATION_LABELS:
        return

    # Prüfen ob der Projekt-Owner auto_delegate aktiviert hat
    from apps.agents.models import AgentCompanyConfig

    company = AgentCompanyConfig.objects.filter(
        user=instance.project.owner,
        is_enabled=True,
        settings__auto_delegate=True,
    ).first()

    if not company:
        return

    from apps.agents.tasks import send_to_paperclip_task

    send_to_paperclip_task.delay(
        issue_id=instance.id,
        user_id=instance.project.owner_id,
    )
    logger.info("Auto-Delegation ausgelöst für Issue %s", instance.key)
```

**Signal registrieren in `backend/apps/agents/apps.py`:**

```python
from django.apps import AppConfig


class AgentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.agents"
    verbose_name = "Agent-Integration"

    def ready(self):
        import apps.agents.signals  # noqa: F401
```

---

## Richtung 2: Paperclip → PM-Tool (Status-Updates via Webhooks)

### Webhook-Event-Typen

Paperclip sendet folgende Events (definiert in `app/api/routes/webhooks.py`):

| Event | Beschreibung | PM-Tool-Handler |
|-------|-------------|-----------------|
| `task.accepted` | Aufgabe angenommen | `_handle_task_status_changed` |
| `task.assigned` | Agent zugewiesen | `_handle_task_status_changed` |
| `task.status_changed` | Status geändert | `_handle_task_status_changed` |
| `task.needs_input` | Agent stellt Rückfrage | `_handle_agent_message` |
| `task.deliverable` | Ergebnis bereitgestellt | `_handle_task_deliverable` |
| `task.completed` | Aufgabe abgeschlossen | `_handle_task_status_changed` |
| `task.failed` | Aufgabe fehlgeschlagen | `_handle_task_status_changed` |
| `agent.message` | Agent-Nachricht | `_handle_agent_message` |
| `agent.status_changed` | Agent-Status geändert | `_handle_agent_status_changed` |

### Webhook-Payload-Format (von Paperclip gesendet)

Paperclip's `pm_tool_callback.py` sendet:

```json
{
  "event_type": "task.status_changed",
  "task_id": "a1b2c3d4-...",
  "external_id": "pm-PROJ-42-a1b2c3d4",
  "agent_id": "coder-agent-1",
  "data": {
    "status": "in_progress",
    "assigned_agent_id": "coder-agent-1"
  },
  "timestamp": "2026-03-29T14:30:00+00:00"
}
```

### HMAC-SHA256 Signatur-Verifizierung

**Paperclip signiert (pm_tool_callback.py):**
```python
signature = hmac.new(
    settings.webhook_secret.encode(),
    payload_body,
    hashlib.sha256,
).hexdigest()

# Header: X-Webhook-Signature: sha256=<hex-digest>
# Header: X-Webhook-Event: <event_type>
```

**PM-Tool verifiziert (webhook_handler.py):**
```python
def verify_webhook_signature(payload_body: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), payload_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

**Wichtig:** Das `webhook_secret` muss in beiden Systemen identisch sein:
- Paperclip: `WEBHOOK_SECRET` in `.env` (Standard: `dev-secret`)
- PM-Tool: `AgentCompanyConfig.webhook_secret` (pro Company konfiguriert)

### Bestehender Webhook-Endpoint im PM-Tool

Der Endpoint `POST /api/v1/agents/webhooks/event/` ist bereits implementiert:

1. Liest `X-Webhook-Signature` Header
2. Iteriert über alle aktiven `AgentCompanyConfig`-Einträge
3. Prüft HMAC-Signatur gegen jedes `webhook_secret`
4. Dispatcht an den passenden Handler aus `EVENT_HANDLERS`
5. Gibt 401 zurück, wenn keine Signatur passt

### Event-Handler-Mapping

```python
EVENT_HANDLERS = {
    "agent.message":         _handle_agent_message,
    "task.accepted":         _handle_task_status_changed,
    "task.assigned":         _handle_task_status_changed,
    "task.status_changed":   _handle_task_status_changed,
    "task.needs_input":      _handle_agent_message,
    "task.deliverable":      _handle_task_deliverable,
    "task.completed":        _handle_task_status_changed,
    "task.failed":           _handle_task_status_changed,
    "agent.status_changed":  _handle_agent_status_changed,
}
```

### Was die Handler tun

**`_handle_task_status_changed`:**
- Findet `AgentTask` via `external_task_id`
- Aktualisiert `status` (nur gültige Werte aus `AgentTask.Status.choices`)
- Bei `completed`: speichert `result_summary`
- Bei `assigned_agent_id`: verknüpft `AgentProfile`
- Erstellt `AgentMessage` vom Typ `STATUS_CHANGE`
- Publiziert Event via Redis Pub/Sub für SSE-Stream

**`_handle_agent_message`:**
- Findet `AgentTask` via `external_task_id`
- Erstellt/aktualisiert `AgentProfile` via `get_or_create` (Name, Rolle, Farbe)
- Erstellt `AgentMessage` mit Inhalt und Metadaten
- Bei `message_type == "question"`: setzt `is_decision_pending = True`
- Publiziert Event via Redis Pub/Sub

**`_handle_task_deliverable`:**
- Findet `AgentTask` via `external_task_id`
- Hängt Deliverable an `task.deliverables` (JSON-Array) an
- Erstellt `AgentMessage` vom Typ `DELIVERABLE`
- Publiziert Event via Redis Pub/Sub

### SSE-Stream für Echtzeit-Updates

PM-Tool bietet bereits einen SSE-Endpoint:

```
GET /api/v1/agents/tasks/<task_id>/stream/
```

Dieser abonniert den Redis-Kanal `agent_task:<external_task_id>` und streamt Events an das Frontend. Jeder Webhook-Handler publiziert automatisch auf diesen Kanal.

---

## Datenmodell-Mapping

### Status-Mapping PM-Tool ↔ Paperclip

| Paperclip (TaskStatus) | PM-Tool (AgentTask.Status) | Beschreibung |
|------------------------|---------------------------|-------------|
| `accepted` | `pending` | Angenommen, wartet auf Verarbeitung |
| `in_progress` | `in_progress` | Wird bearbeitet |
| `review` | `review` | QA-Agent prüft |
| `needs_input` | `needs_input` | Rückfrage an User |
| `needs_approval` | `needs_input` | Human-in-the-Loop-Freigabe |
| `completed` | `completed` | Erfolgreich abgeschlossen |
| `failed` | `failed` | Fehlgeschlagen |
| `cancelled` | `cancelled` | Abgebrochen |

### Feld-Mapping

| PM-Tool (AgentTask) | Paperclip (Task) | Richtung |
|---------------------|------------------|----------|
| `external_task_id` | `external_id` | PM→Paperclip (bei Erstellung) |
| `issue.title` | `title` | PM→Paperclip |
| `issue.description` | `description` | PM→Paperclip |
| `priority` | `context.priority` | PM→Paperclip |
| `task_type` | `context.type` | PM→Paperclip |
| `status` | `status` | Paperclip→PM (via Webhook) |
| `assigned_agent` | `assigned_to` | Paperclip→PM (via Webhook) |
| `result_summary` | `deliverables` | Paperclip→PM (via Webhook) |
| `deliverables` (JSON) | `deliverables` (JSON) | Paperclip→PM (via Webhook) |

---

## Konfiguration

### AgentCompanyConfig (PM-Tool)

Die Verbindung wird pro User in `AgentCompanyConfig` gespeichert:

| Feld | Beispielwert | Beschreibung |
|------|-------------|-------------|
| `name` | "Paperclip Production" | Anzeigename |
| `base_url` | "http://paperclip-api:8000" | Paperclip API-URL (internes Docker-Netzwerk) |
| `api_key` | "pk-abc123..." | API-Key für Paperclip (aus `API_KEYS` in Paperclip `.env`) |
| `webhook_secret` | "shared-hmac-secret-256bit" | Muss mit Paperclip `WEBHOOK_SECRET` übereinstimmen |
| `is_enabled` | `true` | Aktiviert/deaktiviert die Integration |
| `settings` | `{"auto_delegate": true}` | JSON-Einstellungen, inkl. Auto-Delegation |

### Paperclip .env (relevante Variablen)

```bash
# Authentifizierung — kommaseparierte API-Keys
API_KEYS=pk-pmtool-key-abc123,pk-admin-key-xyz789

# Webhook-Secret — muss mit AgentCompanyConfig.webhook_secret übereinstimmen
WEBHOOK_SECRET=shared-hmac-secret-256bit

# Netzwerk-Einstellungen
DATABASE_URL=postgresql+asyncpg://agent:changeme@db:5432/agentic_company
REDIS_URL=redis://redis:6379/0

# AI-Provider (mindestens einer erforderlich)
ANTHROPIC_API_KEY=sk-ant-...
# oder
OPENAI_API_KEY=sk-...
# oder
OPENROUTER_API_KEY=sk-or-...
```

### PM-Tool Django Settings (relevante Ergänzungen)

```python
# settings.py
PM_TOOL_BASE_URL = env("PM_TOOL_BASE_URL", default="http://localhost:4107")
```

Diese URL wird von `AgentBridgeService._pm_base_url()` verwendet, um die `callback_url` zu konstruieren.

---

## Docker-Compose-Integration

### Gemeinsames Netzwerk

Beide Services müssen im selben Docker-Netzwerk kommunizieren können. Es gibt zwei Ansätze:

#### Ansatz A: Gemeinsames externes Netzwerk

```yaml
# docker-compose.override.yml (PM-Tool)
networks:
  shared-network:
    external: true
    name: paperclip-network

services:
  backend:
    networks:
      - default
      - shared-network
    environment:
      PM_TOOL_BASE_URL: "http://backend:8000"
```

```yaml
# docker-compose.override.yml (Paperclip / Agent-Agency)
networks:
  agentic-network:
    name: paperclip-network
    driver: bridge

services:
  api:
    environment:
      WEBHOOK_SECRET: "shared-hmac-secret-256bit"
      API_KEYS: "pk-pmtool-key-abc123"
```

Netzwerk erstellen:
```bash
docker network create paperclip-network
```

#### Ansatz B: Kommunikation über Host-Ports

Wenn die Services auf demselben Host laufen, können sie über die exponierten Ports kommunizieren:

- PM-Tool Backend: `http://host.docker.internal:4107`
- Paperclip API: `http://host.docker.internal:4108`

```yaml
# PM-Tool .env
PAPERCLIP_BASE_URL=http://host.docker.internal:4108

# AgentCompanyConfig.base_url = http://host.docker.internal:4108
```

### Umgebungsvariablen für PM-Tool Services

```yaml
# docker-compose.yml (PM-Tool) — Ergänzungen für den backend-Service
services:
  backend:
    environment:
      # Basis-URL des eigenen PM-Tool (für callback_url-Konstruktion)
      PM_TOOL_BASE_URL: "http://backend:8000"
      # Redis für SSE-Pub/Sub
      REDIS_URL: "redis://redis:6379/1"
```

### Umgebungsvariablen für Paperclip Services

```yaml
# docker-compose.yml (Paperclip / Agent-Agency) — relevante Variablen
services:
  api:
    ports: ["4108:8000"]
    environment:
      API_KEYS: "pk-pmtool-key-abc123"
      WEBHOOK_SECRET: "shared-hmac-secret-256bit"

  worker:
    environment:
      WEBHOOK_SECRET: "shared-hmac-secret-256bit"
```

---

## Frontend-Anpassung (Next.js)

### Neuer Toggle auf Issue-Detail: "An AI-Agent delegieren"

**Komponente: `DelegateToAgentButton`**

```tsx
// frontend/components/issues/DelegateToAgentButton.tsx

interface DelegateToAgentButtonProps {
  issueId: number;
  hasActiveAgentTask: boolean;
}

export function DelegateToAgentButton({ issueId, hasActiveAgentTask }: DelegateToAgentButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [taskType, setTaskType] = useState("general");
  const [instructions, setInstructions] = useState("");
  const [priority, setPriority] = useState(3);

  const handleDelegate = async () => {
    await fetch("/api/v1/agents/tasks/delegate/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        issue_id: issueId,
        task_type: taskType,
        priority,
        instructions,
      }),
    });
    setIsOpen(false);
  };

  if (hasActiveAgentTask) {
    return <AgentTaskStatusBadge issueId={issueId} />;
  }

  return (
    <button onClick={() => setIsOpen(true)}>
      An AI-Agent delegieren
    </button>
    // ... Modal mit task_type, priority, instructions
  );
}
```

### Status-Badge: Agent-Task-Zustand

```tsx
// frontend/components/issues/AgentTaskStatusBadge.tsx

const STATUS_CONFIG = {
  pending:     { label: "Wartend",        color: "gray"   },
  assigned:    { label: "Zugewiesen",     color: "blue"   },
  in_progress: { label: "In Bearbeitung", color: "yellow" },
  review:      { label: "Im Review",      color: "purple" },
  needs_input: { label: "Rückfrage",      color: "orange" },
  completed:   { label: "Erledigt",       color: "green"  },
  failed:      { label: "Fehlgeschlagen", color: "red"    },
  cancelled:   { label: "Abgebrochen",    color: "gray"   },
};
```

### Echtzeit-Updates via SSE

```tsx
// frontend/hooks/useAgentTaskStream.ts

export function useAgentTaskStream(taskId: number) {
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [status, setStatus] = useState<string>("");

  useEffect(() => {
    const eventSource = new EventSource(
      `/api/v1/agents/tasks/${taskId}/stream/`
    );

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case "new_message":
          setMessages((prev) => [...prev, data.message]);
          break;
        case "status_changed":
          setStatus(data.new_status);
          break;
        case "deliverable":
          // Deliverable-Anzeige aktualisieren
          break;
      }
    };

    return () => eventSource.close();
  }, [taskId]);

  return { messages, status };
}
```

### Deliverables-Anzeige

```tsx
// frontend/components/issues/AgentDeliverables.tsx

interface Deliverable {
  type: string;       // "code", "document", "analysis"
  filename?: string;
  content: string;
  language?: string;  // Programmiersprache für Syntax-Highlighting
}

export function AgentDeliverables({ deliverables }: { deliverables: Deliverable[] }) {
  return (
    <div>
      <h3>Ergebnisse vom AI-Agent</h3>
      {deliverables.map((d, i) => (
        <div key={i}>
          {d.type === "code" ? (
            <CodeBlock language={d.language} filename={d.filename}>
              {d.content}
            </CodeBlock>
          ) : (
            <MarkdownRenderer content={d.content} />
          )}
        </div>
      ))}
    </div>
  );
}
```

---

## User-Interaktion: Rückfragen beantworten

### Ablauf bei `task.needs_input`

```
Paperclip                    PM-Tool                      User
   │                            │                            │
   │──webhook: needs_input─────▶│                            │
   │  (question + Optionen)     │──SSE: new_message─────────▶│
   │                            │  (is_decision_pending)     │
   │                            │                            │
   │                            │◀──POST reply/──────────────│
   │◀──POST /tasks/{id}/reply/──│  (content + decision)      │
   │  (AgentBridgeService)      │                            │
   │                            │                            │
   │──webhook: status_changed──▶│                            │
   │  (in_progress)             │──SSE: status_changed──────▶│
```

### PM-Tool Reply-Endpoint (bereits implementiert)

```python
# views.py — AgentTaskViewSet.reply()
@action(detail=True, methods=["post"])
def reply(self, request, pk=None):
    task = self.get_object()
    # 1. User-Message speichern
    # 2. Offene Rückfragen als beantwortet markieren
    # 3. An Paperclip weiterleiten via AgentBridgeService.send_reply()
```

### Paperclip Reply-Endpoint

```
POST /api/v1/tasks/{task_id}/reply/
Body: { "message": "Verwende OAuth2 mit Google-Provider" }
```

Voraussetzung: Task muss im Status `needs_input` sein.

---

## Fehlerbehandlung und Resilienz

### Webhook-Delivery (Paperclip-Seite)

`pm_tool_callback.py` implementiert automatische Retries:
- 3 Versuche mit exponentiellem Backoff (1s, 2s, 4s)
- Timeout pro Request: 10 Sekunden
- Bei Erschöpfung aller Retries: Error-Log, kein Task-Abbruch

### Celery-Task-Retries (PM-Tool-Seite)

`send_to_paperclip_task` implementiert:
- `max_retries=3` mit `default_retry_delay=30` Sekunden
- Duplikat-Prüfung: Kein zweiter Task für dasselbe Issue
- Fehler-Message in `AgentMessage` bei Verbindungsfehlern

### Empfohlene Erweiterungen

1. **Dead Letter Queue**: Fehlgeschlagene Webhooks in einer Queue speichern und manuell/periodisch wiederholen
2. **Idempotenz**: `external_task_id` als Idempotenz-Schlüssel verwenden — Paperclip ignoriert doppelte `external_id`-Werte
3. **Health-Check**: Periodischer Celery-Beat-Task, der `GET /health` auf Paperclip prüft und `AgentCompanyConfig.is_enabled` bei Ausfall deaktiviert

---

## Sicherheitshinweise

### HMAC-Webhook-Secret

- Mindestens 32 Zeichen, kryptographisch zufällig generiert
- Generierung: `python -c "import secrets; print(secrets.token_hex(32))"`
- Nicht in Versionskontrolle speichern — nur in `.env` oder Secret-Manager
- Rotation: Neues Secret in beiden Systemen gleichzeitig konfigurieren

### API-Key-Verwaltung

- Paperclip unterstützt mehrere API-Keys (kommasepariert in `API_KEYS`)
- Separaten Key pro Integration verwenden (PM-Tool bekommt eigenen Key)
- Bei Kompromittierung: Key aus `API_KEYS` entfernen, neuen in `AgentCompanyConfig` eintragen

### Netzwerk-Isolation

- Webhook-Endpoint (`/api/v1/agents/webhooks/event/`) ist `AllowAny` (keine Auth) — Schutz nur via HMAC
- Im Produktionsbetrieb: Firewall/Reverse-Proxy so konfigurieren, dass der Webhook-Endpoint nur von Paperclip's IP erreichbar ist
- Paperclip API-Endpoints sind durch `require_api_key` geschützt (Bearer-Token)

---

## Schritt-für-Schritt-Einrichtung

### 1. Paperclip aufsetzen

```bash
cd C:\Projekte\Agent-Agency
cp .env.example .env
# .env editieren: API_KEYS, WEBHOOK_SECRET, AI-Provider-Keys setzen
docker compose up -d
# Warten bis healthy: docker compose ps
```

### 2. PM-Tool konfigurieren

```bash
cd C:\Projekte\Pm-tool
# .env editieren: PM_TOOL_BASE_URL setzen
docker compose up -d
```

### 3. AgentCompanyConfig anlegen

Im PM-Tool Admin-Panel oder via Shell:

```python
# python manage.py shell
from apps.agents.models import AgentCompanyConfig
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.get(username="admin")

config = AgentCompanyConfig.objects.create(
    user=user,
    name="Paperclip Production",
    base_url="http://host.docker.internal:4108",  # oder Docker-Netzwerk-URL
    api_key="pk-pmtool-key-abc123",                # muss in Paperclip API_KEYS stehen
    webhook_secret="shared-hmac-secret-256bit",     # muss mit Paperclip WEBHOOK_SECRET übereinstimmen
    is_enabled=True,
    settings={"auto_delegate": False},
)
```

### 4. Verbindung testen

```bash
# Paperclip Health-Check
curl http://localhost:4108/health

# Agent-Profile synchronisieren (im PM-Tool)
python manage.py shell -c "
from apps.agents.models import AgentCompanyConfig
from apps.agents.services import AgentBridgeService
company = AgentCompanyConfig.objects.first()
with AgentBridgeService(company) as bridge:
    agents = bridge.sync_agent_profiles()
    print(f'{len(agents)} Agents gefunden')
"
```

### 5. Erste Aufgabe delegieren

Im PM-Tool Frontend:
1. Neues Issue erstellen (z.B. "Hello World API erstellen")
2. Auf "An AI-Agent delegieren" klicken
3. Task-Typ wählen (z.B. "software")
4. Instruktionen eingeben (z.B. "Verwende FastAPI und Python 3.11")
5. Absenden

Im Hintergrund:
- PM-Tool erstellt `AgentTask` und sendet an Paperclip `POST /api/v1/tasks/`
- Paperclip akzeptiert (`task.accepted` Webhook) → Orchestrator klassifiziert → Executor arbeitet → QA prüft
- Jede Statusänderung und jedes Ergebnis fließt via Webhook zurück
- SSE-Stream im Frontend zeigt Live-Updates

---

## Monitoring und Debugging

### Paperclip-seitig

```bash
# Task-Status prüfen
curl -H "Authorization: Bearer pk-pmtool-key-abc123" \
  http://localhost:4108/api/v1/tasks/<task-id>

# Task-Nachrichten anzeigen
curl -H "Authorization: Bearer pk-pmtool-key-abc123" \
  http://localhost:4108/api/v1/tasks/<task-id>/messages/

# Alle Tasks auflisten
curl -H "Authorization: Bearer pk-pmtool-key-abc123" \
  http://localhost:4108/api/v1/tasks/?status=in_progress

# Worker-Logs
docker compose logs -f worker
```

### PM-Tool-seitig

```bash
# Company-Status
curl -H "Authorization: Bearer <jwt-token>" \
  http://localhost:4107/api/v1/agents/company/status/

# Agent-Tasks auflisten
curl -H "Authorization: Bearer <jwt-token>" \
  http://localhost:4107/api/v1/agents/tasks/

# Backend-Logs (Webhooks)
docker compose logs -f backend | grep -i webhook

# Celery-Worker-Logs
docker compose logs -f celery_worker
```

### Häufige Fehler

| Symptom | Ursache | Lösung |
|---------|---------|--------|
| "Invalid signature" (401) | Webhook-Secret stimmt nicht überein | Secret in beiden `.env`-Dateien angleichen |
| "Task not found" im Webhook | `external_task_id` nicht in PM-Tool DB | Prüfen ob `AgentTask` korrekt erstellt wurde |
| Webhook kommt nicht an | Netzwerk-Isolation / falsche callback_url | `PM_TOOL_BASE_URL` und Docker-Netzwerk prüfen |
| "Keine aktive Agent-Company" | `AgentCompanyConfig.is_enabled = False` | Im Admin aktivieren |
| Task bleibt auf "pending" | Celery-Worker nicht gestartet | `docker compose logs worker` prüfen |
| SSE-Stream bricht ab | Redis nicht erreichbar | Redis-Verbindung in beiden Services prüfen |
