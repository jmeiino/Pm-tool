# CI/CD Pipeline

Uebersicht aller GitHub Actions Workflows, Container-Registry und Deployment-Prozesse.

---

## Workflows

### Backend CI (`backend.yml`)

**Trigger:** Push auf `main` oder PR, wenn `backend/**` geaendert wird.

| Job | Beschreibung |
|---|---|
| **Lint (ruff)** | Code-Stil und Formatierung pruefen |
| **Tests (pytest)** | Unit-Tests mit PostgreSQL + Redis, Coverage-Report mit Schwellenwert (70%) |
| **Build & Push** | Docker-Image bauen und in GHCR pushen (nur auf `main`) |
| **Slack Notification** | Benachrichtigung bei Fehler |

### Frontend CI (`frontend.yml`)

**Trigger:** Push auf `main` oder PR, wenn `frontend/**` geaendert wird.

| Job | Beschreibung |
|---|---|
| **Lint & Typecheck** | ESLint + TypeScript-Pruefung |
| **Unit Tests (Vitest)** | Komponenten- und Utility-Tests mit Coverage |
| **Build & Push** | Docker-Image bauen und in GHCR pushen (nur auf `main`) |
| **Slack Notification** | Benachrichtigung bei Fehler |

### E2E Tests (`e2e-tests.yml`)

**Trigger:** Push auf `main` oder PR, wenn `frontend/**` geaendert wird.

| Job | Beschreibung |
|---|---|
| **Playwright E2E** | Startet Backend + Frontend, fuehrt Playwright-Tests mit Chromium aus |

Das Backend wird mit PostgreSQL und Redis als Service-Container gestartet. Playwright-Reports werden als Artifact gespeichert (14 Tage).

### Security Scanning (`security.yml`)

**Trigger:** PRs, Push auf `main`, woechentlich (Montag 6:00 UTC).

| Job | Beschreibung |
|---|---|
| **CodeQL** | SAST-Analyse fuer Python und TypeScript |
| **pip-audit** | Python-Abhaengigkeiten auf Schwachstellen pruefen |
| **npm audit** | Node-Abhaengigkeiten auf Schwachstellen pruefen |
| **Trivy** | Container-Image-Scanning (nur auf `main`) |

### Deploy Staging (`deploy-staging.yml`)

**Trigger:** Automatisch nach erfolgreichem Backend/Frontend CI auf `main`.

- Verbindet sich per SSH zum Staging-Server
- Pullt die neuesten GHCR-Images
- Fuehrt Migrationen und Static-File-Collection aus
- Prueft den Health-Endpoint

### Deploy Production (`deploy-production.yml`)

**Trigger:** Manuell (`workflow_dispatch`) mit waehlbarem Image-Tag.

- Erfordert GitHub Environment `production` mit manueller Genehmigung
- Erstellt Rollback-Tags vor dem Deploy
- Prueft den Health-Endpoint nach Deploy
- Benachrichtigt bei Erfolg und Fehler

### Release (`release.yml`)

**Trigger:** Push auf `main`.

- Nutzt `release-please` fuer automatisches Versioning
- Erstellt GitHub Releases mit Changelog
- Taggt GHCR-Images mit Semver-Version

---

## Container Registry (GHCR)

Images werden in der GitHub Container Registry gespeichert:

| Image | Tags |
|---|---|
| `ghcr.io/jmeiino/pm-tool-backend` | `latest`, `main`, `sha-<commit>`, `v1.2.3` |
| `ghcr.io/jmeiino/pm-tool-frontend` | `latest`, `main`, `sha-<commit>`, `v1.2.3` |

---

## Dependabot

Automatische Abhaengigkeitsaktualisierungen (`.github/dependabot.yml`):

| Ecosystem | Verzeichnis | Intervall |
|---|---|---|
| pip | `/backend` | Woechentlich (Montag) |
| npm | `/frontend` | Woechentlich (Montag) |
| GitHub Actions | `/` | Monatlich |
| Docker | `/backend`, `/frontend` | Monatlich |

Minor/Patch-Updates werden gruppiert.

---

## Benoetigte Secrets

| Secret | Verwendung |
|---|---|
| `GITHUB_TOKEN` | Automatisch verfuegbar, GHCR-Push |
| `CODECOV_TOKEN` | Coverage-Upload zu Codecov |
| `SLACK_WEBHOOK_URL` | Failure-Benachrichtigungen |
| `STAGING_HOST` | SSH-Host des Staging-Servers |
| `STAGING_USER` | SSH-Benutzer fuer Staging |
| `STAGING_SSH_KEY` | SSH-Private-Key fuer Staging |
| `PROD_HOST` | SSH-Host des Produktionsservers |
| `PROD_USER` | SSH-Benutzer fuer Produktion |
| `PROD_SSH_KEY` | SSH-Private-Key fuer Produktion |

### Variables (nicht geheim)

| Variable | Verwendung |
|---|---|
| `NEXT_PUBLIC_API_URL` | Backend-URL fuer Frontend-Build |
| `STAGING_URL` | URL fuer Staging-Health-Check |
| `STAGING_APP_DIR` | App-Verzeichnis auf Staging |
| `PROD_URL` | URL fuer Produktions-Health-Check |
| `PROD_APP_DIR` | App-Verzeichnis auf Produktion |

---

## Environments

| Environment | Schutzregeln |
|---|---|
| `staging` | Keine (automatisches Deploy) |
| `production` | Required Reviewers (manuelle Genehmigung) |
