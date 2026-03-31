# KPI-Tracking -- Okosystem-Integration

## Ubersicht

KPI-Tracking (`C:\Projekte\KPI-Tracking`) ist der zentrale Beobachter des gesamten INOTEC-Okosystems. Alle Systeme -- Agent-Agency, PM-Tool, Paperclip -- senden ihre Events uber das KPI-Tracking SDK bzw. die REST-API. Die Daten landen in InfluxDB und werden uber Grafana-Dashboards visualisiert.

**Technologie-Stack von KPI-Tracking:**
- Runtime: Node.js mit Fastify
- Datenbank: InfluxDB (Zeitreihendaten)
- Visualisierung: Grafana
- API-Port: 4109
- SDK: JavaScript/TypeScript SDK fur direkte Integration

## Events die getrackt werden

### Von Agent-Agency

| Event | Felder | Beschreibung |
|-------|--------|--------------|
| `task.created` | `task_id`, `task_type`, `priority`, `workspace_id` | Neue Aufgabe wurde erstellt |
| `task.completed` | `task_id`, `task_type`, `duration_ms`, `retries` | Aufgabe erfolgreich abgeschlossen |
| `task.failed` | `task_id`, `task_type`, `error_type`, `duration_ms` | Aufgabe fehlgeschlagen |
| `ai.tokens_used` | `provider`, `model`, `input_tokens`, `output_tokens`, `cost` | Token-Verbrauch pro AI-Aufruf |
| `ai.provider_latency` | `provider`, `model`, `duration_ms`, `status_code` | Antwortzeit des AI-Providers |
| `agent.execution` | `executor_type`, `agent_role`, `duration_ms`, `success` | Ausfuhrung eines Agenten (Coder/Writer/Researcher) |

### Von PM-Tool

| Event | Felder | Beschreibung |
|-------|--------|--------------|
| `project.issue_created` | `project_id`, `issue_type`, `priority` | Neues Issue angelegt |
| `project.issue_completed` | `project_id`, `issue_id`, `duration_days` | Issue abgeschlossen |
| `sprint.velocity` | `sprint_id`, `story_points_completed`, `story_points_planned` | Sprint-Velocity nach Abschluss |
| `integration.sync` | `source` (jira/github/confluence), `items_synced`, `errors` | Synchronisation mit externen Tools |

### Von Paperclip

| Event | Felder | Beschreibung |
|-------|--------|--------------|
| `company.task_assigned` | `agent_name`, `role`, `task_type`, `priority` | Aufgabe einem Agenten zugewiesen |
| `company.task_completed` | `agent_name`, `role`, `duration_ms`, `quality_score` | Agent hat Aufgabe abgeschlossen |
| `company.budget_usage` | `agent_name`, `tokens_used`, `budget_remaining`, `budget_total` | Budget-Verbrauch pro Agent |
| `company.approval_requested` | `agent_name`, `task_id`, `risk_level` | Agent fordert menschliche Genehmigung an |
| `company.approval_granted` | `agent_name`, `task_id`, `approver`, `wait_time_ms` | Genehmigung erteilt |

## SDK-Integration

### In Agent-Agency (Python)

Agent-Agency nutzt `httpx` um Events an die KPI-Tracking API zu senden. Die Integration erfolgt im Workflow-Engine und in den Provider-Wrappern.

**Basis-Client einrichten (`app/kpi.py`):**

```python
import httpx
import time
import structlog
from app.config import settings

logger = structlog.get_logger()

KPI_BASE_URL = settings.KPI_TRACKING_URL  # z.B. "http://kpi-api:4109/api/v1"
KPI_API_KEY = settings.KPI_API_KEY

_kpi_client: httpx.AsyncClient | None = None


async def get_kpi_client() -> httpx.AsyncClient:
    """Lazy-initialisierter httpx-Client fuer KPI-Tracking."""
    global _kpi_client
    if _kpi_client is None:
        _kpi_client = httpx.AsyncClient(
            base_url=KPI_BASE_URL,
            headers={"X-API-Key": KPI_API_KEY},
            timeout=5.0,  # Kurzer Timeout, KPI-Tracking darf nicht blockieren
        )
    return _kpi_client


async def track_event(kpi: str, value: float, tags: dict | None = None) -> None:
    """Einzelnes Event an KPI-Tracking senden (fire-and-forget)."""
    try:
        client = await get_kpi_client()
        await client.post("/events", json={
            "events": [{
                "kpi": kpi,
                "value": value,
                "tags": tags or {},
                "timestamp": int(time.time() * 1000),
            }]
        })
    except Exception as e:
        # KPI-Tracking-Fehler sollen niemals den Hauptprozess stoeren
        logger.warning("KPI-Event konnte nicht gesendet werden", kpi=kpi, error=str(e))


async def track_events(events: list[dict]) -> None:
    """Mehrere Events als Batch senden."""
    try:
        client = await get_kpi_client()
        await client.post("/events", json={"events": events})
    except Exception as e:
        logger.warning("KPI-Batch konnte nicht gesendet werden", count=len(events), error=str(e))
```

**Integration in der Workflow-Engine (`app/orchestration/workflow_engine.py`):**

```python
from app.kpi import track_event

# Nach Task-Erstellung
await track_event("task.created", 1, tags={
    "task_id": str(task.id),
    "task_type": task.task_type,
    "priority": task.priority,
    "workspace_id": str(task.workspace_id),
})

# Nach erfolgreicher Ausfuehrung
await track_event("task.completed", 1, tags={
    "task_id": str(task.id),
    "task_type": task.task_type,
    "duration_ms": duration_ms,
    "retries": task.retry_count,
})

# Bei Fehler
await track_event("task.failed", 1, tags={
    "task_id": str(task.id),
    "task_type": task.task_type,
    "error_type": error.__class__.__name__,
})
```

**Token-Tracking im Provider (`app/providers/`):**

```python
from app.kpi import track_event

# Nach jedem AI-Aufruf
await track_event("ai.tokens_used", usage.total_tokens, tags={
    "provider": self.provider_name,
    "model": model,
    "input_tokens": usage.prompt_tokens,
    "output_tokens": usage.completion_tokens,
    "cost": calculated_cost,
})

await track_event("ai.provider_latency", duration_ms, tags={
    "provider": self.provider_name,
    "model": model,
    "status_code": response.status_code,
})
```

### In PM-Tool (Python/Django)

PM-Tool nutzt ebenfalls `httpx` fuer die Integration. Da PM-Tool synchron (Django) arbeitet, wird der synchrone Client verwendet.

**Basis-Client (`pm_tool/kpi_client.py`):**

```python
import httpx
import time
from django.conf import settings

kpi_client = httpx.Client(
    base_url=settings.KPI_TRACKING_URL,  # "http://kpi-api:4109/api/v1"
    headers={"X-API-Key": settings.KPI_API_KEY},
    timeout=5.0,
)


def track_event(kpi: str, value: float, tags: dict | None = None) -> None:
    """Event an KPI-Tracking senden."""
    try:
        kpi_client.post("/events", json={
            "events": [{
                "kpi": kpi,
                "value": value,
                "tags": tags or {},
                "timestamp": int(time.time() * 1000),
            }]
        })
    except Exception:
        pass  # KPI-Fehler nicht propagieren
```

**Integration in Django-Signals:**

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from pm_tool.kpi_client import track_event


@receiver(post_save, sender=Issue)
def track_issue_event(sender, instance, created, **kwargs):
    if created:
        track_event("project.issue_created", 1, tags={
            "project_id": str(instance.project_id),
            "issue_type": instance.issue_type,
            "priority": instance.priority,
        })
    elif instance.status == "done":
        track_event("project.issue_completed", 1, tags={
            "project_id": str(instance.project_id),
            "issue_id": str(instance.id),
            "duration_days": instance.duration_days,
        })
```

### In Paperclip (Node.js)

Paperclip nutzt die native `fetch`-API (Node.js 20+) fuer die KPI-Integration.

**Basis-Client (`src/lib/kpi-client.ts`):**

```typescript
const KPI_BASE_URL = process.env.KPI_TRACKING_URL || "http://kpi-api:4109/api/v1";
const KPI_API_KEY = process.env.KPI_API_KEY || "";

interface KpiEvent {
  kpi: string;
  value: number;
  tags?: Record<string, string | number>;
  timestamp?: number;
}

export async function trackEvent(kpi: string, value: number, tags?: Record<string, string | number>): Promise<void> {
  try {
    await fetch(`${KPI_BASE_URL}/events`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": KPI_API_KEY,
      },
      body: JSON.stringify({
        events: [{
          kpi,
          value,
          tags: tags ?? {},
          timestamp: Date.now(),
        }],
      }),
      signal: AbortSignal.timeout(5000), // 5s Timeout
    });
  } catch (error) {
    // KPI-Fehler sollen den Hauptprozess nicht stoeren
    console.warn(`KPI-Event '${kpi}' konnte nicht gesendet werden:`, error);
  }
}

export async function trackEvents(events: KpiEvent[]): Promise<void> {
  try {
    await fetch(`${KPI_BASE_URL}/events`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": KPI_API_KEY,
      },
      body: JSON.stringify({ events }),
      signal: AbortSignal.timeout(5000),
    });
  } catch (error) {
    console.warn(`KPI-Batch (${events.length} Events) fehlgeschlagen:`, error);
  }
}
```

**Nutzung in Paperclip-Services:**

```typescript
import { trackEvent } from "@/lib/kpi-client";

// Wenn ein Agent eine Aufgabe zugewiesen bekommt
await trackEvent("company.task_assigned", 1, {
  agent_name: agent.name,
  role: agent.role,
  task_type: task.type,
  priority: task.priority,
});

// Wenn ein Agent eine Aufgabe abschliesst
await trackEvent("company.task_completed", 1, {
  agent_name: agent.name,
  role: agent.role,
  duration_ms: endTime - startTime,
  quality_score: qaResult.score,
});

// Budget-Tracking
await trackEvent("company.budget_usage", tokensUsed, {
  agent_name: agent.name,
  tokens_used: tokensUsed,
  budget_remaining: agent.budget - tokensUsed,
  budget_total: agent.budget,
});
```

## Neue KPI-Definitionen

Diese KPIs muessen in KPI-Tracking registriert werden (uber die Admin-API oder Konfiguration):

### ai_task_completion_rate

```json
{
  "name": "ai_task_completion_rate",
  "description": "Anteil erfolgreich abgeschlossener AI-Aufgaben",
  "unit": "percent",
  "calculation": "completed_tasks / (completed_tasks + failed_tasks) * 100",
  "aggregation": "avg",
  "window": "1h",
  "alert_threshold": { "below": 80, "severity": "warning" }
}
```

### ai_cost_per_task

```json
{
  "name": "ai_cost_per_task",
  "description": "Durchschnittliche AI-Kosten pro Aufgabe (alle Provider)",
  "unit": "usd",
  "calculation": "sum(ai.tokens_used.cost) / count(task.completed)",
  "aggregation": "avg",
  "window": "1d",
  "alert_threshold": { "above": 0.50, "severity": "warning" }
}
```

### ai_provider_reliability

```json
{
  "name": "ai_provider_reliability",
  "description": "Verfuegbarkeit der AI-Provider (Erfolgsrate der API-Aufrufe)",
  "unit": "percent",
  "calculation": "successful_calls / total_calls * 100",
  "aggregation": "avg",
  "window": "15m",
  "tags": ["provider"],
  "alert_threshold": { "below": 95, "severity": "critical" }
}
```

### agent_utilization

```json
{
  "name": "agent_utilization",
  "description": "Auslastung der Agenten (aktive Zeit / verfuegbare Zeit)",
  "unit": "percent",
  "calculation": "sum(agent.execution.duration_ms) / window_ms * 100",
  "aggregation": "avg",
  "window": "1h",
  "tags": ["executor_type", "agent_role"],
  "alert_threshold": { "above": 90, "severity": "warning" }
}
```

### human_approval_time

```json
{
  "name": "human_approval_time",
  "description": "Durchschnittliche Wartezeit auf menschliche Genehmigung",
  "unit": "ms",
  "calculation": "avg(approval_granted.timestamp - approval_requested.timestamp)",
  "aggregation": "avg",
  "window": "1d",
  "alert_threshold": { "above": 3600000, "severity": "warning" }
}
```

## Grafana Dashboard: "AI Okosystem"

Ein dediziertes Grafana-Dashboard fuer das gesamte INOTEC-Okosystem. Import uber die Grafana-API oder als JSON-Datei.

### Panel-Layout

```
+------------------------------------------------------+
|              AI Okosystem -- Uebersicht               |
+------------------+------------------+----------------+
| Aufgaben heute   | Token-Verbrauch  | Kosten heute   |
| (Stat Panel)     | (Stat Panel)     | (Stat Panel)   |
+------------------+------------------+----------------+
|         Task Completion Rate (Gauge)                  |
|         [Ziel: > 90%]                                 |
+------------------------------------------------------+
|    AI-Provider Latenz           |  Provider Reliability|
|    (Time Series, pro Provider)  |  (Gauge, pro Prov.) |
+------------------------------------------------------+
|         Token-Verbrauch nach Provider & Modell        |
|         (Stacked Bar Chart, stuendlich)               |
+------------------------------------------------------+
|    Agent Auslastung             |  Budget-Verbrauch    |
|    (Heatmap nach Rolle)         |  (Bar Gauge)         |
+------------------------------------------------------+
|         Human Approval Wartezeit                      |
|         (Time Series mit Threshold-Linie)             |
+------------------------------------------------------+
|    Sprint Velocity              |  Integrations-Sync   |
|    (Bar Chart)                  |  (Status-Tabelle)    |
+------------------------------------------------------+
```

### InfluxDB Queries (Flux)

**Task Completion Rate:**
```flux
completed = from(bucket: "kpi")
  |> range(start: -1h)
  |> filter(fn: (r) => r.kpi == "task.completed")
  |> count()

failed = from(bucket: "kpi")
  |> range(start: -1h)
  |> filter(fn: (r) => r.kpi == "task.failed")
  |> count()

// Rate = completed / (completed + failed) * 100
```

**Token-Verbrauch nach Provider:**
```flux
from(bucket: "kpi")
  |> range(start: -24h)
  |> filter(fn: (r) => r.kpi == "ai.tokens_used")
  |> group(columns: ["provider", "model"])
  |> aggregateWindow(every: 1h, fn: sum)
```

**Kosten pro Tag:**
```flux
from(bucket: "kpi")
  |> range(start: -7d)
  |> filter(fn: (r) => r.kpi == "ai.tokens_used")
  |> filter(fn: (r) => r._field == "cost")
  |> aggregateWindow(every: 1d, fn: sum)
```

**Provider Latenz (P95):**
```flux
from(bucket: "kpi")
  |> range(start: -1h)
  |> filter(fn: (r) => r.kpi == "ai.provider_latency")
  |> group(columns: ["provider"])
  |> quantile(q: 0.95)
```

### Alerting-Regeln

| Regel | Bedingung | Aktion |
|-------|-----------|--------|
| Task-Fehlerrate hoch | Completion Rate < 80% fuer 15min | Slack-Benachrichtigung |
| Provider ausgefallen | Reliability < 50% fuer 5min | Slack + E-Mail |
| Budget fast aufgebraucht | budget_remaining < 10% | Slack-Warnung |
| Genehmigung wartet lange | approval_time > 1h | E-Mail an Approver |
| Kosten-Spike | cost_per_task > 2x Durchschnitt | Slack-Warnung |

### Dashboard als Code (Provisioning)

Die Dashboard-Definition wird als JSON in `C:\Projekte\KPI-Tracking\grafana\dashboards\ai-ecosystem.json` abgelegt und uber Grafana-Provisioning automatisch geladen:

```yaml
# grafana/provisioning/dashboards/ecosystem.yml
apiVersion: 1
providers:
  - name: "INOTEC Ecosystem"
    folder: "AI Ecosystem"
    type: file
    options:
      path: /var/lib/grafana/dashboards
      foldersFromFilesStructure: true
```

## Netzwerk-Konfiguration

Alle Services kommunizieren uber das Docker-Netzwerk `inotec-ecosystem`:

```
Agent-Agency (8000) ---> KPI-Tracking (4109)
PM-Tool (8080)      ---> KPI-Tracking (4109)
Paperclip (3100)    ---> KPI-Tracking (4109)
                         |
                         v
                    InfluxDB (8086)
                         |
                         v
                    Grafana (3000)
```

## Checkliste fuer die Integration

- [ ] `KPI_TRACKING_URL` und `KPI_API_KEY` in allen `.env`-Dateien konfigurieren
- [ ] KPI-Client-Modul in jedem Projekt erstellen (siehe oben)
- [ ] Events in Workflow-Engine (Agent-Agency) einbauen
- [ ] Events in Django-Signals (PM-Tool) einbauen
- [ ] Events in Paperclip-Services einbauen
- [ ] Neue KPI-Definitionen in KPI-Tracking registrieren
- [ ] Grafana-Dashboard importieren
- [ ] Alerting-Regeln konfigurieren
- [ ] Smoke-Test: Ein Task durchlaufen lassen und Events in Grafana pruefen
