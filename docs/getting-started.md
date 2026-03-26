# Schnellstart

Diese Anleitung fuehrt dich von der Installation bis zum ersten Login.

---

## Voraussetzungen

- **Docker** und **Docker Compose** (v2+)
- **Git**
- Mindestens 4 GB RAM (fuer alle Container)

---

## 1. Repository klonen

```bash
git clone <repository-url>
cd Pm-tool
```

## 2. Umgebungsvariablen konfigurieren

```bash
cp .env.example .env
```

Die `.env`-Datei enthaelt sinnvolle Standardwerte fuer die lokale Entwicklung. Passe bei Bedarf an:

| Variable | Zweck |
|---|---|
| `DJANGO_SECRET_KEY` | Aendern fuer Produktion! |
| `POSTGRES_PASSWORD` | Datenbankpasswort |
| `ANTHROPIC_API_KEY` | Fuer Claude-KI-Features |

> **Tipp:** KI-Provider und Integrationen koennen auch spaeter in der GUI unter **Einstellungen** konfiguriert werden.

## 3. Starten

```bash
docker compose up --build
```

Beim ersten Start werden automatisch:
- Die Datenbank erstellt und migriert
- Alle Python- und Node.js-Abhaengigkeiten installiert
- Celery-Worker und Beat-Scheduler gestartet

## 4. Dienste

| Dienst | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend-API | http://localhost:8000/api/v1/ |
| API-Dokumentation (Swagger) | http://localhost:8000/api/docs/ |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

## 5. Admin-Benutzer anlegen

```bash
docker compose exec backend python manage.py createsuperuser
```

## 6. Erste Schritte nach dem Login

1. **Einstellungen oeffnen** (`/einstellungen`) — KI-Provider konfigurieren
2. **Projekt erstellen** (`/projekte`) — Erstes manuelles Projekt anlegen
3. **Todos hinzufuegen** (`/todos`) — Aufgaben erfassen
4. **Tagesplan erstellen** (`/planung/tagesplan`) — Aufgaben per Drag-and-Drop planen
5. **Optional:** Integrationen verbinden (Jira, GitHub, Confluence, Microsoft 365)

---

## Haeufige Probleme

### Container starten nicht

```bash
# Logs anzeigen
docker compose logs backend

# Datenbank-Migrationen manuell ausfuehren
docker compose exec backend python manage.py migrate
```

### Frontend zeigt Verbindungsfehler

Stelle sicher, dass `NEXT_PUBLIC_API_URL` in der `.env` korrekt auf das Backend zeigt (Standard: `http://localhost:8000/api/v1`).

### Celery-Tasks laufen nicht

```bash
# Worker-Status pruefen
docker compose logs celery

# Redis-Verbindung pruefen
docker compose exec redis redis-cli ping
```
