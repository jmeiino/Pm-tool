# Architekturuebersicht

PM-Tool ist eine Full-Stack-Anwendung mit klarer Trennung zwischen Frontend, Backend und externen Diensten.

---

## Systemdiagramm

```
                              +-----------+
                              |  Nginx    |  (nur Produktion)
                              +-----+-----+
                                    |
                        +-----------+-----------+
                        |                       |
                  +-----+-----+         +------+------+
                  |  Frontend  |         |   Backend   |
                  |  Next.js   |         |   Django    |
                  |  :3000     |         |   :8000     |
                  +------------+         +------+------+
                                                |
                              +-----------------+-----------------+
                              |                 |                 |
                        +-----+-----+    +------+------+   +-----+-----+
                        | PostgreSQL |    |    Redis    |   |   Celery   |
                        |   :5432    |    |    :6379    |   |  Worker +  |
                        +------------+    +-------------+   |   Beat     |
                                                            +-----------+

Externe Dienste:
  Jira ←→ Backend (bidirektional)
  Confluence → Backend (inbound)
  GitHub → Backend (inbound)
  Microsoft Graph → Backend (inbound, OAuth2)
  Agent-Microservice ←→ Backend (bidirektional, Webhooks)
  KI-Provider (Claude / Ollama / OpenRouter) → Backend
```

---

## Komponenten

### Frontend (Next.js 14)

| Aspekt | Technologie |
|---|---|
| Framework | Next.js 14 mit App Router |
| Sprache | TypeScript |
| Styling | Tailwind CSS 3.4 |
| State Management | TanStack React Query 5, Zustand |
| Formulare | React Hook Form + Zod |
| Drag & Drop | dnd-kit |
| UI-Bibliothek | Headless UI, Heroicons, eigene Basis-Komponenten |

**Verzeichnisstruktur:**

```
frontend/src/
├── app/          # Seiten (file-based routing)
├── components/   # React-Komponenten (layout, ui, features)
├── hooks/        # React-Query-Hooks (Datenabfrage)
├── lib/          # API-Client, Typen, Schemas, Utils
└── stores/       # Zustand-Stores
```

### Backend (Django 5.1)

| Aspekt | Technologie |
|---|---|
| Framework | Django 5.1 + Django REST Framework |
| Sprache | Python 3.12 |
| Auth | Session-basiert |
| API-Docs | drf-spectacular (Swagger-UI) |

**App-Struktur:**

```
backend/apps/
├── core/           # Basis: TimeStampedModel, Pagination, Exceptions
├── users/          # Erweitertes User-Modell
├── projects/       # Projekte, Sprints, Issues, Labels, Kommentare
├── todos/          # PersonalTodos, Tagesplaene, Wochenplaene
├── integrations/   # Config, Sync-Services, Import-Wizard
│   ├── jira/       # JiraClient, JiraSyncService
│   ├── confluence/  # ConfluenceClient, ConfluenceSyncService
│   ├── git/        # GitHubClient, GitHubSyncService
│   └── microsoft/  # GraphClient, OAuth2, MicrosoftSyncService
├── ai/             # Multi-Provider-Clients, AIService, Prompts, Caching
├── agents/         # Agent-Company-Integration, Delegation, Webhooks
└── notifications/  # Benachrichtigungen, Deadline-Warnungen
```

### Datenbank (PostgreSQL 16)

- Relationale Datenbank fuer alle persistenten Daten
- Migrationen via Django ORM
- JSONFields fuer flexible Daten (Credentials, Preferences, Deliverables)

### Redis 7

- Message Broker fuer Celery
- Cache-Backend fuer Django

### Celery

- **Worker:** Fuehrt asynchrone Tasks aus (Sync, KI-Analyse)
- **Beat:** Periodischer Scheduler (Polling-Intervalle)
- Retry-Strategie: 3 Versuche mit 60s Wartezeit

---

## Datenfluss

### Sync-Zyklus (z.B. Jira)

```
Celery Beat (alle 15 Min)
  → dispatch_integration_sync("jira")
    → poll_jira_updates(config_id)
      → JiraClient.get_projects() / get_issues()
        → JiraSyncService.sync_projects() / sync_issues()
          → Erstellt/Aktualisiert Project, Sprint, Issue in DB
            → Erstellt SyncLog mit Ergebnis
```

### KI-Anfrage

```
Frontend: POST /api/v1/ai/daily-plan/
  → AIView.daily_plan()
    → get_ai_client(user) → ClaudeClient / OllamaClient / OpenRouterClient
      → AIService.suggest_daily_plan(todos, events)
        → Prueft AIResult-Cache (24h TTL)
        → Falls kein Cache: KI-Provider API-Aufruf
          → Speichert Ergebnis in AIResult
            → Gibt JSON-Antwort zurueck
```

### Agent-Delegation

```
Frontend: POST /api/v1/agents/tasks/delegate/
  → AgentTaskViewSet.delegate()
    → Erstellt AgentTask (status=ASSIGNED)
      → AgentBridgeService.delegate_task()
        → HTTP POST an Agent-Microservice
          → Agent arbeitet, sendet Webhooks zurueck
            → webhook_handler verarbeitet Events
              → Aktualisiert AgentTask und erstellt AgentMessages
                → SSE-Stream benachrichtigt Frontend
```

---

## Authentifizierung

### Intern (Session-basiert)

- Django Session-Authentication
- Alle API-Aufrufe benoetigen einen authentifizierten Benutzer
- ViewSets filtern automatisch nach dem aktuellen Benutzer

### Extern (OAuth2 fuer Microsoft 365)

```
1. GET /integrations/microsoft/auth/
   → Generiert Authorization-URL via MSAL
   → Redirect zu Microsoft Login

2. Microsoft Callback → GET /integrations/microsoft/callback/
   → Empfaengt Authorization Code
   → Tauscht Code gegen Access Token
   → Speichert Token in IntegrationConfig.credentials
```
