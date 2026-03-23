# PM-Tool — Personal Project Manager

Ein persoenlicher Projektmanager mit KI-Unterstuetzung, der Jira, Confluence, GitHub und Microsoft 365 in einer einheitlichen Oberflaeche vereint. Plane deinen Tag mit Drag-and-Drop, lass dir von KI Vorschlaege machen und behalte alle Projekte im Blick. Unterstuetzt mehrere KI-Provider (Claude, Ollama, OpenRouter) — konfigurierbar direkt in der GUI.

---

## Inhaltsverzeichnis

- [Features](#features)
- [Tech-Stack](#tech-stack)
- [Architektur](#architektur)
- [Schnellstart](#schnellstart)
- [Umgebungsvariablen](#umgebungsvariablen)
- [API-Endpunkte](#api-endpunkte)
- [Datenmodell](#datenmodell)
- [Integrationen](#integrationen)
- [Hintergrund-Tasks (Celery)](#hintergrund-tasks-celery)
- [Frontend](#frontend)
- [Tests](#tests)
- [Produktion](#produktion)
- [Projektstruktur](#projektstruktur)

---

## Features

- **Projektmanagement** — Projekte, Sprints, Issues und Labels verwalten
- **Persoenliche Todos** — Aufgaben mit Prioritaet, Schaetzung und Quellenzuordnung
- **Tagesplanung** — Drag-and-Drop-Planung mit Zeitbloecken und Kapazitaetsanzeige
- **Wochenplanung** — 5-Tage-Uebersicht (Mo–Fr) fuer die Wochenplanung
- **KI-Unterstuetzung** — Tagesplan-Vorschlaege, Zusammenfassungen, Action-Item-Extraktion, Confluence- und Repository-Analyse
- **Multi-Provider KI** — Waehlbar zwischen Claude (Anthropic), Ollama (lokal) und OpenRouter (100+ Modelle)
- **GitHub-Repository-Analyse** — Repositories per KI analysieren: Tech-Stack, Staerken, Verbesserungen, naechste Schritte
- **Jira-Sync** — Bidirektionale Synchronisation von Projekten, Sprints und Issues
- **Confluence-Integration** — Seiten importieren und per KI analysieren (Zusammenfassung, Entscheidungen, Risiken)
- **GitHub-Tracking** — Commits, Pull Requests und deren Verknuepfung zu Issues
- **Microsoft 365** — Kalender-Events via OAuth2 synchronisieren
- **GUI-Einstellungen** — Alle Konfigurationen (Profil, KI-Provider, Integrationen) direkt in der Oberflaeche aenderbar
- **Benachrichtigungen** — Deadline-Warnungen, Sync-Fehler und KI-Vorschlaege
- **API-Dokumentation** — Automatisch generierte Swagger-UI

---

## Tech-Stack

| Komponente | Technologie |
|---|---|
| **Backend** | Django 5.1, Django REST Framework, Python 3.12 |
| **Frontend** | Next.js 14 (App Router), React 18, TypeScript |
| **Datenbank** | PostgreSQL 16 |
| **Message Broker** | Redis 7 |
| **Task Queue** | Celery 5.4 mit django-celery-beat |
| **KI** | Claude (Anthropic), Ollama (lokal), OpenRouter (Multi-Modell) |
| **Styling** | Tailwind CSS 3.4 |
| **State Management** | TanStack React Query 5, Zustand |
| **Formulare** | React Hook Form + Zod |
| **Drag & Drop** | dnd-kit |
| **Containerisierung** | Docker, Docker Compose |
| **Reverse Proxy** | Nginx (Produktion) |

---

## Architektur

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
```

**Externe Dienste:** Jira, Confluence, GitHub, Microsoft Graph API, Claude / Ollama / OpenRouter

---

## Schnellstart

### Voraussetzungen

- Docker und Docker Compose
- Git

### 1. Repository klonen

```bash
git clone <repository-url>
cd Pm-tool
```

### 2. Umgebungsvariablen konfigurieren

```bash
cp .env.example .env
```

Die `.env`-Datei enthaelt Standardwerte fuer die lokale Entwicklung. KI-Provider,
API-Keys und Integrationen koennen spaeter auch direkt in der GUI unter
**Einstellungen** konfiguriert werden.

### 3. Starten (Entwicklung)

```bash
docker compose up --build
```

Das startet alle Dienste:

| Dienst | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000/api/v1/ |
| API-Dokumentation | http://localhost:8000/api/docs/ |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

### 4. Admin-Benutzer anlegen

```bash
docker compose exec backend python manage.py createsuperuser
```

---

## Umgebungsvariablen

Alle Variablen werden in `.env` im Projektroot konfiguriert:

### Django

| Variable | Beschreibung | Standard |
|---|---|---|
| `DJANGO_SECRET_KEY` | Geheimer Schluessel fuer Django | `change-me-in-production` |
| `DJANGO_DEBUG` | Debug-Modus | `True` |
| `DJANGO_ALLOWED_HOSTS` | Erlaubte Hosts (kommagetrennt) | `localhost,127.0.0.1` |

### Datenbank (PostgreSQL)

| Variable | Beschreibung | Standard |
|---|---|---|
| `POSTGRES_DB` | Datenbankname | `pmtool` |
| `POSTGRES_USER` | Datenbankbenutzer | `pmtool` |
| `POSTGRES_PASSWORD` | Datenbankpasswort | `pmtool` |
| `POSTGRES_HOST` | Datenbank-Host | `db` |
| `POSTGRES_PORT` | Datenbank-Port | `5432` |

### Redis / Celery

| Variable | Beschreibung | Standard |
|---|---|---|
| `CELERY_BROKER_URL` | Redis-URL fuer Celery | `redis://redis:6379/0` |

### Integrationen

| Variable | Beschreibung |
|---|---|
| `ATLASSIAN_URL` | Atlassian-Cloud-URL (z.B. `https://firma.atlassian.net`) |
| `ATLASSIAN_EMAIL` | Atlassian-Account-E-Mail |
| `ATLASSIAN_API_TOKEN` | Atlassian-API-Token |
| `MS_CLIENT_ID` | Microsoft Azure App Client-ID |
| `MS_CLIENT_SECRET` | Microsoft Azure App Client-Secret |
| `MS_TENANT_ID` | Microsoft Azure Tenant-ID |
| `MS_REDIRECT_URI` | OAuth2-Redirect-URI |
| `GITHUB_TOKEN` | GitHub Personal Access Token |

### KI-Provider

> **Hinweis:** Diese Variablen dienen als Fallback. Alle KI-Einstellungen koennen
> auch direkt in der GUI unter **Einstellungen > KI-Provider** konfiguriert werden.
> GUI-Einstellungen haben Vorrang vor `.env`-Werten.

| Variable | Beschreibung | Standard |
|---|---|---|
| `AI_PROVIDER` | Aktiver Provider: `claude`, `ollama` oder `openrouter` | `claude` |
| `ANTHROPIC_API_KEY` | Anthropic Claude API-Key | |
| `ANTHROPIC_MODEL` | Claude-Modell | `claude-sonnet-4-20250514` |
| `OLLAMA_BASE_URL` | Ollama-Server-URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama-Modell | `llama3.1` |
| `OPENROUTER_API_KEY` | OpenRouter API-Key | |
| `OPENROUTER_MODEL` | OpenRouter-Modell | `anthropic/claude-sonnet-4` |

### Frontend

| Variable | Beschreibung | Standard |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Backend-API-URL | `http://localhost:8000/api/v1` |

---

## API-Endpunkte

Basis-URL: `/api/v1/`

### Projects

| Methode | Pfad | Beschreibung |
|---|---|---|
| `GET/POST` | `/projects/` | Projekte auflisten / erstellen |
| `GET/PUT/PATCH/DELETE` | `/projects/{id}/` | Projekt-CRUD |
| `GET/POST` | `/sprints/` | Sprints auflisten / erstellen |
| `GET/PUT/PATCH/DELETE` | `/sprints/{id}/` | Sprint-CRUD |
| `GET/POST` | `/issues/` | Issues auflisten / erstellen |
| `GET/PUT/PATCH/DELETE` | `/issues/{id}/` | Issue-CRUD |
| `GET/POST` | `/issues/{id}/comments/` | Kommentare zu einem Issue |
| `GET/POST` | `/labels/` | Labels auflisten / erstellen |

### Todos

| Methode | Pfad | Beschreibung |
|---|---|---|
| `GET/POST` | `/todos/` | Persoenliche Todos auflisten / erstellen |
| `GET/PUT/PATCH/DELETE` | `/todos/{id}/` | Todo-CRUD |
| `GET/POST` | `/daily-plans/` | Tagesplaene auflisten / erstellen |
| `GET/PUT/PATCH/DELETE` | `/daily-plans/{id}/` | Tagesplan-CRUD |
| `GET/POST` | `/weekly-plans/` | Wochenplaene auflisten / erstellen |
| `GET/PUT/PATCH/DELETE` | `/weekly-plans/{id}/` | Wochenplan-CRUD |

### Integrations

| Methode | Pfad | Beschreibung |
|---|---|---|
| `GET/POST` | `/integrations/configs/` | Integrationskonfigurationen |
| `GET` | `/integrations/sync-logs/` | Sync-Protokolle |
| `GET/POST` | `/integrations/confluence-pages/` | Confluence-Seiten |
| `GET/POST` | `/integrations/calendar-events/` | Kalender-Events |
| `GET/POST` | `/integrations/git-activities/` | Git-Aktivitaeten |
| `GET/POST` | `/integrations/repo-analyses/` | Repository-Analysen |
| `POST` | `/integrations/repo-analyses/{id}/analyze/` | KI-Analyse eines Repos starten |
| `POST` | `/integrations/repo-analyses/{id}/create-todos/` | Todos aus Repo-Analyse erstellen |
| `GET` | `/integrations/microsoft/auth/` | Microsoft OAuth2 starten |
| `GET` | `/integrations/microsoft/callback/` | Microsoft OAuth2 Callback |

### AI

| Methode | Pfad | Beschreibung |
|---|---|---|
| `GET/PATCH` | `/ai/ai/provider/` | KI-Provider lesen / aendern |
| `POST` | `/ai/ai/prioritize/` | Aufgaben priorisieren |
| `POST` | `/ai/ai/summarize/` | Inhalte zusammenfassen |
| `POST` | `/ai/ai/extract-actions/` | Action-Items extrahieren |
| `POST` | `/ai/ai/daily-plan/` | Tagesplan-Vorschlag generieren |

### Users

| Methode | Pfad | Beschreibung |
|---|---|---|
| `GET/PATCH` | `/users/me/` | Eigenes Profil lesen / aktualisieren |
| `GET/PUT/PATCH` | `/users/{id}/` | Benutzer-CRUD |

### Notifications

| Methode | Pfad | Beschreibung |
|---|---|---|
| `GET/POST` | `/notifications/` | Benachrichtigungen auflisten / erstellen |
| `GET/PUT/PATCH/DELETE` | `/notifications/{id}/` | Benachrichtigung-CRUD |

### Dokumentation

| Pfad | Beschreibung |
|---|---|
| `/api/docs/` | Swagger-UI (interaktive API-Dokumentation) |
| `/api/schema/` | OpenAPI-Schema (JSON) |

---

## Datenmodell

### Uebersicht

```
User
 ├── Project ──── Sprint
 │       └── Issue ──── Comment
 │             │
 ├── PersonalTodo ◄── (linked_issue)
 │       │
 ├── DailyPlan ──── DailyPlanItem ──► PersonalTodo
 │       │
 ├── WeeklyPlan ──► DailyPlan (M2M)
 │
 ├── IntegrationConfig ──── SyncLog
 │
 ├── CalendarEvent
 ├── Notification
 │
 ConfluencePage (standalone)
 GitActivity ──► Project, Issue
 GitRepoAnalysis (standalone, KI-analysiert)
 AIResult (Cache)
 Label ◄──► Issue (M2M)
```

### Wichtige Modelle

| Modell | App | Beschreibung |
|---|---|---|
| `User` | users | Erweitertes Django-User-Modell mit Zeitzone und Kapazitaet |
| `Project` | projects | Projekt mit optionaler Jira-Verknuepfung |
| `Sprint` | projects | Sprint innerhalb eines Projekts |
| `Issue` | projects | Issue/Aufgabe mit Typ, Prioritaet und Jira-Sync |
| `Comment` | projects | Kommentar zu einem Issue |
| `Label` | projects | Farbiges Label fuer Issues |
| `PersonalTodo` | todos | Persoenliche Aufgabe mit Quelle und KI-Confidence |
| `DailyPlan` | todos | Tagesplan mit KI-Zusammenfassung |
| `DailyPlanItem` | todos | Zeitblock im Tagesplan |
| `WeeklyPlan` | todos | Wochenplan (Sammlung von Tagesplaenen) |
| `IntegrationConfig` | integrations | Konfiguration einer externen Integration |
| `SyncLog` | integrations | Protokoll eines Sync-Vorgangs |
| `ConfluencePage` | integrations | Importierte Confluence-Seite mit KI-Analyse |
| `CalendarEvent` | integrations | Synchronisiertes Kalender-Event |
| `GitActivity` | integrations | GitHub-Commit oder Pull Request |
| `GitRepoAnalysis` | integrations | KI-analysiertes GitHub-Repository |
| `AIResult` | ai | Gecachtes KI-Ergebnis |
| `Notification` | notifications | Benutzer-Benachrichtigung |

---

## Integrationen

### Jira (Bidirektional)

- **Sync-Richtung:** Inbound + Outbound
- **Was wird synchronisiert:** Projekte, Sprints, Issues, Kommentare
- **Konflikterkennung:** Vergleich von `jira_updated_at` Timestamps
- **Client:** `JiraClient` (REST API via `atlassian-python-api`)
- **Service:** `JiraSyncService` mit `sync_projects()`, `sync_issues()`, `detect_conflicts()`

### Confluence (Inbound + KI-Analyse)

- **Sync-Richtung:** Inbound
- **Was wird synchronisiert:** Seiten (Titel, Inhalt)
- **KI-Features:** Zusammenfassung, Action-Items, Entscheidungen, Risiken
- **Client:** `ConfluenceClient` (REST API via `atlassian-python-api`)
- **Service:** `ConfluenceSyncService` mit `sync_pages()`, `sync_inbound()`

### GitHub (Inbound + Repository-Analyse)

- **Sync-Richtung:** Inbound
- **Was wird synchronisiert:** Commits, Pull Requests
- **Verknuepfung:** Automatische Zuordnung zu Issues anhand von Commit-Messages
- **Repository-Analyse:** Repos per KI analysieren (Tech-Stack, Staerken, Verbesserungen, Action-Items)
- **Client:** `GitHubClient` (REST API via `httpx`) mit `get_repo()`, `get_readme()`, `get_languages()`, `get_contributors()`
- **Service:** `GitHubSyncService` mit `sync_commits()`, `sync_pull_requests()`

### Microsoft 365 (Inbound, OAuth2)

- **Sync-Richtung:** Inbound
- **Was wird synchronisiert:** Kalender-Events
- **Authentifizierung:** OAuth2 via MSAL (Microsoft Authentication Library)
- **Client:** `GraphClient` (Microsoft Graph API)
- **Service:** `MicrosoftSyncService` mit `sync_calendar()`

### KI-Provider (Multi-Provider)

Alle KI-Funktionen laufen ueber eine einheitliche Schnittstelle (`BaseAIClient`).
Der aktive Provider kann in der GUI unter **Einstellungen > KI-Provider** gewaehlt werden.

| Provider | Beschreibung | Konfiguration |
|---|---|---|
| **Claude (Anthropic)** | Leistungsstarke Cloud-KI | API-Key + Modellauswahl |
| **Ollama (Lokal)** | Laeuft auf eigenem Rechner, keine Cloud | Server-URL + Modellname |
| **OpenRouter** | Zugang zu 100+ Modellen ueber eine API | API-Key + Modellname |

- **Funktionen:**
  - `prioritize_todos()` — Todos nach Wichtigkeit sortieren
  - `summarize_content()` — Texte zusammenfassen
  - `extract_action_items()` — Action-Items aus Text extrahieren
  - `suggest_daily_plan()` — KI-gestuetzten Tagesplan erstellen
  - `analyze_confluence_page()` — Confluence-Seite analysieren
  - `analyze_github_repo()` — GitHub-Repository analysieren
- **Client-Architektur:** `BaseAIClient` → `ClaudeClient` / `OllamaClient` / `OpenRouterClient`
- **Factory:** `get_ai_client(user)` waehlt Provider aus User-Preferences (Fallback: `.env`)
- **Caching:** Ergebnisse werden in `AIResult` gespeichert (24h TTL)

---

## Hintergrund-Tasks (Celery)

### Periodische Tasks (Celery Beat)

| Task | Intervall | Beschreibung |
|---|---|---|
| `poll_all_jira_integrations` | alle 15 Min. | Jira-Projekte und Issues synchronisieren |
| `dispatch_integration_sync("jira")` | alle 15 Min. | Jira-Sync dispatchen |
| `dispatch_integration_sync("confluence")` | alle 30 Min. | Confluence-Seiten synchronisieren |
| `dispatch_integration_sync("github")` | alle 10 Min. | GitHub-Aktivitaeten synchronisieren |
| `dispatch_integration_sync("microsoft_calendar")` | alle 15 Min. | Kalender-Events synchronisieren |
| `check_deadline_warnings` | jede Stunde | Deadline-Warnungen als Benachrichtigungen erstellen |

### Asynchrone Tasks

| Task | Beschreibung |
|---|---|
| `poll_jira_updates` | Jira fuer eine Integration synchronisieren |
| `poll_confluence_updates` | Confluence fuer eine Integration synchronisieren |
| `poll_github_updates` | GitHub fuer eine Integration synchronisieren |
| `poll_microsoft_calendar` | Kalender fuer eine Integration synchronisieren |
| `analyze_confluence_page_task` | Einzelne Confluence-Seite per KI analysieren |
| `async_prioritize_todos` | Todos per KI priorisieren |
| `async_summarize_content` | Inhalt per KI zusammenfassen |
| `async_extract_action_items` | Action-Items per KI extrahieren |
| `async_suggest_daily_plan` | Tagesplan per KI vorschlagen |
| `async_analyze_confluence_page` | Confluence-Seite per KI analysieren |
| `analyze_github_repo_task` | GitHub-Repository abrufen und per KI analysieren |

Alle Tasks haben `max_retries=3` und `default_retry_delay=60s`.

---

## Frontend

### Seiten

| Route | Beschreibung |
|---|---|
| `/` | Dashboard — Statistiken, offene Aufgaben, naechste Events |
| `/projekte` | Projekte — Grid-Ansicht mit Statusfilter |
| `/projekte/[id]` | Projektdetail — Tabs: Uebersicht, Issues, Sprints |
| `/todos` | Aufgaben — Filterbare Liste aller persoenlichen Todos |
| `/planung/tagesplan` | Tagesplan — Drag-and-Drop-Planung mit KI-Vorschlaegen |
| `/planung/wochenplan` | Wochenplan — 5-Tage-Uebersicht (Mo–Fr) |
| `/kalender` | Kalender — Wochen- und Monatsansicht |
| `/confluence` | Confluence — Seitensuche und KI-Analyse |
| `/confluence/[id]` | Confluence-Detail — Einzelne Seite mit Analyse |
| `/github` | GitHub — Commits und PRs nach Projekt/Typ gefiltert |
| `/github/repos` | Repository-Analyse — Repos hinzufuegen und per KI analysieren |
| `/github/repos/[id]` | Repository-Detail — Sprachen, KI-Analyse, Action-Items |
| `/einstellungen` | Einstellungen — Profil, KI-Provider und Integrationen konfigurieren |

### Technologie-Details

- **Routing:** Next.js 14 App Router
- **Datenabfrage:** TanStack React Query mit 60s Stale-Time
- **Formulare:** React Hook Form + Zod-Validierung
- **Drag & Drop:** dnd-kit fuer Tagesplan-Sortierung
- **UI-Komponenten:** Headless UI, Heroicons, eigene Basiskomponenten (Button, Card, Badge, Pagination, Skeleton, EmptyState)
- **Sprache:** Deutsch (alle Labels und Datumsformate)

---

## Tests

### Backend-Tests ausfuehren

```bash
docker compose exec backend pytest
```

### Test-Konfiguration

- Framework: pytest + pytest-django
- Fixtures: factory-boy (User, Project, etc.)
- Config: `backend/pytest.ini`

### Vorhandene Tests

- `test_projects.py` — Projekt-API
- `test_todos.py` — Todo-API
- `test_integrations.py` — Integrationskonfigurationen
- `test_microsoft.py` — Microsoft-Sync
- `test_github.py` — GitHub-Sync
- `test_confluence.py` — Confluence-Sync
- `test_calendar.py` — Kalender-Events

---

## Produktion

### Starten

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

### Unterschiede zur Entwicklung

| Aspekt | Entwicklung | Produktion |
|---|---|---|
| **WSGI-Server** | Django runserver | Gunicorn (4 Workers) |
| **Reverse Proxy** | keiner | Nginx (Port 80/443) |
| **Static Files** | Django liefert aus | Nginx via Volume |
| **Debug** | aktiviert | deaktiviert |
| **Settings** | `config.settings.dev` | `config.settings.prod` |
| **Healthchecks** | nur DB/Redis | alle Dienste |
| **Restart Policy** | keine | `unless-stopped` |
| **Celery Concurrency** | Standard | 2 Worker |

### Nginx-Konfiguration

Die Nginx-Konfiguration liegt unter `nginx/nginx.conf` und routet:
- `/api/` und `/admin/` an das Backend
- `/static/` an das Static-Files-Volume
- Alles andere an das Frontend

---

## Projektstruktur

```
Pm-tool/
├── .env.example                    # Umgebungsvariablen-Vorlage
├── docker-compose.yml              # Entwicklungs-Setup
├── docker-compose.prod.yml         # Produktions-Setup
├── nginx/
│   └── nginx.conf                  # Nginx-Konfiguration
│
├── backend/
│   ├── Dockerfile
│   ├── manage.py
│   ├── pytest.ini
│   ├── requirements/
│   │   ├── base.txt                # Produktionsabhaengigkeiten
│   │   └── dev.txt                 # Entwicklungsabhaengigkeiten
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py             # Gemeinsame Einstellungen
│   │   │   ├── dev.py              # Entwicklung
│   │   │   └── prod.py             # Produktion
│   │   ├── urls.py                 # Haupt-URL-Konfiguration
│   │   ├── celery.py               # Celery-Konfiguration
│   │   └── wsgi.py
│   ├── apps/
│   │   ├── core/                   # Basis: TimeStampedModel, Exceptions, Pagination
│   │   ├── users/                  # Benutzer-Verwaltung
│   │   ├── projects/               # Projekte, Sprints, Issues, Labels, Kommentare
│   │   ├── todos/                  # Todos, Tagesplaene, Wochenplaene
│   │   ├── integrations/           # Externe Integrationen
│   │   │   ├── jira/               # Client, Sync-Service, Tasks
│   │   │   ├── confluence/         # Client, Sync-Service, Tasks
│   │   │   ├── git/                # GitHub-Client, Sync-Service, Tasks
│   │   │   └── microsoft/          # Graph-Client, Sync-Service, Tasks, OAuth2
│   │   ├── ai/                     # Multi-Provider-Client, Services, Prompts, Tasks
│   │   └── notifications/          # Benachrichtigungen, Deadline-Warnungen
│   └── tests/
│       ├── conftest.py             # Pytest-Fixtures
│       ├── factories.py            # Factory-Boy-Factories
│       └── test_*.py               # Testdateien
│
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── next.config.js
    ├── tailwind.config.js
    └── src/
        ├── app/                    # Next.js App Router (Seiten)
        ├── components/             # React-Komponenten
        │   ├── layout/             # Sidebar, Header
        │   ├── ui/                 # Basis-UI (Button, Card, Badge, ...)
        │   ├── projects/           # Projekt-Dialoge
        │   ├── todos/              # Todo-Dialoge
        │   ├── issues/             # Issue-Tabelle, Detail-Panel
        │   └── integrations/       # Verbindungs-Dialoge
        ├── hooks/                  # React-Query-Hooks
        ├── lib/                    # API-Client, Typen, Schemas, Utils
        └── stores/                 # Zustand-Store
```
