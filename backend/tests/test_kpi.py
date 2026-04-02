import pytest
from unittest.mock import MagicMock
from inotec_kpi_tracker import KPISyncClient, SyncKPIConfig, KPIEvent


@pytest.fixture
def mock_kpi_client():
    config = SyncKPIConfig(
        api_url="http://localhost:4109/api/v1",
        api_key="test-key",
        app_id="pm-tool",
        batch_size=10,
        flush_interval=999,
    )
    client = KPISyncClient(config)
    client._http = MagicMock()
    client._http.post = MagicMock(return_value=MagicMock(status_code=202))
    client._http.close = MagicMock()
    return client


def test_track_issue_created(mock_kpi_client):
    event = KPIEvent(
        app_id="pm-tool",
        event_type="project.issue_created",
        category="usage",
        kpi_id="usage.issue_created",
        value=1,
        dimensions={"project_id": "p-1", "issue_type": "task", "priority": "high"},
    )
    mock_kpi_client.track(event)
    assert len(mock_kpi_client._queue) == 1
    mock_kpi_client.close()


def test_flush_sends_bare_array(mock_kpi_client):
    event = KPIEvent(
        app_id="pm-tool",
        event_type="project.issue_created",
        category="usage",
        kpi_id="usage.issue_created",
        value=1,
    )
    mock_kpi_client.track(event)
    mock_kpi_client.flush()
    call_args = mock_kpi_client._http.post.call_args
    payload = call_args[1]["json"]
    assert isinstance(payload, list)
    assert payload[0]["app_id"] == "pm-tool"
    mock_kpi_client.close()
