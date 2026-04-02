# Paperclip -- Docker-Setup

## Voraussetzungen

- Docker >= 24.0 und Docker Compose >= 2.20
- Node.js 20+ (nur fuer lokale Entwicklung ohne Docker)
- pnpm (empfohlener Paketmanager fuer Paperclip)
- Mindestens 2 GB freier RAM fuer die Container

## Option 1: Lokale Entwicklung

Fuer schnelle Iterationen ohne Docker:

```bash
cd C:\Projekte\paperclip

# Umgebungsvariablen konfigurieren
cp .env.example .env
# .env anpassen: DATABASE_URL, API-Keys etc.

# Abhaengigkeiten installieren
pnpm install

# Datenbank-Migrationen ausfuehren (falls vorhanden)
pnpm db:migrate

# Entwicklungsserver starten
pnpm dev

# Oeffne http://localhost:3100
```

**Hinweis:** Fuer lokale Entwicklung wird eine lokale PostgreSQL-Instanz benoetigt. Alternativ kann nur der Datenbank-Container aus Option 2 gestartet werden:

```bash
docker compose -f docker-compose.paperclip.yml up paperclip-db -d
```

## Option 2: Docker-Compose (Produktion)

### docker-compose.paperclip.yml

Erstelle diese Datei in `C:\Projekte\paperclip\docker-compose.paperclip.yml`:

```yaml
version: "3.9"

services:
  paperclip:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: paperclip-app
    restart: unless-stopped
    ports:
      - "3100:3100"
    environment:
      NODE_ENV: production
      PORT: 3100
      DATABASE_URL: postgresql://paperclip:paperclip_secret@paperclip-db:5432/paperclip
      # AI-Provider Konfiguration
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:-}
      OPENAI_API_KEY: ${OPENAI_API_KEY:-}
      # KPI-Tracking Integration
      KPI_TRACKING_URL: http://kpi-api:4109/api/v1
      KPI_API_KEY: ${KPI_API_KEY:-}
      # Agent-Agency Verbindung
      AGENT_AGENCY_URL: http://agent-agency:8000/api/v1
      AGENT_AGENCY_API_KEY: ${AGENT_AGENCY_API_KEY:-}
      # Session & Security
      SESSION_SECRET: ${SESSION_SECRET:-bitte-aendern-in-produktion}
      CORS_ORIGINS: http://localhost:3100,http://paperclip:3100
    depends_on:
      paperclip-db:
        condition: service_healthy
    networks:
      - inotec-ecosystem
    healthcheck:
      test: ["CMD", "node", "-e", "fetch('http://localhost:3100/health').then(r => process.exit(r.ok ? 0 : 1))"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 15s

  paperclip-db:
    image: postgres:16-alpine
    container_name: paperclip-db
    restart: unless-stopped
    ports:
      - "5433:5432"
    environment:
      POSTGRES_DB: paperclip
      POSTGRES_USER: paperclip
      POSTGRES_PASSWORD: paperclip_secret
    volumes:
      - paperclip-db-data:/var/lib/postgresql/data
    networks:
      - inotec-ecosystem
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U paperclip -d paperclip"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  paperclip-db-data:
    driver: local

networks:
  inotec-ecosystem:
    external: true
```

### Dockerfile (falls noch nicht vorhanden)

Erstelle `C:\Projekte\paperclip\Dockerfile`:

```dockerfile
FROM node:20-alpine AS base
RUN corepack enable && corepack prepare pnpm@latest --activate
WORKDIR /app

# Abhaengigkeiten installieren
FROM base AS deps
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile --prod=false

# Build
FROM base AS build
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN pnpm build

# Production
FROM base AS production
ENV NODE_ENV=production
COPY --from=deps /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
COPY --from=build /app/package.json ./

EXPOSE 3100
USER node
CMD ["node", "dist/server.js"]
```

### Starten

```bash
# Netzwerk erstellen (einmalig, falls noch nicht vorhanden)
docker network create inotec-ecosystem

# Paperclip starten
cd C:\Projekte\paperclip
docker compose -f docker-compose.paperclip.yml up -d

# Logs pruefen
docker compose -f docker-compose.paperclip.yml logs -f paperclip

# Status pruefen
docker compose -f docker-compose.paperclip.yml ps
```

## Erste Schritte nach dem Start

### 1. Company "INOTEC" anlegen

Oeffne `http://localhost:3100` und erstelle die Firma:

- **Name:** INOTEC Sicherheitstechnik
- **Beschreibung:** KI-gestuetztes Unternehmen fuer Sicherheitstechnik
- **Budget:** Initiales Token-Budget festlegen (z.B. 1.000.000 Tokens)

### 2. Org-Chart erstellen

Erstelle die Unternehmensstruktur:

```
CEO (Orchestrator)
 |
 +-- Engineering-Abteilung
 |    +-- Senior Coder (Agent)
 |    +-- Junior Coder (Agent)
 |
 +-- Content-Abteilung
 |    +-- Technical Writer (Agent)
 |
 +-- Research-Abteilung
 |    +-- Researcher (Agent)
 |
 +-- Quality Assurance
      +-- QA Reviewer (Agent)
```

### 3. Agents registrieren mit HTTP-Adapter

Jeder Agent wird mit einem HTTP-Adapter konfiguriert, der auf Agent-Agency zeigt:

```json
{
  "name": "Senior Coder",
  "role": "coder",
  "adapter": {
    "type": "http",
    "url": "http://agent-agency:8000/api/v1/tasks/",
    "headers": {
      "X-API-Key": "agent-agency-api-key"
    },
    "method": "POST"
  },
  "capabilities": ["python", "javascript", "docker", "sql"],
  "max_concurrent_tasks": 3
}
```

Wiederhole dies fuer alle Agenten-Rollen (Writer, Researcher, QA).

### 4. Budget pro Agent setzen

Konfiguriere Token-Budgets fuer jeden Agenten:

| Agent | Tages-Budget | Monats-Budget | Max pro Aufgabe |
|-------|-------------|---------------|-----------------|
| Senior Coder | 100.000 Tokens | 2.000.000 Tokens | 50.000 Tokens |
| Junior Coder | 50.000 Tokens | 1.000.000 Tokens | 25.000 Tokens |
| Technical Writer | 30.000 Tokens | 600.000 Tokens | 15.000 Tokens |
| Researcher | 80.000 Tokens | 1.500.000 Tokens | 40.000 Tokens |
| QA Reviewer | 20.000 Tokens | 400.000 Tokens | 10.000 Tokens |

### 5. Erste Test-Aufgabe erstellen

Erstelle eine einfache Aufgabe um den gesamten Flow zu testen:

```bash
curl -X POST http://localhost:3100/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Hello-World Python-Skript erstellen",
    "description": "Erstelle ein einfaches Python-Skript das Hello World ausgibt",
    "priority": "low",
    "assign_to": "Senior Coder"
  }'
```

Erwarteter Ablauf:
1. Paperclip nimmt die Aufgabe entgegen
2. Prueft Budget des zugewiesenen Agenten
3. Leitet die Aufgabe an Agent-Agency weiter (HTTP-Adapter)
4. Agent-Agency fuehrt die Aufgabe aus (Orchestrator -> Coder -> QA)
5. Ergebnis wird an Paperclip zurueckgeliefert
6. KPI-Events werden an KPI-Tracking gesendet

## Master Docker-Compose

### docker-compose.ecosystem.yml

Diese Datei orchestriert das gesamte INOTEC-Okosystem. Erstelle sie in `C:\Projekte\docker-compose.ecosystem.yml`:

```yaml
version: "3.9"

# Master-Compose fuer das gesamte INOTEC AI-Oekosystem
# Startet alle 4 Projekte in einem gemeinsamen Netzwerk

include:
  # Agent-Agency -- AI-Agenten-Microservice
  - path: ./Agent-Agency/docker-compose.yml
    env_file: ./Agent-Agency/.env

  # PM-Tool -- Projektmanagement
  - path: ./pm-tool/docker-compose.yml
    env_file: ./pm-tool/.env

  # KPI-Tracking -- Metriken & Monitoring
  - path: ./KPI-Tracking/docker-compose.yml
    env_file: ./KPI-Tracking/.env

  # Paperclip -- AI-Company Management
  - path: ./paperclip/docker-compose.paperclip.yml
    env_file: ./paperclip/.env

networks:
  inotec-ecosystem:
    driver: bridge
    name: inotec-ecosystem
```

### Alternatives Setup mit Profilen

Falls `include` nicht unterstuetzt wird (Docker Compose < 2.20), kann stattdessen ein monolithisches Setup verwendet werden:

```yaml
version: "3.9"

services:
  # ============================================
  # Agent-Agency
  # ============================================
  agent-agency:
    build:
      context: ./Agent-Agency
    container_name: agent-agency
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://agency:agency_secret@agency-db:5432/agency
      REDIS_URL: redis://agency-redis:6379/0
      KPI_TRACKING_URL: http://kpi-api:4109/api/v1
    depends_on:
      agency-db:
        condition: service_healthy
      agency-redis:
        condition: service_healthy
    networks:
      - inotec-ecosystem
    profiles: ["agency", "full"]

  agency-db:
    image: postgres:16-alpine
    container_name: agency-db
    restart: unless-stopped
    environment:
      POSTGRES_DB: agency
      POSTGRES_USER: agency
      POSTGRES_PASSWORD: agency_secret
    volumes:
      - agency-db-data:/var/lib/postgresql/data
    networks:
      - inotec-ecosystem
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U agency -d agency"]
      interval: 10s
      timeout: 5s
      retries: 5
    profiles: ["agency", "full"]

  agency-redis:
    image: redis:7-alpine
    container_name: agency-redis
    restart: unless-stopped
    networks:
      - inotec-ecosystem
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    profiles: ["agency", "full"]

  agency-worker:
    build:
      context: ./Agent-Agency
    container_name: agency-worker
    restart: unless-stopped
    command: celery -A app.worker worker -l info -c 4
    environment:
      DATABASE_URL: postgresql+asyncpg://agency:agency_secret@agency-db:5432/agency
      REDIS_URL: redis://agency-redis:6379/0
    depends_on:
      agency-db:
        condition: service_healthy
      agency-redis:
        condition: service_healthy
    networks:
      - inotec-ecosystem
    profiles: ["agency", "full"]

  # ============================================
  # PM-Tool
  # ============================================
  pm-tool:
    build:
      context: ./pm-tool
    container_name: pm-tool
    restart: unless-stopped
    ports:
      - "8080:8080"
    environment:
      DATABASE_URL: postgresql://pmtool:pmtool_secret@pmtool-db:5432/pmtool
      KPI_TRACKING_URL: http://kpi-api:4109/api/v1
      AGENT_AGENCY_URL: http://agent-agency:8000/api/v1
    depends_on:
      pmtool-db:
        condition: service_healthy
    networks:
      - inotec-ecosystem
    profiles: ["pmtool", "full"]

  pmtool-db:
    image: postgres:16-alpine
    container_name: pmtool-db
    restart: unless-stopped
    environment:
      POSTGRES_DB: pmtool
      POSTGRES_USER: pmtool
      POSTGRES_PASSWORD: pmtool_secret
    volumes:
      - pmtool-db-data:/var/lib/postgresql/data
    networks:
      - inotec-ecosystem
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U pmtool -d pmtool"]
      interval: 10s
      timeout: 5s
      retries: 5
    profiles: ["pmtool", "full"]

  # ============================================
  # KPI-Tracking
  # ============================================
  kpi-api:
    build:
      context: ./KPI-Tracking
    container_name: kpi-api
    restart: unless-stopped
    ports:
      - "4109:4109"
    environment:
      INFLUXDB_URL: http://kpi-influxdb:8086
      INFLUXDB_TOKEN: ${INFLUXDB_TOKEN:-mein-influxdb-token}
      INFLUXDB_ORG: inotec
      INFLUXDB_BUCKET: kpi
    depends_on:
      kpi-influxdb:
        condition: service_healthy
    networks:
      - inotec-ecosystem
    profiles: ["kpi", "full"]

  kpi-influxdb:
    image: influxdb:2-alpine
    container_name: kpi-influxdb
    restart: unless-stopped
    ports:
      - "8086:8086"
    environment:
      DOCKER_INFLUXDB_INIT_MODE: setup
      DOCKER_INFLUXDB_INIT_USERNAME: admin
      DOCKER_INFLUXDB_INIT_PASSWORD: admin_secret
      DOCKER_INFLUXDB_INIT_ORG: inotec
      DOCKER_INFLUXDB_INIT_BUCKET: kpi
      DOCKER_INFLUXDB_INIT_ADMIN_TOKEN: ${INFLUXDB_TOKEN:-mein-influxdb-token}
    volumes:
      - kpi-influxdb-data:/var/lib/influxdb2
    networks:
      - inotec-ecosystem
    healthcheck:
      test: ["CMD", "influx", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    profiles: ["kpi", "full"]

  kpi-grafana:
    image: grafana/grafana:latest
    container_name: kpi-grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_USER: admin
      GF_SECURITY_ADMIN_PASSWORD: admin
    volumes:
      - kpi-grafana-data:/var/lib/grafana
      - ./KPI-Tracking/grafana/provisioning:/etc/grafana/provisioning
      - ./KPI-Tracking/grafana/dashboards:/var/lib/grafana/dashboards
    networks:
      - inotec-ecosystem
    profiles: ["kpi", "full"]

  # ============================================
  # Paperclip
  # ============================================
  paperclip:
    build:
      context: ./paperclip
    container_name: paperclip-app
    restart: unless-stopped
    ports:
      - "3100:3100"
    environment:
      NODE_ENV: production
      PORT: 3100
      DATABASE_URL: postgresql://paperclip:paperclip_secret@paperclip-db:5432/paperclip
      KPI_TRACKING_URL: http://kpi-api:4109/api/v1
      AGENT_AGENCY_URL: http://agent-agency:8000/api/v1
    depends_on:
      paperclip-db:
        condition: service_healthy
    networks:
      - inotec-ecosystem
    profiles: ["paperclip", "full"]

  paperclip-db:
    image: postgres:16-alpine
    container_name: paperclip-db
    restart: unless-stopped
    ports:
      - "5433:5432"
    environment:
      POSTGRES_DB: paperclip
      POSTGRES_USER: paperclip
      POSTGRES_PASSWORD: paperclip_secret
    volumes:
      - paperclip-db-data:/var/lib/postgresql/data
    networks:
      - inotec-ecosystem
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U paperclip -d paperclip"]
      interval: 10s
      timeout: 5s
      retries: 5
    profiles: ["paperclip", "full"]

volumes:
  agency-db-data:
  pmtool-db-data:
  kpi-influxdb-data:
  kpi-grafana-data:
  paperclip-db-data:

networks:
  inotec-ecosystem:
    driver: bridge
    name: inotec-ecosystem
```

### Nutzung des Master-Compose

```bash
cd C:\Projekte

# Gesamtes Oekosystem starten
docker compose -f docker-compose.ecosystem.yml --profile full up -d

# Nur bestimmte Teile starten
docker compose -f docker-compose.ecosystem.yml --profile agency --profile kpi up -d

# Status aller Services pruefen
docker compose -f docker-compose.ecosystem.yml --profile full ps

# Logs eines bestimmten Services
docker compose -f docker-compose.ecosystem.yml logs -f paperclip

# Alles stoppen
docker compose -f docker-compose.ecosystem.yml --profile full down
```

### Port-Uebersicht

| Service | Port | URL |
|---------|------|-----|
| Agent-Agency API | 8000 | http://localhost:8000 |
| Agent-Agency Dashboard | 8000 | http://localhost:8000/dashboard |
| PM-Tool | 8080 | http://localhost:8080 |
| KPI-Tracking API | 4109 | http://localhost:4109 |
| Grafana | 3000 | http://localhost:3000 |
| InfluxDB | 8086 | http://localhost:8086 |
| Paperclip | 3100 | http://localhost:3100 |
| Agency DB (Postgres) | 5432 | localhost:5432 |
| PM-Tool DB (Postgres) | 5434 | localhost:5434 |
| Paperclip DB (Postgres) | 5433 | localhost:5433 |
| Redis (Agency) | 6379 | localhost:6379 |

## Fehlerbehebung

### Container startet nicht

```bash
# Logs pruefen
docker compose -f docker-compose.paperclip.yml logs paperclip

# In den Container einsteigen
docker exec -it paperclip-app sh

# Datenbank-Verbindung testen
docker exec -it paperclip-db psql -U paperclip -d paperclip -c "SELECT 1"
```

### Netzwerk-Probleme

```bash
# Pruefen ob das Netzwerk existiert
docker network ls | grep inotec-ecosystem

# Netzwerk manuell erstellen
docker network create inotec-ecosystem

# Pruefen welche Container im Netzwerk sind
docker network inspect inotec-ecosystem
```

### Datenbank zuruecksetzen

```bash
# Achtung: Loescht alle Daten!
docker compose -f docker-compose.paperclip.yml down -v
docker compose -f docker-compose.paperclip.yml up -d
```
