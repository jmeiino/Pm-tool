# PM-Tool Session-Uebergabe

**Datum:** 2026-03-31
**Branch:** `claude/personal-project-manager-MSf4g`
**Projekt:** `C:\Projekte\Pm-tool`

---

## Aktueller Zustand

### Uncommitted Changes (MUESSEN zuerst committet werden)

4 geaenderte Dateien + 1 neue Migration:

| Datei | Aenderung |
|-------|-----------|
| `backend/apps/agents/models.py` | Neue Roles hinzugefuegt: `orchestrator`, `coder`, `writer`, `researcher` |
| `backend/apps/agents/services.py` | `sync_agent_profiles()` persistiert jetzt Agents in DB (vorher nur JSON-Return) |
| `backend/apps/agents/signals.py` | Signal von `post_save` auf `m2m_changed` umgestellt (Labels sind M2M, werden erst nach `create()` gesetzt) |
| `docker-compose.override.yml` | DB-Alias `pm-db` + `POSTGRES_HOST=pm-db` fuer alle Services (DNS-Konflikt-Fix) |
| `backend/apps/agents/migrations/0002_add_agent_roles.py` | Migration fuer neue Role-Choices (UNTRACKED) |

```bash
# Commit erstellen:
git add backend/apps/agents/models.py backend/apps/agents/services.py backend/apps/agents/signals.py docker-compose.override.yml backend/apps/agents/migrations/0002_add_agent_roles.py
git commit -m "fix: DNS-Konflikt pm-db Alias, Agent-Roles erweitern, sync_agent_profiles persistieren, Signal auf m2m_changed"
```

### Datenbank-Zustand (im Docker-Volume)

- Migration `0002_add_agent_roles` ist bereits applied
- **AgentCompanyConfig** existiert (id=1): `INOTEC Agent-Agency`, `base_url=http://agent-agency-api-1:8000`, `auto_delegate=True`
- **6 AgentProfiles** synchronisiert: Orchestrator, Coder, Writer, Researcher, QA Reviewer, Test-Agent
- **1 AgentTask** delegiert: `pm-FTEST-2-2746dae5` (Status: `assigned`, Typ: `research`)
- **Labels** angelegt: `ai-agent` (id=1), `auto-delegate` (id=2)

### Docker-Container (beim Session-Ende gestoppt)

```
PM-Tool      → docker compose up -d                    (Port: Backend 4107, Frontend 3115, DB 5409)
Agent-Agency → cd /c/Projekte/agent-agency && docker compose up -d  (Port: API 4108, Nginx 80/443)
Paperclip    → cd /c/Projekte/paperclip && docker compose up -d     (Port: App 3116, DB 5412)
```

Shared Network: `inotec-ecosystem` (existiert bereits, muss nicht neu erstellt werden)

### Bekannter DB-Passwort-Bug

Beim ersten Start nach Neustart kann der Backend-Container die DB nicht erreichen (`password authentication failed for user "pmtool"`). Das Postgres-Volume wurde mit einem anderen Passwort initialisiert.

**Workaround:**
```bash
docker compose up -d
# Warten bis db healthy ist, dann:
docker compose exec db sh -c "psql -U pmtool -d pmtool -c \"ALTER USER pmtool WITH PASSWORD 'pmtool';\""
docker compose restart backend celery celery-beat
```

---

## Naechste Schritte (1-4)

### Schritt 1: ALLOWED_HOSTS erweitern

**Problem:** Backend blockt Requests mit Docker-Hostnamen. Log-Fehler:
```
django.core.exceptions.DisallowedHost: Invalid HTTP_HOST header: 'pm-tool-backend-1:8000'
```

Webhooks von Agent-Agency an `http://pm-backend:8000/api/v1/agents/webhooks/event/` werden abgelehnt.

**Loesung:** In `.env` die ALLOWED_HOSTS erweitern:
```env
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,backend,pm-backend,pm-tool-backend-1
```

**Datei:** `.env` Zeile 4
**Verifizierung:** `curl -s http://localhost:4107/api/v1/` sollte JSON zurueckgeben (nicht 400).

---

### Schritt 2: KPI-Tracking anbinden

**Problem:** KPI-Stack laeuft im Ecosystem (`kpi-collection-api` auf `192.168.32.6`), aber PM-Tool sendet keine Events.

**Dateien:**
- `backend/apps/core/kpi_client.py` — Fire-and-forget HTTP Client (existiert bereits)
- `backend/apps/core/kpi_middleware.py` — Django Middleware fuer automatische Mutation-Events (existiert bereits)
- `backend/config/settings/base.py:218-219` — `KPI_API_URL` und `KPI_API_KEY` lesen aus `.env`

**Loesung:** In `.env` ergaenzen:
```env
KPI_API_URL=http://kpi-collection-api:4109
KPI_API_KEY=<api-key-aus-kpi-tracking-projekt>
```

**Verifizierung:**
```bash
# Im Backend-Container:
docker compose exec backend python manage.py shell -c "
from apps.core.kpi_client import track_event
track_event('test.ping', {'source': 'pm-tool'})
print('Event gesendet')
"
```

Dann im KPI-Grafana pruefen: `http://localhost:3000` (Grafana aus KPI-Stack).

---

### Schritt 3: Jira/Confluence/Microsoft verbinden (HITL)

**Status:** Atlassian-Credentials sind bereits in `.env` vorhanden:
```env
ATLASSIAN_URL=https://inotec-licht.atlassian.net
ATLASSIAN_EMAIL=jonas.meisterjahn@inotec-licht.de
ATLASSIAN_API_TOKEN=ATATT3x...  (gesetzt)
```

**Noch offen — Jira-Sync testen:**
```bash
# Projekte aus Jira laden:
docker compose exec backend python manage.py shell -c "
from apps.integrations.atlassian import JiraClient
client = JiraClient()
projects = client.get_projects()
print(f'{len(projects)} Jira-Projekte gefunden')
for p in projects[:5]: print(f'  {p[\"key\"]}: {p[\"name\"]}')
"
```

**Noch offen — Microsoft 365:**
Braucht Azure App Registration. In `.env` muessen gesetzt werden:
```env
MS_CLIENT_ID=<azure-app-client-id>
MS_CLIENT_SECRET=<azure-app-client-secret>
MS_TENANT_ID=<azure-tenant-id>
```
Redirect URI ist konfiguriert: `http://localhost:4107/api/v1/integrations/microsoft/callback/`

**Confluence:** Nutzt dieselben Atlassian-Credentials wie Jira, sollte funktionieren.

**MCP-Tools verfuegbar:** Es gibt Atlassian MCP-Tools (`mcp__claude_ai_Atlassian__*`) die direkt Jira/Confluence abfragen koennen — nuetzlich zum Testen.

---

### Schritt 4: Production Hardening

**4a) Secrets-Management**
- `.env` enthaelt Klartext-API-Keys und Tokens
- Fuer Produktion: Docker Secrets oder Vault einsetzen
- Mindestens: `.env` niemals committen (ist in `.gitignore`)

**4b) HTTPS/SSL**
- Agent-Agency Nginx hat bereits SSL-Konfiguration (Port 443)
- PM-Tool hat keinen Reverse-Proxy — `backend/config/settings/prod.py` hat `SECURE_PROXY_SSL_HEADER` vorbereitet
- Fuer Produktion: Nginx oder Traefik als Reverse-Proxy vor PM-Tool stellen

**4c) Backup-Strategie**
```bash
# PostgreSQL Backup (manuell):
docker compose exec db pg_dump -U pmtool pmtool > backup_$(date +%Y%m%d).sql

# Automatisch via Celery-Beat:
# Neuen PeriodicTask anlegen der taeglich pg_dump ausfuehrt
```

**4d) Monitoring**
- KPI-Middleware tracked bereits alle POST/PUT/PATCH Requests
- Celery Flower fuer Worker-Monitoring: `pip install flower` + Port-Mapping
- Django Health-Check Endpoint existiert nicht — sollte angelegt werden (`/api/v1/health/`)

---

## Architektur-Ueberblick

```
                    inotec-ecosystem (Docker Network)
    ┌─────────────────────────────────────────────────────────┐
    │                                                         │
    │  PM-Tool (pm-backend:8000)                              │
    │    ├── Django Backend + DRF                              │
    │    ├── Celery Worker + Beat                              │
    │    ├── Next.js Frontend (:3115)                          │
    │    └── PostgreSQL (pm-db:5432)                           │
    │           │                                              │
    │           │  AgentBridgeService (httpx)                  │
    │           ▼                                              │
    │  Agent-Agency (agent-agency-api-1:8000)                  │
    │    ├── FastAPI + Uvicorn                                 │
    │    ├── 6 AI-Agents (Orchestrator, Coder, Writer, ...)   │
    │    └── Webhooks → pm-backend:8000/api/v1/agents/webhooks│
    │           │                                              │
    │           │  Paperclip-Client                             │
    │           ▼                                              │
    │  Paperclip (paperclip-app:3100)                          │
    │    └── Code-Execution, Sandbox                           │
    │                                                         │
    │  KPI-Tracking                                            │
    │    ├── Collection-API (:4109)                             │
    │    ├── InfluxDB                                           │
    │    └── Grafana (:3000)                                    │
    └─────────────────────────────────────────────────────────┘
```

## Wichtige Dateien

| Datei | Zweck |
|-------|-------|
| `docker-compose.yml` | Haupt-Container-Definition |
| `docker-compose.override.yml` | Ecosystem-Netzwerk + DNS-Fix |
| `.env` | Alle Credentials und Config |
| `backend/apps/agents/services.py` | AgentBridgeService — HTTP-Client zu Agent-Agency |
| `backend/apps/agents/signals.py` | Auto-Delegation bei Label-Zuweisung |
| `backend/apps/agents/tasks.py` | Celery-Task fuer async Delegation |
| `backend/apps/agents/webhook_handler.py` | Webhook-Empfang von Agent-Agency |
| `backend/apps/core/kpi_client.py` | KPI-Event-Client |
| `backend/apps/core/kpi_middleware.py` | Automatisches KPI-Tracking |
| `orchestration-plan/MASTER-PLAN.md` | Gesamtarchitektur des INOTEC Ecosystems |

## Quick-Start fuer naechste Session

```bash
cd C:\Projekte\Pm-tool

# 1. Alle Services starten
docker compose up -d
cd /c/Projekte/agent-agency && docker compose up -d
cd /c/Projekte/paperclip && docker compose up -d

# 2. DB-Passwort-Fix falls noetig (siehe "Bekannter DB-Passwort-Bug")

# 3. Verifizieren
docker compose ps -a
curl -s http://localhost:4107/api/v1/  # PM-Tool Backend
curl -s http://localhost:4108/health    # Agent-Agency
curl -s http://localhost:3115           # PM-Tool Frontend

# 4. Dann Schritte 1-4 oben abarbeiten
```
