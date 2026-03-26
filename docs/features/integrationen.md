# Integrationen

PM-Tool verbindet sich mit Jira, Confluence, GitHub und Microsoft 365. Alle Integrationen werden ueber `IntegrationConfig` pro Benutzer gespeichert.

---

## Jira (Bidirektional)

### Was wird synchronisiert?

| Objekt | Richtung | Details |
|---|---|---|
| Projekte | Inbound + Outbound | Name, Key, Status |
| Sprints | Inbound + Outbound | Name, Status, Zeitraum |
| Issues | Inbound + Outbound | Alle Felder inkl. Assignee, Priority, Status |
| Kommentare | Inbound + Outbound | Autor, Inhalt |

### Konflikterkennung

Bei bidirektionalem Sync kann es zu Konflikten kommen, wenn ein Issue sowohl lokal als auch in Jira geaendert wurde:

- Vergleich ueber `jira_updated_at` Timestamps
- Bei Konflikt: Warnung im SyncLog
- Benutzer kann entscheiden, welche Version gilt

### Konfiguration

1. Unter **Einstellungen > Integrationen > Jira**
2. Atlassian-URL, E-Mail und API-Token eingeben
3. Integration aktivieren

### Technische Details

- **Client:** `JiraClient` (basiert auf `atlassian-python-api`)
- **Service:** `JiraSyncService`
- **Polling:** Alle 15 Minuten via Celery Beat
- **Mapper:** `JiraMapper` wandelt Jira-Felder in Django-Modelle um

---

## Confluence (Inbound + KI-Analyse)

### Was wird synchronisiert?

| Objekt | Richtung | Details |
|---|---|---|
| Seiten | Inbound | Titel, Inhalt, Space, Autor |

### KI-Analyse

Importierte Confluence-Seiten koennen per KI analysiert werden:

- **Zusammenfassung** — Kompakter Ueberblick
- **Entscheidungen** — Getroffene Beschluesse
- **Risiken** — Identifizierte Risiken
- **Action-Items** — Konkrete naechste Schritte

### Konfiguration

1. Unter **Einstellungen > Integrationen > Confluence**
2. Atlassian-URL, E-Mail und API-Token eingeben (kann Jira-Credentials teilen)

### Technische Details

- **Client:** `ConfluenceClient` (basiert auf `atlassian-python-api`)
- **Service:** `ConfluenceSyncService`
- **Polling:** Alle 30 Minuten via Celery Beat

---

## GitHub (Inbound + Repository-Analyse)

### Was wird synchronisiert?

| Objekt | Richtung | Details |
|---|---|---|
| Commits | Inbound | SHA, Autor, Message, Branch |
| Pull Requests | Inbound | Titel, Status, Autor |

### Auto-Verknuepfung

Commit-Messages werden per Regex auf Issue-Keys geprueft. Enthaelt ein Commit z.B. `PM-42`, wird er automatisch mit Issue PM-42 verknuepft.

### Repository-Analyse

Repositories koennen per KI analysiert werden:

- **Tech-Stack** — Verwendete Sprachen und Frameworks
- **Staerken** — Was gut gemacht wird
- **Verbesserungen** — Wo Potenzial besteht
- **Naechste Schritte** — Empfohlene Action-Items

Aus den Ergebnissen koennen direkt Todos erstellt werden (`POST /integrations/repo-analyses/{id}/create-todos/`).

### Konfiguration

1. Unter **Einstellungen > Integrationen > GitHub**
2. GitHub Personal Access Token eingeben

### Technische Details

- **Client:** `GitHubClient` (eigene Implementierung mit `httpx`)
- **Service:** `GitHubSyncService`
- **Polling:** Alle 10 Minuten via Celery Beat

---

## Microsoft 365 (Inbound, OAuth2)

### Was wird synchronisiert?

| Objekt | Richtung | Details |
|---|---|---|
| Kalender-Events | Inbound | Titel, Start/Ende, Ort, Teilnehmer |

### OAuth2-Flow

```
1. Benutzer klickt "Microsoft verbinden" in Einstellungen
2. Redirect zu Microsoft Login
3. Benutzer autorisiert die App
4. Callback mit Authorization Code
5. Token wird in IntegrationConfig gespeichert
6. Kalender-Sync startet automatisch
```

### Konfiguration

Voraussetzung: Azure App Registration mit folgenden Berechtigungen:
- `Calendars.Read`

Umgebungsvariablen:
- `MS_CLIENT_ID`, `MS_CLIENT_SECRET`, `MS_TENANT_ID`, `MS_REDIRECT_URI`

### Technische Details

- **Client:** `GraphClient` (Microsoft Graph API)
- **Auth-Library:** MSAL (Microsoft Authentication Library)
- **Service:** `MicrosoftSyncService`
- **Polling:** Alle 15 Minuten via Celery Beat

---

## Sync-Protokolle

Jeder Sync-Vorgang wird in `SyncLog` protokolliert:

| Feld | Beschreibung |
|---|---|
| `status` | success, partial, failed |
| `records_created` | Anzahl neu erstellter Datensaetze |
| `records_updated` | Anzahl aktualisierter Datensaetze |
| `errors` | JSON mit Fehlerdetails |
| `duration_seconds` | Dauer des Sync-Vorgangs |

Logs sind unter `/import` (Dashboard-Ansicht) einsehbar.

---

## Polling-Intervalle

| Integration | Standard-Intervall |
|---|---|
| Jira | 15 Minuten |
| Confluence | 30 Minuten |
| GitHub | 10 Minuten |
| Microsoft Kalender | 15 Minuten |

Intervalle koennen ueber das Import-Dashboard angepasst werden (1–120 Minuten).
