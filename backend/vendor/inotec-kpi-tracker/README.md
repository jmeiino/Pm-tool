# inotec-kpi-tracker (Python SDK)

Python SDK zum Senden von KPI-Events an die KPI-Tracking API.

## Installation

```
pip install inotec-kpi-tracker
```

## Verwendung

### Async (FastAPI / Agent-Agency)

```python
from inotec_kpi_tracker import KPIClient, KPIEvent, KPIConfig

config = KPIConfig(
    api_url="http://kpi-api:4109/api/v1",
    api_key="your-api-key",
    app_id="agent-agency",
    environment="production",
)
client = KPIClient(config)

await client.track(KPIEvent(
    app_id="agent-agency",
    event_type="task.completed",
    category="business_impact",
    kpi_id="business_impact.ai_task_completion_rate",
    value=95.0,
    unit="percent",
    dimensions={"provider": "anthropic", "model": "claude-opus-4-6"},
))

await client.close()
```

### Sync (Django / PM-Tool)

```python
from inotec_kpi_tracker import KPISyncClient, KPIEvent, SyncKPIConfig

client = KPISyncClient(SyncKPIConfig(
    api_url="http://kpi-api:4109/api/v1",
    api_key="your-api-key",
    app_id="pm-tool",
))

client.track(KPIEvent(
    app_id="pm-tool",
    event_type="project.issue_created",
    category="usage",
    kpi_id="usage.api_calls",
    value=1.0,
))
```
