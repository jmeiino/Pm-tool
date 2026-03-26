# Branch-Protection & CODEOWNERS

Empfohlene Konfiguration fuer den `main`-Branch.

---

## Branch-Protection-Regeln fuer `main`

Diese Regeln werden in den **GitHub Repository Settings** unter **Branches > Branch protection rules** konfiguriert.

### Empfohlene Einstellungen

| Regel | Empfehlung |
|---|---|
| **Require a pull request before merging** | Aktiviert |
| **Required approving reviews** | Mindestens 1 |
| **Dismiss stale pull request approvals** | Aktiviert |
| **Require status checks to pass** | Aktiviert |
| **Required status checks** | `Lint (ruff)`, `Tests (pytest)`, `Lint & Typecheck`, `Playwright E2E` |
| **Require branches to be up to date** | Aktiviert |
| **Require linear history** | Aktiviert |
| **Include administrators** | Aktiviert |

### Status-Checks einrichten

Nachdem die Workflows mindestens einmal gelaufen sind, koennen die Status-Checks ausgewaehlt werden:

1. Repository Settings > Branches > Add branch protection rule
2. Branch name pattern: `main`
3. "Require status checks to pass before merging" aktivieren
4. Folgende Checks auswaehlen:
   - `Lint (ruff)` (aus Backend CI)
   - `Tests (pytest)` (aus Backend CI)
   - `Lint & Typecheck` (aus Frontend CI)
   - `Unit Tests (Vitest)` (aus Frontend CI)
   - `Playwright E2E` (aus E2E Tests)

---

## CODEOWNERS

Die Datei `.github/CODEOWNERS` definiert, wer fuer welche Bereiche verantwortlich ist und automatisch als Reviewer zu PRs hinzugefuegt wird.

### Aktuelle Konfiguration

```
/backend/           @jmeiino
/frontend/          @jmeiino
/.github/           @jmeiino
/docker-compose*    @jmeiino
/nginx/             @jmeiino
```

### Anpassung fuer Teams

Bei mehreren Entwicklern die CODEOWNERS-Datei erweitern:

```
/backend/           @backend-team
/frontend/          @frontend-team
/.github/           @devops-team
```
