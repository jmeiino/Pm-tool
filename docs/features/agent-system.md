# Agent-System

Das Agent-System ermoeglicht die Delegation von Aufgaben an einen externen KI-Agenten-Microservice. Agenten arbeiten autonom, koennen aber Rueckfragen stellen.

---

## Konzept

```
PM-Tool (Benutzer)                    Agent-Microservice
       |                                      |
       |  1. Aufgabe delegieren               |
       |  ─────────────────────────────────>  |
       |                                      |
       |  2. Agent arbeitet                   |
       |                                      |
       |  3. Webhook: Status/Frage            |
       |  <─────────────────────────────────  |
       |                                      |
       |  4. Benutzer antwortet               |
       |  ─────────────────────────────────>  |
       |                                      |
       |  5. Webhook: Ergebnis/Deliverables   |
       |  <─────────────────────────────────  |
```

---

## Einrichtung

### Agent-Company konfigurieren

Unter **Einstellungen** kann die Verbindung zum Agent-Microservice eingerichtet werden:

| Feld | Beschreibung |
|---|---|
| `name` | Name der Agent-Company |
| `base_url` | URL des Agent-Microservice |
| `api_key` | API-Schluessel fuer Authentifizierung |
| `webhook_secret` | Geheimschluessel fuer Webhook-Verifizierung |

---

## Agenten-Rollen

Agenten sind hierarchisch organisiert:

| Rolle | Beschreibung |
|---|---|
| **CEO** | Oberste Instanz, koordiniert Abteilungen |
| **Department Head** | Leitet eine Abteilung, verteilt Aufgaben |
| **Specialist** | Fuehrt Aufgaben aus |
| **QA** | Qualitaetssicherung der Ergebnisse |

### Org-Chart

Die Agenten werden in einem Organigramm dargestellt:
- CEO oben
- Abteilungsleiter darunter
- Spezialisten unter ihren Abteilungsleitern
- QA-Agenten separat

Jeder Agent hat einen Status:
- **Idle** — Verfuegbar
- **Working** — Arbeitet an einer Aufgabe
- **Waiting** — Wartet auf Antwort
- **Offline** — Nicht verfuegbar

---

## Aufgaben delegieren

### Workflow

1. Oeffne ein **Issue** im Projektmanagement
2. Klicke **An Agenten delegieren**
3. Fuelle das Formular aus:

| Feld | Beschreibung |
|---|---|
| Aufgabentyp | Software, Content, Design, Research |
| Prioritaet | 1 (hoechste) bis 5 (niedrigste) |
| Anweisungen | Optionale Zusatzinformationen |

4. Die Aufgabe wird erstellt und an den Microservice gesendet

### Status-Verlauf

```
Pending → Assigned → In Progress → Review → Completed
                                          → Failed
                                          → Cancelled
```

---

## Kommunikation

### Nachrichtentypen

| Typ | Beschreibung |
|---|---|
| `text` | Normale Textnachricht |
| `question` | Agent stellt eine Frage |
| `decision` | Agent bittet um Entscheidung (mit Optionen) |
| `handoff` | Aufgabe wird an anderen Agenten uebergeben |
| `status_change` | Statusaenderung der Aufgabe |
| `deliverable` | Agent liefert Ergebnis (Link) |
| `error` | Fehlermeldung |
| `system` | Systemnachricht |

### Rueckfragen beantworten

Wenn ein Agent eine Frage stellt (`is_decision_pending=true`):

1. Die Frage erscheint in der Timeline mit Antwort-Optionen
2. Der Benutzer waehlt eine Option oder schreibt frei
3. Die Antwort wird an den Microservice weitergeleitet
4. Der Agent arbeitet weiter

---

## Echtzeit-Updates

Agent-Aufgaben nutzen **Server-Sent Events (SSE)** fuer Live-Updates:

```
GET /api/v1/agents/tasks/{task_id}/stream/
```

- Neue Nachrichten werden sofort angezeigt
- Statusaenderungen aktualisieren die UI
- Kein manuelles Neuladen noetig

Zusaetzlich pollt das Frontend:
- Task-Liste: alle 15 Sekunden
- Einzelne Task: alle 5 Sekunden
- Company-Status: alle 10 Sekunden

---

## Frontend

### Agenten-Seite (`/agents`)

Die Hauptseite zeigt:
- **Statuskarten** — Aktive Aufgaben, wartende Entscheidungen, Agenten-Anzahl
- **Organigramm** — Hierarchische Agent-Ansicht
- **Aufgabenliste** — Aktive und abgeschlossene Aufgaben

### Task-Detail (AgentTaskPanel)

Beim Klick auf eine Aufgabe oeffnet sich das Detail-Panel:
- **Links:** Organigramm mit hervorgehobenem aktivem Agent
- **Rechts:** Timeline aller Nachrichten + Chat-Eingabe
- **Header:** Status, zugewiesener Agent, offene Entscheidungen
- **Deliverables:** Links zu Ergebnissen

---

## API-Endpunkte

| Methode | Pfad | Beschreibung |
|---|---|---|
| `GET` | `/agents/tasks/` | Alle Aufgaben auflisten |
| `POST` | `/agents/tasks/delegate/` | Neue Aufgabe delegieren |
| `POST` | `/agents/tasks/{id}/reply/` | Auf Agenten-Frage antworten |
| `POST` | `/agents/tasks/{id}/cancel/` | Aufgabe abbrechen |
| `POST` | `/agents/tasks/{id}/reprioritize/` | Prioritaet aendern |
| `GET` | `/agents/tasks/{id}/stream/` | SSE-Stream fuer Live-Updates |
| `GET` | `/agents/profiles/` | Alle Agenten-Profile |
| `GET` | `/agents/company/status/` | Company-Dashboard-Statistiken |
| `POST` | `/agents/webhooks/event/` | Webhook-Empfang vom Microservice |
