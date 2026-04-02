import time
import pytest
import respx
import httpx
import json
from inotec_kpi_tracker.sync_client import KPISyncClient
from inotec_kpi_tracker.types import SyncKPIConfig, KPIEvent


@pytest.fixture
def config() -> SyncKPIConfig:
    return SyncKPIConfig(
        api_url="http://kpi-api:4109/api/v1",
        api_key="test-key",
        app_id="test-app",
        batch_size=3,
        flush_interval=60.0,
    )


@pytest.fixture
def client(config: SyncKPIConfig) -> KPISyncClient:
    c = KPISyncClient(config)
    yield c
    c.close()


def make_event(**kwargs) -> KPIEvent:
    defaults = dict(
        app_id="test-app",
        event_type="task.completed",
        category="business_impact",
        kpi_id="business_impact.ai_task_completion_rate",
        value=1.0,
    )
    defaults.update(kwargs)
    return KPIEvent(**defaults)


@respx.mock
def test_track_queues_without_sending(client: KPISyncClient):
    route = respx.post("http://kpi-api:4109/api/v1/events").mock(
        return_value=httpx.Response(202)
    )
    client.track(make_event())
    client.track(make_event())
    assert len(client._queue) == 2
    assert not route.called


@respx.mock
def test_flush_sends_all_events(client: KPISyncClient):
    route = respx.post("http://kpi-api:4109/api/v1/events").mock(
        return_value=httpx.Response(202, json={"status": "accepted"})
    )
    client.track(make_event())
    client.track(make_event())
    client.flush()
    assert route.called
    events = json.loads(route.calls[0].request.content)
    assert len(events) == 2
    assert client._queue == []


@respx.mock
def test_auto_flush_at_batch_size(client: KPISyncClient):
    route = respx.post("http://kpi-api:4109/api/v1/events").mock(
        return_value=httpx.Response(202)
    )
    client.track(make_event())
    client.track(make_event())
    client.track(make_event())  # triggers flush
    time.sleep(0.05)
    assert route.called


@respx.mock
def test_sends_correct_auth_header(client: KPISyncClient):
    route = respx.post("http://kpi-api:4109/api/v1/events").mock(
        return_value=httpx.Response(202)
    )
    client.track(make_event())
    client.flush()
    assert route.calls[0].request.headers["X-API-Key"] == "test-key"


@respx.mock
def test_retries_on_server_error(client: KPISyncClient):
    route = respx.post("http://kpi-api:4109/api/v1/events").mock(
        return_value=httpx.Response(500)
    )
    client._retry_delays = [0, 0, 0]
    client.track(make_event())
    client.flush()
    assert route.call_count == 3
    assert client._queue == []


@respx.mock
def test_does_not_raise_on_network_error(client: KPISyncClient):
    respx.post("http://kpi-api:4109/api/v1/events").mock(
        side_effect=httpx.ConnectError("refused")
    )
    client._retry_delays = [0, 0, 0]
    client.track(make_event())
    client.flush()  # must not raise
    assert client._queue == []


@respx.mock
def test_close_flushes_remaining(client: KPISyncClient):
    route = respx.post("http://kpi-api:4109/api/v1/events").mock(
        return_value=httpx.Response(202)
    )
    client.track(make_event())
    client.close()
    assert route.called
