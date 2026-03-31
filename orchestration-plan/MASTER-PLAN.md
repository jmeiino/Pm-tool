# Gesamtarchitektur --- INOTEC AI-Oekosystem

## Vision

Paperclip als "Company OS" orchestriert AI-Agenten (Agent-Agency), gesteuert durch Menschen (PM-Tool), ueberwacht durch Metriken (KPI-Tracking). Zusammen bilden diese vier Systeme ein vollstaendig integriertes Oekosystem, in dem menschliche Entscheidungen nahtlos in AI-gesteuerte Ausfuehrung uebergehen und saemtliche Ergebnisse messbar zurueckfliessen.

---

## Architektur-Diagramm

```
                        INOTEC AI-Oekosystem
  =========================================================

  Mensch --> PM-Tool --> Paperclip --> Agent-Agency --> Paperclip --> PM-Tool
                            |                              |
                            v                              v
                       KPI-Tracking <---------------------+
                            |
                            v
                     Grafana Dashboards


  Detaillierter Datenfluss:

  +----------+     Webhook      +------------+    HTTP-Adapter    +---------------+
  |          | ---------------> |            | -----------------> |               |
  | PM-Tool  |                  | Paperclip  |                    | Agent-Agency  |
  |          | <--------------- |            | <----------------- |               |
  +----------+     Webhook      +------------+    PATCH/Callback  +---------------+
       |                |                              |
       |                |                              |
       v                v                              v
  +-----------------------------------------------------------+
  |                    KPI-Tracking                            |
  |              (InfluxDB + Grafana)                          |
  +-----------------------------------------------------------+
```

---

## Die 4 Systeme

### 1. PM-Tool (Human Interface)

- **Technologie:** Django/Next.js
- **Ports:** Frontend 3000, Backend 8000
- **Rolle:** Menschen erstellen Aufgaben, verfolgen den Fortschritt und sehen Ergebnisse. Das PM-Tool ist die primaere Schnittstelle fuer Projektmanager, Teamleiter und Stakeholder.
- **Integration:**
  - Webhook-Sender: Erstellt Issues in Paperclip via HTTP-Webhook
  - Webhook-Empfaenger: Empfaengt Status-Updates von Paperclip (Task abgeschlossen, fehlgeschlagen, etc.)
  - KPI-SDK: Sendet Events an KPI-Tracking (Task erstellt, User-Aktivitaet, etc.)

### 2. Paperclip (Company OS)

- **Technologie:** Node.js/React
- **Port:** 3100
- **Rolle:** Organisationsstruktur (Org-Chart), Budgetverwaltung, Governance-Regeln und Task-Zuweisung. Paperclip entscheidet basierend auf Rollen, verfuegbarem Budget und Organisationsrichtlinien, welcher Agent eine Aufgabe erhaelt.
- **Integration:**
  - HTTP-Adapter: Sendet Tasks an Agent-Agency via POST-Requests
  - Webhook-Empfaenger: Empfaengt neue Issues vom PM-Tool
  - Webhook-Sender: Meldet abgeschlossene Tasks zurueck an PM-Tool
  - Heartbeat-System: Loest regelmaessige Heartbeats an Agent-Agency aus
  - KPI-SDK: Sendet Events an KPI-Tracking (Issue-Zuweisung, Budget-Verbrauch, etc.)

### 3. Agent-Agency (AI Worker)

- **Technologie:** FastAPI/Celery
- **Port:** 4108
- **Rolle:** AI-Ausfuehrung mit spezialisierten Agenten (Coder, Writer, Researcher) und integrierter Qualitaetssicherung (QA-Agent). Agent-Agency fuehrt die eigentliche Arbeit aus und liefert Ergebnisse zurueck.
- **Integration:**
  - Heartbeat-Endpoint: Empfaengt Aufgaben von Paperclip via POST /api/v1/heartbeat/
  - Callback-API: Meldet Ergebnisse via PATCH an Paperclip zurueck
  - Webhook-Sender: Sendet Completion-Events an Paperclip
  - KPI-SDK: Sendet Events an KPI-Tracking (Task-Dauer, Token-Verbrauch, Erfolgsrate, etc.)

### 4. KPI-Tracking (Observer)

- **Technologie:** Fastify/InfluxDB
- **Ports:** API 4109, Admin 4110
- **Rolle:** Metriken sammeln, aggregieren und ueber Grafana-Dashboards visualisieren. KPI-Tracking ist der passive Beobachter, der alle Systeme ueberwacht, ohne sie zu beeinflussen.
- **Integration:**
  - SDK in allen 3 anderen Systemen installiert
  - Empfaengt Events via HTTP-API (POST /events)
  - Speichert Zeitreihen in InfluxDB
  - Stellt Grafana-Dashboards bereit (Port 3001)

---

## Datenfluss (detailliert)

### Schritt 1: Mensch erstellt Issue im PM-Tool

Ein Projektmanager erstellt eine neue Aufgabe im PM-Tool. Diese enthaelt:
- Titel und Beschreibung
- Prioritaet (niedrig/mittel/hoch/kritisch)
- Gewuenschter Aufgabentyp (Code, Text, Recherche)
- Optionale Anhaltspunkte (Repository, Dateien, Links)

**KPI-Event:** `pm.issue.created` (Timestamp, User-ID, Prioritaet)

### Schritt 2: PM-Tool sendet Webhook an Paperclip

Das PM-Tool feuert einen HTTP-Webhook an Paperclips Eingangs-Endpoint:
```
POST https://paperclip:3100/api/webhooks/pm-tool
Content-Type: application/json
Authorization: Bearer <PM_API_KEY>

{
  "event": "issue.created",
  "issue": { "id": "PM-1234", "title": "...", "description": "...", "priority": "high" }
}
```

**KPI-Event:** `pm.webhook.sent` (Ziel, Latenz, HTTP-Status)

### Schritt 3: Paperclip erstellt Issue und weist Agent zu

Paperclip empfaengt den Webhook und:
1. Erstellt ein internes Issue im Paperclip-Board
2. Prueft Governance-Regeln (Budget vorhanden? Agent verfuegbar? Risiko-Level akzeptabel?)
3. Waehlt den passenden Agent basierend auf Rolle und Org-Chart
4. Setzt den Status auf "assigned"

**KPI-Event:** `paperclip.issue.created`, `paperclip.issue.assigned` (Agent-ID, Board-ID)

### Schritt 4: Paperclip loest Heartbeat aus

Paperclip sendet einen Heartbeat an Agent-Agency, um die Aufgabe zu starten:
```
POST https://agent-agency:4108/api/v1/heartbeat/
Content-Type: application/json
Authorization: Bearer <PAPERCLIP_API_KEY>

{
  "issue_id": "PC-5678",
  "action": "process",
  "payload": {
    "title": "...",
    "description": "...",
    "type": "code",
    "repo": "...",
    "budget_tokens": 50000
  }
}
```

**KPI-Event:** `paperclip.heartbeat.sent` (Issue-ID, Agent-ID)

### Schritt 5: Agent-Agency fuehrt AI-Aufgabe aus

Agent-Agency empfaengt den Heartbeat und startet den internen Workflow:
1. **Orchestrator** klassifiziert die Aufgabe (Coder/Writer/Researcher)
2. **Risiko-Bewertung** prueft Scope und Sicherheit
3. **Executor** fuehrt die Aufgabe aus (AI-Aufruf mit entsprechendem Provider)
4. **QA-Agent** prueft das Ergebnis (optional: Retry bei Ablehnung)
5. **Ergebnis** wird via PATCH an Paperclip zurueckgemeldet:

```
PATCH https://paperclip:3100/api/issues/PC-5678
Content-Type: application/json
Authorization: Bearer <PAPERCLIP_API_KEY>

{
  "status": "completed",
  "result": {
    "deliverables": ["..."],
    "tokens_used": 12345,
    "duration_seconds": 42
  }
}
```

**KPI-Events:** `agent.task.started`, `agent.task.classified`, `agent.task.executed`, `agent.task.qa_passed`, `agent.task.completed` (jeweils mit Metriken)

### Schritt 6: Paperclip schliesst Issue ab

Paperclip empfaengt das Ergebnis und:
1. Aktualisiert den Issue-Status auf "done" (oder "failed")
2. Bucht Token-Verbrauch gegen das Budget
3. Optional: Leitet an einen weiteren QA-Schritt weiter

**KPI-Event:** `paperclip.issue.completed` (Dauer, Budget-Verbrauch)

### Schritt 7: Paperclip Webhook an PM-Tool

Paperclip benachrichtigt das PM-Tool ueber den Abschluss:
```
POST https://pm-backend:8000/api/webhooks/paperclip
Content-Type: application/json
Authorization: Bearer <PAPERCLIP_WEBHOOK_SECRET>

{
  "event": "issue.completed",
  "issue_id": "PC-5678",
  "pm_reference": "PM-1234",
  "result": { "status": "completed", "deliverables": ["..."] }
}
```

Das PM-Tool aktualisiert den Task-Status und benachrichtigt den Ersteller.

**KPI-Event:** `pm.task.updated` (Quelle: Paperclip, Status)

### Schritt 8: Alle Systeme senden KPI-Events

Jedes System sendet waehrend des gesamten Prozesses Events an KPI-Tracking:
```
POST https://kpi-api:4109/api/events
Content-Type: application/json
X-API-Key: <APP_API_KEY>

{
  "source": "agent-agency",
  "event": "task.completed",
  "timestamp": "2026-03-29T14:30:00Z",
  "data": {
    "task_id": "...",
    "duration_ms": 42000,
    "tokens_used": 12345,
    "provider": "anthropic",
    "model": "claude-sonnet-4-20250514"
  }
}
```

---

## Phasen-Plan

### Phase 1: Paperclip aufsetzen

**Ziel:** Paperclip als eigenstaendiges System mit Docker-Stack betreiben.

- [ ] Docker-Compose fuer Paperclip erstellen (App + PostgreSQL)
- [ ] Company-Struktur anlegen (INOTEC GmbH)
- [ ] Org-Chart definieren (Teams, Rollen, Agenten)
- [ ] Board fuer AI-Tasks erstellen
- [ ] Budget-Pools konfigurieren (Token-Limits pro Team/Agent)
- [ ] Governance-Regeln festlegen (Risiko-Schwellen, Genehmigungspflichten)
- [ ] API-Keys generieren fuer externe Systeme

**Erfolgskriterium:** Paperclip laeuft, Company ist angelegt, Board ist sichtbar.

### Phase 2: Agent-Agency als Paperclip-Agent

**Ziel:** Agent-Agency empfaengt und verarbeitet Aufgaben von Paperclip.

- [ ] HTTP-Adapter in Agent-Agency implementieren (Heartbeat-Endpoint)
- [ ] Paperclip-Client-Modul erstellen (Issue lesen, Status updaten)
- [ ] Agent-Registrierung bei Paperclip (Name, Faehigkeiten, Kapazitaet)
- [ ] Mapping: Paperclip Issue-Typen auf Agent-Agency Task-Typen
- [ ] Callback-Mechanismus implementieren (Ergebnis zurueck an Paperclip)
- [ ] Error-Handling: Fehlgeschlagene Tasks korrekt an Paperclip melden
- [ ] Integration-Tests: Paperclip sendet Task, Agent-Agency verarbeitet, meldet zurueck

**Erfolgskriterium:** End-to-End-Flow Paperclip -> Agent-Agency -> Paperclip funktioniert.

### Phase 3: PM-Tool mit Paperclip verbinden

**Ziel:** Bidirektionale Kommunikation zwischen PM-Tool und Paperclip.

- [ ] Webhook-Sender im PM-Tool implementieren (Issue erstellt/aktualisiert)
- [ ] Webhook-Empfaenger im PM-Tool implementieren (Status-Updates von Paperclip)
- [ ] Webhook-Empfaenger in Paperclip implementieren (PM-Tool Events)
- [ ] Mapping: PM-Tool Tasks auf Paperclip Issues (ID-Referenzen)
- [ ] Status-Synchronisation: PM-Tool Status <-> Paperclip Status
- [ ] Fehlerbehandlung: Retry-Logik fuer fehlgeschlagene Webhooks
- [ ] UI-Integration: PM-Tool zeigt Paperclip-Status an

**Erfolgskriterium:** Mensch erstellt Task im PM-Tool, sieht Ergebnis im PM-Tool.

### Phase 4: KPI-Tracking einbinden

**Ziel:** Alle Systeme senden Metriken an KPI-Tracking.

- [ ] KPI-Tracking Docker-Stack aufsetzen (Fastify + InfluxDB + Grafana)
- [ ] KPI-SDK als npm/pip-Paket bereitstellen
- [ ] SDK in PM-Tool integrieren (Django Middleware)
- [ ] SDK in Paperclip integrieren (Express Middleware)
- [ ] SDK in Agent-Agency integrieren (FastAPI Middleware)
- [ ] Event-Schema definieren (einheitliches Format fuer alle Systeme)
- [ ] Grafana-Dashboards erstellen:
  - Uebersichts-Dashboard (alle Systeme)
  - Agent-Performance (Erfolgsrate, Dauer, Token-Verbrauch)
  - Budget-Dashboard (Verbrauch pro Team/Agent)
  - Pipeline-Dashboard (End-to-End Durchlaufzeiten)
- [ ] Alerting konfigurieren (Budget-Limits, Fehlerquoten)

**Erfolgskriterium:** Grafana zeigt End-to-End-Metriken ueber alle 4 Systeme.

### Phase 5: Master Docker-Compose

**Ziel:** Alle 4 Systeme in einem einzigen Docker-Compose-Stack.

- [ ] Master docker-compose.yml erstellen
- [ ] Shared Docker-Netzwerk `inotec-ecosystem` konfigurieren
- [ ] Environment-Variablen konsolidieren (.env.ecosystem)
- [ ] Health-Checks fuer alle Services definieren
- [ ] Startup-Reihenfolge sicherstellen (depends_on mit Conditions)
- [ ] Volumes fuer persistente Daten konfigurieren
- [ ] Logging-Stack (optional: Loki + Grafana)
- [ ] Backup-Strategie fuer alle Datenbanken
- [ ] Dokumentation: Setup-Guide fuer neue Entwickler
- [ ] Smoke-Tests: Automatisierter End-to-End-Test nach `docker compose up`

**Erfolgskriterium:** `docker compose up` startet das gesamte Oekosystem, End-to-End-Flow funktioniert.

---

## Ports und Netzwerk

| System              | Port | Docker Service Name | Beschreibung                  |
|---------------------|------|---------------------|-------------------------------|
| PM-Tool Frontend    | 3000 | pm-frontend         | Next.js Frontend              |
| PM-Tool Backend     | 8000 | pm-backend          | Django REST API               |
| Paperclip           | 3100 | paperclip           | Company OS (Node.js/React)    |
| Agent-Agency        | 4108 | agent-agency        | AI Worker (FastAPI)           |
| KPI-Tracking API    | 4109 | kpi-api             | Metriken-API (Fastify)        |
| KPI-Tracking Admin  | 4110 | kpi-admin           | Admin-Oberflaeche             |
| PostgreSQL (PM)     | 5432 | pm-db               | PM-Tool Datenbank             |
| PostgreSQL (Paper.) | 5433 | paperclip-db        | Paperclip Datenbank           |
| PostgreSQL (Agent)  | 5410 | agent-db            | Agent-Agency Datenbank        |
| PostgreSQL (KPI)    | 5434 | kpi-db              | KPI-Tracking Datenbank        |
| Redis               | 6379 | redis               | Celery Broker + Cache         |
| InfluxDB            | 8086 | influxdb            | Zeitreihen-Datenbank          |
| Grafana             | 3001 | grafana             | Dashboard-Visualisierung      |

---

## Shared Network

Alle Services laufen im Docker-Netzwerk `inotec-ecosystem`. Dies ermoeglicht:
- Service-Discovery ueber Docker-DNS (z.B. `http://paperclip:3100`)
- Isolation vom Host-Netzwerk
- Einfache Kommunikation zwischen Containern ohne Port-Mapping

```yaml
networks:
  inotec-ecosystem:
    driver: bridge
    name: inotec-ecosystem
```

Jeder Service verbindet sich mit diesem Netzwerk:
```yaml
services:
  paperclip:
    networks:
      - inotec-ecosystem
  agent-agency:
    networks:
      - inotec-ecosystem
  # ... etc.
```

---

## Authentifizierung

### Paperclip --> Agent-Agency
- **Methode:** JWT (JSON Web Token), pro Agent
- **Environment-Variable:** `PAPERCLIP_API_KEY`
- **Header:** `Authorization: Bearer <PAPERCLIP_API_KEY>`
- **Rotation:** Quartalsweise oder bei Kompromittierung
- **Scope:** Nur Task-bezogene Endpoints (heartbeat, task-status)

### PM-Tool --> Paperclip
- **Methode:** API-Key, Board-Level
- **Environment-Variable:** `PM_TOOL_API_KEY`
- **Header:** `Authorization: Bearer <PM_TOOL_API_KEY>`
- **Scope:** Issue-Erstellung und Status-Abfrage fuer das zugewiesene Board

### Paperclip --> PM-Tool (Webhooks)
- **Methode:** HMAC-SHA256 Signatur
- **Environment-Variable:** `PAPERCLIP_WEBHOOK_SECRET`
- **Header:** `X-Webhook-Signature: sha256=<HMAC>`
- **Validierung:** PM-Tool verifiziert Signatur vor Verarbeitung

### Alle --> KPI-Tracking
- **Methode:** X-API-Key, pro Applikation
- **Environment-Variable:** `KPI_API_KEY`
- **Header:** `X-API-Key: <KPI_API_KEY>`
- **Scope:** Nur Event-Schreibzugriff (kein Lesezugriff auf andere Apps)

### Sicherheits-Richtlinien
- Alle API-Keys werden als Docker Secrets oder Environment-Variablen verwaltet
- Keine Keys im Source-Code oder in Git
- TLS/HTTPS fuer alle externen Verbindungen (intern optional via Docker-Netzwerk)
- Rate-Limiting auf allen oeffentlichen Endpoints
- Audit-Logging fuer alle authentifizierten Zugriffe (via KPI-Tracking)

---

## Offene Fragen und Entscheidungen

1. **Retry-Strategie:** Exponential Backoff mit maximal 5 Versuchen fuer fehlgeschlagene Webhooks?
2. **Dead-Letter-Queue:** Wohin mit Tasks, die nach allen Retries fehlschlagen?
3. **Multi-Tenancy:** Soll Paperclip mehrere Companies/Teams parallel verwalten?
4. **Skalierung:** Horizontale Skalierung von Agent-Agency (mehrere Worker-Instanzen)?
5. **Disaster Recovery:** Backup- und Restore-Prozess fuer alle 4 Datenbanken?

---

*Erstellt: 2026-03-29 | Version: 1.0 | Autor: INOTEC Entwicklungsteam*
