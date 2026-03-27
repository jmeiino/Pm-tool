# Benachrichtigungen

PM-Tool informiert Benutzer ueber wichtige Ereignisse durch ein internes Benachrichtigungssystem.

---

## Benachrichtigungstypen

| Typ | Beispiel |
|---|---|
| Deadline-Warnung | "Issue PM-42 ist morgen faellig" |
| Sync-Fehler | "Jira-Synchronisation fehlgeschlagen" |
| Sync-Erfolg | "15 Issues aus Jira aktualisiert" |
| KI-Vorschlag | "KI-Tagesplan wurde generiert" |
| Status-Aenderung | "Issue PM-42 wurde auf 'Done' gesetzt" |

## Schweregrade

| Schweregrad | Beschreibung |
|---|---|
| `info` | Informativ, keine Aktion noetig |
| `warning` | Warnung, moegliche Aktion erforderlich |
| `error` | Fehler, Aktion erforderlich |

---

## Deadline-Warnungen

Jede Stunde prueft ein Celery-Task (`check_deadline_warnings`) alle offenen Issues und Todos auf bevorstehende Faelligkeiten. Ist ein Faelligkeitsdatum innerhalb der naechsten 24 Stunden, wird eine Warnung erstellt.

---

## API-Endpunkte

| Methode | Pfad | Beschreibung |
|---|---|---|
| `GET` | `/api/v1/notifications/` | Benachrichtigungen auflisten (paginiert) |
| `GET` | `/api/v1/notifications/{id}/` | Einzelne Benachrichtigung |
| `PATCH` | `/api/v1/notifications/{id}/` | Als gelesen markieren |
| `DELETE` | `/api/v1/notifications/{id}/` | Benachrichtigung loeschen |

### Filter

- `?is_read=false` — Nur ungelesene
- `?severity=warning` — Nach Schweregrad filtern
