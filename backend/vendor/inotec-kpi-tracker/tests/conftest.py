import pytest
from inotec_kpi_tracker.types import KPIEvent, KPIConfig, SyncKPIConfig


@pytest.fixture
def sample_event() -> KPIEvent:
    return KPIEvent(
        app_id="test-app",
        event_type="task.completed",
        category="business_impact",
        kpi_id="business_impact.ai_task_completion_rate",
        value=95.0,
        unit="percent",
    )


@pytest.fixture
def async_config() -> KPIConfig:
    return KPIConfig(
        api_url="http://localhost:4109/api/v1",
        api_key="test-key",
        app_id="test-app",
    )


@pytest.fixture
def sync_config() -> SyncKPIConfig:
    return SyncKPIConfig(
        api_url="http://localhost:4109/api/v1",
        api_key="test-key",
        app_id="test-app",
    )
