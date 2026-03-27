# Konfiguration

PM-Tool wird ueber Umgebungsvariablen (`.env`) und GUI-Einstellungen konfiguriert. GUI-Einstellungen haben Vorrang vor `.env`-Werten.

---

## Umgebungsvariablen

### Django

| Variable | Beschreibung | Standard |
|---|---|---|
| `DJANGO_SECRET_KEY` | Geheimer Schluessel | `change-me-in-production` |
| `DJANGO_DEBUG` | Debug-Modus | `True` |
| `DJANGO_ALLOWED_HOSTS` | Erlaubte Hosts (kommagetrennt) | `localhost,127.0.0.1` |

### Datenbank

| Variable | Beschreibung | Standard |
|---|---|---|
| `POSTGRES_DB` | Datenbankname | `pmtool` |
| `POSTGRES_USER` | Benutzer | `pmtool` |
| `POSTGRES_PASSWORD` | Passwort | `pmtool` |
| `POSTGRES_HOST` | Host | `db` |
| `POSTGRES_PORT` | Port | `5432` |

### Redis / Celery

| Variable | Beschreibung | Standard |
|---|---|---|
| `CELERY_BROKER_URL` | Redis-URL | `redis://redis:6379/0` |

### KI-Provider

> Diese Werte dienen als Fallback. Alle Einstellungen koennen in der GUI unter **Einstellungen > KI-Provider** ueberschrieben werden.

| Variable | Beschreibung | Standard |
|---|---|---|
| `AI_PROVIDER` | Aktiver Provider: `claude`, `ollama`, `openrouter` | `claude` |
| `ANTHROPIC_API_KEY` | Claude API-Key | — |
| `ANTHROPIC_MODEL` | Claude-Modell | `claude-sonnet-4-20250514` |
| `OLLAMA_BASE_URL` | Ollama-Server-URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama-Modell | `llama3.1` |
| `OPENROUTER_API_KEY` | OpenRouter API-Key | — |
| `OPENROUTER_MODEL` | OpenRouter-Modell | `anthropic/claude-sonnet-4` |

### Integrationen

| Variable | Beschreibung |
|---|---|
| `ATLASSIAN_URL` | Atlassian-Cloud-URL (z.B. `https://firma.atlassian.net`) |
| `ATLASSIAN_EMAIL` | Atlassian-Account-E-Mail |
| `ATLASSIAN_API_TOKEN` | Atlassian-API-Token |
| `GITHUB_TOKEN` | GitHub Personal Access Token |
| `MS_CLIENT_ID` | Microsoft Azure App Client-ID |
| `MS_CLIENT_SECRET` | Microsoft Azure App Client-Secret |
| `MS_TENANT_ID` | Microsoft Azure Tenant-ID |
| `MS_REDIRECT_URI` | OAuth2-Redirect-URI |

### Frontend

| Variable | Beschreibung | Standard |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Backend-API-URL | `http://localhost:8000/api/v1` |

---

## GUI-Einstellungen

Unter `/einstellungen` koennen folgende Bereiche konfiguriert werden:

### Profil

- Benutzername, E-Mail
- Zeitzone
- Taegliche Arbeitskapazitaet (in Stunden)

### KI-Provider

- Provider-Auswahl (Claude / Ollama / OpenRouter)
- API-Key und Modellname
- Einstellungen werden pro Benutzer in `User.preferences` gespeichert

### Integrationen

- **Jira** — URL, E-Mail, API-Token
- **Confluence** — URL, E-Mail, API-Token
- **GitHub** — Personal Access Token
- **Microsoft 365** — OAuth2-Verbindung starten

Alle Credentials werden im `IntegrationConfig.credentials`-Feld gespeichert.

---

## Konfigurationsprioriaet

```
1. GUI-Einstellungen (User.preferences)        ← hoechste Prioritaet
2. IntegrationConfig.credentials (pro User)
3. Umgebungsvariablen (.env)                    ← niedrigste Prioritaet
```
