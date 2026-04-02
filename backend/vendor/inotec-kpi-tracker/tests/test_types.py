import pytest
from datetime import datetime, timezone
from uuid import UUID
from inotec_kpi_tracker.types import KPIEvent, KPIConfig, SyncKPIConfig


def test_kpi_event_requires_mandatory_fields():
    with pytest.raises(TypeError):
        KPIEvent()  # Missing required fields


def test_kpi_event_auto_generates_event_id():
    event = KPIEvent(
        app_id="test-app",
        event_type="task.completed",
        category="business_impact",
        kpi_id="business_impact.ai_task_completion_rate",
        value=95.0,
    )
    assert event.event_id != ""
    UUID(event.event_id)  # Must be valid UUID


def test_kpi_event_auto_generates_timestamp():
    event = KPIEvent(
        app_id="test-app",
        event_type="task.completed",
        category="business_impact",
        kpi_id="business_impact.ai_task_completion_rate",
        value=95.0,
    )
    # Must be valid ISO 8601 with Z suffix
    assert event.timestamp.endswith("Z")


def test_kpi_event_to_dict_matches_api_schema():
    event = KPIEvent(
        app_id="test-app",
        event_type="task.completed",
        category="business_impact",
        kpi_id="business_impact.ai_task_completion_rate",
        value=95.0,
        unit="percent",
        dimensions={"provider": "anthropic"},
    )
    d = event.to_dict()
    assert d["schema_version"] == "1.0"
    assert d["app_id"] == "test-app"
    assert d["event_type"] == "task.completed"
    assert d["category"] == "business_impact"
    assert d["kpi_id"] == "business_impact.ai_task_completion_rate"
    assert d["value"] == 95.0
    assert d["unit"] == "percent"
    assert d["dimensions"] == {"provider": "anthropic"}
    assert "event_id" in d
    assert "timestamp" in d


def test_kpi_event_category_must_be_valid():
    with pytest.raises(ValueError, match="category"):
        KPIEvent(
            app_id="test-app",
            event_type="x",
            category="invalid_category",
            kpi_id="x",
            value=1.0,
        )


def test_kpi_config_defaults():
    config = KPIConfig(
        api_url="http://localhost:4109/api/v1",
        api_key="test-key",
        app_id="test-app",
    )
    assert config.environment == "production"
    assert config.batch_size == 50
    assert config.flush_interval == 10.0


def test_sync_kpi_config_defaults():
    config = SyncKPIConfig(
        api_url="http://localhost:4109/api/v1",
        api_key="test-key",
        app_id="test-app",
    )
    assert config.environment == "production"
    assert config.batch_size == 50
    assert config.flush_interval == 10.0
