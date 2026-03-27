# Projektmanagement

PM-Tool bietet vollstaendiges Projektmanagement mit Projekten, Sprints, Issues, Labels und Kommentaren — manuell oder synchronisiert aus Jira.

---

## Projekte

### Erstellen

Unter `/projekte` koennen Projekte manuell erstellt werden:

- **Name** — Projektname
- **Key** — Eindeutiger Kurzschluessel (z.B. `PM`, `WEB`)
- **Beschreibung** — Optionale Beschreibung
- **Status** — Active, Paused oder Archived

### Jira-Synchronisation

Projekte koennen mit Jira verknuepft werden:

1. Integration unter **Einstellungen** konfigurieren
2. Projekt erstellen mit aktiviertem `jira_sync`-Flag
3. Oder ueber den **Import-Wizard** Jira-Projekte importieren

Synchronisierte Projekte erhalten ein `jira_project_key` und werden alle 15 Minuten automatisch aktualisiert.

### Ansichten

- **Grid-Ansicht** (`/projekte`) — Alle Projekte als Karten mit Statusfilter
- **Detailansicht** (`/projekte/[id]`) — Tabs fuer Uebersicht, Issues und Sprints

---

## Sprints

Sprints sind Zeitraeume innerhalb eines Projekts:

| Feld | Beschreibung |
|---|---|
| Name | Sprint-Bezeichnung |
| Status | Planned, Active, Closed |
| Start-/Enddatum | Zeitraum des Sprints |
| Projekt | Zugehoeriges Projekt |

Sprints koennen manuell erstellt oder aus Jira synchronisiert werden.

---

## Issues

Issues sind die zentrale Arbeitseinheit:

### Typen

| Typ | Beschreibung |
|---|---|
| Epic | Grosses Feature, das mehrere Stories umfasst |
| Story | Benutzerstory / Feature |
| Task | Technische Aufgabe |
| Bug | Fehlerbehebung |
| Subtask | Unteraufgabe eines Issues |

### Prioritaeten

| Prioritaet | Stufe |
|---|---|
| Highest | Hoechste |
| High | Hoch |
| Medium | Mittel |
| Low | Niedrig |
| Lowest | Niedrigste |

### Status-Workflow

```
Backlog → To Do → In Progress → In Review → Done
```

### Felder

- Titel, Beschreibung, Typ, Prioritaet, Status
- Zugewiesener Benutzer (Assignee), Reporter
- Sprint-Zuordnung
- Labels (M2M)
- Jira-ID und GitHub-ID fuer Sync
- Geschaetzte und tatsaechliche Story Points

### Kommentare

Jedes Issue kann Kommentare haben. Kommentare werden bei Jira-Sync ebenfalls synchronisiert.

---

## Labels

Labels sind farbige Tags, die Issues kategorisieren:

- Jedes Label hat einen **Namen** und eine **Farbe**
- Labels werden projektuebergreifend geteilt
- Ein Issue kann mehrere Labels haben (Many-to-Many)

---

## API-Endpunkte

| Methode | Pfad | Beschreibung |
|---|---|---|
| `GET/POST` | `/api/v1/projects/` | Projekte auflisten / erstellen |
| `GET/PUT/PATCH/DELETE` | `/api/v1/projects/{id}/` | Projekt-CRUD |
| `GET` | `/api/v1/projects/{id}/stats/` | Projektstatistiken |
| `GET/POST` | `/api/v1/sprints/` | Sprints auflisten / erstellen |
| `GET/PUT/PATCH/DELETE` | `/api/v1/sprints/{id}/` | Sprint-CRUD |
| `GET/POST` | `/api/v1/issues/` | Issues auflisten / erstellen |
| `GET/PUT/PATCH/DELETE` | `/api/v1/issues/{id}/` | Issue-CRUD |
| `POST` | `/api/v1/issues/{id}/transition/` | Status-Uebergang |
| `GET/POST` | `/api/v1/issues/{id}/comments/` | Kommentare lesen / erstellen |
| `GET/POST` | `/api/v1/labels/` | Labels verwalten |
