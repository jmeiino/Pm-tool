# API-Referenz

Vollstaendige Uebersicht aller REST-Endpunkte. Basis-URL: `/api/v1/`

> **Tipp:** Die interaktive Swagger-UI ist unter `/api/docs/` verfuegbar.

---

## Authentifizierung

Alle Endpunkte erfordern eine authentifizierte Session. Daten werden automatisch nach dem angemeldeten Benutzer gefiltert.

---

## Projects

| Methode | Pfad | Beschreibung |
|---|---|---|
| `GET` | `/projects/` | Alle Projekte auflisten |
| `POST` | `/projects/` | Neues Projekt erstellen |
| `GET` | `/projects/{id}/` | Projekt-Details |
| `PUT` | `/projects/{id}/` | Projekt vollstaendig aktualisieren |
| `PATCH` | `/projects/{id}/` | Projekt teilweise aktualisieren |
| `DELETE` | `/projects/{id}/` | Projekt loeschen |
| `GET` | `/projects/{id}/stats/` | Projektstatistiken (Issues nach Status, Sprint-Fortschritt) |

## Sprints

| Methode | Pfad | Beschreibung |
|---|---|---|
| `GET` | `/sprints/` | Sprints auflisten (Filter: `?project=id`) |
| `POST` | `/sprints/` | Sprint erstellen |
| `GET` | `/sprints/{id}/` | Sprint-Details |
| `PUT/PATCH` | `/sprints/{id}/` | Sprint aktualisieren |
| `DELETE` | `/sprints/{id}/` | Sprint loeschen |

## Issues

| Methode | Pfad | Beschreibung |
|---|---|---|
| `GET` | `/issues/` | Issues auflisten (Filter: `?project=id`, `?status=`, `?assignee=`, `?sprint=`) |
| `POST` | `/issues/` | Issue erstellen |
| `GET` | `/issues/{id}/` | Issue-Details |
| `PUT/PATCH` | `/issues/{id}/` | Issue aktualisieren |
| `DELETE` | `/issues/{id}/` | Issue loeschen |
| `POST` | `/issues/{id}/transition/` | Status-Uebergang (Body: `{"status": "in_progress"}`) |
| `GET` | `/issues/{id}/comments/` | Kommentare auflisten |
| `POST` | `/issues/{id}/comments/` | Kommentar hinzufuegen |

## Labels

| Methode | Pfad | Beschreibung |
|---|---|---|
| `GET` | `/labels/` | Labels auflisten |
| `POST` | `/labels/` | Label erstellen (`name`, `color`) |

---

## Todos

| Methode | Pfad | Beschreibung |
|---|---|---|
| `GET` | `/todos/` | Todos auflisten (Filter: `?status=`, `?priority=`, `?source=`) |
| `POST` | `/todos/` | Todo erstellen |
| `GET` | `/todos/{id}/` | Todo-Details |
| `PUT/PATCH` | `/todos/{id}/` | Todo aktualisieren |
| `DELETE` | `/todos/{id}/` | Todo loeschen |

## Daily Plans

| Methode | Pfad | Beschreibung |
|---|---|---|
| `GET` | `/daily-plans/` | Tagesplaene auflisten (Filter: `?date=YYYY-MM-DD`) |
| `POST` | `/daily-plans/` | Tagesplan erstellen |
| `GET` | `/daily-plans/{id}/` | Tagesplan-Details (inkl. Items) |
| `PUT/PATCH` | `/daily-plans/{id}/` | Tagesplan aktualisieren |
| `DELETE` | `/daily-plans/{id}/` | Tagesplan loeschen |

## Weekly Plans

| Methode | Pfad | Beschreibung |
|---|---|---|
| `GET` | `/weekly-plans/` | Wochenplaene auflisten |
| `POST` | `/weekly-plans/` | Wochenplan erstellen |
| `GET` | `/weekly-plans/{id}/` | Wochenplan-Details |
| `PUT/PATCH` | `/weekly-plans/{id}/` | Wochenplan aktualisieren |
| `DELETE` | `/weekly-plans/{id}/` | Wochenplan loeschen |

---

## Integrationen

| Methode | Pfad | Beschreibung |
|---|---|---|
| `GET` | `/integrations/configs/` | Alle Konfigurationen |
| `POST` | `/integrations/configs/` | Neue Integration einrichten |
| `GET` | `/integrations/configs/{id}/` | Konfiguration-Details |
| `PUT/PATCH` | `/integrations/configs/{id}/` | Konfiguration aendern |
| `DELETE` | `/integrations/configs/{id}/` | Integration entfernen |
| `POST` | `/integrations/configs/{id}/sync/` | Manuellen Sync ausloesen |
| `POST` | `/integrations/configs/{id}/register-webhook/` | Webhook fuer alle Repos registrieren (Body: `{"callback_url": "..."}`) |
| `GET` | `/integrations/configs/{id}/conflicts/` | Sync-Konflikte anzeigen |
| `GET` | `/integrations/sync-logs/` | Sync-Protokolle |

## Confluence

| Methode | Pfad | Beschreibung |
|---|---|---|
| `GET` | `/integrations/confluence-pages/` | Importierte Seiten |
| `POST` | `/integrations/confluence-pages/{id}/analyze/` | KI-Analyse starten |

## GitHub

| Methode | Pfad | Beschreibung |
|---|---|---|
| `GET` | `/integrations/git-activities/` | Commits, PRs und Reviews |
| `GET` | `/integrations/repo-analyses/` | Repository-Analysen |
| `POST` | `/integrations/repo-analyses/{id}/analyze/` | KI-Analyse starten |
| `POST` | `/integrations/repo-analyses/{id}/create-todos/` | Todos aus Analyse erstellen |
| `POST` | `/integrations/github/webhook/` | GitHub Webhook-Endpoint (wird von GitHub aufgerufen) |

## Kalender

| Methode | Pfad | Beschreibung |
|---|---|---|
| `GET` | `/integrations/calendar-events/` | Synchronisierte Events |

## Microsoft OAuth

| Methode | Pfad | Beschreibung |
|---|---|---|
| `GET` | `/integrations/microsoft/auth/` | OAuth2-Flow starten |
| `GET` | `/integrations/microsoft/callback/` | OAuth2-Callback |

---

## Import-Wizard

### Jira

| Methode | Pfad | Beschreibung |
|---|---|---|
| `GET` | `/integrations/import/jira/preview/` | Projekte/Issues vorschauen |
| `POST` | `/integrations/import/jira/confirm/` | Import bestaetigen |

### GitHub

| Methode | Pfad | Beschreibung |
|---|---|---|
| `GET` | `/integrations/import/github/preview/` | Repos/Issues vorschauen |
| `POST` | `/integrations/import/github/confirm/` | Import bestaetigen |
| `GET` | `/integrations/import/github/conflicts/` | Konflikte erkennen |

### Confluence

| Methode | Pfad | Beschreibung |
|---|---|---|
| `GET` | `/integrations/import/confluence/preview/` | Spaces/Seiten vorschauen |
| `POST` | `/integrations/import/confluence/confirm/` | Import bestaetigen |

### Dashboard

| Methode | Pfad | Beschreibung |
|---|---|---|
| `GET` | `/integrations/import/dashboard/history/` | Sync-Historie |
| `POST` | `/integrations/import/dashboard/update-schedule/` | Polling-Intervall aendern |

---

## KI

| Methode | Pfad | Beschreibung |
|---|---|---|
| `GET` | `/ai/ai/provider/` | Aktuellen KI-Provider abrufen |
| `PATCH` | `/ai/ai/provider/` | KI-Provider aendern |
| `POST` | `/ai/ai/prioritize/` | Todos priorisieren |
| `POST` | `/ai/ai/summarize/` | Text zusammenfassen |
| `POST` | `/ai/ai/extract-actions/` | Action-Items extrahieren |
| `POST` | `/ai/ai/daily-plan/` | Tagesplan-Vorschlag |

---

## Agents

| Methode | Pfad | Beschreibung |
|---|---|---|
| `GET` | `/agents/tasks/` | Alle Agent-Aufgaben |
| `POST` | `/agents/tasks/delegate/` | Aufgabe delegieren |
| `POST` | `/agents/tasks/{id}/reply/` | Auf Frage antworten |
| `POST` | `/agents/tasks/{id}/cancel/` | Aufgabe abbrechen |
| `POST` | `/agents/tasks/{id}/reprioritize/` | Prioritaet aendern |
| `GET` | `/agents/tasks/{id}/stream/` | SSE-Stream (Echtzeit) |
| `GET` | `/agents/profiles/` | Agenten-Profile |
| `GET` | `/agents/company/status/` | Company-Status |
| `POST` | `/agents/webhooks/event/` | Webhook-Empfang |

---

## Users

| Methode | Pfad | Beschreibung |
|---|---|---|
| `GET` | `/users/me/` | Eigenes Profil |
| `PATCH` | `/users/me/` | Profil aktualisieren |

## Notifications

| Methode | Pfad | Beschreibung |
|---|---|---|
| `GET` | `/notifications/` | Benachrichtigungen (paginiert, Filter: `?is_read=`, `?severity=`) |
| `PATCH` | `/notifications/{id}/` | Als gelesen markieren |
| `DELETE` | `/notifications/{id}/` | Loeschen |

---

## API-Dokumentation

| Pfad | Beschreibung |
|---|---|
| `/api/docs/` | Swagger-UI (interaktiv) |
| `/api/schema/` | OpenAPI-Schema (JSON) |
