# Entwicklung

Anleitung fuer die lokale Entwicklungsumgebung, Code-Struktur und Tests.

---

## Lokale Entwicklung starten

```bash
# Alle Dienste starten
docker compose up --build

# Nur Backend neu bauen
docker compose up --build backend

# Logs anzeigen
docker compose logs -f backend
docker compose logs -f celery
```

### Datenbank-Migrationen

```bash
# Migrationen erstellen
docker compose exec backend python manage.py makemigrations

# Migrationen ausfuehren
docker compose exec backend python manage.py migrate
```

### Django-Shell

```bash
docker compose exec backend python manage.py shell
```

### Frontend-Entwicklung

Das Frontend laeuft mit Hot-Reload auf Port 3000:

```bash
# Node-Abhaengigkeiten manuell installieren (falls noetig)
docker compose exec frontend npm install

# Frontend-Logs
docker compose logs -f frontend
```

---

## Code-Struktur

### Backend

```
backend/
├── config/
│   ├── settings/
│   │   ├── base.py       # Gemeinsame Konfiguration
│   │   ├── dev.py        # DEBUG=True, CORS erlaubt
│   │   └── prod.py       # DEBUG=False, Sicherheitseinstellungen
│   ├── urls.py            # URL-Routing
│   ├── celery.py          # Celery + Beat-Konfiguration
│   └── wsgi.py
├── apps/
│   ├── core/              # TimeStampedModel, Pagination, Exceptions
│   ├── users/             # Custom User, Profile-Endpoints
│   ├── projects/          # Project, Sprint, Issue, Comment, Label
│   ├── todos/             # PersonalTodo, DailyPlan, WeeklyPlan
│   ├── integrations/      # IntegrationConfig, Sync-Services
│   │   ├── jira/          # JiraClient, JiraSyncService
│   │   ├── confluence/    # ConfluenceClient, ConfluenceSyncService
│   │   ├── git/           # GitHubClient, GitHubSyncService
│   │   ├── microsoft/     # GraphClient, MicrosoftSyncService
│   │   ├── views.py       # Integration-Config CRUD
│   │   └── import_views.py # Import-Wizard-Endpunkte
│   ├── ai/                # BaseAIClient, AIService, Prompts
│   ├── agents/            # AgentTask, AgentMessage, Webhooks
│   └── notifications/     # Notification, Deadline-Warnungen
├── tests/
│   ├── conftest.py        # Pytest-Fixtures
│   ├── factories.py       # Factory-Boy-Factories
│   └── test_*.py          # Testdateien
└── requirements/
    ├── base.txt           # Produktionsabhaengigkeiten
    └── dev.txt            # Entwicklungsabhaengigkeiten
```

### Frontend

```
frontend/src/
├── app/                   # Next.js App Router (Seiten)
│   ├── page.tsx           # Dashboard
│   ├── projekte/          # Projekte
│   ├── todos/             # Todos
│   ├── planung/           # Tages-/Wochenplan
│   ├── kalender/          # Kalender
│   ├── confluence/        # Confluence-Integration
│   ├── github/            # GitHub-Integration
│   ├── agents/            # Agent-System
│   ├── import/            # Import-Wizard
│   └── einstellungen/     # Einstellungen
├── components/
│   ├── layout/            # Sidebar, Header, Navigation
│   ├── ui/                # Button, Card, Badge, etc.
│   ├── projects/          # Projekt-spezifische Komponenten
│   ├── todos/             # Todo-Formulare
│   ├── issues/            # Issue-Tabelle, Detail-Panel
│   ├── integrations/      # Verbindungs-Dialoge
│   ├── agents/            # Agent-UI (Panel, OrgChart, Timeline)
│   └── import/            # Import-Wizard-Schritte
├── hooks/                 # React-Query-Hooks (Datenzugriff)
├── lib/
│   ├── api.ts             # Axios-Instanz mit Interceptors
│   ├── types.ts           # TypeScript-Interfaces
│   ├── schemas.ts         # Zod-Validierungsschemas
│   └── utils.ts           # Hilfsfunktionen, Konstanten
└── stores/                # Zustand-Stores
```

---

## Tests

### Backend-Tests ausfuehren

```bash
# Alle Tests
docker compose exec backend pytest

# Einzelne Testdatei
docker compose exec backend pytest tests/test_projects.py

# Verbose-Ausgabe
docker compose exec backend pytest -v

# Mit Coverage
docker compose exec backend pytest --cov=apps
```

### Test-Konfiguration

- **Framework:** pytest + pytest-django
- **Fixtures:** factory-boy (Factories fuer User, Project, Issue, Todo etc.)
- **Konfiguration:** `backend/pytest.ini`

### Vorhandene Tests

| Datei | Bereich |
|---|---|
| `test_projects.py` | Projekt-API (CRUD, Stats) |
| `test_todos.py` | Todo-API (CRUD, Filter) |
| `test_integrations.py` | Integrationskonfigurationen |
| `test_microsoft.py` | Microsoft OAuth, Kalender |
| `test_github.py` | GitHub-Sync, Repo-Analyse |
| `test_confluence.py` | Confluence-Sync, KI-Analyse |
| `test_calendar.py` | Kalender-Events |

### Neue Tests schreiben

```python
# tests/test_example.py
import pytest
from tests.factories import UserFactory, ProjectFactory

@pytest.mark.django_db
class TestProjectAPI:
    def test_create_project(self, api_client, user):
        api_client.force_authenticate(user=user)
        response = api_client.post('/api/v1/projects/', {
            'name': 'Neues Projekt',
            'key': 'NP',
        })
        assert response.status_code == 201
```

---

## API-Dokumentation

Die interaktive API-Dokumentation ist unter http://localhost:8000/api/docs/ verfuegbar (Swagger-UI, generiert durch drf-spectacular).

Das OpenAPI-Schema kann unter http://localhost:8000/api/schema/ heruntergeladen werden.

---

## Nuetzliche Befehle

```bash
# Container stoppen
docker compose down

# Container + Volumes loeschen (Datenbank zuruecksetzen)
docker compose down -v

# Einzelnen Service neustarten
docker compose restart backend

# In Container einloggen
docker compose exec backend bash
docker compose exec frontend sh

# Python-Abhaengigkeiten aktualisieren
docker compose exec backend pip install -r requirements/dev.txt

# Statische Dateien sammeln (fuer Produktion)
docker compose exec backend python manage.py collectstatic --noinput
```
