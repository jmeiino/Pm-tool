# KI-Integration

PM-Tool unterstuetzt mehrere KI-Provider ueber eine einheitliche Schnittstelle. Alle KI-Features nutzen dieselbe Abstraktion und koennen per GUI umgeschaltet werden.

---

## Provider

### Claude (Anthropic)

- **Typ:** Cloud-basiert
- **Staerken:** Hochwertige Analyse, komplexe Zusammenfassungen
- **Konfiguration:** API-Key + Modellname
- **Standard-Modell:** `claude-sonnet-4-20250514`

### Ollama (Lokal)

- **Typ:** Lokal / On-Premises
- **Staerken:** Kostenlos, datenschutzfreundlich, keine Cloud-Abhaengigkeit
- **Konfiguration:** Server-URL + Modellname
- **Standard-Modell:** `llama3.1`
- **Voraussetzung:** Ollama-Server muss laufen

### OpenRouter (Multi-Modell)

- **Typ:** Cloud-Gateway
- **Staerken:** Zugang zu 100+ Modellen (Claude, GPT, Llama, Mistral etc.)
- **Konfiguration:** API-Key + Modellname
- **Standard-Modell:** `anthropic/claude-sonnet-4`

---

## Architektur

```
                    get_ai_client(user)
                           |
              +------------+------------+
              |            |            |
        ClaudeClient  OllamaClient  OpenRouterClient
              |            |            |
              +------------+------------+
                           |
                     BaseAIClient (ABC)
                           |
                      AIService
                    (Business-Logik)
```

### Konfigurationsprioriaet

1. `User.preferences.ai` (GUI-Einstellung) — hoechste Prioritaet
2. Umgebungsvariablen (`.env`) — Fallback

### Caching

KI-Ergebnisse werden im `AIResult`-Modell zwischengespeichert:
- **TTL:** 24 Stunden
- **Schluessel:** Hash aus Eingabeinhalt + Ergebnistyp
- Verhindert doppelte API-Aufrufe bei identischen Anfragen

---

## Funktionen

### Aufgaben priorisieren

- **Endpunkt:** `POST /api/v1/ai/prioritize/`
- **Eingabe:** Liste offener Todos
- **Ausgabe:** Sortierte Liste mit KI-Confidence-Werten
- **Anwendung:** Automatische Priorisierung nach Dringlichkeit und Wichtigkeit

### Tagesplan vorschlagen

- **Endpunkt:** `POST /api/v1/ai/daily-plan/`
- **Eingabe:** Offene Todos, Kalender-Events, Kapazitaet
- **Ausgabe:** Zeitblock-Plan mit empfohlener Reihenfolge
- **Anwendung:** KI plant den Tag unter Beruecksichtigung von Meetings und Prioritaeten

### Inhalte zusammenfassen

- **Endpunkt:** `POST /api/v1/ai/summarize/`
- **Eingabe:** Beliebiger Text
- **Ausgabe:** Kompakte Zusammenfassung
- **Anwendung:** Lange Confluence-Seiten oder Issue-Beschreibungen zusammenfassen

### Action-Items extrahieren

- **Endpunkt:** `POST /api/v1/ai/extract-actions/`
- **Eingabe:** Text (z.B. Meeting-Protokoll)
- **Ausgabe:** Liste konkreter Aufgaben
- **Anwendung:** Aus Texten automatisch Todos ableiten

### Confluence-Seite analysieren

- **Endpunkt:** `POST /api/v1/integrations/confluence-pages/{id}/analyze/`
- **Eingabe:** Confluence-Seiteninhalt
- **Ausgabe:** Zusammenfassung, Entscheidungen, Risiken, Action-Items
- **Anwendung:** Wichtige Informationen aus Confluence-Seiten extrahieren

### GitHub-Repository analysieren

- **Endpunkt:** `POST /api/v1/integrations/repo-analyses/{id}/analyze/`
- **Eingabe:** Repository-Metadaten (Sprachen, README, Contributors)
- **Ausgabe:** Tech-Stack, Staerken, Verbesserungsvorschlaege, naechste Schritte
- **Anwendung:** Code-Qualitaet und Verbesserungspotential bewerten

---

## Asynchrone Verarbeitung

Alle KI-Tasks laufen asynchron ueber Celery:

| Celery-Task | Beschreibung |
|---|---|
| `async_prioritize_todos` | Todos priorisieren |
| `async_suggest_daily_plan` | Tagesplan vorschlagen |
| `async_summarize_content` | Inhalt zusammenfassen |
| `async_extract_action_items` | Action-Items extrahieren |
| `async_analyze_confluence_page` | Confluence-Seite analysieren |
| `analyze_github_repo_task` | GitHub-Repo analysieren |

Alle Tasks: `max_retries=3`, `default_retry_delay=60s`

---

## Provider wechseln

1. Oeffne **Einstellungen** (`/einstellungen`)
2. Waehle den Tab **KI-Provider**
3. Waehle den gewuenschten Provider
4. Gib API-Key und Modellname ein
5. Speichern — alle KI-Features nutzen ab sofort den neuen Provider
