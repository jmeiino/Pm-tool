# PM-Tool Implementierungsplan — Orchestration Integration

## Status: Bereits vorhanden (kein Handlungsbedarf)

- [x] `AgentBridgeService` (httpx-Client) — `backend/apps/agents/services.py`
- [x] `AgentCompanyConfig`, `AgentTask`, `AgentMessage` Models — `backend/apps/agents/models.py`
- [x] `webhook_handler.py` mit HMAC-Verifizierung — `backend/apps/agents/webhook_handler.py`
- [x] SSE-Stream Endpoint — `backend/apps/agents/views.py`
- [x] Reply-Endpoint — `backend/apps/agents/views.py`
- [x] Event-Handler-Mapping — `backend/apps/agents/webhook_handler.py`
- [x] Agents-Seite Frontend — `frontend/src/app/agents/page.tsx`

---

## Phase 1: Backend — Automatische Delegation (Celery + Signals)

### 1.1 Celery-Task: `send_to_paperclip_task`
- **Datei:** `backend/apps/agents/tasks.py` (neu)
- Delegiert Issue asynchron an Paperclip
- max_retries=3, default_retry_delay=30
- Duplikat-Pruefung (kein zweiter Task fuer selbes Issue)
- Error-Messages in AgentMessage bei Fehler

### 1.2 Django Signal: `auto_delegate_to_paperclip`
- **Datei:** `backend/apps/agents/signals.py` (neu)
- post_save auf Issue
- Trigger bei Labels: `ai-agent`, `paperclip`, `auto-delegate`
- Prueft `AgentCompanyConfig.settings.auto_delegate`

### 1.3 Signal-Registrierung
- **Datei:** `backend/apps/agents/apps.py` (editieren)
- `ready()` Hook: `import apps.agents.signals`

---

## Phase 2: Frontend — Delegation UI + Echtzeit-Updates

### 2.1 `DelegateToAgentButton` Komponente
- **Datei:** `frontend/src/components/issues/DelegateToAgentButton.tsx` (neu)
- Button "An AI-Agent delegieren" auf Issue-Detail
- Dialog: Task-Typ, Prioritaet, Instruktionen
- Zeigt `AgentTaskStatusBadge` wenn bereits delegiert

### 2.2 `AgentTaskStatusBadge` Komponente
- **Datei:** `frontend/src/components/issues/AgentTaskStatusBadge.tsx` (neu)
- Farbcodierte Status-Anzeige (pending/assigned/in_progress/review/needs_input/completed/failed)

### 2.3 `useAgentTaskStream` Hook
- **Datei:** `frontend/src/hooks/useAgentTaskStream.ts` (neu)
- SSE EventSource auf `/api/v1/agents/tasks/{id}/stream/`
- Parst new_message, status_changed, deliverable Events

### 2.4 `AgentDeliverables` Komponente
- **Datei:** `frontend/src/components/issues/AgentDeliverables.tsx` (neu)
- Zeigt Code-Bloecke (Syntax-Highlighting) und Markdown-Ergebnisse

### 2.5 Integration in Issue-Detail-Seite
- **Datei:** `frontend/src/app/projekte/[id]/page.tsx` (editieren)
- DelegateToAgentButton einbinden
- AgentDeliverables bei abgeschlossenen Tasks anzeigen

---

## Phase 3: KPI-SDK Integration

### 3.1 KPI-Client erstellen
- **Datei:** `backend/apps/core/kpi_client.py` (neu)
- Leichtgewichtiger httpx-Client fuer POST /api/events
- Fire-and-forget (Fehler loggen, nicht blockieren)
- Config: KPI_API_URL, KPI_API_KEY aus settings

### 3.2 Django Middleware fuer automatische Events
- **Datei:** `backend/apps/core/kpi_middleware.py` (neu)
- Events: project.issue_created, project.issue_completed, integration.sync

### 3.3 .env Erweiterung
- KPI_API_URL, KPI_API_KEY

---

## Phase 4: Docker-Netzwerk fuer Oekosystem

### 4.1 docker-compose.override.yml erstellen
- Shared Network `inotec-ecosystem`
- Backend verbindet sich mit default + inotec-ecosystem
- PM_TOOL_BASE_URL Environment-Variable

### 4.2 .env Erweiterung
- PM_TOOL_BASE_URL
- PAPERCLIP_BASE_URL (fuer AgentCompanyConfig Defaults)

---

## Nicht in diesem Repo (andere Projekte)

- Paperclip Docker-Setup → C:\Projekte\Agent-Agency
- Agent-Agency Heartbeat-Adapter → C:\Projekte\Agent-Agency
- KPI-Tracking Stack → C:\Projekte\KPI-Tracking
- Grafana Dashboards → C:\Projekte\KPI-Tracking
