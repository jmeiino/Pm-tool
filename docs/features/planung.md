# Tages- und Wochenplanung

Die Planungsfunktion ist das Herzstuck von PM-Tool: Organisiere deinen Tag mit Drag-and-Drop und lass dir von der KI Vorschlaege machen.

---

## Tagesplan

### Uebersicht

Der Tagesplan (`/planung/tagesplan`) ermoeglicht die Strukturierung des Arbeitstags in Zeitbloecke.

### Funktionsweise

1. **Todos auswaehlen** — Aus der offenen Todo-Liste Aufgaben in den Tagesplan ziehen
2. **Zeitbloecke anordnen** — Per Drag-and-Drop (dnd-kit) die Reihenfolge bestimmen
3. **Zeiten zuweisen** — Startzeit und Dauer fuer jeden Block festlegen
4. **Kapazitaet pruefen** — Die Kapazitaetsanzeige zeigt verplante vs. verfuegbare Stunden

### KI-Vorschlaege

Ueber den Button **KI-Vorschlag** wird ein automatischer Tagesplan generiert:

- Die KI beruecksichtigt offene Todos, Prioritaeten und geschaetzte Zeiten
- Kalender-Events werden als geblockte Zeiten eingeplant
- Die verfuegbare Kapazitaet (`daily_capacity_hours`) wird respektiert
- Ergebnis: Ein vorgeschlagener Zeitplan, der manuell angepasst werden kann

### Felder

| Feld | Beschreibung |
|---|---|
| `date` | Datum des Tagesplans |
| `capacity_hours` | Verfuegbare Arbeitsstunden |
| `ai_summary` | KI-generierte Zusammenfassung |
| `notes` | Eigene Notizen |

### DailyPlanItem (Zeitblock)

| Feld | Beschreibung |
|---|---|
| `todo` | Verknuepftes PersonalTodo |
| `order` | Reihenfolge im Plan |
| `time_block_start` | Startzeit |
| `time_block_minutes` | Dauer in Minuten |
| `completed` | Abgeschlossen? |

---

## Wochenplan

### Uebersicht

Der Wochenplan (`/planung/wochenplan`) zeigt eine 5-Tage-Uebersicht (Montag bis Freitag).

### Funktionsweise

- Fasst die Tagesplaene einer Woche zusammen
- Ermoeglicht die Planung von Wochenzielen
- Am Ende der Woche kann eine Retrospektive erfasst werden

### Felder

| Feld | Beschreibung |
|---|---|
| `week_start` | Montag der Woche |
| `daily_plans` | Verknuepfte Tagesplaene (M2M) |
| `goals` | Wochenziele |
| `retrospective` | Rueckblick am Wochenende |

---

## PersonalTodo

Persoenliche Todos sind die Basis fuer die Planung:

### Quellen

| Quelle | Beschreibung |
|---|---|
| `manual` | Manuell erstellt |
| `jira` | Aus Jira importiert |
| `confluence` | Aus Confluence-Analyse extrahiert |
| `email` | Aus E-Mail abgeleitet |
| `teams` | Aus Teams-Nachricht |
| `ai` | Von der KI vorgeschlagen |

### Felder

- **Titel** und **Beschreibung**
- **Prioritaet** (1–5, wobei 1 = hoechste)
- **Status** — Open, In Progress, Done, Cancelled
- **Faelligkeitsdatum**
- **Geschaetzte Stunden**
- **Verknuepftes Issue** (optional)
- **KI-Confidence** — Wie sicher ist die KI bei der Priorisierung

---

## API-Endpunkte

| Methode | Pfad | Beschreibung |
|---|---|---|
| `GET/POST` | `/api/v1/todos/` | Todos auflisten / erstellen |
| `GET/PUT/PATCH/DELETE` | `/api/v1/todos/{id}/` | Todo-CRUD |
| `GET/POST` | `/api/v1/daily-plans/` | Tagesplaene auflisten / erstellen |
| `GET/PUT/PATCH/DELETE` | `/api/v1/daily-plans/{id}/` | Tagesplan-CRUD |
| `GET/POST` | `/api/v1/weekly-plans/` | Wochenplaene auflisten / erstellen |
| `GET/PUT/PATCH/DELETE` | `/api/v1/weekly-plans/{id}/` | Wochenplan-CRUD |
| `POST` | `/api/v1/ai/daily-plan/` | KI-Tagesplan-Vorschlag |
| `POST` | `/api/v1/ai/prioritize/` | KI-Priorisierung |
