# Deployment

Anleitung fuer das Produktions-Deployment mit Docker, Gunicorn und Nginx.

---

## Produktion starten

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

## Vorbereitungen

### 1. Umgebungsvariablen anpassen

```bash
cp .env.example .env
```

Fuer Produktion **muessen** folgende Werte geaendert werden:

| Variable | Aktion |
|---|---|
| `DJANGO_SECRET_KEY` | Sicheren Schluessel generieren |
| `DJANGO_DEBUG` | `False` setzen |
| `DJANGO_ALLOWED_HOSTS` | Domain(s) eintragen |
| `POSTGRES_PASSWORD` | Sicheres Passwort setzen |

### 2. Admin-Benutzer erstellen

```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

### 3. Statische Dateien

Statische Dateien werden beim Build automatisch gesammelt und ueber Nginx ausgeliefert.

---

## Unterschiede zur Entwicklung

| Aspekt | Entwicklung | Produktion |
|---|---|---|
| WSGI-Server | Django runserver | Gunicorn (4 Workers) |
| Reverse Proxy | keiner | Nginx (Port 80/443) |
| Static Files | Django liefert aus | Nginx via Volume |
| Debug | aktiviert | deaktiviert |
| Settings | `config.settings.dev` | `config.settings.prod` |
| Healthchecks | nur DB/Redis | alle Dienste |
| Restart Policy | keine | `unless-stopped` |
| Celery Concurrency | Standard | 2 Worker |

---

## Nginx-Konfiguration

Die Konfiguration liegt unter `nginx/nginx.conf`:

| Pfad | Ziel |
|---|---|
| `/api/` | Backend (Django/Gunicorn) |
| `/admin/` | Django Admin |
| `/static/` | Static-Files-Volume |
| `/*` | Frontend (Next.js) |

### SSL/TLS

Fuer HTTPS muss die Nginx-Konfiguration um SSL-Zertifikate erweitert werden:

```nginx
server {
    listen 443 ssl;
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    # ... restliche Konfiguration
}
```

---

## Docker-Dienste (Produktion)

| Dienst | Beschreibung | Port |
|---|---|---|
| `nginx` | Reverse Proxy | 80 (443) |
| `backend` | Django + Gunicorn | 8000 (intern) |
| `frontend` | Next.js | 3000 (intern) |
| `db` | PostgreSQL 16 | 5432 (intern) |
| `redis` | Redis 7 | 6379 (intern) |
| `celery` | Celery Worker | — |
| `celery-beat` | Celery Beat Scheduler | — |

---

## Monitoring

### Healthchecks

Alle Dienste haben Docker-Healthchecks:

```bash
# Status pruefen
docker compose -f docker-compose.prod.yml ps
```

### Logs

```bash
# Alle Logs
docker compose -f docker-compose.prod.yml logs -f

# Einzelner Dienst
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f celery
```

### Celery-Monitoring

```bash
# Aktive Tasks pruefen
docker compose -f docker-compose.prod.yml exec celery celery -A config inspect active

# Scheduled Tasks
docker compose -f docker-compose.prod.yml exec celery celery -A config inspect scheduled
```

---

## Backup

### Datenbank

```bash
# Backup erstellen
docker compose -f docker-compose.prod.yml exec db pg_dump -U pmtool pmtool > backup.sql

# Backup einspielen
docker compose -f docker-compose.prod.yml exec -T db psql -U pmtool pmtool < backup.sql
```

---

## Updates

```bash
# Neuen Code pullen
git pull origin main

# Container mit neuem Code bauen und starten
docker compose -f docker-compose.prod.yml up --build -d

# Migrationen ausfuehren (falls noetig)
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate
```
