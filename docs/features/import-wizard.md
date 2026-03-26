# Import-Wizard

Der Import-Wizard ermoeglicht den Bulk-Import von Daten aus Jira, GitHub und Confluence ueber eine gefuehrte Oberflaeche.

---

## Uebersicht

Der Import-Bereich (`/import`) bietet zwei Ansichten:

1. **Dashboard** — Integrationsstatus, Sync-Historie und Intervall-Konfiguration
2. **Wizard** — Tab-basierter Import fuer jede Datenquelle

### Workflow-Prinzip

Jeder Import folgt dem gleichen Muster:

```
Preview (nur lesen) → Auswahl → Confirm (Datenbank-Schreibzugriff)
```

Die Preview-Daten werden 5 Minuten lang gecacht, um unnoetige API-Aufrufe zu vermeiden.

---

## Jira-Import

### Schritt 1: Preview

```
GET /api/v1/integrations/import/jira/preview/
```

- Laedt alle Jira-Projekte mit Issue-Anzahl
- Optional: `?project_key=X` — Laedt Issues fuer ein bestimmtes Projekt nach (Lazy Loading)

### Schritt 2: Auswahl

- Projekte expandieren, um Issues zu sehen
- Filter verfuegbar: Assignee, Status, Sprint
- Einzelne Issues oder ganze Projekte auswaehlen
- "Alle auswaehlen"-Button

### Schritt 3: Bestaetigen

```
POST /api/v1/integrations/import/jira/confirm/
```

- Erstellt/aktualisiert `Project` und `Issue` Datensaetze
- Gibt Anzahl erstellter/aktualisierter Eintraege zurueck

---

## GitHub-Import

### Schritt 1: Preview

```
GET /api/v1/integrations/import/github/preview/
```

- Laedt Repositories mit Metadaten (Sterne, Sprache, Issue-Anzahl)
- Optional: `?mine_only=true` — Nur eigene Repos/Issues

### Schritt 2: Auswahl

- Repos expandieren fuer Issue-Uebersicht
- Zielprojekt waehlen: Neues Projekt erstellen oder bestehendes verwenden

### Schritt 3: Bestaetigen

```
POST /api/v1/integrations/import/github/confirm/
```

- Erstellt Projekt (falls neu) und Issues
- Speichert Repo-Konfiguration in `IntegrationConfig.settings`

### Konflikterkennung

```
GET /api/v1/integrations/import/github/conflicts/
```

Erkennt Issues, die sowohl lokal als auch auf GitHub geaendert wurden.

---

## Confluence-Import

### Schritt 1: Spaces laden

```
GET /api/v1/integrations/import/confluence/preview/
```

- Ohne Parameter: Alle Spaces auflisten
- Mit `?space_key=X`: Seiten in einem Space laden
- Optional: `?my_pages_only=true` — Nur eigene Seiten

### Schritt 2: Seiten auswaehlen

- Zweiphasen-Wizard:
  1. **Seiten auswaehlen** — Checkbox-Auswahl mit optionaler KI-Analyse
  2. **Action-Items pruefen** — Extrahierte Action-Items aus der KI-Analyse

### Schritt 3: Bestaetigen

```
POST /api/v1/integrations/import/confluence/confirm/
```

- Erstellt `ConfluencePage` Datensaetze
- Optional mit `analyze=true`: Triggert KI-Analyse fuer Action-Items

---

## Import-Dashboard

Das Dashboard (`/import`, Ansicht: Dashboard) zeigt:

### Integrationskarten

Fuer jede aktive Integration:
- Letzter Sync-Zeitpunkt und Status-Badge
- Anzahl synchronisierter Elemente
- Button fuer manuellen Sync
- Einstellbares Polling-Intervall (1–120 Minuten)

### Sync-Historie

- Letzte Sync-Logs mit erstellten/aktualisierten Eintraegen
- Fehlermeldungen bei fehlgeschlagenen Syncs

### Intervall anpassen

```
POST /api/v1/integrations/import/dashboard/update-schedule/
```

Aendert das Polling-Intervall fuer eine Integration (in Minuten).

---

## Frontend-Komponenten

| Komponente | Beschreibung |
|---|---|
| `ImportWizard` | Tab-Navigation (Jira, GitHub, Confluence) |
| `JiraImportStep` | Projekt-/Issue-Auswahl mit Filtern |
| `GitHubImportStep` | Repo-Auswahl mit Zielprojekt-Selektor |
| `ConfluenceImportStep` | Zweiphasen-Wizard (Seiten → Action-Items) |
| `ImportDashboard` | Statuskarten und Sync-Historie |
| `ImportConfirmDialog` | Bestaetigungsdialog vor Import |
| `ImportResultSummary` | Ergebnisanzeige nach Import |
